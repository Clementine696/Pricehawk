"""
Upload product matches from Excel files to the database.
Run from project root: python matching/upload_matches.py

Excel files should contain matching data with Thai Watsadu products
as base products and competitor products as candidates.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pricehawk",
    "user": "pricehawk",
    "password": "pricehawk_secret",
}

# Mapping from filename part to retailer_id
COMPETITOR_MAPPING = {
    "homepro": "hp",
    "megahome": "mgh",
    "dohome": "dh",
    "boonthavorn": "btv",
    "globalhouse": "gbh",
}

# Thai Watsadu retailer_id
TWD_RETAILER_ID = "twd"


def get_db():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def parse_competitor_from_filename(filename: str) -> str | None:
    """Extract competitor retailer_id from filename like 'twd_homepro_correct_matches_v18.17.xlsx'"""
    filename_lower = filename.lower()
    for key, retailer_id in COMPETITOR_MAPPING.items():
        if key in filename_lower:
            return retailer_id
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


def insert_match(conn, base_product_id: int, candidate_product_id: int, retailer_id: str,
                 is_same: bool = True, confidence: float = 1.0, reason: str = "excel_import",
                 is_verified: bool = True) -> bool:
    """
    Insert a product match into the database.

    Args:
        is_verified: If True, mark as verified correct match.
                     If False, mark as unverified (needs review in UI).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO product_matches
                    (base_product_id, candidate_product_id, retailer_id, is_same, confidence_score,
                     reason, match_type, verified_by_user, verified_result)
                VALUES (%s, %s, %s, %s, %s, %s, 'import', %s, %s)
                ON CONFLICT (base_product_id, candidate_product_id)
                DO UPDATE SET
                    is_same = EXCLUDED.is_same,
                    confidence_score = EXCLUDED.confidence_score,
                    verified_by_user = EXCLUDED.verified_by_user,
                    verified_result = EXCLUDED.verified_result,
                    updated_at = NOW()
                """,
                (base_product_id, candidate_product_id, retailer_id, is_same, confidence, reason,
                 is_verified, is_same if is_verified else None)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"    ! Error inserting match: {e}")
        conn.rollback()
        return False


def preview_excel_structure(file_path: Path):
    """Print the structure of an Excel file to help identify columns"""
    print(f"\n=== Preview of {file_path.name} ===")
    df = pd.read_excel(file_path, nrows=5)
    print(f"Columns: {list(df.columns)}")
    print(f"First 5 rows:")
    # Use ASCII-safe representation to avoid encoding errors
    for idx, row in df.iterrows():
        row_str = " | ".join([f"{col}: {str(val)[:30]}" for col, val in row.items()])
        try:
            print(f"  Row {idx}: {row_str}")
        except UnicodeEncodeError:
            print(f"  Row {idx}: [contains non-ASCII characters]")
    print("=" * 50)


def process_excel_file(conn, file_path: Path, twd_sku_col: str, comp_sku_col: str,
                       dry_run: bool = False, correct_only: bool = False) -> tuple[int, int, int]:
    """
    Process an Excel file and upload matches.
    Returns (total_rows, successful_matches, failed_matches)
    """
    filename = file_path.name
    competitor_id = parse_competitor_from_filename(filename)

    if not competitor_id:
        print(f"Could not determine competitor from filename: {filename}")
        return (0, 0, 0)

    print(f"\nProcessing: {filename}")
    print(f"  Competitor retailer_id: {competitor_id}")

    # Read Excel file
    df = pd.read_excel(file_path)
    total_rows = len(df)
    print(f"  Total rows: {total_rows}")

    # Filter for correct matches only if requested
    if correct_only and "IS_CORRECT" in df.columns:
        df = df[df["IS_CORRECT"] == True]
        print(f"  Filtered to IS_CORRECT=True: {len(df)} rows")

    # Check if required columns exist
    if twd_sku_col not in df.columns:
        print(f"  Error: Column '{twd_sku_col}' not found. Available: {list(df.columns)}")
        return (total_rows, 0, 0)

    if comp_sku_col not in df.columns:
        print(f"  Error: Column '{comp_sku_col}' not found. Available: {list(df.columns)}")
        return (total_rows, 0, 0)

    successful = 0
    failed = 0
    not_found_twd = 0
    not_found_comp = 0
    verified_count = 0
    unverified_count = 0

    # Check if IS_CORRECT column exists
    has_is_correct = "IS_CORRECT" in df.columns

    for idx, row in df.iterrows():
        twd_sku = row[twd_sku_col]
        comp_sku = row[comp_sku_col]

        # Skip empty rows
        if pd.isna(twd_sku) or pd.isna(comp_sku):
            continue

        # Get IS_CORRECT value (default to True if column doesn't exist)
        is_correct = True
        if has_is_correct:
            is_correct = bool(row["IS_CORRECT"]) if not pd.isna(row["IS_CORRECT"]) else False

        # Look up product IDs
        twd_product_id = get_product_id(conn, TWD_RETAILER_ID, twd_sku)
        comp_product_id = get_product_id(conn, competitor_id, comp_sku)

        if not twd_product_id:
            not_found_twd += 1
            if not_found_twd <= 3:  # Only show first 3 warnings
                print(f"    ! TWD product not found: {twd_sku}")
            continue

        if not comp_product_id:
            not_found_comp += 1
            if not_found_comp <= 3:  # Only show first 3 warnings
                print(f"    ! Competitor product not found: {comp_sku}")
            continue

        if dry_run:
            status = "verified" if is_correct else "needs review"
            print(f"    [DRY RUN] Would match TWD:{twd_sku} -> {competitor_id}:{comp_sku} ({status})")
            successful += 1
            if is_correct:
                verified_count += 1
            else:
                unverified_count += 1
        else:
            if insert_match(conn, twd_product_id, comp_product_id, competitor_id, is_verified=is_correct):
                successful += 1
                if is_correct:
                    verified_count += 1
                else:
                    unverified_count += 1
            else:
                failed += 1

    print(f"  Results: {successful} successful ({verified_count} verified, {unverified_count} needs review), {failed} failed")
    if not_found_twd > 0:
        print(f"  Warnings: {not_found_twd} TWD products not found in database")
    if not_found_comp > 0:
        print(f"  Warnings: {not_found_comp} competitor products not found in database")

    return (total_rows, successful, failed)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Upload product matches from Excel files")
    parser.add_argument("--preview", action="store_true", help="Preview Excel structure without uploading")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without actually inserting")
    parser.add_argument("--twd-col", default="TWD_SKU", help="Column name for Thai Watsadu SKU (default: TWD_SKU)")
    parser.add_argument("--comp-col", default="COMPETITOR_SKU", help="Column name for competitor SKU (default: COMPETITOR_SKU)")
    parser.add_argument("--correct-only", action="store_true",
                        help="Only import rows where IS_CORRECT is True. By default, all rows are imported: "
                             "IS_CORRECT=True as verified, IS_CORRECT=False as needs review")
    parser.add_argument("--file", help="Process only a specific file (optional)")

    args = parser.parse_args()

    # Find Excel files
    matching_dir = Path(__file__).parent
    if args.file:
        excel_files = [matching_dir / args.file]
    else:
        excel_files = list(matching_dir.glob("twd_*.xlsx"))

    if not excel_files:
        print("No Excel files found in matching directory")
        return

    print(f"Found {len(excel_files)} Excel files")

    # Preview mode - just show structure
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

    total_successful = 0
    total_failed = 0

    for excel_file in sorted(excel_files):
        rows, successful, failed = process_excel_file(
            conn,
            excel_file,
            args.twd_col,
            args.comp_col,
            dry_run=args.dry_run,
            correct_only=args.correct_only
        )
        total_successful += successful
        total_failed += failed

    conn.close()

    print(f"\n{'='*50}")
    if args.dry_run:
        print(f"DRY RUN COMPLETE: Would upload {total_successful} matches")
    else:
        print(f"UPLOAD COMPLETE: {total_successful} matches uploaded, {total_failed} failed")


if __name__ == "__main__":
    main()
