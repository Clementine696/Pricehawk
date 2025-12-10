# Chore: Manual Comparison Button for All-Incorrect Products

## Metadata
adw_id: `c193c1dd`
prompt: `Implement a 'Manual Comparison' button that appears when all matched products for a product row are marked as 'incorrect'.`

## Chore Description
When all matched products from retailers (HOMEPRO, GLOBAL_HOUSE, DOHOME, BOONTHAVORN) for a specific product row are marked as 'incorrect' via validation statuses stored in localStorage, display a 'Manual Comparison' button. This button navigates users to the /comparison page with the product's SKU and ID pre-filled, allowing them to manually find and compare the correct product.

**Key Context:**
- PriceComparisonTable.tsx displays product rows with prices from 5 retailers
- Validation statuses stored in localStorage via `lib/utils/validation-storage.ts` with pattern `pricehawk_validation_{productId}`
- Matched product IDs follow format: `${retailer.toLowerCase()}_${product.sku}`
- ValidationStatus type: 'pending' | 'correct' | 'incorrect'
- Current implementation already hides prices marked as 'incorrect' (see PriceComparisonRow.tsx:32-38)

## Relevant Files

### Existing Files to Modify

**components/products/PriceComparisonRow.tsx**
- Primary component to modify
- Already has `isRetailerPriceHidden()` helper to check validation statuses
- Currently displays price cells for all retailers
- Needs logic to detect when ALL competitor retailers are marked 'incorrect'
- Should render Manual Comparison button in this case

**lib/utils/validation-storage.ts**
- Contains validation status storage functions
- `getAllValidationStatuses(productId)` retrieves all statuses for a product
- Already implements the storage pattern we need

**lib/types/price-comparison.ts**
- Contains TypeScript type definitions
- Retailer enum defines all 5 retailers
- ValidationStatus type already defined

### New Files

**components/products/ManualComparisonButton.tsx**
- New reusable button component
- Accepts productId and sku as props
- Navigates to /comparison page with query parameters
- Styled consistently with ExportButton.tsx (cyan theme, Tailwind CSS)

### Reference Files

**components/products/ExportButton.tsx**
- Reference for button styling patterns
- Uses cyan-500/600 color scheme with hover effects
- Lucide icons for UI consistency

**app/(main)/comparison/page.tsx**
- Manual comparison page
- Currently accepts manual input for Thai Watsadu SKU and URL
- Needs to support pre-filling from query parameters (sku, productId)

**components/products/PriceCell.tsx**
- Reference for understanding price display logic
- Shows how prices are hidden when validation status is 'incorrect'

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Helper Function for All-Incorrect Detection
- Add `areAllCompetitorMatchesIncorrect()` function in PriceComparisonRow.tsx
- Function signature: `(productId: string, retailers: Retailer[], validationStatuses: Record<string, Record<string, ValidationStatus>> | undefined) => boolean`
- Check all competitor retailers (exclude THAI_WATSADU as it's the reference)
- Return true only if ALL competitor retailers have matched products marked as 'incorrect'
- Handle edge cases: undefined validationStatuses, missing product entries

### 2. Create ManualComparisonButton Component
- Create new file: `components/products/ManualComparisonButton.tsx`
- Accept props: `productId: string`, `sku: string`
- Use Next.js `useRouter` for navigation
- Navigate to `/comparison?sku={sku}&productId={productId}` on click
- Style with Tailwind CSS matching ExportButton pattern:
  - cyan-500 background with cyan-600 hover
  - Rounded corners, shadow effects
  - Include Lucide icon (e.g., Search, Edit, or ExternalLink)
- Add 'use client' directive for client-side navigation
- Export as named export for consistency

### 3. Integrate Manual Comparison Button in PriceComparisonRow
- Import ManualComparisonButton component
- After existing row logic, check if all competitor matches are incorrect
- When true, render a special table cell that spans all retailer columns (use colspan)
- Display ManualComparisonButton centered in this cell
- Keep existing product info cells (NO., SKU, NAME, BRAND, CATEGORY, STATUS, THAI WATSADU) visible
- Replace only the competitor price cells (HOMEPRO through BOONTHAVORN) with the button

### 4. Update Comparison Page to Handle Query Parameters
- Modify `app/(main)/comparison/page.tsx`
- Import `useSearchParams` from 'next/navigation'
- On component mount, check for `sku` and `productId` query parameters
- If present, pre-fill the `thaiWatsuduInput.sku` field with the SKU value
- Optionally store productId for later use (could be used to link back or store results)
- Ensure the form flow works normally after pre-filling

### 5. Update TypeScript Types if Needed
- Review if any new types are needed in `lib/types/price-comparison.ts`
- Ensure all props and return types are properly typed
- Add JSDoc comments for new functions

### 6. Test All-Incorrect Detection Logic
- Manually test with different validation status combinations:
  - All competitors marked 'incorrect' → Button should appear
  - Mix of 'incorrect' and 'correct' → Button should NOT appear
  - No validation statuses set → Button should NOT appear
  - Only some retailers marked 'incorrect' → Button should NOT appear
- Verify THAI_WATSADU is excluded from the check (it's the reference retailer)

### 7. Test Navigation and Pre-filling
- Click Manual Comparison button from a product row
- Verify navigation to /comparison page with correct query parameters
- Confirm SKU field is pre-filled correctly
- Test the manual comparison flow end-to-end from pre-filled state
- Verify productId is captured (check browser console/state if needed)

### 8. Visual and UI Testing
- Verify button appears centered and spans correct columns
- Check responsive behavior on mobile/tablet/desktop
- Ensure button styling matches design system (cyan theme)
- Verify row layout doesn't break when button appears
- Test hover/active states on the button

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Build the application
npm run build

# Start dev server for manual testing
npm run dev

# Manual test checklist:
# 1. Open http://localhost:3000/products
# 2. Open browser DevTools > Application > Local Storage
# 3. Manually set validation statuses for a product to all 'incorrect':
#    Key: pricehawk_validation_{productId}
#    Value: {"statuses":{"homepro_{sku}":"incorrect","global_house_{sku}":"incorrect","dohome_{sku}":"incorrect","boonthavorn_{sku}":"incorrect"},"updatedAt":"2025-12-03T10:00:00.000Z"}
# 4. Refresh the page
# 5. Verify Manual Comparison button appears for that product row
# 6. Click the button and verify navigation to /comparison with pre-filled SKU
# 7. Complete manual comparison flow to ensure it works end-to-end
```

## Notes

### Retailer Exclusion Logic
- THAI_WATSADU is the reference retailer and should be excluded from all-incorrect checks
- Only check competitor retailers: HOMEPRO, GLOBAL_HOUSE, DOHOME, BOONTHAVORN

### Edge Cases to Handle
- Product has no validation statuses stored → Don't show button
- Product has partial validation statuses (some retailers missing) → Don't show button
- Product has validation statuses but none are 'incorrect' → Don't show button
- Product has mix of 'pending', 'correct', and 'incorrect' → Don't show button

### UI/UX Considerations
- Button should be prominent but not overwhelming
- Use colspan to span multiple columns for clean layout
- Consider adding a tooltip or helper text explaining the button's purpose
- Icon choice: Search icon (magnifying glass) or Edit icon works well for "manual comparison"

### Future Enhancements (Out of Scope)
- Store comparison results back to the product after manual comparison
- Add "Return to Product" link in comparison page when coming from products page
- Track which products have been manually compared in localStorage
- Add visual indicator on product row that manual comparison was completed

### Related Chores
- This builds on chore-eb6780c1-hide-incorrect-prices.md which implemented price hiding
- May relate to future validation workflow improvements
