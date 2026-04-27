from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from routers.deps import get_current_user

router = APIRouter()


@router.get("/api/price-alerts/settings")
def get_alert_settings(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM price_alert_settings LIMIT 1")
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Settings not found")
            return dict(row)


@router.put("/api/price-alerts/settings")
def update_alert_settings(body: dict, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE price_alert_settings SET
                    schedule_frequency = %s, schedule_time = %s,
                    schedule_day = %s, enabled = %s, updated_at = NOW()
            """, (
                body.get("schedule_frequency", "daily"),
                body.get("schedule_time", "09:00:00"),
                body.get("schedule_day"),
                body.get("enabled", True),
            ))
            conn.commit()
    return {"success": True}


@router.get("/api/price-alerts/emails")
def get_alert_emails(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM price_alert_emails ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]


@router.post("/api/price-alerts/emails")
def add_alert_email(body: dict, user: dict = Depends(get_current_user)):
    email = (body.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO price_alert_emails (email, verified) VALUES (%s, TRUE) RETURNING *", (email,))
                row = cur.fetchone()
                conn.commit()
                return dict(row)
            except Exception:
                raise HTTPException(status_code=409, detail="Email already exists")


@router.delete("/api/price-alerts/emails/{email_id}")
def delete_alert_email(email_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM price_alert_emails WHERE email_id = %s RETURNING email_id", (email_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Email not found")
            conn.commit()
    return {"success": True}
