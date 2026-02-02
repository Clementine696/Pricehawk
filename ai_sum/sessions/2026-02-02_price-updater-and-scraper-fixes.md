# Price Updater and Scraper Fixes - Complete Session Summary

**Date**: 2026-02-02
**Branch**: sit
**Status**: ✅ Completed

## Overview

This session focused on fixing critical issues with the Thai Watsadu scraper and price updater service. We implemented three major fixes:

1. **Active/Inactive Product Status Indicators** - UI feature to show product scraping health
2. **Thai Watsadu Scraper Price Fix** - Fixed wrong price extraction from HTML
3. **Price Updater Continuous Retry** - Removed skip logic for failed products

---

## Part 1: Active/Inactive Product Status Indicators

### Problem
Need to show users which products are being successfully scraped vs which have persistent failures.

### Solution
Added status indicators based on `scrape_fail_count`:
- **Active** (green): scrape_fail_count < 3 - Product is being monitored regularly
- **Inactive** (red): scrape_fail_count >= 3 - Product has failed to scrape multiple times

### Implementation

#### Backend Changes
**File**: `backend/main.py`

1. **Product Detail API** (lines 2121-2148)
   - Added `scrape_fail_count` to base product query
   - Added to matched products query (line 2170)
   - Included in both verified and non-verified match responses

```python
# Base product
SELECT p.product_id, p.sku, p.name, ..., p.scrape_fail_count
FROM products p

# Response
"scrape_fail_count": product["scrape_fail_count"] if product["scrape_fail_count"] is not None else 0
```

#### Frontend Changes
**File**: `ui/src/app/products/[id]/page.tsx`

1. **Updated TypeScript Interface** (line 35)
```typescript
interface Product {
  // ... existing fields
  scrape_fail_count: number;
}
```

2. **Thai Watsadu Card Status Box** (lines 707-723)
```tsx
{product.scrape_fail_count >= 3 ? (
  <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
    <AlertCircle className="w-4 h-4 text-red-600" />
    <p className="text-sm font-medium text-red-800">Inactive Product</p>
  </div>
) : (
  <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
    <CheckCircle className="w-4 h-4 text-green-600" />
    <p className="text-sm font-medium text-green-800">Active Product</p>
  </div>
)}
```

3. **Matched Product Status** (lines 876-920)
   - Shows status on bottom left with verification buttons
   - Only displays for verified correct matches
   - Text-only style (no background box)

```tsx
<div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center gap-3">
  {/* Left: Active/Inactive Status */}
  <div>
    {match.verified_by_user && match.is_same && (
      match.product.scrape_fail_count >= 3 ? (
        <div className="flex items-center gap-1.5 text-xs text-red-600 font-medium">
          <AlertCircle className="w-4 h-4" />
          Inactive Product
        </div>
      ) : (
        <div className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
          <CheckCircle className="w-4 h-4" />
          Active Product
        </div>
      )
    )}
  </div>

  {/* Right: Verification Buttons */}
  <div className="flex gap-3">
    {/* Undo, Correct Match, Incorrect Match buttons */}
  </div>
</div>
```

4. **Layout Improvements** (lines 689-704)
   - Moved "Updated" timestamp to same row as "View on Thai Watsadu" link
   - Used flexbox with justify-between for left-right alignment

### Commit
**Hash**: `f2184df`
**Message**: "Add active/inactive product status indicators"

---

## Part 2: Thai Watsadu Scraper Price Fix

### Problem
Both the cron job price updater and resync button were getting **wrong prices** because the scraper extracted from JSON-LD and `__NEXT_DATA__` instead of the actual displayed HTML.

### Investigation
Confirmed both systems use the same scraper:
- **Price Updater**: `backend/services/price_updater.py` → `scrape_product()` (line 530)
- **Resync Button**: `backend/main.py` → `scrape_single_url()` (line 2915)
- **Both call**: `backend/scraper-url/adws/adw_ecommerce_product_scraper.py`

### Solution
Changed scraper to extract prices from rendered HTML DOM instead of JSON data.

### Three Price Display Cases

User provided three Thai Watsadu product examples:

#### Case 1: Normal Discount
**URL**: https://www.thaiwatsadu.com/th/product/60296303

**HTML**:
```html
<span class="ms-1 font-price text-redPrice text-2xl">1,830</span>
<div class="text-grayDark line-through text-lg">ราคาเดิม<!-- --> <!-- -->2,180.00</div>
```

**Expected**:
- `current_price`: 1,830
- `original_price`: 2,180

---

#### Case 2: Coupon Discount
**URL**: https://www.thaiwatsadu.com/th/product/60422670

**HTML**:
```html
<span class="ms-1 font-price text-redPrice text-2xl">7,740</span>
<div class="bg-[#F9A01B]"><!-- Coupon badge --></div>
<div class="text-grayDark line-through text-lg">ราคาเดิม<!-- --> <!-- -->8,730.00</div>
```

**Expected**:
- `current_price`: 7,740 (ignore coupon badge)
- `original_price`: 8,730

---

#### Case 3: Pack/Multiple Pricing
**URL**: https://www.thaiwatsadu.com/th/product/60425652

**HTML**:
```html
<!-- Pack options: ทุก 6 ชิ้น = 1,390, ทุก 4 ชิ้น = 1,395 -->
<div class="whitespace-nowrap font-semibold">1 <!-- -->ชิ้น</div>
<div class="text-center text-primary text-[24px] font-price">1,420</div>
```

**Expected**:
- `current_price`: 1,420 (find "1 ชิ้น" container, not bulk prices)
- `original_price`: None

---

### Implementation

**File**: `backend/scraper-url/adws/adw_modules/product_extractor.py` (lines 991-1061)

#### Strategy
1. Extract from HTML DOM first (most reliable)
2. Override JSON-LD prices if HTML prices found
3. Fallback to `__NEXT_DATA__` only if HTML extraction fails

#### Code Changes

```python
# 2b. Extract price from rendered HTML (Thai Watsadu)
html_current_price = None
html_original_price = None

# CASE 1: Pack/Multiple pricing - Find "1 ชิ้น" (1 piece) price
pack_price_pattern = r'<div[^>]*class="[^"]*whitespace-nowrap[^"]*font-semibold[^"]*"[^>]*>1\s*(?:<!--|&nbsp;|<!--\s*-->)\s*ชิ้น</div>(?:(?!</div>).)*?<div[^>]*class="[^"]*text-center[^"]*text-primary[^"]*text-\[24px\][^"]*font-price[^"]*"[^>]*>([\d,]+)</div>'
pack_match = re.search(pack_price_pattern, html_content, re.DOTALL | re.IGNORECASE)
if pack_match:
    price_str = pack_match.group(1).replace(',', '')
    html_current_price = float(price_str)

# CASE 2 & 3: Normal and Coupon case - Red price
if not html_current_price:
    red_price_pattern = r'<span[^>]*class="[^"]*ms-1[^"]*font-price[^"]*text-redPrice[^"]*text-2xl[^"]*"[^>]*>([\d,]+)</span>'
    red_match = re.search(red_price_pattern, html_content, re.IGNORECASE)
    if red_match:
        price_str = red_match.group(1).replace(',', '')
        html_current_price = float(price_str)

# Extract original price (ราคาเดิม with line-through)
original_price_pattern = r'<div[^>]*class="[^"]*text-grayDark[^"]*line-through[^"]*"[^>]*>ราคาเดิม(?:<!--|&nbsp;|<!--\s*-->|\s)*(?:<!--|&nbsp;|<!--\s*-->|\s)*([\d,]+(?:\.\d{2})?)</div>'
original_match = re.search(original_price_pattern, html_content, re.IGNORECASE)
if original_match:
    price_str = original_match.group(1).replace(',', '')
    html_original_price = float(price_str)

# Override with HTML prices if found
if html_current_price:
    product.current_price = html_current_price
if html_original_price:
    product.original_price = html_original_price

# Fallback to __NEXT_DATA__ if needed
if not product.current_price:
    # Try JSON extraction as last resort
    ...
```

### Testing

**Regex Validation**:
```bash
# Test normal case
html = '<span class="ms-1 font-price text-redPrice text-2xl">1,830</span>'
# ✅ Matched: 1,830

html = '<div class="text-grayDark line-through">ราคาเดิม<!-- --> <!-- -->2,180.00</div>'
# ✅ Matched: 2,180.00
```

**Integration Test**:
```bash
$ python ./backend/scraper-url/adws/adw_ecommerce_product_scraper.py --urls-file test_urls.txt

✅ Successfully extracted: ปั๊มน้ำอัตโนมัติ 250 วัตต์...
Price: 7740.00 (Coupon case - correct!)
```

### Commit
**Hash**: `aff148c`
**Message**: "Fix Thai Watsadu price extraction to use rendered HTML"

---

## Part 3: Price Updater Continuous Retry

### Problem
Price updater was **permanently skipping** products with `scrape_fail_count >= 3`, even if their URLs came back online later.

### Previous Behavior
```python
# Query had this filter:
AND (p.scrape_fail_count IS NULL OR p.scrape_fail_count < %s)

# Result: Products with 3+ failures were never scraped again
# Required manual SQL to reset: UPDATE products SET scrape_fail_count = 0
```

### Solution
Remove the skip logic - keep retrying all products continuously.

### Implementation

**File**: `backend/services/price_updater.py`

#### 1. Remove Filter from Query (line 431)
**Before**:
```python
WHERE p.link IS NOT NULL AND p.link != ''
  AND (p.scrape_fail_count IS NULL OR p.scrape_fail_count < %s)
  AND (...)
```

**After**:
```python
WHERE p.link IS NOT NULL AND p.link != ''
  AND (
      p.retailer_id = 'twd'
      OR EXISTS (...)
  )
```

#### 2. Update Documentation (lines 9, 18-20)
**Before**:
- "Failure tracking: Skip products after 3 consecutive failures"
- "Products with scrape_fail_count >= 3 are skipped"

**After**:
- "Failure tracking: Tracks consecutive failures (scrape_fail_count)"
- "Products are continuously retried even after multiple failures"
- "Failed products may come back online, so we keep trying"

#### 3. Update Method Docstring (line 412)
**Before**:
```python
Skips:
- Unmatched/unverified retailer products (~50%+ of database)
- Products that have failed too many times (scrape_fail_count >= MAX_SCRAPE_FAILURES)
```

**After**:
```python
Skips:
- Unmatched/unverified retailer products (~50%+ of database)

Note: Products are attempted even if they have high scrape_fail_count, as URLs may come back online.
```

#### 4. Update Logging (lines 869-872)
**Before**:
```python
if current_fails >= self.MAX_SCRAPE_FAILURES:
    logger.warning(f"Product {sku} reached max failures ({current_fails}), will be skipped in future runs")
```

**After**:
```python
if current_fails >= self.MAX_SCRAPE_FAILURES:
    logger.warning(f"Product {sku} has {current_fails} consecutive failures (marked as inactive)")
```

### How It Works Now

1. **Price updater fetches ALL products** (including those with high fail counts)
2. **Attempts to scrape** each one
3. **On success**:
   - Updates price in database
   - Resets `scrape_fail_count` to 0 (line 819)
   - Product becomes "Active" in UI
4. **On failure**:
   - Increments `scrape_fail_count` (line 862: `COALESCE(scrape_fail_count, 0) + 1`)
   - Updates `last_updated_at`
   - Product stays in queue
   - Count keeps going up: 1, 2, 3, 4, 5, ... (no cap)
5. **UI shows "Inactive"** when count >= 3

### Testing

```bash
$ python -c "from price_updater import PriceUpdater; ..."

Fetched 10 products
  SKU: 10127354, Retailer: dh, Fails: 3, SKIPPED BEFORE ✅ Now included
  SKU: 10083535, Retailer: dh, Fails: 3, SKIPPED BEFORE ✅ Now included
  SKU: 10350641, Retailer: dh, Fails: 3, SKIPPED BEFORE ✅ Now included
  ...
SUCCESS: Includes 10 products with fails >= 3
```

### Commits
**Hash**: `c60462c` - "Remove scrape_fail_count filter to keep retrying all products"
**Hash**: `e28b01d` - "Update failure logging to reflect continuous retry behavior"

---

## Summary of All Changes

### Commits Made
1. **f2184df** - Add active/inactive product status indicators
2. **aff148c** - Fix Thai Watsadu price extraction to use rendered HTML
3. **c60462c** - Remove scrape_fail_count filter to keep retrying all products
4. **e28b01d** - Update failure logging to reflect continuous retry behavior

### Files Modified

#### Backend
1. **backend/main.py**
   - Added scrape_fail_count to product detail API
   - Added scrape_fail_count to matched products API

2. **backend/services/price_updater.py**
   - Removed scrape_fail_count < 3 filter from query
   - Updated documentation
   - Updated logging messages

3. **backend/scraper-url/adws/adw_modules/product_extractor.py**
   - Changed from JSON-LD to HTML DOM price extraction
   - Added regex patterns for 3 Thai Watsadu price cases
   - Override JSON prices with HTML prices

#### Frontend
4. **ui/src/app/products/[id]/page.tsx**
   - Added scrape_fail_count to Product interface
   - Added status indicator icons (CheckCircle, AlertCircle)
   - Added status box to Thai Watsadu card
   - Added status text to matched product cards
   - Repositioned Updated timestamp

---

## Impact

### Before This Session
- ❌ Users couldn't see which products were failing to scrape
- ❌ Scraper extracted wrong prices from JSON data
- ❌ Price updater permanently skipped failed products
- ❌ Required manual SQL to retry failed products

### After This Session
- ✅ Active/Inactive status clearly visible in UI
- ✅ Scraper extracts correct prices from HTML
- ✅ Both cron job and resync button use same (fixed) scraper
- ✅ Price updater continuously retries all products
- ✅ Products self-recover when URLs come back online
- ✅ No manual intervention needed

---

## Key Technical Decisions

### 1. Why HTML Over JSON for Prices?
**Problem**: JSON-LD and `__NEXT_DATA__` contain internal pricing data that doesn't always match the UI.

**Solution**: Extract from rendered HTML to get exactly what users see.

**Benefit**: Reliable, accurate prices that match the display.

---

### 2. Why Keep Retrying Failed Products?
**Problem**: URLs may be temporarily down but come back online later.

**Solution**: Remove the skip logic, continuously retry all products.

**Benefit**: Products self-recover without manual intervention.

---

### 3. Why Show Status in UI?
**Problem**: Users need visibility into scraping health.

**Solution**: Active/Inactive indicators based on fail count.

**Benefit**: Users can identify problem products and take action.

---

## Testing Recommendations

1. **Test scraper with all 3 URL cases**:
   - Normal discount case
   - Coupon discount case
   - Pack/multiple pricing case

2. **Test price updater**:
   - Run cron job and verify products with high fail counts are retried
   - Check that successful scrapes reset fail count to 0

3. **Test UI status indicators**:
   - Products with fail count < 3 show "Active Product"
   - Products with fail count >= 3 show "Inactive Product"
   - Verified matches show status on bottom left

4. **Test resync button**:
   - Click resync on product detail page
   - Verify prices update correctly
   - Check that fail count resets on success

---

## Future Enhancements

1. Add bulk reset button for inactive products in admin panel
2. Add analytics dashboard showing active vs inactive ratio
3. Add email notifications when products become inactive
4. Add manual retry button for individual inactive products
5. Consider adding max fail count cap (e.g., stop at 100 to prevent unbounded growth)
6. Add scraper health monitoring and alerts

---

## Documentation Created

1. `ai_sum/sessions/2026-02-02_active-inactive-product-status.md` - Status indicators
2. `ai_sum/sessions/2026-02-02_thai-watsadu-scraper-price-fix.md` - Scraper fix
3. `ai_sum/sessions/2026-02-02_price-updater-and-scraper-fixes.md` - This summary

---

## Branch Status

**Current Branch**: sit
**Ready for**: Testing and merge to uat

All changes are committed and documented. The system is ready for testing with real products.
