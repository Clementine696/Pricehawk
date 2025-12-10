import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pricehawk",
    "user": "pricehawk",
    "password": "pricehawk_secret",
}


@contextmanager
def get_db():
    """Get database connection"""
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Get user from database by username"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, hashed_password, is_active FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()


def create_user(username: str, hashed_password: str) -> dict:
    """Create a new user"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, hashed_password) VALUES (%s, %s) RETURNING user_id, username",
                (username, hashed_password)
            )
            return cur.fetchone()
