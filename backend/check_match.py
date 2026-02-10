"""
Check product_matches for Global House product 9907
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
from db_pool import get_pool

# Load environment variables
load_dotenv()

async def check_match():
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Check the Global House product
        print("=== Global House Product (ID: 9907) ===")
        gh_product = await conn.fetchrow("""
            SELECT product_id, name, retailer_id, sku
            FROM products 
            WHERE product_id = 9907
        """)
        print(f"Product: {dict(gh_product) if gh_product else 'NOT FOUND'}\n")
        
        # Check Thai Watsadu product
        print("=== Thai Watsadu Product (ID: 4758) ===")
        twd_product = await conn.fetchrow("""
            SELECT product_id, name, retailer_id, sku
            FROM products 
            WHERE product_id = 4758
        """)
        print(f"Product: {dict(twd_product) if twd_product else 'NOT FOUND'}\n")
        
        # Check product_matches - both directions
        print("=== Product Matches Table Schema ===")
        schema = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'product_matches'
            ORDER BY ordinal_position
        """)
        for col in schema:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
        print("\n=== Product Matches (Global House as candidate) ===")
        match1 = await conn.fetchrow("""
            SELECT *
            FROM product_matches
            WHERE candidate_product_id = 9907
        """)
        print(f"Match: {dict(match1) if match1 else 'NO MATCH FOUND'}\n")
        
        print("\n=== Product Matches (Thai Watsadu as base) ===")
        matches = await conn.fetch("""
            SELECT *
            FROM product_matches
            WHERE base_product_id = 4758
        """)
        print(f"Found {len(matches)} matches:")
        for match in matches:
            print(f"  - {dict(match)}")
        
        print("\n=== Test Query (same as alert) ===")
        test_result = await conn.fetchrow("""
            SELECT 
                p.product_id,
                p.name,
                p.retailer_id,
                pm.base_product_id,
                pm.verified_result,
                CASE
                    WHEN p.retailer_id = 'twd' THEN p.product_id
                    ELSE COALESCE(pm.base_product_id, p.product_id)
                END as twd_product_id
            FROM products p
            LEFT JOIN product_matches pm ON p.product_id = pm.candidate_product_id AND pm.verified_result = true
            WHERE p.product_id = 9907
        """)
        print(f"Result: {dict(test_result) if test_result else 'NOT FOUND'}")
        print(f"\nExpected twd_product_id: 4758")
        print(f"Actual twd_product_id: {test_result['twd_product_id'] if test_result else 'N/A'}")
    
    await pool.close()

if __name__ == '__main__':
    asyncio.run(check_match())
