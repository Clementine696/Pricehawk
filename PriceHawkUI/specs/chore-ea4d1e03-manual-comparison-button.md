# Chore: Replace Inline ManualComparisonForm with Manual Comparison Button

## Metadata
adw_id: `ea4d1e03`
prompt: `Modify Product Comparison Detail page to show a 'Manual Comparison' button instead of inline ManualComparisonForm when all matched products are marked as incorrect.`

## Chore Description
Currently, when all matched products on the Product Comparison Detail page (`/products/[id]`) are marked as "incorrect", the page renders an inline `<ManualComparisonForm />` component directly. This chore changes that behavior to display a "Manual Comparison" button instead, which navigates users to the `/comparison` page with pre-filled query parameters.

The button will pass the Thai Watsadu product's SKU, productId, and optionally other data (name, price, imageUrl) as URL query parameters, allowing the comparison page to pre-fill its form fields.

## Relevant Files
Use these files to complete the chore:

- **`app/(main)/products/[id]/page.tsx`** - Main file to modify. Contains the `shouldShowManualForm` logic (lines 228-231) and the section where ManualComparisonForm is rendered (lines 439-451)
- **`app/(main)/comparison/page.tsx`** - Comparison page that already handles `sku` and `productId` query params (lines 96-112). May need updates to pre-fill URL field or additional data
- **`components/products/ManualComparisonButton.tsx`** - Existing button component that navigates to `/comparison` with query params. Can be reused or referenced for styling
- **`lib/types/price-comparison.ts`** - Type definitions for `ProductComparison`, `Retailer` enum - needed to access product properties
- **`components/comparison/ManualComparisonForm.tsx`** - Current inline form component. Import may be removed if unused elsewhere

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update the Product Detail Page to Use Button Instead of Form
- In `app/(main)/products/[id]/page.tsx`, locate the `shouldShowManualForm` conditional block (lines 439-451)
- Keep the yellow warning box that displays "All matched products have been marked as incorrect"
- Remove the `<ManualComparisonForm>` component and replace it with a "Manual Comparison" button
- Import the existing `ManualComparisonButton` component from `@/components/products/ManualComparisonButton`
- Pass the required props: `productId` and `sku` (from `data.product.sku`)

### 2. Enhance ManualComparisonButton to Accept Additional Props (Optional)
- The existing `ManualComparisonButton` component passes `sku` and `productId` to the comparison page
- Optionally extend it to pass additional query params like `name`, `price`, `imageUrl` for better pre-filling
- Update the component interface and router.push URL construction if needed

### 3. Verify Comparison Page Query Param Handling
- The comparison page (`app/(main)/comparison/page.tsx`) already reads `sku` and `productId` from searchParams (lines 96-112)
- Verify the pre-fill logic works correctly with the SKU value
- Optionally extend to read additional params (`name`, `price`, `imageUrl`) and pre-fill corresponding fields

### 4. Clean Up Unused Imports
- In `app/(main)/products/[id]/page.tsx`, check if `ManualComparisonForm` is still used
- If the form is only used in the removed section, remove the import statement
- Remove any other unused imports related to the form (e.g., `handleManualComparisonSubmit`, `handleFetchProduct` handlers if no longer needed)

### 5. Validate the Implementation
- Run type-check to ensure no TypeScript errors
- Run lint to ensure code quality
- Build the application to verify no build errors
- Manually test the flow: mark all products as incorrect → button appears → clicking navigates to comparison page with correct query params

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build

# Manual testing (start dev server)
npm run dev
# Then navigate to http://localhost:3000/products/[any-product-id]
# Mark all matched products as incorrect
# Verify the Manual Comparison button appears
# Click button and verify navigation to /comparison?sku=...&productId=...
```

## Notes
- The existing `ManualComparisonButton` component already follows the codebase styling conventions (cyan-500 background, Lucide icon, Tailwind CSS)
- The comparison page already has infrastructure to read query params and pre-fill the Thai Watsadu SKU field
- Consider whether to remove the `manualComparisonData` display section (lines 454-470) or keep it for cases where manual comparison was previously saved
- The `showManualForm` state and related handlers (`setShowManualForm`, `handleManualComparisonSubmit`, `handleFetchProduct`) may become dead code after this change - evaluate whether to keep or remove
