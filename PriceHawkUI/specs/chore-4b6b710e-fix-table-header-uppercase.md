# Chore: Fix PriceComparisonTable Header Text to Uppercase

## Metadata
adw_id: `4b6b710e`
prompt: `Fix PriceComparisonTable.tsx header text to use uppercase as specified in the chore: Change 'Product Name' to 'PRODUCT NAME', 'Brand' to 'BRAND', 'Category' to 'CATEGORY', 'Status' to 'STATUS', 'Thai Watsadu' to 'THAI WATSADU', 'HomePro' to 'HOMEPRO', 'Global House' to 'GLOBAL HOUSE', 'Do Home' to 'DO HOME', and 'Boonthavorn' to 'BOONTHAVORN'. The headers should match the spec which requires all uppercase formatting for table column headers.`

## Chore Description

This is a simple text formatting fix to ensure all table column headers in the PriceComparisonTable component use consistent uppercase formatting as specified in the UI design specifications (chore-9eadd15a). Currently, some headers use mixed case (e.g., "Product Name", "Thai Watsadu") while the specification requires all headers to be fully uppercase for visual consistency and professional appearance.

The table headers that need to be changed from mixed case to uppercase are:
- "Product Name" → "PRODUCT NAME"
- "Brand" → "BRAND"
- "Category" → "CATEGORY"
- "Status" → "STATUS"
- "Thai Watsadu" → "THAI WATSADU"
- "HomePro" → "HOMEPRO"
- "Global House" → "GLOBAL HOUSE"
- "Do Home" → "DO HOME"
- "Boonthavorn" → "BOONTHAVORN"

Headers that are already uppercase (NO., SKU) do not need changes.

## Relevant Files

Use these files to complete the chore:

- `components/products/PriceComparisonTable.tsx` (lines 48-85) - Contains the table header (`<thead>`) section with all column header text that needs to be updated to uppercase. This is the only file that needs modification.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Table Headers to Uppercase
- Open `components/products/PriceComparisonTable.tsx`
- Locate the `<thead>` section (lines 49-85)
- Update line 58: Change "Product Name" to "PRODUCT NAME"
- Update line 61: Change "Brand" to "BRAND"
- Update line 64: Change "Category" to "CATEGORY"
- Update line 67: Change "Status" to "STATUS"
- Update line 70: Change "Thai Watsadu" to "THAI WATSADU"
- Update line 73: Change "HomePro" to "HOMEPRO"
- Update line 76: Change "Global House" to "GLOBAL HOUSE"
- Update line 79: Change "Do Home" to "DO HOME"
- Update line 82: Change "Boonthavorn" to "BOONTHAVORN"
- Verify that NO. and SKU headers remain unchanged (already uppercase)
- Ensure the `uppercase` CSS class remains on all `<th>` elements

### 2. Validate Changes
- Run type check to ensure no TypeScript errors: `npm run type-check`
- Run lint to ensure code quality: `npm run lint`
- Start the development server: `npm run dev`
- Navigate to http://localhost:3000/products
- Visually verify all table headers are displayed in uppercase
- Confirm the table layout and styling remain unchanged
- Check that the text is still readable and properly aligned

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check for TypeScript errors
npm run type-check

# Lint the code
npm run lint

# Build the application to ensure no build errors
npm run build

# Start development server and verify headers
npm run dev
# Open http://localhost:3000/products and verify:
# 1. All table column headers are in uppercase
# 2. Headers match the specification exactly
# 3. Table styling and layout are unchanged
```

## Notes

- This is a purely cosmetic change affecting only the header text strings
- No functional changes to the component logic or behavior
- The `uppercase` CSS class in the Tailwind classes already forces uppercase rendering, but the text content should also match for consistency and accessibility (screen readers)
- This change aligns with the design specification in chore-9eadd15a which requires all table headers to be uppercase for professional appearance
