# Chore: Refactor Product Comparison Detail Page

## Metadata
adw_id: `f5df3e67`
prompt: `Refactor Product Comparison Detail page with UI changes: remove stock field, add retailer colors, add validation action buttons, support multiple matched products per retailer, add manual comparison fallback, add validation status types, create validation persistence utility`

## Chore Description
Refactor the Product Comparison Detail page (`app/(main)/products/[id]/page.tsx`) and related components to:
1. Remove the stock/inStock field from ProductDetailCard and MatchedProductCard
2. Add distinct header colors for each retailer in MatchedProductCard
3. Add validation action buttons (Incorrect/Correct) to each matched product
4. Support multiple matched products per retailer
5. Show ManualComparisonForm when all matched products are marked incorrect
6. Add validation status types to the type definitions
7. Create localStorage utility for persisting validation status

## Relevant Files
Use these files to complete the chore:

- **lib/types/price-comparison.ts** - Add ValidationStatus type, update matchedProducts interface to support multiple products per retailer, add validationStatus and isManualEntry fields
- **components/products/ProductDetailCard.tsx** - Remove stock field from the details grid (lines 76-80)
- **components/products/MatchedProductCard.tsx** - Remove stock field (lines 89-94), add retailer header colors, add validation action buttons
- **app/(main)/products/[id]/page.tsx** - Handle validation state, filter incorrect products, integrate ManualComparisonForm
- **components/comparison/ManualComparisonForm.tsx** - Existing component to show as fallback when all products marked incorrect

### New Files
- **lib/utils/validation-storage.ts** - localStorage utility for persisting validation status
- **lib/constants/retailer-colors.ts** - RetailerColors constant mapping Retailer enum to Tailwind bg colors

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Validation Status Types to lib/types/price-comparison.ts
- Add `ValidationStatus` type: `'pending' | 'correct' | 'incorrect'`
- Add `validationStatus?: ValidationStatus` field to matched product interface
- Add `isManualEntry?: boolean` field to matched product interface
- Update `matchedProducts` in `ProductComparisonDetailResponse` to support array of products per retailer:
  ```typescript
  matchedProducts: {
    retailer: Retailer;
    confidence: number;
    matchType: 'exact' | 'similar';
    products: {  // Changed from 'product' to 'products' array
      id: string;  // Unique ID for each product
      name: string;
      sku: string;
      imageUrl: string;
      price: number;
      url: string;
      description?: string;
      brand?: string;
      category?: string;
      validationStatus?: ValidationStatus;
      isManualEntry?: boolean;
    }[];
  }[];
  ```

### 2. Create Retailer Colors Constant
- Create new file `lib/constants/retailer-colors.ts`
- Define `RetailerColors` constant mapping `Retailer` enum to Tailwind bg classes:
  ```typescript
  import { Retailer } from '@/lib/types/price-comparison';

  export const RetailerColors: Record<Retailer, string> = {
    [Retailer.THAI_WATSADU]: 'bg-red-600',
    [Retailer.HOMEPRO]: 'bg-red-500',
    [Retailer.GLOBAL_HOUSE]: 'bg-blue-800',
    [Retailer.DOHOME]: 'bg-orange-500',
    [Retailer.BOONTHAVORN]: 'bg-green-600',
  };
  ```

### 3. Create Validation Storage Utility
- Create new file `lib/utils/validation-storage.ts`
- Implement functions:
  - `getValidationStatus(productId: string, matchedProductId: string): ValidationStatus | null`
  - `setValidationStatus(productId: string, matchedProductId: string, status: ValidationStatus): void`
  - `getAllValidationStatuses(productId: string): Record<string, ValidationStatus>`
  - `clearValidationStatuses(productId: string): void`
  - `getManualComparison(productId: string): ManualComparisonData | null`
  - `setManualComparison(productId: string, data: ManualComparisonData): void`
- Use localStorage key pattern: `pricehawk_validation_{productId}`
- Handle SSR by checking for `typeof window !== 'undefined'`

### 4. Remove Stock Field from ProductDetailCard
- Open `components/products/ProductDetailCard.tsx`
- Remove the stock field section from the details grid (lines 75-80):
  ```tsx
  // DELETE this entire div:
  <div>
    <span className="text-gray-500">Stock</span>
    <p className={`font-medium ${thaiWatsaduPrice.inStock ? 'text-green-600' : 'text-red-600'}`}>
      {thaiWatsaduPrice.inStock ? 'In Stock' : 'Out of Stock'}
    </p>
  </div>
  ```

### 5. Refactor MatchedProductCard Component
- Open `components/products/MatchedProductCard.tsx`
- Remove the stock field section from details grid (lines 89-94)
- Import `RetailerColors` from `lib/constants/retailer-colors.ts`
- Update header div to use dynamic retailer color:
  ```tsx
  <div className={`${RetailerColors[retailer]} px-4 py-3 border-b border-gray-200`}>
    <span className="font-medium text-white">{retailerName.en}</span>
  ```
- Update the interface to receive additional props:
  ```typescript
  interface MatchedProductCardProps {
    retailer: Retailer;
    confidence: number;
    matchType: 'exact' | 'similar';
    products: MatchedProduct[]; // Changed to array
    onMarkCorrect: (productId: string) => void;
    onMarkIncorrect: (productId: string) => void;
  }
  ```
- Update component to iterate over `products` array
- Add validation action buttons at the bottom-right of each product item:
  ```tsx
  <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-100">
    <button
      onClick={() => onMarkIncorrect(product.id)}
      className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
    >
      <X className="w-4 h-4" />
      Incorrect
    </button>
    <button
      onClick={() => onMarkCorrect(product.id)}
      className="flex items-center gap-1 px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded-lg transition-colors"
    >
      <Check className="w-4 h-4" />
      Correct
    </button>
  </div>
  ```
- Show validation status badge when product is validated:
  - If `validationStatus === 'correct'`: Green checkmark badge
  - If `validationStatus === 'incorrect'`: Red X badge (though these will be filtered out)

### 6. Update Product Detail Page with Validation Logic
- Open `app/(main)/products/[id]/page.tsx`
- Import validation storage utilities and ManualComparisonForm
- Add local state for validation statuses:
  ```typescript
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ValidationStatus>>({});
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualComparisonData, setManualComparisonData] = useState<ManualComparisonData | null>(null);
  ```
- Load validation statuses from localStorage on mount:
  ```typescript
  useEffect(() => {
    if (productId) {
      const statuses = getAllValidationStatuses(productId);
      setValidationStatuses(statuses);
      const manualData = getManualComparison(productId);
      setManualComparisonData(manualData);
    }
  }, [productId]);
  ```
- Implement `handleMarkCorrect` and `handleMarkIncorrect` functions:
  - Update local state
  - Persist to localStorage
  - Check if all products are now incorrect -> show manual form
- Filter out products with `validationStatus === 'incorrect'` when rendering
- Transform API response to support new multi-product structure
- Conditionally render ManualComparisonForm when:
  - All matched products for the source product are marked 'incorrect'
  - OR `showManualForm` state is true
- Handle ManualComparisonForm submission:
  - Store manual comparison data in localStorage
  - Display manual entry in matched products section with `isManualEntry: true`

### 7. Update API Mock Data (if needed)
- Check `data/mock-products.json` or API route handler
- Update mock data to return products array per retailer instead of single product
- Add unique IDs to each matched product

### 8. Validate the Implementation
- Run type checking: `npm run type-check`
- Run linting: `npm run lint`
- Run build: `npm run build`
- Test manually:
  - Navigate to product detail page
  - Verify stock fields are removed
  - Verify retailer header colors
  - Click Incorrect/Correct buttons and verify persistence
  - Refresh page and verify incorrect products are filtered
  - Mark all products incorrect and verify ManualComparisonForm appears
  - Submit manual comparison and verify display

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Build
npm run build

# Start dev server for manual testing
npm run dev
```

Manual Testing Checklist:
1. Navigate to `/products/[id]` for any product
2. Verify stock field is NOT visible in ProductDetailCard
3. Verify stock field is NOT visible in MatchedProductCard
4. Verify each retailer has distinct header color:
   - Thai Watsadu: Red header (bg-red-600) - shown in ProductDetailCard
   - HomePro: Red header (bg-red-500)
   - Global House: Blue header (bg-blue-800)
   - DoHome: Orange header (bg-orange-500)
   - Boonthavorn: Green header (bg-green-600)
5. Verify Incorrect/Correct buttons appear at bottom-right of each matched product
6. Click "Incorrect" on a product, verify it disappears on page refresh
7. Click "Correct" on a product, verify green checkmark badge appears
8. Mark ALL matched products as "Incorrect", verify ManualComparisonForm appears
9. Submit manual comparison, verify new product appears in matched products section

## Notes
- The `ManualComparisonForm` component already exists in `components/comparison/ManualComparisonForm.tsx` - it requires `onSubmit` and `onFetchProduct` props
- The existing `Retailer` enum in `lib/types/price-comparison.ts` already has all 5 retailers defined
- Thai Watsadu header color (bg-red-600) is already used in ProductDetailCard but needs to be defined in RetailerColors constant for consistency
- Consider adding a "Reset Validations" button to allow users to start over
- localStorage is used for persistence to avoid API complexity; can be migrated to API later
- Product IDs for matched products should be generated using a combination of retailer and SKU: `${retailer}_${sku}`
