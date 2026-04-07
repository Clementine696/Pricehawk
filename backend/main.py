"""
PriceHawk API - CFW/Makro Branch
Simplified backend for CFW (Central Food Wholesale) and Makro comparison
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, Depends, Cookie, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import secrets
import os
import logging

from database import get_user_by_username, get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_sessions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _parse_search_input(search: str) -> list[str]:
    """Normalise a search string (commas/newlines → spaces) and split into tokens."""
    normalised = search.replace('\n', ' ').replace('\r', ' ').replace(',', ' ')
    return [s.strip() for s in normalised.split() if s.strip()]


def _extract_bearer_token(authorization: str | None) -> str | None:
    """Return the token from an 'Authorization: Bearer <token>' header, or None."""
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or direct connection"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# FastAPI App Setup
# ---------------------------------------------------------------------------

app = FastAPI(title="PriceHawk CFW/Makro API")

# CORS configuration
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
cors_origins_list = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Session settings
SESSION_EXPIRE_MINUTES = 10080  # 7 days
COOKIE_NAME = "session_token"
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str


def get_current_user(
    session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    authorization: Optional[str] = Header(None)
) -> dict:
    """Validate session from cookie or Authorization header and return user"""
    token = _extract_bearer_token(authorization) or session_token

    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[token]
    if datetime.utcnow() > session["expires"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")

    session["last_activity"] = datetime.utcnow()
    return session["user"]


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response, request: Request):
    """Login and set session cookie"""
    user = get_user_by_username(data.username)

    if not user or not verify_password(data.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for username: {data.username} from IP: {get_client_ip(request)}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create session token
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    login_time = datetime.utcnow()

    sessions[token] = {
        "user": {"user_id": user["user_id"], "username": user["username"]},
        "expires": expires,
        "login_time": login_time,
        "last_activity": login_time,
        "ip_address": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown"),
    }

    logger.info(
        f"LOGIN | User: {user['username']} | IP: {get_client_ip(request)} | "
        f"Time: {login_time.isoformat()}"
    )

    # Set HTTP-only cookie
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")

    if is_production:
        cookie_value = f"{COOKIE_NAME}={token}; HttpOnly; Secure; SameSite=None; Partitioned; Max-Age={SESSION_EXPIRE_MINUTES * 60}; Path=/"
        response.headers.append("Set-Cookie", cookie_value)
    else:
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=SESSION_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=False,
        )

    return {"message": "Login successful", "username": user["username"], "token": token}


@app.post("/api/auth/logout")
def logout(
    response: Response,
    request: Request,
    session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    authorization: Optional[str] = Header(None)
):
    """Logout and clear session"""
    token = _extract_bearer_token(authorization) or session_token

    if token and token in sessions:
        session = sessions[token]
        username = session["user"]["username"]
        login_time = session.get("login_time", datetime.utcnow())
        logout_time = datetime.utcnow()
        session_duration = (logout_time - login_time).total_seconds()
        
        logger.info(
            f"LOGOUT | User: {username} | IP: {get_client_ip(request)} | "
            f"Duration: {session_duration:.0f} seconds"
        )
        
        del sessions[token]

    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    response.delete_cookie(
        key=COOKIE_NAME,
        samesite="none" if is_production else "lax",
        secure=True if is_production else False,
    )
    return {"message": "Logged out"}


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return user


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# Dashboard Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/stats")
def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics for CFW/Makro"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Total products by retailer
            cur.execute("""
                SELECT 
                    retailer_id,
                    COUNT(*) as product_count,
                    COUNT(DISTINCT category_id) as category_count
                FROM products
                GROUP BY retailer_id
            """)
            retailer_stats = cur.fetchall()
            
            # Total products
            cur.execute("SELECT COUNT(*) as total FROM products")
            total_products = cur.fetchone()["total"]
            
            # Total categories
            cur.execute("SELECT COUNT(*) as total FROM categories")
            total_categories = cur.fetchone()["total"]
            
            # Total retailers
            cur.execute("SELECT COUNT(*) as total FROM retailers")
            total_retailers = cur.fetchone()["total"]
            
            # Recent price updates
            cur.execute("""
                SELECT COUNT(*) as total
                FROM price_history
                WHERE recorded_at >= NOW() - INTERVAL '7 days'
            """)
            recent_updates = cur.fetchone()["total"]
            
            # Price statistics by retailer
            cur.execute("""
                SELECT 
                    retailer_id,
                    AVG(current_price) as avg_price,
                    MIN(current_price) as min_price,
                    MAX(current_price) as max_price
                FROM products
                WHERE current_price IS NOT NULL
                GROUP BY retailer_id
            """)
            price_stats = cur.fetchall()
            
            return {
                "total_products": total_products,
                "total_retailers": total_retailers,
                "total_categories": total_categories,
                "total_matches": 0,  # Not applicable for CFW/Makro
                "pending_reviews": 0,  # Not applicable for CFW/Makro
                "recent_price_updates": recent_updates,
                "retailer_stats": [
                    {
                        "retailer_id": r["retailer_id"],
                        "product_count": r["product_count"],
                        "category_count": r["category_count"]
                    }
                    for r in retailer_stats
                ],
                "price_stats": [
                    {
                        "retailer_id": p["retailer_id"],
                        "avg_price": float(p["avg_price"]) if p["avg_price"] else None,
                        "min_price": float(p["min_price"]) if p["min_price"] else None,
                        "max_price": float(p["max_price"]) if p["max_price"] else None
                    }
                    for p in price_stats
                ]
            }


@app.get("/api/retailers")
def get_retailers(user: dict = Depends(get_current_user)):
    """Get all retailers (CFW and Makro)"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.retailer_id,
                    r.name,
                    r.domain,
                    COUNT(p.id) as product_count
                FROM retailers r
                LEFT JOIN products p ON r.retailer_id = p.retailer_id
                GROUP BY r.retailer_id, r.name, r.domain
                ORDER BY r.retailer_id
            """)
            retailers = cur.fetchall()
            
            return {
                "retailers": [
                    {
                        "retailer_id": r["retailer_id"],
                        "name": r["name"],
                        "domain": r["domain"],
                        "product_count": r["product_count"]
                    }
                    for r in retailers
                ]
            }


# ---------------------------------------------------------------------------
# Product Endpoints (from previous CFW/Makro endpoints)
# ---------------------------------------------------------------------------

@app.get("/api/products")
def get_products(
    user: dict = Depends(get_current_user),
    retailer: Optional[str] = Query(None, description="Filter by retailer: 'cfw' or 'makro'"),
    category: Optional[str] = Query(None, description="Filter by category (comma-separated category IDs)"),
    brand: Optional[str] = Query(None, description="Filter by brand (comma-separated brands)"),
    search: Optional[str] = Query(None, description="Search by name, SKU, or barcode"),
    match_status: Optional[str] = Query(None, description="Filter by match status: 'verified', 'unverified', 'no_match'"),
    price_status: Optional[str] = Query(None, description="Filter by price status: 'lower', 'higher', 'same', 'no_match'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    """Get products with filters"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Build WHERE clause
            where_parts = ["p.retailer_id = 'cfw'"]
            params = []

            if retailer:
                where_parts[0] = "p.retailer_id = %s"
                params.append(retailer)
            
            # Category filter (supports multiple categories)
            if category:
                category_ids = [c.strip() for c in category.split(',') if c.strip()]
                if category_ids:
                    placeholders = ','.join(['%s'] * len(category_ids))
                    where_parts.append(f"p.category_id IN ({placeholders})")
                    params.extend(category_ids)
            
            # Brand filter (supports multiple brands)
            if brand:
                brands = [b.strip() for b in brand.split(',') if b.strip()]
                if brands:
                    placeholders = ','.join(['%s'] * len(brands))
                    where_parts.append(f"p.brand IN ({placeholders})")
                    params.extend(brands)
            
            if search:
                search_tokens = _parse_search_input(search)
                for token in search_tokens:
                    where_parts.append(
                        "(p.name ILIKE %s OR p.name_en ILIKE %s OR p.sku ILIKE %s OR p.barcode ILIKE %s)"
                    )
                    pattern = f"%{token}%"
                    params.extend([pattern, pattern, pattern, pattern])
            
            # Add match_status filter
            if match_status:
                if match_status == 'no_match':
                    # No matches at all, OR all matches are rejected (is_same = FALSE)
                    where_parts.append("""
                        NOT EXISTS (
                            SELECT 1 FROM product_matches pm
                            WHERE (pm.cfw_product_id = p.id OR pm.makro_product_id = p.id)
                            AND (pm.is_verified = FALSE OR pm.is_same = TRUE)
                        )
                    """)
                elif match_status == 'unverified':
                    # Has at least one match not yet reviewed
                    where_parts.append("""
                        EXISTS (
                            SELECT 1 FROM product_matches pm
                            WHERE (pm.cfw_product_id = p.id OR pm.makro_product_id = p.id)
                            AND pm.is_verified = FALSE
                        )
                    """)
                elif match_status == 'verified':
                    # Has a confirmed correct match
                    where_parts.append("""
                        EXISTS (
                            SELECT 1 FROM product_matches pm
                            WHERE (pm.cfw_product_id = p.id OR pm.makro_product_id = p.id)
                            AND pm.is_verified = TRUE AND pm.is_same = TRUE
                        )
                    """)
            
            # Add price_status filter  
            if price_status:
                if price_status == 'no_match':
                    # No confirmed match = no price comparison
                    where_parts.append("""
                        NOT EXISTS (
                            SELECT 1 FROM product_matches pm
                            WHERE (pm.cfw_product_id = p.id OR pm.makro_product_id = p.id)
                            AND pm.is_verified = TRUE AND pm.is_same = TRUE
                        )
                    """)
                elif price_status in ['lower', 'higher', 'same']:
                    if price_status == 'lower':
                        comparison = '<'
                    elif price_status == 'higher':
                        comparison = '>'
                    else:
                        comparison = '='

                    where_parts.append(f"""
                        EXISTS (
                            SELECT 1 FROM product_matches pm
                            JOIN products p2 ON (
                                CASE
                                    WHEN pm.cfw_product_id = p.id THEN pm.makro_product_id = p2.id
                                    WHEN pm.makro_product_id = p.id THEN pm.cfw_product_id = p2.id
                                END
                            )
                            WHERE (pm.cfw_product_id = p.id OR pm.makro_product_id = p.id)
                            AND pm.is_verified = TRUE AND pm.is_same = TRUE
                            AND p.current_price IS NOT NULL
                            AND p2.current_price IS NOT NULL
                            AND p.current_price {comparison} p2.current_price
                        )
                    """)
            
            where_clause = " AND ".join(where_parts)
            
            # Get total count
            cur.execute(
                f"SELECT COUNT(*) as count FROM products p WHERE {where_clause}",
                params
            )
            total = cur.fetchone()["count"]
            
            # Get paginated products with match information
            offset = (page - 1) * page_size
            cur.execute(
                f"""
                SELECT 
                    p.id,
                    p.retailer_id,
                    r.name as retailer_name,
                    p.sku,
                    p.barcode,
                    p.name,
                    p.name_en,
                    p.brand,
                    p.category_id,
                    c.category_name,
                    p.dept_id,
                    p.sub_dept_id,
                    p.class_id,
                    p.sub_class_id,
                    p.current_price,
                    p.step_prices,
                    p.url,
                    p.image_url,
                    p.is_active,
                    p.created_at,
                    p.updated_at,
                    -- Match information
                    CASE 
                        WHEN p.retailer_id = 'cfw' THEN 
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.cfw_product_id = p.id)
                        WHEN p.retailer_id = 'makro' THEN 
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.makro_product_id = p.id)
                    END as match_count,
                    -- confirmed correct matches
                    CASE
                        WHEN p.retailer_id = 'cfw' THEN
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.cfw_product_id = p.id AND pm.is_verified = TRUE AND pm.is_same = TRUE)
                        WHEN p.retailer_id = 'makro' THEN
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.makro_product_id = p.id AND pm.is_verified = TRUE AND pm.is_same = TRUE)
                    END as verified_match_count,
                    -- matches not yet reviewed
                    CASE
                        WHEN p.retailer_id = 'cfw' THEN
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.cfw_product_id = p.id AND pm.is_verified = FALSE)
                        WHEN p.retailer_id = 'makro' THEN
                            (SELECT COUNT(*) FROM product_matches pm WHERE pm.makro_product_id = p.id AND pm.is_verified = FALSE)
                    END as unverified_count,
                    -- price: use confirmed correct match first, else top unverified by score
                    CASE
                        WHEN p.retailer_id = 'cfw' THEN COALESCE(
                            (SELECT mp.current_price FROM product_matches pm
                             JOIN products mp ON pm.makro_product_id = mp.id
                             WHERE pm.cfw_product_id = p.id AND pm.is_verified = TRUE AND pm.is_same = TRUE
                             LIMIT 1),
                            (SELECT mp.current_price FROM product_matches pm
                             JOIN products mp ON pm.makro_product_id = mp.id
                             WHERE pm.cfw_product_id = p.id AND pm.is_verified = FALSE
                             ORDER BY pm.match_score DESC LIMIT 1)
                        )
                        WHEN p.retailer_id = 'makro' THEN COALESCE(
                            (SELECT cp.current_price FROM product_matches pm
                             JOIN products cp ON pm.cfw_product_id = cp.id
                             WHERE pm.makro_product_id = p.id AND pm.is_verified = TRUE AND pm.is_same = TRUE
                             LIMIT 1),
                            (SELECT cp.current_price FROM product_matches pm
                             JOIN products cp ON pm.cfw_product_id = cp.id
                             WHERE pm.makro_product_id = p.id AND pm.is_verified = FALSE
                             ORDER BY pm.match_score DESC LIMIT 1)
                        )
                    END as matched_price
                FROM products p
                JOIN retailers r ON p.retailer_id = r.retailer_id
                LEFT JOIN categories c ON p.retailer_id = c.retailer_id AND p.category_id = c.category_id
                WHERE {where_clause}
                ORDER BY p.id
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset]
            )
            products = cur.fetchall()
            
            # Get all retailers for filter
            cur.execute("""
                SELECT DISTINCT r.retailer_id, r.name
                FROM retailers r
                JOIN products p ON r.retailer_id = p.retailer_id
                ORDER BY r.name
            """)
            retailers = cur.fetchall()
            
            # Get all categories for filter
            cur.execute("""
                SELECT DISTINCT c.category_id, c.category_name, c.retailer_id
                FROM categories c
                JOIN products p ON c.retailer_id = p.retailer_id AND c.category_id = p.category_id
                ORDER BY c.category_name
            """)
            categories = cur.fetchall()
            
            # Get all brands for filter
            cur.execute("""
                SELECT DISTINCT brand
                FROM products
                WHERE brand IS NOT NULL AND brand != ''
                ORDER BY brand
            """)
            brands = [row["brand"] for row in cur.fetchall()]
            
            return {
                "products": products,
                "total": total,
                "retailers": retailers,
                "categories": categories,
                "brands": brands,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }


@app.get("/api/products/{sku}")
def get_product_detail(
    sku: str,
    user: dict = Depends(get_current_user)
):
    """Get single product details by SKU"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get product details by SKU
            cur.execute(
                """
                SELECT 
                    p.id,
                    p.retailer_id,
                    p.sku,
                    p.barcode,
                    p.name,
                    p.brand,
                    p.category_id,
                    c.category_name,
                    p.current_price,
                    p.url,
                    p.image_url,
                    p.is_active,
                    p.created_at,
                    p.updated_at
                FROM products p
                LEFT JOIN categories c ON p.retailer_id = c.retailer_id AND p.category_id = c.category_id
                WHERE p.sku = %s
                """,
                (sku,)
            )
            product = cur.fetchone()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Get all matches for this product
            cur.execute(
                """
                SELECT
                    pm.match_id,
                    pm.match_score,
                    pm.is_verified,
                    pm.is_same,
                    pm.verified_at,
                    p2.id as matched_product_id,
                    p2.retailer_id as matched_retailer_id,
                    r2.name as matched_retailer_name,
                    p2.sku as matched_sku,
                    p2.barcode as matched_barcode,
                    p2.name as matched_name,
                    p2.brand as matched_brand,
                    c2.category_name as matched_category_name,
                    p2.current_price as matched_price,
                    p2.url as matched_url,
                    p2.image_url as matched_image,
                    p2.updated_at as matched_updated_at
                FROM product_matches pm
                JOIN products p2 ON (
                    CASE
                        WHEN pm.cfw_product_id = %s THEN pm.makro_product_id = p2.id
                        WHEN pm.makro_product_id = %s THEN pm.cfw_product_id = p2.id
                    END
                )
                JOIN retailers r2 ON p2.retailer_id = r2.retailer_id
                LEFT JOIN categories c2 ON p2.retailer_id = c2.retailer_id AND p2.category_id = c2.category_id
                WHERE pm.cfw_product_id = %s OR pm.makro_product_id = %s
                ORDER BY pm.is_verified DESC, pm.match_score DESC
                """,
                (product['id'], product['id'], product['id'], product['id'])
            )

            matches_rows = cur.fetchall()

            # Format matches — shape must match frontend Match interface
            matches = []
            for row in matches_rows:
                matches.append({
                    "match_id": row["match_id"],
                    "is_same": row["is_same"],
                    "verified_by_user": bool(row["is_verified"]),
                    "confidence_score": float(row["match_score"]) if row["match_score"] else None,
                    "reason": None,
                    "match_type": "auto",
                    "product": {
                        "product_id": row["matched_product_id"],
                        "sku": row["matched_sku"],
                        "name": row["matched_name"],
                        "brand": row["matched_brand"],
                        "category": row["matched_category_name"],
                        "current_price": float(row["matched_price"]) if row["matched_price"] else None,
                        "original_price": None,
                        "link": row["matched_url"],
                        "image": row["matched_image"],
                        "retailer_id": row["matched_retailer_id"],
                        "retailer_name": row["matched_retailer_name"],
                        "last_updated_at": row["matched_updated_at"].isoformat() if row["matched_updated_at"] else None,
                        "scrape_fail_count": 0,
                    }
                })
            
            # Format product response
            product_data = {
                "id": product["id"],
                "retailer_id": product["retailer_id"],
                "sku": product["sku"],
                "barcode": product["barcode"],
                "name": product["name"],
                "brand": product["brand"],
                "category_id": product["category_id"],
                "category_name": product["category_name"],
                "current_price": float(product["current_price"]) if product["current_price"] else None,
                "url": product["url"],
                "image": product["image_url"],  # Frontend expects "image"
                "is_active": product["is_active"],
                "created_at": product["created_at"].isoformat() if product["created_at"] else None,
                "updated_at": product["updated_at"].isoformat() if product["updated_at"] else None
            }
            
            return {
                "product": product_data,
                "matches": matches,
                "total_matches": len(matches)
            }


@app.get("/api/products/{product_id}/price-history")
def get_price_history(
    product_id: int,
    user: dict = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365)
):
    """Get price history for a product"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    price,
                    step_prices,
                    recorded_at
                FROM price_history
                WHERE product_id = %s
                    AND recorded_at >= NOW() - INTERVAL '%s days'
                ORDER BY recorded_at ASC
                """,
                (product_id, days)
            )
            history = cur.fetchall()
            
            return {
                "product_id": product_id,
                "history": [
                    {
                        "price": float(h["price"]) if h["price"] else None,
                        "step_prices": h["step_prices"],
                        "recorded_at": h["recorded_at"].isoformat()
                    }
                    for h in history
                ]
            }


@app.post("/api/matches/{match_id}/verify")
def verify_match(
    match_id: int,
    body: dict,
    user: dict = Depends(get_current_user)
):
    """Verify a match as correct (is_same=True) or incorrect (is_same=False)"""
    is_same = body.get("is_same")
    if is_same is None:
        raise HTTPException(status_code=400, detail="is_same is required")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE product_matches
                SET is_verified = TRUE,
                    is_same = %s,
                    verified_at = NOW(),
                    updated_at = NOW()
                WHERE match_id = %s
                RETURNING match_id
                """,
                (is_same, match_id)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Match not found")
            conn.commit()
    return {"match_id": match_id, "is_verified": True, "is_same": is_same}


@app.post("/api/matches/{match_id}/undo")
def undo_match(
    match_id: int,
    user: dict = Depends(get_current_user)
):
    """Reset a match back to unverified"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE product_matches
                SET is_verified = FALSE,
                    is_same = NULL,
                    verified_at = NULL,
                    updated_at = NOW()
                WHERE match_id = %s
                RETURNING match_id
                """,
                (match_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Match not found")
            conn.commit()
    return {"match_id": match_id, "is_verified": False, "is_same": None}


@app.get("/api/categories")
def get_categories(
    user: dict = Depends(get_current_user),
    retailer: Optional[str] = Query(None, description="Filter by retailer: 'cfw' or 'makro'")
):
    """Get all categories"""
    with get_db() as conn:
        with conn.cursor() as cur:
            where_clause = ""
            params = []
            
            if retailer:
                where_clause = "WHERE retailer_id = %s"
                params.append(retailer)
            
            cur.execute(
                f"""
                SELECT 
                    c.retailer_id,
                    c.category_id,
                    c.category_name,
                    COUNT(p.id) as product_count
                FROM categories c
                LEFT JOIN products p ON c.retailer_id = p.retailer_id AND c.category_id = p.category_id
                {where_clause}
                GROUP BY c.retailer_id, c.category_id, c.category_name
                ORDER BY c.retailer_id, c.category_name
                """,
                params
            )
            categories = cur.fetchall()
            
            return {"categories": categories}


# ---------------------------------------------------------------------------
# Scraping Infrastructure
# ---------------------------------------------------------------------------

import subprocess
import uuid
import json as _json
import signal

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_SCRIPT = os.path.join(BACKEND_DIR, "scraper-url", "adws", "adw_ecommerce_product_scraper.py")
RESULTS_DIR = os.path.join(BACKEND_DIR, "results")


def normalize_url(url: str) -> str:
    if not url:
        return url
    return url.split('?')[0].rstrip('/')


def _is_scraper_browser(pinfo: dict) -> bool:
    name = pinfo['name'].lower() if pinfo['name'] else ''
    if not any(b in name for b in ['chrome', 'chromium']):
        return False
    cmdline = pinfo['cmdline'] if pinfo['cmdline'] else []
    cmdline_str = ' '.join(cmdline).lower()
    if 'playwright' in cmdline_str or 'crawl4ai' in cmdline_str:
        return True
    if any(flag in cmdline for flag in ['--disable-dev-shm-usage', '--no-sandbox']) and '--headless' in cmdline:
        has_user_profile = any(
            '--profile-directory' in str(arg) or
            ('--user-data-dir' in str(arg) and os.path.expanduser('~') in str(arg))
            for arg in cmdline
        )
        return not has_user_profile
    return False


def _cleanup_scraper_browsers(zombies_only: bool = False) -> int:
    if not PSUTIL_AVAILABLE:
        return 0
    try:
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pinfo = proc.info
                if not _is_scraper_browser(pinfo):
                    continue
                proc_obj = psutil.Process(pinfo['pid'])
                if zombies_only:
                    is_zombie = proc_obj.status() == psutil.STATUS_ZOMBIE
                    is_stuck = (proc_obj.cpu_percent(interval=0.1) == 0 and
                                proc_obj.create_time() < psutil.boot_time() + 300)
                    if not (is_zombie or is_stuck):
                        continue
                proc_obj.kill()
                killed_count += 1
                if not zombies_only:
                    try:
                        proc_obj.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        proc_obj.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                pass
        return killed_count
    except Exception as e:
        logger.error("[CLEANUP] Error: %s", e)
        return 0


def cleanup_zombie_browser_processes() -> int:
    return _cleanup_scraper_browsers(zombies_only=True)


def cleanup_all_scraper_browsers() -> int:
    return _cleanup_scraper_browsers(zombies_only=False)


def scrape_single_url(url: str) -> dict:
    process = None
    try:
        output_file = os.path.join(RESULTS_DIR, f"scrape_{uuid.uuid4().hex}.json")
        os.makedirs(RESULTS_DIR, exist_ok=True)

        cmd = ["python", SCRAPER_SCRIPT, "--url", url, "--output-file", output_file, "--timeout", "60"]

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=BACKEND_DIR,
            env=env,
            encoding="utf-8",
            errors="replace"
        )

        try:
            stdout, stderr = process.communicate(timeout=120)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            logger.warning("[SCRAPER] TIMEOUT: %s", url)
            if PSUTIL_AVAILABLE:
                try:
                    parent = psutil.Process(process.pid)
                    for child in parent.children(recursive=True):
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    parent.kill()
                    process.wait(timeout=5)
                except psutil.NoSuchProcess:
                    pass
            else:
                process.kill()
                process.wait(timeout=5)
            return {"success": False, "url": url, "error": "Scraper timed out"}
        finally:
            if process and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass

        if returncode != 0:
            logger.warning("[SCRAPER] FAILED rc=%d %s\nSTDERR: %s", returncode, url, stderr[-500:])
            return {"success": False, "url": url, "error": f"Scraper failed (exit {returncode})"}

        # Check for makro.json output file
        retailer_files = ["makro.json", "unknown.json"]
        output_dir = os.path.dirname(output_file)

        for fname in retailer_files:
            fpath = os.path.join(output_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        scraped_data = _json.load(f)
                    if isinstance(scraped_data, list):
                        for item in scraped_data:
                            if normalize_url(item.get('url', '')) == normalize_url(url) or item.get('url') == url:
                                item["source_url"] = url
                                logger.info("[SCRAPER] SUCCESS: %s -> %s", url, (item.get('name') or '')[:50])
                                try:
                                    os.remove(output_file)
                                except OSError:
                                    pass
                                return {"success": True, "url": url, "data": item}
                except Exception as e:
                    logger.error("[SCRAPER] Error reading %s: %s", fpath, e)

        # Fallback: check output file directly
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    scraped_data = _json.load(f)
                if isinstance(scraped_data, list) and scraped_data:
                    item = scraped_data[0]
                    item["source_url"] = url
                    os.remove(output_file)
                    return {"success": True, "url": url, "data": item}
            except Exception as e:
                logger.error("[SCRAPER] Error reading output file: %s", e)

        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception:
            pass

        return {"success": False, "url": url, "error": "Scraper output not found"}

    except Exception as e:
        if process and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass
        return {"success": False, "url": url, "error": str(e)}


# ---------------------------------------------------------------------------
# Scrape Endpoint
# ---------------------------------------------------------------------------

class ScrapeUrlRequest(BaseModel):
    urls: list[str]


@app.post("/api/scrape")
def scrape_urls(
    data: ScrapeUrlRequest,
    user: dict = Depends(get_current_user)
):
    """Scrape product URLs in parallel. Returns scraped data for each URL."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cleanup_zombie_browser_processes()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    results = []
    errors = []

    max_workers = min(len(data.urls), 4)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_single_url, url): url for url in data.urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result["success"]:
                    results.append(result["data"])
                else:
                    errors.append({"url": url, "error": result["error"]})
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

    cleanup_all_scraper_browsers()

    return {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors,
        "total_scraped": len(results),
        "total_errors": len(errors)
    }


# ---------------------------------------------------------------------------
# Manual Comparison Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/products/{sku}/rescrape")
def rescrape_product(
    sku: str,
    user: dict = Depends(get_current_user)
):
    """Rescrape verified Makro matches for a CFW product (looked up by SKU) and update their prices."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Resolve SKU → DB id
            cur.execute("SELECT id FROM products WHERE sku = %s AND retailer_id = 'cfw'", (sku,))
            cfw_row = cur.fetchone()
            if not cfw_row:
                raise HTTPException(status_code=404, detail=f"CFW product with SKU '{sku}' not found")
            product_id = cfw_row["id"]

            # Get all verified correct Makro matches for this product
            cur.execute("""
                SELECT mp.id, mp.sku, mp.url
                FROM product_matches pm
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE pm.cfw_product_id = %s
                  AND pm.is_verified = TRUE AND pm.is_same = TRUE
                  AND mp.url IS NOT NULL AND mp.url != ''
            """, (product_id,))
            makro_products = cur.fetchall()

    if not makro_products:
        return {"successful": 0, "failed": 0, "message": "No verified Makro matches with URLs to rescrape"}

    successful = 0
    failed = 0

    for mp in makro_products:
        result = scrape_single_url(mp["url"])
        if result["success"]:
            scraped = result["data"]
            new_price = scraped.get("current_price")
            new_step_prices = _json.dumps(scraped.get("step_prices") or [])
            new_image = (scraped.get("images") or [None])[0]

            with get_db() as conn:
                with conn.cursor() as cur:
                    # Update product price
                    cur.execute("""
                        UPDATE products SET
                            current_price = %s,
                            step_prices = %s,
                            image_url = COALESCE(%s, image_url),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (new_price, new_step_prices, new_image, mp["id"]))

                    # Insert price history
                    if new_price:
                        cur.execute("""
                            INSERT INTO price_history (product_id, price, step_prices)
                            VALUES (%s, %s, %s)
                        """, (mp["id"], new_price, new_step_prices))

                    conn.commit()
            successful += 1
        else:
            failed += 1

    return {
        "successful": successful,
        "failed": failed,
        "message": f"Updated {successful} Makro product{'s' if successful != 1 else ''}"
    }


@app.get("/api/products/sku/{sku}/matches")
def get_product_matches_by_sku(
    sku: str,
    user: dict = Depends(get_current_user)
):
    """Get existing verified Makro matches for a CFW product by SKU"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, current_price, url, image_url
                FROM products WHERE sku = %s AND retailer_id = 'cfw'
            """, (sku,))
            cfw_product = cur.fetchone()

            if not cfw_product:
                return {"found": False, "product": None, "matches": []}

            cur.execute("""
                SELECT
                    mp.id as makro_id,
                    mp.sku as makro_sku,
                    mp.name as makro_name,
                    mp.current_price as makro_price,
                    mp.url as makro_url,
                    mp.image_url as makro_image,
                    pm.match_id,
                    pm.is_verified,
                    pm.is_same
                FROM product_matches pm
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE pm.cfw_product_id = %s
                  AND pm.is_verified = TRUE AND pm.is_same = TRUE
                ORDER BY mp.name
            """, (cfw_product["id"],))

            matches = cur.fetchall()

            return {
                "found": True,
                "product": {
                    "id": cfw_product["id"],
                    "name": cfw_product["name"],
                    "price": float(cfw_product["current_price"]) if cfw_product["current_price"] else None,
                    "url": cfw_product["url"],
                    "image": cfw_product["image_url"],
                },
                "matches": [
                    {
                        "retailer_id": "makro",
                        "retailer_name": "Makro",
                        "product_id": m["makro_id"],
                        "sku": m["makro_sku"],
                        "name": m["makro_name"],
                        "price": float(m["makro_price"]) if m["makro_price"] else None,
                    }
                    for m in matches
                ]
            }


class ManualComparisonRequest(BaseModel):
    cfw_sku: str
    makro_url: str
    scraped_data: dict | None = None  # scraped Makro product data


@app.post("/api/comparison/manual")
def manual_comparison(
    data: ManualComparisonRequest,
    user: dict = Depends(get_current_user)
):
    """
    Manual comparison: given a CFW SKU + scraped Makro product data,
    upsert the Makro product and create a product_match entry.
    """
    scraped = data.scraped_data or {}

    with get_db() as conn:
        with conn.cursor() as cur:
            # Find CFW product
            cur.execute("""
                SELECT id, name, current_price FROM products
                WHERE sku = %s AND retailer_id = 'cfw'
            """, (data.cfw_sku,))
            cfw_product = cur.fetchone()
            if not cfw_product:
                raise HTTPException(status_code=404, detail=f"CFW product with SKU '{data.cfw_sku}' not found")

            # Upsert Makro product
            makro_sku = str(scraped.get('sku') or '').strip() or None
            makro_name = (scraped.get('name') or '').strip() or None
            makro_price = scraped.get('current_price')
            makro_brand = (scraped.get('brand') or '').strip() or None
            makro_image = (scraped.get('images') or [None])[0] if scraped.get('images') else None
            makro_step_prices = _json.dumps(scraped.get('step_prices') or [])

            if not makro_sku:
                raise HTTPException(status_code=400, detail="Scraped Makro product has no SKU")

            # Get or resolve Makro category
            makro_category_name = (scraped.get('category') or '').strip() or None
            makro_category_id = None
            if makro_category_name:
                cur.execute("""
                    SELECT category_id FROM categories
                    WHERE retailer_id = 'makro' AND category_name ILIKE %s
                    LIMIT 1
                """, (makro_category_name,))
                row = cur.fetchone()
                if row:
                    makro_category_id = row["category_id"]
                else:
                    # Insert new category
                    makro_category_id = makro_category_name.upper().replace(' ', '_')[:50]
                    cur.execute("""
                        INSERT INTO categories (retailer_id, category_id, category_name)
                        VALUES ('makro', %s, %s)
                        ON CONFLICT (retailer_id, category_id) DO NOTHING
                    """, (makro_category_id, makro_category_name))

            cur.execute("""
                INSERT INTO products (retailer_id, sku, name, brand, category_id, current_price, url, image_url, step_prices)
                VALUES ('makro', %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (retailer_id, sku) DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    category_id = EXCLUDED.category_id,
                    current_price = EXCLUDED.current_price,
                    url = EXCLUDED.url,
                    image_url = EXCLUDED.image_url,
                    step_prices = EXCLUDED.step_prices,
                    updated_at = NOW()
                RETURNING id
            """, (makro_sku, makro_name, makro_brand, makro_category_id,
                  makro_price, data.makro_url, makro_image, makro_step_prices))
            makro_product_id = cur.fetchone()["id"]

            # Block if this CFW product already has a verified correct match
            cur.execute("""
                SELECT pm.match_id, mp.name as makro_name
                FROM product_matches pm
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE pm.cfw_product_id = %s
                  AND pm.is_verified = TRUE AND pm.is_same = TRUE
                LIMIT 1
            """, (cfw_product["id"],))
            existing_verified = cur.fetchone()
            if existing_verified:
                raise HTTPException(
                    status_code=409,
                    detail=f"This CFW product already has a verified match: \"{existing_verified['makro_name']}\". Undo the existing match first before adding a new one."
                )

            # Create match entry — auto-verified as correct (manually added = user intent)
            cur.execute("""
                INSERT INTO product_matches (cfw_product_id, makro_product_id, match_score, is_verified, is_same, verified_at)
                VALUES (%s, %s, 100, TRUE, TRUE, NOW())
                ON CONFLICT (cfw_product_id, makro_product_id) DO UPDATE SET
                    is_verified = TRUE,
                    is_same = TRUE,
                    verified_at = NOW(),
                    updated_at = NOW()
                RETURNING match_id
            """, (cfw_product["id"], makro_product_id))
            match_id = cur.fetchone()["match_id"]

            conn.commit()

            return {
                "success": True,
                "cfw_product": {
                    "id": cfw_product["id"],
                    "name": cfw_product["name"],
                    "price": float(cfw_product["current_price"]) if cfw_product["current_price"] else None,
                },
                "makro_product": {
                    "id": makro_product_id,
                    "sku": makro_sku,
                    "name": makro_name,
                    "price": float(makro_price) if makro_price else None,
                    "url": data.makro_url,
                    "image": makro_image,
                },
                "match_id": match_id,
                "message": "Match created. Go to the product detail page to verify."
            }


# ---------------------------------------------------------------------------
# Server Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30,
        limit_max_requests=None,
    )
    server = uvicorn.Server(config)
    server.run()
