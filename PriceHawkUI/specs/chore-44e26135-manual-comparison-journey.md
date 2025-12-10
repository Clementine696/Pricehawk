# Chore: Implement Manual Product Comparison Journey with Two-Sided Input Flow

## Metadata
adw_id: `44e26135`
prompt: `Implement Manual Product Comparison Journey with two-sided input flow. Customer Journey Overview (from wireframe): The flow has 4 main stages: 1. Side A (Thai Watsadu Input) - Red header card with SKU and URL fields 2. Retailer Selection - List to select from: HomePro, MegaHome, Boonthavorn, Global House, DoHome 3. Side B (Competitor Inputs) - For each selected retailer, input URL(s) 4. User Validation - Display results showing Match/Not Match with percentages, plus Retry and Confirm buttons`

## Chore Description
Implement a new manual product comparison journey with a four-stage two-sided input flow:

1. **Side A (Thai Watsadu Input)**: A card with red header (#DC2626) containing required SKU and URL input fields
2. **Retailer Selection**: A list allowing users to select from 5 competitors (HomePro, MegaHome, Boonthavorn, Global House, DoHome)
3. **Side B (Competitor Inputs)**: For each selected retailer, display a colored card with URL input field(s) and ability to add multiple URLs
4. **User Validation**: Display comparison results grouped by competitor showing match/not-match counts with confidence percentages, plus Retry and Confirm buttons

The UI layout flow should be:
- Left side: Thai Watsadu card (red header) -> Arrow -> Retailer selection list
- Right side: Selected competitor cards (colored headers) -> Arrow -> User Validation panel
- Final actions: Retry (outline button) and Confirm (solid dark button) at bottom

## Relevant Files
Use these files to complete the chore:

### Existing Files to Update
- **`/app/(main)/comparison/page.tsx`**: Main comparison page - needs to be rewritten to implement the new 4-stage flow with proper state management
- **`/lib/types/manual-comparison.ts`**: Already has the V2 types (ThaiWatsuduInput, CompetitorUrlEntry, ManualComparisonInputV2) - may need minor updates
- **`/lib/constants/competitors.ts`**: Already has color properties and THAI_WATSADU_COLOR constant - no changes needed
- **`/app/api/comparison/manual/route.ts`**: Needs to support ManualComparisonRequestV2 format and generate mock results with matchCount/notMatchCount
- **`/components/comparison/index.ts`**: Needs to export the new components (ThaiWatsuduInputCard, RetailerSelector, CompetitorInputCard, UserValidationPanel)

### Existing Components (Already Created)
- **`/components/comparison/ThaiWatsuduInputCard.tsx`**: Already exists with red header, SKU and URL inputs - no changes needed
- **`/components/comparison/RetailerSelector.tsx`**: Already exists with retailer list - no changes needed
- **`/components/comparison/CompetitorInputCard.tsx`**: Already exists with colored header and multi-URL support - no changes needed
- **`/components/comparison/UserValidationPanel.tsx`**: Already exists with match/not-match display and Retry/Confirm buttons - no changes needed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update API Route to Support V2 Format
- Open `/app/api/comparison/manual/route.ts`
- Import `ManualComparisonRequestV2` and `CompetitorUrlEntry` types
- Add a new function `generateMockResultsV2()` that:
  - Takes `CompetitorUrlEntry[]` and generates results with `urlResults`, `matchCount`, and `notMatchCount`
  - For each competitor entry, simulate results for each URL
  - Calculate aggregate match/not-match counts
- Update the POST handler to detect V2 format (check for `thaiWatsadu` and `competitors` array with `urls` property)
- Return results compatible with UserValidationPanel display

### 2. Update Component Exports
- Open `/components/comparison/index.ts`
- Add exports for:
  - `ThaiWatsuduInputCard`
  - `RetailerSelector`
  - `CompetitorInputCard`
  - `UserValidationPanel`

### 3. Rewrite Comparison Page for 4-Stage Flow
- Open `/app/(main)/comparison/page.tsx`
- Define a `ComparisonStage` type: `'input' | 'selecting' | 'competitor_urls' | 'validation'`
- Add state for:
  - `stage`: Current stage in the flow
  - `thaiWatsuduInput`: ThaiWatsuduInput object
  - `selectedRetailers`: CompetitorRetailer[]
  - `competitorEntries`: CompetitorUrlEntry[]
  - `results`: CompetitorMatchResult[]
  - `isSubmitting`: boolean
  - `errors`: Validation error messages
- Implement stage navigation:
  - Stage 1 (input): Show ThaiWatsuduInputCard with "Next" button
  - Stage 2 (selecting): Show RetailerSelector with "Back" and "Next" buttons
  - Stage 3 (competitor_urls): Show CompetitorInputCard for each selected retailer with "Back" and "Compare" buttons
  - Stage 4 (validation): Show UserValidationPanel with results
- Implement validation logic:
  - Thai Watsadu SKU and URL are required
  - At least one retailer must be selected
  - Each competitor must have at least one valid URL
- Create layout with left/right flow using grid or flexbox:
  - Left column: Thai Watsadu input + arrow + Retailer selection
  - Right column: Competitor inputs + arrow + Validation panel
- Handle API submission using V2 format
- Implement Retry (re-run comparison) and Confirm (finalize results) handlers

### 4. Validate the Implementation
- Run `npm run type-check` to ensure no TypeScript errors
- Run `npm run lint` to check for linting issues
- Run `npm run dev` and test the flow manually:
  - Enter SKU and URL in Thai Watsadu card
  - Select retailers from the list
  - Enter URLs for each selected competitor
  - Submit and verify results display correctly
  - Test Retry and Confirm buttons

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Build (ensures no build errors)
npm run build

# Start dev server and manually test the flow
npm run dev
# Navigate to http://localhost:3000/comparison
```

## Notes
- The existing components (ThaiWatsuduInputCard, RetailerSelector, CompetitorInputCard, UserValidationPanel) are already implemented and follow the wireframe design
- The lib/constants/competitors.ts already has all competitor colors defined
- The lib/types/manual-comparison.ts already has all V2 types defined
- The main work is in the comparison page.tsx to implement the 4-stage flow and the API route to support V2 format
- Use existing Tailwind CSS patterns from the codebase for consistency
- The arrow icons should use `lucide-react` ArrowRight component with amber/orange color (#F59E0B or text-amber-500)
