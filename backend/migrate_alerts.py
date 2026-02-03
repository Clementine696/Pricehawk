#!/usr/bin/env python3
"""
Run price alerts database migration

This script creates the price alert tables if they don't exist.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_pool import get_pool

async def main():
    print("=" * 80)
    print("Price Alerts Database Migration")
    print("=" * 80)

    # Read SQL file
    sql_file = Path(__file__).parent.parent / 'database' / 'init' / '06_price_alerts.sql'

    if not sql_file.exists():
        print(f"ERROR: SQL file not found at {sql_file}")
        return 1

    print(f"Reading SQL from: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("\nConnecting to database...")
    pool = None

    try:
        pool = await get_pool()
        print("✓ Connected to database")

        async with pool.acquire() as conn:
            print("\nExecuting migration...")
            await conn.execute(sql)
            print("✓ Migration completed successfully")

            # Verify tables were created
            print("\nVerifying tables...")
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'price_alert%'
                ORDER BY table_name
            """)

            if tables:
                print("✓ Created tables:")
                for row in tables:
                    print(f"  - {row['table_name']}")
            else:
                print("⚠ Warning: No price_alert tables found")

            # Check default settings
            settings = await conn.fetchrow("SELECT * FROM price_alert_settings LIMIT 1")
            if settings:
                print("\n✓ Default settings created:")
                print(f"  - Frequency: {settings['schedule_frequency']}")
                print(f"  - Time: {settings['schedule_time']}")
                print(f"  - Enabled: {settings['enabled']}")

        print("\n" + "=" * 80)
        print("Migration completed successfully!")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if pool:
            await pool.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
