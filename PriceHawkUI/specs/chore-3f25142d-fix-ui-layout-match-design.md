# Chore: Fix PriceHawk UI Layout to Match Design

## Metadata
adw_id: `3f25142d`
prompt: `Fix PriceHawk UI layout to match design: 1) Add 'No.' column as first column in PriceComparisonTable showing row numbers (1, 2, 3, etc.) 2) Update ProductSearchFilter layout to put Reset and Export buttons on the same row as the search input and dropdown selects - all elements should be in a single horizontal flex row with proper spacing 3) Wrap the Price Comparison table section in a white card container with shadow and rounded corners (bg-white rounded-lg shadow p-6) similar to the Search & Filter card`

## Chore Description
Update the PriceHawk UI to match the reference design shown in `expected/image.png`. The changes involve three layout improvements:

1. **Add 'No.' column**: The PriceComparisonTable already has a "No." column header and displays row numbers, but we need to verify it matches the design exactly
2. **Single-row filter layout**: Restructure ProductSearchFilter so all controls (search input, category dropdown, brand dropdown, Reset button, Export button) are in one horizontal flex row instead of having buttons on a separate row below
3. **Table card wrapper**: Wrap the Price Comparison table section in a white card container with shadow and rounded corners, matching the styling of the Search & Filter card above it

## Relevant Files
Use these files to complete the chore:

- `components/products/PriceComparisonTable.tsx` - Table component that already has "No." column implemented, needs verification
- `components/products/PriceComparisonRow.tsx` - Row component that already passes and displays rowNumber prop
- `components/products/ProductSearchFilter.tsx` - Filter component that needs layout restructure to put all controls in single row
- `app/(main)/products/page.tsx` - Main products page that needs to wrap table section in card container
- `expected/image.png` - Reference design showing desired layout

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Verify No. Column Implementation
- Review PriceComparisonTable.tsx to confirm "No." column is correctly implemented (line 52-53)
- Review PriceComparisonRow.tsx to confirm rowNumber display is correct (line 28)
- Compare with reference design to ensure alignment and styling match
- No changes needed if already correct

### 2. Restructure ProductSearchFilter Layout
- Update ProductSearchFilter.tsx to change from multi-row to single-row layout
- Modify the grid layout (currently `grid grid-cols-1 md:grid-cols-4`) to accommodate all 5 elements in one row
- Move Reset and Export buttons from separate div (lines 92-120) into the same flex row as search and dropdowns
- Adjust responsive breakpoints to maintain usability on smaller screens
- Update button spacing and alignment to match reference design
- Keep search input with icon on the left side
- Position category and brand dropdowns in the middle
- Place Reset and Export buttons on the right side

### 3. Wrap Price Comparison Section in Card Container
- Update app/(main)/products/page.tsx
- Locate the Price Comparison section (lines 108-121)
- Wrap the PriceComparisonTable component in a card container div
- Apply Tailwind classes: `bg-white rounded-lg shadow p-6`
- Move the "Price Comparison" h2 heading inside the card wrapper
- Ensure spacing between heading and table is appropriate
- Remove existing spacing/wrapper if any that conflicts with new card design

### 4. Test Responsive Behavior
- Verify layout works on desktop view (1920px width)
- Verify layout works on tablet view (768px width)
- Verify layout works on mobile view (375px width)
- Ensure horizontal scrolling works for table on smaller screens
- Confirm all buttons remain accessible and properly spaced

### 5. Validate Visual Consistency
- Compare final result with expected/image.png reference
- Verify card shadows and rounded corners match between Search & Filter and Price Comparison cards
- Confirm row numbers display correctly in "No." column
- Ensure all elements align properly in single-row filter layout
- Check that padding and spacing are consistent throughout

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check for TypeScript errors
npm run type-check

# Lint the code
npm run lint

# Build the application to catch any build errors
npm run build

# Start development server and manually verify UI matches expected/image.png
npm run dev
# Open http://localhost:3000/products in browser
# Compare with expected/image.png reference image
```

## Visual Validation Checklist
- [ ] "No." column appears as first column with row numbers (1, 2, 3, etc.)
- [ ] Search input, category dropdown, brand dropdown, Reset button, and Export button are in single horizontal row
- [ ] Price Comparison section is wrapped in white card with shadow and rounded corners
- [ ] Card styling matches Search & Filter card above it
- [ ] Layout is responsive and works on mobile/tablet/desktop
- [ ] No visual regressions or layout breaks

## Notes
- The "No." column is already implemented in PriceComparisonTable.tsx (line 52-53) and PriceComparisonRow.tsx (line 28), so task 1 is primarily verification
- The main work is in tasks 2 and 3: restructuring the filter layout and adding the card wrapper
- Reference design shows cyan/sky blue color scheme for primary buttons (Export) which is already implemented
- Maintain existing functionality (search debouncing, filtering, export) while updating layout
- The table already has `overflow-x-auto` for horizontal scrolling on small screens, preserve this behavior
