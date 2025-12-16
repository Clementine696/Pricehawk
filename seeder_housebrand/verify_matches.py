"""
Verify product matches from Excel files - update existing matches in database.
Run: python seeder/verify_matches.py

This script reads Excel match result files and marks rank=1 + is_correct=TRUE
matches as verified in the product_matches table.

Expected Excel columns:
- TWD_SKU: Thai Watsadu product SKU
- RANK: Match ranking (1-5)
- IS_CORRECT: Whether the match is correct (TRUE/FALSE)
- One of: HP_SKU, MGH_SKU, DH_SKU, BTV_SKU, GBH_SKU (competitor SKU)
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)

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

# Mapping from filename part to retailer_id and SKU column
COMPETITOR_MAPPING = {
    "homepro": {"retailer_id": "hp", "sku_col": "HP_SKU"},
    "megahome": {"retailer_id": "mgh", "sku_col": "MGH_SKU"},
    "dohome": {"retailer_id": "dh", "sku_col": "DH_SKU"},
    "boonthavorn": {"retailer_id": "btv", "sku_col": "BTV_SKU"},
    "globalhouse": {"retailer_id": "gbh", "sku_col": "GBH_SKU"},
}

TWD_RETAILER_ID = "twd"


def get_db():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def parse_competitor_from_filename(filename: str) -> dict | None:
    """Extract competitor info from filename like 'twd_boonthavorn_match_result_v18.17.xlsx'"""
    filename_lower = filename.lower()
    for key, info in COMPETITOR_MAPPING.items():
        if key in filename_lower:
            return info
    return None


def get_product_id(conn, retailer_id: str, sku: str) -> int | None:
    """Look up product_id by retailer and SKU"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT product_id FROM products WHERE retailer_id = %s AND sku = %s",
            (retailer_id, str(sku).strip())
        )
        result = cur.fetchone()
        return result["product_id"] if result else None


def verify_match(conn, base_product_id: int, candidate_product_id: int, dry_run: bool = False) -> bool:
    """
    Update an existing product match to mark it as verified correct.
    Sets verified_by_user = TRUE and is_same = TRUE.
    """
    try:
        if dry_run:
            return True

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE product_matches
                SET verified_by_user = TRUE,
                    is_same = TRUE,
                    verified_result = TRUE,
                    updated_at = NOW()
                WHERE base_product_id = %s
                  AND candidate_product_id = %s
                """,
                (base_product_id, candidate_product_id)
            )
            updated = cur.rowcount > 0
            conn.commit()
            return updated
    except Exception as e:
        print(f"    ! Error updating match: {e}")
        conn.rollback()
        return False


def preview_excel_structure(file_path: Path):
    """Print the structure of an Excel file to help identify columns"""
    print(f"\n=== Preview of {file_path.name} ===")
    df = pd.read_excel(file_path, nrows=10)
    print(f"Columns: {list(df.columns)}")
    print(f"\nSample data:")
    print(df.to_string())
    print("=" * 50)


def process_excel_file(conn, file_path: Path, dry_run: bool = False) -> tuple[int, int, int, int]:
    """
    Process an Excel file and verify rank=1, is_correct=TRUE matches.
    Returns (total_rows, verified, skipped, not_found)
    """
    filename = file_path.name
    competitor_info = parse_competitor_from_filename(filename)

    if not competitor_info:
        print(f"Could not determine competitor from filename: {filename}")
        return (0, 0, 0, 0)

    retailer_id = competitor_info["retailer_id"]
    comp_sku_col = competitor_info["sku_col"]

    print(f"\nProcessing: {filename}")
    print(f"  Competitor: {retailer_id}, SKU column: {comp_sku_col}")

    # Read Excel file
    df = pd.read_excel(file_path)
    total_rows = len(df)
    print(f"  Total rows: {total_rows}")

    # Check required columns
    required_cols = ["TWD_SKU", "RANK", "IS_CORRECT"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"  Error: Missing columns: {missing_cols}")
        print(f"  Available columns: {list(df.columns)}")
        return (total_rows, 0, 0, 0)

    # Check for competitor SKU column
    if comp_sku_col not in df.columns:
        # Try to find alternative column names
        alt_cols = [c for c in df.columns if retailer_id.upper() in c.upper() or "COMP" in c.upper() or "CANDIDATE" in c.upper()]
        if alt_cols:
            comp_sku_col = alt_cols[0]
            print(f"  Using alternative SKU column: {comp_sku_col}")
        else:
            print(f"  Error: SKU column '{comp_sku_col}' not found. Available: {list(df.columns)}")
            return (total_rows, 0, 0, 0)

    # Filter for rank=1 and is_correct=TRUE
    df_filtered = df[(df["RANK"] == 1) & (df["IS_CORRECT"] == True)]
    print(f"  Matches to verify (RANK=1 AND IS_CORRECT=TRUE): {len(df_filtered)}")

    verified = 0
    skipped = 0
    not_found_twd = 0
    not_found_comp = 0
    not_in_db = 0

    for idx, row in df_filtered.iterrows():
        twd_sku = row["TWD_SKU"]
        comp_sku = row[comp_sku_col]

        # Skip empty rows
        if pd.isna(twd_sku) or pd.isna(comp_sku):
            skipped += 1
            continue

        # Look up product IDs
        twd_product_id = get_product_id(conn, TWD_RETAILER_ID, twd_sku)
        comp_product_id = get_product_id(conn, retailer_id, comp_sku)

        if not twd_product_id:
            not_found_twd += 1
            if not_found_twd <= 3:
                print(f"    ! TWD product not found: {twd_sku}")
            continue

        if not comp_product_id:
            not_found_comp += 1
            if not_found_comp <= 3:
                print(f"    ! Competitor product not found: {comp_sku}")
            continue

        if dry_run:
            print(f"    [DRY RUN] Would verify: TWD:{twd_sku} -> {retailer_id}:{comp_sku}")
            verified += 1
        else:
            if verify_match(conn, twd_product_id, comp_product_id):
                verified += 1
            else:
                not_in_db += 1
                if not_in_db <= 3:
                    print(f"    ! Match not found in DB: TWD:{twd_sku} -> {retailer_id}:{comp_sku}")

    print(f"  Results: {verified} verified")
    if skipped > 0:
        print(f"  Skipped: {skipped} (empty values)")
    if not_found_twd > 0:
        print(f"  Warning: {not_found_twd} TWD products not found")
    if not_found_comp > 0:
        print(f"  Warning: {not_found_comp} competitor products not found")
    if not_in_db > 0:
        print(f"  Warning: {not_in_db} matches not found in product_matches table")

    return (total_rows, verified, skipped, not_found_twd + not_found_comp + not_in_db)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify product matches from Excel files")
    parser.add_argument("--preview", action="store_true", help="Preview Excel structure without updating")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without actually updating")
    parser.add_argument("--file", help="Process only a specific file")
    parser.add_argument("--pattern", default="*match_result*.xlsx", help="File pattern to match (default: *match_result*.xlsx)")

    args = parser.parse_args()

    print(f"DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    # Find Excel files
    seeder_dir = Path(__file__).parent
    if args.file:
        excel_files = [seeder_dir / args.file]
        if not excel_files[0].exists():
            print(f"File not found: {args.file}")
            return
    else:
        excel_files = list(seeder_dir.glob(args.pattern))

    if not excel_files:
        print(f"No Excel files found matching pattern: {args.pattern}")
        return

    print(f"Found {len(excel_files)} Excel file(s)")
    for f in excel_files:
        print(f"  - {f.name}")

    # Preview mode
    if args.preview:
        for f in excel_files:
            preview_excel_structure(f)
        return

    # Connect to database
    try:
        conn = get_db()
        print("Connected to database")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    total_verified = 0
    total_not_found = 0

    for excel_file in sorted(excel_files):
        rows, verified, skipped, not_found = process_excel_file(
            conn,
            excel_file,
            dry_run=args.dry_run
        )
        total_verified += verified
        total_not_found += not_found

    conn.close()

    print(f"\n{'='*50}")
    if args.dry_run:
        print(f"DRY RUN COMPLETE: Would verify {total_verified} matches")
    else:
        print(f"VERIFICATION COMPLETE: {total_verified} matches verified")
    if total_not_found > 0:
        print(f"  {total_not_found} products/matches not found")


if __name__ == "__main__":
    main()
