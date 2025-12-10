# Chore: Fix Responsive Design Issues in Manual Comparison Page

## Metadata
adw_id: `4ca412fc`
prompt: `Fix responsive design issues in Manual Comparison page: 1) StageIndicator.tsx has duplicate text on mobile - the mobile label at lines 69-77 always renders both hidden and visible states incorrectly, fix the conditional rendering so only active stage shows label on mobile. 2) Sidebar.tsx needs responsive classes - add 'hidden md:flex' to hide sidebar on mobile/tablet and ensure MainLayout handles the responsive layout properly. Reference the /products page responsive behavior for consistency.`

## Chore Description
Fix two critical responsive design issues affecting the Manual Comparison page:

1. **StageIndicator.tsx Mobile Label Issue**: Lines 69-77 contain incorrect conditional rendering logic that causes duplicate text on mobile devices. The mobile label currently renders both hidden and visible states simultaneously. The fix requires proper conditional rendering so that only the active stage displays its label on mobile screens.

2. **Sidebar.tsx Responsive Visibility Issue**: The sidebar currently displays on all screen sizes, including mobile and tablet devices where it should be hidden. Need to add responsive Tailwind classes (`hidden md:flex`) to hide the sidebar on mobile/tablet breakpoints and ensure MainLayout properly handles the responsive layout. The /products page demonstrates the expected responsive behavior that should be used as a reference.

## Relevant Files
- `components/comparison/StageIndicator.tsx` - Contains the mobile label rendering logic with duplicate text issue (lines 69-77)
- `components/layout/Sidebar.tsx` - Main sidebar navigation component that needs responsive visibility classes
- `components/layout/MainLayout.tsx` - Layout wrapper that must properly handle responsive layout when sidebar is hidden
- `app/(main)/comparison/page.tsx` - Manual Comparison page that uses StageIndicator and MainLayout
- `app/(main)/products/page.tsx` - Reference implementation for responsive behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix StageIndicator.tsx Mobile Label Conditional Rendering
- Read `components/comparison/StageIndicator.tsx` focusing on lines 69-77 where mobile label is rendered
- Identify the issue: The mobile label has `block sm:hidden` which always renders the element, then uses conditional classes for `text-cyan-600` vs `hidden`
- Fix the conditional rendering by ensuring the entire `<span>` element only renders when `isActive` is true on mobile
- Remove the redundant `hidden` class in the ternary operator since the element should not render at all when not active
- Verify the desktop label at lines 52-66 remains unchanged with `hidden sm:block` for proper desktop display

### 2. Add Responsive Classes to Sidebar.tsx
- Read `components/layout/Sidebar.tsx` to understand current structure
- Add `hidden md:flex` classes to the main sidebar container div at line 35
- The classes should hide the sidebar on mobile/tablet (< 768px) and show it as flex on desktop (≥ 768px)
- Ensure the sidebar maintains its existing `flex flex-col` layout structure
- Reference the /products page to confirm this matches the expected responsive behavior

### 3. Update MainLayout.tsx for Responsive Layout Handling
- Read `components/layout/MainLayout.tsx` to understand the current flex container structure
- Verify that the main content area (lines 14-24) properly expands to full width when sidebar is hidden on mobile
- Ensure the `flex-1` class on the main content div allows it to take full width when sidebar is hidden
- Confirm the layout works correctly on both mobile (full width) and desktop (with sidebar) breakpoints
- The MainLayout should automatically handle the responsive behavior without additional changes due to flex layout

### 4. Test Responsive Behavior on Manual Comparison Page
- Start the development server with `npm run dev`
- Navigate to `/comparison` (Manual Comparison page)
- Test StageIndicator on mobile viewport (< 640px):
  - Verify only the active stage shows a label below its circle
  - Verify inactive stages show no label text on mobile
  - Verify all stages show labels on desktop viewport (≥ 640px)
- Test Sidebar visibility:
  - Verify sidebar is hidden on mobile/tablet (< 768px)
  - Verify sidebar is visible on desktop (≥ 768px)
  - Verify main content takes full width on mobile
- Compare responsive behavior with `/products` page to ensure consistency

### 5. Validate Type Safety and Build
- Run TypeScript type checking: `npm run type-check`
- Run linting: `npm run lint`
- Run production build: `npm run build`
- Verify no type errors or build warnings related to the changes

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Type check
npm run type-check

# Lint code
npm run lint

# Build for production
npm run build

# Start development server for manual testing
npm run dev
```

## Manual Testing Steps
1. Open `http://localhost:3000/comparison` in browser
2. Open DevTools and toggle device toolbar to test mobile viewport (375px width)
3. Verify StageIndicator shows label only for active stage on mobile
4. Verify Sidebar is completely hidden on mobile/tablet
5. Resize to desktop viewport (1280px width)
6. Verify all stage labels are visible on desktop
7. Verify Sidebar is visible on desktop
8. Compare with `/products` page responsive behavior for consistency

## Notes
- The StageIndicator fix requires changing the conditional logic from using CSS classes to control visibility to using conditional rendering (element only renders when active)
- The Sidebar responsive fix uses Tailwind's responsive prefixes: `hidden` (mobile default) and `md:flex` (desktop ≥768px)
- MainLayout should automatically handle the responsive layout due to its flex-based structure, but verify the main content area expands properly
- The responsive breakpoints are: `sm` (640px), `md` (768px), `lg` (1024px) per Tailwind's default configuration
- Both fixes improve mobile UX by reducing clutter and maximizing content space on small screens
