from fastapi import APIRouter, Depends
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.get("/api/dashboard/stats")
def get_dashboard_stats(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT retailer_id, COUNT(*) as product_count, COUNT(DISTINCT category_id) as category_count
                FROM products GROUP BY retailer_id
            """)
            retailer_stats = cur.fetchall()

            cur.execute("SELECT COUNT(*) as total FROM products")
            total_products = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM categories")
            total_categories = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM retailers")
            total_retailers = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM price_history WHERE recorded_at >= NOW() - INTERVAL '7 days'")
            recent_updates = cur.fetchone()["total"]

            cur.execute("""
                SELECT retailer_id, AVG(current_price) as avg_price,
                       MIN(current_price) as min_price, MAX(current_price) as max_price
                FROM products WHERE current_price IS NOT NULL GROUP BY retailer_id
            """)
            price_stats = cur.fetchall()

            return {
                "total_products": total_products,
                "total_retailers": total_retailers,
                "total_categories": total_categories,
                "total_matches": 0,
                "pending_reviews": 0,
                "recent_price_updates": recent_updates,
                "retailer_stats": [
                    {"retailer_id": r["retailer_id"], "product_count": r["product_count"], "category_count": r["category_count"]}
                    for r in retailer_stats
                ],
                "price_stats": [
                    {
                        "retailer_id": p["retailer_id"],
                        "avg_price": float(p["avg_price"]) if p["avg_price"] else None,
                        "min_price": float(p["min_price"]) if p["min_price"] else None,
                        "max_price": float(p["max_price"]) if p["max_price"] else None,
                    }
                    for p in price_stats
                ],
            }


@router.get("/api/retailers")
def get_retailers(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.retailer_id, r.name, r.domain, COUNT(p.id) as product_count
                FROM retailers r LEFT JOIN products p ON r.retailer_id = p.retailer_id
                GROUP BY r.retailer_id, r.name, r.domain ORDER BY r.retailer_id
            """)
            retailers = cur.fetchall()
            return {
                "retailers": [
                    {"retailer_id": r["retailer_id"], "name": r["name"], "domain": r["domain"], "product_count": r["product_count"]}
                    for r in retailers
                ]
            }
