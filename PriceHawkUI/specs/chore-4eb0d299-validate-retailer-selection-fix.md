# Chore: Validate CompetitorInputCard Retailer Selection Fix with Playwright MCP

## Metadata
adw_id: `4eb0d299`
prompt: `Use Playwright MCP to validate the CompetitorInputCard retailer selection fix on http://localhost:3000/comparison. Test steps: 1) Navigate to the comparison page, 2) Take a screenshot of the initial state showing the retailer grid (HomePro, MegaHome, Boonthavorn, Global House, DoHome buttons visible), 3) Click on the HomePro retailer button, 4) Take a screenshot after clicking - verify: the retailer grid is hidden, HomePro is shown as selected with blue brand color and logo, the Product URL input is enabled with placeholder 'https://www.homepro.co.th/...', and a 'Change' button appears, 5) Click the 'Change' button to verify the retailer grid reappears, 6) Select MegaHome retailer and verify it shows with green brand color. Save screenshots to .playwright-mcp/ folder with descriptive names like 'retailer-selection-before.png' and 'retailer-selection-after.png'. Report PASS if all validations succeed, FAIL with details if any step fails.`

## Chore Description

This chore validates the fix for the CompetitorInputCard retailer selection functionality using Playwright MCP automation. The fix (from chore f0f68c05) addressed an issue where clicking retailer buttons did not properly update the state and enable the Product URL input field.

**What This Chore Does:**
- Uses Playwright MCP to automate browser testing of the manual comparison page
- Validates that retailer selection works correctly after the fix
- Captures screenshots at key stages to provide visual proof of functionality
- Tests the full interaction flow: viewing retailer grid → selecting retailer → seeing selected state → changing retailer

**Expected Behavior to Validate:**
1. Initial state shows retailer selection grid with all 5 retailers visible
2. Clicking HomePro hides the grid and shows HomePro as selected with:
   - Blue brand color (#1E88E5)
   - HomePro logo visible
   - Product URL input enabled
   - Placeholder shows "https://www.homepro.co.th/..."
   - "Change" button appears
3. Clicking "Change" shows the retailer grid again
4. Selecting MegaHome shows it with green brand color (#43A047)

**Test Result:**
- **PASS**: All validations succeed and screenshots show correct behavior
- **FAIL**: Any validation fails with details about what went wrong

## Relevant Files

### Files to Reference (Read-Only)

- **components/comparison/CompetitorInputCard.tsx** - The component being validated. Contains retailer selection logic with visual feedback including:
  - Retailer grid display (lines 117-180)
  - Selected retailer display (lines 80-114)
  - Product URL input (lines 190-259)
  - State management with `showRetailerSelector` (line 33)

- **lib/constants/competitors.ts** - Defines competitor data including:
  - HomePro: color '#1E88E5' (blue), logo '/logos/homepro.svg'
  - MegaHome: color '#43A047' (green), logo '/logos/megahome.svg'
  - Other retailers: Boonthavorn, Global House, DoHome

- **app/(main)/comparison/page.tsx** - The comparison page component that uses CompetitorInputCard. Initial state shows one empty competitor card (lines 79-81).

- **.mcp/mcp.json** - Playwright MCP configuration file for running browser automation

### New Files

- **specs/chore-4eb0d299-validate-retailer-selection-fix.md** - This plan file
- **.playwright-mcp/retailer-selection-initial.png** - Screenshot of initial state with retailer grid
- **.playwright-mcp/retailer-selection-homepro-selected.png** - Screenshot after selecting HomePro
- **.playwright-mcp/retailer-selection-grid-reappeared.png** - Screenshot after clicking Change
- **.playwright-mcp/retailer-selection-megahome-selected.png** - Screenshot after selecting MegaHome
- **.playwright-mcp/validation-report-4eb0d299.txt** - Detailed validation report with PASS/FAIL result

## Step by Step Tasks

### 1. Start Development Server
- Verify the Next.js development server is running on port 3000
- If not running, start it with `npm run dev`
- Wait for the server to be ready before proceeding with tests

### 2. Navigate to Comparison Page
- Use Playwright MCP to navigate to `http://localhost:3000/comparison`
- Wait for the page to fully load
- Verify the page title contains "Manual Comparison"
- Verify the initial stage is "Input" (Stage 1)

### 3. Capture Initial State Screenshot
- Scroll to the "Competitor Products" section (section with numbered badge "2")
- Locate the first CompetitorInputCard component
- Verify the retailer selection grid is visible
- Take a full screenshot showing:
  - All 5 retailer buttons (HomePro, MegaHome, Boonthavorn, Global House, DoHome)
  - Each button displays retailer name, Thai name, and logo
  - The Product URL input appears disabled/grayed out
- Save screenshot as `.playwright-mcp/retailer-selection-initial.png`

### 4. Click HomePro Retailer Button
- Locate the HomePro button in the retailer grid
- Verify the button is clickable (not disabled)
- Click the HomePro button
- Wait for UI updates to complete

### 5. Verify HomePro Selection State
- Verify the retailer grid is now hidden
- Verify a selected retailer card is displayed showing:
  - HomePro logo visible
  - "HomePro" name displayed
  - Thai name "โฮมโปร" displayed
  - Blue brand color (#1E88E5 or rgb(30, 136, 229)) in border/background
  - "Change" text appears in the card
- Verify the Product URL input is now enabled (not disabled)
- Verify the placeholder text is "https://www.homepro.co.th/..."
- Take a screenshot showing the selected state
- Save screenshot as `.playwright-mcp/retailer-selection-homepro-selected.png`

### 6. Click Change Button to Reopen Retailer Grid
- Locate the "Change" button/text in the selected retailer card
- Click the button
- Wait for UI updates

### 7. Verify Retailer Grid Reappears
- Verify the retailer selection grid is visible again
- Verify all 5 retailer buttons are displayed
- Verify HomePro button shows as currently selected (with visual indicators)
- Take a screenshot
- Save screenshot as `.playwright-mcp/retailer-selection-grid-reappeared.png`

### 8. Select MegaHome Retailer
- Locate the MegaHome button in the retailer grid
- Verify the button is clickable
- Click the MegaHome button
- Wait for UI updates

### 9. Verify MegaHome Selection State
- Verify the retailer grid is now hidden
- Verify a selected retailer card is displayed showing:
  - MegaHome logo visible
  - "MegaHome" name displayed
  - Thai name "เมกาโฮม" displayed
  - Green brand color (#43A047 or rgb(67, 160, 71)) in border/background
  - "Change" text appears in the card
- Verify the Product URL input is enabled
- Verify the placeholder text is "https://www.megahome.co.th/..."
- Take a screenshot showing the MegaHome selected state
- Save screenshot as `.playwright-mcp/retailer-selection-megahome-selected.png`

### 10. Generate Validation Report
- Create a detailed validation report file
- Document each validation step with PASS/FAIL status
- Include details of any failures:
  - Expected vs actual behavior
  - Element states
  - Screenshots showing the issue
- Calculate overall result: PASS if all steps pass, FAIL if any step fails
- Save report as `.playwright-mcp/validation-report-4eb0d299.txt`

## Validation Commands

Execute these commands to complete the validation:

```bash
# Verify the development server is running
lsof -ti:3000

# If not running, start the dev server
npm run dev

# The Playwright MCP commands will be executed through Claude Code's MCP integration
# No manual Playwright commands needed - the agent will use the MCP server

# After validation, verify screenshots were created
ls -la .playwright-mcp/retailer-selection-*.png

# Review the validation report
cat .playwright-mcp/validation-report-4eb0d299.txt
```

## Notes

**Key Elements to Validate:**

1. **Retailer Grid State**
   - All 5 retailers displayed
   - Buttons are interactive
   - Visual layout matches design

2. **HomePro Selection**
   - Color: #1E88E5 (blue)
   - Logo: /logos/homepro.svg
   - Domain: homepro.co.th

3. **MegaHome Selection**
   - Color: #43A047 (green)
   - Logo: /logos/megahome.svg
   - Domain: megahome.co.th

4. **State Transitions**
   - Grid visible → Select → Grid hidden + Selected card shown
   - Selected card → Change → Grid visible again
   - Can switch between retailers

**Potential Issues to Watch For:**
- onClick handler not triggering
- State not updating (grid remains visible)
- URL input not enabling
- Brand colors not applying
- "Change" button not appearing
- Grid not reappearing when clicking "Change"

**Success Criteria:**
- All 9 validation steps pass
- Screenshots clearly show each state
- Brand colors match specifications
- UI transitions are smooth and complete
- No console errors during interaction

**Reference:**
This validation is based on the fix implemented in chore f0f68c05 which corrected the onClick handler in CompetitorInputCard.tsx to properly call `onRetailerChange(comp.id)` and `setShowRetailerSelector(false)`.
