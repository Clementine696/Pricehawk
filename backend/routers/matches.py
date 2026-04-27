from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.post("/api/matches/{match_id}/verify")
def verify_match(match_id: int, body: dict, user: dict = Depends(get_current_user)):
    is_same = body.get("is_same")
    if is_same is None:
        raise HTTPException(status_code=400, detail="is_same is required")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE product_matches SET is_verified = TRUE, is_same = %s, verified_at = NOW(), updated_at = NOW()
                WHERE match_id = %s RETURNING match_id
            """, (is_same, match_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Match not found")
            conn.commit()
    return {"match_id": match_id, "is_verified": True, "is_same": is_same}


@router.post("/api/matches/{match_id}/undo")
def undo_match(match_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE product_matches SET is_verified = FALSE, is_same = NULL, verified_at = NULL, updated_at = NOW()
                WHERE match_id = %s RETURNING match_id
            """, (match_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Match not found")
            conn.commit()
    return {"match_id": match_id, "is_verified": False, "is_same": None}
