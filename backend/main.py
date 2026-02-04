from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Response, Depends, Cookie, Header, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import secrets
import subprocess
import json
import os
import uuid
import tempfile
import io
import logging
import signal
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available - zombie process cleanup disabled")
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
import pandas as pd

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
SESSION_EXPIRE_MINUTES = 10080  # 7 days
COOKIE_NAME = "session_token"

# In-memory session store (users now in PostgreSQL)
sessions: dict[str, dict] = {}

# Helper function to get client IP
def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or direct connection"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


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
    token = None

    # First, try Authorization header (Bearer token)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix

    # Fall back to cookie
    if not token:
        token = session_token

    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[token]
    if datetime.utcnow() > session["expires"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")

    # Update last activity time for session tracking
    session["last_activity"] = datetime.utcnow()

    return session["user"]


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

    # Log successful login
    logger.info(
        f"LOGIN | User: {user['username']} | IP: {get_client_ip(request)} | "
        f"Time: {login_time.isoformat()} | User-Agent: {request.headers.get('User-Agent', 'unknown')}"
    )

    # Set HTTP-only cookie
    # For cross-origin (Vercel frontend -> Railway backend), need SameSite=None + Secure=True
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")

    # Build cookie manually to support Partitioned attribute for cross-site cookies
    if is_production:
        # Cross-origin production: SameSite=None, Secure, Partitioned
        cookie_value = f"{COOKIE_NAME}={token}; HttpOnly; Secure; SameSite=None; Partitioned; Max-Age={SESSION_EXPIRE_MINUTES * 60}; Path=/"
        response.headers.append("Set-Cookie", cookie_value)
    else:
        # Local development: standard cookie
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
    # Try Authorization header first
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        token = session_token

    if token and token in sessions:
        session = sessions[token]
        username = session["user"]["username"]
        login_time = session.get("login_time", datetime.utcnow())
        logout_time = datetime.utcnow()
        session_duration = (logout_time - login_time).total_seconds()
        
        # Log logout with session duration
        logger.info(
            f"LOGOUT | User: {username} | IP: {get_client_ip(request)} | "
            f"Login: {login_time.isoformat()} | Logout: {logout_time.isoformat()} | "
            f"Duration: {session_duration:.0f} seconds ({session_duration/60:.1f} minutes)"
        )
        
        del sessions[token]

    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    response.delete_cookie(
        key=COOKIE_NAME,
        samesite="none" if is_production else "lax",
        secure=True if is_production else False,
    )
    return {"message": "Logged out"}


@app.post("/api/auth/page-unload")
def page_unload(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    authorization: Optional[str] = Header(None)
):
    """Track when user closes page/browser tab (called via sendBeacon)"""
    # Try Authorization header first
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        token = session_token

    if token and token in sessions:
        session = sessions[token]
        username = session["user"]["username"]
        login_time = session.get("login_time", datetime.utcnow())
        unload_time = datetime.utcnow()
        session_duration = (unload_time - login_time).total_seconds()
        
        # Log page unload
        logger.info(
            f"PAGE_UNLOAD | User: {username} | IP: {get_client_ip(request)} | "
            f"Login: {login_time.isoformat()} | Unload: {unload_time.isoformat()} | "
            f"Duration: {session_duration:.0f} seconds ({session_duration/60:.1f} minutes)"
        )
        
        # Update last activity time (don't delete session - they might come back)
        session["last_activity"] = unload_time
    
    return {"message": "Page unload tracked"}


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return user


@app.get("/api/auth/sessions")
def get_active_sessions(user: dict = Depends(get_current_user)):
    """Get all active sessions (admin only - shows all logged-in users)"""
    active_sessions = []
    current_time = datetime.utcnow()
    
    for token, session in sessions.items():
        if current_time <= session["expires"]:
            login_time = session.get("login_time", current_time)
            last_activity = session.get("last_activity", login_time)
            session_duration = (current_time - login_time).total_seconds()
            idle_time = (current_time - last_activity).total_seconds()
            
            active_sessions.append({
                "username": session["user"]["username"],
                "login_time": login_time.isoformat(),
                "last_activity": last_activity.isoformat(),
                "session_duration_seconds": int(session_duration),
                "session_duration_minutes": round(session_duration / 60, 1),
                "idle_time_seconds": int(idle_time),
                "ip_address": session.get("ip_address", "unknown"),
                "user_agent": session.get("user_agent", "unknown"),
            })
    
    return {
        "active_sessions": active_sessions,
        "total_active": len(active_sessions),
    }


# ============== Watchlist API (Global Category Groups) ==============

# ============== Watchlist SKU Groups ==============

@app.get("/api/watchlist/sku-groups")
def get_sku_watchlist_groups(user: dict = Depends(get_current_user)):
    """Get all SKU-based watchlist groups with their products"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get all groups sorted alphabetically
            cur.execute("""
                SELECT group_id, name, created_at, updated_at
                FROM watchlist_sku_groups
                ORDER BY name ASC
            """)
            groups = cur.fetchall()
            
            result = []
            for group in groups:
                # Get products for this group with product details
                cur.execute("""
                    SELECT 
                        wsgp.sku,
                        wsgp.added_at,
                        p.name,
                        p.image,
                        p.current_price,
                        p.category
                    FROM watchlist_sku_group_products wsgp
                    LEFT JOIN products p ON wsgp.sku = p.sku AND p.retailer_id = 'twd'
                    WHERE wsgp.group_id = %s
                    ORDER BY wsgp.added_at DESC
                """, (group["group_id"],))
                products = cur.fetchall()
                
                result.append({
                    "group_id": group["group_id"],
                    "name": group["name"],
                    "created_at": group["created_at"].isoformat() if group["created_at"] else None,
                    "updated_at": group["updated_at"].isoformat() if group["updated_at"] else None,
                    "products": [
                        {
                            "sku": p["sku"],
                            "name": p["name"],
                            "image_url": p["image"],
                            "price": float(p["current_price"]) if p["current_price"] else None,
                            "category": p["category"],
                            "added_at": p["added_at"].isoformat() if p["added_at"] else None
                        }
                        for p in products
                    ],
                    "product_count": len(products)
                })
            
            return {"groups": result, "total": len(result)}


@app.post("/api/watchlist/sku-groups")
def create_sku_watchlist_group(data: dict, user: dict = Depends(get_current_user)):
    """Create a new SKU-based watchlist group"""
    name = data.get("name", "").strip()
    
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO watchlist_sku_groups (name)
                    VALUES (%s)
                    RETURNING group_id, name, created_at, updated_at
                """, (name,))
                group = cur.fetchone()
                conn.commit()
                
                return {
                    "group_id": group["group_id"],
                    "name": group["name"],
                    "created_at": group["created_at"].isoformat() if group["created_at"] else None,
                    "updated_at": group["updated_at"].isoformat() if group["updated_at"] else None,
                    "products": [],
                    "product_count": 0
                }
            except Exception as e:
                conn.rollback()
                if "unique constraint" in str(e).lower():
                    raise HTTPException(status_code=400, detail="Group name already exists")
                raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/watchlist/sku-groups/{group_id}")
def delete_sku_watchlist_group(group_id: int, user: dict = Depends(get_current_user)):
    """Delete a SKU-based watchlist group"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM watchlist_sku_groups WHERE group_id = %s", (group_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Group not found")
            conn.commit()
            return {"message": "Group deleted successfully"}


@app.post("/api/watchlist/sku-groups/{group_id}/products")
def add_product_to_sku_group(group_id: int, data: dict, user: dict = Depends(get_current_user)):
    """Add a product (by SKU) to a SKU-based watchlist group"""
    sku = data.get("sku", "").strip()
    
    if not sku:
        raise HTTPException(status_code=400, detail="SKU is required")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if group exists
            cur.execute("SELECT group_id FROM watchlist_sku_groups WHERE group_id = %s", (group_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Group not found")
            
            # Check if product exists
            cur.execute("""
                SELECT sku, name FROM products 
                WHERE sku = %s AND retailer_id = 'twd'
                LIMIT 1
            """, (sku,))
            product = cur.fetchone()
            if not product:
                raise HTTPException(status_code=400, detail="Product not found")
            
            try:
                # Add product to group
                cur.execute("""
                    INSERT INTO watchlist_sku_group_products (group_id, sku)
                    VALUES (%s, %s)
                    ON CONFLICT (group_id, sku) DO NOTHING
                """, (group_id, sku))
                
                # Update group's updated_at timestamp
                cur.execute("""
                    UPDATE watchlist_sku_groups
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE group_id = %s
                """, (group_id,))
                
                conn.commit()
                return {"message": "Product added to group successfully", "sku": sku}
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchlist/sku-groups/test-upload")
async def test_file_upload(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Test endpoint to verify file upload is working"""
    print(f"\n{'='*60}")
    print(f"TEST UPLOAD ENDPOINT HIT")
    print(f"{'='*60}")

    try:
        print(f"User: {user.get('username', 'Unknown')}")
        print(f"File received: {file.filename}")
        print(f"Content type: {file.content_type}")

        # Read file to get size
        contents = await file.read()
        file_size = len(contents)

        print(f"File size: {file_size} bytes ({file_size / 1024:.2f} KB, {file_size / 1024 / 1024:.2f} MB)")

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 2),
            "size_mb": round(file_size / 1024 / 1024, 2),
            "message": "File upload test successful"
        }
    except Exception as e:
        print(f"ERROR in test upload: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Test upload failed: {str(e)}")


@app.options("/api/watchlist/sku-groups/import-excel")
async def import_excel_options():
    """Handle OPTIONS request for CORS pre-flight"""
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })


@app.post("/api/watchlist/sku-groups/import-excel")
async def import_excel_to_sku_groups(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Import Excel file to create SKU watchlist groups based on S-dept column"""

    print(f"\n{'='*60}")
    print(f"ENDPOINT HIT: /api/watchlist/sku-groups/import-excel")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"User: {user.get('username', 'Unknown')} (ID: {user.get('user_id', 'N/A')})")
    print(f"{'='*60}")

    # Check if file was received
    if not file:
        print(f"ERROR: No file received in request")
        raise HTTPException(status_code=400, detail="No file provided")

    print(f"File object received successfully")
    print(f"File content_type: {file.content_type}")
    print(f"File filename: {file.filename}")

    if not file.filename.endswith(('.xlsx', '.xls')):
        print(f"ERROR: Invalid file type - {file.filename}")
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    try:
        # Read Excel file
        print(f"Reading Excel file...")
        contents = await file.read()
        file_size = len(contents)
        print(f"File size: {file_size} bytes ({file_size / 1024:.2f} KB)")

        print(f"Parsing Excel with pandas...")
        df = pd.read_excel(io.BytesIO(contents))
        print(f"Excel parsed successfully. Total rows: {len(df)}, Columns: {list(df.columns)}")
        
        # Validate required columns
        print(f"Validating columns...")
        required_columns = ['SKU_Number', 'S-dept']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Expected columns: SKU_Number, PRNAME, Brand, S-dept, Dept"
            )
        print(f"Column validation passed")

        # Remove rows with missing SKU_Number or S-dept
        rows_before = len(df)
        df = df.dropna(subset=['SKU_Number', 'S-dept'])
        rows_after = len(df)
        print(f"Removed {rows_before - rows_after} rows with missing SKU_Number or S-dept")

        if len(df) == 0:
            print(f"ERROR: No valid data after cleanup")
            raise HTTPException(status_code=400, detail="No valid data found in Excel file")

        # Convert SKU_Number to string and clean
        print(f"Converting and cleaning data...")
        df['SKU_Number'] = df['SKU_Number'].astype(str).str.strip()
        df['S-dept'] = df['S-dept'].astype(str).str.strip()
        print(f"Data conversion complete")

        # Group by S-dept
        print(f"Grouping by S-dept...")
        grouped = df.groupby('S-dept')['SKU_Number'].apply(list).to_dict()
        print(f"Found {len(grouped)} unique S-dept groups")
        
        results = {
            "groups_created": [],
            "groups_updated": [],
            "skus_added": {},
            "skus_not_found": {},
            "total_rows": len(df),
            "groups_processed": len(grouped)
        }

        print(f"------------------------------------------------------------")
        print(f"Starting database operations...")
        print(f"Opening database connection...")

        with get_db() as conn:
            with conn.cursor() as cur:
                print(f"Database connection established successfully")
                print(f"Processing {len(grouped)} S-dept groups...")
                print(f"------------------------------------------------------------")

                group_counter = 0
                for s_dept, skus in grouped.items():
                    group_counter += 1
                    print(f"\n[GROUP {group_counter}/{len(grouped)}] Processing S-dept: '{s_dept}'")

                    # Remove duplicates
                    skus_before_dedup = len(skus)
                    skus = list(set(skus))
                    print(f"  - SKUs in this group: {len(skus)} (removed {skus_before_dedup - len(skus)} duplicates)")

                    # Use S-dept name directly as group name
                    group_name = s_dept

                    # Check if group exists
                    print(f"  - Checking if group '{group_name}' exists...")
                    cur.execute("""
                        SELECT group_id FROM watchlist_sku_groups WHERE name = %s
                    """, (group_name,))
                    existing_group = cur.fetchone()

                    if existing_group:
                        group_id = existing_group['group_id']
                        print(f"  - Group EXISTS (group_id: {group_id}), will UPDATE")
                        results["groups_updated"].append(s_dept)
                    else:
                        # Create new group
                        print(f"  - Group DOES NOT EXIST, creating new group...")
                        try:
                            cur.execute("""
                                INSERT INTO watchlist_sku_groups (name)
                                VALUES (%s)
                                RETURNING group_id
                            """, (group_name,))
                            group_id = cur.fetchone()['group_id']
                            print(f"  - Group CREATED successfully (group_id: {group_id})")
                            results["groups_created"].append(s_dept)
                        except Exception as e:
                            print(f"  - ERROR creating group '{s_dept}': {e}")
                            print(f"  - Skipping this group due to error")
                            continue

                    # Verify which SKUs exist in products table
                    print(f"  - Validating {len(skus)} SKUs against products table...")
                    cur.execute("""
                        SELECT DISTINCT sku FROM products
                        WHERE sku = ANY(%s) AND retailer_id = 'twd'
                    """, (skus,))
                    valid_skus = [row['sku'] for row in cur.fetchall()]
                    invalid_skus = [sku for sku in skus if sku not in valid_skus]

                    print(f"  - Validation complete: {len(valid_skus)} valid, {len(invalid_skus)} not found in products")
                    if invalid_skus and len(invalid_skus) <= 10:
                        print(f"  - Invalid SKUs: {invalid_skus}")
                    elif invalid_skus:
                        print(f"  - Invalid SKUs (first 10): {invalid_skus[:10]}")

                    added_count = 0
                    already_exists_count = 0

                    # Add valid SKUs to group
                    print(f"  - Adding {len(valid_skus)} valid SKUs to group...")
                    for sku in valid_skus:
                        try:
                            cur.execute("""
                                INSERT INTO watchlist_sku_group_products (group_id, sku)
                                VALUES (%s, %s)
                                ON CONFLICT (group_id, sku) DO NOTHING
                            """, (group_id, sku))
                            if cur.rowcount > 0:
                                added_count += 1
                            else:
                                already_exists_count += 1
                        except Exception as e:
                            print(f"  - ERROR adding SKU '{sku}' to group '{s_dept}': {e}")
                            continue

                    print(f"  - SKU insertion complete: {added_count} new, {already_exists_count} already existed")

                    # Update group timestamp
                    print(f"  - Updating group timestamp...")
                    cur.execute("""
                        UPDATE watchlist_sku_groups
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE group_id = %s
                    """, (group_id,))
                    print(f"  - Group timestamp updated")

                    results["skus_added"][s_dept] = {
                        "added": added_count,
                        "already_exists": already_exists_count,
                        "total_valid": len(valid_skus)
                    }

                    if invalid_skus:
                        results["skus_not_found"][s_dept] = invalid_skus

                print(f"\n------------------------------------------------------------")
                print(f"All groups processed, committing transaction...")
                conn.commit()
                print(f"Transaction committed successfully")

        print(f"\n============================================================")
        print(f"=== EXCEL IMPORT COMPLETED SUCCESSFULLY ===")
        print(f"============================================================")
        print(f"Summary:")
        print(f"  - Total rows processed: {results['total_rows']}")
        print(f"  - S-dept groups processed: {results['groups_processed']}")
        print(f"  - Groups created: {len(results['groups_created'])}")
        print(f"  - Groups updated: {len(results['groups_updated'])}")

        total_added = sum(info['added'] for info in results['skus_added'].values())
        total_already_exists = sum(info['already_exists'] for info in results['skus_added'].values())
        total_not_found = sum(len(skus) for skus in results['skus_not_found'].values())

        print(f"  - SKUs added: {total_added}")
        print(f"  - SKUs already existed: {total_already_exists}")
        print(f"  - SKUs not found in products: {total_not_found}")
        print(f"============================================================")

        return results

    except pd.errors.EmptyDataError:
        print(f"ERROR: Excel file is empty (pd.errors.EmptyDataError)")
        raise HTTPException(status_code=400, detail="Excel file is empty")
    except HTTPException as he:
        # Re-raise HTTP exceptions (like column validation errors)
        print(f"ERROR: HTTPException - {he.detail}")
        raise
    except Exception as e:
        print(f"============================================================")
        print(f"=== EXCEL IMPORT FAILED ===")
        print(f"============================================================")
        print(f"ERROR: Unexpected error during Excel import")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details:")
        import traceback
        print(traceback.format_exc())
        print(f"============================================================")
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")


@app.delete("/api/watchlist/sku-groups/{group_id}/products/{sku}")
def remove_product_from_sku_group(group_id: int, sku: str, user: dict = Depends(get_current_user)):
    """Remove a product from a SKU-based watchlist group"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM watchlist_sku_group_products
                WHERE group_id = %s AND sku = %s
            """, (group_id, sku))
            
            if cur.rowcount > 0:
                # Update group's updated_at timestamp
                cur.execute("""
                    UPDATE watchlist_sku_groups
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE group_id = %s
                """, (group_id,))
                conn.commit()
                return {"message": "Product removed from group successfully"}
            else:
                raise HTTPException(status_code=404, detail="Product not in watchlist group")


@app.get("/api/watchlist/sku-groups/{group_id}/export")
def export_sku_group(group_id: int, user: dict = Depends(get_current_user)):
    """Export SKU group products to Excel with price comparison across retailers (same format as products export)"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get group info
            cur.execute("""
                SELECT name FROM watchlist_sku_groups WHERE group_id = %s
            """, (group_id,))
            group = cur.fetchone()
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
            
            # Get Thai Watsadu retailer ID (base retailer)
            cur.execute("SELECT retailer_id FROM retailers WHERE name = 'Thai Watsadu'")
            base_retailer = cur.fetchone()
            if not base_retailer:
                raise HTTPException(status_code=404, detail="Thai Watsadu retailer not found")
            base_retailer_id = base_retailer["retailer_id"]
            
            # Get products in this group from Thai Watsadu
            cur.execute("""
                SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link,
                       wg.name as watchlist_name
                FROM watchlist_sku_group_products wsg
                JOIN products p ON wsg.sku = p.sku AND p.retailer_id = %s
                LEFT JOIN watchlist_sku_groups wg ON wsg.group_id = wg.group_id
                WHERE wsg.group_id = %s
                ORDER BY p.sku
            """, (base_retailer_id, group_id))
            base_products = cur.fetchall()
            
            if not base_products:
                raise HTTPException(status_code=404, detail="No products found in this group")
            
            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            # Sanitize sheet name - remove invalid characters: / \ ? * [ ]
            sheet_name = group["name"][:31]
            for char in ['/', '\\', '?', '*', '[', ']']:
                sheet_name = sheet_name.replace(char, '-')
            ws.title = sheet_name

            # Write header row
            headers = ['Product Name', 'SKU', 'Brand', 'Category', 'S-dept', 'Thai Watsadu Price',
                      'HomePro Price', 'MegaHome Price', 'Do Home Price', 'Boonthavorn Price', 'Global House Price', 'Status']
            ws.append(headers)
            
            # Style header row
            header_font = Font(bold=True)
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.font = header_font
            
            # Define retailer order for columns (excluding Thai Watsadu which is base)
            retailer_order = ['HomePro', 'MegaHome', 'Do Home', 'Boonthavorn', 'Global House']
            
            # Retailer name aliases
            retailer_aliases = {
                'MegaHome': ['Mega Home', 'megahome'],
                'Do Home': ['DoHome', 'dohome'],
                'Global House': ['GlobalHouse', 'globalhouse'],
                'HomePro': ['Home Pro', 'homepro'],
            }
            
            def get_retailer_data(retailer_data_dict, retailer_name):
                """Get retailer data, checking canonical name and aliases."""
                if retailer_name in retailer_data_dict:
                    return retailer_data_dict[retailer_name]
                for alias in retailer_aliases.get(retailer_name, []):
                    if alias in retailer_data_dict:
                        return retailer_data_dict[alias]
                return None
            
            # Hyperlink style (blue, underlined)
            link_font = Font(color="0563C1", underline="single")
            
            # Color fills for price comparison (pastel)
            dark_green_fill = PatternFill(start_color="00C057", end_color="00C057", fill_type="solid")
            light_green_fill = PatternFill(start_color="ABDB77", end_color="ABDB77", fill_type="solid")
            dark_red_fill = PatternFill(start_color="D16969", end_color="D16969", fill_type="solid")
            light_red_fill = PatternFill(start_color="DB9D9D", end_color="DB9D9D", fill_type="solid")
            grey_fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
            white_font = Font(color="FFFFFF", underline="single")
            
            # Process each product
            row_num = 2
            for bp in base_products:
                base_price = float(bp["current_price"]) if bp["current_price"] else None
                base_link = bp["link"] or ''
                
                # Get verified correct matches from other retailers
                cur.execute("""
                    SELECT DISTINCT ON (r.retailer_id)
                        r.name as retailer_name,
                        p2.current_price,
                        p2.link
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    JOIN retailers r ON p2.retailer_id = r.retailer_id
                    WHERE pm.base_product_id = %s
                      AND pm.verified_by_user = TRUE
                      AND pm.is_same = TRUE
                    ORDER BY r.retailer_id, pm.confidence_score DESC NULLS LAST
                """, (bp["product_id"],))
                
                matches = cur.fetchall()
                retailer_data = {}
                for match in matches:
                    retailer_data[match["retailer_name"]] = {
                        "price": float(match["current_price"]) if match["current_price"] else None,
                        "link": match["link"] or ''
                    }
                
                # Collect all prices for comparison
                all_prices = []
                if base_price:
                    all_prices.append(base_price)
                for rd in retailer_data.values():
                    if rd["price"]:
                        all_prices.append(rd["price"])
                
                # Determine min and max prices
                min_price = min(all_prices) if all_prices else None
                max_price = max(all_prices) if all_prices else None
                
                # Determine status
                status = ''
                if base_price:
                    if len(all_prices) == 1:
                        status = 'No Competitor Data'
                    elif base_price == min_price:
                        if all(p == min_price for p in all_prices):
                            status = 'Cheapest (Shared)'
                        else:
                            status = 'Cheapest'
                    elif base_price == max_price:
                        if all(p == max_price for p in all_prices):
                            status = 'Most Expensive (Shared)'
                        else:
                            status = 'Most Expensive'

                # Write row data
                ws.cell(row=row_num, column=1, value=bp["name"] or '')
                ws.cell(row=row_num, column=2, value=bp["sku"] or '')
                ws.cell(row=row_num, column=3, value=bp["brand"] or '')
                ws.cell(row=row_num, column=4, value=bp["category"] or '')
                ws.cell(row=row_num, column=5, value=bp.get("watchlist_name") or '')

                # Thai Watsadu price with hyperlink and color
                if base_price:
                    cell = ws.cell(row=row_num, column=6, value=base_price)
                    if base_link:
                        cell.hyperlink = base_link
                    
                    # Apply color based on price comparison
                    if len(all_prices) > 1:
                        if base_price == min_price:
                            # Cheapest
                            if all(p == min_price for p in all_prices):
                                # Same as others (light green)
                                cell.fill = light_green_fill
                            else:
                                # Unique cheapest (dark green)
                                cell.fill = dark_green_fill
                                cell.font = Font(color="FFFFFF", underline="single") if base_link else Font(color="FFFFFF")
                        elif base_price == max_price:
                            # Most expensive
                            if all(p == max_price for p in all_prices):
                                # Same as others (light red)
                                cell.fill = light_red_fill
                            else:
                                # Unique most expensive (dark red)
                                cell.fill = dark_red_fill
                                cell.font = Font(color="FFFFFF", underline="single") if base_link else Font(color="FFFFFF")
                        else:
                            # Keep default hyperlink font
                            if base_link:
                                cell.font = link_font
                    elif base_link:
                        cell.font = link_font
                
                # Retailer prices with hyperlinks and colors
                for col_offset, retailer_name in enumerate(retailer_order):
                    col_num = 7 + col_offset
                    data = get_retailer_data(retailer_data, retailer_name)
                    if data and data["price"]:
                        cell = ws.cell(row=row_num, column=col_num, value=data["price"])
                        
                        # Apply color based on price comparison
                        if len(all_prices) > 1:
                            # Check if same as TWD (grey)
                            if base_price and data["price"] == base_price:
                                cell.fill = grey_fill
                            elif data["price"] == min_price:
                                # Cheapest
                                if all(p == min_price for p in all_prices):
                                    # Same as others (light green)
                                    cell.fill = light_green_fill
                                else:
                                    # Unique cheapest (dark green)
                                    cell.fill = dark_green_fill
                                    cell.font = Font(color="FFFFFF", underline="single") if data["link"] else Font(color="FFFFFF")
                            elif data["price"] == max_price:
                                # Most expensive
                                if all(p == max_price for p in all_prices):
                                    # Same as others (light red)
                                    cell.fill = light_red_fill
                                else:
                                    # Unique most expensive (dark red)
                                    cell.fill = dark_red_fill
                                    cell.font = Font(color="FFFFFF", underline="single") if data["link"] else Font(color="FFFFFF")
                            else:
                                # Middle price - keep default
                                if data["link"]:
                                    cell.hyperlink = data["link"]
                                    cell.font = link_font
                        else:
                            if data["link"]:
                                cell.hyperlink = data["link"]
                                cell.font = link_font
                        
                        # Set hyperlink if not already set by color logic
                        if data["link"] and not cell.hyperlink:
                            cell.hyperlink = data["link"]

                # Status
                ws.cell(row=row_num, column=12, value=status)

                row_num += 1

            # Auto-adjust column widths
            for col_num, header in enumerate(headers, 1):
                ws.column_dimensions[ws.cell(row=1, column=col_num).column_letter].width = max(len(header) + 2, 12)

            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={group['name']}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
            )


@app.get("/api/watchlist/products/available")
def get_available_products_for_sku_groups(
    search: str = "",
    category: str = "",
    brand: str = "",
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get available products that can be added to SKU watchlist groups"""
    with get_db() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT DISTINCT 
                    p.sku, 
                    p.name,
                    p.brand,
                    p.category,
                    p.current_price,
                    p.image
                FROM products p
                WHERE p.retailer_id = 'twd' 
                AND p.sku IS NOT NULL 
                AND p.sku != ''
            """
            params = []
            
            if search:
                query += " AND (p.name ILIKE %s OR p.sku ILIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
            
            # Parse comma-separated values for multi-select filters
            category_list = [c.strip() for c in category.split(',')] if category else []
            brand_list = [b.strip() for b in brand.split(',')] if brand else []
            
            if category_list:
                placeholders = ','.join(['%s'] * len(category_list))
                query += f" AND p.category IN ({placeholders})"
                params.extend(category_list)
            
            if brand_list:
                placeholders = ','.join(['%s'] * len(brand_list))
                query += f" AND p.brand IN ({placeholders})"
                params.extend(brand_list)
            
            query += " ORDER BY p.name LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            products = cur.fetchall()
            
            return {
                "products": [
                    {
                        "sku": row["sku"],
                        "name": row["name"],
                        "brand": row["brand"],
                        "category": row["category"],
                        "price": float(row["current_price"]) if row["current_price"] else None,
                        "image_url": row["image"]
                    }
                    for row in products
                ],
                "total": len(products)
            }


# ============== OLD User-Specific Watchlist (Deprecated) ==============

@app.get("/api/watchlist")
def get_watchlist(user: dict = Depends(get_current_user)):
    """Get user's category watchlist"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, created_at
                FROM user_category_watchlist
                WHERE user_id = %s
                ORDER BY category
            """, (user["user_id"],))
            categories = cur.fetchall()

            return {
                "categories": [row["category"] for row in categories],
                "total": len(categories)
            }


@app.post("/api/watchlist")
def add_to_watchlist(data: dict, user: dict = Depends(get_current_user)):
    """Add a category to user's watchlist"""
    category = data.get("category")
    if not category:
        raise HTTPException(status_code=400, detail="Category is required")

    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if category exists in products
            cur.execute("""
                SELECT DISTINCT category FROM products
                WHERE category = %s AND retailer_id = 'twd'
            """, (category,))
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="Category not found")

            # Add to watchlist (ignore if already exists)
            cur.execute("""
                INSERT INTO user_category_watchlist (user_id, category)
                VALUES (%s, %s)
                ON CONFLICT (user_id, category) DO NOTHING
                RETURNING watchlist_id
            """, (user["user_id"], category))
            result = cur.fetchone()
            conn.commit()

            if result:
                return {"message": "Category added to watchlist", "category": category}
            else:
                return {"message": "Category already in watchlist", "category": category}


@app.delete("/api/watchlist/{category}")
def remove_from_watchlist(category: str, user: dict = Depends(get_current_user)):
    """Remove a category from user's watchlist"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM user_category_watchlist
                WHERE user_id = %s AND category = %s
                RETURNING watchlist_id
            """, (user["user_id"], category))
            result = cur.fetchone()
            conn.commit()

            if result:
                return {"message": "Category removed from watchlist", "category": category}
            else:
                raise HTTPException(status_code=404, detail="Category not in watchlist")


@app.get("/api/watchlist/categories")
def get_available_categories(user: dict = Depends(get_current_user)):
    """Get all available categories with watchlist status"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get all categories from Thai Watsadu products
            cur.execute("""
                SELECT DISTINCT p.category, COUNT(*) as product_count
                FROM products p
                WHERE p.retailer_id = 'twd' AND p.category IS NOT NULL AND p.category != ''
                GROUP BY p.category
                ORDER BY p.category
            """)
            all_categories = cur.fetchall()

            # Get user's watched categories
            cur.execute("""
                SELECT category FROM user_category_watchlist
                WHERE user_id = %s
            """, (user["user_id"],))
            watched = {row["category"] for row in cur.fetchall()}

            return {
                "categories": [
                    {
                        "category": row["category"],
                        "product_count": row["product_count"],
                        "is_watched": row["category"] in watched
                    }
                    for row in all_categories
                ],
                "total": len(all_categories)
            }


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
    retailer: Optional[str] = None,
    watched_only: Optional[bool] = False,
    watchlist_group_id: Optional[int] = None,
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

            # Parse comma-separated category and brand values for multi-select
            category_list = [c.strip() for c in category.split(',')] if category else []
            brand_list = [b.strip() for b in brand.split(',')] if brand else []

            # Get user's watched categories if watched_only is enabled
            watched_categories = []
            if watched_only:
                user_id = user.get("user_id")
                if user_id:
                    cur.execute("SELECT category FROM user_category_watchlist WHERE user_id = %s", (user_id,))
                    watched_categories = [row["category"] for row in cur.fetchall()]

            # Get unique categories for filters (filtered by selected brands for cascading)
            category_query = """
                SELECT DISTINCT category FROM products
                WHERE retailer_id = %s AND category IS NOT NULL
            """
            category_params = [base_retailer_id]
            if brand_list:
                placeholders = ','.join(['%s'] * len(brand_list))
                category_query += f" AND brand IN ({placeholders})"
                category_params.extend(brand_list)
            # Filter categories by watchlist when watched_only is enabled
            if watched_only and watched_categories:
                placeholders = ','.join(['%s'] * len(watched_categories))
                category_query += f" AND category IN ({placeholders})"
                category_params.extend(watched_categories)
            category_query += " ORDER BY category"
            cur.execute(category_query, category_params)
            categories = [row["category"] for row in cur.fetchall()]

            # Get unique brands for filters (filtered by selected categories for cascading)
            brand_query = """
                SELECT DISTINCT brand FROM products
                WHERE retailer_id = %s AND brand IS NOT NULL
            """
            brand_params = [base_retailer_id]
            if category_list:
                placeholders = ','.join(['%s'] * len(category_list))
                brand_query += f" AND category IN ({placeholders})"
                brand_params.extend(category_list)
            # Filter brands by watchlist categories when watched_only is enabled
            if watched_only and watched_categories:
                placeholders = ','.join(['%s'] * len(watched_categories))
                brand_query += f" AND category IN ({placeholders})"
                brand_params.extend(watched_categories)
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
                # Check if search contains multiple SKUs (comma, newline, or space separated)
                # Replace newlines and commas with spaces, then split and filter
                search_normalized = search.replace('\n', ' ').replace('\r', ' ').replace(',', ' ')
                search_values = [s.strip() for s in search_normalized.split() if s.strip()]

                if len(search_values) > 1:
                    # Multiple SKUs - use exact match with IN clause
                    placeholders = ','.join(['%s'] * len(search_values))
                    query += f" AND p.sku IN ({placeholders})"
                    params.extend(search_values)
                else:
                    # Single search term - use ILIKE for partial matching (name, sku, or brand)
                    query += " AND (p.name ILIKE %s OR p.sku ILIKE %s OR p.brand ILIKE %s)"
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])

            if category_list:
                placeholders = ','.join(['%s'] * len(category_list))
                query += f" AND p.category IN ({placeholders})"
                params.extend(category_list)

            if brand_list:
                placeholders = ','.join(['%s'] * len(brand_list))
                query += f" AND p.brand IN ({placeholders})"
                params.extend(brand_list)

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

            # Filter by specific retailer match (only products with verified match for this retailer)
            if retailer:
                query += """ AND EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id
                    AND pm.retailer_id = %s
                    AND pm.verified_by_user = TRUE
                    AND pm.is_same = TRUE
                )"""
                params.append(retailer)

            # Filter by user's watched categories
            if watched_only:
                user_id = user.get("user_id")
                if user_id:
                    query += """ AND p.category IN (
                        SELECT category FROM user_category_watchlist WHERE user_id = %s
                    )"""
                    params.append(user_id)

            # Filter by watchlist group (SKU-based watchlist)
            if watchlist_group_id:
                query += """ AND p.sku IN (
                    SELECT sku FROM watchlist_sku_group_products WHERE group_id = %s
                )"""
                params.append(watchlist_group_id)

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

                # Get best match from each retailer (verified first, then top unverified)
                cur.execute("""
                    SELECT DISTINCT ON (r.retailer_id)
                        r.name as retailer_name,
                        p2.current_price,
                        p2.link,
                        pm.is_same,
                        pm.verified_by_user,
                        pm.confidence_score
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    JOIN retailers r ON p2.retailer_id = r.retailer_id
                    WHERE pm.base_product_id = %s
                      AND (pm.is_same IS NULL OR pm.is_same = TRUE)
                    ORDER BY r.retailer_id,
                             (pm.verified_by_user = TRUE AND pm.is_same = TRUE) DESC,
                             pm.confidence_score DESC NULLS LAST
                """, (bp["product_id"],))

                matches = cur.fetchall()
                for match in matches:
                    product["retailer_prices"][match["retailer_name"]] = {
                        "price": float(match["current_price"]) if match["current_price"] else None,
                        "link": match["link"],
                        "verified": bool(match["verified_by_user"] and match["is_same"]),
                        "price_change": None  # Will be populated below
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

                # Get price changes for base product (last 7 days)
                cur.execute("""
                    SELECT price FROM price_history
                    WHERE product_id = %s
                      AND scraped_at < NOW() - INTERVAL '1 day'
                    ORDER BY scraped_at ASC
                    LIMIT 1
                """, (bp["product_id"],))
                old_price_row = cur.fetchone()
                if old_price_row and product["base_price"]:
                    old_price = float(old_price_row["price"])
                    if old_price != product["base_price"]:
                        change = product["base_price"] - old_price
                        change_pct = (change / old_price) * 100 if old_price > 0 else 0
                        product["base_price_change"] = {
                            "old_price": old_price,
                            "change": round(change, 2),
                            "change_pct": round(change_pct, 1),
                            "direction": "up" if change > 0 else "down"
                        }
                    else:
                        product["base_price_change"] = None
                else:
                    product["base_price_change"] = None

                # Get price changes for matched retailers
                for retailer_name, rp in product["retailer_prices"].items():
                    if rp["price"] is None:
                        continue
                    # Get the product_id for this retailer's match
                    cur.execute("""
                        SELECT p2.product_id
                        FROM product_matches pm
                        JOIN products p2 ON pm.candidate_product_id = p2.product_id
                        JOIN retailers r ON p2.retailer_id = r.retailer_id
                        WHERE pm.base_product_id = %s AND r.name = %s
                          AND pm.verified_by_user = TRUE AND pm.is_same = TRUE
                        LIMIT 1
                    """, (bp["product_id"], retailer_name))
                    match_product = cur.fetchone()
                    if match_product:
                        cur.execute("""
                            SELECT price FROM price_history
                            WHERE product_id = %s
                              AND scraped_at < NOW() - INTERVAL '1 day'
                            ORDER BY scraped_at ASC
                            LIMIT 1
                        """, (match_product["product_id"],))
                        old_match_price = cur.fetchone()
                        if old_match_price:
                            old_price = float(old_match_price["price"])
                            if old_price != rp["price"]:
                                change = rp["price"] - old_price
                                change_pct = (change / old_price) * 100 if old_price > 0 else 0
                                rp["price_change"] = {
                                    "old_price": old_price,
                                    "change": round(change, 2),
                                    "change_pct": round(change_pct, 1),
                                    "direction": "up" if change > 0 else "down"
                                }

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
    retailer: Optional[str] = None,
    watched_only: Optional[bool] = False,
    watchlist_group_id: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """Export products to Excel with price comparison across retailers (prices are hyperlinked to product pages)"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get Thai Watsadu retailer ID (base retailer)
            cur.execute("SELECT retailer_id FROM retailers WHERE name = 'Thai Watsadu'")
            base_retailer = cur.fetchone()
            if not base_retailer:
                # Return empty Excel if no base retailer
                wb = Workbook()
                ws = wb.active
                ws.append(['Product Name', 'SKU', 'Brand', 'Category', 'Thai Watsadu Price',
                          'HomePro Price', 'MegaHome Price', 'Do Home Price', 'Boonthavorn Price', 'Global House Price', 'Status'])
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                return Response(
                    content=output.getvalue(),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
                )
            base_retailer_id = base_retailer["retailer_id"]

            # Parse comma-separated category and brand values for multi-select
            category_list = [c.strip() for c in category.split(',')] if category else []
            brand_list = [b.strip() for b in brand.split(',')] if brand else []

            # Build query for Thai Watsadu products (same logic as /api/products but without pagination)
            query = """
                SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link,
                       wg.name as watchlist_name
                FROM products p
                LEFT JOIN watchlist_sku_group_products wsgp ON p.sku = wsgp.sku AND p.retailer_id = 'twd'
                LEFT JOIN watchlist_sku_groups wg ON wsgp.group_id = wg.group_id
                WHERE p.retailer_id = %s
            """
            params = [base_retailer_id]

            if search:
                # Check if search contains multiple SKUs (comma, newline, or space separated)
                # Replace newlines and commas with spaces, then split and filter
                search_normalized = search.replace('\n', ' ').replace('\r', ' ').replace(',', ' ')
                search_values = [s.strip() for s in search_normalized.split() if s.strip()]

                if len(search_values) > 1:
                    # Multiple SKUs - use exact match with IN clause
                    placeholders = ','.join(['%s'] * len(search_values))
                    query += f" AND p.sku IN ({placeholders})"
                    params.extend(search_values)
                else:
                    # Single search term - use ILIKE for partial matching (name, sku, or brand)
                    query += " AND (p.name ILIKE %s OR p.sku ILIKE %s OR p.brand ILIKE %s)"
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])

            if category_list:
                placeholders = ','.join(['%s'] * len(category_list))
                query += f" AND p.category IN ({placeholders})"
                params.extend(category_list)

            if brand_list:
                placeholders = ','.join(['%s'] * len(brand_list))
                query += f" AND p.brand IN ({placeholders})"
                params.extend(brand_list)

            # Filter by verification status
            # Use same logic as products table filter:
            # Retailer is "done" if: has verified correct match OR all matches reviewed
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

            # Filter by specific retailer match
            if retailer:
                query += """ AND EXISTS (
                    SELECT 1 FROM product_matches pm
                    WHERE pm.base_product_id = p.product_id
                    AND pm.retailer_id = %s
                    AND pm.verified_by_user = TRUE
                    AND pm.is_same = TRUE
                )"""
                params.append(retailer)

            # Filter by user's watched categories
            if watched_only:
                user_id = user.get("user_id")
                if user_id:
                    query += """ AND p.category IN (
                        SELECT category FROM user_category_watchlist WHERE user_id = %s
                    )"""
                    params.append(user_id)

            # Filter by watchlist group (SKU-based watchlist)
            if watchlist_group_id:
                query += """ AND p.sku IN (
                    SELECT sku FROM watchlist_sku_group_products WHERE group_id = %s
                )"""
                params.append(watchlist_group_id)

            query += " ORDER BY p.product_id"

            cur.execute(query, params)
            base_products = cur.fetchall()

            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Products"

            # Write header row
            headers = ['Product Name', 'SKU', 'Brand', 'Category', 'S-dept', 'Thai Watsadu Price',
                      'HomePro Price', 'MegaHome Price', 'Do Home Price', 'Boonthavorn Price', 'Global House Price', 'Status']
            ws.append(headers)

            # Style header row
            header_font = Font(bold=True)
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.font = header_font

            # Define retailer order for columns (excluding Thai Watsadu which is base)
            retailer_order = ['HomePro', 'MegaHome', 'Do Home', 'Boonthavorn', 'Global House']

            # Retailer name aliases - map canonical names to possible DB names
            retailer_aliases = {
                'MegaHome': ['Mega Home', 'megahome'],
                'Do Home': ['DoHome', 'dohome'],
                'Global House': ['GlobalHouse', 'globalhouse'],
                'HomePro': ['Home Pro', 'homepro'],
            }

            def get_retailer_data(retailer_data_dict, retailer_name):
                """Get retailer data, checking canonical name and aliases."""
                # Try canonical name first
                if retailer_name in retailer_data_dict:
                    return retailer_data_dict[retailer_name]
                # Try aliases
                for alias in retailer_aliases.get(retailer_name, []):
                    if alias in retailer_data_dict:
                        return retailer_data_dict[alias]
                return None

            # Hyperlink style (blue, underlined)
            link_font = Font(color="0563C1", underline="single")

            # Color fills for price comparison (pastel)
            dark_green_fill = PatternFill(start_color="00C057", end_color="00C057", fill_type="solid")
            light_green_fill = PatternFill(start_color="ABDB77", end_color="ABDB77", fill_type="solid")
            dark_red_fill = PatternFill(start_color="D16969", end_color="D16969", fill_type="solid")
            light_red_fill = PatternFill(start_color="DB9D9D", end_color="DB9D9D", fill_type="solid")
            grey_fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
            white_font = Font(color="FFFFFF", underline="single")

            # Process each product
            row_num = 2
            for bp in base_products:
                base_price = float(bp["current_price"]) if bp["current_price"] else None
                base_link = bp["link"] or ''

                # Get verified correct matches from other retailers (include link)
                cur.execute("""
                    SELECT DISTINCT ON (r.retailer_id)
                        r.name as retailer_name,
                        p2.current_price,
                        p2.link
                    FROM product_matches pm
                    JOIN products p2 ON pm.candidate_product_id = p2.product_id
                    JOIN retailers r ON p2.retailer_id = r.retailer_id
                    WHERE pm.base_product_id = %s
                      AND pm.verified_by_user = TRUE
                      AND pm.is_same = TRUE
                    ORDER BY r.retailer_id, pm.confidence_score DESC NULLS LAST
                """, (bp["product_id"],))

                matches = cur.fetchall()
                retailer_data = {}
                for match in matches:
                    retailer_data[match["retailer_name"]] = {
                        "price": float(match["current_price"]) if match["current_price"] else None,
                        "link": match["link"] or ''
                    }

                # Collect all prices for comparison
                all_prices = []
                if base_price:
                    all_prices.append(base_price)
                for rd in retailer_data.values():
                    if rd["price"]:
                        all_prices.append(rd["price"])

                # Determine min and max prices
                min_price = min(all_prices) if all_prices else None
                max_price = max(all_prices) if all_prices else None

                # Determine status
                status = ''
                if base_price:
                    if len(all_prices) == 1:
                        status = 'No Competitor Data'
                    elif base_price == min_price:
                        if all(p == min_price for p in all_prices):
                            status = 'Cheapest (Shared)'
                        else:
                            status = 'Cheapest'
                    elif base_price == max_price:
                        if all(p == max_price for p in all_prices):
                            status = 'Most Expensive (Shared)'
                        else:
                            status = 'Most Expensive'

                # Write row data
                ws.cell(row=row_num, column=1, value=bp["name"] or '')
                ws.cell(row=row_num, column=2, value=bp["sku"] or '')
                ws.cell(row=row_num, column=3, value=bp["brand"] or '')
                ws.cell(row=row_num, column=4, value=bp["category"] or '')
                ws.cell(row=row_num, column=5, value=bp.get("watchlist_name") or '')

                # Thai Watsadu price with hyperlink (column 6) and color
                if base_price:
                    cell = ws.cell(row=row_num, column=6, value=base_price)
                    if base_link:
                        cell.hyperlink = base_link
                    
                    # Apply color based on price comparison
                    if len(all_prices) > 1:
                        if base_price == min_price:
                            # Cheapest
                            if all(p == min_price for p in all_prices):
                                # Same as others (light green)
                                cell.fill = light_green_fill
                            else:
                                # Unique cheapest (dark green)
                                cell.fill = dark_green_fill
                                cell.font = Font(color="FFFFFF", underline="single") if base_link else Font(color="FFFFFF")
                        elif base_price == max_price:
                            # Most expensive
                            if all(p == max_price for p in all_prices):
                                # Same as others (light red)
                                cell.fill = light_red_fill
                            else:
                                # Unique most expensive (dark red)
                                cell.fill = dark_red_fill
                                cell.font = Font(color="FFFFFF", underline="single") if base_link else Font(color="FFFFFF")
                        else:
                            # Keep default hyperlink font
                            if base_link:
                                cell.font = link_font
                    elif base_link:
                        cell.font = link_font

                # Retailer prices with hyperlinks (columns 7-11) and colors
                for col_offset, retailer_name in enumerate(retailer_order):
                    col_num = 7 + col_offset
                    data = get_retailer_data(retailer_data, retailer_name)
                    if data and data["price"]:
                        cell = ws.cell(row=row_num, column=col_num, value=data["price"])
                        
                        # Apply color based on price comparison
                        if len(all_prices) > 1:
                            # Check if same as TWD (grey)
                            if base_price and data["price"] == base_price:
                                cell.fill = grey_fill
                            elif data["price"] == min_price:
                                # Cheapest
                                if all(p == min_price for p in all_prices):
                                    # Same as others (light green)
                                    cell.fill = light_green_fill
                                else:
                                    # Unique cheapest (dark green)
                                    cell.fill = dark_green_fill
                                    cell.font = Font(color="FFFFFF", underline="single") if data["link"] else Font(color="FFFFFF")
                            elif data["price"] == max_price:
                                # Most expensive
                                if all(p == max_price for p in all_prices):
                                    # Same as others (light red)
                                    cell.fill = light_red_fill
                                else:
                                    # Unique most expensive (dark red)
                                    cell.fill = dark_red_fill
                                    cell.font = Font(color="FFFFFF", underline="single") if data["link"] else Font(color="FFFFFF")
                            else:
                                # Middle price - keep default
                                if data["link"]:
                                    cell.hyperlink = data["link"]
                                    cell.font = link_font
                        else:
                            if data["link"]:
                                cell.hyperlink = data["link"]
                                cell.font = link_font
                        
                        # Set hyperlink if not already set by color logic
                        if data["link"] and not cell.hyperlink:
                            cell.hyperlink = data["link"]

                # Status (column 12)
                ws.cell(row=row_num, column=12, value=status)

                row_num += 1

            # Auto-adjust column widths
            for col_num, header in enumerate(headers, 1):
                ws.column_dimensions[ws.cell(row=1, column=col_num).column_letter].width = max(len(header) + 2, 12)

            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
            )


@app.get("/api/products/{product_id}/price-history")
def get_price_history(
    product_id: int,
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """Get price history for a product and its verified matches"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get base product info
            cur.execute("""
                SELECT p.product_id, p.name, r.name as retailer_name
                FROM products p
                JOIN retailers r ON p.retailer_id = r.retailer_id
                WHERE p.product_id = %s
            """, (product_id,))
            base_product = cur.fetchone()
            if not base_product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Get price history for base product
            # Use date-based query with extended range to ensure we get multiple data points
            # This keeps all products on the same timeline
            fetch_days = days + 2 if days <= 7 else days
            cur.execute("""
                SELECT price, scraped_at
                FROM price_history
                WHERE product_id = %s
                  AND scraped_at >= NOW() - INTERVAL '%s days'
                ORDER BY scraped_at ASC
            """, (product_id, fetch_days))
            base_history = cur.fetchall()

            result = {
                "base_product": {
                    "product_id": base_product["product_id"],
                    "name": base_product["name"],
                    "retailer": base_product["retailer_name"],
                    "history": [
                        {
                            "price": float(row["price"]),
                            "date": row["scraped_at"].isoformat()
                        }
                        for row in base_history
                    ]
                },
                "matched_products": []
            }

            # Get verified matches and their price history
            cur.execute("""
                SELECT DISTINCT ON (r.retailer_id)
                    p2.product_id, p2.name, r.name as retailer_name
                FROM product_matches pm
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                JOIN retailers r ON p2.retailer_id = r.retailer_id
                WHERE pm.base_product_id = %s
                  AND pm.verified_by_user = TRUE
                  AND pm.is_same = TRUE
                ORDER BY r.retailer_id, pm.updated_at DESC
            """, (product_id,))
            matches = cur.fetchall()

            for match in matches:
                cur.execute("""
                    SELECT price, scraped_at
                    FROM price_history
                    WHERE product_id = %s
                      AND scraped_at >= NOW() - INTERVAL '%s days'
                    ORDER BY scraped_at ASC
                """, (match["product_id"], fetch_days))
                match_history = cur.fetchall()

                result["matched_products"].append({
                    "product_id": match["product_id"],
                    "name": match["name"],
                    "retailer": match["retailer_name"],
                    "history": [
                        {
                            "price": float(row["price"]),
                            "date": row["scraped_at"].isoformat()
                        }
                        for row in match_history
                    ]
                })

            return result


@app.get("/api/products/{product_id}/price-history/export")
def export_price_history(
    product_id: int,
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """Export price history to Excel"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get base product info with watchlist
            cur.execute("""
                SELECT p.product_id, p.name, p.sku, p.brand, p.category, r.name as retailer_name,
                       wg.name as watchlist_name
                FROM products p
                JOIN retailers r ON p.retailer_id = r.retailer_id
                LEFT JOIN watchlist_sku_group_products wsgp ON p.sku = wsgp.sku AND p.retailer_id = 'twd'
                LEFT JOIN watchlist_sku_groups wg ON wsgp.group_id = wg.group_id
                WHERE p.product_id = %s
            """, (product_id,))
            base_product = cur.fetchone()
            if not base_product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Get price history for base product
            # Use date-based query with extended range to ensure we get multiple data points
            fetch_days = days + 2 if days <= 7 else days
            cur.execute("""
                SELECT price, scraped_at
                FROM price_history
                WHERE product_id = %s
                  AND scraped_at >= NOW() - INTERVAL '%s days'
                ORDER BY scraped_at ASC
            """, (product_id, fetch_days))
            base_history = cur.fetchall()

            # Define fixed retailer order (excluding Thai Watsadu which is base)
            all_retailers = ['HomePro', 'MegaHome', 'Do Home', 'Boonthavorn', 'Global House']

            # Get verified correct matches
            cur.execute("""
                SELECT DISTINCT ON (pm.candidate_product_id)
                    p.product_id, p.name, r.name as retailer_name
                FROM product_matches pm
                JOIN products p ON pm.candidate_product_id = p.product_id
                JOIN retailers r ON p.retailer_id = r.retailer_id
                WHERE pm.base_product_id = %s
                  AND pm.verified_by_user = TRUE
                  AND pm.is_same = TRUE
                ORDER BY pm.candidate_product_id, pm.confidence_score DESC NULLS LAST
            """, (product_id,))
            matches = cur.fetchall()

            # Get price history for each match
            matched_histories = {}
            for match in matches:
                cur.execute("""
                    SELECT price, scraped_at
                    FROM price_history
                    WHERE product_id = %s
                      AND scraped_at >= NOW() - INTERVAL '%s days'
                    ORDER BY scraped_at ASC
                """, (match["product_id"], fetch_days))
                matched_histories[match["retailer_name"]] = cur.fetchall()

            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Price History"

            # Write headers with fixed retailer columns
            headers = ['Timestamp', 'SKU', 'Product Name', 'Brand', 'Sub-Dept', base_product["retailer_name"]]
            for retailer in all_retailers:
                headers.append(retailer)
            ws.append(headers)

            # Style header row
            header_font = Font(bold=True)
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.font = header_font

            # Collect all unique dates with timestamps
            all_timestamps = {}
            for row in base_history:
                date_key = row["scraped_at"].date()
                if date_key not in all_timestamps:
                    all_timestamps[date_key] = row["scraped_at"]
            for history in matched_histories.values():
                for row in history:
                    date_key = row["scraped_at"].date()
                    if date_key not in all_timestamps:
                        all_timestamps[date_key] = row["scraped_at"]

            # Sort dates
            sorted_dates = sorted(all_timestamps.keys())

            # Write data rows
            for date in sorted_dates:
                timestamp = all_timestamps[date]
                row_data = [
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    base_product["sku"] or '',
                    base_product["name"] or '',
                    base_product["brand"] or '',
                    base_product["watchlist_name"] or ''
                ]

                # Base product price for this date
                base_price = next((float(h["price"]) for h in base_history
                                  if h["scraped_at"].date() == date), None)
                row_data.append(base_price if base_price else '')

                # All retailers prices in fixed order
                for retailer in all_retailers:
                    if retailer in matched_histories:
                        match_price = next((float(h["price"]) for h in matched_histories[retailer]
                                          if h["scraped_at"].date() == date), None)
                        row_data.append(match_price if match_price else '')
                    else:
                        row_data.append('')

                ws.append(row_data)

            # Auto-adjust column widths
            for col_num, header in enumerate(headers, 1):
                ws.column_dimensions[ws.cell(row=1, column=col_num).column_letter].width = max(len(str(header)) + 2, 12)

            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=price_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
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
                       p.last_updated_at, p.scrape_fail_count,
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
                "last_updated_at": product["last_updated_at"].isoformat() if product["last_updated_at"] else None,
                "scrape_fail_count": product["scrape_fail_count"] if product["scrape_fail_count"] is not None else 0,
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
                    p2.last_updated_at as matched_last_updated_at,
                    p2.scrape_fail_count as matched_scrape_fail_count,
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
                                    "last_updated_at": row["matched_last_updated_at"].isoformat() if row["matched_last_updated_at"] else None,
                                    "scrape_fail_count": row["matched_scrape_fail_count"] if row["matched_scrape_fail_count"] is not None else 0,
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
                                "last_updated_at": row["matched_last_updated_at"].isoformat() if row["matched_last_updated_at"] else None,
                                "scrape_fail_count": row["matched_scrape_fail_count"] if row["matched_scrape_fail_count"] is not None else 0,
                            }
                        })

            return {
                "product": base_product,
                "matches": matches,
                "total_matches": len(matches),
            }


@app.get("/api/products/{product_id}/watchlist-groups")
def get_product_watchlist_groups(product_id: int, user: dict = Depends(get_current_user)):
    """Get all watchlist groups that contain this product's SKU"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # First get the product's SKU
            cur.execute("""
                SELECT sku FROM products WHERE product_id = %s
            """, (product_id,))
            product = cur.fetchone()

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Get all watchlist groups containing this SKU
            cur.execute("""
                SELECT
                    wsg.group_id,
                    wsg.name,
                    wsgp.added_at
                FROM watchlist_sku_groups wsg
                JOIN watchlist_sku_group_products wsgp ON wsg.group_id = wsgp.group_id
                WHERE wsgp.sku = %s
                ORDER BY wsg.name ASC
            """, (product["sku"],))
            groups = cur.fetchall()

            return {
                "groups": [
                    {
                        "group_id": g["group_id"],
                        "name": g["name"],
                        "added_at": g["added_at"].isoformat() if g["added_at"] else None
                    }
                    for g in groups
                ]
            }


@app.post("/api/products/{product_id}/rescrape")
def rescrape_product(product_id: int, user: dict = Depends(get_current_user)):
    """
    Rescrape prices for a product and its verified matches.
    Only scrapes the base product and verified correct matches.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get base product
            cur.execute("""
                SELECT p.product_id, p.sku, p.name, p.link, p.current_price,
                       p.original_price, p.lowest_price, p.highest_price,
                       r.name as retailer_name, r.retailer_id
                FROM products p
                JOIN retailers r ON p.retailer_id = r.retailer_id
                WHERE p.product_id = %s
            """, (product_id,))
            base_product = cur.fetchone()

            if not base_product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Get verified correct matches only
            cur.execute("""
                SELECT p.product_id, p.sku, p.name, p.link, p.current_price,
                       p.original_price, p.lowest_price, p.highest_price,
                       r.name as retailer_name, r.retailer_id
                FROM product_matches pm
                JOIN products p ON pm.candidate_product_id = p.product_id
                JOIN retailers r ON p.retailer_id = r.retailer_id
                WHERE pm.base_product_id = %s
                  AND pm.verified_by_user = TRUE
                  AND pm.is_same = TRUE
            """, (product_id,))
            verified_matches = cur.fetchall()

            # Collect all products to scrape
            products_to_scrape = [base_product] + list(verified_matches)

            results = []
            for product in products_to_scrape:
                url = product["link"]
                if not url:
                    results.append({
                        "product_id": product["product_id"],
                        "retailer_name": product["retailer_name"],
                        "success": False,
                        "error": "No URL available"
                    })
                    continue

                # Scrape the URL
                scrape_result = scrape_single_url(url)

                if scrape_result.get("success"):
                    scraped_data = scrape_result.get("data", {})
                    new_price = scraped_data.get("current_price")
                    new_original_price = scraped_data.get("original_price")

                    if new_price is not None:
                        try:
                            new_price = float(new_price)
                            old_price = float(product["current_price"]) if product["current_price"] else None
                            lowest_price = float(product["lowest_price"]) if product["lowest_price"] else new_price
                            highest_price = float(product["highest_price"]) if product["highest_price"] else new_price

                            # Update lowest/highest
                            if new_price < lowest_price:
                                lowest_price = new_price
                            if new_price > highest_price:
                                highest_price = new_price

                            # Update database
                            cur.execute("""
                                UPDATE products SET
                                    current_price = %s,
                                    original_price = COALESCE(%s, original_price),
                                    lowest_price = %s,
                                    highest_price = %s,
                                    last_updated_at = NOW(),
                                    scrape_fail_count = 0
                                WHERE product_id = %s
                            """, (new_price, new_original_price, lowest_price, highest_price, product["product_id"]))

                            # Insert price history
                            cur.execute("""
                                INSERT INTO price_history (product_id, price)
                                VALUES (%s, %s)
                            """, (product["product_id"], new_price))

                            results.append({
                                "product_id": product["product_id"],
                                "retailer_name": product["retailer_name"],
                                "success": True,
                                "old_price": old_price,
                                "new_price": new_price,
                                "price_changed": old_price != new_price if old_price else True
                            })
                        except (TypeError, ValueError) as e:
                            results.append({
                                "product_id": product["product_id"],
                                "retailer_name": product["retailer_name"],
                                "success": False,
                                "error": f"Invalid price format: {new_price}"
                            })
                    else:
                        results.append({
                            "product_id": product["product_id"],
                            "retailer_name": product["retailer_name"],
                            "success": False,
                            "error": "No price found in scraped data"
                        })
                else:
                    results.append({
                        "product_id": product["product_id"],
                        "retailer_name": product["retailer_name"],
                        "success": False,
                        "error": scrape_result.get("error", "Unknown scrape error")
                    })

            conn.commit()

            return {
                "success": True,
                "total_scraped": len(products_to_scrape),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "results": results
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

@app.get("/api/matches/grouped")
def get_matches_grouped(user: dict = Depends(get_current_user)):
    """Get product matches grouped by base product and retailer - excludes products where all retailers are verified"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get all matches grouped by base product
            # Exclude base products where ALL retailers have at least one verified "Same" match
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
                    r1.retailer_id as base_retailer_id,
                    p2.product_id as candidate_product_id,
                    p2.name as candidate_name,
                    p2.sku as candidate_sku,
                    p2.current_price as candidate_price,
                    p2.image as candidate_image,
                    r2.name as candidate_retailer,
                    r2.retailer_id as candidate_retailer_id
                FROM product_matches pm
                JOIN products p1 ON pm.base_product_id = p1.product_id
                JOIN retailers r1 ON p1.retailer_id = r1.retailer_id
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                JOIN retailers r2 ON p2.retailer_id = r2.retailer_id
                WHERE p1.product_id NOT IN (
                    -- Exclude base products where all retailers have verified matches
                    SELECT base_product_id
                    FROM (
                        -- Get all retailers that have matches for each base product
                        SELECT DISTINCT pm_all.base_product_id, p_all.retailer_id
                        FROM product_matches pm_all
                        JOIN products p_all ON pm_all.candidate_product_id = p_all.product_id
                    ) all_retailers
                    GROUP BY base_product_id
                    HAVING COUNT(*) = (
                        -- Count how many of those retailers have a verified "Same" match
                        SELECT COUNT(DISTINCT p_verified.retailer_id)
                        FROM product_matches pm_verified
                        JOIN products p_verified ON pm_verified.candidate_product_id = p_verified.product_id
                        WHERE pm_verified.base_product_id = all_retailers.base_product_id
                          AND pm_verified.verified_by_user = TRUE
                          AND pm_verified.is_same = TRUE
                    )
                )
                ORDER BY p1.name, r2.name, pm.confidence_score DESC NULLS LAST
            """)
            rows = cur.fetchall()

            # Group by base product
            products_map = {}
            for row in rows:
                base_id = row["base_product_id"]

                if base_id not in products_map:
                    products_map[base_id] = {
                        "base_product": {
                            "product_id": row["base_product_id"],
                            "name": row["base_name"],
                            "sku": row["base_sku"],
                            "retailer_name": row["base_retailer"],
                            "retailer_id": row["base_retailer_id"],
                            "current_price": float(row["base_price"]) if row["base_price"] else None,
                            "image": row["base_image"],
                        },
                        "matches_by_retailer": {}
                    }

                retailer_id = row["candidate_retailer_id"]
                retailer_name = row["candidate_retailer"]

                if retailer_id not in products_map[base_id]["matches_by_retailer"]:
                    products_map[base_id]["matches_by_retailer"][retailer_id] = {
                        "retailer_name": retailer_name,
                        "retailer_id": retailer_id,
                        "matches": []
                    }

                products_map[base_id]["matches_by_retailer"][retailer_id]["matches"].append({
                    "match_id": row["match_id"],
                    "is_same": row["is_same"],
                    "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
                    "reason": row["reason"],
                    "match_type": row["match_type"],
                    "verified_by_user": row["verified_by_user"],
                    "candidate_product": {
                        "product_id": row["candidate_product_id"],
                        "name": row["candidate_name"],
                        "sku": row["candidate_sku"],
                        "retailer_name": row["candidate_retailer"],
                        "current_price": float(row["candidate_price"]) if row["candidate_price"] else None,
                        "image": row["candidate_image"],
                    }
                })

            # Convert to list and transform matches_by_retailer to list
            products = []
            for product in products_map.values():
                product["matches_by_retailer"] = list(product["matches_by_retailer"].values())
                products.append(product)

            return {"products": products}


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


@app.post("/api/matches/{match_id}/undo")
def undo_match_verification(
    match_id: int,
    user: dict = Depends(get_current_user)
):
    """Undo verification of a product match - set back to unverified state"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE product_matches
                SET verified_by_user = FALSE,
                    verified_result = NULL,
                    verified_at = NULL,
                    is_same = NULL
                WHERE match_id = %s
            """, (match_id,))

            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Match not found")

            return {"message": "Verification undone", "match_id": match_id}


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


def cleanup_zombie_browser_processes():
    """
    Clean up SCRAPER-RELATED zombie Chrome/Playwright processes to prevent thread exhaustion.
    This prevents accumulation of browser processes from previous scrapes.

    IMPORTANT: Only kills browsers launched by Playwright/crawl4ai, NOT user's Chrome.
    Identifies scraper browsers by checking for:
    - 'playwright' or 'crawl4ai' in command line
    - '--headless' flag (scrapers run headless)
    - '--disable-dev-shm-usage' (our scraper-specific flag)
    """
    if not PSUTIL_AVAILABLE:
        print("  [CLEANUP] psutil not available - skipping zombie process cleanup")
        return 0

    try:
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pinfo = proc.info
                name = pinfo['name'].lower() if pinfo['name'] else ''
                cmdline = pinfo['cmdline'] if pinfo['cmdline'] else []
                cmdline_str = ' '.join(cmdline).lower()

                # Only process Chrome/Chromium
                if not any(browser in name for browser in ['chrome', 'chromium']):
                    continue

                # SAFETY CHECK: Only kill if it matches scraper-specific patterns
                is_scraper_browser = False

                # Check 1: Playwright or crawl4ai in command line
                if 'playwright' in cmdline_str or 'crawl4ai' in cmdline_str:
                    is_scraper_browser = True

                # Check 2: Has scraper-specific flags AND is headless
                elif any(flag in cmdline for flag in [
                    '--disable-dev-shm-usage',  # Our specific flag
                    '--no-sandbox'  # Common in automated browsers
                ]) and '--headless' in cmdline:
                    # Additional check: user Chrome will have profile flags
                    has_user_profile = any(
                        '--profile-directory' in str(arg) or
                        ('--user-data-dir' in str(arg) and os.path.expanduser('~') in str(arg))
                        for arg in cmdline
                    )
                    if not has_user_profile:
                        is_scraper_browser = True

                if is_scraper_browser:
                    # Check if it's a zombie or stuck
                    try:
                        proc_obj = psutil.Process(pinfo['pid'])
                        # Kill if zombie or consuming no CPU (likely stuck)
                        if proc_obj.status() == psutil.STATUS_ZOMBIE or \
                           (proc_obj.cpu_percent(interval=0.1) == 0 and proc_obj.create_time() < (psutil.boot_time() + 300)):
                            print(f"  [CLEANUP] Killing zombie scraper browser: PID={pinfo['pid']} {name}")
                            proc_obj.kill()
                            killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                pass

        if killed_count > 0:
            print(f"  [CLEANUP] Killed {killed_count} zombie scraper browser processes")
        return killed_count
    except Exception as e:
        print(f"  [CLEANUP] Error during zombie process cleanup: {e}")
        return 0


def scrape_single_url(url: str) -> dict:
    """
    Scrape a single URL and return result dict.
    Returns {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    process = None
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

        # Use Popen for better process control and cleanup
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

        # Wait for process with timeout
        try:
            stdout, stderr = process.communicate(timeout=120)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            # Kill the process and all its children on timeout
            print(f"  [PARALLEL] TIMEOUT: {url} - killing process tree")
            try:
                # Try to kill process group (includes child processes like Chrome)
                if PSUTIL_AVAILABLE:
                    # Use psutil to kill process tree (works on Windows and Linux)
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    parent.kill()
                    process.wait(timeout=5)
                elif hasattr(os, 'killpg'):
                    # Unix: kill process group
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.wait(timeout=5)
                else:
                    # Fallback: just kill the main process
                    process.kill()
                    process.wait(timeout=5)
            except Exception as kill_err:
                print(f"  [PARALLEL] Error killing process: {kill_err}")
            return {"success": False, "url": url, "error": "Scraper timed out (120s)"}
        finally:
            # Ensure process is cleaned up
            if process and process.poll() is None:
                try:
                    if PSUTIL_AVAILABLE:
                        # Kill process tree
                        try:
                            parent = psutil.Process(process.pid)
                            children = parent.children(recursive=True)
                            for child in children:
                                try:
                                    child.kill()
                                except psutil.NoSuchProcess:
                                    pass
                            parent.kill()
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass

        if returncode != 0:
            error_msg = stderr or stdout or 'Unknown error'
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

    except Exception as e:
        # Ensure process cleanup on any exception
        if process and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass
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

    # Clean up zombie browser processes before starting new scrape
    print(f"\n  [CLEANUP] Checking for zombie browser processes...")
    cleanup_zombie_browser_processes()

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


# ==================== PRICE ALERTS API ====================

@app.get("/api/price-alerts/settings")
def get_alert_settings(user: dict = Depends(get_current_user)):
    """Get current alert configuration"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM price_alert_settings LIMIT 1")
        result = cur.fetchone()

        if not result:
            # Create default settings if none exist
            cur.execute("""
                INSERT INTO price_alert_settings
                (schedule_frequency, schedule_time, enabled)
                VALUES ('daily', '09:00:00', true)
                RETURNING *
            """)
            result = cur.fetchone()
            conn.commit()

        # RealDictRow to dict, convert datetime to string
        data = dict(result)
        if 'schedule_time' in data and data['schedule_time']:
            data['schedule_time'] = str(data['schedule_time'])
        if 'created_at' in data and data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = data['updated_at'].isoformat()
        if 'last_alert_sent_at' in data and data['last_alert_sent_at']:
            data['last_alert_sent_at'] = data['last_alert_sent_at'].isoformat()

        return data


@app.put("/api/price-alerts/settings")
def update_alert_settings(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Update schedule configuration"""
    # Validate frequency
    frequency = data.get('schedule_frequency')
    if frequency not in ['immediate', 'hourly', 'daily', 'weekly']:
        raise HTTPException(status_code=400, detail="Invalid schedule_frequency")

    # Validate schedule_time format if provided
    schedule_time = data.get('schedule_time', None)
    if schedule_time and not isinstance(schedule_time, str):
        raise HTTPException(status_code=400, detail="schedule_time must be a string")

    # Default to '09:00:00' if not provided
    if not schedule_time:
        schedule_time = '09:00:00'

    # Validate schedule_day if weekly
    schedule_day = data.get('schedule_day', None)
    if frequency == 'weekly':
        if schedule_day is None or not (0 <= schedule_day <= 6):
            raise HTTPException(status_code=400, detail="schedule_day must be 0-6 for weekly frequency")

    enabled = data.get('enabled', True)

    with get_db() as conn:
        cur = conn.cursor()

        # Check if settings row exists
        cur.execute("SELECT COUNT(*) as count FROM price_alert_settings")
        result = cur.fetchone()
        count = result['count']

        if count == 0:
            # Insert new settings
            cur.execute("""
                INSERT INTO price_alert_settings
                (schedule_frequency, schedule_time, schedule_day, enabled)
                VALUES (%s, %s, %s, %s)
            """, (frequency, schedule_time, schedule_day, enabled))
        else:
            # Update existing settings
            cur.execute("""
                UPDATE price_alert_settings SET
                    schedule_frequency = %s,
                    schedule_time = %s,
                    schedule_day = %s,
                    enabled = %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (frequency, schedule_time, schedule_day, enabled))

        conn.commit()

    return {"success": True}


@app.get("/api/price-alerts/emails")
def get_alert_emails(user: dict = Depends(get_current_user)):
    """List all email recipients"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT email_id, email, verified, created_at FROM price_alert_emails ORDER BY created_at")
        rows = cur.fetchall()
        # Convert RealDictRow to dict and serialize datetimes
        result = []
        for row in rows:
            data = dict(row)
            if 'created_at' in data and data['created_at']:
                data['created_at'] = data['created_at'].isoformat()
            result.append(data)
        return result


@app.post("/api/price-alerts/emails")
def add_alert_email(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Add email to recipient list"""
    import re
    import psycopg2

    email = data.get('email', '').strip().lower()

    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO price_alert_emails (email, verified)
                VALUES (%s, false)
                RETURNING email_id, email, verified, created_at
            """, (email,))
            result = cur.fetchone()
            conn.commit()
            # Convert RealDictRow to dict and serialize datetime
            data = dict(result)
            if 'created_at' in data and data['created_at']:
                data['created_at'] = data['created_at'].isoformat()
            return data
        except psycopg2.IntegrityError:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Email already exists")


@app.delete("/api/price-alerts/emails/{email_id}")
def remove_alert_email(
    email_id: int,
    user: dict = Depends(get_current_user)
):
    """Remove email from recipient list"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM price_alert_emails WHERE email_id = %s",
            (email_id,)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Email not found")
        conn.commit()
    return {"success": True}


@app.get("/api/price-alerts/history")
def get_alert_history(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get recent alert send history"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM price_alert_history
            ORDER BY sent_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        # Convert RealDictRow to dict and serialize datetimes
        result = []
        for row in rows:
            data = dict(row)
            for key in ['sent_at', 'period_start', 'period_end']:
                if key in data and data[key]:
                    data[key] = data[key].isoformat()
            result.append(data)
        return result


@app.post("/api/price-alerts/test")
def send_test_alert(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Send test email to verify configuration"""
    email = data.get('email', '').strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    from services.email_service import EmailService

    email_service = EmailService()
    success = email_service.send_test_email(email)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check SMTP configuration.")

    return {"success": True, "message": f"Test email sent to {email}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
