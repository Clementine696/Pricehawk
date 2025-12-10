# Chore: Remove Manual Comparison Button from Products Page

## Metadata
adw_id: `6a909ca4`
prompt: `Remove the Manual Comparison button from the Products page (app/(main)/products/page.tsx). This page should only display price information without any action buttons for manual comparison. The ManualComparisonButton component should not be rendered in the PriceComparisonTable or PriceComparisonRow on this page. Keep the Manual Comparison functionality available only on the dedicated Manual Comparison page.`

## Chore Description
The Products page (`app/(main)/products/page.tsx`) currently displays a Manual Comparison button in the `PriceComparisonRow` component when all competitor matches are marked as incorrect. This chore removes that button from the Products page while preserving the Manual Comparison functionality on the dedicated Manual Comparison page (`app/(main)/comparison/page.tsx`).

The button should be removed by:
1. Removing the conditional logic in `PriceComparisonRow` that shows the ManualComparisonButton
2. Always displaying the competitor price cells instead of conditionally replacing them with the button
3. Ensuring the import of `ManualComparisonButton` is removed from `PriceComparisonRow` if no longer used

## Relevant Files
Use these files to complete the chore:

- **components/products/PriceComparisonRow.tsx** (lines 5, 68, 112-116) - Contains the logic that conditionally renders the ManualComparisonButton when all competitor matches are marked as incorrect. Need to remove the import, the `areAllCompetitorMatchesIncorrect()` function, the `showManualComparisonButton` variable, and the conditional rendering logic.

- **app/(main)/products/page.tsx** - The Products page that uses PriceComparisonTable. No changes needed here, but should be reviewed to ensure the Manual Comparison button is no longer visible.

- **components/products/PriceComparisonTable.tsx** - Renders PriceComparisonRow components. No changes needed here.

- **app/(main)/comparison/page.tsx** - The dedicated Manual Comparison page where the button functionality should still be available. No changes needed here, just verification that it exists and works independently.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Remove ManualComparisonButton from PriceComparisonRow
- Remove the import statement for `ManualComparisonButton` from line 5
- Remove the `areAllCompetitorMatchesIncorrect()` function (lines 44-66)
- Remove the `showManualComparisonButton` variable assignment (line 68)
- Remove the conditional rendering logic (lines 112-116) that shows the Manual Comparison button
- Keep only the competitor price cells rendering block (lines 118-171)
- Ensure the competitor prices are always displayed regardless of validation status

### 2. Verify the Changes
- Read the modified `PriceComparisonRow.tsx` file to confirm all Manual Comparison button references are removed
- Verify that competitor price cells are always rendered
- Confirm that the component still properly handles the `validationStatuses` prop for hiding individual retailer prices

### 3. Test the Application
- Run type checking to ensure no TypeScript errors
- Start the development server to verify the Products page displays correctly without the Manual Comparison button
- Check that the comparison page still exists and is accessible at `/comparison`

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Start development server
npm run dev
```

Then manually verify:
1. Navigate to http://localhost:3000/products
2. Confirm that NO Manual Comparison buttons appear in the product rows
3. Confirm that all competitor price columns are always visible
4. Confirm that the `/comparison` page still exists and is accessible

## Notes
- The ManualComparisonButton component itself (`components/products/ManualComparisonButton.tsx`) should NOT be deleted as it may be used elsewhere (e.g., on the Manual Comparison page or Product Detail page)
- The validation logic for hiding individual retailer prices should remain intact - only the button rendering logic is being removed
- This change simplifies the Products page to be a pure data display without action buttons
