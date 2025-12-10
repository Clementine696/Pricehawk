"""
Seed ALL data from JSON files
Run: python seed_all_data.py

This script imports ALL products from JSON files in the seeder folder.
"""
import json
from pathlib import Path
from database import get_or_create_retailer, upsert_product

# Retailer domain mapping
RETAILER_DOMAINS = {
    "Thai Watsadu": "thaiwatsadu.com",
    "HomePro": "homepro.co.th",
    "Do Home": "dohome.co.th",
    "Boonthavorn": "boonthavorn.com",
    "Global House": "globalhouse.co.th",
}


def import_json_file(json_file: Path) -> int:
    """Import all products from a JSON file. Returns count."""
    print(f"\nProcessing: {json_file.name}")

    with open(json_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    if not products:
        print("  No products found")
        return 0

    # Get retailer info from first product
    retailer_name = products[0].get("retailer", "Unknown")
    retailer_domain = RETAILER_DOMAINS.get(retailer_name)

    # Get or create retailer
    retailer_id = get_or_create_retailer(retailer_name, retailer_domain)
    print(f"  Retailer: {retailer_name} (ID: {retailer_id})")
    print(f"  Total products: {len(products)}")

    count = 0
    errors = 0
    for product in products:
        try:
            # Get first image if available
            image = product.get("images", [None])[0] if product.get("images") else None

            # Upsert product
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
            count += 1

            # Progress indicator every 100 products
            if count % 100 == 0:
                print(f"    Imported {count} products...")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    Error: {product.get('sku')} - {e}")
            elif errors == 6:
                print(f"    ... suppressing further errors")

    print(f"  Imported: {count} products" + (f" ({errors} errors)" if errors else ""))
    return count


def main():
    print("=" * 60)
    print("Seeding ALL data from JSON files")
    print("=" * 60)

    # Find all JSON files in seeder folder
    seeder_dir = Path(__file__).parent.parent / "seeder"
    json_files = list(seeder_dir.glob("*_products.json"))

    print(f"\nFound {len(json_files)} JSON files in {seeder_dir}")

    total = 0
    for json_file in json_files:
        count = import_json_file(json_file)
        total += count

    print("\n" + "=" * 60)
    print(f"DONE! Imported {total} total products from {len(json_files)} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
