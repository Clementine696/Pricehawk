"""
Seed only products that appear in match Excel files.
Run: python seeder/seed_products_matched.py

This script:
1. Reads twd_*.xlsx match files to extract all SKUs
2. Reads *_products.json files
3. Inserts only products whose SKU appears in match results
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlparse
from dotenv import load_dotenv

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    exit(1)

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
    db_host = os.environ.get("DB_HOST", "localhost")
    DB_CONFIG = {
        "host": db_host,
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "pricehawk"),
        "user": os.environ.get("DB_USER", "pricehawk"),
        "password": os.environ.get("DB_PASSWORD", "pricehawk_secret"),
    }
    if db_host != "localhost":
        DB_CONFIG["sslmode"] = "require"


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


# Retailer mappings
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

# Map filename keywords to retailer codes
COMPETITOR_MAPPING = {
    "homepro": "hp",
    "megahome": "mgh",
    "dohome": "dh",
    "boonthavorn": "btv",
    "globalhouse": "gbh",
}


def extract_skus_from_excel(seeder_dir: Path, twd_col: str = "TWD_SKU", comp_col: str = "COMPETITOR_SKU") -> dict:
    """
    Read all twd_*.xlsx files and extract SKUs.
    Returns dict: {retailer_id: set of SKUs}
    """
    excel_files = list(seeder_dir.glob("twd_*.xlsx"))

    if not excel_files:
        print("No Excel match files found (twd_*.xlsx)")
        return {}

    print(f"Found {len(excel_files)} Excel match files")

    # SKUs by retailer: {"twd": set(), "hp": set(), ...}
    skus_by_retailer = {"twd": set()}

    for excel_file in excel_files:
        filename = excel_file.name.lower()

        # Determine competitor retailer from filename
        competitor_id = None
        for key, rid in COMPETITOR_MAPPING.items():
            if key in filename:
                competitor_id = rid
                break

        if not competitor_id:
            print(f"  Skipping {excel_file.name} - unknown competitor")
            continue

        if competitor_id not in skus_by_retailer:
            skus_by_retailer[competitor_id] = set()

        # Read Excel
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            print(f"  Error reading {excel_file.name}: {e}")
            continue

        # Extract TWD SKUs
        if twd_col in df.columns:
            twd_skus = df[twd_col].dropna().astype(str).str.strip().tolist()
            skus_by_retailer["twd"].update(twd_skus)

        # Extract competitor SKUs
        if comp_col in df.columns:
            comp_skus = df[comp_col].dropna().astype(str).str.strip().tolist()
            skus_by_retailer[competitor_id].update(comp_skus)

        print(f"  {excel_file.name}: {len(twd_skus) if twd_col in df.columns else 0} TWD, {len(comp_skus) if comp_col in df.columns else 0} {competitor_id}")

    # Print summary
    print("\nSKUs extracted:")
    for rid, skus in skus_by_retailer.items():
        print(f"  {rid}: {len(skus)} unique SKUs")

    return skus_by_retailer


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
    import argparse

    parser = argparse.ArgumentParser(description="Seed only products that appear in match results")
    parser.add_argument("--twd-col", default="TWD_SKU", help="Column name for Thai Watsadu SKU (default: TWD_SKU)")
    parser.add_argument("--comp-col", default="COMPETITOR_SKU", help="Column name for competitor SKU (default: COMPETITOR_SKU)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be inserted without actually inserting")

    args = parser.parse_args()

    seeder_dir = Path(__file__).parent

    print("=" * 50)
    print("Seed Products (Matched Only)")
    print("=" * 50)
    print(f"DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    # Step 1: Extract SKUs from Excel files
    print("\n[1/3] Extracting SKUs from Excel match files...")
    skus_by_retailer = extract_skus_from_excel(seeder_dir, args.twd_col, args.comp_col)

    if not skus_by_retailer:
        print("No SKUs found. Make sure Excel files are in seeder folder.")
        return

    # Step 2: Read product JSON files
    print("\n[2/3] Reading product JSON files...")
    json_files = list(seeder_dir.glob("*_products.json"))

    if not json_files:
        print("No product JSON files found")
        return

    print(f"Found {len(json_files)} product files")

    # Step 3: Insert filtered products
    print("\n[3/3] Inserting matched products...")

    total_products = 0
    total_skipped = 0

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

            retailer_id = RETAILER_CODES[retailer_name]

            # Get SKUs for this retailer
            retailer_skus = skus_by_retailer.get(retailer_id, set())

            if not retailer_skus:
                print(f"  No matched SKUs for {retailer_name}, skipping...")
                continue

            # Seed retailer
            seed_retailer(conn, retailer_name)
            print(f"  Retailer: {retailer_name} (ID: {retailer_id})")
            print(f"  Filtering {len(products)} products -> {len(retailer_skus)} matched SKUs")

            inserted = 0
            skipped = 0

            for product in products:
                sku = str(product.get("sku", "")).strip()

                if sku not in retailer_skus:
                    skipped += 1
                    continue

                if args.dry_run:
                    print(f"    [DRY RUN] Would insert: {sku}")
                    inserted += 1
                else:
                    try:
                        product_id = seed_product(conn, retailer_id, product)

                        if product.get("current_price"):
                            seed_price_history(conn, product_id, product["current_price"])

                        inserted += 1
                    except Exception as e:
                        print(f"    ! Error inserting {sku}: {e}")

            print(f"  Inserted: {inserted}, Skipped: {skipped}")
            total_products += inserted
            total_skipped += skipped

    print("\n" + "=" * 50)
    if args.dry_run:
        print(f"DRY RUN: Would insert {total_products} products")
    else:
        print(f"Done! Inserted {total_products} products, skipped {total_skipped}")
    print("=" * 50)


if __name__ == "__main__":
    main()
