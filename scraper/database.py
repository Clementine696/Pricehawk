import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pricehawk",
    "user": "pricehawk",
    "password": "pricehawk_secret",
}


@contextmanager
def get_db():
    """Get database connection"""
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
    "Do Home": "dh",
    "Boonthavorn": "btv",
    "Global House": "gbh",
}


# Retailer functions
def get_retailer_code(name: str) -> str:
    """Get retailer code from name"""
    return RETAILER_CODES.get(name)


def get_or_create_retailer(name: str, domain: str = None) -> str:
    """Get retailer by name or create if not exists. Returns retailer_id (code)."""
    code = RETAILER_CODES.get(name)
    if not code:
        raise ValueError(f"Unknown retailer: {name}. Must be one of: {list(RETAILER_CODES.keys())}")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retailer_id FROM retailers WHERE retailer_id = %s", (code,))
            result = cur.fetchone()
            if result:
                return result["retailer_id"]

            cur.execute(
                "INSERT INTO retailers (retailer_id, name, domain) VALUES (%s, %s, %s) RETURNING retailer_id",
                (code, name, domain)
            )
            return cur.fetchone()["retailer_id"]


# Product functions
def get_products_by_retailer(retailer_id: str):
    """Get all products for a retailer"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE retailer_id = %s", (retailer_id,))
            return cur.fetchall()


def get_product_by_sku(retailer_id: str, sku: str) -> dict | None:
    """Get product by retailer and SKU"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE retailer_id = %s AND sku = %s",
                (retailer_id, sku)
            )
            return cur.fetchone()


def upsert_product(retailer_id: str, sku: str, name: str, link: str,
                   current_price: float = None, original_price: float = None,
                   brand: str = None, category: str = None,
                   image: str = None, description: str = None) -> int:
    """
    Insert or update product with price.
    - Updates current_price
    - Updates lowest_price/highest_price
    - Adds entry to price_history
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if product exists to get current lowest/highest
            cur.execute(
                "SELECT product_id, lowest_price, highest_price FROM products WHERE retailer_id = %s AND sku = %s",
                (retailer_id, sku)
            )
            existing = cur.fetchone()

            # Calculate new lowest/highest
            if existing and current_price:
                lowest = min(existing["lowest_price"] or current_price, current_price)
                highest = max(existing["highest_price"] or current_price, current_price)
            else:
                lowest = current_price
                highest = current_price

            # Upsert product
            cur.execute("""
                INSERT INTO products (retailer_id, sku, name, link, brand, category, image, description,
                                      current_price, original_price, lowest_price, highest_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (retailer_id, sku)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    link = EXCLUDED.link,
                    brand = EXCLUDED.brand,
                    category = EXCLUDED.category,
                    image = EXCLUDED.image,
                    description = EXCLUDED.description,
                    current_price = EXCLUDED.current_price,
                    original_price = EXCLUDED.original_price,
                    lowest_price = LEAST(products.lowest_price, EXCLUDED.current_price),
                    highest_price = GREATEST(products.highest_price, EXCLUDED.current_price),
                    last_updated_at = NOW()
                RETURNING product_id
            """, (retailer_id, sku, name, link, brand, category, image, description,
                  current_price, original_price, lowest, highest))
            product_id = cur.fetchone()["product_id"]

            # Add to price history if price exists
            if current_price:
                cur.execute(
                    "INSERT INTO price_history (product_id, price, currency) VALUES (%s, %s, 'THB')",
                    (product_id, current_price)
                )

            return product_id


# Price functions
def add_price_history(product_id: int, price: float, currency: str = "USD"):
    """Add price to history"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO price_history (product_id, price, currency) VALUES (%s, %s, %s)",
                (product_id, price, currency)
            )


def get_price_history(product_id: int, limit: int = 30):
    """Get price history for a product"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT price, currency, scraped_at
                FROM price_history
                WHERE product_id = %s
                ORDER BY scraped_at DESC
                LIMIT %s
            """, (product_id, limit))
            return cur.fetchall()


# Product match functions
def add_product_match(base_product_id: int, candidate_product_id: int, retailer_id: str,
                      is_same: bool = None, confidence_score: float = None,
                      reason: str = None, match_type: str = "auto") -> int:
    """Add a product match"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO product_matches
                (base_product_id, candidate_product_id, retailer_id, is_same, confidence_score, reason, match_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (base_product_id, candidate_product_id) DO UPDATE SET
                    is_same = EXCLUDED.is_same,
                    confidence_score = EXCLUDED.confidence_score,
                    reason = EXCLUDED.reason,
                    updated_at = NOW()
                RETURNING match_id
            """, (base_product_id, candidate_product_id, retailer_id, is_same, confidence_score, reason, match_type))
            return cur.fetchone()["match_id"]


def get_unverified_matches(limit: int = 100):
    """Get matches that need user verification"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pm.*, p1.name as base_name, p2.name as candidate_name
                FROM product_matches pm
                JOIN products p1 ON pm.base_product_id = p1.product_id
                JOIN products p2 ON pm.candidate_product_id = p2.product_id
                WHERE pm.verified_by_user = FALSE
                ORDER BY pm.confidence_score DESC NULLS LAST
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
