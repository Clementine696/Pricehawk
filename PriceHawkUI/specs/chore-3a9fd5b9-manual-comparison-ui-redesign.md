# Chore: Manual Comparison Page UI Redesign

## Metadata
adw_id: `3a9fd5b9`
prompt: `Adjust the Manual Comparison page UI/layout based on the expected design in '/Users/naruechon/Documents/Project/PriceHack/expected/Untitled (14)'`

## Chore Description
Redesign the Manual Comparison page UI to match the expected Figma design. This involves updating 6 components to achieve a cleaner, more modern design with consistent cyan/teal color scheme, improved stage indicator, redesigned input cards, streamlined review panel, and horizontal Apple-style comparison table.

Key design changes:
1. **StageIndicator**: Use cyan circles for all steps (not red), with proper labels
2. **Stage 1 Input**: Cyan step badges, red Thai Watsadu header, competitor cards with 2-column retailer grid
3. **Stage 2 Review**: Remove CollapsibleStepCard, use centered layout with status card
4. **Stage 3 Results**: Horizontal table with retailer logo header row, product images, price comparison section

## Relevant Files
Use these files to complete the chore:

- **components/comparison/StageIndicator.tsx** - Update step circle colors from red to cyan, change labels to match design
- **app/(main)/comparison/page.tsx** - Update step badges from red (1) to cyan, adjust layout structure for all stages
- **components/comparison/ThaiWatsuduInputCard.tsx** - Already matches design with red header, minor placeholder/helper text updates
- **components/comparison/CompetitorInputCard.tsx** - Update header to show "Competitor" with X button, ensure 2-column retailer grid, update URL placeholder
- **components/comparison/ReviewConfirmPanel.tsx** - Redesign to remove dependency on CollapsibleStepCard, use new centered layout with status card
- **components/comparison/AppleStyleComparisonTable.tsx** - Update to horizontal layout with retailer logos in header row, section headers for PRICE COMPARISON and PRODUCT INFORMATION
- **components/comparison/ComparisonStickyHeader.tsx** - Update header row to show retailer logos centered (not product images in header)
- **lib/constants/competitors.ts** - Reference file for retailer colors and logos (no changes needed)

### Reference Files (Read Only)
- **expected/Untitled (14)/Frame 7.png** - Stage 1 Input design (Thai Watsadu card, competitor selector)
- **expected/Untitled (14)/Frame 8.png** - Stage 1 Input design (multiple competitors, Add button, Next button)
- **expected/Untitled (14)/Frame 9.png** - Stage 2 Review design (centered layout, status card, summary cards)
- **expected/Untitled (14)/Frame 10.png** - Stage 2 Review design (alternative view)
- **expected/Untitled (14)/Frame 11.png** - Stage 3 Results design (horizontal comparison table)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update StageIndicator Component
- Change step 1 circle color from any special styling to consistent cyan (`bg-cyan-500`)
- Active step: solid cyan background with white number (already correct)
- Completed step: cyan background with white checkmark (already correct)
- Inactive step: gray background (already correct)
- Update STAGES_V3 labels:
  - `label: 'Input'` stays, but `description: 'Enter product details'` (already matches)
  - `label: 'Review'` stays, but `description: 'Confirm your inputs'` (already matches)
  - `label: 'Results'` stays, but `description: 'View comparison'` (already matches)
- Remove the `animate-pulse` class from active step to match cleaner design
- Ensure step labels show in cyan when active (label + description both cyan)

### 2. Update comparison/page.tsx Stage 1 Layout
- Change step 1 badge from `bg-red-500` to `bg-cyan-500` for consistency
- Step 2 badge already uses `bg-cyan-500` (keep as is)
- Update section heading text to match design:
  - "Thai Watsadu Product" with description "Enter the details of the product you want to compare from Thai Watsadu"
  - "Competitor Products" with description "Add up to 5 competitor products to compare against"
- Ensure Add Competitor button shows count as "(X/5)" format
- Next button text should be "Next: Review →" with cyan gradient styling

### 3. Update ThaiWatsuduInputCard Component
- Verify red header bar styling matches design (already has red header)
- Verify cart icon is present in header (using Image component with logo)
- Verify header text shows "Thai Watsadu (Source Product)" in white (already matches)
- Verify SKU placeholder is "e.g., TW-12345-ABC" (already matches)
- Verify SKU helper text is "Enter the unique product identifier from Thai Watsadu" (already matches)
- Verify URL placeholder is "https://www.thaiwatsadu.com/..." (already matches)
- Verify URL helper text is "Copy and paste the full URL from your browser address bar" (already matches)

### 4. Update CompetitorInputCard Component
- Update header to show "Competitor" text (without retailer name when none selected)
- Keep X close button on right side of header
- Ensure "Select Retailer *" label has info icon tooltip
- Verify retailer selector shows as 2-column grid with:
  - Logo + Name + Thai name for each retailer
  - HomePro/โฮมโปร, MegaHome/เมกาโฮม, Boonthavorn/บุญถาวร, Global House/โกลบอลเฮ้าส์, DoHome/ดูโฮม
- Add helper text "Choose a retailer to compare products from" below retailer grid
- Update Product URL placeholder to "Select a retailer first" when no retailer is selected (already implemented)
- Remove the colored left border styling and use simpler card design with just gray border

### 5. Update comparison/page.tsx Stage 2 (Review)
- Remove the CollapsibleStepCard usage from Stage 2
- Replace with direct ReviewConfirmPanel component that handles entire review layout
- Pass necessary props to ReviewConfirmPanel (thaiWatsuduInput, competitorEntries, onEdit, onConfirm)

### 6. Redesign ReviewConfirmPanel Component
- Remove any CollapsibleStepCard dependencies
- Create new centered layout structure:
  - Centered heading "Review Your Comparison" (already exists)
  - Subtitle "Verify all details before proceeding with the comparison" (already exists)
- Status card design:
  - Light green/teal background (`bg-gradient-to-br from-cyan-50 to-teal-50`)
  - White checkmark icon in cyan circle
  - "Ready to Compare" title
  - Subtitle "X Thai Watsadu product vs Y competitor(s)"
- Thai Watsadu summary card:
  - Red header with cart icon + "Thai Watsadu" title + "Source Product" subtitle (already implemented)
  - White body showing SKU in gray badge and URL as cyan link with external icon (already implemented)
- Competitor Products section:
  - Card header "Competitor Products (X)" + subtitle "Comparing against these retailers"
  - Each competitor: number badge (cyan circle), retailer logo, name + Thai name, URL link
- Bottom action buttons:
  - "← Back to Edit" - outline style, left aligned
  - "✓ Confirm & Compare" - solid cyan gradient, right aligned

### 7. Update AppleStyleComparisonTable Component
- Restructure to horizontal table layout with retailer columns
- Update ComparisonStickyHeader to show:
  - First column: "Compare" label
  - Subsequent columns: Retailer logos centered (Thai Watsadu first, then competitors)
- Add "Compare" row below header showing product images for each retailer
- Add "PRICE COMPARISON" section header (uppercase, gray text)
- "Price" row: Large prices in Thai Baht format (฿X,XXX)
- Add "PRODUCT INFORMATION" section header (uppercase, gray text)
- Rows for: Product Name, SKU, Brand (with checkmark if matching), Category (with checkmark if matching)
- "Product Link" row with "View Product" cyan links + external icon

### 8. Update ComparisonStickyHeader Component
- Restructure header to show retailer logos in each column header (not product images)
- First column should show "Compare" text
- Thai Watsadu column: Show Thai Watsadu logo centered
- Competitor columns: Show each competitor's logo centered
- Remove product images from header (move to "Compare" row in table body)

### 9. Run Validation and Fix Any Issues
- Run `npm run type-check` to verify TypeScript types
- Run `npm run lint` to check for linting errors
- Run `npm run build` to ensure production build succeeds
- Test the UI manually in development server (`npm run dev`)

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build

# Start dev server and manually test all 3 stages
npm run dev
# Then navigate to http://localhost:3000/comparison and test:
# 1. Stage 1: Verify cyan step badges, Thai Watsadu card, competitor cards
# 2. Stage 2: Verify centered review layout, status card, summary cards
# 3. Stage 3: Verify horizontal table with retailer logos, price comparison
```

## Notes
- The design reference images show a clean, modern UI with consistent cyan/teal color scheme
- Thai Watsadu branding uses red (`#DC2626`) which should be preserved in source product cards
- Competitor cards should use the competitor's brand color for accents
- The horizontal comparison table in Stage 3 is the key visual change - it shows all retailers side-by-side with their logos in the header row
- Ensure responsive design works on mobile (the images show desktop design but components should scale down gracefully)
- The "Add Competitor" button has a dashed cyan border with light cyan gradient background
- Stage indicator should use pure cyan circles without the red color for step 1
