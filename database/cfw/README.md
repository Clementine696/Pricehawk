# CFW / Makro Food Comparison System

A new food-based price comparison module built within the existing PriceHawk repository.

**Purpose**: Compare wholesale food prices between CFW (Central Food Wholesale) and Makro across 28K+ products with tier/step pricing, barcode matching, and price tracking.

---

## Folder Structure

```
database/cfw/
├── 01_schema.sql          # Database schema (tables, indexes, triggers)
├── 02_DESIGN.md           # Architecture & design decisions (detailed explanation)
├── README.md              # This file
├── 03_import_cfw.py       # (To create) Load CFW Excel data
├── 03_import_makro.py     # (To create) Load Makro JSON data
└── 04_match_barcodes.py   # (To create) Auto-match CFW ↔ Makro
```

---

## Quick Start

### 1. Initialize Database Schema
```bash
psql $DATABASE_URL -f database/cfw/01_schema.sql
```

This creates:
- `food_products` — Food product data (barcode, categories, weight, unit prices, step prices)
- `food_product_matches` — CFW ↔ Makro product matching
- `food_price_history` — Historical prices
- `food_watchlist_groups` / `food_watchlist_group_products` — User watchlists
- `food_price_alerts` — Price change alerts

### 2. Load Data (Next Phase)
```bash
python database/cfw/03_import_cfw.py          # Load 28,812 CFW products from Excel
python database/cfw/03_import_makro.py        # Load 14,398 Makro products from JSON
python database/cfw/04_match_barcodes.py      # Auto-match by barcode
```

### 3. Verify
```sql
SELECT COUNT(*) FROM food_products;           -- Should be ~43K (28K CFW + 14K Makro)
SELECT COUNT(*) FROM food_product_matches;    -- Should be ~thousands (barcode matches)
```

---

## Key Concepts

### Step/Tier Pricing
Both CFW and Makro use quantity-based pricing tiers. Normalized to:
```json
[
  { "min_qty": 1, "price": 100 },
  { "min_qty": 3, "price": 90 },
  { "min_qty": 6, "price": 80 }
]
```

See `02_DESIGN.md` for conversion details.

### 4-Level Categories
- `dept` — Department
- `sub_dept` — Sub-department
- `class` — Class
- `sub_class` — Sub-class (most specific)

### Barcode Matching
Primary matching strategy: exact barcode match → `food_product_matches` confidence=0.95.
Fallback: SKU match (lower confidence), manual verification.

### Price Unit Semantics
- **CFW** (`price_unit='per_unit'`): prices are per individual unit
- **Makro** (`price_unit='per_pack'`): prices are per bulk pack

---

## Data Sources

| Source | Location | Format | Size |
|--------|----------|--------|------|
| **CFW** | `temp/Product_template_CFW.xlsx` | Excel (4 sheets) | 28,812 rows |
| **Makro** | `temp/makro_complete.json` | JSON array | 14,398 rows |

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (Next.js)                     │
│  /food-products, /food-comparison, etc. │
└───────────────┬─────────────────────────┘
                │ API calls
                ▼
┌─────────────────────────────────────────┐
│  Backend (FastAPI)                      │
│  /api/food/products                     │
│  /api/food/matches                      │
│  /api/food/watchlist                    │
└───────────────┬─────────────────────────┘
                │ SQL queries
                ▼
┌─────────────────────────────────────────┐
│  PostgreSQL Database                    │
│  food_products                          │
│  food_product_matches                   │
│  food_price_history                     │
│  food_watchlist_*                       │
│  food_price_alerts                      │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **Phase 0** | Database schema (01_schema.sql) | ✅ Complete |
| **Phase 0** | Architecture documentation (02_DESIGN.md) | ✅ Complete |
| **Phase 1** | Data import from CFW Excel + Makro JSON | ⏳ Next |
| **Phase 1** | Barcode auto-matching | ⏳ Next |
| **Phase 2** | Makro live price scraper (daily) | 📅 Future |
| **Phase 3** | Frontend pages (`/food-*`) | 📅 Future |
| **Phase 4** | Email alerts for price changes | 📅 Future |

---

## File Reference

### `01_schema.sql`
**Purpose**: Creates all food-related database tables.

Tables created:
- `food_products` — Core food product records
- `food_product_matches` — CFW ↔ Makro matching
- `food_price_history` — Historical price snapshots
- `food_watchlist_groups` / `food_watchlist_group_products` — User watchlists
- `food_price_alerts` — Price change events

Indexes + triggers included.

### `02_DESIGN.md`
**Purpose**: Deep-dive architecture document.

Covers:
- Step price normalization strategy
- Schema design rationale
- Data import workflow (pseudo-code)
- PostgreSQL JSONB tips
- Makro scraper architecture
- FAQ + design decisions

Read this before implementing data import scripts.

---

## Next Steps

1. **Inspect data**: Already done (temp/ files reviewed)
2. **Schema**: Already created (01_schema.sql)
3. **Import CFW**: Create `03_import_cfw.py` to load Excel
4. **Import Makro**: Create `03_import_makro.py` to load JSON
5. **Match**: Create `04_match_barcodes.py` to link products
6. **Verify**: Query database to confirm imports successful
7. **Build frontend**: Create pages to visualize food data
8. **Scraper**: Build Makro price scraper (daily updates)

---

## Questions?

Refer to `02_DESIGN.md` for detailed design rationale and architecture decisions. For implementation specifics, see the import script templates (to be created).
