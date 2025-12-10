"""
Seed script for users
Run: python seeder/seed_users.py
"""
import os
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env from this folder
load_dotenv(Path(__file__).parent / ".env")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path[1:],
        "user": parsed.username,
        "password": parsed.password,
        "sslmode": "require",
    }
else:
    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "pricehawk"),
        "user": os.environ.get("DB_USER", "pricehawk"),
        "password": os.environ.get("DB_PASSWORD", "pricehawk_secret"),
    }


@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_user_by_username(username: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()


def seed_admin():
    """Create admin user if not exists"""
    username = "admin"
    password = "password123"

    existing = get_user_by_username(username)
    if existing:
        print(f"User '{username}' already exists")
        return

    hashed = hash_password(password)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, hashed_password) VALUES (%s, %s)",
                (username, hashed)
            )
    print(f"Created user '{username}' with password '{password}'")


if __name__ == "__main__":
    print(f"DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("Seeding users...")
    seed_admin()
    print("Done!")
