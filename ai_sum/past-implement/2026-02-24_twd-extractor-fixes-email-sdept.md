# Session: Thai Watsadu Extractor Fixes + Email S-dept Fix

Date: 2026-02-24

---

## Changes Made

### 1. Fix: TWD Extractor — Wrong price from suggested products (CASE 2)
**File:** `backend/scraper-url/adws/adw_modules/product_extractor.py` — CASE 2 red price pattern (~line 1016)

`re.search` could match suggested product prices before the main product price. Anchored pattern on `<span>฿</span>` which only appears in the main product block (suggested products use `<div>฿</div>`).

```python
# BEFORE:
red_price_pattern = r'<span[^>]*class="[^"]*font-price[^"]*text-redPrice[^"]*"[^>]*>([\d,]+)</span>'

# AFTER:
red_price_pattern = r'<span[^>]*class="[^"]*text-redPrice[^"]*"[^>]*>฿</span>\s*<span[^>]*class="[^"]*font-price[^"]*text-redPrice[^"]*"[^>]*>([\d,]+(?:\.\d+)?)</span>'
```

Also added `(?:\.\d+)?` for decimal prices (bonus fix).

---

### 2. Fix: TWD Extractor — Pack price instead of 1-piece price (CASE 1)
**File:** `backend/scraper-url/adws/adw_modules/product_extractor.py` — CASE 1 pack price pattern (~line 1002)

1-piece price uses `text-[40px]` class and has no `text-center`, but pattern required `text-[24px]` and `text-center`. CASE 1 never matched → fell through to JSON-LD which returned the pack (per-unit) price.

```python
# BEFORE:
pack_price_pattern = r'...<div[^>]*class="[^"]*text-center[^"]*text-primary[^"]*text-\[24px\][^"]*font-price[^"]*"[^>]*>([\d,]+)</div>'

# AFTER:
pack_price_pattern = r'...<div[^>]*class="[^"]*text-primary[^"]*text-\[(?:24|40)px\][^"]*font-price[^"]*"[^>]*>([\d,]+(?:\.\d+)?)</div>'
```

Changes:
- `text-\[24px\]` → `text-\[(?:24|40)px\]` — accepts both 24px (pack cards) and 40px (1-piece card)
- Removed `text-center` requirement — 1-piece card doesn't have it
- Added `(?:\.\d+)?` for decimal prices

---

### 3. Fix: Price change alert email — S-dept column always empty
**File:** `backend/services/alert_service.py`

`email_service.py` uses `product.get('watchlist_group', '')` at lines 781 and 868 for the S-dept column in Excel attachments. Both queries in `alert_service.py` didn't include `watchlist_group` in their result sets.

**Fix:** Added LEFT JOINs to `watchlist_sku_group_products` and `watchlist_sku_groups` in both queries, selecting `wsg.display_name as watchlist_group`.

Applied to:
- `get_price_changes_since()` — price change alerts (~line 254-255)
- `get_status_changes()` — product active/inactive status alerts (~line 304-305)

```sql
LEFT JOIN watchlist_sku_group_products wsgp ON p.sku = wsgp.sku AND p.retailer_id = 'twd'
LEFT JOIN watchlist_sku_groups wsg ON wsgp.group_id = wsg.group_id
```
And in SELECT: `wsg.display_name as watchlist_group`

The JOIN condition `AND p.retailer_id = 'twd'` ensures only TWD products match the watchlist (S-dept only applies to TWD). Non-TWD products get NULL → empty string in Excel.

---

## Files Modified

| File | Change |
|------|--------|
| `backend/scraper-url/adws/adw_modules/product_extractor.py` | CASE 2: anchor red price on `<span>฿</span>`; CASE 1: accept `text-[40px]`, remove `text-center` requirement |
| `backend/services/alert_service.py` | Both SQL queries: JOIN watchlist tables to populate `watchlist_group` field |

---

## Key Decisions

- HTML distinction: main product `฿` is in `<span>`, suggested product `฿` is in `<div>` — reliable anchor
- 1-piece price card uses `text-[40px]`, pack cards use `text-[24px]` — CASE 1 needed to accept both
- `watchlist_sku_groups.display_name` is the correct column (not `name`) — used for the S-dept label in the UI
- JOIN condition `AND p.retailer_id = 'twd'` prevents false matches from other retailers' SKUs
