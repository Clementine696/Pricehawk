from typing import Optional

from fastapi import APIRouter, Depends, Query
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.get("/api/categories")
def get_categories(
    user: dict = Depends(get_current_user),
    retailer: Optional[str] = Query(None),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            where_clause = ""
            params = []
            if retailer:
                where_clause = "WHERE c.retailer_id = %s"
                params.append(retailer)
            cur.execute(f"""
                SELECT c.retailer_id, c.category_id, c.category_name, COUNT(p.id) as product_count
                FROM categories c
                LEFT JOIN products p ON c.retailer_id = p.retailer_id AND c.category_id = p.category_id
                {where_clause}
                GROUP BY c.retailer_id, c.category_id, c.category_name
                ORDER BY c.retailer_id, c.category_name
            """, params)
            return {"categories": cur.fetchall()}
