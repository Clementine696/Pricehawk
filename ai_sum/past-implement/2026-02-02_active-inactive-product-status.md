# Active/Inactive Product Status Indicators

**Date**: 2026-02-02
**Branch**: sit
**Status**: ✅ Completed

## Overview

This session implemented active/inactive status indicators for products based on their scrape failure count. Products that fail to scrape 3 or more consecutive times are marked as "Inactive," while products being monitored successfully are marked as "Active." The feature applies to both Thai Watsadu base products and verified correct matches from other retailers.

---

## 1. Backend API Changes

### 1.1 Add scrape_fail_count to Product Detail Response

**Files Modified**:
- `backend/main.py` (lines 2121-2148)

**Changes**:
- Added `p.scrape_fail_count` to the base product query
- Included `scrape_fail_count` in the base product response object
- Defaults to 0 if NULL

**Query Update**:
```python
cur.execute("""
    SELECT p.product_id, p.sku, p.name, p.brand, p.category,
           p.current_price, p.original_price, p.link, p.image,
           p.last_updated_at, p.scrape_fail_count,
           r.name as retailer_name, r.retailer_id
    FROM products p
    JOIN retailers r ON p.retailer_id = r.retailer_id
    WHERE p.product_id = %s
""", (product_id,))
```

**Response Object**:
```python
base_product = {
    # ... other fields ...
    "scrape_fail_count": product["scrape_fail_count"] if product["scrape_fail_count"] is not None else 0,
}
```

---

### 1.2 Add scrape_fail_count to Matched Products

**Files Modified**:
- `backend/main.py` (lines 2152-2256)

**Changes**:
- Added `p2.scrape_fail_count as matched_scrape_fail_count` to matched products query
- Included field in both verified and non-verified match product objects
- Defaults to 0 if NULL

**Query Update**:
```python
cur.execute("""
    SELECT
        pm.match_id,
        pm.is_same,
        # ... other fields ...
        p2.scrape_fail_count as matched_scrape_fail_count,
        r.name as matched_retailer_name,
        r.retailer_id as matched_retailer_id
    FROM product_matches pm
    JOIN products p2 ON pm.candidate_product_id = p2.product_id
    JOIN retailers r ON p2.retailer_id = r.retailer_id
    WHERE pm.base_product_id = %s
    ORDER BY r.name, pm.confidence_score DESC NULLS LAST
""", (product_id,))
```

**Updated in Two Locations**:
1. Verified correct matches (line 2228)
2. Non-verified matches (line 2256)

Both include:
```python
"scrape_fail_count": row["matched_scrape_fail_count"] if row["matched_scrape_fail_count"] is not None else 0,
```

---

## 2. Frontend UI Changes

### 2.1 Add Status Icons

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (line 8)

**Changes**:
- Added `CheckCircle` and `AlertCircle` icons from lucide-react

**Import Statement**:
```typescript
import { ArrowLeft, ExternalLink, Check, X, Plus, ChevronDown, ChevronUp,
         RotateCcw, Loader2, RefreshCw, TrendingUp, TrendingDown, Download,
         Calendar, CheckCircle, AlertCircle } from 'lucide-react';
```

---

### 2.2 Update Product Interface

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 22-36)

**Changes**:
- Added `scrape_fail_count: number` to Product interface

**Interface Update**:
```typescript
interface Product {
  product_id: number;
  sku: string;
  name: string;
  brand: string | null;
  category: string | null;
  current_price: number | null;
  original_price: number | null;
  link: string | null;
  image: string | null;
  retailer_name: string;
  retailer_id: string;
  last_updated_at: string | null;
  scrape_fail_count: number;  // NEW
}
```

---

### 2.3 Thai Watsadu Card Status Indicator

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 707-723)

**Changes**:
- Added status indicator box below the View/Updated row
- Shows "Inactive Product" (red) if scrape_fail_count >= 3
- Shows "Active Product" (green) if scrape_fail_count < 3

**Implementation**:
```tsx
{/* Product Status Indicator */}
<div className="mt-4">
  {product.scrape_fail_count >= 3 ? (
    <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
      <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-red-800">Inactive Product</p>
      </div>
    </div>
  ) : (
    <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-green-800">Active Product</p>
      </div>
    </div>
  )}
</div>
```

**Visual Design**:
- **Inactive**: Red background (`bg-red-50`), red border, AlertCircle icon
- **Active**: Green background (`bg-green-50`), green border, CheckCircle icon
- Box layout with icon on left, text centered vertically

---

### 2.4 Updated Timestamp Repositioning

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 689-704)

**Changes**:
- Moved "Updated" timestamp to same row as "View on Thai Watsadu" link
- Used flexbox with `justify-between` for left-right alignment

**Layout Update**:
```tsx
{/* View link and Updated timestamp on same row */}
<div className="mt-4 flex items-center justify-between">
  {product.link && (
    <a
      href={product.link}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 text-cyan-500 hover:text-cyan-600"
    >
      <ExternalLink className="w-4 h-4" />
      View on {product.retailer_name}
    </a>
  )}
  <div className="text-sm text-gray-500">
    Updated: {formatLastUpdated(product.last_updated_at)}
  </div>
</div>
```

**Result**:
- "View on Thai Watsadu" on the left
- "Updated: X hours ago" on the right
- Both vertically centered in same row

---

### 2.5 Matched Product Status Indicators

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 876-920)

**Changes**:
- Added active/inactive status to bottom left of verification actions row
- Only shows for verified correct matches
- Positioned alongside verification buttons (Undo/Correct/Incorrect)

**Implementation**:
```tsx
{/* Verification Actions */}
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

**Display Logic**:
- Only visible for matches where:
  - `verified_by_user = true` (user has verified the match)
  - `is_same = true` (match marked as correct)
- Shows "Inactive Product" if `scrape_fail_count >= 3`
- Shows "Active Product" if `scrape_fail_count < 3`

**Visual Design**:
- Smaller text (`text-xs`) compared to base product
- Same color scheme (red for inactive, green for active)
- Inline layout with icon and text

---

## 3. Status Logic and Behavior

### 3.1 Active Status
- **Condition**: `scrape_fail_count < 3`
- **Meaning**: Product is being scraped successfully and updated regularly
- **Visual**: Green background/text with CheckCircle icon
- **Applies to**:
  - Thai Watsadu base products (always shown)
  - Verified correct matches from other retailers (shown when verified)

### 3.2 Inactive Status
- **Condition**: `scrape_fail_count >= 3`
- **Meaning**: Product has failed to scrape 3 or more consecutive times
- **Visual**: Red background/text with AlertCircle icon
- **Applies to**:
  - Thai Watsadu base products (always shown)
  - Verified correct matches from other retailers (shown when verified)

### 3.3 When Status is Displayed

**Thai Watsadu Card**:
- Status always displayed for base product
- Appears below the View/Updated row
- Full box with background color and border

**Retailer Match Cards**:
- Status only displayed for verified correct matches
- Appears on bottom left in verification actions row
- Text-only style (no background box)
- Hidden for unverified matches and rejected matches

---

## 4. Layout Changes Summary

### Before
```
Thai Watsadu Card:
├─ Price
├─ View on Thai Watsadu
├─ Updated: X hours ago
└─ [rest of card]

Match Card:
├─ Product details
├─ Updated: X hours ago
└─ [Undo] [Correct Match]
```

### After
```
Thai Watsadu Card:
├─ Price
├─ View on Thai Watsadu          Updated: X hours ago
├─ ✓ Active Product / ⚠ Inactive Product
└─ [rest of card]

Match Card:
├─ Product details
├─ Updated: X hours ago
└─ ✓ Active Product              [Undo] [Correct Match]
   (only if verified correct)
```

---

## Summary of Files Modified

### Backend
1. **backend/main.py**
   - Line 2124: Add scrape_fail_count to base product query
   - Line 2148: Include scrape_fail_count in base product response
   - Line 2170: Add matched_scrape_fail_count to matches query
   - Line 2228: Include scrape_fail_count in verified match response
   - Line 2256: Include scrape_fail_count in non-verified match response

### Frontend
2. **ui/src/app/products/[id]/page.tsx**
   - Line 8: Import CheckCircle and AlertCircle icons
   - Line 35: Add scrape_fail_count to Product interface
   - Lines 689-704: Move Updated timestamp to same row as View link
   - Lines 707-723: Add status indicator box to Thai Watsadu card
   - Lines 876-920: Add status indicator to matched product verification row

---

## Testing Checklist

- [x] scrape_fail_count returned in product detail API response
- [x] scrape_fail_count returned for matched products
- [x] Thai Watsadu card shows "Active Product" when count < 3
- [x] Thai Watsadu card shows "Inactive Product" when count >= 3
- [x] Matched products show status only when verified correct
- [x] Status appears on bottom left with verification buttons
- [x] Updated timestamp appears on same row as View link
- [x] Status indicators use correct colors (green/red)
- [x] Icons display correctly (CheckCircle/AlertCircle)

---

## User Requirements Addressed

1. ✅ "i want to implement a new box that add in product dtail page and tell that is the product is active or inactive base on product scrape_fail_count if it >= 3 the product is inactive"
2. ✅ "just say inactive product" (simplified message, no detailed count)
3. ✅ "if the retailer that verify correct is not in active , it will show inactive too"
4. ✅ "can you show flag \active too" (show both active and inactive)
5. ✅ "can the active/inactive flag for another retail show at the bottom left in same row of the correct, undo incrrect button"
6. ✅ "can the text Updated: 11 hours ago set it to same row as View on Thai Watsadu, make it on the right"

---

## Commit Information

**Commit Hash**: f2184df
**Branch**: sit
**Commit Message**:
```
Add active/inactive product status indicators

- Backend: Add scrape_fail_count to product detail API response
- Backend: Include scrape_fail_count for matched products
- Frontend: Add CheckCircle and AlertCircle icons
- Frontend: Display active/inactive status box on Thai Watsadu card
- Frontend: Show active/inactive status for verified correct matches
- Frontend: Position match status on bottom left with verification buttons
- UI: Move Updated timestamp to same row as View link for Thai Watsadu

Products with scrape_fail_count >= 3 show as "Inactive Product" (red)
Products with scrape_fail_count < 3 show as "Active Product" (green)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Technical Decisions

1. **Threshold of 3 Failures**:
   - Matches the price updater logic which skips products with `scrape_fail_count >= 3`
   - Consistent with existing system behavior
   - Documented in `backend/services/price_updater.py`

2. **Conditional Display for Matches**:
   - Only show status for verified correct matches
   - Avoids clutter for unverified or rejected matches
   - Users care most about the status of confirmed matches

3. **Visual Design**:
   - Base product uses full box with background for prominence
   - Matched products use compact text style to save space
   - Same color scheme throughout (green = active, red = inactive)

4. **Layout Optimization**:
   - Combined View link and Updated timestamp on same row
   - Saves vertical space on Thai Watsadu card
   - Better use of horizontal space

---

## Next Steps / Future Enhancements

1. Add bulk "Reset scrape_fail_count" action for inactive products
2. Add filtering options to show only active or inactive products
3. Add notification/alert when products become inactive
4. Add retry button to manually trigger scrape for inactive products
5. Display last successful scrape date for inactive products
6. Add analytics dashboard showing active vs inactive product ratio
