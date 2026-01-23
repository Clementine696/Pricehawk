"""
Seed Thai Watsadu products (UPSERT) and their top 5 matches per retailer.

This script:
1. UPSERTS ALL Thai Watsadu products from data/thaiwatsadu.json (insert new or update existing)
2. Reads match Excel files from part1/
3. For each Thai Watsadu product, inserts ONLY TOP 5 matches per retailer
4. Gets product details from data/{retailer}.json files

Run: python seed_new.py
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlparse
from dotenv import load_dotenv
from typing import Dict, Optional

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    exit(1)

# Load .env from this folder
load_dotenv(Path(__file__).parent / ".env")

# ============== CONFIGURATION ==============
# Change these to switch between different data sources
DATA_FOLDER = "data"           # Folder containing JSON product files
MATCH_FOLDER = "part3"         # Folder containing Excel match files (part1, part2, etc.)
# ==========================================

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
EXCEL_TO_RETAILER = {
    "homepro": "hp",
    "megahome": "mgh",
    "dohome": "dh",
    "boonthavorn": "btv",
    "globalhouse": "gbh",
}

JSON_FILES = {
    "hp": "homepro.json",
    "mgh": "megahome.json",
    "dh": "dohome.json",
    "btv": "boonthavorn.json",
    "gbh": "globalhouse.json",
}


def load_json_data(data_dir: Path) -> Dict[str, Dict[str, dict]]:
    """Load all JSON files and create SKU lookup dictionaries"""
    print("\n📚 Loading JSON data files...")
    json_data = {}
    
    # Load Thai Watsadu
    twd_file = data_dir / "thaiwatsadu.json"
    with open(twd_file, encoding="utf-8") as f:
        twd_products = json.load(f)
        json_data["twd"] = {p["sku"]: p for p in twd_products}
        print(f"  ✓ Thai Watsadu: {len(json_data['twd'])} products")
    
    # Load competitors
    for retailer_code, json_file in JSON_FILES.items():
        file_path = data_dir / json_file
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                products = json.load(f)
                # For GlobalHouse, remove leading zeros from SKUs
                if retailer_code == "gbh":
                    json_data[retailer_code] = {
                        p["sku"].lstrip("0") if p.get("sku") else None: p 
                        for p in products if p.get("sku")
                    }
                else:
                    json_data[retailer_code] = {p["sku"]: p for p in products}
                print(f"  ✓ {json_file}: {len(json_data[retailer_code])} products")
        else:
            print(f"  ⚠ {json_file} not found, skipping")
            json_data[retailer_code] = {}
    
    return json_data


def load_match_data(part1_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all Excel match files and keep only top 5 per TWD SKU"""
    print("\n📊 Loading match Excel files (top 5 matches per TWD product)...")
    match_data = {}
    
    for excel_file in part1_dir.glob("twd_*_match_result_*.xlsx"):
        # Extract retailer name from filename
        filename = excel_file.stem.lower()
        for keyword, retailer_code in EXCEL_TO_RETAILER.items():
            if keyword in filename:
                df = pd.read_excel(excel_file)
                
                # Filter to keep only top 5 matches per TWD_SKU (based on RANK)
                df = df.sort_values(['TWD_SKU', 'RANK'])
                df = df.groupby('TWD_SKU').head(5)
                
                match_data[retailer_code] = df
                total_skus = df['TWD_SKU'].nunique()
                total_matches = len(df)
                print(f"  ✓ {excel_file.name}: {total_skus} TWD SKUs, {total_matches} matches")
                break
    
    return match_data


def upsert_product(conn, product_data: dict, retailer_code: str) -> Optional[int]:
    """Insert or update a product and return its product_id"""
    try:
        with conn.cursor() as cur:
            # UPSERT using ON CONFLICT
            cur.execute("""
                INSERT INTO products (
                    retailer_id, sku, name, brand, category, link, image,
                    description, current_price, original_price,
                    lowest_price, highest_price, currency, last_updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (retailer_id, sku) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    category = EXCLUDED.category,
                    link = EXCLUDED.link,
                    image = EXCLUDED.image,
                    description = EXCLUDED.description,
                    current_price = EXCLUDED.current_price,
                    original_price = EXCLUDED.original_price,
                    lowest_price = LEAST(products.lowest_price, EXCLUDED.current_price),
                    highest_price = GREATEST(products.highest_price, EXCLUDED.current_price),
                    last_updated_at = NOW()
                RETURNING product_id
            """, (
                retailer_code,
                product_data["sku"],
                product_data.get("name"),
                product_data.get("brand"),
                product_data.get("category"),
                product_data.get("url"),
                product_data.get("images", [None])[0] if product_data.get("images") else None,
                product_data.get("description"),
                product_data.get("current_price"),
                product_data.get("original_price") or product_data.get("current_price"),
                product_data.get("current_price"),  # lowest_price
                product_data.get("current_price"),  # highest_price
                "THB",
            ))
            
            result = cur.fetchone()
            conn.commit()
            return result["product_id"]
            
    except Exception as e:
        print(f"    ⚠ Error upserting product {product_data.get('sku')}: {e}")
        conn.rollback()
        return None


def insert_match(conn, base_product_id: int, candidate_product_id: int, 
                 retailer_code: str, match_score: float):
    """Insert a product match (skip if already exists)"""
    try:
        with conn.cursor() as cur:
            # Check if match already exists
            cur.execute("""
                SELECT match_id FROM product_matches
                WHERE base_product_id = %s AND candidate_product_id = %s
            """, (base_product_id, candidate_product_id))
            
            if cur.fetchone():
                return  # Match already exists
            
            # Insert match
            cur.execute("""
                INSERT INTO product_matches (
                    base_product_id, candidate_product_id, retailer_id,
                    is_same, confidence_score, match_type, verified_by_user
                )
                VALUES (%s, %s, %s, NULL, %s, 'auto', FALSE)
            """, (
                base_product_id,
                candidate_product_id,
                retailer_code,
                min(match_score, 1.0),  # Cap at 1.0
            ))
            
            conn.commit()
            
    except Exception as e:
        print(f"    ⚠ Error inserting match: {e}")
        conn.rollback()


def main():
    script_dir = Path(__file__).parent
    data_dir = script_dir / DATA_FOLDER
    match_dir = script_dir / MATCH_FOLDER
    
    print("="*70)
    print("🚀 Starting Product Seeding (UPSERT TWD + Top 5 Matches)")
    print("="*70)
    print(f"📂 Using match files from: {MATCH_FOLDER}/")
    
    # Load data
    json_data = load_json_data(data_dir)
    match_data = load_match_data(match_dir)
    
    print(f"\n📊 Summary:")
    print(f"  - Thai Watsadu products to upsert: {len(json_data['twd'])}")
    print(f"  - Retailers with match data: {len(match_data)}")
    
    # Connect to database
    with get_db() as conn:
        print("\n" + "="*70)
        print("📦 STEP 1: UPSERTING Thai Watsadu Products")
        print("="*70)
        
        twd_upserted = 0
        twd_failed = 0
        twd_product_ids = {}
        
        for sku, product in json_data["twd"].items():
            product_id = upsert_product(conn, product, "twd")
            if product_id:
                twd_product_ids[sku] = product_id
                twd_upserted += 1
                if twd_upserted % 100 == 0:
                    print(f"  Progress: {twd_upserted} products upserted...")
            else:
                twd_failed += 1
        
        print(f"\n✅ Thai Watsadu products:")
        print(f"  - Upserted (inserted/updated): {twd_upserted}")
        if twd_failed > 0:
            print(f"  - Failed: {twd_failed}")
        
        # Process matches for each retailer
        print("\n" + "="*70)
        print("🔗 STEP 2: Inserting Competitor Products & Matches (Top 5)")
        print("="*70)
        
        total_matches_inserted = 0
        total_products_upserted = 0
        
        for retailer_code, df in match_data.items():
            print(f"\n  Processing {retailer_code.upper()} matches...")
            
            retailer_products_upserted = 0
            retailer_matches_inserted = 0
            retailer_skipped = 0
            
            for _, row in df.iterrows():
                # Convert SKUs properly (Excel stores as float like 15447.0)
                twd_sku = str(int(row['TWD_SKU'])) if pd.notna(row['TWD_SKU']) else None
                comp_sku = str(int(row['COMPETITOR_SKU'])) if pd.notna(row['COMPETITOR_SKU']) else None
                
                if not twd_sku or not comp_sku:
                    retailer_skipped += 1
                    continue
                    
                match_score = float(row.get('MATCH_SCORE', 0.8))
                
                # Get TWD product_id
                if twd_sku not in twd_product_ids:
                    retailer_skipped += 1
                    continue
                
                base_product_id = twd_product_ids[twd_sku]
                
                # Get competitor product data from JSON
                if comp_sku not in json_data.get(retailer_code, {}):
                    retailer_skipped += 1
                    continue
                
                comp_product = json_data[retailer_code][comp_sku]
                
                # Upsert competitor product
                candidate_product_id = upsert_product(conn, comp_product, retailer_code)
                if not candidate_product_id:
                    retailer_skipped += 1
                    continue
                
                retailer_products_upserted += 1
                
                # Insert match
                insert_match(conn, base_product_id, candidate_product_id, 
                           retailer_code, match_score)
                retailer_matches_inserted += 1
            
            print(f"    ✓ {retailer_code.upper()}: {retailer_products_upserted} products, {retailer_matches_inserted} matches")
            if retailer_skipped > 0:
                print(f"      (Skipped {retailer_skipped} - SKU not found in data)")
            
            total_products_upserted += retailer_products_upserted
            total_matches_inserted += retailer_matches_inserted
        
        print("\n" + "="*70)
        print("✅ SEEDING COMPLETE!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  📦 Thai Watsadu products: {twd_upserted} upserted")
        print(f"  📦 Competitor products: {total_products_upserted} upserted")
        print(f"  🔗 Product matches: {total_matches_inserted} created (top 5 per TWD)")
        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
