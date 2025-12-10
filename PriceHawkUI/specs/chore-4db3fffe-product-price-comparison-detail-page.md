# Chore: Product Price Comparison Detail Page

## Metadata
adw_id: `4db3fffe`
prompt: `Implement Product Price Comparison Detail Page. Users can open this page by clicking on a product row from the overview page. Objective: Allow users to see full details of all matched products—helping them verify if the compared products are truly identical or just similar. This enables manual checking when the system's automated match may be inaccurate. This detail page must include: Product name, Product description, Product images, SKU, Prices from each retailer, URL links to each retailer's product page. Display should anchor around Thai Watsadu's product, with other retailers shown as 'same item' or 'similar item' for verification. Design and layout should follow the concept similar to Reference [Image #2] (expected/image2.png) and [Image #3] (expected/image3.png). The UI should show: Left side - Thai Watsadu product info (name, description, image, SKU, price, URL), Right side - Matched products from other retailers with confidence rate, match type indicator (exact/similar), and their product details side by side for easy comparison.`

## Chore Description
Implement a Product Price Comparison Detail Page that allows users to verify product matches across retailers. When users click on a product row from the overview page (`/products`), they will navigate to a detail page (`/products/[id]`) showing:

1. **Left Panel (Primary Product)**: Thai Watsadu's product information as the reference/anchor including:
   - Product image
   - Product name (Thai and English)
   - SKU
   - Price with currency
   - Product URL link to Thai Watsadu website
   - Stock status

2. **Right Panel (Matched Products)**: Competitor products from HomePro, Global House, DoHome, and Boonthavorn showing:
   - Match type badge (exact/similar)
   - Confidence rate percentage (e.g., "100%", "90%")
   - Product image
   - Product name
   - SKU
   - Price with currency
   - Product URL link
   - Stock status
   - "Collected" scanning status

The layout is inspired by the reference images:
- **Image #2**: Shows INPUT/OUTPUT split view with primary product on left and matched retailer URLs on right
- **Image #3**: Shows "Matched Product Overview" modal with two products side-by-side displaying price, SKU, brand, category, store, confidence rate, color, and scanning status

## Relevant Files
Use these files to complete the chore:

### Existing Files to Modify
- `app/(main)/products/page.tsx` - Update `handleRowClick` to navigate to detail page instead of console.log
- `lib/types/price-comparison.ts` - Already contains `ProductComparisonDetailResponse` with `matchedProducts` array including confidence and matchType
- `app/api/products/comparison/[id]/route.ts` - Already exists with mock data for detail response; may need enhancement for more detailed matched product info

### New Files to Create

- `app/(main)/products/[id]/page.tsx` - New detail page component
- `components/products/ProductDetailCard.tsx` - Reusable component for displaying Thai Watsadu's product info (left panel)
- `components/products/MatchedProductCard.tsx` - Reusable component for displaying matched competitor product (right panel cards)
- `components/products/ConfidenceBadge.tsx` - Badge component showing confidence percentage
- `components/products/MatchTypeBadge.tsx` - Badge component showing "Exact" or "Similar" match type

### Reference Files
- `expected/image2.png` - Reference UI showing INPUT/OUTPUT split layout
- `expected/image3.png` - Reference UI showing matched product overview with side-by-side comparison
- `data/mock-products.json` - Existing mock data structure for products

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Extend Type Definitions
- Add `description` and `descriptionTh` fields to `ProductComparison` interface in `lib/types/price-comparison.ts`
- Update `matchedProducts` type in `ProductComparisonDetailResponse` to include description field in the product object
- Ensure all necessary fields are typed for the detail view

### 2. Update Mock Data
- Add `description` and `descriptionTh` fields to products in `data/mock-products.json`
- Ensure mock data supports the new detail view requirements

### 3. Enhance API Detail Endpoint
- Update `app/api/products/comparison/[id]/route.ts` to return richer matched product data
- Include varied confidence rates (some exact 100%, some similar 85-95%)
- Include varied match types (exact vs similar)
- Add description field to matched products response

### 4. Create MatchTypeBadge Component
- Create `components/products/MatchTypeBadge.tsx`
- Display "Exact" badge in green for exact matches
- Display "Similar" badge in yellow/orange for similar matches
- Style similar to existing StatusBadge component

### 5. Create ConfidenceBadge Component
- Create `components/products/ConfidenceBadge.tsx`
- Display confidence percentage (e.g., "100%", "90%")
- Color-coded: green for high confidence (95%+), yellow for medium (80-94%), orange for lower

### 6. Create ProductDetailCard Component
- Create `components/products/ProductDetailCard.tsx`
- Display Thai Watsadu's product as the primary/anchor product
- Include: image, name (Thai), SKU, brand, category, price, stock status, URL link
- Style with card layout and prominent display
- Add "My product" or similar label to indicate this is the reference product

### 7. Create MatchedProductCard Component
- Create `components/products/MatchedProductCard.tsx`
- Display competitor product info in a card format
- Include: MatchTypeBadge, ConfidenceBadge, image, name, SKU, brand, category, store name, price, URL link, scanning status
- Show "Collected" status badge for scanning status
- Style to match reference image #3 layout

### 8. Create Product Detail Page
- Create `app/(main)/products/[id]/page.tsx`
- Fetch product detail data using `GET /api/products/comparison/:id`
- Layout: Two-column split view
  - Left column (~40%): ProductDetailCard for Thai Watsadu product
  - Right column (~60%): Grid/list of MatchedProductCard components
- Add breadcrumb navigation: Products > Product Detail
- Add back button to return to products list
- Handle loading and error states
- Make page responsive (stack on mobile)

### 9. Update Products Page Navigation
- Modify `handleRowClick` in `app/(main)/products/page.tsx`
- Use Next.js router to navigate to `/products/[id]` when row is clicked
- Import and use `useRouter` from `next/navigation`

### 10. Validate Implementation
- Run type checking with `npm run type-check`
- Run linting with `npm run lint`
- Run build with `npm run build`
- Start dev server with `npm run dev`
- Test navigation from products list to detail page
- Verify all product information displays correctly
- Test responsive layout on different screen sizes

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type checking - ensure no TypeScript errors
npm run type-check

# Linting - ensure code style compliance
npm run lint

# Build - ensure production build succeeds
npm run build

# Start dev server and manually test
npm run dev
# Then navigate to http://localhost:3000/products
# Click on any product row to verify navigation to detail page
```

## Notes

### UI Design Considerations
- The design should clearly distinguish the "anchor" product (Thai Watsadu) from matched products
- Confidence rate should be prominently displayed to help users assess match quality
- Match type (exact/similar) should be immediately visible with color-coded badges
- Product images should be displayed if available, with placeholder for missing images
- External URLs should open in new tabs with proper `rel="noopener noreferrer"`

### Data Considerations
- The existing API endpoint already returns `matchedProducts` array with `confidence` and `matchType`
- Mock data should include varied confidence rates and match types to demonstrate the UI
- Consider adding "similar" matches with lower confidence (80-90%) to show the full range

### Responsive Design
- Desktop: Side-by-side two-column layout
- Tablet: May reduce spacing but maintain two columns
- Mobile: Stack vertically - Thai Watsadu product first, then matched products below

### Accessibility
- Ensure proper ARIA labels on interactive elements
- External links should indicate they open in new window
- Color-coded badges should also have text labels for color-blind users
