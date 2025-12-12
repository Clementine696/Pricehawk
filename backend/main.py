from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Response, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import secrets
import subprocess
import json
import os
import uuid
import tempfile
import csv
import io

from database import get_user_by_username, get_db

app = FastAPI(title="PriceHawk API")

# CORS configuration - supports multiple origins via environment variable
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
cors_origins_list = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Session settings
SESSION_EXPIRE_MINUTES = 30
COOKIE_NAME = "session_token"

# In-memory session store (users now in PostgreSQL)
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str


def get_current_user(session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME)) -> dict:
    """Validate session cookie and return user"""
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[session_token]
    if datetime.utcnow() > session["expires"]:
        del sessions[session_token]
        raise HTTPException(status_code=401, detail="Session expired")

    return session["user"]


@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response):
    """Login and set session cookie"""
    user = get_user_by_username(data.username)

    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create session token
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRE_MINUTES)

    sessions[token] = {
        "user": {"username": user["username"]},
        "expires": expires,
    }

    # Set HTTP-only cookie
    # For cross-origin (Vercel frontend -> Railway backend), need SameSite=None + Secure=True
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=SESSION_EXPIRE_MINUTES * 60,
        samesite="none" if is_production else "lax",
        secure=True if is_production else False,
    )

    return {"message": "Login successful", "username": user["username"]}


@app.post("/api/auth/logout")
def logout(response: Response, session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME)):
    """Logout and clear session cookie"""
    if session_token and session_token in sessions:
        del sessions[session_token]

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
def health():
    return {"status": "ok"}


# ============== Products API ==============

@app.get("/api/products")
def get_products(
    page: int = 1,
    pageSize: int = 10,
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    verified: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get Thai Watsadu products with price comparison across retailers"""
    offset = (page - 1) * pageSize

    with get_db() as conn:
        with conn.cursor() as cur:
            # Get Thai Watsadu retailer ID (base retailer)
            cur.execute("SELECT retailer_id FROM retailers WHERE name = 'Thai Watsadu'")
            base_retailer = cur.fetchone()
            if not base_retailer:
                return {"products": [], "total": 0, "retailers": [], "categories": [], "brands": []}
            base_retailer_id = base_retailer["retailer_id"]

            # Get all retailers for column headers
            cur.execute("SELECT retailer_id, name FROM retailers ORDER BY name")
            retailers = cur.fetchall()

            # Get unique categories for filters (filtered by selected brand for cascading)
            category_query = """
                SELECT DISTINCT category FROM products
                WHERE retailer_id = %s AND category IS NOT NULL
            """
            category_params = [base_retailer_id]
            if brand:
                category_query += " AND brand = %s"
                category_params.append(brand)
            category_query += " ORDER BY category"
            cur.execute(category_query, category_params)
            categories = [row["category"] for row in cur.fetchall()]

            # Get unique brands for filters (filtered by selected category for cascading)
            brand_query = """
                SELECT DISTINCT brand FROM products
                WHERE retailer_id = %s AND brand IS NOT NULL
            """
            brand_params = [base_retailer_id]
            if category:
                brand_query += " AND category = %s"
                brand_params.append(category)
            brand_query += " ORDER BY brand"
            cur.execute(brand_query, brand_params)
            brands = [row["brand"] for row in cur.fetchall()]

            # Build query for Thai Watsadu products
            query = """
                SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link
                FROM products p
                WHERE p.retailer_id = %s
            """
            params = [base_retailer_id]

            if search:
                query += " AND (p.name ILIKE %s OR p.sku ILIKE %s OR p.brand ILIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            if category:
                query += " AND p.category = %s"
                params.append(category)

            if brand:
                query += " AND p.brand = %s"
                params.append(brand)

            # Filter by verification status
            # Retailer is "done" if:
            #   1. Has at least one verified correct match (is_same = TRUE), OR
            #   2. ALL matches have been reviewed (even if all rejected)
            # Retailer "needs review" if: no verified correct match AND has unreviewed matches
            if verified == "true":
                # Products where all retailers are "done" (no retailer needs review)
                query += """ AND NOT EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id
                    AND NOT EXISTS (
                        SELECT 1 FROM product_matches pm2
                        WHERE pm2.base_product_id = pm.base_product_id
                          AND pm2.retailer_id = pm.retailer_id
                          AND pm2.verified_by_user = TRUE
                          AND pm2.is_same = TRUE
                    )
                    AND EXISTS (
                        SELECT 1 FROM product_matches pm3
                        WHERE pm3.base_product_id = pm.base_product_id
                          AND pm3.retailer_id = pm.retailer_id
                          AND pm3.verified_by_user = FALSE
                    )
                )"""
            elif verified == "false":
                # Products with at least one retailer that needs review
                query += """ AND EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id
                    AND NOT EXISTS (
                        SELECT 1 FROM product_matches pm2
                        WHERE pm2.base_product_id = pm.base_product_id
                          AND pm2.retailer_id = pm.retailer_id
                          AND pm2.verified_by_user = TRUE
                          AND pm2.is_same = TRUE
                    )
                    AND EXISTS (
                        SELECT 1 FROM product_matches pm3
                        WHERE pm3.base_product_id = pm.base_product_id
                          AND pm3.retailer_id = pm.retailer_id
                          AND pm3.verified_by_user = FALSE
                    )
                )"""

            # Get total count
            count_query = query.replace("SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link", "SELECT COUNT(*)")
            cur.execute(count_query, params)
            total = cur.fetchone()["count"]

            # Add pagination
            query += " ORDER BY p.product_id LIMIT %s OFFSET %s"
            params.extend([pageSize, offset])

            cur.execute(query, params)
            base_products = cur.fetchall()

            # For each base product, get matched prices from other retailers
            products = []
            for bp in base_products:
                product = {
                    "product_id": bp["product_id"],
                    "sku": bp["sku"],
                    "name": bp["name"],
                    "brand": bp["brand"],
                    "category": bp["category"],
                    "base_price": float(bp["current_price"]) if bp["current_price"] else None,
                    "base_link": bp["link"],
                    "retailer_prices": {},
                    "is_verified": True  # Default to True, will set to False if unverified matches exist
                }

                # Check if product has any retailer that needs review
                # Retailer is "done" if: has verified correct match OR all matches reviewed
                # Retailer "needs review" if: no verified correct match AND has unreviewed matches
                cur.execute("""
                    SELECT COUNT(*) as retailers_needing_review
                    FROM (
                        SELECT DISTINCT pm.retailer_id
                        FROM product_matches pm
                        WHERE pm.base_product_id = %s
                        AND NOT EXISTS (
                            SELECT 1 FROM product_matches pm2
                            WHERE pm2.base_product_id = pm.base_product_id
                              AND pm2.retailer_id = pm.retailer_id
                              AND pm2.verified_by_user = TRUE
                              AND pm2.is_same = TRUE
                        )
                        AND EXISTS (
                            SELECT 1 FROM product_matches pm3
                            WHERE pm3.base_product_id = pm.base_product_id
                              AND pm3.retailer_id = pm.retailer_id
                              AND pm3.verified_by_user = FALSE
                        )
                    ) as needs_review
                """, (bp["product_id"],))
                unverified = cur.fetchone()
                if unverified and unverified["retailers_needing_review"] > 0:
                    product["is_verified"] = False

                # Get verified correct matches from other retailers (one per retailer - the top match)
                cur.execute("""
                    SELECT DISTINCT ON (r.retailer_id)
                        r.name as retailer_name,
                        p2.current_price,
                        p2.link,
                        pm.is_same,
                        pm.confidence_score
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    JOIN retailers r ON p2.retailer_id = r.retailer_id
                    WHERE pm.base_product_id = %s
                      AND pm.verified_by_user = TRUE
                      AND pm.is_same = TRUE
                    ORDER BY r.retailer_id, pm.confidence_score DESC NULLS LAST
                """, (bp["product_id"],))

                matches = cur.fetchall()
                for match in matches:
                    product["retailer_prices"][match["retailer_name"]] = {
                        "price": float(match["current_price"]) if match["current_price"] else None,
                        "link": match["link"]
                    }

                # Determine status (cheapest, same, higher)
                if product["base_price"]:
                    all_prices = [product["base_price"]]
                    for rp in product["retailer_prices"].values():
                        if rp["price"]:
                            all_prices.append(rp["price"])

                    min_price = min(all_prices)
                    if product["base_price"] == min_price and len(all_prices) > 1:
                        if all(p == min_price for p in all_prices):
                            product["status"] = "same"
                        else:
                            product["status"] = "cheapest"
                    elif product["base_price"] > min_price:
                        product["status"] = "higher"
                    else:
                        product["status"] = None
                else:
                    product["status"] = None

                products.append(product)

            return {
                "products": products,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "retailers": retailers,
                "categories": categories,
                "brands": brands
            }


@app.get("/api/products/export")
def export_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    verified: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Export products to CSV with price comparison across retailers"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get Thai Watsadu retailer ID (base retailer)
            cur.execute("SELECT retailer_id FROM retailers WHERE name = 'Thai Watsadu'")
            base_retailer = cur.fetchone()
            if not base_retailer:
                # Return empty CSV if no base retailer
                output = io.StringIO()
                output.write('\ufeff')  # UTF-8 BOM for Excel
                writer = csv.writer(output)
                writer.writerow(['Product Name', 'SKU', 'Brand', 'Category', 'Thai Watsadu Price',
                                'HomePro Price', 'Do Home Price', 'Boonthavorn Price', 'Global House Price', 'Status'])
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=products_export.csv"}
                )
            base_retailer_id = base_retailer["retailer_id"]

            # Build query for Thai Watsadu products (same logic as /api/products but without pagination)
            query = """
                SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link
                FROM products p
                WHERE p.retailer_id = %s
            """
            params = [base_retailer_id]

            if search:
                query += " AND (p.name ILIKE %s OR p.sku ILIKE %s OR p.brand ILIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            if category:
                query += " AND p.category = %s"
                params.append(category)

            if brand:
                query += " AND p.brand = %s"
                params.append(brand)

            # Filter by verification status
            if verified == "true":
                query += """ AND NOT EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id AND pm.verified_by_user = FALSE
                )"""
            elif verified == "false":
                query += """ AND EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id AND pm.verified_by_user = FALSE
                )"""

            query += " ORDER BY p.product_id"

            cur.execute(query, params)
            base_products = cur.fetchall()

            # Prepare CSV output with UTF-8 BOM for Excel compatibility with Thai characters
            output = io.StringIO()
            output.write('\ufeff')  # UTF-8 BOM
            writer = csv.writer(output)

            # Write header row
            writer.writerow([
                'Product Name', 'SKU', 'Brand', 'Category', 'Thai Watsadu Price',
                'HomePro Price', 'Do Home Price', 'Boonthavorn Price', 'Global House Price', 'Status'
            ])

            # Define retailer order for columns (excluding Thai Watsadu which is base)
            retailer_order = ['HomePro', 'Do Home', 'Boonthavorn', 'Global House']

            # Process each product
            for bp in base_products:
                base_price = float(bp["current_price"]) if bp["current_price"] else None

                # Get verified correct matches from other retailers
                cur.execute("""
                    SELECT DISTINCT ON (r.retailer_id)
                        r.name as retailer_name,
                        p2.current_price
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    JOIN retailers r ON p2.retailer_id = r.retailer_id
                    WHERE pm.base_product_id = %s
                      AND pm.verified_by_user = TRUE
                      AND pm.is_same = TRUE
                    ORDER BY r.retailer_id, pm.confidence_score DESC NULLS LAST
                """, (bp["product_id"],))

                matches = cur.fetchall()
                retailer_prices = {}
                for match in matches:
                    retailer_prices[match["retailer_name"]] = float(match["current_price"]) if match["current_price"] else None

                # Determine status
                status = ''
                if base_price:
                    all_prices = [base_price]
                    for rp in retailer_prices.values():
                        if rp:
                            all_prices.append(rp)

                    min_price = min(all_prices)
                    if base_price == min_price and len(all_prices) > 1:
                        if all(p == min_price for p in all_prices):
                            status = 'same'
                        else:
                            status = 'cheapest'
                    elif base_price > min_price:
                        status = 'higher'

                # Build row
                row = [
                    bp["name"] or '',
                    bp["sku"] or '',
                    bp["brand"] or '',
                    bp["category"] or '',
                    base_price if base_price else '',
                ]

                # Add retailer prices in order
                for retailer in retailer_order:
                    price = retailer_prices.get(retailer)
                    row.append(price if price else '')

                row.append(status)
                writer.writerow(row)

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=products_export.csv"}
            )


@app.get("/api/products/{product_id}")
def get_product_detail(product_id: int, user: dict = Depends(get_current_user)):
    """Get product details with all matches for comparison view"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get base product
            cur.execute("""
                SELECT p.product_id, p.sku, p.name, p.brand, p.category,
                       p.current_price, p.original_price, p.link, p.image,
                       r.name as retailer_name, r.retailer_id
                FROM products p
                JOIN retailers r ON p.retailer_id = r.retailer_id
                WHERE p.product_id = %s
            """, (product_id,))
            product = cur.fetchone()

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            base_product = {
                "product_id": product["product_id"],
                "sku": product["sku"],
                "name": product["name"],
                "brand": product["brand"],
                "category": product["category"],
                "current_price": float(product["current_price"]) if product["current_price"] else None,
                "original_price": float(product["original_price"]) if product["original_price"] else None,
                "link": product["link"],
                "image": product["image"],
                "retailer_name": product["retailer_name"],
                "retailer_id": product["retailer_id"],
            }

            # Get all matches for this product
            cur.execute("""
                SELECT
                    pm.match_id,
                    pm.is_same,
                    pm.confidence_score,
                    pm.reason,
                    pm.match_type,
                    pm.verified_by_user,
                    p2.product_id as matched_product_id,
                    p2.sku as matched_sku,
                    p2.name as matched_name,
                    p2.brand as matched_brand,
                    p2.category as matched_category,
                    p2.current_price as matched_price,
                    p2.original_price as matched_original_price,
                    p2.link as matched_link,
                    p2.image as matched_image,
                    r.name as matched_retailer_name,
                    r.retailer_id as matched_retailer_id
                FROM product_matches pm
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                JOIN retailers r ON p2.retailer_id = r.retailer_id
                WHERE pm.base_product_id = %s
                ORDER BY r.name, pm.confidence_score DESC NULLS LAST
            """, (product_id,))

            matches_rows = cur.fetchall()

            # Group matches by retailer and apply "1 match per retailer" rule:
            # If a retailer has a verified correct match, only show that one match
            # Otherwise, show all matches for that retailer (so user can review)
            retailer_matches = {}  # retailer_id -> list of matches
            retailer_has_verified_correct = {}  # retailer_id -> bool

            for row in matches_rows:
                retailer_id = row["matched_retailer_id"]
                is_verified_correct = row["verified_by_user"] and row["is_same"]

                if retailer_id not in retailer_matches:
                    retailer_matches[retailer_id] = []
                    retailer_has_verified_correct[retailer_id] = False

                if is_verified_correct:
                    retailer_has_verified_correct[retailer_id] = True

                retailer_matches[retailer_id].append(row)

            # Build filtered matches list
            matches = []
            for retailer_id, rows in retailer_matches.items():
                if retailer_has_verified_correct[retailer_id]:
                    # Only include the verified correct match for this retailer
                    for row in rows:
                        if row["verified_by_user"] and row["is_same"]:
                            matches.append({
                                "match_id": row["match_id"],
                                "is_same": row["is_same"],
                                "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
                                "reason": row["reason"],
                                "match_type": row["match_type"],
                                "verified_by_user": row["verified_by_user"],
                                "product": {
                                    "product_id": row["matched_product_id"],
                                    "sku": row["matched_sku"],
                                    "name": row["matched_name"],
                                    "brand": row["matched_brand"],
                                    "category": row["matched_category"],
                                    "current_price": float(row["matched_price"]) if row["matched_price"] else None,
                                    "original_price": float(row["matched_original_price"]) if row["matched_original_price"] else None,
                                    "link": row["matched_link"],
                                    "image": row["matched_image"],
                                    "retailer_name": row["matched_retailer_name"],
                                    "retailer_id": row["matched_retailer_id"],
                                }
                            })
                            break  # Only one verified correct match per retailer
                else:
                    # No verified correct match yet, include all matches for review
                    for row in rows:
                        matches.append({
                            "match_id": row["match_id"],
                            "is_same": row["is_same"],
                            "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
                            "reason": row["reason"],
                            "match_type": row["match_type"],
                            "verified_by_user": row["verified_by_user"],
                            "product": {
                                "product_id": row["matched_product_id"],
                                "sku": row["matched_sku"],
                                "name": row["matched_name"],
                                "brand": row["matched_brand"],
                                "category": row["matched_category"],
                                "current_price": float(row["matched_price"]) if row["matched_price"] else None,
                                "original_price": float(row["matched_original_price"]) if row["matched_original_price"] else None,
                                "link": row["matched_link"],
                                "image": row["matched_image"],
                                "retailer_name": row["matched_retailer_name"],
                                "retailer_id": row["matched_retailer_id"],
                            }
                        })

            return {
                "product": base_product,
                "matches": matches,
                "total_matches": len(matches),
            }


@app.get("/api/dashboard/stats")
def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics - Thai Watsadu centric"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get Thai Watsadu retailer ID
            cur.execute("SELECT retailer_id FROM retailers WHERE name = 'Thai Watsadu'")
            twd = cur.fetchone()
            twd_id = twd["retailer_id"] if twd else None

            # Total products (Thai Watsadu only)
            cur.execute(
                "SELECT COUNT(*) as count FROM products WHERE retailer_id = %s",
                (twd_id,)
            )
            total_products = cur.fetchone()["count"]

            # Total retailers
            cur.execute("SELECT COUNT(*) as count FROM retailers")
            total_retailers = cur.fetchone()["count"]

            # Pending Reviews: TWD products that have at least 1 retailer needing review
            # Retailer is "done" if: has verified correct match OR all matches reviewed
            # Retailer "needs review" if: no verified correct match AND has unreviewed matches
            cur.execute("""
                SELECT COUNT(DISTINCT p.product_id) as count
                FROM products p
                WHERE p.retailer_id = %s
                AND EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id
                    AND NOT EXISTS (
                        SELECT 1 FROM product_matches pm2
                        WHERE pm2.base_product_id = pm.base_product_id
                          AND pm2.retailer_id = pm.retailer_id
                          AND pm2.verified_by_user = TRUE
                          AND pm2.is_same = TRUE
                    )
                    AND EXISTS (
                        SELECT 1 FROM product_matches pm3
                        WHERE pm3.base_product_id = pm.base_product_id
                          AND pm3.retailer_id = pm.retailer_id
                          AND pm3.verified_by_user = FALSE
                    )
                )
            """, (twd_id,))
            pending_reviews = cur.fetchone()["count"]

            # Product Matches: All TWD products that are NOT pending review
            # This includes: fully verified products + products with no matches at all
            total_matches = total_products - pending_reviews

            return {
                "total_products": total_products,
                "total_retailers": total_retailers,
                "total_matches": total_matches,
                "pending_reviews": pending_reviews
            }


@app.get("/api/retailers")
def get_retailers_with_stats(user: dict = Depends(get_current_user)):
    """Get all retailers with product counts"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    r.retailer_id,
                    r.name,
                    COUNT(p.product_id) as product_count
                FROM retailers r
                LEFT JOIN products p ON r.retailer_id = p.retailer_id
                GROUP BY r.retailer_id, r.name
                ORDER BY r.name
            """)
            retailers = cur.fetchall()

            return [dict(r) for r in retailers]


# ============== Matches API ==============

@app.get("/api/matches")
def get_matches(user: dict = Depends(get_current_user)):
    """Get product matches for review"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get matches, but exclude unverified matches if the base product
            # already has a verified correct match for the same retailer
            cur.execute("""
                SELECT
                    pm.match_id,
                    pm.is_same,
                    pm.confidence_score,
                    pm.reason,
                    pm.match_type,
                    pm.verified_by_user,
                    p1.product_id as base_product_id,
                    p1.name as base_name,
                    p1.sku as base_sku,
                    p1.current_price as base_price,
                    p1.image as base_image,
                    r1.name as base_retailer,
                    p2.product_id as candidate_product_id,
                    p2.name as candidate_name,
                    p2.sku as candidate_sku,
                    p2.current_price as candidate_price,
                    p2.image as candidate_image,
                    r2.name as candidate_retailer,
                    p2.retailer_id as candidate_retailer_id
                FROM product_matches pm
                JOIN products p1 ON pm.base_product_id = p1.product_id
                JOIN retailers r1 ON p1.retailer_id = r1.retailer_id
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                JOIN retailers r2 ON p2.retailer_id = r2.retailer_id
                WHERE
                    -- Include if: it's a verified match (show all verified matches)
                    pm.verified_by_user = TRUE
                    OR
                    -- Include if: it's unverified AND there's no verified correct match
                    -- for the same base product + candidate retailer
                    (pm.verified_by_user = FALSE AND NOT EXISTS (
                        SELECT 1
                        FROM product_matches pm2
                        JOIN products p3 ON pm2.candidate_product_id = p3.product_id
                        WHERE pm2.base_product_id = pm.base_product_id
                          AND p3.retailer_id = p2.retailer_id
                          AND pm2.verified_by_user = TRUE
                          AND pm2.is_same = TRUE
                    ))
                ORDER BY pm.verified_by_user ASC, pm.confidence_score DESC NULLS LAST
                LIMIT 100
            """)
            rows = cur.fetchall()

            matches = []
            for row in rows:
                matches.append({
                    "match_id": row["match_id"],
                    "is_same": row["is_same"],
                    "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
                    "reason": row["reason"],
                    "match_type": row["match_type"],
                    "verified_by_user": row["verified_by_user"],
                    "base_product": {
                        "product_id": row["base_product_id"],
                        "name": row["base_name"],
                        "sku": row["base_sku"],
                        "retailer_name": row["base_retailer"],
                        "current_price": float(row["base_price"]) if row["base_price"] else None,
                        "image": row["base_image"],
                    },
                    "candidate_product": {
                        "product_id": row["candidate_product_id"],
                        "name": row["candidate_name"],
                        "sku": row["candidate_sku"],
                        "retailer_name": row["candidate_retailer"],
                        "current_price": float(row["candidate_price"]) if row["candidate_price"] else None,
                        "image": row["candidate_image"],
                    },
                })

            return {"matches": matches}


class VerifyMatchRequest(BaseModel):
    is_same: bool


class ThaiWatsuduInput(BaseModel):
    sku: str
    url: str


class CompetitorInput(BaseModel):
    retailer: str
    url: str


class ScrapedProductData(BaseModel):
    name: str | None = None
    retailer: str | None = None
    url: str | None = None
    source_url: str | None = None
    current_price: float | None = None
    original_price: float | None = None
    brand: str | None = None
    sku: str | None = None
    category: str | None = None
    images: list[str] = []
    has_discount: bool = False
    discount_percent: float | None = None


class ManualComparisonRequest(BaseModel):
    thaiwatsadu: ThaiWatsuduInput
    competitors: list[CompetitorInput]
    scraped_data: list[ScrapedProductData] | None = None


@app.post("/api/matches/{match_id}/verify")
def verify_match(
    match_id: int,
    data: VerifyMatchRequest,
    user: dict = Depends(get_current_user)
):
    """Verify a product match"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE product_matches
                SET verified_by_user = TRUE,
                    verified_result = %s,
                    verified_at = NOW(),
                    is_same = %s
                WHERE match_id = %s
            """, (data.is_same, data.is_same, match_id))

            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Match not found")

            return {"message": "Match verified", "match_id": match_id, "is_same": data.is_same}


# ============== Scraping API ==============

# Backend directory (where this file is located)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# scraper-url is now inside backend folder
SCRAPER_SCRIPT = os.path.join(BACKEND_DIR, "scraper-url", "adws", "adw_ecommerce_product_scraper.py")
RESULTS_DIR = os.path.join(BACKEND_DIR, "results")


class ScrapeUrlRequest(BaseModel):
    urls: list[str]


class ScrapedProduct(BaseModel):
    name: str | None = None
    retailer: str | None = None
    url: str | None = None
    description: str | None = None
    product_key: str | None = None
    current_price: float | None = None
    original_price: float | None = None
    has_discount: bool = False
    discount_percent: float | None = None
    discount_amount: float | None = None
    brand: str | None = None
    model: str | None = None
    sku: str | None = None
    category: str | None = None
    volume: str | None = None
    dimensions: str | None = None
    material: str | None = None
    color: str | None = None
    images: list[str] = []
    scraped_at: str | None = None


def normalize_url(url: str) -> str:
    """Remove query string and trailing slashes for URL matching"""
    if not url:
        return url
    # Remove query string
    base_url = url.split('?')[0]
    # Remove trailing slashes
    return base_url.rstrip('/')


def scrape_single_url(url: str) -> dict:
    """
    Scrape a single URL and return result dict.
    Returns {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    try:
        # Generate unique output file for this scrape
        output_file = os.path.join(RESULTS_DIR, f"scrape_{uuid.uuid4().hex}.json")

        # Run the scraper script
        cmd = [
            "python",
            SCRAPER_SCRIPT,
            "--url", url,
            "--output-file", output_file
        ]

        print(f"\n  [PARALLEL] Scraping: {url}")

        # Execute scraper with timeout
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 120 second timeout per URL
            cwd=BACKEND_DIR,
            env=env,
            encoding="utf-8",
            errors="replace"
        )

        if process.returncode != 0:
            error_msg = process.stderr or process.stdout or 'Unknown error'
            print(f"  [PARALLEL] FAILED: {url} - {error_msg[:200]}")
            return {"success": False, "url": url, "error": f"Scraper failed: {error_msg[:500]}"}

        # Look for scraped data in retailer files
        output_dir = os.path.dirname(output_file)
        retailer_files = [
            "mega_home.json", "megahome.json",
            "thai_watsadu.json", "thaiwatsadu.json",
            "homepro.json", "home_pro.json",
            "do_home.json", "dohome.json",
            "boonthavorn.json",
            "global_house.json", "globalhouse.json",
            "unknown.json"
        ]

        for retailer_file in retailer_files:
            retailer_path = os.path.join(output_dir, retailer_file)
            if os.path.exists(retailer_path):
                try:
                    with open(retailer_path, 'r', encoding='utf-8') as f:
                        scraped_data = json.load(f)

                    if isinstance(scraped_data, list):
                        for product_data in scraped_data:
                            product_url = product_data.get('url', '')
                            if normalize_url(product_url) == normalize_url(url) or product_url == url:
                                product_data["source_url"] = url
                                print(f"  [PARALLEL] SUCCESS: {url} -> {product_data.get('name', 'N/A')[:40]}...")
                                # Clean up temp file
                                try:
                                    if os.path.exists(output_file):
                                        os.remove(output_file)
                                except:
                                    pass
                                return {"success": True, "url": url, "data": product_data}
                except Exception as e:
                    print(f"  [PARALLEL] Error reading {retailer_path}: {e}")

        # Check original output file as fallback
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                if isinstance(scraped_data, list) and len(scraped_data) > 0:
                    product_data = scraped_data[0]
                    product_data["source_url"] = url
                    print(f"  [PARALLEL] SUCCESS (fallback): {url}")
                    os.remove(output_file)
                    return {"success": True, "url": url, "data": product_data}
            except Exception as e:
                print(f"  [PARALLEL] Error reading output file: {e}")

        # Clean up
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except:
            pass

        return {"success": False, "url": url, "error": "Scraper output file not found or URL not matched"}

    except subprocess.TimeoutExpired:
        return {"success": False, "url": url, "error": "Scraper timed out (120s)"}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


@app.post("/api/scrape")
def scrape_urls(
    data: ScrapeUrlRequest,
    user: dict = Depends(get_current_user)
):
    """
    Scrape product data from URLs using the Python scraper script.
    Scrapes URLs in PARALLEL for faster execution.
    Returns scraped product data for each URL.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import shutil

    print(f"\n{'='*60}")
    print(f"=== DEBUG: /api/scrape called (PARALLEL MODE) ===")
    print(f"{'='*60}")
    print(f"  URLs to scrape: {data.urls}")
    print(f"  Total URLs: {len(data.urls)}")
    print(f"  BACKEND_DIR: {BACKEND_DIR}")
    print(f"  SCRAPER_SCRIPT: {SCRAPER_SCRIPT}")
    print(f"  Script exists: {os.path.exists(SCRAPER_SCRIPT)}")
    print(f"  Python executable: {shutil.which('python')}")

    results = []
    errors = []

    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Scrape all URLs in parallel using ThreadPoolExecutor
    # Max 4 workers to avoid overwhelming the system
    max_workers = min(len(data.urls), 4)
    print(f"  Starting parallel scraping with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scrape tasks
        future_to_url = {executor.submit(scrape_single_url, url): url for url in data.urls}

        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result["success"]:
                    results.append(result["data"])
                else:
                    errors.append({"url": result["url"], "error": result["error"]})
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

    response = {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors,
        "total_scraped": len(results),
        "total_errors": len(errors)
    }
    print(f"\n=== DEBUG: /api/scrape returning ===")
    print(f"  Total scraped: {len(results)}")
    print(f"  Total errors: {len(errors)}")
    if errors:
        print(f"  Errors: {errors}")
    return response


# ============== Manual Comparison API ==============

RETAILER_MAPPING = {
    "HomePro": "hp",
    "MegaHome": "mgh",
    "Do Home": "dh",
    "Boonthavorn": "btv",
    "Global House": "gbh",
    "Thai Watsadu": "twd",
}

RETAILER_NAMES = {
    "hp": "HomePro",
    "mgh": "MegaHome",
    "dh": "Do Home",
    "btv": "Boonthavorn",
    "gbh": "Global House",
}


@app.get("/api/products/sku/{sku}/matches")
def get_product_matches_by_sku(
    sku: str,
    user: dict = Depends(get_current_user)
):
    """Get existing verified matches for a Thai Watsadu product by SKU"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Find the TWD product
            cur.execute("""
                SELECT product_id, name, current_price, image, link
                FROM products WHERE sku = %s AND retailer_id = 'twd'
            """, (sku,))
            twd_product = cur.fetchone()

            if not twd_product:
                return {
                    "found": False,
                    "product": None,
                    "verified_retailers": [],
                    "matches": []
                }

            # Get verified correct matches grouped by retailer
            cur.execute("""
                SELECT
                    p2.retailer_id,
                    r.name as retailer_name,
                    p2.product_id,
                    p2.sku as matched_sku,
                    p2.name as matched_name,
                    p2.current_price as matched_price,
                    p2.image as matched_image,
                    p2.link as matched_link
                FROM product_matches pm
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                JOIN retailers r ON p2.retailer_id = r.retailer_id
                WHERE pm.base_product_id = %s
                  AND pm.verified_by_user = TRUE
                  AND pm.is_same = TRUE
                ORDER BY r.name
            """, (twd_product["product_id"],))

            matches = cur.fetchall()
            verified_retailers = list(set(m["retailer_id"] for m in matches))

            return {
                "found": True,
                "product": {
                    "product_id": twd_product["product_id"],
                    "name": twd_product["name"],
                    "price": float(twd_product["current_price"]) if twd_product["current_price"] else None,
                    "image": twd_product["image"],
                    "link": twd_product["link"],
                },
                "verified_retailers": verified_retailers,
                "matches": [
                    {
                        "retailer_id": m["retailer_id"],
                        "retailer_name": m["retailer_name"],
                        "product_id": m["product_id"],
                        "sku": m["matched_sku"],
                        "name": m["matched_name"],
                        "price": float(m["matched_price"]) if m["matched_price"] else None,
                        "image": m["matched_image"],
                        "link": m["matched_link"],
                    }
                    for m in matches
                ]
            }


@app.post("/api/comparison/manual")
def manual_comparison(
    data: ManualComparisonRequest,
    user: dict = Depends(get_current_user)
):
    """
    Manual comparison: Add Thai Watsadu product and compare with competitors.
    Creates products if they don't exist, creates matches, and returns comparison.
    Uses scraped_data if provided to populate product information.
    """
    # Debug: Log received scraped data
    print(f"\n=== DEBUG: Received scraped_data ===")
    print(f"scraped_data count: {len(data.scraped_data) if data.scraped_data else 0}")
    if data.scraped_data:
        for i, sd in enumerate(data.scraped_data):
            print(f"  [{i}] source_url: {sd.source_url}")
            print(f"      url: {sd.url}")
            print(f"      retailer: {sd.retailer}")
            print(f"      name: {sd.name}")
            print(f"      price: {sd.current_price}")
            print(f"      images: {len(sd.images) if sd.images else 0} images")

    # Build a lookup of scraped data by URL (with multiple key variations)
    scraped_lookup = {}
    scraped_by_retailer = {}  # Fallback lookup by retailer name
    if data.scraped_data:
        for scraped in data.scraped_data:
            # Match by both source_url and url, and their normalized versions
            if scraped.source_url:
                scraped_lookup[scraped.source_url] = scraped
                scraped_lookup[normalize_url(scraped.source_url)] = scraped
            if scraped.url:
                scraped_lookup[scraped.url] = scraped
                scraped_lookup[normalize_url(scraped.url)] = scraped
            # Also index by retailer name (normalize to handle variations like "Mega Home" vs "MegaHome")
            if scraped.retailer:
                retailer_key = scraped.retailer.lower().replace(" ", "")
                scraped_by_retailer[retailer_key] = scraped

    print(f"\n=== DEBUG: Lookup tables ===")
    print(f"scraped_lookup keys: {list(scraped_lookup.keys())}")
    print(f"scraped_by_retailer keys: {list(scraped_by_retailer.keys())}")

    with get_db() as conn:
        with conn.cursor() as cur:
            results = []

            # Get or create Thai Watsadu retailer
            cur.execute("SELECT retailer_id FROM retailers WHERE retailer_id = 'twd'")
            twd_retailer = cur.fetchone()
            if not twd_retailer:
                cur.execute("""
                    INSERT INTO retailers (retailer_id, name, website)
                    VALUES ('twd', 'Thai Watsadu', 'https://www.thaiwatsadu.com')
                    ON CONFLICT (retailer_id) DO NOTHING
                """)

            # Check if we have scraped data for Thai Watsadu
            twd_scraped = scraped_lookup.get(data.thaiwatsadu.url) or scraped_lookup.get(normalize_url(data.thaiwatsadu.url))
            twd_sku = data.thaiwatsadu.sku
            if twd_scraped and twd_scraped.sku:
                twd_sku = twd_scraped.sku

            # Get or create Thai Watsadu product
            cur.execute("""
                SELECT product_id, name, current_price, original_price, image, link, brand, category
                FROM products WHERE sku = %s AND retailer_id = 'twd'
            """, (twd_sku,))
            twd_product = cur.fetchone()

            if not twd_product:
                # Create product using scraped data if available
                if twd_scraped:
                    cur.execute("""
                        INSERT INTO products (sku, retailer_id, name, link, current_price, original_price, brand, category, image)
                        VALUES (%s, 'twd', %s, %s, %s, %s, %s, %s, %s)
                        RETURNING product_id, name, current_price, original_price, image, link, brand, category
                    """, (
                        twd_sku,
                        twd_scraped.name or f"Thai Watsadu Product {twd_sku}",
                        data.thaiwatsadu.url,
                        twd_scraped.current_price,
                        twd_scraped.original_price,
                        twd_scraped.brand,
                        twd_scraped.category,
                        twd_scraped.images[0] if twd_scraped.images else None
                    ))
                else:
                    cur.execute("""
                        INSERT INTO products (sku, retailer_id, name, link, current_price)
                        VALUES (%s, 'twd', %s, %s, NULL)
                        RETURNING product_id, name, current_price, original_price, image, link, brand, category
                    """, (twd_sku, f"Thai Watsadu Product {twd_sku}", data.thaiwatsadu.url))
                twd_product = cur.fetchone()
            else:
                # Update existing product with scraped data if available
                if twd_scraped:
                    cur.execute("""
                        UPDATE products SET
                            name = COALESCE(%s, name),
                            current_price = COALESCE(%s, current_price),
                            original_price = COALESCE(%s, original_price),
                            brand = COALESCE(%s, brand),
                            category = COALESCE(%s, category),
                            image = COALESCE(%s, image),
                            link = COALESCE(%s, link)
                        WHERE product_id = %s
                        RETURNING product_id, name, current_price, original_price, image, link, brand, category
                    """, (
                        twd_scraped.name,
                        twd_scraped.current_price,
                        twd_scraped.original_price,
                        twd_scraped.brand,
                        twd_scraped.category,
                        twd_scraped.images[0] if twd_scraped.images else None,
                        data.thaiwatsadu.url,
                        twd_product["product_id"]
                    ))
                    twd_product = cur.fetchone()

            base_product = {
                "product_id": twd_product["product_id"],
                "name": twd_product["name"] or f"Thai Watsadu Product {twd_sku}",
                "sku": twd_sku,
                "price": float(twd_product["current_price"]) if twd_product["current_price"] else None,
                "original_price": float(twd_product["original_price"]) if twd_product.get("original_price") else None,
                "retailer": "Thai Watsadu",
                "url": twd_product["link"] or data.thaiwatsadu.url,
                "image": twd_product["image"],
                "brand": twd_product.get("brand"),
                "category": twd_product.get("category"),
            }

            results.append(base_product)

            # Process each competitor
            for comp in data.competitors:
                print(f"\n=== DEBUG: Processing competitor ===")
                print(f"  comp.retailer: {comp.retailer}")
                print(f"  comp.url: {comp.url}")
                print(f"  normalized url: {normalize_url(comp.url)}")
                print(f"  retailer lookup key: {comp.retailer.lower().replace(' ', '')}")

                retailer_id = RETAILER_MAPPING.get(comp.retailer)
                if not retailer_id:
                    print(f"  ERROR: No retailer_id mapping for {comp.retailer}")
                    continue

                # Check if there's already a verified correct match for this retailer
                cur.execute("""
                    SELECT pm.match_id, p2.product_id, p2.name, p2.sku, p2.current_price, p2.image, p2.link, p2.brand, p2.category
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    WHERE pm.base_product_id = %s
                      AND p2.retailer_id = %s
                      AND pm.verified_by_user = TRUE
                      AND pm.is_same = TRUE
                    LIMIT 1
                """, (twd_product["product_id"], retailer_id))
                existing_verified = cur.fetchone()

                if existing_verified:
                    # Skip this retailer - already has a verified correct match
                    results.append({
                        "product_id": existing_verified["product_id"],
                        "name": existing_verified["name"] or f"{comp.retailer} Product",
                        "sku": existing_verified["sku"],
                        "price": float(existing_verified["current_price"]) if existing_verified["current_price"] else None,
                        "retailer": comp.retailer,
                        "url": existing_verified["link"] or comp.url,
                        "image": existing_verified["image"],
                        "brand": existing_verified.get("brand"),
                        "category": existing_verified.get("category"),
                        "already_verified": True,
                    })
                    continue

                # Check if we have scraped data for this competitor URL
                # Try URL match first, then fall back to retailer name match
                url_match = scraped_lookup.get(comp.url)
                normalized_url_match = scraped_lookup.get(normalize_url(comp.url))
                retailer_match = scraped_by_retailer.get(comp.retailer.lower().replace(" ", ""))

                print(f"  URL match: {url_match is not None}")
                print(f"  Normalized URL match: {normalized_url_match is not None}")
                print(f"  Retailer match: {retailer_match is not None}")
                if retailer_match:
                    print(f"    -> retailer match name: {retailer_match.name}")
                    print(f"    -> retailer match price: {retailer_match.current_price}")

                comp_scraped = url_match or normalized_url_match or retailer_match
                print(f"  Final comp_scraped: {comp_scraped is not None}")

                # Ensure retailer exists
                try:
                    domain = urlparse(comp.url).netloc
                except:
                    domain = None

                cur.execute("""
                    INSERT INTO retailers (retailer_id, name, domain)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (retailer_id) DO NOTHING
                """, (retailer_id, comp.retailer, domain))

                # Get SKU from scraped data or extract from URL
                if comp_scraped and comp_scraped.sku:
                    comp_sku = comp_scraped.sku
                else:
                    comp_sku = comp.url.split('/')[-1].split('?')[0] or f"manual_{retailer_id}_{twd_product['product_id']}"

                # Get or create competitor product
                cur.execute("""
                    SELECT product_id, name, current_price, original_price, image, link, brand, category
                    FROM products WHERE link = %s AND retailer_id = %s
                """, (comp.url, retailer_id))
                comp_product = cur.fetchone()

                if not comp_product:
                    # Also try to find by SKU
                    cur.execute("""
                        SELECT product_id, name, current_price, original_price, image, link, brand, category
                        FROM products WHERE sku = %s AND retailer_id = %s
                    """, (comp_sku, retailer_id))
                    comp_product = cur.fetchone()

                if not comp_product:
                    # Create product using scraped data if available
                    if comp_scraped:
                        cur.execute("""
                            INSERT INTO products (sku, retailer_id, name, link, current_price, original_price, brand, category, image)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING product_id, name, current_price, original_price, image, link, brand, category
                        """, (
                            comp_sku,
                            retailer_id,
                            comp_scraped.name or f"{comp.retailer} Product",
                            comp.url,
                            comp_scraped.current_price,
                            comp_scraped.original_price,
                            comp_scraped.brand,
                            comp_scraped.category,
                            comp_scraped.images[0] if comp_scraped.images else None
                        ))
                    else:
                        cur.execute("""
                            INSERT INTO products (sku, retailer_id, name, link, current_price)
                            VALUES (%s, %s, %s, %s, NULL)
                            RETURNING product_id, name, current_price, original_price, image, link, brand, category
                        """, (comp_sku, retailer_id, f"{comp.retailer} Product", comp.url))
                    comp_product = cur.fetchone()
                else:
                    # Update existing product with scraped data if available
                    if comp_scraped:
                        cur.execute("""
                            UPDATE products SET
                                name = COALESCE(%s, name),
                                current_price = COALESCE(%s, current_price),
                                original_price = COALESCE(%s, original_price),
                                brand = COALESCE(%s, brand),
                                category = COALESCE(%s, category),
                                image = COALESCE(%s, image)
                            WHERE product_id = %s
                            RETURNING product_id, name, current_price, original_price, image, link, brand, category
                        """, (
                            comp_scraped.name,
                            comp_scraped.current_price,
                            comp_scraped.original_price,
                            comp_scraped.brand,
                            comp_scraped.category,
                            comp_scraped.images[0] if comp_scraped.images else None,
                            comp_product["product_id"]
                        ))
                        comp_product = cur.fetchone()

                # Create product match - manual matches are auto-verified as correct
                cur.execute("""
                    INSERT INTO product_matches (base_product_id, candidate_product_id, retailer_id, match_type, verified_by_user, is_same)
                    VALUES (%s, %s, %s, 'manual', TRUE, TRUE)
                    ON CONFLICT (base_product_id, candidate_product_id) DO UPDATE SET match_type = 'manual', verified_by_user = TRUE, is_same = TRUE
                    RETURNING match_id
                """, (twd_product["product_id"], comp_product["product_id"], retailer_id))

                results.append({
                    "product_id": comp_product["product_id"],
                    "name": comp_product["name"] or f"{comp.retailer} Product",
                    "sku": comp_sku,
                    "price": float(comp_product["current_price"]) if comp_product["current_price"] else None,
                    "original_price": float(comp_product["original_price"]) if comp_product.get("original_price") else None,
                    "retailer": comp.retailer,
                    "url": comp_product["link"] or comp.url,
                    "image": comp_product["image"],
                    "brand": comp_product.get("brand"),
                    "category": comp_product.get("category"),
                })

            # Find lowest price for comparison
            prices = [r["price"] for r in results if r["price"] is not None]
            lowest_price = min(prices) if prices else None

            for r in results:
                if r["price"] is not None and lowest_price is not None:
                    r["is_lowest"] = r["price"] == lowest_price
                    if lowest_price > 0:
                        r["difference_percent"] = round(((r["price"] - lowest_price) / lowest_price) * 100, 1)
                    else:
                        r["difference_percent"] = 0
                else:
                    r["is_lowest"] = False
                    r["difference_percent"] = None

            return {
                "success": True,
                "base_sku": data.thaiwatsadu.sku,
                "twd_product_id": twd_product["product_id"],
                "results": results,
                "lowest_price": lowest_price,
            }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
