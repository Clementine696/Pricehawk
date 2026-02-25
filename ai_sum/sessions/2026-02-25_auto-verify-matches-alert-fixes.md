# Session: Auto-Verify Matches + Alert Email Fixes

Date: 2026-02-25

---

## Changes Made

### 1. Fix: Alert email S-dept column empty
**File:** `backend/services/alert_service.py`

Both `get_price_changes_since()` and `get_status_changes()` queries didn't return `watchlist_group`.

Added to both queries:
```sql
LEFT JOIN products p_twd ON pm.base_product_id = p_twd.product_id AND p_twd.retailer_id = 'twd'
LEFT JOIN watchlist_sku_group_products wsgp ON COALESCE(p_twd.sku, p.sku) = wsgp.sku
LEFT JOIN watchlist_sku_groups wsg ON wsgp.group_id = wsg.group_id
```
And in SELECT: `wsg.name as watchlist_group`

- TWD rows: `p_twd` is NULL → `COALESCE(NULL, p.sku)` = own SKU ✓
- Competitor rows: `p_twd` resolves via `pm.base_product_id` → TWD SKU ✓
- Used `wsg.name` (not `display_name` — that column doesn't exist on this DB)

---

### 2. Fix: Alert email price cells — add hyperlinks
**File:** `backend/services/email_service.py` — `_generate_price_excel()` (~line 791)

Old Price (col 7) and Updated Price (col 9) cells now hyperlink to product page:
```python
if link:
    cell.hyperlink = link
    cell.font = Font(color='0000FF', underline='single')
```

---

### 3. Fix: auto_verify_matches.py — URL not found (3016 → 7)
**File:** `temp/auto_verify_matches.py`

**Root causes identified:**
- gbh: Excel uses `/product/detail/{barcode}` but DB stores `/product/...i.{barcode}` — different URL formats for same product
- All retailers: many products in Excel answer file were never scraped into DB

**Fixes:**
1. Added `extract_barcode()` — extracts barcode from both gbh URL formats
2. Added `extract_url_id()` — extracts trailing numeric ID from slugs (dh: `-10093499.html`)
3. Added `derive_sku()` — gets SKU from item, falls back to url_id, barcode, product_key
4. Added `load_json_index()` — loads `temp/data/*.json` at startup into url+barcode indexes
5. Added JSON fallback in match loop: if not in DB, find in JSON → INSERT product → create match

**JSON files used:** `temp/data/{boonthavorn,dohome,globalhouse,homepro,megahome}.json`

**Insert uses:** `ON CONFLICT (retailer_id, sku) DO UPDATE` — safe to re-run

**Final results:**
```
Already verified:    2114
Updated (verified):  519
Created (new match): 2490
Inserted from JSON:  2375
URL not in DB:       7
No URL in Excel:     15575
TWD SKU not in DB:   78
```

---

## Files Modified

| File | Change |
|------|--------|
| `backend/services/alert_service.py` | Both SQL queries: JOIN via p_twd to get watchlist_group for all retailers |
| `backend/services/email_service.py` | Price cells in alert Excel now hyperlink to product URL |
| `temp/auto_verify_matches.py` | JSON fallback matching + product insert; barcode + url_id extraction |
