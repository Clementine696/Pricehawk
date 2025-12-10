"""Seed script to create initial admin user"""
import bcrypt
from database import get_db, get_user_by_username


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed_admin():
    """Create admin user if not exists"""
    username = "admin"
    password = "password123"

    # Check if admin already exists
    existing = get_user_by_username(username)
    if existing:
        print(f"User '{username}' already exists")
        return

    # Create admin user
    hashed = hash_password(password)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, hashed_password) VALUES (%s, %s)",
                (username, hashed)
            )
    print(f"Created user '{username}' with password '{password}'")


if __name__ == "__main__":
    seed_admin()
