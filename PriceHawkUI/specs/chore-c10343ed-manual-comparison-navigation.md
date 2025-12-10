# Chore: Manual Comparison Navigation with Query Parameters

## Metadata
adw_id: `c10343ed`
prompt: `When clicking the Manual Comparison button on the Product Comparison Detail page (app/(main)/products/[id]/page.tsx), navigate to the Manual Comparison page (app/(main)/comparison/page.tsx) and pass the product SKU and Thai Watsadu URL as query parameters. The Manual Comparison page should read these query parameters and pre-fill the SKU field and Thai Watsadu URL field automatically when the page loads.`

## Chore Description
Currently, the Manual Comparison button navigates to the Manual Comparison page and passes the SKU and productId as query parameters. However, the button does not pass the Thai Watsadu URL, and the Manual Comparison page only pre-fills the SKU field but not the URL field.

This chore will:
1. Update the ManualComparisonButton component to include the Thai Watsadu URL in the query parameters
2. Update the Manual Comparison page to read the URL query parameter and pre-fill the Thai Watsadu URL field automatically when the page loads

## Relevant Files
Use these files to complete the chore:

- `components/products/ManualComparisonButton.tsx` - Button component that navigates to the Manual Comparison page. Need to add the Thai Watsadu URL to query parameters.
- `app/(main)/comparison/page.tsx` - Manual Comparison page that needs to read and pre-fill the Thai Watsadu URL from query parameters (currently only reads SKU at lines 96-112).
- `app/(main)/products/[id]/page.tsx` - Product detail page that uses the ManualComparisonButton component. Need to verify it passes the correct URL prop.
- `lib/types/price-comparison.ts` - Type definitions for understanding the ProductComparison structure and how to access the Thai Watsadu URL.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update ManualComparisonButton Component
- Modify the `ManualComparisonButtonProps` interface to include a `url` parameter for the Thai Watsadu product URL
- Update the `handleClick` function to include the URL in the query parameters when navigating
- Ensure the URL is properly encoded using `encodeURIComponent`

### 2. Update Product Detail Page to Pass URL
- In `app/(main)/products/[id]/page.tsx`, locate where the `ManualComparisonButton` is rendered (around line 398-401)
- Add the `url` prop to the ManualComparisonButton component
- Extract the Thai Watsadu URL from `data.product.prices[Retailer.THAI_WATSADU].productUrl`
- Handle the case where the URL might be null

### 3. Update Manual Comparison Page to Read URL Parameter
- In `app/(main)/comparison/page.tsx`, locate the `useEffect` hook that reads query parameters (lines 96-112)
- Add logic to read the `url` query parameter using `searchParams.get('url')`
- Pre-fill the `thaiWatsuduInput.url` field with the decoded URL value if present
- Ensure the URL is properly decoded

### 4. Validate the Implementation
- Test the navigation flow from Product Detail page to Manual Comparison page
- Verify that both SKU and URL fields are pre-filled correctly
- Ensure URL encoding/decoding works properly for special characters
- Check that the existing productId parameter still works

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check the TypeScript code
npm run type-check

# Lint the code for any issues
npm run lint

# Start the development server and test manually
npm run dev
# Then navigate to:
# 1. http://localhost:3000/products
# 2. Click on any product to go to detail page
# 3. Mark all products as incorrect (if needed) to show the Manual Comparison button
# 4. Click the "Manual Comparison" button
# 5. Verify that both SKU and Thai Watsadu URL fields are pre-filled on the Manual Comparison page
```

## Notes
- The Thai Watsadu URL is stored in `data.product.prices[Retailer.THAI_WATSADU].productUrl` and can be null, so we need to handle that case gracefully
- The Manual Comparison page already has the infrastructure to read query parameters via `useSearchParams()` hook
- Make sure to properly encode/decode URLs to handle special characters in query parameters
- The existing functionality for passing productId should remain intact
