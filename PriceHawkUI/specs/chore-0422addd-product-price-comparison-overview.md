# Chore: Product Price Comparison Overview Page

## Metadata
adw_id: `0422addd`
prompt: `Implement Product Price Comparison Overview Page that compares products (same category and SKU) sold by Thai Watsadu, HomePro, Global House, DoHome, and Boonthavorn. The page should display: product image, product name, SKU, prices from each retailer (clickable links), and a status badge showing whether Thai Watsadu offers the lowest price (green Cheapest), highest price (yellow Higher), or similar price (gray Same). Include search/filter, category/brand dropdowns, and CSV export. Reference: specs/chore-price-comparison-overview.md and expected/image.png`

## Chore Description

Build a comprehensive **Product Price Comparison Overview Page** that allows users to compare the same products (by category and SKU) across five major Thai home improvement retailers:
- **Thai Watsadu** (reference/primary retailer)
- **HomePro**
- **Global House**
- **DoHome**
- **Boonthavorn**

The page will feature:
1. A data table displaying product information with prices from all five retailers
2. Clickable price links that open the product page on the respective retailer's website
3. Status badges showing Thai Watsadu's competitive position (Cheapest/Higher/Same)
4. Search and filter functionality (by name, SKU, brand, category)
5. CSV export capability
6. Product detail modal with comprehensive comparison data
7. Responsive design matching the PriceHawk branding

This is a standalone web application for internal price monitoring and competitive analysis.

## Relevant Files

### Reference Documents
- **specs/chore-price-comparison-overview.md** - Complete specification with UX flows, UI components, data models, and acceptance criteria
- **expected/image.png** - UI reference showing the expected design and layout
- **expected/image2.png** - Additional UI reference (if applicable)
- **expected/image3.png** - Additional UI reference (if applicable)

### New Files

#### Type Definitions & Utilities
- **lib/types/price-comparison.ts** - TypeScript type definitions for products, retailers, prices, filters, and API responses
- **lib/utils/price-utils.ts** - Utility functions for price calculations, status determination, and formatting
- **lib/utils/export-utils.ts** - CSV/Excel export functionality
- **lib/hooks/usePriceComparison.ts** - React hook for data fetching and caching
- **lib/hooks/useProductFilters.ts** - React hook for managing filter state
- **lib/hooks/useExport.ts** - React hook for export functionality

#### UI Components - Products Module
- **components/products/PriceComparisonTable.tsx** - Main table component with sorting and row rendering
- **components/products/PriceComparisonRow.tsx** - Individual table row with product data
- **components/products/PriceCell.tsx** - Price display cell with clickable link and styling
- **components/products/StatusBadge.tsx** - Color-coded status badge (Cheapest/Higher/Same)
- **components/products/ProductSearchFilter.tsx** - Search input and filter controls
- **components/products/ProductDetailModal.tsx** - Modal for detailed product comparison
- **components/products/ProductMatchCard.tsx** - Card showing matched competitor products
- **components/products/PriceHistoryChart.tsx** - Optional price trend visualization
- **components/products/ExportButton.tsx** - CSV/Excel export button

#### Layout Components
- **components/layout/Sidebar.tsx** - Navigation sidebar with PriceHawk logo and menu items
- **components/layout/MainLayout.tsx** - Main layout wrapper with sidebar and content area

#### Shared UI Components (if not already present)
- **components/ui/Table.tsx** - Reusable table component
- **components/ui/Select.tsx** - Dropdown select component
- **components/ui/SearchInput.tsx** - Search input component
- **components/ui/Pagination.tsx** - Pagination controls
- **components/ui/Badge.tsx** - Generic badge component (extend if exists)

#### Pages
- **app/(main)/products/page.tsx** - Main products page (price comparison overview)
- **app/(main)/products/[id]/page.tsx** - Product detail page (optional, can use modal instead)

#### API Routes
- **app/api/products/comparison/route.ts** - GET endpoint for product comparison list with filtering, sorting, pagination
- **app/api/products/comparison/[id]/route.ts** - GET endpoint for individual product detail with price history

#### Mock Data (Development)
- **data/mock-products.json** - Mock product data for development and testing

#### Styling
- **app/globals.css** - Global styles (update if needed for badges, table styling)
- **tailwind.config.js** - Tailwind configuration (update if needed for custom colors)

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Project Setup and Technology Verification
- Verify the project structure (Next.js, React, TypeScript)
- Check existing dependencies (React, Next.js version, UI library)
- Install required packages if missing:
  - `@tanstack/react-table` for table management
  - `papaparse` for CSV export (verify if present)
  - `xlsx` for Excel export
  - `recharts` for charts (verify if present)
- Review existing UI component library and styling approach (Tailwind CSS, shadcn/ui, etc.)
- Check for existing layout components to reuse or extend

### 2. Create Type Definitions and Data Models
- Create `lib/types/price-comparison.ts` with:
  - `Retailer` enum (THAI_WATSADU, HOMEPRO, GLOBAL_HOUSE, DOHOME, BOONTHAVORN)
  - `RetailerNames` mapping for Thai and English names
  - `PriceStatus` type ('cheapest' | 'higher' | 'same' | 'unavailable')
  - `RetailerPrice` interface
  - `ProductComparison` interface
  - `ProductFilterState` interface
  - `PaginationState` interface
  - `ProductComparisonListResponse` interface
  - `ProductComparisonDetailResponse` interface
- Export all types from `lib/types/index.ts` (create if needed)

### 3. Create Utility Functions
- Create `lib/utils/price-utils.ts` with:
  - `calculateStatus()` - Determine if Thai Watsadu price is cheapest/higher/same
  - `findLowestPrice()` - Find lowest price among all retailers
  - `findHighestPrice()` - Find highest price among all retailers
  - `calculatePriceDifference()` - Calculate percentage difference
  - `formatCurrency()` - Format Thai Baht currency
  - `formatDate()` - Format dates for Thai locale
- Create `lib/utils/export-utils.ts` with:
  - `exportToCSV()` - Convert product data to CSV
  - `exportToExcel()` - Convert product data to Excel (optional)
  - `generateFilename()` - Generate export filename with timestamp

### 4. Create Mock Data for Development
- Create `data/mock-products.json` with 20-30 sample products
- Include varied data:
  - Different categories (กระเบื้อง, สีทาบ้าน, เครื่องมือช่าง, ไฟฟ้า)
  - Different brands (XX, TOA, MAKITA, PHILIPS, MODERN FORM)
  - Varied price ranges and statuses
  - Some products with missing competitor prices
  - Realistic Thai product names and SKUs
- Ensure data matches the `ProductComparison` type definition

### 5. Create API Routes with Mock Data
- Create `app/api/products/comparison/route.ts`:
  - GET endpoint that returns paginated product list
  - Support query parameters: `search`, `category`, `brand`, `status`, `page`, `pageSize`, `sortBy`, `sortOrder`
  - Load mock data from `data/mock-products.json`
  - Apply filtering based on query parameters
  - Apply sorting based on query parameters
  - Return paginated results with metadata (total, totalPages)
  - Return available filters (categories, brands) with counts
  - Return summary statistics (cheapest/higher/same counts)
- Create `app/api/products/comparison/[id]/route.ts`:
  - GET endpoint for individual product detail
  - Return product data with price history (can be mocked)
  - Return matched products from competitors with confidence scores

### 6. Create Core UI Components - Badges and Cells
- Create `components/products/StatusBadge.tsx`:
  - Accept `status` prop ('cheapest' | 'higher' | 'same' | 'unavailable')
  - Render colored badge with appropriate text:
    - Cheapest: green background (#10B981), white text
    - Higher: orange/yellow background (#F59E0B), white text
    - Same: gray background (#6B7280), white text
    - Unavailable: light gray, "N/A" text
  - Use rounded pill shape (border-radius: 9999px)
  - Small text size (12px) with medium font weight
- Create `components/products/PriceCell.tsx`:
  - Accept props: `price`, `originalPrice`, `productUrl`, `isLowest`, `isHighest`
  - Display formatted price (฿ symbol) or "-" if null
  - Show external link icon if URL is available
  - Make price clickable, opening URL in new tab
  - Apply green text color if `isLowest`
  - Apply red/orange text color if `isHighest`
  - Show strikethrough original price if different from current price

### 7. Create Table Components
- Create `components/products/PriceComparisonRow.tsx`:
  - Accept `product` prop (ProductComparison type)
  - Accept `rowNumber` prop for the "No." column
  - Accept `onRowClick` callback for row click handling
  - Render table row with columns:
    - No. (row number)
    - Category (Thai name if available)
    - SKU
    - Product Name (truncate with tooltip if too long)
    - Brand
    - Thai Watsadu price (PriceCell component)
    - HomePro price (PriceCell component)
    - Global House price (PriceCell component)
    - DoHome price (PriceCell component)
    - Boonthavorn price (PriceCell component)
    - Status (StatusBadge component)
  - Add hover effect for row
  - Make row clickable (cursor pointer)
- Create `components/products/PriceComparisonTable.tsx`:
  - Accept props: `products`, `isLoading`, `onRowClick`, `sortBy`, `sortOrder`, `onSort`
  - Render table with header row and sortable columns
  - Use `PriceComparisonRow` for each product
  - Show loading skeleton when `isLoading` is true
  - Show empty state when no products
  - Implement column sorting (click header to sort)
  - Style table with borders, alternating row colors
  - Make table horizontally scrollable on small screens

### 8. Create Search and Filter Components
- Create `components/products/ProductSearchFilter.tsx`:
  - Accept props: `filters`, `categories`, `brands`, `onFilterChange`, `onReset`, `onExport`
  - Render search input with placeholder "Search by name, SKU, brand, or retailer..."
  - Render category dropdown with "All Categories" default option
  - Render brand dropdown with "All Brands" default option
  - Render "Reset" button to clear all filters
  - Render "Export" button to trigger CSV export
  - Apply debouncing to search input (300ms delay)
  - Use card/panel styling with proper spacing
  - Ensure responsive layout (stack on mobile)

### 9. Create Export Functionality
- Create `components/products/ExportButton.tsx`:
  - Accept props: `products`, `filename`
  - Render button with download icon
  - On click, convert products to CSV using `exportToCSV()` utility
  - Trigger browser download with generated filename
  - Show loading state during export
  - Handle errors gracefully
- Create `lib/hooks/useExport.ts`:
  - Provide `exportProducts()` function
  - Handle CSV generation and download
  - Support filtering exported data

### 10. Create Data Fetching Hooks
- Create `lib/hooks/usePriceComparison.ts`:
  - Use React Query or SWR for data fetching and caching
  - Fetch from `/api/products/comparison` endpoint
  - Support query parameters for filtering, sorting, pagination
  - Handle loading, error, and success states
  - Auto-refresh every 5 minutes (configurable)
  - Provide manual refresh function
- Create `lib/hooks/useProductFilters.ts`:
  - Manage filter state (search, category, brand, status)
  - Manage sort state (sortBy, sortOrder)
  - Manage pagination state (page, pageSize)
  - Provide filter update functions
  - Provide reset function
  - Sync with URL query parameters (optional but recommended)

### 11. Create Main Products Page
- Create `app/(main)/products/page.tsx`:
  - Set up page layout with header section:
    - Page title: "Products"
    - Subtitle: "Compare prices across retailers"
  - Import and use `ProductSearchFilter` component
  - Import and use `PriceComparisonTable` component
  - Import and use `Pagination` component (create if needed)
  - Use `usePriceComparison` hook for data fetching
  - Use `useProductFilters` hook for filter management
  - Use `useExport` hook for export functionality
  - Connect all components with proper state management
  - Show loading state while fetching data
  - Show error state if data fetching fails
  - Display "Showing X of Y products" text
  - Handle row click to open product detail modal (next step)

### 12. Create Layout Components
- Create `components/layout/Sidebar.tsx`:
  - Display PriceHawk logo at top
  - Render navigation menu items:
    - Dashboard (icon: 📊)
    - Products (icon: 🏷️) - active state
    - Scraping Settings (icon: ⚙️)
  - Style active menu item with blue background
  - Set width to 180px
  - Use proper spacing and hover effects
  - Make responsive (collapsible on mobile)
- Create `components/layout/MainLayout.tsx`:
  - Create layout wrapper with sidebar and main content area
  - Sidebar on left (180px width)
  - Main content area fills remaining space
  - Add top header with "Price Monitoring System" text
  - Ensure proper spacing and responsive behavior
- Update `app/(main)/products/page.tsx` to use `MainLayout`

### 13. Create Product Detail Modal (Optional Enhancement)
- Create `components/products/ProductDetailModal.tsx`:
  - Accept props: `product`, `isOpen`, `onClose`
  - Render modal dialog with backdrop
  - Left side: Thai Watsadu product details
    - Product image
    - Product name
    - Price (current and original)
    - Stock status
    - Promo text (if applicable)
    - SKU, Brand, Category
    - Link to store
  - Right side: Matched competitor products
    - Tabs or cards for each retailer
    - Show match confidence and type (exact/similar)
    - Same product info layout
  - Close on ESC key or click outside
  - Close button in top-right corner
- Create `components/products/ProductMatchCard.tsx`:
  - Display competitor product information
  - Show match confidence percentage
  - Show "Exact Match" or "Similar" badge
  - Link to competitor product page
- Add modal state management to products page
- Connect row click to open modal

### 14. Styling and Responsive Design
- Review and update `app/globals.css`:
  - Add table styles (borders, row colors, hover effects)
  - Add badge styles (if not using component-level styling)
  - Ensure proper typography hierarchy
  - Add responsive breakpoints
- Update `tailwind.config.js` if needed:
  - Add custom colors for badges (green, orange, gray)
  - Add custom spacing values
  - Configure responsive breakpoints
- Test responsive design:
  - Desktop (1920px, 1440px, 1280px)
  - Tablet (768px, 1024px)
  - Mobile (375px, 414px)
- Ensure table is horizontally scrollable on small screens
- Ensure filters stack properly on mobile

### 15. Add Loading States and Error Handling
- Create loading skeleton components for:
  - Table rows (shimmer effect)
  - Filter dropdowns
  - Search input
- Create error state components:
  - Error message display
  - Retry button
- Add empty state for no products found:
  - Empty state icon
  - "No products found" message
  - Clear filters suggestion
- Implement error boundaries for component-level errors
- Add toast notifications for export success/failure

### 16. Thai Language Support
- Add Thai translations for:
  - Page titles and headings
  - Filter labels
  - Button text
  - Status badge text
  - Error messages
  - Empty states
- Support Thai category and product names in data
- Format dates using Thai locale
- Ensure proper Thai Baht (฿) symbol placement

### 17. Testing and Validation
- Test all filter combinations:
  - Search by product name
  - Search by SKU
  - Search by brand
  - Filter by category
  - Filter by brand
  - Combined filters
- Test sorting:
  - Sort by name (asc/desc)
  - Sort by SKU (asc/desc)
  - Sort by category (asc/desc)
  - Sort by brand (asc/desc)
  - Sort by price (asc/desc)
- Test pagination:
  - Navigate between pages
  - Change page size
  - Ensure pagination resets on filter change
- Test export:
  - Export all products
  - Export filtered products
  - Verify CSV format
  - Verify filename includes date
- Test price status logic:
  - Verify "Cheapest" badge when Thai Watsadu has lowest price
  - Verify "Higher" badge when Thai Watsadu has highest price
  - Verify "Same" badge when prices are similar (within 2%)
  - Verify "N/A" when no competitor prices available
- Test clickable price links:
  - Verify links open in new tab
  - Verify links go to correct retailer URL
- Test product detail modal (if implemented):
  - Opens on row click
  - Displays correct product data
  - Closes properly
- Test responsive design on multiple screen sizes
- Test keyboard navigation and accessibility
- Test loading states and error handling

### 18. Performance Optimization
- Implement virtualization for large datasets (if > 1000 products)
- Optimize table rendering with React.memo for row components
- Ensure search debouncing is working (300ms)
- Verify data caching is working (React Query/SWR)
- Check for unnecessary re-renders
- Optimize image loading (lazy loading, proper sizing)
- Test performance with large datasets

### 19. Documentation
- Add code comments for complex logic (price status calculation)
- Document component props with JSDoc
- Update README if needed with:
  - Feature description
  - API endpoints
  - Data model overview
- Create inline documentation for utility functions

### 20. Final Review and Cleanup
- Review all created files for code quality
- Remove any debug console.log statements
- Ensure consistent code formatting
- Verify all TypeScript types are properly defined
- Check for unused imports
- Verify error handling is comprehensive
- Test the complete user journey from entry to export
- Ensure all acceptance criteria are met (reference section 9 of spec)
- Take screenshots for documentation

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# 1. Type checking
npm run type-check
# or
npx tsc --noEmit

# 2. Linting
npm run lint

# 3. Build the application
npm run build

# 4. Start development server and manually test
npm run dev
# Then navigate to http://localhost:3000/products

# 5. Verify all files were created
ls -la lib/types/price-comparison.ts
ls -la lib/utils/price-utils.ts
ls -la lib/utils/export-utils.ts
ls -la components/products/
ls -la app/(main)/products/
ls -la app/api/products/comparison/

# 6. Test API endpoints
curl http://localhost:3000/api/products/comparison
curl http://localhost:3000/api/products/comparison?search=SPC
curl http://localhost:3000/api/products/comparison?category=กระเบื้อง

# 7. Check for console errors in browser DevTools
# Open browser DevTools and verify no errors in Console

# 8. Test responsive design
# Use browser DevTools device toolbar to test mobile/tablet views

# 9. Test export functionality
# Click Export button and verify CSV file downloads with correct data

# 10. Verify git status
git status
# Should show all new files ready to commit
```

## Manual Testing Checklist

After running validation commands, perform these manual tests:

1. **Navigation**
   - [ ] Sidebar displays correctly with PriceHawk logo
   - [ ] "Products" menu item shows active state
   - [ ] Page loads without errors

2. **Table Display**
   - [ ] All 5 retailer columns are visible
   - [ ] Product data displays correctly (image, name, SKU, category, brand)
   - [ ] Prices show correctly with ฿ symbol
   - [ ] Status badges show correct colors (green/yellow/gray)

3. **Search and Filters**
   - [ ] Search input filters products by name, SKU, brand
   - [ ] Category dropdown filters correctly
   - [ ] Brand dropdown filters correctly
   - [ ] Reset button clears all filters
   - [ ] Multiple filters work together

4. **Sorting**
   - [ ] Click column headers to sort
   - [ ] Sort indicator shows direction (asc/desc)
   - [ ] Sorting works for all columns

5. **Pagination**
   - [ ] Pagination controls appear when needed
   - [ ] Page navigation works correctly
   - [ ] "Showing X of Y products" text is accurate
   - [ ] Pagination resets when filters change

6. **Price Links**
   - [ ] Clicking price opens retailer URL in new tab
   - [ ] Links go to correct retailer
   - [ ] "-" displays for unavailable prices

7. **Export**
   - [ ] Export button downloads CSV file
   - [ ] Filename includes date
   - [ ] CSV contains correct data
   - [ ] Filtered data exports correctly

8. **Responsive Design**
   - [ ] Layout adapts to mobile screens
   - [ ] Table scrolls horizontally on small screens
   - [ ] Filters stack properly on mobile
   - [ ] Sidebar collapses on mobile (if implemented)

9. **Loading & Error States**
   - [ ] Loading skeleton shows while fetching data
   - [ ] Error message displays if API fails
   - [ ] Empty state shows when no products found

10. **Accessibility**
    - [ ] Can navigate with keyboard (Tab, Enter, Esc)
    - [ ] Screen reader announces important elements
    - [ ] Focus indicators are visible

## Notes

### Implementation Approach
This implementation follows a **bottom-up component architecture**:
1. Start with foundational types and utilities
2. Build atomic UI components (badges, cells)
3. Compose into molecules (rows, filters)
4. Create organism components (table, page)
5. Integrate with data layer (hooks, API)
6. Add cross-cutting concerns (responsive design, i18n, error handling)

### Technology Stack Assumptions
- **Framework**: Next.js 13+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks + React Query/SWR for server state
- **Table**: @tanstack/react-table for advanced table features
- **Export**: papaparse for CSV generation

### Performance Considerations
- Use `React.memo()` for `PriceComparisonRow` to prevent unnecessary re-renders
- Implement search debouncing to reduce API calls
- Use virtualization (react-window or @tanstack/react-virtual) if dataset exceeds 1000 products
- Enable React Query caching with 5-minute stale time
- Lazy load product detail modal

### Accessibility Features
- ARIA labels on all interactive elements
- Keyboard navigation support (Tab, Enter, Esc)
- Focus management in modal
- Screen reader announcements for filter changes
- Color contrast meets WCAG AA standards
- Semantic HTML structure

### Future Enhancements
- Real-time price updates via WebSocket
- Price history chart in detail modal
- Email alerts for price changes
- Bulk export to Excel
- Advanced filtering (price range, stock status, promo)
- Saved filter presets
- Product comparison across multiple SKUs
- Price trend analysis dashboard

### Critical Success Factors
1. **Status badge logic must be accurate** - The 2% threshold for "Same" status is business-critical
2. **Price links must be functional** - External links are primary user action
3. **Performance with large datasets** - System should handle 1000+ products smoothly
4. **Export reliability** - CSV export is a key reporting feature
5. **Mobile responsiveness** - Users may access on tablets/mobile devices

### Data Source Integration
Currently using mock data (`data/mock-products.json`). In production:
- API should fetch from database of scraped product data
- Price data should be refreshed regularly (daily/hourly)
- Product matching logic should handle variations in names/SKUs
- Historical price data should be preserved for trend analysis
