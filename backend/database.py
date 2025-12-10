import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print(f"DB_HOST from .env: {os.environ.get('DB_HOST')}")

# Database configuration - supports DATABASE_URL or individual components
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL for cloud deployments (Railway, Neon, etc.)
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path[1:],  # Remove leading slash
        "user": parsed.username,
        "password": parsed.password,
        "sslmode": "require",  # Required for cloud databases
    }
else:
    # Individual DB_* variables configuration
    db_host = os.environ.get("DB_HOST", "localhost")
    DB_CONFIG = {
        "host": db_host,
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "pricehawk"),
        "user": os.environ.get("DB_USER", "pricehawk"),
        "password": os.environ.get("DB_PASSWORD", "pricehawk_secret"),
    }
    # Add SSL for non-localhost (cloud databases like Neon)
    if db_host != "localhost":
        DB_CONFIG["sslmode"] = "require"


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
