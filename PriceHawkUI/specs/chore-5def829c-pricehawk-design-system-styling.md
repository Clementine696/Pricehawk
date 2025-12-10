# Chore: Implement PriceHawk Design System Styling

## Metadata
adw_id: `5def829c`
prompt: `Implement frontend UI styling to match the PriceHawk design system from the style guide images. Apply the following theme: 1) Primary color: cyan/sky-blue (#0EA5E9) for brand, links, and active states 2) Background: light gray (#F8FAFC) for main content area 3) Sidebar: white background with cyan highlight for active menu item, dark text 4) Cards: white with subtle shadow and rounded corners 5) Status badges: green (#22C55E) for 'Cheapest', red (#EF4444) for 'Higher', gray (#6B7280) for 'Same' with white text and rounded-full style 6) Price cells: cyan colored text with external link icon 7) Table: clean design with light borders, header in gray text 8) Buttons: cyan filled for primary (Export), outline for secondary (Reset) 9) Search/Filter section: white card with search input, dropdown selects for Categories and Brands 10) Typography: clean sans-serif, dark gray for headings, medium gray for secondary text. Update tailwind.config.js with proper color palette and apply styles to all components including Sidebar, PriceComparisonTable, StatusBadge, PriceCell, ProductSearchFilter, and ExportButton.`

## Chore Description
Implement comprehensive UI styling to transform the PriceHawk application to match the design system shown in the reference images. This involves updating the Tailwind configuration with a custom color palette, then systematically applying the design system to all components including the sidebar navigation, product comparison table, status badges, price cells, search filters, and buttons. The goal is to achieve a cohesive, professional appearance with cyan (#0EA5E9) as the primary brand color, clean card-based layouts, and proper visual hierarchy through typography and spacing.

## Relevant Files

### Configuration Files
- `tailwind.config.js` - Define custom color palette (primary cyan, status colors, grays) and extend theme with custom values
- `app/globals.css` - Update base styles, add custom utilities if needed

### Layout Components
- `components/layout/Sidebar.tsx` - Apply white background, cyan active state (#0EA5E9), proper spacing and typography
- `components/layout/MainLayout.tsx` - Ensure light gray background (#F8FAFC) for main content area, white header

### Product Components
- `components/products/PriceComparisonTable.tsx` - Apply clean table design with light borders, gray header text, white background with shadow
- `components/products/PriceComparisonRow.tsx` - Ensure proper row styling and hover states
- `components/products/StatusBadge.tsx` - Update to use green (#22C55E), red (#EF4444), gray (#6B7280) with white text and rounded-full
- `components/products/PriceCell.tsx` - Apply cyan text color (#0EA5E9) for prices with external link icons
- `components/products/ProductSearchFilter.tsx` - Style as white card with search input, dropdowns, and action buttons
- `components/products/ExportButton.tsx` - Apply cyan filled button style with proper hover states

### Utility Files
- `lib/utils/price-utils.ts` - Update `getStatusColor()` function to return new color classes matching design system

### New Files
None - all changes are updates to existing files

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Tailwind Configuration
- Add custom color palette to `tailwind.config.js`:
  - Primary: `sky-500` (#0EA5E9) for brand color
  - Status colors: green-500 (#22C55E), red-500 (#EF4444), gray-500 (#6B7280)
  - Background: `gray-50` (#F8FAFC)
  - Semantic color names for consistency
- Extend theme with any additional spacing or border radius values needed

### 2. Update Global Styles
- Review `app/globals.css` to ensure base body background is `gray-50`
- Verify scrollbar styling aligns with design system
- Add any missing utility classes for consistent shadows and borders

### 3. Update Sidebar Component
- Apply white background (`bg-white`) to sidebar
- Update active menu item to use cyan background (`bg-sky-500`) with white text
- Ensure inactive items use dark gray text (`text-gray-700`) with hover state (`hover:bg-gray-100`)
- Update PriceHawk logo to use cyan color (`text-sky-500`)
- Verify spacing and typography matches design

### 4. Update Main Layout Component
- Ensure main content area has light gray background (`bg-gray-50`)
- Verify header has white background with proper border
- Update heading typography to use dark gray (`text-gray-900`)

### 5. Update Status Badge Component
- Modify `lib/utils/price-utils.ts` `getStatusColor()` function:
  - Cheapest: `bg-green-500 text-white` (#22C55E)
  - Higher: `bg-red-500 text-white` (#EF4444) - change from amber to red
  - Same: `bg-gray-500 text-white` (#6B7280)
  - Unavailable: keep as `bg-gray-300 text-gray-600`
- Ensure `StatusBadge.tsx` uses `rounded-full` class
- Verify proper padding and text sizing

### 6. Update Price Cell Component
- Change price link color to cyan (`text-sky-500`)
- Update hover state to use cyan underline
- Ensure external link icon is properly styled
- Keep green/red colors for lowest/highest indicators but update shades if needed

### 7. Update Price Comparison Table
- Apply white background with shadow (`bg-white rounded-lg shadow`)
- Update table header to use gray text (`text-gray-500`)
- Ensure light borders between rows (`divide-gray-200`)
- Verify clean, minimal table design with proper spacing
- Update loading and empty states to match design

### 8. Update Search Filter Component
- Ensure white card background with shadow and rounded corners
- Update search input with proper border and focus states (cyan ring)
- Style dropdown selects consistently
- Update Reset button to outline style with gray border
- Update Export button to cyan filled style (`bg-sky-500 hover:bg-sky-600`)
- Verify proper spacing and typography

### 9. Update Export Button Component
- Apply cyan background (`bg-sky-500`)
- Add cyan hover state (`hover:bg-sky-600`)
- Update focus ring to cyan (`focus:ring-sky-500`)
- Ensure disabled state has proper opacity

### 10. Update Typography Throughout
- Ensure headings use dark gray (`text-gray-900`) with proper font weights
- Secondary text uses medium gray (`text-gray-600`)
- Verify font sizes create proper visual hierarchy
- Check all components for consistent typography

### 11. Test Responsive Design
- Verify all styling works on desktop, tablet, and mobile
- Check that cyan colors are consistent across all breakpoints
- Ensure proper spacing and shadows on smaller screens

### 12. Validate Against Reference Images
- Compare rendered UI against `expected/image.png` reference
- Verify color accuracy (cyan, status badge colors)
- Check spacing, shadows, and overall visual consistency
- Make any final adjustments needed

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check to ensure no TypeScript errors
npm run type-check

# Lint code to check for style issues
npm run lint

# Build the application to verify no build errors
npm run build

# Start dev server and manually verify UI
npm run dev
# Open http://localhost:3000/products and compare with expected/image.png
```

## Manual Validation Checklist
After running the dev server, verify:
- [ ] Sidebar: White background, cyan active state, proper spacing
- [ ] Logo: Cyan colored "PriceHawk" text
- [ ] Main area: Light gray background (#F8FAFC)
- [ ] Search card: White with shadow, proper input and select styling
- [ ] Reset button: Gray outline style
- [ ] Export button: Cyan filled style
- [ ] Table: White background with shadow, light borders, gray headers
- [ ] Status badges: Green (Cheapest), Red (Higher), Gray (Same), all with white text and rounded-full
- [ ] Price links: Cyan colored with external link icon
- [ ] Typography: Dark headings, medium gray secondary text
- [ ] Overall: Matches design from expected/image.png

## Notes
- The primary brand color cyan (#0EA5E9) corresponds to Tailwind's `sky-500`
- Background gray (#F8FAFC) corresponds to Tailwind's `gray-50`
- Status badge colors have been updated: green-500 for Cheapest, red-500 for Higher (changed from amber), gray-500 for Same
- All changes should use Tailwind's built-in color utilities where possible for consistency
- Focus states should use cyan ring colors for interactive elements
- The design emphasizes clean, minimal aesthetics with proper use of white space and subtle shadows
