"""
Import product matches for CFW SKUs.

Usage:
    python temp/import_match_cfw/import_matches_interest.py [options]

Options:
    --file FILE         Match JSON file (default: auto-detect latest matched_release*.json)
    --interest FILE     Interest SKU list (default: interest.txt in same dir)
    --include-review    Also import review_queue items (score 0.38-0.42)
    --min-score FLOAT   Override minimum score threshold (e.g. 0.40)
    --dry-run           Print what would be imported without writing to DB
    --no-interest       Import all SKUs in the file, not just interest list
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Load temp/.env manually (no dotenv dependency)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())


def get_db():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ.get('DB_PORT', '5432'),
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        sslmode=os.environ.get('DB_SSLMODE', 'require'),
        cursor_factory=RealDictCursor
    )


def find_latest_json(base: Path) -> Path:
    """Pick the latest matched_release*.json by name (lexicographic)."""
    candidates = sorted(base.glob('matched_release*.json'), reverse=True)
    if candidates:
        return candidates[0]
    # Fallback to any matched_products*.json
    candidates = sorted(base.glob('matched_products*.json'), reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No match JSON file found in {base}")


def load_interest_skus(path: Path) -> set:
    skus = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            sku = line.strip()
            if sku:
                skus.add(sku)
    return skus


def find_product_id(cur, retailer_id: str, sku: str, barcode: str):
    if sku:
        cur.execute(
            "SELECT id FROM products WHERE retailer_id = %s AND sku = %s LIMIT 1",
            (retailer_id, sku)
        )
        row = cur.fetchone()
        if row:
            return row['id']
    if barcode:
        cur.execute(
            "SELECT id FROM products WHERE retailer_id = %s AND barcode = %s LIMIT 1",
            (retailer_id, barcode)
        )
        row = cur.fetchone()
        if row:
            return row['id']
    return None


def parse_args():
    parser = argparse.ArgumentParser(description='Import CFW/Makro product matches')
    base = Path(__file__).parent

    parser.add_argument('--file', type=Path, default=None,
                        help='Match JSON file (default: auto-detect latest matched_release*.json)')
    parser.add_argument('--interest', type=Path, default=base / 'interest.txt',
                        help='Interest SKU list file')
    parser.add_argument('--include-review', action='store_true',
                        help='Also import review_queue items (score 0.38-0.42)')
    parser.add_argument('--min-score', type=float, default=None,
                        help='Override minimum score threshold')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate import without writing to DB')
    parser.add_argument('--no-interest', action='store_true',
                        help='Import all SKUs in the file, ignoring interest.txt')
    return parser.parse_args()


def main():
    args = parse_args()
    base = Path(__file__).parent

    # Resolve JSON file
    json_path = args.file or find_latest_json(base)
    print(f"Match file:   {json_path.name}")

    # Load JSON
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    file_threshold = summary.get('score_threshold', 0.38)
    file_review_threshold = summary.get('review_threshold', 0.42)

    print(f"File summary: {summary.get('fuzzy_matches', '?')} matches, "
          f"{summary.get('review_candidates', '?')} review, "
          f"{summary.get('unmatched_cfw', '?')} unmatched")
    print(f"File thresholds: score>={file_review_threshold} for matches, "
          f"{file_threshold}-{file_review_threshold} for review")

    # Collect candidates
    candidates = list(data.get('matches', []))
    if args.include_review:
        candidates += list(data.get('review_queue', []))
        print(f"Including review_queue items (--include-review)")

    # Apply min-score filter if overridden
    if args.min_score is not None:
        before = len(candidates)
        candidates = [m for m in candidates if m.get('score', 0) >= args.min_score]
        print(f"Min-score filter {args.min_score}: {before} -> {len(candidates)}")

    # Filter by interest SKUs
    if not args.no_interest:
        interest_skus = load_interest_skus(args.interest)
        print(f"Interest SKUs: {len(interest_skus)} (from {args.interest.name})")
        candidates = [m for m in candidates if m.get('cfw_sku') in interest_skus]
    else:
        print("No interest filter — importing all SKUs in file")

    print(f"Candidates to process: {len(candidates)}")

    if not candidates:
        print("Nothing to import.")
        return

    if args.dry_run:
        print("\n[DRY RUN] No DB writes will happen.\n")

    conn = None if args.dry_run else get_db()
    cur = None if args.dry_run else conn.cursor()

    stats = {
        'total': len(candidates),
        'imported': 0,
        'skipped_no_cfw': 0,
        'skipped_no_makro': 0,
        'skipped_duplicate': 0,
        'errors': 0,
    }

    try:
        for idx, match in enumerate(candidates, 1):
            cfw_sku     = match.get('cfw_sku')
            cfw_barcode = match.get('cfw_barcode')
            makro_sku   = match.get('makro_sku')
            makro_barcode = match.get('makro_barcode')
            score       = match.get('score')
            cfw_name    = match.get('cfw_name_en', '')
            makro_name  = match.get('makro_name', '')

            label = f"[{idx}/{stats['total']}]"

            if args.dry_run:
                print(f"{label} DRY  CFW {cfw_sku} ({cfw_name[:35]}) "
                      f"<-> Makro {makro_sku} ({makro_name[:30]})  score={score:.4f}")
                stats['imported'] += 1
                continue

            cfw_id = find_product_id(cur, 'cfw', cfw_sku, cfw_barcode)
            if not cfw_id:
                print(f"{label} SKIP - CFW not found: SKU={cfw_sku}")
                stats['skipped_no_cfw'] += 1
                continue

            makro_id = find_product_id(cur, 'makro', makro_sku, makro_barcode)
            if not makro_id:
                print(f"{label} SKIP - Makro not found: SKU={makro_sku}")
                stats['skipped_no_makro'] += 1
                continue

            try:
                cur.execute("""
                    INSERT INTO product_matches
                        (cfw_product_id, makro_product_id, match_score, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                    ON CONFLICT (cfw_product_id, makro_product_id)
                    DO UPDATE SET match_score = EXCLUDED.match_score, updated_at = NOW()
                """, (cfw_id, makro_id, score))

                if cur.rowcount == 1:
                    stats['imported'] += 1
                    print(f"{label} OK   CFW {cfw_sku} (#{cfw_id}) "
                          f"<-> Makro {makro_sku} (#{makro_id})  score={score:.4f}")
                else:
                    stats['skipped_duplicate'] += 1
                    print(f"{label} DUP  CFW {cfw_sku} <-> Makro {makro_sku}")

                conn.commit()

            except Exception as e:
                conn.rollback()
                stats['errors'] += 1
                print(f"{label} ERR  {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    print()
    print("=" * 50)
    print(f"Match file:        {json_path.name}")
    print(f"Total processed:   {stats['total']}")
    print(f"Imported/Updated:  {stats['imported']}")
    print(f"Skipped (no CFW):  {stats['skipped_no_cfw']}")
    print(f"Skipped (no Makro):{stats['skipped_no_makro']}")
    print(f"Duplicates:        {stats['skipped_duplicate']}")
    print(f"Errors:            {stats['errors']}")
    if args.dry_run:
        print("[DRY RUN — nothing was written]")
    print("=" * 50)


if __name__ == '__main__':
    main()
