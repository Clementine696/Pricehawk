# Chore: Product Price Comparison Detail Page

## Metadata
adw_id: `30d9ad00`
prompt: `Implement Product Price Comparison Detail Page. Users can open this page by clicking on a product row from the overview page. Objective: Allow users to see full details of all matched products—helping them verify if the compared products are truly identical or just similar. This enables manual checking when the system's automated match may be inaccurate. This detail page must include: Product name, Product description, Product images, SKU, Prices from each retailer, URL links to each retailer's product page. Display should anchor around Thai Watsadu's product, with other retailers shown as 'same item' or 'similar item' for verification. Design and layout should follow the concept similar to Reference [Image #2] (expected/image2.png) and [Image #3] (expected/image3.png). The UI should show: Left side - Thai Watsadu product info (name, description, image, SKU, price, URL), Right side - Matched products from other retailers with confidence rate, match type indicator (exact/similar), and their product details side by side for easy comparison.`

## Chore Description
Implement a Product Price Comparison Detail Page that enables users to verify product matches across retailers. When users click on a product row from the overview page (`/products`), they will navigate to a detail page (`/products/[id]`) that displays:

### Primary Product Display (Left Panel)
Thai Watsadu's product serves as the anchor/reference product, showing:
- Product image (high resolution)
- Product name (Thai and English if available)
- Product description (Thai and English if available)
- SKU
- Brand
- Category
- Current price with currency (THB)
- Stock availability status
- Direct URL link to Thai Watsadu's product page
- Clear visual indicator that this is "My Product" or the reference product

### Matched Products Display (Right Panel)
For each competitor retailer (HomePro, Global House, DoHome, Boonthavorn), display matched products with:
- Retailer name/logo
- Match quality indicators:
  - Match type badge: "Exact" (green) or "Similar" (yellow/orange)
  - Confidence rate: Percentage value (e.g., 100%, 90%, 85%)
- Product details:
  - Product image
  - Product name
  - SKU
  - Brand
  - Category
  - Current price with currency (THB)
  - Stock availability status
  - Direct URL link to retailer's product page
  - Scanning/collection status badge ("Collected")

### Layout Inspiration
The design follows concepts from reference images:
- **Image #2** (`expected/image2.png`): Shows INPUT/OUTPUT split-view layout with primary product on left and matched retailer information on right
- **Image #3** (`expected/image3.png`): Shows "Matched Product Overview" modal with two products displayed side-by-side, including price, SKU, brand, category, store, confidence rate, color, and scanning status indicators

### Key Features
- Two-column responsive layout (stacks on mobile)
- Breadcrumb navigation (Products > Product Detail)
- Back button to return to products list
- Clear visual distinction between reference product and matched products
- External links open in new tabs with security attributes
- Loading and error state handling

## Relevant Files
Use these files to complete the chore:

### Existing Files to Review/Modify
- `app/(main)/products/page.tsx` - Products overview page; `handleRowClick` already navigates to `/products/[id]`
- `lib/types/price-comparison.ts` - Type definitions; already includes `ProductComparisonDetailResponse` with `matchedProducts` array
- `app/api/products/comparison/[id]/route.ts` - API endpoint returning product detail data with matched products, confidence rates, and match types
- `data/mock-products.json` - Mock product data with descriptions

### Existing Components (Already Created)
- `components/products/ProductDetailCard.tsx` - Component displaying Thai Watsadu's product (left panel)
- `components/products/MatchedProductCard.tsx` - Component displaying matched competitor products (right panel)
- `components/products/ConfidenceBadge.tsx` - Badge showing confidence percentage
- `components/products/MatchTypeBadge.tsx` - Badge showing "Exact" or "Similar" match type

### New Files to Create
- `app/(main)/products/[id]/page.tsx` - Product detail page component (main implementation)

### Reference Files
- `expected/image2.png` - UI reference showing INPUT/OUTPUT split layout
- `expected/image3.png` - UI reference showing matched product overview with side-by-side comparison
- `components/products/StatusBadge.tsx` - Existing badge component for reference styling
- `components/layout/MainLayout.tsx` - Main layout wrapper for consistent page structure

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Verify Existing Components
- Read `components/products/ProductDetailCard.tsx` to understand the left panel component structure
- Read `components/products/MatchedProductCard.tsx` to understand the right panel component structure
- Read `components/products/ConfidenceBadge.tsx` to verify confidence rate display
- Read `components/products/MatchTypeBadge.tsx` to verify match type badge display
- Confirm all components match the requirements and reference images

### 2. Review API Endpoint
- Read `app/api/products/comparison/[id]/route.ts` to understand the data structure
- Verify the API returns:
  - Complete product information
  - `matchedProducts` array with confidence and matchType
  - All required fields for display
- Test API response format matches component expectations

### 3. Create Product Detail Page
- Create `app/(main)/products/[id]/page.tsx` as a Next.js client component
- Implement the following structure:
  - Use `'use client'` directive at the top
  - Import necessary components: `MainLayout`, `ProductDetailCard`, `MatchedProductCard`
  - Import types from `lib/types/price-comparison.ts`
  - Use Next.js `useParams` hook to get the product ID from URL
  - Use `useRouter` for back navigation

### 4. Implement Data Fetching
- Add state management for:
  - Product detail data (`ProductComparisonDetailResponse`)
  - Loading state (boolean)
  - Error state (string or null)
- Use `useEffect` to fetch data from `/api/products/comparison/[id]`
- Handle loading, success, and error states appropriately
- Display appropriate UI for each state

### 5. Build Page Layout
- Wrap page in `MainLayout` component
- Add page header section:
  - Back button (using `useRouter().back()` or `router.push('/products')`)
  - Breadcrumb navigation: "Products > Product Detail"
  - Product name as page title
- Create two-column layout:
  - Left column (~40% width): ProductDetailCard
  - Right column (~60% width): Matched products section
- Add proper spacing and margins

### 6. Implement Left Panel (Primary Product)
- Render `ProductDetailCard` component
- Pass `product` prop from API response
- Ensure the card displays all required information:
  - Product image
  - Name (Thai/English)
  - Description (Thai/English)
  - SKU, Brand, Category
  - Price and stock status
  - URL link to Thai Watsadu

### 7. Implement Right Panel (Matched Products)
- Add section title: "Matched Products" or "Other Retailers"
- Map through `matchedProducts` array from API response
- Render `MatchedProductCard` for each matched product
- Pass required props: `retailer`, `confidence`, `matchType`, `product`
- Display cards in a vertical stack or grid layout
- Handle empty state (no matched products)

### 8. Add Responsive Design
- Desktop (≥1024px): Two-column side-by-side layout
- Tablet (768px-1023px): Two-column layout with reduced spacing
- Mobile (<768px): Stack vertically
  - Thai Watsadu product first
  - Matched products below in vertical list
- Use Tailwind CSS responsive classes (e.g., `md:`, `lg:`)

### 9. Handle Loading and Error States
- Loading state:
  - Display skeleton loader or spinner
  - Show "Loading product details..." message
- Error state:
  - Display error message: "Failed to load product details"
  - Show "Try again" button to retry fetch
- 404 state:
  - Display "Product not found" message
  - Show button to return to products list

### 10. Validate Implementation
- Run type checking: `npm run type-check`
- Run linting: `npm run lint`
- Run build: `npm run build`
- Start dev server: `npm run dev`
- Manual testing:
  - Navigate to `/products` page
  - Click on any product row
  - Verify navigation to detail page works
  - Verify all product information displays correctly
  - Verify matched products display with badges
  - Test responsive layout on different screen sizes
  - Test back button functionality
  - Test external links (should open in new tabs)
  - Verify loading and error states

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type checking - ensure no TypeScript errors
npm run type-check

# Linting - ensure code style compliance
npm run lint

# Build - ensure production build succeeds
npm run build

# Start dev server for manual testing
npm run dev
# Then navigate to http://localhost:3000/products
# Click on any product row to verify detail page
# Verify:
# 1. Page loads without errors
# 2. Thai Watsadu product displays on left
# 3. Matched products display on right with badges
# 4. All links work and open in new tabs
# 5. Back button returns to products list
# 6. Layout is responsive on mobile/tablet/desktop
```

## Notes

### UI/UX Considerations
- **Visual Hierarchy**: Thai Watsadu product should be visually distinct as the "anchor" product
- **Confidence Indicators**: Color-coded confidence badges help users quickly assess match quality
- **Match Type Clarity**: "Exact" vs "Similar" badges should be immediately visible
- **External Links**: All product URLs should open in new tabs with `target="_blank"` and `rel="noopener noreferrer"`
- **Navigation**: Easy navigation back to products list via back button and breadcrumbs

### Data Structure
- API already returns proper `ProductComparisonDetailResponse` format
- Matched products include varied confidence rates (95-100% for exact, 80-94% for similar)
- Mock data demonstrates the full range of match types and confidence levels

### Responsive Breakpoints
- Desktop: `lg:` prefix (≥1024px) - two-column layout
- Tablet: `md:` prefix (≥768px) - two-column with tighter spacing
- Mobile: Default (< 768px) - vertical stack layout

### Accessibility
- Proper ARIA labels on all interactive elements
- External link indicators for screen readers
- Color-coded badges also include text labels (not color-only)
- Keyboard navigation support
- Semantic HTML structure

### Performance
- Client-side data fetching with loading states
- Image optimization via Next.js `Image` component
- Lazy loading for images
- Error boundary consideration for production

### Future Enhancements (Not in Scope)
- Price history chart visualization
- Product comparison checklist/table
- Save/bookmark favorite comparisons
- Email alerts for price changes
- Advanced filtering of matched products
