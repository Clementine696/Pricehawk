# Chore: Hide Incorrect Validation Prices on Products List

## Metadata
adw_id: `eb6780c1`
prompt: `Update the Products list page (app/(main)/products/page.tsx) and PriceComparisonTable component to respect validation statuses stored in localStorage. When a matched product is marked as 'incorrect' on the Product Comparison Detail page, the corresponding retailer price should be hidden (show '-' or empty) on the Products list page table. The validation statuses are stored in localStorage with key pattern 'pricehawk_validation_{productId}' and contain a statuses object mapping '{retailer}_{sku}' to ValidationStatus. Add a utility function getAllValidationStatusesForAllProducts() in lib/utils/validation-storage.ts to retrieve all validation statuses across products. In PriceComparisonRow component, check if the retailer price has been marked 'incorrect' and hide it accordingly. The PriceCell component should accept an optional 'hidden' prop to display '-' instead of the price when the matched product was marked incorrect.`

## Chore Description

The Products list page currently displays all retailer prices without respecting user validation decisions made on the Product Comparison Detail page. When a user marks a matched product as "incorrect" on the detail page, that validation status is stored in localStorage but does not affect the display on the Products list page.

This chore implements the following behavior:
1. When a user marks a retailer's matched product as "incorrect" on the Product Detail page, that retailer's price should be hidden on the Products list page
2. Hidden prices should display as "-" instead of the actual price value
3. The PriceCell component needs a new optional `hidden` prop to support this behavior
4. A utility function is needed to efficiently retrieve all validation statuses across all products from localStorage
5. The PriceComparisonRow component needs to check validation statuses and pass the `hidden` prop to PriceCell when appropriate

## Relevant Files

### Existing Files to Modify

- **lib/utils/validation-storage.ts** - Add `getAllValidationStatusesForAllProducts()` function to retrieve all validation statuses from localStorage across all products. Currently has functions for managing validation statuses for a single product, but needs a function to retrieve statuses for all products at once.

- **components/products/PriceCell.tsx** - Add optional `hidden` prop that when true, displays "-" instead of the price. Currently displays price with color coding based on comparison category, needs to support hiding prices.

- **components/products/PriceComparisonRow.tsx** - Check validation statuses for each retailer price and pass `hidden={true}` to PriceCell when the matched product is marked as "incorrect". Currently renders price cells without checking validation status.

- **components/products/PriceComparisonTable.tsx** - Pass validation statuses data to PriceComparisonRow components. May need to accept validation statuses as a prop or have rows fetch them internally.

- **app/(main)/products/page.tsx** - Load all validation statuses from localStorage and pass them down to the PriceComparisonTable component, or implement an alternative data flow pattern.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add utility function to retrieve all validation statuses
- Open `lib/utils/validation-storage.ts`
- Add new function `getAllValidationStatusesForAllProducts()` that:
  - Returns a Record mapping productId to their validation statuses Record
  - Iterates through all localStorage keys matching the pattern `pricehawk_validation_*`
  - Extracts productId from each key
  - Parses the stored data and builds a mapping structure
  - Returns type: `Record<string, Record<string, ValidationStatus>>`
  - Handles errors gracefully and returns empty object on failure

### 2. Add hidden prop to PriceCell component
- Open `components/products/PriceCell.tsx`
- Add optional `hidden?: boolean` prop to PriceCellProps interface
- Modify component logic to check `hidden` prop first
- If `hidden === true`, return `<span className="text-gray-400">-</span>` (same as null price)
- Ensure this check happens before other rendering logic
- Test with existing price display logic to ensure no regressions

### 3. Update PriceComparisonRow to check validation statuses
- Open `components/products/PriceComparisonRow.tsx`
- Add `validationStatuses?: Record<string, Record<string, ValidationStatus>>` to PriceComparisonRowProps
- For each retailer price cell (HOMEPRO, GLOBAL_HOUSE, DOHOME, BOONTHAVORN):
  - Construct the matched product ID: `${retailer}_${product.sku}`
  - Check if `validationStatuses?.[product.id]?.[matchedProductId] === 'incorrect'`
  - Pass `hidden={isIncorrect}` prop to PriceCell component
- Do not modify Thai Watsadu price cell (it's the reference price)
- Ensure the check only applies to non-null prices

### 4. Update PriceComparisonTable to pass validation statuses
- Open `components/products/PriceComparisonTable.tsx`
- Add `validationStatuses?: Record<string, Record<string, ValidationStatus>>` to PriceComparisonTableProps
- Pass `validationStatuses` prop to each PriceComparisonRow component in the map function

### 5. Update Products page to load and pass validation statuses
- Open `app/(main)/products/page.tsx`
- Import `getAllValidationStatusesForAllProducts` from validation-storage utils
- Add state: `const [validationStatuses, setValidationStatuses] = useState<Record<string, Record<string, ValidationStatus>>>({})`
- Add useEffect to load validation statuses on mount:
  - Call `getAllValidationStatusesForAllProducts()`
  - Set the result to state
- Pass `validationStatuses` prop to PriceComparisonTable component

### 6. Test the implementation
- Run `npm run dev` to start development server
- Navigate to Products list page at http://localhost:3000/products
- Verify all prices display normally when no validations exist
- Navigate to a Product Detail page
- Mark a retailer's matched product as "incorrect"
- Navigate back to Products list page
- Verify the retailer's price for that product now shows "-" instead of the price
- Verify other products and retailers are unaffected
- Mark the same matched product as "correct"
- Verify the price reappears on the list page
- Test with multiple products and multiple retailers
- Verify no console errors appear

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check to ensure no TypeScript errors
npm run type-check

# Lint the code to ensure code quality
npm run lint

# Build the application to ensure production build works
npm run build

# Start development server for manual testing
npm run dev
```

### Manual Testing Steps
1. Visit http://localhost:3000/products
2. Click on any product to view details
3. Mark one or more matched products as "incorrect" using the X button
4. Return to the products list
5. Verify the retailer prices for marked products show "-" instead of price values
6. Return to product detail and mark products as "correct" using the checkmark button
7. Return to products list and verify prices reappear
8. Test with multiple products across different pages
9. Verify localStorage persistence by refreshing the page

## Notes

### localStorage Key Pattern
- Validation statuses are stored with key: `pricehawk_validation_{productId}`
- Each entry contains: `{ statuses: { [matchedProductId]: ValidationStatus }, updatedAt: string }`
- Matched product IDs follow pattern: `{retailer}_{sku}` (e.g., "homepro_SKU123")

### Validation Status Values
- `'pending'` - Not yet validated (default)
- `'correct'` - User confirmed the match is correct
- `'incorrect'` - User marked the match as incorrect (should hide price)

### Component Hierarchy
```
ProductsPage (loads validation statuses)
  └─ PriceComparisonTable (receives validation statuses)
      └─ PriceComparisonRow (checks validation per retailer)
          └─ PriceCell (renders "-" when hidden=true)
```

### Performance Considerations
- `getAllValidationStatusesForAllProducts()` reads from localStorage which is synchronous
- Consider memoizing the result to avoid unnecessary re-reads
- The function only needs to run once on page mount
- Consider using a state update pattern that allows for reactive updates when validation changes on the detail page (future enhancement)

### Edge Cases to Handle
- Products with no validation statuses (show prices normally)
- Products with validation for some retailers but not others
- Invalid or corrupted localStorage data
- Products where price is already null (continue showing "-")
- Thai Watsadu prices should never be hidden (it's the reference retailer)
