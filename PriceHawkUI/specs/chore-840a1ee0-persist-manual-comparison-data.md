# Chore: Persist Manual Comparison Data

## Metadata
adw_id: `840a1ee0`
prompt: `When a product is added through the Manual Comparison page, save the manually compared product data so it displays on the Products page (app/(main)/products/page.tsx) in the price comparison table and also on the Product Comparison Detail page (app/(main)/products/[id]/page.tsx). The manually added product should show the same information as other products including SKU, product name, brand, category, status, and prices from different retailers. Ensure the manual comparison results are persisted and integrated with the existing product display logic.`

## Chore Description

Currently, when users complete a manual comparison on the Manual Comparison page (`app/(main)/comparison/page.tsx`), the comparison results are only displayed on that page and are not persisted. The data is stored temporarily in `localStorage` using `validation-storage.ts` but is not integrated into the main product listing and detail views.

This chore will implement a complete data persistence and integration system that:

1. **Captures manual comparison results** from the Manual Comparison page (Apple-style comparison flow)
2. **Transforms comparison data** into the `ProductComparison` format used by the Products page
3. **Persists data** to localStorage with a structure that can be merged with mock data
4. **Integrates persisted data** into the Products list API endpoint
5. **Displays manual entries** in the price comparison table with visual indicators
6. **Shows manual comparison data** on the Product Comparison Detail page
7. **Maintains data consistency** across page navigation and browser sessions

The manually added products should appear in the Products page table showing:
- SKU from Thai Watsadu
- Product name
- Brand and category
- Status badge (cheapest/higher/same) calculated from comparison prices
- Prices from Thai Watsadu and all compared retailers
- Visual indicator (badge) showing it's a manual entry

## Relevant Files

### Existing Files to Modify

- **app/api/products/comparison/route.ts** - Update to merge manual comparison data with mock products. Add logic to read from localStorage-backed storage and combine with existing mock data before returning results.

- **app/api/products/comparison/[id]/route.ts** - Update to support manual comparison product IDs. Handle retrieval of manually added products and format them as `ProductComparisonDetailResponse`.

- **app/(main)/comparison/page.tsx** - Add logic to save comparison results when the Apple-style comparison completes. After successful comparison in `handleConfirmAndCompare`, persist the data using the new storage utility.

- **app/(main)/products/page.tsx** - Already integrated with validation-storage for validation statuses. Will automatically display manual entries once API endpoints are updated.

- **app/(main)/products/[id]/page.tsx** - Already has manual comparison data display logic (lines 406-424) but currently only reads from validation-storage. Will work once storage utilities are updated.

- **lib/utils/validation-storage.ts** - Extend to handle full product comparison data, not just validation statuses. Add functions for:
  - `saveManualComparisonProduct()` - Save complete product comparison
  - `getAllManualComparisonProducts()` - Retrieve all manual entries
  - `getManualComparisonProduct(id)` - Retrieve specific manual entry
  - Transform functions between `ComparisonTableData` and `ProductComparison`

- **components/products/PriceComparisonTable.tsx** - Add visual indicator for manually added products (e.g., badge showing "Manual Entry")

- **components/products/PriceComparisonRow.tsx** - Update to display manual entry badge and handle manual product data structure

### New Files

#### New File: `lib/utils/manual-comparison-storage.ts`
A dedicated storage utility module for managing manual comparison products:
- Functions to save/retrieve/delete manual comparison products
- Transform `ComparisonTableData` from manual comparison API to `ProductComparison` format
- Generate unique IDs for manual entries (prefix: `manual_`)
- Calculate price status based on comparison data
- Merge manual products with mock data

## Step by Step Tasks

### 1. Create Manual Comparison Storage Utility
- Create `lib/utils/manual-comparison-storage.ts`
- Implement storage key constants for manual products (e.g., `pricehawk_manual_products`)
- Add `ManualProductEntry` interface matching `ProductComparison` structure
- Implement `saveManualComparisonProduct(data: ComparisonTableData): string` - Returns generated product ID
- Implement `getAllManualComparisonProducts(): ProductComparison[]` - Returns array of manual products
- Implement `getManualComparisonProductById(id: string): ProductComparison | null`
- Implement `deleteManualComparisonProduct(id: string): void`
- Implement `transformComparisonToProduct(data: ComparisonTableData): ProductComparison` - Converts Apple-style comparison data to ProductComparison format
- Add helper to calculate price status (cheapest/higher/same) from prices
- Add helper to generate unique manual product ID (e.g., `manual_${timestamp}_${sku}`)

### 2. Update Manual Comparison Page to Persist Data
- In `app/(main)/comparison/page.tsx`, import new storage utility
- In `handleConfirmAndCompare` function (after line 241), after successful comparison and before showing success toast:
  - Call `saveManualComparisonProduct(comparisonData)` with the `ComparisonTableData` response
  - Store returned product ID in state or show in success message
- Update success toast message to indicate data has been saved (e.g., "Comparison saved! View in Products page")
- Consider adding a "View in Products" button after successful comparison

### 3. Update Products List API to Include Manual Data
- In `app/api/products/comparison/route.ts`:
  - This is a server-side API route, so it cannot directly access localStorage
  - Add a URL parameter to accept manual product data from client (e.g., `manualProducts` as JSON)
  - OR keep existing approach: Client-side merges data before display
- Actually, since this is server API and localStorage is client-only, we need client-side approach:
  - The Products page will need to merge data on the client side after fetching from API

### 4. Update Products Page to Merge Manual Data
- In `app/(main)/products/page.tsx`:
  - Import `getAllManualComparisonProducts` from manual-comparison-storage
  - After fetching products from API (line 59), merge with manual products:
    - Call `getAllManualComparisonProducts()`
    - Combine API products with manual products
    - Apply filters and sorting to combined dataset
  - Update the data state to include manual entries
  - Ensure pagination works correctly with merged data

### 5. Update Product Detail API to Support Manual Products
- In `app/api/products/comparison/[id]/route.ts`:
  - Check if the requested ID starts with `manual_` prefix
  - If manual ID: Return response indicating data should come from localStorage
  - Add a special response field like `isManual: true` to signal client-side handling

### 6. Update Product Detail Page for Manual Products
- In `app/(main)/products/[id]/page.tsx`:
  - Before or after API fetch (line 124), check if productId starts with `manual_`
  - If manual product:
    - Load from `getManualComparisonProductById(productId)`
    - Transform to `ProductComparisonDetailResponse` format
    - Set data state with manual product data
  - Update manual comparison data display section (lines 406-424) to show richer data

### 7. Add Visual Indicators for Manual Entries
- In `components/products/PriceComparisonTable.tsx`:
  - Add a new column or badge to indicate "Manual Entry"
  - Use distinct styling (e.g., purple badge, special icon)
- In `components/products/PriceComparisonRow.tsx`:
  - Check if product ID starts with `manual_`
  - Render manual entry badge next to SKU or product name
  - Style: Small badge with text "Manual" or icon

### 8. Add Data Management Functions
- In manual-comparison-storage.ts:
  - Add `clearAllManualProducts()` - For testing/reset
  - Add `updateManualProduct(id: string, updates: Partial<ProductComparison>)` - For future edits
  - Add export function to export manual products to CSV/JSON

### 9. Test Data Flow End-to-End
- Start dev server (`npm run dev`)
- Navigate to Manual Comparison page (`/comparison`)
- Complete a manual comparison with Thai Watsadu SKU and competitor URLs
- Verify success message shows "saved"
- Navigate to Products page (`/products`)
- Verify manual product appears in table with all details
- Verify manual entry badge is visible
- Click on manual product row
- Navigate to Product Detail page
- Verify all comparison data displays correctly
- Refresh browser
- Verify manual product persists across page reloads

### 10. Handle Edge Cases and Validation
- Test with duplicate SKUs (manual vs mock data) - Should merge or show both
- Test with invalid/missing data fields
- Test localStorage quota limits (handle gracefully)
- Test with empty comparison results
- Add error handling for JSON parse failures
- Add TypeScript strict type checking

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check - ensure no TypeScript errors
npm run type-check

# Lint - ensure code quality
npm run lint

# Build - ensure production build works
npm run build

# Run dev server for manual testing
npm run dev
```

### Manual Testing Steps

1. **Create Manual Comparison**:
   ```
   - Navigate to http://localhost:3000/comparison
   - Enter Thai Watsadu SKU: "TEST123"
   - Enter Thai Watsadu URL
   - Add at least 2 competitors with URLs
   - Click through to Results stage
   - Verify success message includes "saved"
   ```

2. **Verify Products Page**:
   ```
   - Navigate to http://localhost:3000/products
   - Search for "TEST123" or scroll to find manual entry
   - Verify product appears with:
     - Correct SKU, name, brand, category
     - Prices from Thai Watsadu and competitors
     - Status badge (cheapest/higher/same)
     - "Manual Entry" badge or indicator
   ```

3. **Verify Product Detail Page**:
   ```
   - Click on the manual product in the table
   - Verify URL contains manual product ID (starts with "manual_")
   - Verify all product details display correctly
   - Verify competitor prices appear in matched products section
   ```

4. **Test Persistence**:
   ```
   - Refresh the browser
   - Navigate back to /products
   - Verify manual product still appears
   - Open browser DevTools > Application > Local Storage
   - Verify key exists: pricehawk_manual_products
   - Verify data structure is valid JSON
   ```

5. **Test Filtering and Sorting**:
   ```
   - On Products page, apply filters (brand, category, status)
   - Verify manual products filter correctly
   - Sort by different columns
   - Verify manual products sort correctly alongside mock data
   ```

## Notes

- **Storage Limitations**: localStorage has a 5-10MB limit. Consider implementing storage quota warnings if approaching limits. For production, this should be replaced with a backend database.

- **Data Format Compatibility**: The `ComparisonTableData` format from manual comparison API must be carefully transformed to match the `ProductComparison` format expected by the Products page. Pay special attention to:
  - Retailer name format differences (`THAI_WATSADU` vs `thai_watsadu`)
  - Price object structure (`prices[retailer]` object with `price`, `productUrl`, etc.)
  - Status calculation logic (needs to match existing price-utils.ts logic)

- **ID Generation**: Manual product IDs should use a consistent format like `manual_${timestamp}_${sku}` to:
  - Avoid conflicts with mock data IDs
  - Be easily identifiable as manual entries
  - Maintain uniqueness across multiple manual comparisons of the same SKU

- **Merge Strategy**: When merging manual products with mock data:
  - Manual products should appear first (for visibility)
  - OR group manual products separately with a divider
  - OR allow filtering to show only manual/only mock products

- **Future Enhancements**:
  - Add edit/delete functionality for manual products
  - Add import/export for manual comparison data
  - Add validation to prevent duplicate manual entries
  - Sync with backend API when available
  - Add manual entry history/audit log

- **Type Safety**: Ensure all transform functions maintain type safety. Use TypeScript's type guards and assertions where needed.

- **Error Handling**: Gracefully handle scenarios like:
  - localStorage unavailable (private browsing)
  - Corrupted data in localStorage
  - Missing required fields in comparison data
  - API errors when fetching initial product list
