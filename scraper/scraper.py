"""
PriceHawk Scraper - Import scraped products to database
Run with: python scraper.py

This script:
1. Reads JSON files from scraped data
2. Upserts products (insert new or update existing)
3. Updates price history automatically
"""
import json
from pathlib import Path
import logging
from database import get_or_create_retailer, upsert_product

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Retailer domain mapping
RETAILERS = {
    "Thai Watsadu": "thaiwatsadu.com",
    "HomePro": "homepro.co.th",
    "Do Home": "dohome.co.th",
    "Boonthavorn": "boonthavorn.com",
    "Global House": "globalhouse.co.th",
}


def import_products_from_json(json_file: Path) -> int:
    """
    Import products from a JSON file.
    Returns number of products imported.
    """
    logger.info(f"Processing: {json_file.name}")

    with open(json_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    if not products:
        logger.warning(f"No products in {json_file.name}")
        return 0

    # Get retailer info from first product
    retailer_name = products[0].get("retailer", "Unknown")
    retailer_domain = RETAILERS.get(retailer_name)

    # Get or create retailer
    retailer_id = get_or_create_retailer(retailer_name, retailer_domain)
    logger.info(f"Retailer: {retailer_name} (ID: {retailer_id})")

    count = 0
    for product in products:
        try:
            # Get first image if available
            image = product.get("images", [None])[0] if product.get("images") else None

            # Upsert product (this also updates price_history)
            product_id = upsert_product(
                retailer_id=retailer_id,
                sku=product.get("sku"),
                name=product.get("name"),
                link=product.get("url"),
                current_price=product.get("current_price"),
                original_price=product.get("original_price"),
                brand=product.get("brand"),
                category=product.get("category"),
                image=image,
                description=product.get("description"),
            )
            logger.debug(f"Upserted product {product_id}: {product.get('name', '')[:50]}")
            count += 1

        except Exception as e:
            logger.error(f"Error importing product {product.get('sku')}: {e}")

    return count


def import_all_json_files(directory: Path = None):
    """Import all JSON files from a directory"""
    if directory is None:
        # Default to seeder folder for testing
        directory = Path(__file__).parent.parent / "seeder"

    json_files = list(directory.glob("*_products.json"))
    logger.info(f"Found {len(json_files)} JSON files to import")

    total = 0
    for json_file in json_files:
        count = import_products_from_json(json_file)
        total += count
        logger.info(f"Imported {count} products from {json_file.name}")

    logger.info(f"Total imported: {total} products")
    return total


def import_single_product(retailer_name: str, product_data: dict) -> int:
    """
    Import a single product (for real-time scraping).

    Usage:
        product_id = import_single_product("Thai Watsadu", {
            "sku": "12345",
            "name": "Product Name",
            "url": "https://...",
            "current_price": 199.0,
            "original_price": 299.0,
            "brand": "Brand",
            "category": "Category",
            "images": ["https://..."],
        })
    """
    retailer_domain = RETAILERS.get(retailer_name)
    retailer_id = get_or_create_retailer(retailer_name, retailer_domain)

    image = product_data.get("images", [None])[0] if product_data.get("images") else None

    return upsert_product(
        retailer_id=retailer_id,
        sku=product_data.get("sku"),
        name=product_data.get("name"),
        link=product_data.get("url"),
        current_price=product_data.get("current_price"),
        original_price=product_data.get("original_price"),
        brand=product_data.get("brand"),
        category=product_data.get("category"),
        image=image,
        description=product_data.get("description"),
    )


if __name__ == "__main__":
    # Import all JSON files from seeder folder
    import_all_json_files()
