# Chore: Fix Manual Comparison Page Display Issues

## Metadata
adw_id: `aadb3494`
prompt: `Fix Manual Comparison page: 1) Logo not displaying - In next.config.js, add '/expected/logo/**' to images.remotePatterns or copy logo files to public folder. Currently retailerLogo paths like '/expected/logo/thaiwatsau.png' don't work because Next.js only serves static files from /public. Either move expected/logo/*.png files to public/logos/ and update all logo paths in lib/constants/competitors.ts and app/api/comparison/manual/route.ts to use '/logos/*.png' format, OR configure next.config.js to serve from expected folder. 2) Reduce price font - In components/comparison/AppleStyleComparisonTable.tsx line 132 and components/comparison/PriceDifferenceDisplay.tsx line 22, change 'text-4xl' to 'text-2xl' to reduce the large price font size in the comparison table.`

## Chore Description
Fix two display issues on the Manual Comparison page:

1. **Logo Display Issue**: Retailer logos are not displaying because they reference `/expected/logo/*.png` paths, but Next.js only serves static files from the `/public` directory. The logo files exist in `expected/logo/` as PNG files, and there are already SVG versions in `public/logos/`. We need to copy the PNG files from `expected/logo/` to `public/logos/` and update all references to use the `/logos/*.png` path format.

2. **Price Font Size Issue**: The price display uses `text-4xl` (2.25rem/36px) which is too large. This needs to be reduced to `text-2xl` (1.5rem/24px) for better readability and layout balance in the comparison table.

## Relevant Files

### Files to Modify
- **lib/constants/competitors.ts** (lines 15, 23, 31, 39, 47) - Update logo paths from `/expected/logo/*.png` to `/logos/*.png` for all 5 competitors (HomePro, MegaHome, Boonthavorn, Global House, DoHome)
- **app/api/comparison/manual/route.ts** (line 199, 220) - Update Thai Watsadu logo path and ensure competitor logos use the updated paths from constants
- **components/comparison/AppleStyleComparisonTable.tsx** (line 132) - Change price font from `text-4xl` to `text-2xl`
- **components/comparison/PriceDifferenceDisplay.tsx** (line 22) - Change price font from `text-4xl` to `text-2xl`

### Directories Involved
- **expected/logo/** - Source directory containing PNG logo files (boonthavorn.png, dohome.png, globalhouse.png, homepro.png, megahome.png, thaiwatsau.png)
- **public/logos/** - Destination directory for logo files (already contains SVG versions, will receive PNG files)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Copy Logo Files from expected/logo to public/logos
- Copy all PNG logo files from `expected/logo/` to `public/logos/` directory
- Verify all 6 logo files are copied: boonthavorn.png, dohome.png, globalhouse.png, homepro.png, megahome.png, thaiwatsau.png

### 2. Update Logo Paths in lib/constants/competitors.ts
- Change HomePro logo path from `/expected/logo/homepro.png` to `/logos/homepro.png` (line 15)
- Change MegaHome logo path from `/expected/logo/megahome.png` to `/logos/megahome.png` (line 23)
- Change Boonthavorn logo path from `/expected/logo/boonthavorn.png` to `/logos/boonthavorn.png` (line 31)
- Change Global House logo path from `/expected/logo/globalhouse.png` to `/logos/globalhouse.png` (line 39)
- Change DoHome logo path from `/expected/logo/dohome.png` to `/logos/dohome.png` (line 47)

### 3. Update Thai Watsadu Logo Path in app/api/comparison/manual/route.ts
- Change Thai Watsadu logo path from `/expected/logo/thaiwatsau.png` to `/logos/thaiwatsau.png` (line 199)
- Verify that competitor logos on line 220 use `competitorInfo.logo` which references the updated paths from constants

### 4. Reduce Price Font Size in AppleStyleComparisonTable.tsx
- Change `text-4xl` to `text-2xl` in the Thai Watsadu price display (line 132)
- Verify the change maintains proper layout and readability

### 5. Reduce Price Font Size in PriceDifferenceDisplay.tsx
- Change `text-4xl` to `text-2xl` in the competitor price display (line 22)
- Ensure consistent font sizing across all price displays

### 6. Validate Changes
- Start the development server
- Navigate to the Manual Comparison page
- Verify all retailer logos display correctly
- Verify price font sizes are reduced and consistent
- Check that the layout is balanced and readable

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Verify logo files were copied
ls -la public/logos/*.png

# Type check the TypeScript changes
npm run type-check

# Lint the code
npm run lint

# Start development server to test visually
npm run dev
# Then navigate to http://localhost:3000/comparison in browser

# Verify no broken image references
grep -r "/expected/logo" lib/ app/ components/
# Should return no results if all paths updated correctly
```

## Notes
- The public/logos directory already contains SVG versions of logos; we're adding PNG versions alongside them
- Next.js serves files from the /public directory at the root path (e.g., /public/logos/homepro.png → /logos/homepro.png)
- The text-4xl (36px) → text-2xl (24px) change reduces font size by 33%, improving visual balance
- All changes are non-breaking and maintain existing functionality
- No next.config.js changes needed since we're using the standard /public directory approach
