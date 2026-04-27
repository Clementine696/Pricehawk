from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.get("/api/pbl/locations")
def get_pbl_locations(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM makro_locations ORDER BY name")
            return {"locations": [dict(r) for r in cur.fetchall()]}


@router.post("/api/pbl/locations")
def create_pbl_location(body: dict, user: dict = Depends(get_current_user)):
    name = (body.get("name") or "").strip()
    branch_code = (body.get("branch_code") or "").strip()
    region = (body.get("region") or "").strip() or None
    if not name or not branch_code:
        raise HTTPException(status_code=400, detail="name and branch_code are required")
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO makro_locations (name, branch_code, region) VALUES (%s, %s, %s) RETURNING *",
                    (name, branch_code, region)
                )
                row = cur.fetchone()
                conn.commit()
                return dict(row)
            except Exception:
                raise HTTPException(status_code=409, detail=f"Branch code '{branch_code}' already exists")


@router.delete("/api/pbl/locations/{location_id}")
def delete_pbl_location(location_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM makro_locations WHERE id = %s RETURNING id", (location_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Location not found")
            conn.commit()
    return {"success": True}


@router.get("/api/pbl/settings")
def get_pbl_settings(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT watchlist_id FROM pbl_monitored_watchlists")
            watchlist_ids = [r["watchlist_id"] for r in cur.fetchall()]
            cur.execute("SELECT location_id FROM pbl_monitored_locations")
            location_ids = [r["location_id"] for r in cur.fetchall()]
    return {"watchlist_ids": watchlist_ids, "location_ids": location_ids}


@router.post("/api/pbl/settings")
def save_pbl_settings(body: dict, user: dict = Depends(get_current_user)):
    watchlist_ids = body.get("watchlist_ids", [])
    location_ids = body.get("location_ids", [])
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pbl_monitored_watchlists")
            for wid in watchlist_ids:
                cur.execute("INSERT INTO pbl_monitored_watchlists (watchlist_id) VALUES (%s) ON CONFLICT DO NOTHING", (wid,))
            cur.execute("DELETE FROM pbl_monitored_locations")
            for lid in location_ids:
                cur.execute("INSERT INTO pbl_monitored_locations (location_id) VALUES (%s) ON CONFLICT DO NOTHING", (lid,))
            conn.commit()
    return {"success": True, "watchlist_ids": watchlist_ids, "location_ids": location_ids}


@router.get("/api/pbl/products")
def get_pbl_products(
    user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None),
    watchlist_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ml.id, ml.name, ml.branch_code as postal_code
                FROM pbl_monitored_locations pml
                JOIN makro_locations ml ON pml.location_id = ml.id
                WHERE ml.is_active = TRUE ORDER BY ml.branch_code
            """)
            locations = [dict(r) for r in cur.fetchall()]

            where_parts = ["pw.watchlist_id IN (SELECT watchlist_id FROM pbl_monitored_watchlists)"]
            params = []

            if watchlist_id:
                where_parts.append("pw.watchlist_id = %s")
                params.append(watchlist_id)
            if search:
                where_parts.append("(cfw.name ILIKE %s OR cfw.sku ILIKE %s)")
                pattern = f"%{search}%"
                params.extend([pattern, pattern])

            where_clause = " AND ".join(where_parts)

            cur.execute(f"SELECT COUNT(DISTINCT cfw.id) as count FROM watchlist_products pw JOIN products cfw ON pw.product_id = cfw.id WHERE {where_clause}", params)
            total = cur.fetchone()["count"]

            offset = (page - 1) * page_size
            cur.execute(f"""
                SELECT DISTINCT cfw.id as cfw_id, cfw.sku as cfw_sku, cfw.name as cfw_name,
                    cfw.brand, cfw.current_price as cfw_price, cfw.image_url,
                    c.category_name, mp.id as makro_id, mp.sku as makro_sku, mp.name as makro_name,
                    mp.current_price as makro_price_default, pw.watchlist_id, w.name as watchlist_name
                FROM watchlist_products pw
                JOIN products cfw ON pw.product_id = cfw.id
                JOIN watchlists w ON pw.watchlist_id = w.id
                LEFT JOIN categories c ON cfw.retailer_id = c.retailer_id AND cfw.category_id = c.category_id
                JOIN product_matches pm ON pm.cfw_product_id = cfw.id AND pm.is_verified = TRUE AND pm.is_same = TRUE
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE {where_clause}
                ORDER BY cfw.sku LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cur.fetchall()

            price_map = {}
            if rows and locations:
                makro_ids = list({r["makro_id"] for r in rows})
                loc_ids = [l["id"] for l in locations]
                cur.execute(f"""
                    SELECT makro_product_id, location_id, price FROM makro_location_prices
                    WHERE makro_product_id IN ({','.join(['%s'] * len(makro_ids))})
                      AND location_id IN ({','.join(['%s'] * len(loc_ids))})
                """, makro_ids + loc_ids)
                for pr in cur.fetchall():
                    price_map[(pr["makro_product_id"], pr["location_id"])] = pr["price"]

            products = []
            for r in rows:
                loc_prices = [
                    {"location_id": loc["id"], "name": loc["name"], "postal_code": loc["postal_code"],
                     "price": float(price_map[(r["makro_id"], loc["id"])]) if (r["makro_id"], loc["id"]) in price_map else None}
                    for loc in locations
                ]
                products.append({**dict(r), "location_prices": loc_prices})

            cur.execute("""
                SELECT w.id, w.name FROM pbl_monitored_watchlists pmw
                JOIN watchlists w ON pmw.watchlist_id = w.id ORDER BY w.name
            """)
            watchlists = [dict(r) for r in cur.fetchall()]

            return {
                "products": products,
                "locations": locations,
                "watchlists": watchlists,
                "total": total,
                "pagination": {"page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}
            }


@router.get("/api/pbl/products/{cfw_sku}")
def get_pbl_product_detail(cfw_sku: str, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.sku, p.name, p.brand, p.current_price, p.image_url, c.category_name
                FROM products p
                LEFT JOIN categories c ON p.retailer_id = c.retailer_id AND p.category_id = c.category_id
                WHERE p.sku = %s AND p.retailer_id = 'cfw'
            """, (cfw_sku,))
            cfw = cur.fetchone()
            if not cfw:
                raise HTTPException(status_code=404, detail="CFW product not found")

            cur.execute("""
                SELECT mp.id, mp.sku, mp.name, mp.current_price
                FROM product_matches pm
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE pm.cfw_product_id = %s AND pm.is_verified = TRUE AND pm.is_same = TRUE LIMIT 1
            """, (cfw["id"],))
            makro = cur.fetchone()

            cur.execute("""
                SELECT ml.id as location_id, ml.name as branch_name, ml.branch_code as postal_code,
                       mlp.price as makro_price, mlp.scraped_at
                FROM makro_locations ml
                LEFT JOIN makro_location_prices mlp ON mlp.location_id = ml.id AND mlp.makro_product_id = %s
                WHERE ml.id IN (SELECT location_id FROM pbl_monitored_locations) AND ml.is_active = TRUE
                ORDER BY ml.branch_code
            """, (makro["id"] if makro else -1,))
            locations = [dict(r) for r in cur.fetchall()]

            return {"cfw": dict(cfw), "makro": dict(makro) if makro else None, "locations": locations}
