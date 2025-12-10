# Chore: Adjust Products Page Price Comparison Table UI

## Metadata
adw_id: `9eadd15a`
prompt: `Adjust the Products page price comparison table UI with the following changes:

  1. COLUMN ORDERING - Reorder table columns to: NO., SKU, PRODUCT NAME, BRAND, CATEGORY, STATUS, then all retailer price
  columns (THAI WATSADU, HOMEPRO, GLOBAL HOUSE, DO HOME, BOONTHAVORN). Move STATUS column to be before the price columns for
  better visual flow.

  2. PRICE COLOR CODING - Apply dynamic color styling to each individual price cell based on comparison logic:
     - GREEN (#10B981 or text-green-600): The cell with the LOWEST/CHEAPEST price among all retailers for that product row
     - GRAY (#6B7280 or text-gray-500): Prices that are the SAME or within 1-2% of the cheapest price (similar/matching
  prices)
     - RED (#EF4444 or text-red-600): Prices that are HIGHER than the cheapest price (not matching the minimum)

  3. Each price cell should be individually colored based on whether that specific retailer's price is the cheapest, same, or
   higher compared to other retailers in the same row. Remove the current uniform teal color.

  4. Keep the external link icons on prices but apply the dynamic color to both the price text and icon.

  5. The STATUS badge column should remain as-is (Cheapest=green, Same=gray, Higher=yellow/orange badges) but reflect the
  overall product status.`

## Chore Description

Enhance the price comparison table UI by reordering columns for better information hierarchy and implementing dynamic color-coded pricing cells based on price comparison logic. The table currently shows columns in a different order with uniform teal coloring for all prices. This chore will:

1. **Reorder table columns** to prioritize product information (NO., SKU, PRODUCT NAME, BRAND, CATEGORY) followed by STATUS badge, then all retailer price columns
2. **Implement dynamic cell-level color coding** where each individual price cell gets colored based on its competitive position (cheapest=green, similar=gray, higher=red)
3. **Replace current uniform teal color** (text-cyan-500) with the new dynamic color system that provides immediate visual feedback on price competitiveness
4. **Maintain external link functionality** while applying the new color scheme to both price text and ExternalLink icons

## Relevant Files

Use these files to complete the chore:

- `components/products/PriceComparisonTable.tsx` - Main table component containing the header row definition. Need to reorder the `<th>` elements to match the new column order: NO., SKU, PRODUCT NAME, BRAND, CATEGORY, STATUS, then price columns.

- `components/products/PriceComparisonRow.tsx` - Row component that renders individual product data. Need to reorder the `<td>` elements to match the new header order, pass comparison logic props to PriceCell components, and ensure proper data flow for color determination.

- `components/products/PriceCell.tsx` - Individual price cell component that displays formatted price with optional external link. Need to update color logic from simple `isLowest`/`isHighest` boolean flags to a three-state system (cheapest/same/higher) and remove the hardcoded teal color (text-cyan-500).

- `lib/utils/price-utils.ts` - Utility functions for price calculations. May need to add a new helper function to determine price comparison category (cheapest/same/higher) based on the 1-2% threshold logic. This centralizes the color determination logic.

### New Files

None required - all changes are modifications to existing components.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Price Comparison Helper Function
- Open `lib/utils/price-utils.ts`
- Add a new type definition: `export type PriceComparisonCategory = 'cheapest' | 'same' | 'higher';`
- Create a new function `getPriceComparisonCategory` that takes a price and an array of all valid prices for that row
- Function should return 'cheapest' if price equals the minimum, 'same' if within 1-2% of minimum, 'higher' otherwise
- This centralizes the comparison logic and makes it reusable across components

### 2. Update PriceCell Component Color Logic
- Open `components/products/PriceCell.tsx`
- Update the `PriceCellProps` interface to accept a new prop: `comparisonCategory?: 'cheapest' | 'same' | 'higher'`
- Remove or deprecate the current `isLowest` and `isHighest` props (keep for backward compatibility if needed)
- Update the `colorClass` variable logic to use the new three-state system:
  - 'cheapest' → `'text-green-600 font-semibold'` (green for lowest price)
  - 'same' → `'text-gray-500'` (gray for prices within 1-2% threshold)
  - 'higher' → `'text-red-600'` (red for prices above the threshold)
  - Remove the hardcoded `'text-cyan-500'` fallback
- Ensure the ExternalLink icon inherits the same color class from its parent
- Test that null prices still render as gray dashes

### 3. Update PriceComparisonRow Component
- Open `components/products/PriceComparisonRow.tsx`
- Extract all valid prices from the product for comparison using `Object.values(product.prices).map(p => p.price).filter(p => p !== null && p > 0)`
- Find the minimum price in the row for comparison baseline
- Reorder the `<td>` elements to match the new column order:
  1. NO. (rowNumber) - already first
  2. SKU (product.sku)
  3. PRODUCT NAME (product.nameTh || product.name)
  4. BRAND (product.brand)
  5. CATEGORY (product.categoryTh || product.category)
  6. STATUS (StatusBadge component)
  7. THAI WATSADU price (PriceCell)
  8. HOMEPRO price (PriceCell)
  9. GLOBAL HOUSE price (PriceCell)
  10. DO HOME price (PriceCell)
  11. BOONTHAVORN price (PriceCell)
- For each PriceCell, calculate and pass the `comparisonCategory` prop using the helper function from step 1
- Ensure the STATUS column still displays the overall product status badge correctly

### 4. Update PriceComparisonTable Component Header
- Open `components/products/PriceComparisonTable.tsx`
- Reorder the `<th>` header elements in the `<thead>` section to match the new column order:
  1. NO.
  2. SKU
  3. PRODUCT NAME (change from "Product Name")
  4. BRAND
  5. CATEGORY
  6. STATUS
  7. THAI WATSADU (change from "Thai Watsadu" to uppercase)
  8. HOMEPRO (change from "HomePro")
  9. GLOBAL HOUSE (change from "Global House" to uppercase)
  10. DO HOME (change from "Do Home" to uppercase)
  11. BOONTHAVORN (change from "Boonthavorn" to uppercase)
- Verify that all header text maintains consistent uppercase styling
- Ensure the column alignment and spacing remains consistent

### 5. Test and Validate Changes
- Start the development server: `npm run dev`
- Navigate to http://localhost:3000/products
- Verify column order matches specification: NO., SKU, PRODUCT NAME, BRAND, CATEGORY, STATUS, then all price columns
- Verify price color coding works correctly:
  - Lowest price in each row is GREEN
  - Prices within 1-2% of lowest are GRAY
  - Prices above threshold are RED
  - No teal colors remain
- Test external links still work and icons have matching colors
- Verify STATUS badges remain unchanged (overall product status)
- Check responsive behavior and table scrolling
- Test with various products to ensure logic works across different price scenarios

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check for TypeScript errors
npm run type-check

# Lint the code for any issues
npm run lint

# Build the application to ensure no build errors
npm run build

# Start development server and visually inspect the table
npm run dev
# Open http://localhost:3000/products and verify:
# 1. Column order: NO., SKU, PRODUCT NAME, BRAND, CATEGORY, STATUS, then prices
# 2. Price colors: Green (lowest), Gray (similar), Red (higher)
# 3. No teal/cyan colors remain in price cells
# 4. External links work with matching icon colors
# 5. STATUS badges remain unchanged
```

## Notes

- The STATUS column badge represents the overall Thai Watsadu competitive position (based on the `product.status` field calculated by backend/utility logic), while individual price cell colors show cell-by-cell comparison
- The 1-2% threshold should match the existing threshold in `calculateStatus` function (currently set at 2%)
- Maintain backward compatibility by keeping the table responsive and ensuring overflow-x scrolling works
- The color changes should be subtle enough to maintain readability while providing clear visual hierarchy
- Consider accessibility: ensure color contrast ratios meet WCAG AA standards (green #10B981, gray #6B7280, red #EF4444 all have good contrast on white backgrounds)
