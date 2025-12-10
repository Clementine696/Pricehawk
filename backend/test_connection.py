"""
Test database connection
Run: python test_connection.py
"""
import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    print(f"Using DATABASE_URL")
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
    print("Using individual DB_* variables")
    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "pricehawk"),
        "user": os.environ.get("DB_USER", "pricehawk"),
        "password": os.environ.get("DB_PASSWORD", "pricehawk_secret"),
        "sslmode": "require",  # Required for Neon
    }

print(f"\nConnecting to:")
print(f"  Host: {DB_CONFIG['host']}")
print(f"  Port: {DB_CONFIG['port']}")
print(f"  Database: {DB_CONFIG['database']}")
print(f"  User: {DB_CONFIG['user']}")
print(f"  SSL: {DB_CONFIG.get('sslmode', 'disabled')}")

try:
    print("\nAttempting connection...")
    conn = psycopg2.connect(**DB_CONFIG)

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    print(f"\n✓ Connection successful!")
    print(f"  PostgreSQL: {version}")

    # Check if tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    if tables:
        print(f"\n  Tables found: {len(tables)}")
        for table in tables:
            print(f"    - {table[0]}")
    else:
        print("\n  No tables found (database is empty)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n✗ Connection failed!")
    print(f"  Error: {e}")
