# Chore: Enhance Products Page UX/UI Styling

## Metadata
adw_id: `385c5fcc`
prompt: `Enhance Products page UX/UI styling to match design reference while preserving existing functionality: 1) PriceCell.tsx - change price text color from current styling to cyan-500 (teal), ensure external link icon displays next to price, maintain clickable link behavior. 2) StatusBadge.tsx - update badge color scheme: 'cheapest' status should use green background (bg-green-500 text-white), 'higher' status should use amber/orange background (bg-amber-500 text-white), 'same' status should use gray background (bg-gray-200 text-gray-700), ensure pill/rounded-full shape. 3) PriceComparisonTable.tsx - add 'No.' column as first column showing row number (1, 2, 3...), reorder columns to match: No., Category, SKU, Product Name, Brand, Thai Watsadu, HomePro, Global House, Do Home, Boonthavorn, Status. Display dash '-' for null/missing prices. 4) ProductSearchFilter.tsx - style Export button with cyan-500 background and white text with download icon, style Reset button with border and gray text with refresh icon. Keep all existing filter logic, API calls, and data flow unchanged.`

## Chore Description

Update the Products page styling to match the design reference image (`expected/image.png`) while maintaining all existing functionality. This is a pure styling/UI enhancement task that does not change any business logic, API calls, or data flow.

Key changes:
- **PriceCell.tsx**: Change price text color to cyan-500 (teal) to match design
- **StatusBadge.tsx**: Update status badge colors (green for cheapest, amber for higher, gray for same)
- **PriceComparisonTable.tsx**: Table already has correct structure including No. column
- **ProductSearchFilter.tsx**: Style buttons to match design (Export with cyan background, Reset with border)

## Relevant Files

- **components/products/PriceCell.tsx** - Price cell component that displays retailer prices with external links. Currently uses sky-500 (line 30), needs to change to cyan-500.

- **components/products/StatusBadge.tsx** - Status badge component showing price comparison status. Uses utility function `getStatusColor()` from price-utils.ts to determine badge colors.

- **lib/utils/price-utils.ts** - Contains `getStatusColor()` function (lines 129-142) that returns Tailwind color classes for status badges. Currently uses:
  - 'cheapest': bg-green-500 (correct)
  - 'higher': bg-red-500 (needs to change to bg-amber-500)
  - 'same': bg-gray-500 (needs to change to bg-gray-200 with text-gray-700)

- **components/products/PriceComparisonTable.tsx** - Table component with column headers and row rendering. Already has correct column structure including No. column (line 52). No changes needed.

- **components/products/PriceComparisonRow.tsx** - Row component that renders each product. Already displays row number and handles null prices correctly. No changes needed.

- **components/products/ProductSearchFilter.tsx** - Filter component with search, category, brand filters, and action buttons. Export button (lines 101-119) and Reset button (lines 92-98) need styling updates to match design.

## Step by Step Tasks

### 1. Update PriceCell Text Color
- Open `components/products/PriceCell.tsx`
- Change line 30 from `'text-sky-500'` to `'text-cyan-500'`
- Verify external link icon is already displaying (line 41)
- Verify clickable link behavior is preserved (lines 34-43)

### 2. Update StatusBadge Colors
- Open `lib/utils/price-utils.ts`
- In the `getStatusColor()` function (lines 129-142):
  - Line 133: Keep `'bg-green-500 text-white'` for 'cheapest' (already correct)
  - Line 135: Change `'bg-red-500 text-white'` to `'bg-amber-500 text-white'` for 'higher'
  - Line 137: Change `'bg-gray-500 text-white'` to `'bg-gray-200 text-gray-700'` for 'same'
- Verify StatusBadge.tsx already has `rounded-full` class (line 15) for pill shape

### 3. Verify Table Structure (No Changes Needed)
- Verify `components/products/PriceComparisonTable.tsx` already has:
  - No. column as first column (line 51-53)
  - Correct column order: No., Category, SKU, Product Name, Brand, Thai Watsadu, HomePro, Global House, Do Home, Boonthavorn, Status
- Verify `components/products/PriceComparisonRow.tsx` displays row number (line 28)
- Verify `components/products/PriceCell.tsx` displays '-' for null prices (line 23)

### 4. Update Filter Button Styles
- Open `components/products/ProductSearchFilter.tsx`
- Reset button (lines 92-98):
  - Verify it already has correct styling: border, gray text, RotateCcw icon
  - Current implementation already matches design requirements
- Export button (lines 101-119):
  - Verify it already has cyan-500 background (line 103)
  - Verify it already has white text (line 103)
  - Verify it already has download icon (lines 105-117)
  - Current implementation already matches design requirements

### 5. Visual Validation
- Start development server with `npm run dev`
- Navigate to http://localhost:3000/products
- Verify price text colors are cyan-500 (teal)
- Verify status badges show correct colors:
  - Green for "Cheapest"
  - Amber/Orange for "Higher"
  - Gray for "Same"
- Verify table structure matches design with correct column order
- Verify buttons match design (Export: cyan background, Reset: bordered)
- Test all existing functionality still works (search, filter, export, clicking prices)

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check for TypeScript errors
npm run type-check

# Lint code for style issues
npm run lint

# Build to ensure no production issues
npm run build

# Start development server for visual testing
npm run dev
# Then open http://localhost:3000/products in browser
```

## Notes

- This is a pure styling change - no logic, API, or data flow changes
- The table structure (including No. column) is already correct per the code review
- The Export and Reset buttons are already styled correctly per the design
- Main changes are:
  1. PriceCell color: sky-500 → cyan-500
  2. StatusBadge 'higher': red → amber
  3. StatusBadge 'same': gray-500 white text → gray-200 gray-700 text
- All existing functionality (clickable links, external icons, filtering, export) must remain unchanged
