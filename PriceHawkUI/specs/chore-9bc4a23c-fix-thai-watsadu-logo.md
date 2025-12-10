# Chore: Fix missing Thai Watsadu logo in API response

## Metadata
adw_id: `9bc4a23c`
prompt: `Fix missing Thai Watsadu logo in API response: In app/api/comparison/manual/route.ts, update the generateComparisonTableData function to add retailerLogo: '/expected/logo/thaiwatsau.png' to the thaiWatsuduProduct object (around line 198, after stockStatus)`

## Chore Description
The Thai Watsadu product object in the comparison table data response is missing the `retailerLogo` field. This field needs to be added to ensure consistency with competitor products, which already include retailer logos. The logo path should point to `/expected/logo/thaiwatsau.png` (note: the existing file is named `thaiwatsau.png`, not `thaiwatsadu.png`).

## Relevant Files
Use these files to complete the chore:

- **app/api/comparison/manual/route.ts** (line ~186-199): Contains the `generateComparisonTableData` function that creates the Thai Watsadu product object for Apple-style comparison responses. The `retailerLogo` field needs to be added to the `thaiWatsuduProduct` object.
- **expected/logo/thaiwatsau.png**: The logo file exists and will be referenced in the API response.
- **lib/constants/competitors.ts**: Reference file showing the logo path pattern used for competitors (e.g., `/expected/logo/homepro.png`).

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add retailerLogo field to thaiWatsuduProduct object
- Open `app/api/comparison/manual/route.ts`
- Locate the `generateComparisonTableData` function (around line 181)
- Find the `thaiWatsuduProduct` object definition (around line 187-199)
- Add the `retailerLogo: '/expected/logo/thaiwatsau.png'` field after the `stockStatus` field (line 197)
- Ensure the field is added with proper TypeScript syntax and matches the pattern used in competitor products (line 219)

### 2. Verify the change
- Review the modified code to ensure the field is properly added
- Confirm the logo path matches the actual file path (`/expected/logo/thaiwatsau.png`)
- Ensure consistency with how competitor products include the `retailerLogo` field

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check to ensure TypeScript types are correct
npm run type-check

# Build the application to verify no compilation errors
npm run build

# Optional: Start dev server to test the API endpoint
npm run dev
# Then test: POST http://localhost:3000/api/comparison/manual with V3 request format
```

## Notes
- The logo file is named `thaiwatsau.png` (not `thaiwatsadu.png`), which is the correct spelling to use
- Competitor products already include the `retailerLogo` field (line 219), so this change creates consistency
- The V3 (Apple-style) comparison flow is the only code path affected by this change
- The `retailer` field for Thai Watsadu is set to `'THAI_WATSADU'` (line 198), but there's no corresponding entry in the `COMPETITORS` constant for Thai Watsadu
