# Chore: Fix Status Badge Visibility Issue

## Metadata
adw_id: `af1b005f`
prompt: `Fix the Status Badge visibility issue - the getStatusColor function in lib/utils/price-utils.ts was correctly updated to use hardcoded Tailwind classes (bg-green-500, bg-amber-500, bg-gray-500), but the tailwind.config.js content array is missing the lib directory. Add './lib/**/*.{js,ts,jsx,tsx}' to the content array in tailwind.config.js so Tailwind JIT can detect the classes defined in lib/utils/price-utils.ts.`

## Chore Description
The Status Badge component is experiencing a visibility issue where background colors are not being applied correctly. The root cause is that the `getStatusColor` function in `lib/utils/price-utils.ts` (lines 129-142) correctly returns hardcoded Tailwind classes such as:
- `bg-green-500 text-white` (for 'cheapest' status)
- `bg-amber-500 text-white` (for 'higher' status)
- `bg-gray-500 text-white` (for 'same' status)
- `bg-gray-300 text-gray-600` (for 'unavailable' status)

However, Tailwind CSS's JIT (Just-In-Time) compiler is not detecting these classes because the `tailwind.config.js` content array only scans the `pages/`, `components/`, and `app/` directories. It does not include the `lib/` directory where `price-utils.ts` is located.

This chore requires adding `'./lib/**/*.{js,ts,jsx,tsx}'` to the content array in `tailwind.config.js` so that Tailwind's JIT compiler can scan all TypeScript/JavaScript files in the `lib` directory and include the necessary utility classes in the generated CSS.

## Relevant Files
Use these files to complete the chore:

- **tailwind.config.js** - Tailwind CSS configuration file that needs to be updated to include the `lib` directory in the content array (lines 3-7)
- **lib/utils/price-utils.ts** - Contains the `getStatusColor` function (lines 129-142) that uses the Tailwind classes that need to be detected
- **components/products/StatusBadge.tsx** - The component that uses `getStatusColor` to apply badge colors (lines 10, 15)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Tailwind Configuration
- Open `tailwind.config.js`
- Locate the `content` array (currently lines 3-7)
- Add `'./lib/**/*.{js,ts,jsx,tsx}'` as a new entry to the content array
- Ensure the entry is added after the existing entries to maintain configuration consistency

### 2. Validate Configuration Syntax
- Verify that the updated `tailwind.config.js` has valid JavaScript syntax
- Ensure all array entries are properly comma-separated
- Confirm the file exports the configuration object correctly

### 3. Rebuild and Test
- Clear the Next.js build cache to ensure fresh compilation
- Rebuild the application to regenerate Tailwind CSS with the new content paths
- Verify that Status Badge colors are now visible in the UI

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Remove Next.js cache and build artifacts
rm -rf .next

# Type check the project
npm run type-check

# Lint the code
npm run lint

# Build the application (this will regenerate Tailwind CSS)
npm run build

# Start the development server to verify Status Badge colors
npm run dev
```

After running `npm run dev`, navigate to `http://localhost:3000/products` and verify that:
- Cheapest status badges show green background (`bg-green-500`)
- Higher status badges show amber/orange background (`bg-amber-500`)
- Same status badges show gray background (`bg-gray-500`)
- N/A status badges show light gray background (`bg-gray-300`)

## Notes
- This is a configuration fix only - no changes to component or utility code are required
- The issue occurs because Tailwind's JIT compiler only scans directories specified in the `content` array
- Without scanning the `lib` directory, classes defined in `lib/utils/price-utils.ts` are not included in the final CSS bundle
- After this fix, all Tailwind classes used in the `lib` directory will be properly detected and included
