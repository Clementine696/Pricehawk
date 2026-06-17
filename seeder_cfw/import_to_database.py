#!/usr/bin/env python3
"""
Import CFW and Makro products from JSON files to PostgreSQL database.

Reads:
- temp/cfw_products.json
- temp/makro_complete.json

Connects to database using temp/.env configuration.

Usage:
    python temp/import_to_database.py
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# File paths
SCRIPT_DIR = Path(__file__).parent
CFW_JSON = SCRIPT_DIR / "cfw_products.json"
MAKRO_JSON = SCRIPT_DIR / "makro_complete.json"
ENV_FILE = SCRIPT_DIR / ".env"


def load_env():
    """Load database configuration from .env file"""
    if not ENV_FILE.exists():
        print(f"[ERROR] {ENV_FILE} not found")
        sys.exit(1)
    
    load_dotenv(ENV_FILE)
    
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'pricehawk'),
        'user': os.getenv('DB_USER', 'pricehawk'),
        'password': os.getenv('DB_PASSWORD', 'pricehawk_secret'),
    }
    
    sslmode = os.getenv('DB_SSLMODE', 'disable')
    if sslmode != 'disable':
        config['sslmode'] = sslmode
    
    return config


def get_db_connection(config):
    """Create database connection"""
    try:
        conn = psycopg2.connect(**config)
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        sys.exit(1)


def extract_categories(cfw_products, makro_products):
    """Extract unique categories from both datasets"""
    categories = []
    
    # CFW categories - use existing numeric IDs
    cfw_cats = set()
    for p in cfw_products:
        cat_id = p.get('Category ID')
        cat_name = p.get('Category Name')
        if cat_id and cat_name:
            cfw_cats.add((str(cat_id), cat_name))
    
    for cat_id, cat_name in sorted(cfw_cats):
        categories.append(('cfw', cat_id, cat_name))
    
    # Makro categories - generate sequential IDs
    makro_cat_names = set()
    for p in makro_products:
        cat = p.get('category')
        if cat:
            makro_cat_names.add(cat)
    
    # Sort and assign MK-001, MK-002, etc.
    for idx, cat_name in enumerate(sorted(makro_cat_names), start=1):
        cat_id = f"MK-{idx:03d}"  # MK-001, MK-002, etc.
        categories.append(('makro', cat_id, cat_name))
    
    return categories


def build_makro_category_map(categories):
    """Build mapping from Makro category name to generated ID"""
    makro_map = {}
    for retailer_id, cat_id, cat_name in categories:
        if retailer_id == 'makro':
            makro_map[cat_name] = cat_id
    return makro_map


def extract_departments(cfw_products):
    """Extract unique departments (Dept → Sub-Dept) from CFW"""
    departments = set()
    
    for p in cfw_products:
        dept = p.get('Dept')
        dept_name = p.get('Dept Name')
        sub_dept = p.get('Sub-Dept')
        sub_dept_name = p.get('Sub-Dept Name')
        
        if dept and dept_name:
            # Use 'N/A' as placeholder for NULL sub_dept (PRIMARY KEY can't contain NULL)
            sub_dept_str = str(sub_dept) if sub_dept else 'N/A'
            sub_dept_name_str = sub_dept_name if sub_dept_name else 'N/A'
            departments.add((str(dept), dept_name, sub_dept_str, sub_dept_name_str))
    
    return list(departments)


def extract_classes(cfw_products):
    """Extract unique classes (Class → Sub-Class) from CFW"""
    classes = set()
    
    for p in cfw_products:
        cls = p.get('Class')
        cls_name = p.get('Class Name')
        sub_cls = p.get('Sub-Class')
        sub_cls_name = p.get('Sub-Class Name')
        
        if cls and cls_name:
            # Use 'N/A' as placeholder for NULL sub_class (PRIMARY KEY can't contain NULL)
            sub_cls_str = str(sub_cls) if sub_cls else 'N/A'
            sub_cls_name_str = sub_cls_name if sub_cls_name else 'N/A'
            classes.add((str(cls), cls_name, sub_cls_str, sub_cls_name_str))
    
    return list(classes)


def insert_categories(conn, categories):
    """Insert categories into database"""
    if not categories:
        return
    
    cursor = conn.cursor()
    
    # Use INSERT ... ON CONFLICT to avoid duplicates
    query = """
        INSERT INTO categories (retailer_id, category_id, category_name)
        VALUES %s
        ON CONFLICT (retailer_id, category_id) DO NOTHING
    """
    
    execute_values(cursor, query, categories)
    conn.commit()
    cursor.close()
    
    print(f"   [OK] Inserted {len(categories)} categories")


def insert_departments(conn, departments):
    """Insert departments into database"""
    if not departments:
        return
    
    # Deduplicate by (dept_id, sub_dept_id) - keep first occurrence
    seen = set()
    unique_departments = []
    for dept in departments:
        key = (dept[0], dept[2])  # (dept_id, sub_dept_id)
        if key not in seen:
            seen.add(key)
            unique_departments.append(dept)
    
    cursor = conn.cursor()
    
    query = """
        INSERT INTO departments (dept_id, dept_name, sub_dept_id, sub_dept_name)
        VALUES %s
        ON CONFLICT (dept_id, sub_dept_id) DO UPDATE SET
            dept_name = EXCLUDED.dept_name,
            sub_dept_name = EXCLUDED.sub_dept_name
    """
    
    execute_values(cursor, query, unique_departments)
    conn.commit()
    cursor.close()
    
    print(f"   [OK] Inserted {len(unique_departments)} departments (deduped from {len(departments)})")


def insert_classes(conn, classes):
    """Insert classes into database"""
    if not classes:
        return
    
    # Deduplicate by (class_id, sub_class_id) - keep first occurrence
    seen = set()
    unique_classes = []
    for cls in classes:
        key = (cls[0], cls[2])  # (class_id, sub_class_id)
        if key not in seen:
            seen.add(key)
            unique_classes.append(cls)
    
    cursor = conn.cursor()
    
    query = """
        INSERT INTO classes (class_id, class_name, sub_class_id, sub_class_name)
        VALUES %s
        ON CONFLICT (class_id, sub_class_id) DO UPDATE SET
            class_name = EXCLUDED.class_name,
            sub_class_name = EXCLUDED.sub_class_name
    """
    
    execute_values(cursor, query, unique_classes)
    conn.commit()
    cursor.close()
    
    print(f"   [OK] Inserted {len(unique_classes)} classes (deduped from {len(classes)})")


def insert_cfw_products(conn, cfw_products):
    """Insert CFW products"""
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for product in cfw_products:
        sku = product.get('SKU')
        if not sku:
            skipped += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO products (
                    retailer_id, sku, barcode, name, name_en, brand,
                    category_id, dept_id, sub_dept_id, class_id, sub_class_id,
                    current_price, step_prices, url, image_url, is_active
                ) VALUES (
                    'cfw', %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (retailer_id, sku) DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    step_prices = EXCLUDED.step_prices,
                    updated_at = NOW()
            """, (
                str(sku),
                product.get('Barcode'),
                product.get('Product Name (TH)'),
                product.get('Product Name (EN)'),
                product.get('Brand'),
                str(product.get('Category ID')) if product.get('Category ID') else None,
                str(product.get('Dept')) if product.get('Dept') else None,
                str(product.get('Sub-Dept')) if product.get('Sub-Dept') else 'N/A',
                str(product.get('Class')) if product.get('Class') else None,
                str(product.get('Sub-Class')) if product.get('Sub-Class') else 'N/A',
                product.get('POS PRICE'),
                json.dumps(product.get('step_prices', [])),
                product.get('Product URL'),
                product.get('Image URL'),
                product.get('SKU Status', '').startswith('A')  # Active if starts with 'A'
            ))
            inserted += 1
        except Exception as e:
            print(f"   [WARN] Failed to insert CFW SKU {sku}: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    
    print(f"   [OK] Inserted {inserted} CFW products ({skipped} skipped)")


def insert_makro_products(conn, makro_products, makro_category_map):
    """Insert Makro products"""
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for product in makro_products:
        sku = product.get('sku')
        if not sku:
            skipped += 1
            continue
        
        # Map category name to generated ID
        cat_name = product.get('category')
        cat_id = makro_category_map.get(cat_name) if cat_name else None
        
        try:
            cursor.execute("""
                INSERT INTO products (
                    retailer_id, sku, barcode, name, brand,
                    category_id,
                    current_price, step_prices, url, image_url, is_active
                ) VALUES (
                    'makro', %s, %s, %s, %s,
                    %s,
                    %s, %s, %s, %s, TRUE
                )
                ON CONFLICT (retailer_id, sku) DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    step_prices = EXCLUDED.step_prices,
                    updated_at = NOW()
            """, (
                str(sku),
                product.get('barcode'),
                product.get('name'),
                product.get('brand'),
                cat_id,
                product.get('current_price'),
                json.dumps(product.get('step_prices', [])),
                product.get('url'),
                product.get('images', [None])[0] if product.get('images') else None
            ))
            inserted += 1
        except Exception as e:
            print(f"   [WARN] Failed to insert Makro SKU {sku}: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    
    print(f"   [OK] Inserted {inserted} Makro products ({skipped} skipped)")


def main():
    print("=" * 60)
    print("CFW / MAKRO PRODUCT IMPORT")
    print("=" * 60)
    
    # Load JSON files
    print("\n[INFO] Loading JSON files...")
    
    if not CFW_JSON.exists():
        print(f"[ERROR] {CFW_JSON} not found")
        sys.exit(1)
    
    if not MAKRO_JSON.exists():
        print(f"[ERROR] {MAKRO_JSON} not found")
        sys.exit(1)
    
    with open(CFW_JSON, 'r', encoding='utf-8') as f:
        cfw_products = json.load(f)
    print(f"   [OK] Loaded {len(cfw_products)} CFW products")
    
    with open(MAKRO_JSON, 'r', encoding='utf-8') as f:
        makro_products = json.load(f)
    print(f"   [OK] Loaded {len(makro_products)} Makro products")
    
    # Connect to database
    print("\n[INFO] Connecting to database...")
    config = load_env()
    print(f"   [OK] Host: {config['host']}:{config['port']}, DB: {config['database']}")
    
    conn = get_db_connection(config)
    print(f"   [OK] Connected successfully")
    
    # Extract and insert categories
    print("\n[INFO] Extracting categories...")
    categories = extract_categories(cfw_products, makro_products)
    print(f"   [OK] Found {len(categories)} unique categories")
    
    # Build Makro category mapping
    makro_category_map = build_makro_category_map(categories)
    print(f"   [OK] Generated {len(makro_category_map)} Makro category IDs")
    
    insert_categories(conn, categories)
    
    # Extract and insert departments
    print("\n[INFO] Extracting departments...")
    departments = extract_departments(cfw_products)
    print(f"   [OK] Found {len(departments)} unique departments")
    insert_departments(conn, departments)
    
    # Extract and insert classes
    print("\n[INFO] Extracting classes...")
    classes = extract_classes(cfw_products)
    print(f"   [OK] Found {len(classes)} unique classes")
    insert_classes(conn, classes)
    
    # Insert products
    print("\n[INFO] Inserting CFW products...")
    insert_cfw_products(conn, cfw_products)
    
    print("\n[INFO] Inserting Makro products...")
    insert_makro_products(conn, makro_products, makro_category_map)
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
