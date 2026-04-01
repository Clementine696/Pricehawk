# Export Enhancements and Price History UI Improvements

**Date**: 2026-02-02
**Branch**: sit
**Status**: ✅ Completed

## Overview

This session focused on enhancing the export functionality and implementing comprehensive price history visualization improvements. Major work included adding watchlist columns to exports, restoring and redesigning the price history chart, implementing custom date ranges, and fixing UI layout issues.

---

## 1. Export Enhancements

### 1.1 Add S-dept Column to All Exports

**Files Modified**:
- `backend/main.py` (lines 753-1005, 1560-1890)

**Changes**:
- Added "S-dept" column to both product export and watchlist export endpoints
- Column displays watchlist_sku_groups.name value
- Shows empty string for products not in any watchlist
- Only applies to TWD (Thai Watsadu) base products

**Query Enhancement**:
```sql
SELECT p.product_id, p.sku, p.name, p.brand, p.category, p.current_price, p.link,
       wg.name as watchlist_name
FROM products p
LEFT JOIN watchlist_sku_group_products wsgp ON p.sku = wsgp.sku AND p.retailer_id = 'twd'
LEFT JOIN watchlist_sku_groups wg ON wsgp.group_id = wg.group_id
WHERE p.retailer_id = %s
```

**Excel Column Layout**:
1. Product Name
2. SKU
3. Brand
4. Category
5. **S-dept** (NEW)
6. Thai Watsadu (฿)
7-11. Retailer Prices
12. Status

**Affected Endpoints**:
- `/api/products/export`
- `/api/watchlist/sku-groups/{group_id}/export`

---

### 1.2 Fixed Retailer Columns in Price History Export

**Files Modified**:
- `backend/main.py` (lines 2039-2090)

**Changes**:
- All retailers now appear as fixed columns in exports
- Empty cells for retailers with no match or no data
- Consistent column structure across all exports

**Fixed Retailer Order**:
```python
all_retailers = ['HomePro', 'MegaHome', 'Do Home', 'Boonthavorn', 'Global House']
```

**Export Format**:
| Timestamp | SKU | Product Name | Brand | Sub-Dept | Thai Watsadu | HomePro | MegaHome | Do Home | Boonthavorn | Global House |
|-----------|-----|--------------|-------|----------|--------------|---------|----------|---------|-------------|--------------|
| 2026-02-01 | ... | ... | ... | Paint | 1,130 | 1,190 | 1,190 | | | |

---

## 2. Price History Chart Implementation

### 2.1 Restore Price History Feature

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 8-20, 53-68, 196-234, 891-1110)

**Restored Components**:
1. **Imports**:
   - Recharts library (LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer)
   - TrendingUp, TrendingDown, Download, Calendar icons

2. **TypeScript Interfaces**:
   ```typescript
   interface PriceHistoryPoint {
     price: number;
     date: string;
   }

   interface PriceHistoryProduct {
     product_id: number;
     name: string;
     retailer: string;
     history: PriceHistoryPoint[];
   }

   interface PriceHistoryData {
     base_product: PriceHistoryProduct;
     matched_products: PriceHistoryProduct[];
   }
   ```

3. **State Variables**:
   ```typescript
   const [priceHistory, setPriceHistory] = useState<PriceHistoryData | null>(null);
   const [historyDays, setHistoryDays] = useState<number>(30);
   const [isLoadingHistory, setIsLoadingHistory] = useState(false);
   ```

4. **API Integration**:
   - `fetchPriceHistory()` function to fetch data from backend
   - useEffect hook to refetch on days change

---

### 2.2 Enhanced Time Range Selection

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 896-975)

**Time Range Options**:
- 1 Day
- 1 Week
- 1 Month
- 3 Months
- 6 Months
- 1 Year
- **Custom** (NEW)

**Button Styling**:
```typescript
className={`px-3 h-8 text-sm rounded-md font-medium transition-colors ${
  historyDays === days && !showCustomRange
    ? 'bg-cyan-500 text-white hover:bg-cyan-600'
    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
}`}
```

---

### 2.3 Custom Date Range Picker

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 977-1015)

**Features**:
- Start date and end date pickers with calendar icons
- Hidden HTML date inputs that open native picker
- Calculates day difference and updates historyDays
- Apply button (disabled until both dates selected)
- Styled with gray background matching design

**State Variables**:
```typescript
const [showCustomRange, setShowCustomRange] = useState(false);
const [customStartDate, setCustomStartDate] = useState<string>('');
const [customEndDate, setCustomEndDate] = useState<string>('');
```

**Date Calculation**:
```typescript
const start = new Date(customStartDate);
const end = new Date(customEndDate);
const diffTime = Math.abs(end.getTime() - start.getTime());
const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
setHistoryDays(diffDays);
```

---

### 2.4 Lowest/Highest Price Statistics Cards

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 1020-1090)

**Features**:
- Two stat cards showing price extremes
- Green card for lowest price with TrendingDown icon
- Red card for highest price with TrendingUp icon
- Displays retailer name and date
- Automatically calculates from all price history data

**Card Structure**:
```tsx
<div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
  <div className="p-2 bg-green-100 rounded-full">
    <TrendingDown className="h-5 w-5 text-green-600" />
  </div>
  <div>
    <p className="text-sm text-gray-600">Lowest Price</p>
    <p className="text-xl font-bold text-green-600">฿1,323</p>
    <p className="text-xs text-gray-500">Thai Watsadu • Feb 1</p>
  </div>
</div>
```

---

### 2.5 Chart Styling and Colors

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 1070-1100)

**Retailer Color Mapping**:
```typescript
const retailerColors: Record<string, string> = {
  'HomePro': '#3b82f6',      // Blue
  'Home Pro': '#3b82f6',
  'MegaHome': '#10b981',      // Green
  'Mega Home': '#10b981',
  'Boonthavorn': '#9333ea',   // Purple
  'Global House': '#f97316',  // Orange
  'GlobalHouse': '#f97316',
  'Do Home': '#ef4444',       // Red
  'DoHome': '#ef4444',
};
```

**Thai Watsadu (Base)**:
- Color: `#06b6d4` (Cyan)
- Stroke Width: 3px (thicker than others)

**Chart Components**:
- CartesianGrid with dashed lines
- XAxis with date formatting
- YAxis with Thai Baht symbol (฿)
- Custom Legend with retailer name chips
- Responsive container with 350px height

---

### 2.6 Export Price History to Excel

**Backend Endpoint**:
- `GET /api/products/{product_id}/price-history/export`

**Files Modified**:
- `backend/main.py` (lines 1973-2091)
- `ui/src/app/products/[id]/page.tsx` (lines 260-288, 976-983)

**Export Features**:
- Proper Excel format using openpyxl
- Includes product metadata (Timestamp, SKU, Product Name, Brand, Sub-Dept)
- Fixed columns for all retailers
- Filename: `price_history_export_YYYYMMDD_HHMMSS.xlsx`

**Frontend Export Function**:
```typescript
const exportPriceHistory = async () => {
  if (!productId) return;

  try {
    const response = await apiFetch(
      `/api/products/${productId}/price-history/export?days=${historyDays}`
    );
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `price_history_export_${timestamp}.xlsx`;
    link.click();
  } catch (error) {
    console.error('Error exporting price history:', error);
  }
};
```

---

### 2.7 Consistent Data Points Across Products

**Problem**:
- Products had price data on different dates
- Some showed 2 points, others showed 3+
- Made chart inconsistent and confusing

**Solution**:
- Changed from record-based limits to date-based queries
- All products now fetch from same date range
- Extended range for small periods to ensure multiple data points

**Backend Implementation**:
```python
# For small ranges, extend by 2 days to get more data points
fetch_days = days + 2 if days <= 7 else days

cur.execute("""
    SELECT price, scraped_at
    FROM price_history
    WHERE product_id = %s
      AND scraped_at >= NOW() - INTERVAL '%s days'
    ORDER BY scraped_at ASC
""", (product_id, fetch_days))
```

**Date Range Mapping**:
- 1 Day → fetches last 3 days of data
- 7 Days → fetches last 9 days of data
- Longer ranges use original day count

**Result**:
- All products show data from the same date range
- Products may have different number of points (based on scrape frequency)
- But all share the same X-axis timeline

---

## 3. UI Layout Fixes

### 3.1 Thai Watsadu Card Stretch Layout

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 600-709)

**Problem**:
- Thai Watsadu (left) card was shorter than retailer cards (right)
- Left white space at the bottom

**Solution**:
- Wrapped header and content in single container with shadow/rounded corners
- Applied flexbox to stretch card vertically
- Added spacer div to push "Updated" timestamp to appropriate position

**Layout Structure**:
```tsx
<div className="flex flex-col self-stretch">
  <div className="bg-white rounded-lg shadow overflow-hidden flex-1 flex flex-col">
    {/* Header */}
    <div className="bg-cyan-600 text-white px-4 py-3 flex items-center gap-2 flex-shrink-0">
      {/* Header content */}
    </div>

    {/* Product Card Content */}
    <div className="p-6 flex-1 flex flex-col">
      {/* Product details */}

      {/* Spacer to push content if needed */}
      <div className="flex-1"></div>
    </div>
  </div>
</div>
```

**Result**:
- Card stretches to match right side height when right is taller
- Card stays natural height when content is taller than right side
- No more cyan header overflow glitch

---

### 3.2 Updated Timestamp Repositioning

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 693-697)

**Change**:
- Moved "Updated: X hours ago" from bottom of card
- Now positioned directly under "View on Thai Watsadu" link
- Small top margin (mt-2) for spacing

**New Position**:
```tsx
{product.link && (
  <a href={product.link} ...>
    <ExternalLink className="w-4 h-4" />
    View on {product.retailer_name}
  </a>
)}

{/* Updated timestamp */}
<div className="mt-2 text-sm text-gray-500">
  Updated: {formatLastUpdated(product.last_updated_at)}
</div>
```

---

## 4. Data Point Counter

**Files Modified**:
- `ui/src/app/products/[id]/page.tsx` (lines 1097-1105)

**Feature**:
- Shows total unique dates in the dataset
- Displayed at bottom of chart
- Format: "Showing N data points"

**Implementation**:
```tsx
<div className="flex items-center">
  <h4 className="font-medium text-sm text-gray-500">
    Showing {(() => {
      const allDates = new Set<string>();
      priceHistory.base_product.history.forEach(h =>
        allDates.add(h.date.split('T')[0])
      );
      priceHistory.matched_products.forEach(p =>
        p.history.forEach(h => allDates.add(h.date.split('T')[0]))
      );
      return allDates.size;
    })()} data points
  </h4>
</div>
```

---

## Summary of Files Modified

### Backend
1. **backend/main.py**
   - Added S-dept column to product exports (watchlist export: ~line 753, products export: ~line 1560)
   - Fixed retailer columns in price history export (~line 2039)
   - Implemented price history export endpoint (~line 1973)
   - Updated price history query logic for consistent data points (~line 1907, 1964, 2000, 2039)

### Frontend
2. **ui/src/app/products/[id]/page.tsx**
   - Restored price history chart with all imports and state (~line 8-234)
   - Added enhanced time range buttons with custom range picker (~line 896-1015)
   - Implemented lowest/highest price stat cards (~line 1020-1090)
   - Added retailer color mapping for chart lines (~line 1070-1100)
   - Implemented Excel export functionality (~line 260-288, 976-983)
   - Fixed Thai Watsadu card layout (~line 600-709)
   - Repositioned updated timestamp (~line 693-697)
   - Added data point counter (~line 1097-1105)

---

## Testing Checklist

- [x] S-dept column appears in product exports
- [x] S-dept column appears in watchlist exports
- [x] S-dept shows watchlist name for TWD products
- [x] S-dept shows empty string for products not in watchlist
- [x] Price history chart displays correctly
- [x] Time range buttons work (1 Day, 1 Week, etc.)
- [x] Custom date range picker opens and calculates correctly
- [x] Lowest/Highest price cards show correct data
- [x] Chart lines match retailer brand colors
- [x] Excel export downloads with correct format
- [x] All products show data from same date range
- [x] Thai Watsadu card stretches to match right side height
- [x] Updated timestamp appears under "View on" link
- [x] Data point counter shows correct number

---

## Key Technical Decisions

1. **Date-based vs Record-based Queries**
   - Initially tried LIMIT-based approach to ensure N data points
   - Switched to date-based with extended range for consistency
   - Ensures all products share same timeline on chart

2. **Fixed vs Dynamic Retailer Columns**
   - Chose fixed column order for exports
   - Makes Excel files consistent and easier to analyze
   - Empty cells for missing retailers

3. **Flexbox Layout for Card Stretch**
   - Used flex-1 and self-stretch to match heights
   - Single container approach to avoid header overflow
   - Spacer div for flexible content positioning

4. **Custom Date Range Implementation**
   - Hidden native date inputs for better UX
   - Calculates day difference instead of passing dates to backend
   - Reuses existing historyDays parameter

---

## User Feedback Addressed

1. ✅ "Add column watchlist sku... column name in excel make it name 'S-dept'"
2. ✅ "Export all the retail as fix column, if it dont exist just be empty space"
3. ✅ "Last time, i told you to comment off the price history can you open it back"
4. ✅ "Can you use the graph line color like the color of retail above"
5. ✅ "Add custom range" with date pickers
6. ✅ "On 1 day just show 2 data node left to right" → Fixed to show consistent date range
7. ✅ "The top color of thaiwatsadu is glitch" → Fixed overflow issue
8. ✅ "Move the Updated: 11 hours ago to stick to the top" → Positioned under View link

---

## Commit Information

**Commit Hash**: 5af9dc4
**Branch**: sit
**Commit Message**:
```
Add S-dept column to exports, implement price history UI improvements

- Export: Add S-dept (watchlist) column to products and watchlist exports
- Export: Fix all retailers as fixed columns in price history export
- Price History: Restore price history chart with enhanced UI
- Price History: Add custom date range picker with date selectors
- Price History: Implement Excel export with proper format
- Price History: Add lowest/highest price stat cards
- Price History: Fix chart to show consistent data points across products
- Price History: Match retailer line colors to brand colors
- UI: Fix Thai Watsadu card layout to stretch with right side
- UI: Move updated timestamp below "View on" link

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Next Steps / Future Enhancements

1. Consider adding price change indicators (% change)
2. Add ability to compare multiple products on same chart
3. Implement chart zoom/pan for longer time ranges
4. Add annotations for significant price changes
5. Consider adding price alerts/notifications
6. Add chart download as image option
