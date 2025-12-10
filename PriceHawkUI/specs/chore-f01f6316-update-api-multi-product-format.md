# Chore: Update API to Multi-Product Format

## Metadata
adw_id: `f01f6316`
prompt: `Update the API route at app/api/products/comparison/[id]/route.ts to return matchedProducts in new multi-product format: change 'product' object to 'products' array, add unique 'id' field to each product using pattern '{retailer}_{sku}', and remove the inStock field from matched product response. The products array should contain a single product for now but support multiple products per retailer in the future.`

## Chore Description
Update the product comparison detail API endpoint to migrate from the legacy single-product format to the new multi-product format. The API currently returns `matchedProducts` with a `product` object (singular), but needs to return a `products` array (plural) instead. Each product in the array must include a unique `id` field following the pattern `{retailer}_{sku}`. Additionally, the `inStock` field should be removed from the matched product response. The products array should contain a single product initially but the structure will support multiple products per retailer in the future.

The changes align with the type definitions already defined in `lib/types/price-comparison.ts`, where both `RetailerMatch` (new format with `products` array) and `LegacyMatchedProduct` (old format with `product` object) interfaces exist. The frontend code at `app/(main)/products/[id]/page.tsx` already has transformation logic to handle both formats, so this change will make the API use the new format directly.

## Relevant Files
Use these files to complete the chore:

- **app/api/products/comparison/[id]/route.ts** - Main API route file that needs to be updated. Currently returns matchedProducts in legacy format with `product` object (lines 40-68). Needs to change to new format with `products` array.

- **lib/types/price-comparison.ts** - Type definitions file. Contains both `RetailerMatch` (new format, lines 121-126) and `LegacyMatchedProduct` (old format, lines 129-144) interfaces. The API should return `RetailerMatch[]` format.

- **app/(main)/products/[id]/page.tsx** - Frontend page that consumes this API. Already has transformation logic (lines 29-69) to handle both formats, so it will continue to work after the API change.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update API Response Format
- Change the `matchedProducts` mapping logic in route.ts (lines 40-68)
- Replace `product: { ... }` with `products: [{ ... }]`
- Add unique `id` field to each product using pattern `${retailer}_${sku}`
- Remove the `inStock` field from the product object
- Keep the array with a single product for now (to support multiple products per retailer in future)

### 2. Verify Type Compatibility
- Ensure the response matches the `RetailerMatch` interface from `lib/types/price-comparison.ts`
- Confirm that `ProductComparisonDetailResponse.matchedProducts` can accept `RetailerMatch[]` type
- The interface at line 153 already supports both formats: `matchedProducts: (RetailerMatch | LegacyMatchedProduct)[]`

### 3. Test Frontend Compatibility
- The frontend transformation logic in page.tsx (lines 29-69) should detect the new format via the `'products' in match` check (line 36)
- The products will flow through without transformation since they're already in the correct format
- Validation status and other features should continue working

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check to ensure no TypeScript errors
npm run type-check

# Start development server and test the endpoint
npm run dev

# Test the API endpoint directly (in another terminal)
curl http://localhost:3000/api/products/comparison/TWS-001 | jq '.matchedProducts[0]'

# Expected output should show:
# - "products" array (not "product" object)
# - Each product has an "id" field like "homepro_HP-12345"
# - No "inStock" field in products
```

## Notes
- The frontend already has backward-compatible transformation logic, so this change is safe
- The `RetailerMatch` interface supports multiple products via the `products: MatchedProduct[]` array
- For now, each retailer will have exactly one product in their products array
- Future enhancements can add multiple products per retailer without breaking the API contract
- The `inStock` field removal aligns with the `MatchedProduct` interface (lines 106-118) which doesn't include it
