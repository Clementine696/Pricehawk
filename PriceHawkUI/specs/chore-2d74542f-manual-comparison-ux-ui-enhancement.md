# Chore: Enhance Manual Comparison Journey UX/UI

## Metadata
adw_id: `2d74542f`
prompt: `Enhance Manual Comparison Journey UX/UI to align with PriceHawk design system. Issues to fix: 1) Add sidebar navigation - currently /comparison page has no sidebar like other pages, need MainLayout wrapper with Sidebar component. 2) Improve page header consistency - add breadcrumb navigation and match header styling from /products page. 3) Stage indicator - add a visual step indicator (1-2-3-4) at top showing current progress through the 4 stages. 4) Card styling improvements - add subtle shadows, consistent border-radius, and hover states to match the PriceComparisonTable card style. 5) Button consistency - ensure Next/Back/Compare/Retry/Confirm buttons use consistent styling from the design system (check StatusBadge and ExportButton patterns). 6) Empty state handling - show helpful message when no retailers selected or no URLs entered. 7) Success feedback - show toast notification or success message after Confirm instead of just resetting. 8) Loading state - add skeleton loader or spinner overlay during API call instead of just disabled buttons. Reference existing components: MainLayout, Sidebar, PriceComparisonTable for design patterns.`

## Chore Description

The Manual Comparison page (`/comparison`) currently lacks consistent UX/UI alignment with the PriceHawk design system. This chore will enhance the page to provide a polished, professional experience that matches the rest of the application while improving usability through better visual feedback, navigation, and state handling.

The Manual Comparison Journey is a 4-stage flow:
1. **Stage 1 (Input)**: Thai Watsadu SKU + URL input
2. **Stage 2 (Selecting)**: Retailer selection
3. **Stage 3 (Competitor URLs)**: Competitor URL inputs
4. **Stage 4 (Validation)**: User validation panel

## Relevant Files

### Existing Files to Modify

- **`app/(main)/comparison/page.tsx`** - Main comparison page component that needs MainLayout wrapper, breadcrumb, and stage indicator
- **`components/comparison/ThaiWatsuduInputCard.tsx`** - Card component needing shadow and hover state improvements
- **`components/comparison/RetailerSelector.tsx`** - Retailer selection component needing empty state and improved styling
- **`components/comparison/CompetitorInputCard.tsx`** - Competitor URL input cards needing styling consistency
- **`components/comparison/UserValidationPanel.tsx`** - Validation panel needing button consistency and loading states
- **`components/layout/MainLayout.tsx`** - Already exists, will wrap the comparison page
- **`components/layout/Sidebar.tsx`** - Already exists with `/comparison` route defined

### New Files to Create

#### New Components

- **`components/comparison/StageIndicator.tsx`** - Visual step indicator (1-2-3-4) showing progress through stages
- **`components/comparison/EmptyState.tsx`** - Reusable empty state component for "no retailers" and "no URLs" scenarios
- **`components/ui/Toast.tsx`** - Toast notification component for success feedback
- **`components/comparison/LoadingOverlay.tsx`** - Skeleton loader/spinner overlay for API calls

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create StageIndicator Component
- Create new file `components/comparison/StageIndicator.tsx`
- Implement 4-step visual indicator with labels: "Input", "Select Retailers", "Enter URLs", "Validate"
- Show active stage with cyan highlight (matching PriceHawk brand color)
- Show completed stages with checkmarks
- Show inactive stages with gray styling
- Use responsive design for mobile/tablet

### 2. Create Toast Notification Component
- Create new file `components/ui/Toast.tsx`
- Implement toast with success/error variants
- Include auto-dismiss after 3-5 seconds
- Position at top-right corner
- Use smooth slide-in/slide-out animations
- Match PriceHawk design system colors (cyan-500 for success, red-500 for error)

### 3. Create LoadingOverlay Component
- Create new file `components/comparison/LoadingOverlay.tsx`
- Implement full-screen overlay with semi-transparent background
- Include spinning loader icon with "Processing comparison..." text
- Use skeleton loaders for card content
- Match design system spinner styling

### 4. Create EmptyState Component
- Create new file `components/comparison/EmptyState.tsx`
- Implement reusable empty state with icon, title, and description props
- Include call-to-action button when applicable
- Use gray-400 text and icons for subtle appearance
- Match design system spacing and typography

### 5. Wrap Comparison Page with MainLayout
- Modify `app/(main)/comparison/page.tsx`
- Import and wrap entire page content with `<MainLayout>` component
- This automatically adds sidebar navigation
- Ensure proper spacing matches `/products` page layout

### 6. Add Page Header with Breadcrumb
- In `app/(main)/comparison/page.tsx`, add page header section
- Include breadcrumb: "Home / Manual Comparison"
- Use heading hierarchy: h1 for "Manual Comparison", subtitle "Compare products across retailers manually"
- Match header styling from `/products` page (text-3xl font-bold for h1, text-gray-600 for subtitle)

### 7. Add StageIndicator to Comparison Page
- Import `StageIndicator` component in `app/(main)/comparison/page.tsx`
- Place at top of content area, above the two-column grid
- Pass current stage prop based on state
- Add proper spacing (mb-6 or mb-8)

### 8. Improve Card Styling Consistency
- Update `ThaiWatsuduInputCard.tsx`:
  - Add shadow: `shadow-sm hover:shadow-md transition-shadow`
  - Ensure consistent border-radius: `rounded-lg`
  - Add subtle hover state for entire card
- Update `RetailerSelector.tsx`:
  - Wrap in white card container with shadow
  - Add title outside buttons in card header
  - Improve spacing and typography
- Update `CompetitorInputCard.tsx`:
  - Add shadow and hover states matching other cards
  - Ensure consistent border-radius and padding

### 9. Standardize Button Styling
- Review and update button classes in all comparison components:
  - **Primary buttons** (Next, Compare, Confirm): `bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg shadow-sm font-medium`
  - **Secondary buttons** (Back): `border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium`
  - **Danger buttons** (Retry): `border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium` with refresh icon
  - Ensure consistent padding: `px-6 py-2.5` for primary, `px-4 py-2.5` for secondary
  - All buttons should have `disabled:opacity-50 disabled:cursor-not-allowed transition-colors`

### 10. Add Empty State Handling
- In `RetailerSelector.tsx`:
  - Add `EmptyState` when no retailers selected (only show in validation, not during selection)
- In `CompetitorInputCard.tsx`:
  - Show helpful message when URL field is empty
- In `UserValidationPanel.tsx`:
  - Show empty state if results array is empty

### 11. Implement Toast Success Feedback
- Update `handleConfirm` function in `app/(main)/comparison/page.tsx`
- Add toast state management (useState for toast visibility and message)
- Show success toast: "Comparison confirmed successfully!" after confirmation
- Keep toast visible for 4 seconds then auto-dismiss
- After toast, reset form state

### 12. Implement Loading Overlay
- Update comparison page to use `LoadingOverlay` component
- Show overlay during `isSubmitting` state in Stage 3
- Replace simple disabled buttons with full overlay
- Show "Processing comparison..." message
- Include animated spinner

### 13. Update Error Handling UI
- Ensure error messages are displayed in toast notifications (red variant)
- Add error states to empty state component where appropriate
- Display validation errors inline with red text and alert icon

### 14. Responsive Design Improvements
- Test all new components on mobile, tablet, and desktop viewports
- Ensure StageIndicator collapses gracefully on mobile (vertical layout or smaller text)
- Ensure cards stack properly on mobile
- Verify button layouts work on small screens

## Validation Commands

Execute these commands to validate the chore is complete:

```bash
# Type check - ensure no TypeScript errors
npm run type-check

# Lint the code - ensure code quality standards
npm run lint

# Build the application - ensure no build errors
npm run build

# Start development server and manually test
npm run dev
# Then navigate to http://localhost:3000/comparison
```

### Manual Testing Checklist

1. **Navigation**: Verify sidebar appears on `/comparison` page and "Manual Comparison" is highlighted
2. **Stage Indicator**: Verify 4-stage indicator shows at top and updates as you progress through stages
3. **Card Styling**: Verify all cards have consistent shadows, border-radius, and hover effects
4. **Button Styling**: Verify all buttons (Next, Back, Compare, Retry, Confirm) have consistent styling
5. **Empty States**:
   - Try clicking "Next" in Stage 2 without selecting retailers - verify error message
   - Verify empty URL fields show helpful placeholder text
6. **Success Feedback**: Complete a comparison and click "Confirm" - verify toast notification appears
7. **Loading State**: Click "Compare" and verify loading overlay appears during API call
8. **Responsive Design**: Test on mobile viewport (375px), tablet (768px), and desktop (1440px)
9. **Breadcrumb**: Verify "Home / Manual Comparison" breadcrumb appears in header
10. **Layout Consistency**: Compare `/comparison` page layout with `/products` page - should match spacing and styling

## Notes

- **Design System Colors**: Use `cyan-500` (`#0EA5E9`) as primary brand color, matching the PriceHawk logo and existing UI
- **Consistency Reference**: The `/products` page (`app/(main)/products/page.tsx`) is the gold standard for layout, spacing, and component styling
- **Card Shadows**: Use Tailwind's `shadow-sm` for default state and `shadow-md` for hover state
- **Transitions**: All interactive elements should have smooth transitions using `transition-colors` or `transition-shadow`
- **Accessibility**: Ensure all interactive elements have proper ARIA labels and keyboard navigation support
- **Toast Implementation**: Consider using a portal for toast rendering to avoid z-index issues
- **Loading Overlay**: Use fixed positioning with high z-index (z-50) to overlay entire viewport
- **Stage Names**:
  - Stage 1: "Input"
  - Stage 2: "Select Retailers"
  - Stage 3: "Enter URLs"
  - Stage 4: "Validate"
