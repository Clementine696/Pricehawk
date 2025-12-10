"""
Seed script for products from JSON files
Run: python seeder/seed_products.py
"""
import os
import json
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


# Retailer code mapping
RETAILER_CODES = {
    "Thai Watsadu": "twd",
    "HomePro": "hp",
    "MegaHome": "mgh",
    "Do Home": "dh",
    "Boonthavorn": "btv",
    "Global House": "gbh",
}

RETAILER_DOMAINS = {
    "Thai Watsadu": "thaiwatsadu.com",
    "HomePro": "homepro.co.th",
    "MegaHome": "megahome.co.th",
    "Do Home": "dohome.co.th",
    "Boonthavorn": "boonthavorn.com",
    "Global House": "globalhouse.co.th",
}


def seed_retailer(conn, name: str) -> str:
    """Insert retailer and return retailer_id"""
    code = RETAILER_CODES.get(name)
    if not code:
        raise ValueError(f"Unknown retailer: {name}")

    domain = RETAILER_DOMAINS.get(name)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO retailers (retailer_id, name, domain)
            VALUES (%s, %s, %s)
            ON CONFLICT (retailer_id) DO UPDATE SET name = EXCLUDED.name
            RETURNING retailer_id
            """,
            (code, name, domain)
        )
        conn.commit()
        return cur.fetchone()["retailer_id"]


def seed_product(conn, retailer_id: str, product: dict) -> int:
    """Insert product and return product_id"""
    with conn.cursor() as cur:
        image = product.get("images", [None])[0] if product.get("images") else None

        cur.execute(
            """
            INSERT INTO products (
                retailer_id, sku, name, brand, category, link, image, description,
                current_price, original_price, lowest_price, highest_price
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (retailer_id, sku) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                category = EXCLUDED.category,
                link = EXCLUDED.link,
                image = EXCLUDED.image,
                description = EXCLUDED.description,
                current_price = EXCLUDED.current_price,
                original_price = EXCLUDED.original_price,
                last_updated_at = NOW()
            RETURNING product_id
            """,
            (
                retailer_id,
                product.get("sku"),
                product.get("name"),
                product.get("brand"),
                product.get("category"),
                product.get("url"),
                image,
                product.get("description"),
                product.get("current_price"),
                product.get("original_price"),
                product.get("current_price"),
                product.get("current_price"),
            )
        )
        conn.commit()
        return cur.fetchone()["product_id"]


def seed_price_history(conn, product_id: int, price: float):
    """Add initial price to history"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO price_history (product_id, price, currency) VALUES (%s, %s, 'THB')",
            (product_id, price)
        )
        conn.commit()


def main():
    seeder_dir = Path(__file__).parent
    json_files = list(seeder_dir.glob("*_products.json"))

    if not json_files:
        print("No product JSON files found")
        return

    print(f"Found {len(json_files)} product files")

    total_products = 0

    with get_db() as conn:
        for json_file in json_files:
            print(f"\nProcessing: {json_file.name}")

            with open(json_file, "r", encoding="utf-8") as f:
                products = json.load(f)

            if not products:
                print("  No products found")
                continue

            retailer_name = products[0].get("retailer", "Unknown")

            if retailer_name not in RETAILER_CODES:
                print(f"  Unknown retailer: {retailer_name}, skipping...")
                continue

            retailer_id = seed_retailer(conn, retailer_name)
            print(f"  Retailer: {retailer_name} (ID: {retailer_id})")

            # Seed top 10 products
            top_10 = products[:]
            for product in top_10:
                try:
                    product_id = seed_product(conn, retailer_id, product)

                    if product.get("current_price"):
                        seed_price_history(conn, product_id, product["current_price"])

                    print(f"    + {product.get('name', 'Unknown')[:50]}...")
                    total_products += 1
                except Exception as e:
                    print(f"    ! Error: {e}")

    print(f"\nSeeded {total_products} products")


if __name__ == "__main__":
    print(f"DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("Seeding products...")
    main()
    print("Done!")
