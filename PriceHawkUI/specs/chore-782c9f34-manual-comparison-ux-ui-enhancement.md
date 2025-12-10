# Chore: Manual Comparison Page UX/UI Enhancement

## Metadata
adw_id: `782c9f34`
prompt: `Enhance Manual Comparison page UX/UI for better usability: 1) Simplify the wizard to a cleaner single-column flow with collapsible completed steps instead of 2-column grid layout. 2) Replace plain text retailer buttons with styled cards showing retailer logos/icons, making selection more visual and scannable. 3) Improve the StageIndicator component to show clearer progress with checkmarks, active state highlighting, and step descriptions. 4) Redesign UserValidationPanel to clearly explain match status - replace confusing '1 URL Not Match 0%' with friendly icons, color-coded status (green=match, red=no match, yellow=partial), and clear action guidance. 5) Add a comparison summary card before the Compare button showing Thai Watsadu product info alongside selected competitor retailers. 6) Improve visual hierarchy with distinct card styling for source product (Thai Watsadu) vs competitor inputs using different border colors or background shades. 7) Make 'Add another URL' button more prominent with better styling. 8) Add helpful tooltips or inline hints explaining what each step requires. Keep existing 4-stage flow logic (input → selecting → competitor_urls → validation) but improve the visual presentation and user guidance throughout the journey.`

## Chore Description

This chore focuses on enhancing the Manual Comparison page UX/UI to provide better visual guidance, clarity, and usability throughout the 4-stage comparison journey. The current implementation uses a 2-column grid layout that can be confusing, plain text buttons that lack visual appeal, and validation messages that are unclear. This enhancement will transform the page into a clean, single-column wizard with collapsible steps, visual retailer cards, improved progress indicators, clear status messaging, and helpful guidance at each step.

## Relevant Files

### Existing Files to Modify

- **`app/(main)/comparison/page.tsx`** - Main comparison page component with 4-stage flow (input → selecting → competitor_urls → validation). Need to refactor from 2-column grid to single-column flow with collapsible completed steps.

- **`components/comparison/StageIndicator.tsx`** - Progress indicator showing 4 stages. Enhance with better active state highlighting, checkmarks for completed steps, and descriptive step labels.

- **`components/comparison/RetailerSelector.tsx`** - Retailer selection buttons. Replace plain text buttons with styled cards showing retailer logos/icons and brand colors.

- **`components/comparison/UserValidationPanel.tsx`** - Validation results display. Redesign to show clear match status with icons, color-coded badges (green=match, red=no match, yellow=partial), and friendly messaging instead of confusing "1 URL Not Match 0%".

- **`components/comparison/ThaiWatsuduInputCard.tsx`** - Thai Watsadu input card. Enhance visual hierarchy with distinct border colors or background shades to differentiate from competitor cards.

- **`components/comparison/CompetitorInputCard.tsx`** - Competitor URL input cards. Improve 'Add another URL' button styling and add inline hints. Enhance visual styling to contrast with Thai Watsadu card.

- **`lib/constants/competitors.ts`** - Competitor configuration. May need to add logo/icon paths for visual cards.

### New Files

#### New Components

- **`components/comparison/ComparisonSummaryCard.tsx`** - New summary card component to display before the Compare button, showing Thai Watsadu product info alongside selected competitor retailers for final review.

- **`components/comparison/StepCard.tsx`** - New reusable wrapper component for collapsible step cards in the wizard flow, managing expanded/collapsed states.

- **`components/comparison/RetailerCard.tsx`** - New visual retailer card component with logo/icon, brand colors, and hover states for better selection UX.

- **`components/ui/Tooltip.tsx`** - New tooltip component for inline hints and step explanations throughout the wizard.

#### Assets

- **`public/logos/homepro.svg`** - HomePro retailer logo (to be added)
- **`public/logos/megahome.svg`** - MegaHome retailer logo (to be added)
- **`public/logos/boonthavorn.svg`** - Boonthavorn retailer logo (to be added)
- **`public/logos/globalhouse.svg`** - Global House retailer logo (to be added)
- **`public/logos/dohome.svg`** - DoHome retailer logo (to be added)
- **`public/logos/thaiwatsadu.svg`** - Thai Watsadu logo (to be added)

Note: Logo files should be sourced from official retailer websites or created as simple brand-colored icons.

## Step by Step Tasks

### 1. Create Tooltip Component for Inline Hints
- Create `components/ui/Tooltip.tsx` with hover/click trigger support
- Use Lucide icons (HelpCircle, Info) for tooltip triggers
- Implement with absolute positioning and z-index management
- Add fade-in/fade-out animations for smooth UX
- Support both light and dark tooltip styles
- Make it keyboard accessible (focus states)

### 2. Create Retailer Logo Assets
- Create or source SVG logo files for all 5 competitors
- Add Thai Watsadu logo SVG
- Place in `public/logos/` directory with consistent naming
- Ensure SVGs are optimized and use brand colors
- Create fallback icon component using Lucide icons if logos unavailable
- Update `lib/constants/competitors.ts` to include logo paths

### 3. Create RetailerCard Component
- Create `components/comparison/RetailerCard.tsx` for visual retailer selection
- Display retailer logo/icon prominently (48x48px or similar)
- Show retailer name with brand color accent
- Add hover states with subtle elevation and border color change
- Show checkmark icon when selected (top-right corner)
- Use card-based layout with padding, border-radius, and shadow
- Make entire card clickable with good touch targets (min 44x44px)
- Add disabled state styling with opacity reduction

### 4. Update RetailerSelector Component
- Replace plain text buttons with RetailerCard components
- Arrange cards in a responsive grid (2 columns on mobile, 3-4 on desktop)
- Add "Select at least one retailer" hint with Tooltip
- Improve spacing between cards (gap-3 or gap-4)
- Add visual feedback for multi-select (show count badge)
- Ensure cards are keyboard navigable (Tab key support)

### 5. Enhance StageIndicator Component
- Make stage circles larger and more prominent (12x12 or 14x14)
- Add bold active state with scale animation (scale-110)
- Improve completed state with filled checkmark circle
- Add step descriptions below stage labels (e.g., "Enter Thai Watsadu details")
- Use gradient or stronger color for active stage (cyan-500 to cyan-600)
- Add connecting lines with animated fill on completion
- Improve mobile responsiveness (stack vertically on small screens)
- Add transition animations between stages (300ms ease)

### 6. Create StepCard Component
- Create `components/comparison/StepCard.tsx` for collapsible step wrapper
- Accept props: title, stepNumber, isActive, isCompleted, children
- Implement expand/collapse animation with smooth height transition
- Show compact header when collapsed (step number + title + checkmark)
- Show full content when expanded (isActive or user clicks to expand)
- Add expand/collapse icon (ChevronDown/ChevronUp)
- Use distinct border colors: cyan-500 for active, green-500 for completed, gray-300 for pending
- Add subtle background color for active state (cyan-50)

### 7. Create ComparisonSummaryCard Component
- Create `components/comparison/ComparisonSummaryCard.tsx`
- Display Thai Watsadu product info: SKU, URL preview (truncated)
- Show selected competitor retailers with icons/logos in a horizontal list
- Display count summary (e.g., "Comparing with 3 retailers")
- Use card layout with border and padding
- Add edit icon/button to go back and modify inputs
- Style with subtle background (gray-50) to differentiate from input cards
- Show total URLs to be compared (sum of all competitor URL fields)

### 8. Redesign UserValidationPanel
- Replace confusing "1 URL Not Match 0%" text with clear status messages
- Add status icons: CheckCircle (green) for match, XCircle (red) for no match, AlertCircle (yellow) for partial
- Use color-coded badges for status: green-100 bg with green-800 text for match, etc.
- Show match results as "✓ Match found (95% confidence)" instead of percentages alone
- Show not-match results as "✗ No match found" with helpful action text
- Add partial match status for multi-URL scenarios (e.g., "2 of 3 URLs matched")
- Group results by status (all matches first, then partials, then no-matches)
- Add clear action guidance: "Review matches below" or "Try different URLs"
- Improve button layout with primary/secondary styling (Confirm = primary, Retry = secondary)

### 9. Refactor Main Comparison Page Layout
- Change from 2-column grid to single-column flow (max-w-3xl centered)
- Wrap each stage in StepCard component with collapsible behavior
- Stage 1 (Input): Thai Watsadu input with tooltip "Enter the SKU and URL from Thai Watsadu"
- Stage 2 (Selecting): Retailer selection with tooltip "Choose competitors to compare against"
- Stage 3 (Competitor URLs): Competitor URL inputs with tooltip "Enter product URLs from selected retailers"
- Stage 4 (Validation): Results validation panel
- Auto-collapse completed steps (opacity-60, collapsed height)
- Allow users to click collapsed step headers to expand and edit
- Add smooth scroll to active step when transitioning
- Keep StageIndicator at top, always visible (sticky positioning optional)

### 10. Enhance Thai Watsadu Input Card Styling
- Add distinct border color (red-500 or red-600) to match Thai Watsadu brand
- Use subtle background shade (red-50) for visual differentiation
- Add Thai Watsadu logo/icon in header if available
- Increase header padding for better prominence
- Add tooltip to SKU field: "Product SKU from Thai Watsadu"
- Add tooltip to URL field: "Full product page URL from Thai Watsadu website"
- Improve input field styling with better focus states

### 11. Enhance Competitor Input Card Styling
- Use competitor brand colors for left border accent (4px border-l)
- Keep white background but add subtle hover shadow
- Add competitor logo/icon in header next to name
- Make 'Add another URL' button more prominent with icon (Plus) and cyan color
- Style as outlined button with hover fill effect
- Add tooltip to URL fields: "Product URL from [Retailer Name] website"
- Improve remove button (X) visibility with hover state
- Add URL count indicator (e.g., "2 URLs added")

### 12. Add Comparison Summary Before Compare Button
- Insert ComparisonSummaryCard component before Compare button in Stage 3
- Position between competitor inputs and action buttons
- Show summary of what will be compared
- Add visual separator (border-t with margin) above and below
- Include helpful text: "Review your comparison setup before proceeding"
- Make summary card collapsible for power users

### 13. Improve Button Hierarchy and Actions
- Use consistent button styling: primary (cyan-500), secondary (gray-300), danger (red-500)
- Make 'Next' and 'Compare' buttons larger and more prominent (px-8 py-3)
- Add loading states to Compare button with Loader2 icon
- Improve Back button with ChevronLeft icon and subtle styling
- Add keyboard shortcuts hints (Enter to continue, Esc to go back)
- Ensure buttons are always visible (sticky bottom bar on mobile optional)
- Improve disabled states with tooltip explaining why disabled

### 14. Add Responsive Design Improvements
- Ensure single-column layout works well on mobile (320px+)
- Stack StageIndicator vertically on small screens
- Make retailer cards full-width on mobile, grid on tablet/desktop
- Ensure competitor input cards are scrollable on small screens
- Add touch-friendly spacing (min 44x44 tap targets)
- Test on various screen sizes (mobile, tablet, desktop)
- Ensure tooltips don't overflow viewport on mobile

### 15. Validate and Test Complete Flow
- Test entire 4-stage flow end-to-end
- Verify collapsible steps work correctly
- Confirm tooltips display properly on hover/focus
- Test retailer card selection with multi-select
- Verify summary card shows correct information
- Test validation panel with different match scenarios (all match, partial, none)
- Verify responsive design on mobile, tablet, desktop
- Test keyboard navigation through entire flow
- Ensure color contrast meets WCAG AA standards
- Run type-check: `npm run type-check`
- Run lint: `npm run lint`
- Build application: `npm run build`

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build application
npm run build

# Start dev server and manually test
npm run dev
# Open http://localhost:3000/comparison
```

## Manual Testing Checklist

After running validation commands, manually test:

1. **Stage 1 - Thai Watsadu Input**
   - [ ] Card has distinct red border and subtle background
   - [ ] Tooltips appear on SKU and URL fields
   - [ ] Input validation works
   - [ ] Next button is properly styled and functional

2. **Stage 2 - Retailer Selection**
   - [ ] Retailer cards show logos/icons and brand colors
   - [ ] Multi-select works with visual checkmarks
   - [ ] Cards have hover states and proper spacing
   - [ ] Tooltip explains retailer selection
   - [ ] Grid is responsive (2-col mobile, 3-4 col desktop)

3. **Stage 3 - Competitor URLs**
   - [ ] Competitor cards have brand color accent borders
   - [ ] 'Add another URL' button is prominent with icon
   - [ ] Tooltips explain URL input
   - [ ] Summary card shows Thai Watsadu + selected retailers
   - [ ] Summary shows correct URL count
   - [ ] Compare button is prominent and shows loading state

4. **Stage 4 - Validation**
   - [ ] Match status shows clear icons and color-coded badges
   - [ ] Status messages are friendly and clear (no confusing percentages)
   - [ ] Partial matches show "X of Y matched" format
   - [ ] Action buttons have proper hierarchy (Confirm primary, Retry secondary)
   - [ ] Results are grouped by status (matches, partials, no-matches)

5. **Overall Flow**
   - [ ] Single-column layout is clean and centered
   - [ ] Completed steps collapse automatically with reduced opacity
   - [ ] Can click collapsed step headers to expand and edit
   - [ ] StageIndicator shows clear progress with animations
   - [ ] Active step has prominent highlighting
   - [ ] Smooth transitions between stages
   - [ ] Responsive on mobile, tablet, desktop
   - [ ] Keyboard navigation works throughout
   - [ ] All tooltips work on hover/focus

## Notes

- **Logo Assets**: If official retailer logos are unavailable, use Lucide icons (Building2, Store, Warehouse) with brand colors as fallback
- **Accessibility**: Ensure all interactive elements are keyboard accessible and have proper ARIA labels
- **Performance**: Use CSS transitions instead of JavaScript animations where possible for better performance
- **Consistency**: Follow existing design patterns from Products page (same button styles, card styles, etc.)
- **Color Coding**: Match status colors should be consistent with existing StatusBadge component (green for positive, red for negative, yellow for warning)
- **Mobile First**: Design components mobile-first, then enhance for larger screens
- **Error States**: Ensure validation errors are clearly visible with proper styling and positioning
- **Loading States**: All async actions should show appropriate loading states (spinners, disabled buttons)
