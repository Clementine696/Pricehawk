# Chore: Stage Indicator Animation Enhancements

## Metadata
adw_id: `98257d1b`
prompt: `Fix remaining UX enhancements for Manual Comparison page: 1) Add pulsing animation to active stage in StageIndicator component using animate-pulse or custom keyframe for emphasis. 2) Add ring effect (ring-2 ring-cyan-400 ring-offset-2) to the active stage circle for better visual highlighting. 3) Optionally integrate CollapsibleStepCard in Review stage to collapse the Input stage summary with an expand/collapse toggle.`

## Chore Description

This chore focuses on three specific UX enhancements to improve visual feedback and user guidance in the Manual Comparison page:

1. **Pulsing Animation for Active Stage** - Add a smooth pulsing animation to the active stage circle in the StageIndicator component to draw user attention to the current step they're on. This can be achieved using Tailwind's `animate-pulse` utility or a custom keyframe animation for more control.

2. **Ring Effect for Active Stage** - Enhance the active stage visual prominence by adding a ring effect around the circle using Tailwind classes `ring-2 ring-cyan-400 ring-offset-2`. This creates a glowing halo effect that makes the active step stand out even more.

3. **Collapsible Input Step in Review Stage** - Integrate the existing `CollapsibleStepCard` component in the Review stage to show a collapsed summary of the Input stage. This allows users to see what they entered without taking up the full screen space, with an expand/collapse toggle to review details if needed.

### Current State Analysis

Looking at the existing code:

- **StageIndicator** (`components/comparison/StageIndicator.tsx:82`): Already has `animate-pulse` and `ring-4 ring-cyan-100` classes applied to the active stage, but these might need adjustment for better visual impact
- **CollapsibleStepCard** (`components/comparison/CollapsibleStepCard.tsx`): Fully implemented component that accepts `stepNumber`, `stepTitle`, `isCompleted`, `isActive`, `children`, `summaryContent`, and `onEdit` props
- **Manual Comparison Page** (`app/(main)/comparison/page.tsx`): Uses a 3-stage flow (input → review → results) but doesn't currently use CollapsibleStepCard

### Goals

1. Fine-tune the pulsing animation and ring effect on the active stage for optimal visual emphasis
2. Consider using a custom pulsing animation if Tailwind's default `animate-pulse` is too subtle
3. Integrate CollapsibleStepCard in the Review stage to show a collapsed Input stage summary
4. Ensure the collapsed state shows key information (Thai Watsadu SKU, number of competitors)
5. Add an "Edit" button to expand and navigate back to the Input stage

## Relevant Files

### Existing Files to Modify

- **components/comparison/StageIndicator.tsx** - Update the active stage styling to enhance pulsing animation and ring effect (lines 76-94)
- **app/(main)/comparison/page.tsx** - Integrate CollapsibleStepCard in the Review stage to show collapsed Input stage summary (around line 373)
- **components/comparison/ReviewConfirmPanel.tsx** - May need to accept additional props or be restructured to accommodate the CollapsibleStepCard integration
- **tailwind.config.js** - Optionally add custom keyframe animation for pulsing if Tailwind's default is insufficient (lines 8-26)
- **app/globals.css** - Optionally add custom CSS for pulsing animation if needed

### Files to Reference (No Changes)

- **components/comparison/CollapsibleStepCard.tsx** - Already fully implemented, will be integrated as-is
- **lib/types/manual-comparison.ts** - Type definitions for understanding data structure

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze Current StageIndicator Implementation

- Read the current implementation in `components/comparison/StageIndicator.tsx:76-94`
- Identify what animation and ring classes are currently applied
- Determine if `animate-pulse` provides sufficient visual emphasis
- Check if the ring effect needs to be adjusted from `ring-4 ring-cyan-100` to `ring-2 ring-cyan-400 ring-offset-2`

### 2. Enhance Active Stage Animation in StageIndicator

- Update `components/comparison/StageIndicator.tsx`:
  - Replace or augment the existing `ring-4 ring-cyan-100` with `ring-2 ring-cyan-400 ring-offset-2` for a more prominent, colored ring effect
  - Ensure `animate-pulse` is applied to the active stage circle
  - Test the visual effect - if `animate-pulse` is too subtle, proceed to step 3
  - Keep the existing `scale-110` transform for active state
  - Maintain the gradient background `bg-gradient-to-br from-cyan-500 to-cyan-600`
  - Ensure transitions remain smooth with `transition-all duration-300 ease-in-out`

### 3. Optionally Add Custom Pulsing Animation (if needed)

If Tailwind's default `animate-pulse` is insufficient:

- Add a custom keyframe animation to `tailwind.config.js`:
  ```js
  theme: {
    extend: {
      keyframes: {
        'pulse-ring': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.7', transform: 'scale(1.05)' }
        }
      },
      animation: {
        'pulse-ring': 'pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      }
    }
  }
  ```
- Apply the custom animation class `animate-pulse-ring` to the active stage circle
- Alternatively, add a custom CSS animation in `app/globals.css` if more control is needed

### 4. Test StageIndicator Animation Enhancements

- Run `npm run dev` and navigate to `/comparison`
- Verify the active stage circle has a visible pulsing animation
- Confirm the ring effect appears as a cyan glow around the active stage
- Check that the animation doesn't interfere with stage transitions
- Test on different screen sizes to ensure responsiveness
- Verify that completed stages (with checkmarks) don't pulse or have rings

### 5. Design Input Stage Summary Content for CollapsibleStepCard

- Plan what information should show in the collapsed Input stage summary:
  - Thai Watsadu SKU
  - Number of competitors added
  - Brief format: "SKU: XXX | 3 competitors selected"
- Determine the visual layout for the summary (inline text, badges, etc.)
- Consider using a condensed format to save space

### 6. Integrate CollapsibleStepCard in Review Stage

- Update `app/(main)/comparison/page.tsx` in the Review stage section (around line 373):
  - Import `CollapsibleStepCard` component
  - Wrap the Input stage summary content in a CollapsibleStepCard
  - Pass props:
    - `stepNumber={1}`
    - `stepTitle="Input Stage"`
    - `isCompleted={true}`
    - `isActive={false}`
    - `summaryContent={<InputStageSummary />}` - Create a compact summary component
    - `onEdit={handleEditInputs}` - Use existing edit handler
  - Create a compact summary component that shows:
    - Thai Watsadu SKU
    - Number of competitors and their retailers (e.g., "3 competitors: HomePro, Global House, DoHome")
- Position the CollapsibleStepCard above the ReviewConfirmPanel

### 7. Create Input Stage Summary Component

- Create a new inline component or extract it in the same file:
  ```tsx
  const InputStageSummary = () => (
    <div className="text-sm text-gray-600 space-y-1">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-gray-700">Thai Watsadu SKU:</span>
        <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{thaiWatsuduInput.sku}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-semibold text-gray-700">Competitors:</span>
        <span>{validCompetitorCount} selected</span>
      </div>
    </div>
  );
  ```
- Ensure it has access to the necessary state variables (`thaiWatsuduInput`, `competitorEntries`)

### 8. Adjust Review Stage Layout

- Restructure the Review stage JSX to include the CollapsibleStepCard:
  ```tsx
  {stage === 'review' && (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Collapsible Input Stage Summary */}
      <CollapsibleStepCard
        stepNumber={1}
        stepTitle="Input Stage"
        isCompleted={true}
        isActive={false}
        summaryContent={<InputStageSummary />}
        onEdit={handleEditInputs}
      >
        {/* Full input content (not shown when collapsed) */}
        <div className="text-sm text-gray-600">
          Input stage details...
        </div>
      </CollapsibleStepCard>

      {/* Review Confirm Panel */}
      <ReviewConfirmPanel
        thaiWatsuduInput={thaiWatsuduInput}
        competitorEntries={validCompetitorEntries}
        onEdit={handleEditInputs}
        onConfirm={handleConfirmAndCompare}
      />
    </div>
  )}
  ```
- Ensure proper spacing between CollapsibleStepCard and ReviewConfirmPanel

### 9. Test Collapsible Input Stage in Review Stage

- Navigate to the Review stage in the Manual Comparison flow
- Verify the CollapsibleStepCard appears with the Input Stage summary collapsed
- Click the expand/collapse toggle to verify it opens and shows full content
- Click the "Edit" button to verify it navigates back to Input stage
- Confirm the summary content is clear and informative
- Check that the card styling matches the existing design system (cyan accents, proper borders)

### 10. Handle Edge Cases

- Ensure the CollapsibleStepCard only appears in the Review stage (not Input or Results)
- Verify that if user returns to Input stage and then goes back to Review, the summary updates correctly
- Test with different numbers of competitors (1, 3, 5) to ensure summary text is grammatically correct
- Handle the case where competitor count is 0 (though validation should prevent this)

### 11. Validate TypeScript Types

- Run `npm run type-check` to ensure no TypeScript errors
- Fix any type issues with props or state variables used in the new components
- Ensure CollapsibleStepCard props are correctly typed

### 12. Final End-to-End Testing

- Test the complete Manual Comparison flow:
  1. **Input Stage**: Verify the active stage indicator pulses and has ring effect
  2. Navigate to **Review Stage**: Verify the Input stage appears as a CollapsibleStepCard
  3. Expand/collapse the Input stage card: Verify smooth animation
  4. Click Edit: Verify returns to Input stage with active indicator
  5. Navigate back to **Review**: Verify card state persists correctly
  6. Proceed to **Results Stage**: Verify no CollapsibleStepCard appears
- Test responsiveness on mobile (375px), tablet (768px), and desktop (1024px+)
- Verify animations are smooth and not janky
- Confirm accessibility with keyboard navigation (tab through elements)

### 13. Code Quality and Cleanup

- Remove any console.log statements or debug code
- Ensure consistent code formatting
- Add comments for any complex logic
- Verify all imports are used and necessary
- Check for unused variables or functions

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Lint code
npm run lint

# Build application to ensure no errors
npm run build

# Start development server for manual testing
npm run dev

# Navigate to http://localhost:3000/comparison
# Test the complete flow:
# 1. Input stage - verify pulsing animation and ring effect on active indicator
# 2. Review stage - verify CollapsibleStepCard shows Input summary
# 3. Expand/collapse the card - verify smooth animation
# 4. Click Edit - verify returns to Input stage
# 5. Complete flow - verify results stage works
```

## Manual Testing Checklist

### StageIndicator Enhancements
- [ ] Active stage circle has visible pulsing animation
- [ ] Active stage has cyan ring effect around it (ring-2 ring-cyan-400 ring-offset-2)
- [ ] Ring effect has proper offset and doesn't overlap with stage circle
- [ ] Pulsing animation is smooth and not distracting
- [ ] Completed stages show checkmark and no pulsing/ring
- [ ] Inactive future stages show gray and no pulsing/ring
- [ ] Animation works across all stage transitions (Input → Review → Results)
- [ ] Mobile view shows smaller stage circles with animation still visible

### CollapsibleStepCard Integration
- [ ] Review stage shows CollapsibleStepCard for Input stage summary
- [ ] Card is collapsed by default showing summary content
- [ ] Summary shows Thai Watsadu SKU clearly
- [ ] Summary shows number of competitors selected
- [ ] Clicking expand/collapse toggle animates smoothly
- [ ] Expanded view shows full input details (if implemented)
- [ ] Edit button appears and is clickable
- [ ] Clicking Edit navigates back to Input stage
- [ ] Card styling matches existing design system (cyan accents, proper borders)
- [ ] Card has proper spacing from ReviewConfirmPanel below

### Responsive Design
- [ ] Mobile (375px): StageIndicator animation visible, CollapsibleStepCard works
- [ ] Tablet (768px): All elements properly sized and spaced
- [ ] Desktop (1024px+): Optimal layout with no issues

### Accessibility
- [ ] StageIndicator animation doesn't cause seizure risk (frequency check)
- [ ] CollapsibleStepCard can be operated with keyboard (tab, enter, space)
- [ ] Edit button has proper focus state
- [ ] Screen reader announces stage changes appropriately

### Performance
- [ ] No console errors or warnings
- [ ] Animations run at 60fps without jank
- [ ] Page load time not impacted
- [ ] No unnecessary re-renders during animation

## Notes

### Design Considerations

1. **Animation Intensity**: The pulsing animation should be noticeable but not distracting. If Tailwind's default `animate-pulse` (opacity 0-100% over 2s) is too subtle, consider a custom animation with scale transform for more emphasis.

2. **Ring Effect Clarity**: The ring effect uses `ring-2 ring-cyan-400 ring-offset-2` which creates:
   - A 2px cyan ring around the circle
   - A 2px white offset between the circle and ring
   - This provides better visual separation than the current `ring-4 ring-cyan-100`

3. **CollapsibleStepCard Placement**: The card should appear at the top of the Review stage, before the ReviewConfirmPanel, to maintain a top-to-bottom flow of the wizard.

### Technical Considerations

- The CollapsibleStepCard component already exists and is fully functional, so integration should be straightforward
- The existing `handleEditInputs` callback can be reused for the Edit button
- The StageIndicator already has most of the animation infrastructure in place, just needs fine-tuning
- Consider whether the collapsed state should show a brief list of competitor retailers or just the count

### Current Implementation Notes

From the code review:
- **StageIndicator.tsx:82** already applies `animate-pulse` and `ring-4 ring-cyan-100`
- The change from `ring-4 ring-cyan-100` to `ring-2 ring-cyan-400 ring-offset-2` will make the ring:
  - Thinner (2px vs 4px)
  - More vibrant (cyan-400 vs cyan-100)
  - Have a white offset for better separation
- This should create a more focused, glowing effect rather than a thick light border

### Optional Enhancements (Out of Scope)

- Animate the transition when CollapsibleStepCard appears (fade-in, slide-down)
- Add a subtle gradient to the CollapsibleStepCard summary background
- Show mini retailer logos in the collapsed summary
- Add a "Quick Edit SKU" inline input in the collapsed state
- Persist collapsed/expanded state in localStorage

### Success Criteria

This chore is complete when:
1. The active stage in StageIndicator has a visible pulsing animation and cyan ring effect
2. The ring uses `ring-2 ring-cyan-400 ring-offset-2` classes
3. The Review stage shows a CollapsibleStepCard with Input stage summary
4. The summary shows Thai Watsadu SKU and competitor count
5. The Edit button navigates back to Input stage
6. All TypeScript types are correct and build passes
7. Manual testing confirms smooth animations and proper functionality
