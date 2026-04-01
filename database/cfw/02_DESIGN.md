# CFW / Makro Food Comparison System - Design Document

**Date**: 2026-04-01
**Status**: Schema design complete, ready for data import

---

## Problem Overview

Building a food-based price comparison system within PriceHawk to compare two wholesale food retailers:

| Retailer | Products | Data Source | Update Frequency |
|----------|----------|-------------|-------------------|
| **CFW** (Central Food Wholesale) | 28,812 items | Excel template (`temp/Product_template_CFW.xlsx`) | Manual import |
| **Makro** | 14,398 items | JSON API (`temp/makro_complete.json`) | Daily live scraping (future) |

Both have:
- **Tier/Step Pricing**: Buy 1-2 @ price X, buy 3-5 @ price Y, buy 6+ @ price Z
- **Barcode & SKU**: Used for cross-retailer product matching
- **Physical Attributes**: Weight, volume, pack size
- **4-Level Categories**: Dept → Sub-Dept → Class → Sub-Class

---

## Step Price Normalization

### Problem
Both retailers store tier pricing differently:
- **Makro JSON**: `step_prices: [[1, 100], [3, 90], [6, 80]]` (qty, price pairs)
- **CFW Excel**: Tier columns (1 unit / 1-2 / 3-5 / 6+) with prices in separate cells

### Solution: Normalized JSONB Format

```json
[
  { "min_qty": 1, "price": 100 },
  { "min_qty": 3, "price": 90 },
  { "min_qty": 6, "price": 80 }
]
```

**Semantics**: "At minimum quantity 1, charge 100 THB. At 3+, charge 90 THB. At 6+, charge 80 THB."

### Implementation
1. **Makro conversion** (direct mapping):
   ```python
   # [[1, 100], [3, 90], [6, 80]] →
   step_prices = [{"min_qty": qty, "price": price} for qty, price in makro_data]
   ```

2. **CFW conversion** (from tier columns):
   ```python
   # Extract tier min quantities and prices from sheet
   # E.g., tier_1_unit=['Price1'], tier_1_2=['Price2'] →
   step_prices = [
       {"min_qty": 1, "price": tier_1_unit_price},
       {"min_qty": 2, "price": tier_1_2_price},
       {"min_qty": 3, "price": tier_3_5_price},
       {"min_qty": 6, "price": tier_6_plus_price}
   ]
   ```

### Price Unit Semantics
- **`price_unit='per_pack'`** (Makro): `step_prices[i].price` = total price for entire pack at that tier
  - If min_qty=3 and price=270, customer pays 270 THB for 3 packs
- **`price_unit='per_unit'`** (CFW): `step_prices[i].price` = unit price at that tier
  - If min_qty=3 and price=90, customer pays 90 THB per unit (total = 90 × quantity)

---

## Database Schema

### New Tables

#### `food_products` (extends `products`)
Stores food-specific attributes per product.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | SERIAL PRIMARY KEY | Food product ID |
| `product_id` | INTEGER FK | Link to base `products` table |
| `barcode` | TEXT | EAN/UPC for matching |
| `dept`, `sub_dept`, `class`, `sub_class` | TEXT | 4-level category hierarchy |
| `weight_grams` | INTEGER | Physical weight (null if not applicable) |
| `volume_ml` | INTEGER | Physical volume (null if solid) |
| `pack_size` | TEXT | Human-readable (e.g., "500g", "12 pieces") |
| `unit_price` | DECIMAL(10,4) | Price per gram/ml/unit for customer comparison |
| `unit_type` | VARCHAR(20) | 'per_gram', 'per_ml', 'per_piece', 'per_unit' |
| `step_prices` | JSONB | Normalized tier pricing array |
| `price_unit` | VARCHAR(20) | 'per_pack' (Makro) or 'per_unit' (CFW) |
| `created_at`, `updated_at` | TIMESTAMP | Audit timestamps |

#### `food_product_matches`
Matches CFW products (base) to Makro products (candidate).

| Column | Type | Purpose |
|--------|------|---------|
| `match_id` | SERIAL PRIMARY KEY | Match ID |
| `cfw_product_id` | INTEGER FK | CFW product in `products` |
| `makro_product_id` | INTEGER FK | Makro product in `products` |
| `is_same` | BOOLEAN | Are these the same product? |
| `confidence_score` | NUMERIC(5,4) | 0.0-1.0 match confidence |
| `match_reason` | TEXT | 'exact_barcode', 'sku_match', 'manual', etc. |
| `match_type` | VARCHAR(20) | 'auto' (system-matched), 'manual' (user-verified) |
| `verified_by_user` | BOOLEAN | Has the user reviewed this match? |
| `verified_result` | BOOLEAN | User's verdict (if verified) |
| `verified_at`, `verified_user_id` | TIMESTAMP, FK | When and by whom |

#### `food_price_history`
Historical price snapshots (for price trend analysis).

| Column | Type | Purpose |
|--------|------|---------|
| `price_id` | SERIAL PRIMARY KEY | History record ID |
| `product_id` | INTEGER FK | Product from `products` table |
| `current_price` | DECIMAL(10, 2) | Price at this snapshot |
| `unit_price` | DECIMAL(10, 4) | Price per gram/ml/unit at this time |
| `step_prices` | JSONB | Tier pricing snapshot |
| `scraped_at` | TIMESTAMP | When this price was recorded |

#### `food_watchlist_groups` / `food_watchlist_group_products`
User-created watchlists for tracking specific CFW products.

| Table | Columns | Purpose |
|-------|---------|---------|
| `food_watchlist_groups` | `group_id`, `user_id`, `name`, `description`, `created_at`, `updated_at` | Named watchlist group per user |
| `food_watchlist_group_products` | `id`, `group_id`, `product_id`, `added_at` | Foods in each group |

#### `food_price_alerts`
Tracks price change events for email notifications.

| Column | Type | Purpose |
|--------|------|---------|
| `alert_id` | SERIAL PRIMARY KEY | Alert record ID |
| `user_id` | INTEGER FK | User to notify |
| `product_id` | INTEGER FK | Which product changed |
| `alert_type` | VARCHAR(20) | 'price_drop', 'price_increase', etc. |
| `previous_price`, `current_price` | DECIMAL(10, 2) | Price before/after |
| `price_change_percent` | NUMERIC(6, 2) | Percentage change |
| `is_notified` | BOOLEAN | Has email been sent? |
| `notified_at`, `triggered_at` | TIMESTAMP | When alert triggered and sent |

---

## Key Design Decisions

### 1. Barcode + SKU Kept Separate
- `products.sku` — Retailer's catalog SKU
- `food_products.barcode` — EAN/UPC barcode
- Matching logic tries barcode first (higher confidence), then SKU

### 2. 4-Level Categories as Denormalized Columns
- No separate `categories` table
- Fixed hierarchy: `dept` → `sub_dept` → `class` → `sub_class`
- Simpler queries, no joins needed for category filtering

### 3. Step Prices as JSONB
- Flexible: can store 1, 5, or 10 tiers
- Queryable: PostgreSQL JSONB operators
- Example query: `SELECT * FROM food_products WHERE step_prices @> '[{"min_qty":1}]'`

### 4. Separate History Table
- `products.current_price` — Last known price
- `food_price_history` — Full timeline with snapshots
- Enables price trend visualization, historical comparison

### 5. Base Retailer = CFW
- CFW is the "primary" retailer
- `food_product_matches` always has `cfw_product_id` as the base
- Makro products matched to CFW for comparison

---

## Data Import Workflow (Next Steps)

### 1. Load CFW Excel (`temp/Product_template_CFW.xlsx`)

**From "Products" sheet**:
- SKU, barcode, name (TH+EN) → `products` table
- Dept, sub-dept, class, sub-class → `food_products`
- Tier prices (1 unit / 1-2 / 3-5 / 6+) → normalize to JSONB step_prices
- Pack size, weight, dimensions, color → `food_products`
- Brand, status → `products`

**From "Promotion Step Price" sheet** (if exists):
- Merge tier columns with any additional step rules

**Insert SQLs**:
```python
# Pseudo-code
for row in cfwsheet.rows:
    product = insert_into_products(
        retailer_id='cfw', sku=row.sku, name=row.name_en,
        brand=row.brand, link='', current_price=row.tier_1_price
    )
    insert_into_food_products(
        product_id=product.id,
        barcode=row.barcode,
        dept=row.dept, sub_dept=row.sub_dept,
        class=row.class_, sub_class=row.sub_class,
        weight_grams=row.weight,
        unit_price=row.tier_1_price / row.pack_qty,  # Calculate if needed
        step_prices=normalize_cfwtiers(row),         # Convert tiers
        price_unit='per_unit'  # CFW is always per-unit pricing
    )
```

### 2. Load Makro JSON (`temp/makro_complete.json`)

**From JSON**:
- name, sku, barcode → `products` table
- retailer='makro', link from data
- current_price, unit_price, step_prices (already normalized array)
- weight, volume, dimensions → `food_products`
- category → split into 4 levels if available (or use single category)

**Insert SQLs**:
```python
for item in makro_json:
    product = insert_into_products(
        retailer_id='makro', sku=item.sku, name=item.name,
        brand='', link=item.url, current_price=item.current_price
    )
    insert_into_food_products(
        product_id=product.id,
        barcode=item.barcode,
        dept='', sub_dept='', class='', sub_class=item.category or '',
        weight_grams=item.weight,
        volume_ml=item.volume,
        unit_price=item.unit_price,
        step_prices=item.step_prices,  # Already normalized array
        price_unit='per_pack'
    )
```

### 3. Generate Barcode Matches

```python
# Match CFW → Makro products by barcode
for cfw_product in food_products.filter(retailer_id='cfw'):
    matching_makro = food_products.filter(
        retailer_id='makro',
        barcode=cfw_product.barcode
    )
    for makro_product in matching_makro:
        if cfw_product.barcode:
            insert_into_food_product_matches(
                cfw_product_id=cfw_product.product_id,
                makro_product_id=makro_product.product_id,
                is_same=True,  # Assume barcode match = same product
                confidence_score=0.95,
                match_reason='exact_barcode'
            )
```

### 4. Initial Price History

```python
# Record current prices as history baseline
for product in products.filter(retailer_id in ['cfw', 'makro']):
    food_prod = food_products[product.id]
    insert_into_food_price_history(
        product_id=product.id,
        current_price=product.current_price,
        unit_price=food_prod.unit_price,
        step_prices=food_prod.step_prices,
        scraped_at=NOW()
    )
```

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `01_schema.sql` | DB schema creation (tables, indexes, triggers) |
| `02_design.md` | This document — design rationale and architecture |
| `03_import_cfw.py` | (To create) Load CFW Excel into DB |
| `03_import_makro.py` | (To create) Load Makro JSON into DB |
| `04_match_barcodes.py` | (To create) Auto-match CFW ↔ Makro by barcode |

---

## Next Phase Deliverables

### Phase 1: Data Import (Sprint 1)
- [ ] Load CFW Excel → 28,812 CFW products in DB
- [ ] Load Makro JSON → 14,398 Makro products in DB
- [ ] Auto-match by barcode → initial `food_product_matches` records

### Phase 2: Makro Scraper (Sprint 2)
- [ ] Build daily Makro price scraper
- [ ] Update `products.current_price` + `food_price_history` daily
- [ ] Scrape step prices + unit prices

### Phase 3: Frontend UI (Sprint 3)
- [ ] `/food-products` — List CFW products with Makro price comparison
- [ ] `/food-products/[sku]` — Detail: side-by-side tier pricing table
- [ ] `/food-watchlist` — Track specific CFW items
- [ ] `/food-comparison` — Verify product matches (barcode-assisted UI)

### Phase 4: Alerts (Sprint 4)
- [ ] Email alerts for price drops/increases
- [ ] Batch notification summary

---

## Technical Notes

### PostgreSQL JSONB Queries

**Find products with minimum tier < 3 units**:
```sql
SELECT * FROM food_products
WHERE step_prices @> '[{"min_qty": 1}]' OR step_prices @> '[{"min_qty": 2}]';
```

**Extract all minimum quantities**:
```sql
SELECT jsonb_agg(elem->'min_qty')
FROM food_products, jsonb_array_elements(step_prices) AS elem
WHERE product_id = 123;
```

### Makro Scraper Architecture
```
makro_price_scraper.py (cron entry point)
  └─ For each makro_product in food_products (retailer='makro'):
       ├─ Fetch from Makro API or scrape website
       ├─ Extract: current_price, unit_price, step_prices
       ├─ UPDATE products.current_price
       ├─ INSERT INTO food_price_history
       └─ Check for price changes → trigger food_price_alerts
```

---

## Questions / Decisions Made

**Q: Why not separate Makro into different database?**
A: Keep it simple, reuse PriceHawk infrastructure. Same PostgreSQL instance, different table prefix (`food_*` vs original tables).

**Q: How are categories 4-level if Makro has only 1 category in JSON?**
A: CFW has full 4-level hierarchy. Makro JSON may have only 1 category string. Import as `sub_class` (leaf level), leave others NULL or infer from product name.

**Q: Can we bulk edit / override matches?**
A: Yes — `verified_by_user=TRUE` allows users to correct auto-matches in frontend UI (like existing PriceHawk comparison page).

**Q: When do we scrape Makro prices?**
A: Not phase 1. Install initial data from static JSON. Phase 2 builds live scraper with cron job.
