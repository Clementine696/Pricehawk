"""
Sample data upload script for testing
Run: python sample_upload.py
"""
from database import get_or_create_retailer, upsert_product, add_product_match

# Sample products for Thai Watsadu (base retailer)
THAI_WATSADU_PRODUCTS = [
    {
        "sku": "60272160",
        "name": "คีมล๊อคปากตรง SOLO รุ่น 2000 ขนาด 10 นิ้ว สีเงิน",
        "brand": "SOLO",
        "category": "เครื่องมือช่าง",
        "url": "https://www.thaiwatsadu.com/th/sku/60272160",
        "current_price": 230,
        "original_price": 488,
    },
    {
        "sku": "5567894",
        "name": "LED BULB 9W DAYLIGHT",
        "brand": "PHILIPS",
        "category": "ไฟฟ้า",
        "url": "https://www.thaiwatsadu.com/th/sku/5567894",
        "current_price": 89,
        "original_price": 129,
    },
    {
        "sku": "3345672",
        "name": "MAKITA HAMMER DRILL HP1641",
        "brand": "MAKITA",
        "category": "เครื่องมือช่าง",
        "url": "https://www.thaiwatsadu.com/th/sku/3345672",
        "current_price": 2450,
        "original_price": 2990,
    },
    {
        "sku": "1145439",
        "name": "SPC NARA CREAM 17.78X121.92X0.4 CM.",
        "brand": "XX",
        "category": "กระเบื้อง",
        "url": "https://www.thaiwatsadu.com/th/sku/1145439",
        "current_price": 100,
        "original_price": 150,
    },
    {
        "sku": "2234561",
        "name": "TOA SUPER SHIELD WHITE 5L",
        "brand": "TOA",
        "category": "สีทาบ้าน",
        "url": "https://www.thaiwatsadu.com/th/sku/2234561",
        "current_price": 850,
        "original_price": 950,
    },
    {
        "sku": "4456783",
        "name": "UPVC SLIDING WINDOW 60X150 CM",
        "brand": "MODERN FORM",
        "category": "ประตู-หน้าต่าง",
        "url": "https://www.thaiwatsadu.com/th/sku/4456783",
        "current_price": 3200,
        "original_price": 3500,
    },
]

# Matching products from other retailers
OTHER_RETAILER_PRODUCTS = {
    "HomePro": [
        {"sku": "HP-LED-9W", "name": "LED BULB 9W DAYLIGHT PHILIPS", "brand": "PHILIPS", "category": "ไฟฟ้า", "url": "https://www.homepro.co.th/p/123", "current_price": 95, "match_base_sku": "5567894"},
        {"sku": "HP-MAKITA-1641", "name": "MAKITA HAMMER DRILL HP1641", "brand": "MAKITA", "category": "เครื่องมือช่าง", "url": "https://www.homepro.co.th/p/456", "current_price": 2450, "match_base_sku": "3345672"},
        {"sku": "HP-SPC-NARA", "name": "SPC NARA CREAM FLOORING", "brand": "XX", "category": "กระเบื้อง", "url": "https://www.homepro.co.th/p/789", "current_price": 150, "match_base_sku": "1145439"},
        {"sku": "HP-TOA-5L", "name": "TOA SUPER SHIELD WHITE 5L", "brand": "TOA", "category": "สีทาบ้าน", "url": "https://www.homepro.co.th/p/101", "current_price": 820, "match_base_sku": "2234561"},
        {"sku": "HP-WINDOW-60", "name": "UPVC SLIDING WINDOW 60X150", "brand": "MODERN FORM", "category": "ประตู-หน้าต่าง", "url": "https://www.homepro.co.th/p/102", "current_price": 3350, "match_base_sku": "4456783"},
    ],
    "Global House": [
        {"sku": "GH-5567894", "name": "PHILIPS LED 9W DAYLIGHT", "brand": "PHILIPS", "category": "ไฟฟ้า", "url": "https://www.globalhouse.co.th/p/111", "current_price": 92, "match_base_sku": "5567894"},
        {"sku": "GH-3345672", "name": "MAKITA HP1641 DRILL", "brand": "MAKITA", "category": "เครื่องมือช่าง", "url": "https://www.globalhouse.co.th/p/222", "current_price": 2500, "match_base_sku": "3345672"},
        {"sku": "GH-1145439", "name": "SPC NARA CREAM TILE", "brand": "XX", "category": "กระเบื้อง", "url": "https://www.globalhouse.co.th/p/333", "current_price": 120, "match_base_sku": "1145439"},
        {"sku": "GH-2234561", "name": "TOA SUPER SHIELD 5L WHITE", "brand": "TOA", "category": "สีทาบ้าน", "url": "https://www.globalhouse.co.th/p/444", "current_price": 840, "match_base_sku": "2234561"},
    ],
    "Do Home": [
        {"sku": "DH-LED9W", "name": "LED BULB PHILIPS 9W", "brand": "PHILIPS", "category": "ไฟฟ้า", "url": "https://www.dohome.co.th/p/aaa", "current_price": 89, "match_base_sku": "5567894"},
        {"sku": "DH-MAKITA", "name": "MAKITA HAMMER DRILL", "brand": "MAKITA", "category": "เครื่องมือช่าง", "url": "https://www.dohome.co.th/p/bbb", "current_price": 2480, "match_base_sku": "3345672"},
        {"sku": "DH-SPC", "name": "SPC FLOORING NARA", "brand": "XX", "category": "กระเบื้อง", "url": "https://www.dohome.co.th/p/ccc", "current_price": 100, "match_base_sku": "1145439"},
        {"sku": "DH-TOA", "name": "TOA PAINT WHITE 5L", "brand": "TOA", "category": "สีทาบ้าน", "url": "https://www.dohome.co.th/p/ddd", "current_price": 830, "match_base_sku": "2234561"},
        {"sku": "DH-WINDOW", "name": "UPVC WINDOW 60X150", "brand": "MODERN FORM", "category": "ประตู-หน้าต่าง", "url": "https://www.dohome.co.th/p/eee", "current_price": 3280, "match_base_sku": "4456783"},
    ],
    "Boonthavorn": [
        {"sku": "BT-LED", "name": "PHILIPS LED DAYLIGHT 9W", "brand": "PHILIPS", "category": "ไฟฟ้า", "url": "https://www.boonthavorn.com/p/x1", "current_price": 90, "match_base_sku": "5567894"},
        {"sku": "BT-MAKITA", "name": "MAKITA DRILL HP1641", "brand": "MAKITA", "category": "เครื่องมือช่าง", "url": "https://www.boonthavorn.com/p/x2", "current_price": 2450, "match_base_sku": "3345672"},
        {"sku": "BT-SPC", "name": "SPC NARA CREAM FLOOR", "brand": "XX", "category": "กระเบื้อง", "url": "https://www.boonthavorn.com/p/x3", "current_price": 100, "match_base_sku": "1145439"},
        {"sku": "BT-WINDOW", "name": "UPVC SLIDING WINDOW", "brand": "MODERN FORM", "category": "ประตู-หน้าต่าง", "url": "https://www.boonthavorn.com/p/x5", "current_price": 3200, "match_base_sku": "4456783"},
    ],
}

RETAILER_DOMAINS = {
    "Thai Watsadu": "thaiwatsadu.com",
    "HomePro": "homepro.co.th",
    "Do Home": "dohome.co.th",
    "Boonthavorn": "boonthavorn.com",
    "Global House": "globalhouse.co.th",
}


def main():
    print("Uploading sample data...")

    # 1. Create Thai Watsadu products (base retailer)
    print("\n1. Creating Thai Watsadu products...")
    tw_retailer_id = get_or_create_retailer("Thai Watsadu", RETAILER_DOMAINS["Thai Watsadu"])
    print(f"   Thai Watsadu retailer_id: {tw_retailer_id}")

    base_products = {}  # sku -> product_id mapping
    for product in THAI_WATSADU_PRODUCTS:
        product_id = upsert_product(
            retailer_id=tw_retailer_id,
            sku=product["sku"],
            name=product["name"],
            link=product["url"],
            current_price=product["current_price"],
            original_price=product["original_price"],
            brand=product["brand"],
            category=product["category"],
        )
        base_products[product["sku"]] = product_id
        print(f"   + {product['name'][:40]}... (ID: {product_id})")

    # # 2. Create products from other retailers and matches
    # print("\n2. Creating products from other retailers...")
    # for retailer_name, products in OTHER_RETAILER_PRODUCTS.items():
    #     retailer_id = get_or_create_retailer(retailer_name, RETAILER_DOMAINS[retailer_name])
    #     print(f"\n   {retailer_name} (retailer_id: {retailer_id}):")

    #     for product in products:
    #         match_base_sku = product.pop("match_base_sku")

    #         # Create the product
    #         product_id = upsert_product(
    #             retailer_id=retailer_id,
    #             sku=product["sku"],
    #             name=product["name"],
    #             link=product["url"],
    #             current_price=product["current_price"],
    #             brand=product.get("brand"),
    #             category=product.get("category"),
    #         )

    #         # Create match with Thai Watsadu base product
    #         base_product_id = base_products.get(match_base_sku)
    #         if base_product_id:
    #             match_id = add_product_match(
    #                 base_product_id=base_product_id,
    #                 candidate_product_id=product_id,
    #                 retailer_id=retailer_id,
    #                 is_same=True,
    #                 confidence_score=0.95,
    #                 reason="Sample match for testing",
    #                 match_type="manual",
    #             )
    #             print(f"   + {product['name'][:35]}... -> Match ID: {match_id}")
    #         else:
    #             print(f"   + {product['name'][:35]}... (no match)")

    print("\n✓ Sample data uploaded successfully!")
    print(f"  - {len(THAI_WATSADU_PRODUCTS)} Thai Watsadu products")
    print(f"  - {sum(len(p) for p in OTHER_RETAILER_PRODUCTS.values())} products from other retailers")
    print(f"  - Product matches created for price comparison")


if __name__ == "__main__":
    main()
