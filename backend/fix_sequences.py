#!/usr/bin/env python3
"""
Fix PostgreSQL sequences after data migration
Run this script to reset all sequences to match existing data
"""

import os
from database import get_db

def fix_sequences():
    """Reset all SERIAL sequences to match existing data"""
    
    sequences_to_fix = [
        ('users_user_id_seq', 'users', 'user_id'),
        ('products_product_id_seq', 'products', 'product_id'),
        ('product_matches_match_id_seq', 'product_matches', 'match_id'),
        ('price_history_price_id_seq', 'price_history', 'price_id'),
    ]
    
    with get_db() as conn:
        with conn.cursor() as cur:
            print("Fixing PostgreSQL sequences after migration...\n")
            
            for seq_name, table_name, id_column in sequences_to_fix:
                try:
                    # Get the maximum ID from the table
                    cur.execute(f"SELECT COALESCE(MAX({id_column}), 1) FROM {table_name}")
                    max_id = cur.fetchone()[0]
                    
                    # Set the sequence to max_id
                    cur.execute(f"SELECT setval('{seq_name}', {max_id}, true)")
                    new_value = cur.fetchone()[0]
                    
                    print(f"✓ Fixed {seq_name}")
                    print(f"  Table: {table_name}")
                    print(f"  Max ID in table: {max_id}")
                    print(f"  Sequence now at: {new_value}\n")
                    
                except Exception as e:
                    print(f"✗ Error fixing {seq_name}: {e}\n")
            
            conn.commit()
            
            print("\n" + "="*50)
            print("Verifying sequences...")
            print("="*50 + "\n")
            
            # Verify all sequences
            for seq_name, table_name, id_column in sequences_to_fix:
                try:
                    cur.execute(f"SELECT last_value FROM {seq_name}")
                    seq_value = cur.fetchone()[0]
                    
                    cur.execute(f"SELECT MAX({id_column}) FROM {table_name}")
                    max_id = cur.fetchone()[0] or 0
                    
                    status = "✓ OK" if seq_value >= max_id else "✗ NEEDS FIX"
                    print(f"{status} {seq_name}: {seq_value} (max in table: {max_id})")
                    
                except Exception as e:
                    print(f"✗ Error checking {seq_name}: {e}")
            
            print("\n✅ All sequences fixed!")

if __name__ == "__main__":
    fix_sequences()
