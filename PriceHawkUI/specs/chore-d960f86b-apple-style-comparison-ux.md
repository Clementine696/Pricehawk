# Chore: Enhance Manual Comparison Page UX/UI with Apple-Style Design

## Metadata
adw_id: `d960f86b`
prompt: `Enhance Manual Comparison page UX/UI inspired by Apple iPhone Compare page (https://www.apple.com/th/iphone/compare/) while PRESERVING exact input requirements. KEEP EXISTING INPUT FLOW: 1) THAI WATSADU (Main Input) - SKU field (required), Product URL from Thai Watsadu (required). 2) COMPETITOR INPUTS - Retailer Name dropdown (select ONLY from: HomePro, MegaHome, Boonthavorn, Global House, DoHome), Product URL for each retailer (required). Users can add MULTIPLE competitor entries but each must belong to approved retailer list only. ENHANCE WITH APPLE-STYLE DESIGN: INPUT SECTION - Clean card-based layout for ThaiWatsadu input card and competitor input cards, '+Add Competitor' button to add more retailer entries, each competitor card shows retailer dropdown + URL input with remove button, form validation with clear error states. COMPARISON RESULT VIEW (after submission): 1) STICKY HEADER - ThaiWatsadu product in first column, competitor products in subsequent columns, product images and retailer logos fixed at top while scrolling. 2) SIDE-BY-SIDE COLUMN LAYOUT - first column for attribute labels, remaining columns for ThaiWatsadu vs each competitor (HomePro, MegaHome, etc.). 3) GROUPED SPEC SECTIONS - Pricing section (price, discount %, unit price, price difference), Product Info section (name, SKU, brand, category), Availability section (stock status). 4) PRICE COMPARISON HIGHLIGHT - large bold typography for prices like Apple's screen size display (e.g., '฿1,299' in large text), color-coded difference (green=ThaiWatsadu cheaper, red=competitor cheaper, show ฿ amount and % difference). 5) VISUAL INDICATORS - checkmarks for matching attributes, warning icons for significant price differences, dashes for unavailable data. 6) RETAILER BRANDING - show retailer logo/name in each column header. 7) CTA per column - 'View Product' link to original URL for each retailer. 8) CLEAN WHITESPACE with subtle dividers between spec groups. 9) RESPONSIVE TABLE with proper semantic HTML. Keep multi-step flow: Step 1 (Input ThaiWatsadu + Competitors) -> Step 2 (Review/Confirm) -> Step 3 (Comparison Results in Apple-style table).`

## Chore Description

Redesign the Manual Comparison page to match the Apple iPhone Compare page aesthetic and user experience while preserving the existing input requirements. The enhancement focuses on two main areas:

**INPUT SECTION (Preserve existing flow)**:
- Thai Watsadu input card with SKU and URL fields (required)
- Dynamic competitor input cards with retailer dropdown and URL fields
- '+Add Competitor' button to add multiple competitor entries
- Clean card-based layout with clear validation and error states
- Remove button for each competitor card

**COMPARISON RESULT VIEW (New Apple-style design)**:
- Sticky header with product images and retailer logos that remains fixed while scrolling
- Side-by-side column layout (attribute labels + ThaiWatsadu + competitors)
- Grouped specification sections:
  - **Pricing**: Price, discount %, unit price, price difference
  - **Product Info**: Name, SKU, brand, category
  - **Availability**: Stock status
- Large bold typography for prices (e.g., '฿1,299' like Apple's screen size display)
- Color-coded price differences:
  - Green: ThaiWatsadu cheaper
  - Red: Competitor cheaper
  - Show both ฿ amount and % difference
- Visual indicators:
  - Checkmarks for matching attributes
  - Warning icons for significant price differences
  - Dashes for unavailable data
- Retailer branding in column headers (logo + name)
- 'View Product' CTA link per column
- Clean whitespace with subtle dividers between spec groups
- Responsive design with proper semantic HTML

**Multi-step flow**:
1. Input ThaiWatsadu + Competitors
2. Review/Confirm inputs
3. Display Comparison Results in Apple-style table

## Relevant Files

### Existing Files to Update

- **`app/(main)/comparison/page.tsx`**: Main comparison page - needs major restructuring to support 3-step flow (Input -> Review -> Results) and display Apple-style comparison table
- **`components/comparison/ThaiWatsuduInputCard.tsx`**: Currently exists with red header and SKU/URL inputs - may need minor refinements for consistency
- **`components/comparison/CompetitorInputCard.tsx`**: Currently exists with colored headers and multi-URL support - needs to be simplified to single URL + retailer dropdown
- **`components/comparison/RetailerSelector.tsx`**: Currently used for stage 2 - needs to be integrated as dropdown within CompetitorInputCard
- **`components/comparison/UserValidationPanel.tsx`**: Currently shows match/not-match results - will be REPLACED with new Apple-style comparison table
- **`lib/types/manual-comparison.ts`**: Type definitions - may need updates to support comparison table data structure
- **`lib/utils/price-utils.ts`**: Existing price utilities - needs new functions for price difference calculation and color-coding logic
- **`app/api/products/comparison/route.ts`**: May need to support manual comparison results endpoint or extend existing

### New Files to Create

- **`components/comparison/AppleStyleComparisonTable.tsx`**: Main Apple-style comparison table component with sticky header and column layout
- **`components/comparison/ComparisonStickyHeader.tsx`**: Sticky header component showing product images and retailer logos
- **`components/comparison/ComparisonSpecSection.tsx`**: Reusable component for grouped spec sections (Pricing, Product Info, Availability)
- **`components/comparison/PriceDifferenceDisplay.tsx`**: Component for large bold price display with color-coded difference
- **`components/comparison/ComparisonAttributeRow.tsx`**: Row component for individual attribute comparison with visual indicators
- **`components/comparison/ReviewConfirmPanel.tsx`**: New Step 2 component for reviewing inputs before submission
- **`lib/utils/comparison-display-utils.ts`**: Utilities for formatting comparison data, calculating differences, determining visual indicators

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Utility Functions for Comparison Display
- Create new file `lib/utils/comparison-display-utils.ts`
- Add `calculatePriceDifference(thaiWatsuduPrice: number, competitorPrice: number)` function that returns:
  - `amountDifference`: Absolute difference in baht
  - `percentageDifference`: Percentage difference
  - `status`: 'cheaper' | 'more-expensive' | 'same'
- Add `getComparisonColor(status: string)` function that returns Tailwind color classes (green for cheaper, red for more expensive, gray for same)
- Add `formatThaiCurrency(amount: number)` function for consistent currency display
- Add `getAttributeIcon(attributeName: string, hasValue: boolean)` function that returns appropriate Lucide icon (checkmark, dash, warning)
- Add `isSignificantPriceDifference(percentage: number)` function (returns true if > 5%)

### 2. Create Price Difference Display Component
- Create `components/comparison/PriceDifferenceDisplay.tsx`
- Accept props: `thaiWatsuduPrice`, `competitorPrice`, `competitorName`
- Display large bold price (e.g., '฿1,299' in text-4xl or text-5xl)
- Show price difference below in smaller text with color coding
- Display both baht amount and percentage (e.g., '฿200 cheaper (15%)')
- Use green background tint for cheaper, red tint for more expensive
- Match Apple's visual hierarchy (large number, small subtitle)

### 3. Create Comparison Attribute Row Component
- Create `components/comparison/ComparisonAttributeRow.tsx`
- Accept props: `label`, `thaiWatsuduValue`, `competitorValues[]`, `attributeType`
- First column shows attribute label (e.g., 'Brand', 'SKU', 'Category')
- Subsequent columns show values for ThaiWatsadu and each competitor
- Add visual indicators:
  - Checkmark icon for matching values
  - Warning icon for significant differences (prices)
  - Dash (-) for unavailable data
- Support different attribute types: 'text', 'price', 'status', 'url'
- Apply appropriate formatting based on type

### 4. Create Grouped Spec Section Component
- Create `components/comparison/ComparisonSpecSection.tsx`
- Accept props: `title`, `attributes[]`, `thaiWatsuduData`, `competitorData[]`
- Render section title (e.g., 'Pricing', 'Product Information', 'Availability')
- Map through attributes and render ComparisonAttributeRow for each
- Add subtle divider between sections
- Use clean whitespace matching Apple's design

### 5. Create Sticky Header Component
- Create `components/comparison/ComparisonStickyHeader.tsx`
- Accept props: `thaiWatsuduProduct`, `competitorProducts[]`
- Use `position: sticky` with `top-0` to fix header while scrolling
- First column: Empty or 'Compare' label
- Subsequent columns: Product image + retailer logo + retailer name
- Display product thumbnail (aspect ratio preserved, centered)
- Show retailer logo and name prominently
- Add subtle shadow when scrolled (`shadow-md`)
- Ensure responsive layout (minimum column width, horizontal scroll on mobile)

### 6. Create Main Apple-Style Comparison Table
- Create `components/comparison/AppleStyleComparisonTable.tsx`
- Accept props: `thaiWatsuduProduct`, `competitorProducts[]`
- Render ComparisonStickyHeader at top
- Render three ComparisonSpecSection components:
  - **Pricing Section**: price, discount percentage, unit price, price difference (using PriceDifferenceDisplay)
  - **Product Information Section**: name, SKU, brand, category
  - **Availability Section**: stock status, availability date
- Add 'View Product' link CTA in each column footer
- Use semantic HTML (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`)
- Apply Tailwind classes for clean spacing and dividers
- Ensure responsive behavior with horizontal scroll on small screens
- Add smooth scroll behavior for better UX

### 7. Create Review/Confirm Panel Component
- Create `components/comparison/ReviewConfirmPanel.tsx`
- Accept props: `thaiWatsuduInput`, `competitorEntries[]`, `onEdit`, `onConfirm`
- Display summary card showing:
  - ThaiWatsadu SKU and URL
  - List of competitors with their URLs
  - Total count of comparisons to be performed
- Add 'Edit' button to go back to input stage
- Add 'Confirm & Compare' button to proceed to results
- Use card-based layout matching existing design

### 8. Update Competitor Input Card for Dropdown Retailer Selection
- Open `components/comparison/CompetitorInputCard.tsx`
- Replace current design to include:
  - Retailer dropdown (select from: HomePro, MegaHome, Boonthavorn, Global House, DoHome)
  - Single URL input field (remove multi-URL support for simplicity)
  - Remove button in top-right corner
- Update styling to match ThaiWatsuduInputCard design
- Add validation for retailer selection and URL format
- Display retailer-specific color border based on selection
- Update component props to accept `retailer`, `url`, `onRetailerChange`, `onUrlChange`, `onRemove`

### 9. Restructure Comparison Page for 3-Step Flow
- Open `app/(main)/comparison/page.tsx`
- Update stage type to: `'input' | 'review' | 'results'`
- Update state management:
  - `thaiWatsuduInput`: { sku, url }
  - `competitorEntries`: Array of { id, retailer, url }
  - `comparisonResults`: Results from API
  - `stage`: Current stage
- Implement Stage 1 (Input):
  - Show ThaiWatsuduInputCard
  - Show list of CompetitorInputCard components (dynamic)
  - Add '+Add Competitor' button (cyan/sky button with Plus icon)
  - Validate: SKU, URL required; at least one competitor; no duplicate retailers
  - 'Next' button to go to Review stage
- Implement Stage 2 (Review):
  - Show ReviewConfirmPanel with summary
  - 'Back' button to return to Input
  - 'Confirm & Compare' button to submit and go to Results
- Implement Stage 3 (Results):
  - Show AppleStyleComparisonTable with comparison data
  - Add 'Start New Comparison' button to reset flow
- Add proper error handling and loading states
- Ensure smooth transitions between stages

### 10. Update Type Definitions
- Open `lib/types/manual-comparison.ts`
- Add new interface `ComparisonTableProduct`:
  - `sku: string`
  - `name: string`
  - `price: number`
  - `discountPercentage?: number`
  - `unitPrice?: number`
  - `imageUrl: string`
  - `productUrl: string`
  - `brand?: string`
  - `category?: string`
  - `stockStatus?: string`
  - `retailer: 'THAI_WATSADU' | CompetitorRetailer`
- Add interface `ComparisonTableData`:
  - `thaiWatsadu: ComparisonTableProduct`
  - `competitors: ComparisonTableProduct[]`
- Ensure existing types support single URL per competitor entry

### 11. Update API Route or Create Mock Data Handler
- Check if `app/api/comparison/manual/route.ts` exists
- Update POST handler to:
  - Accept ThaiWatsadu SKU/URL + competitor entries
  - Fetch or mock product data for ThaiWatsadu and each competitor
  - Return ComparisonTableData structure
  - Include all necessary fields for comparison table display
- Add error handling for invalid SKUs or URLs
- Return 200 with comparison data or 400/404 with error messages

### 12. Update Component Index Exports
- Open `components/comparison/index.ts`
- Export all new components:
  - `AppleStyleComparisonTable`
  - `ComparisonStickyHeader`
  - `ComparisonSpecSection`
  - `ComparisonAttributeRow`
  - `PriceDifferenceDisplay`
  - `ReviewConfirmPanel`
- Ensure existing components remain exported

### 13. Add Responsive Styles and Refinements
- Update `tailwind.config.js` if needed for custom breakpoints
- Add responsive behavior to AppleStyleComparisonTable:
  - Desktop: Full side-by-side columns
  - Tablet: Horizontal scroll with sticky first column
  - Mobile: Horizontal scroll with minimum column widths
- Ensure sticky header works correctly on all screen sizes
- Test with 1, 2, 3, 4, and 5 competitors
- Add smooth animations for stage transitions
- Ensure accessibility (ARIA labels, keyboard navigation, screen reader support)

### 14. Test and Validate the Complete Flow
- Run `npm run type-check` to ensure no TypeScript errors
- Run `npm run lint` to check for linting issues
- Test manually in browser:
  - **Input Stage**: Enter ThaiWatsadu SKU/URL, add multiple competitors, validate error states
  - **Review Stage**: Verify all inputs are displayed correctly, test Edit and Confirm buttons
  - **Results Stage**: Check Apple-style table displays correctly, test sticky header scroll, verify price differences, check visual indicators
  - **Responsive**: Test on different screen sizes (desktop, tablet, mobile)
  - **Edge Cases**: Test with 1 competitor, 5 competitors, missing data, unavailable products
- Verify color-coding logic for price differences
- Ensure 'View Product' links work correctly
- Test 'Start New Comparison' flow

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build (ensures production build works)
npm run build

# Start dev server and manually test
npm run dev
# Navigate to http://localhost:3000/comparison
```

## Notes

- **Design Inspiration**: Reference https://www.apple.com/th/iphone/compare/ for visual hierarchy, typography, spacing, and layout patterns
- **Preserve Input Requirements**: Keep exact input flow (ThaiWatsadu SKU+URL, Competitor retailer+URL) as specified
- **Retailer List**: Only allow selection from: HomePro, MegaHome, Boonthavorn, Global House, DoHome (defined in `lib/constants/competitors.ts`)
- **Color Coding**: Use existing Tailwind theme colors (green for cheaper, red for expensive, gray for same/unavailable)
- **Typography**: Use large bold text for prices (text-4xl or text-5xl) to match Apple's emphasis on key specs
- **Sticky Header**: Implement with `position: sticky` and `top-0` - ensure z-index is appropriate to stay above content
- **Whitespace**: Apple uses generous padding/margin - use `p-6`, `p-8`, `gap-6`, `gap-8` for clean spacing
- **Icons**: Use Lucide React icons (Check, AlertTriangle, Minus, ExternalLink)
- **Responsive**: Horizontal scroll on mobile/tablet for comparison table, maintain column structure
- **Performance**: Use Next.js Image component for product images with proper sizing
- **Accessibility**: Ensure semantic HTML, ARIA labels, keyboard navigation, sufficient color contrast
- **Loading States**: Show skeleton loaders or spinners during API calls
- **Error Handling**: Display clear error messages for failed fetches, invalid inputs, or API errors
