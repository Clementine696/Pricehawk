import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.get("/api/price-formula")
def get_price_formula_matches(
    user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            where_parts = ["pm.is_verified = TRUE", "pm.is_same = TRUE"]
            params = []

            if search:
                where_parts.append("(cp.name ILIKE %s OR cp.sku ILIKE %s OR mp.name ILIKE %s OR mp.sku ILIKE %s)")
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern, pattern])

            where_clause = " AND ".join(where_parts)

            cur.execute(
                f"SELECT COUNT(*) as count FROM product_matches pm "
                f"JOIN products cp ON pm.cfw_product_id = cp.id "
                f"JOIN products mp ON pm.makro_product_id = mp.id "
                f"WHERE {where_clause}", params
            )
            total = cur.fetchone()["count"]

            offset = (page - 1) * page_size
            cur.execute(f"""
                SELECT pm.match_id, pm.price_formula,
                    cp.id as cfw_id, cp.sku as cfw_sku, cp.name as cfw_name,
                    cp.brand as cfw_brand, cp.current_price as cfw_price, cp.image_url as cfw_image,
                    mp.id as makro_id, mp.sku as makro_sku, mp.name as makro_name,
                    mp.current_price as makro_price, mp.image_url as makro_image
                FROM product_matches pm
                JOIN products cp ON pm.cfw_product_id = cp.id
                JOIN products mp ON pm.makro_product_id = mp.id
                WHERE {where_clause}
                ORDER BY cp.sku LIMIT %s OFFSET %s
            """, params + [page_size, offset])

            return {
                "matches": [dict(r) for r in cur.fetchall()],
                "total": total,
                "pagination": {"page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}
            }


@router.patch("/api/price-formula/{match_id}")
def save_price_formula(match_id: int, body: dict, user: dict = Depends(get_current_user)):
    formula = body.get("price_formula", None)
    if formula is not None:
        formula = formula.strip() or None
        if formula and not re.match(r'^[*/][0-9]+(\.[0-9]+)?(/[0-9]+(\.[0-9]+)?)?$', formula):
            raise HTTPException(status_code=400, detail="Invalid formula. Use format like *5, /2, *5/2")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE product_matches SET price_formula = %s, updated_at = NOW() WHERE match_id = %s RETURNING match_id",
                (formula, match_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Match not found")
            conn.commit()

    return {"match_id": match_id, "price_formula": formula}
