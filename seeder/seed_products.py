"""
Seed script to populate retailers and top 10 products from each JSON file
Run from project root: python seeder/seed_products.py
"""
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pricehawk",
    "user": "pricehawk",
    "password": "pricehawk_secret",
}

# Retailer code mapping (retailer_id is now string)
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


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def seed_retailer(conn, name: str) -> str:
    """Insert retailer and return retailer_id (string code)"""
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
        # Get first image if available
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
                product.get("current_price"),  # lowest = current initially
                product.get("current_price"),  # highest = current initially
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

    print(f"Found {len(json_files)} product files")

    conn = get_db()

    total_products = 0

    for json_file in json_files:
        print(f"\nProcessing: {json_file.name}")

        with open(json_file, "r", encoding="utf-8") as f:
            products = json.load(f)

        if not products:
            print(f"  No products found")
            continue

        # Get retailer name from first product
        retailer_name = products[0].get("retailer", "Unknown")

        # Skip unknown retailers
        if retailer_name not in RETAILER_CODES:
            print(f"  Unknown retailer: {retailer_name}, skipping...")
            continue

        # Seed retailer
        retailer_id = seed_retailer(conn, retailer_name)
        print(f"  Retailer: {retailer_name} (ID: {retailer_id})")

        # Seed top 10 products
        top_10 = products[:10]
        for product in top_10:
            try:
                product_id = seed_product(conn, retailer_id, product)

                # Add to price history
                if product.get("current_price"):
                    seed_price_history(conn, product_id, product["current_price"])

                print(f"    + {product.get('name', 'Unknown')[:50]}...")
                total_products += 1
            except Exception as e:
                print(f"    ! Error: {e}")

    conn.close()
    print(f"\n✓ Seeded {total_products} products from {len(json_files)} retailers")


if __name__ == "__main__":
    main()
