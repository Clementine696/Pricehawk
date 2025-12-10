# Chore: Manual Comparison UI Design Adjustments

## Metadata
adw_id: `18cd112b`
prompt: `Adjust UI design for Manual Comparison page with the following changes:

  1. LOGO UPDATES - Update retailer logos in both Input stage (CompetitorInputCard) and Results stage to use PNG logos from
  'expected/logo/' folder:
     - HomePro: /expected/logo/homepro.png
     - MegaHome: /expected/logo/megahome.png
     - Boonthavorn: /expected/logo/boonthavorn.png
     - Global House: /expected/logo/globalhouse.png
     - DoHome: /expected/logo/dohome.png
     - Thai Watsadu: /expected/logo/thaiwatsau.png
     Update the logo paths in lib/constants/competitors.ts and ensure logos display correctly in retailer selection grid and
  results display.

  2. RESULTS PAGE CLEANUP - In the comparison results view:
     - Remove price difference display (e.g., '฿325 more expensive (+7.5%)' badge/text)
     - Remove pricing details section: discount percentage, unit price fields
     - Remove stock status/availability info but KEEP the product URL link
     - Ensure consistent font sizing across all elements on the page

  3. PAGE HEADER - Remove the subtitle text 'Compare products across retailers with Apple-style elegance' from the Manual
  Comparison page header in app/(main)/comparison/page.tsx

  Files to modify: lib/constants/competitors.ts, components/comparison/CompetitorInputCard.tsx,
  app/(main)/comparison/page.tsx, and any result display components showing price comparisons.`

## Chore Description

This chore focuses on cleaning up and improving the UI/UX of the Manual Comparison page by:

1. **Updating retailer logos** from SVG to PNG format using actual logo files located in `expected/logo/` directory
2. **Simplifying the comparison results** by removing unnecessary pricing details and status information while keeping essential product links
3. **Removing marketing text** from the page header to keep it clean and professional

The goal is to create a cleaner, more focused comparison interface that displays only essential information without overwhelming users with too many details.

## Relevant Files

### Files to Modify

- **lib/constants/competitors.ts** - Update logo paths from `/logos/*.svg` to `/expected/logo/*.png` for all 5 retailers (HOMEPRO, MEGA_HOME, BOONTHAVORN, GLOBAL_HOUSE, DOHOME)

- **components/comparison/CompetitorInputCard.tsx** - Already uses logos from constants, will automatically reflect changes after updating competitors.ts. Verify display quality with PNG logos.

- **components/comparison/ComparisonStickyHeader.tsx** - Displays retailer logos in the sticky header of results table. Will automatically use updated PNG logos from product data.

- **components/comparison/AppleStyleComparisonTable.tsx** - Main results display component. Need to:
  - Remove/replace PriceDifferenceDisplay usage (lines 150-155)
  - Remove "Pricing Details" section (lines 167-173) that shows discount and unit price
  - Modify "Availability" section to only show product URL, remove stock status

- **components/comparison/PriceDifferenceDisplay.tsx** - Currently displays price comparison badges with difference amount and percentage. Need to modify to show only the competitor price without the difference badge.

- **components/comparison/ComparisonSpecSection.tsx** - Used to render attribute sections. May need to modify or work with existing structure to hide specific attributes.

- **components/comparison/ComparisonAttributeRow.tsx** - Renders individual attribute rows. Already handles URL type correctly, should work fine for product links.

- **app/(main)/comparison/page.tsx** - Remove subtitle text from line 293-295

### Additional Files to Review

- **lib/utils/comparison-display-utils.ts** - Contains utility functions used by PriceDifferenceDisplay. May need review if we modify display logic.

- **components/comparison/RetailerCard.tsx** - Also displays logos, will automatically use updated PNG paths from constants.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Retailer Logo Paths in Constants
- Open `lib/constants/competitors.ts`
- Update logo paths for all 5 competitors:
  - HOMEPRO: Change from `/logos/homepro.svg` to `/expected/logo/homepro.png`
  - MEGA_HOME: Change from `/logos/megahome.svg` to `/expected/logo/megahome.png`
  - BOONTHAVORN: Change from `/logos/boonthavorn.svg` to `/expected/logo/boonthavorn.png`
  - GLOBAL_HOUSE: Change from `/logos/globalhouse.svg` to `/expected/logo/globalhouse.png`
  - DOHOME: Change from `/logos/dohome.svg` to `/expected/logo/dohome.png`
- Verify all PNG files exist in `/expected/logo/` directory (already confirmed: homepro.png, megahome.png, boonthavorn.png, globalhouse.png, dohome.png, thaiwatsau.png)

### 2. Remove Page Header Subtitle
- Open `app/(main)/comparison/page.tsx`
- Locate the page header section (lines 290-296)
- Remove the subtitle paragraph (lines 293-295): `<p className="mt-1 text-gray-600">Compare products across retailers with Apple-style elegance</p>`

### 3. Simplify Price Display in Results
- Open `components/comparison/PriceDifferenceDisplay.tsx`
- Modify the component to display only the competitor price without the price difference badge
- Remove or comment out the price comparison logic (amountDifference, percentageDifference, status calculations)
- Update the return statement to show only the large price display
- Ensure font size consistency (text-4xl for price as in Thai Watsadu column)

### 4. Remove Pricing Details Section
- Open `components/comparison/AppleStyleComparisonTable.tsx`
- Remove the "Pricing Details" section (lines 167-173) that renders discount percentage and unit price
- Remove the pricingAttributes array definition (lines 34-42) since it's no longer needed except for the main price row
- Keep the main "PRICE COMPARISON" section (lines 130-164) but with simplified price display

### 5. Simplify Availability Section
- In `components/comparison/AppleStyleComparisonTable.tsx`
- Modify the availabilityAttributes array (lines 57-61) to only include productUrl
- Remove stockStatus from the attributes array
- Rename section title from "Availability" to "Product Links" for clarity
- Verify that product URLs display correctly as clickable links (ComparisonAttributeRow handles 'url' type)

### 6. Ensure Consistent Font Sizing
- Review `components/comparison/AppleStyleComparisonTable.tsx` for font size consistency
- Verify that all price displays use text-4xl font-bold
- Check that section headers use consistent text-xs uppercase
- Ensure attribute labels and values use consistent text-sm sizing
- Review `components/comparison/ComparisonAttributeRow.tsx` for consistent text sizing

### 7. Visual Verification and Testing
- Start the development server with `npm run dev`
- Navigate to `/comparison` page
- Test the input stage: verify PNG logos display correctly in retailer selection grid
- Complete a comparison flow with at least 2 competitors
- Verify results display:
  - Logos appear correctly in sticky header
  - Price displays show only the amount without difference badges
  - No "Pricing Details" section appears
  - No stock status information appears
  - Product URL links are present and functional
  - All fonts are consistent in size
- Test responsiveness on different screen sizes
- Verify no console errors related to missing images or components

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Verify PNG logo files exist
ls -la expected/logo/*.png

# Type check to ensure no TypeScript errors
npm run type-check

# Lint code to check for any issues
npm run lint

# Start development server to test visually
npm run dev

# Navigate to http://localhost:3000/comparison and verify:
# - Logo paths are updated (check PNG images load)
# - Page subtitle is removed
# - Results page shows simplified pricing (no difference badges)
# - No "Pricing Details" section
# - No stock status information
# - Product links still work
# - Consistent font sizes throughout
```

## Notes

- All logo PNG files already exist in the `expected/logo/` directory
- The Thai Watsadu logo filename is `thaiwatsau.png` (note the spelling)
- Components using COMPETITORS constant will automatically pick up logo changes
- PriceDifferenceDisplay is only used in AppleStyleComparisonTable, so changes are localized
- ComparisonAttributeRow already handles URL type correctly, no changes needed there
- The availability section modification requires updating the attributes array definition
- Font consistency is critical for maintaining the Apple-style elegant design mentioned in the original requirements
