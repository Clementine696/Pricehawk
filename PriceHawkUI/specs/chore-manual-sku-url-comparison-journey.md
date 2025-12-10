# Manual SKU/URL Comparison Journey

## ADW ID: manual-comparison

## Description

Implement a new "Manual Comparison" feature that allows users to input a Thaiwatsadu product (via SKU or URL) and compare it against multiple selected competitors (HomePro, Mega Home, Boonthavorn, Global House, DoHome). The user can review match results and confirm or retry the matching action.

## User Journey

### Flow Overview
1. User navigates to "Manual Comparison" page from sidebar
2. User enters Thaiwatsadu SKU or URL
3. User selects one or more competitors from the list
4. User optionally provides competitor URLs for direct matching
5. System processes and returns match results
6. User reviews results showing Match/Not Match status with confidence
7. User can Confirm (mark as verified) or Retry (re-process) each result

### UI Layout (Based on Reference Design - image2.png)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PriceHawk          Price Monitoring System                                   │
├─────────────┬───────────────────────────────────────────────────────────────┤
│             │  Manual Comparison                                             │
│  Dashboard  │  Compare products across retailers manually                    │
│             │                                                                │
│ ● Products  │  ┌─────────────────────────────────────────────────────────┐  │
│             │  │ Input Section                                            │  │
│  Manual     │  │                                                          │  │
│  Comparison │  │  Thaiwatsadu Product                                     │  │
│             │  │  ┌──────────────────────────────────────────────────┐   │  │
│  Scraping   │  │  │ SKU or URL                                       │   │  │
│  Settings   │  │  │ [________________________________] [Fetch Info]  │   │  │
│             │  │  └──────────────────────────────────────────────────┘   │  │
│             │  │                                                          │  │
│             │  │  Select Competitors                                      │  │
│             │  │  ┌──────────────────────────────────────────────────┐   │  │
│             │  │  │ ☑ HomePro    ☑ Mega Home    ☑ Boonthavorn       │   │  │
│             │  │  │ ☑ Global House    ☐ DoHome                       │   │  │
│             │  │  └──────────────────────────────────────────────────┘   │  │
│             │  │                                                          │  │
│             │  │  Competitor URLs (Optional - for direct matching)        │  │
│             │  │  ┌──────────────────────────────────────────────────┐   │  │
│             │  │  │ HomePro URL:     [_____________________________] │   │  │
│             │  │  │ Mega Home URL:   [_____________________________] │   │  │
│             │  │  │ Boonthavorn URL: [_____________________________] │   │  │
│             │  │  │ Global House URL:[_____________________________] │   │  │
│             │  │  └──────────────────────────────────────────────────┘   │  │
│             │  │                                                          │  │
│             │  │                              [Compare Products]          │  │
│             │  └─────────────────────────────────────────────────────────┘  │
│             │                                                                │
│             │  ┌─────────────────────────────────────────────────────────┐  │
│             │  │ Results Section (shown after comparison)                 │  │
│             │  │                                                          │  │
│             │  │  ┌─────────────────┐    ┌─────────────────────────────┐ │  │
│             │  │  │ INPUT           │ >> │ OUTPUT                      │ │  │
│             │  │  │                 │    │                             │ │  │
│             │  │  │ [Product Image] │    │ HomePro.co.th              │ │  │
│             │  │  │                 │    │ https://homepro.co.th/...  │ │  │
│             │  │  │ Product name    │    │ [✓ Match] [✗ Not Match]    │ │  │
│             │  │  │ SKU: 1234567    │    │ Confidence: 95%            │ │  │
│             │  │  │                 │    │                             │ │  │
│             │  │  │ More info on    │    │ GlobalHouse.com            │ │  │
│             │  │  │ Product listing │    │ https://global-house.com/..│ │  │
│             │  │  │                 │    │ [✓ Match] [✗ Not Match]    │ │  │
│             │  │  │                 │    │ Confidence: 87%            │ │  │
│             │  │  └─────────────────┘    └─────────────────────────────┘ │  │
│             │  │                                                          │  │
│             │  │  Actions:  [Confirm All Matches]  [Retry Failed]         │  │
│             │  └─────────────────────────────────────────────────────────┘  │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

## Relevant Files

### Existing Files to Reference
- `lib/types/price-comparison.ts` - Retailer enum and existing types
- `components/products/ProductSearchFilter.tsx` - Form input patterns
- `components/products/MatchedProductCard.tsx` - Product card display
- `components/products/ConfidenceBadge.tsx` - Confidence display
- `components/products/StatusBadge.tsx` - Status badge patterns
- `components/layout/Sidebar.tsx` - Navigation menu
- `app/(main)/products/page.tsx` - Page structure pattern

### New Files to Create
- `lib/types/manual-comparison.ts` - Types for manual comparison feature
- `components/comparison/CompetitorSelector.tsx` - Multi-select competitor checkboxes
- `components/comparison/ManualComparisonForm.tsx` - Input form for SKU/URL
- `components/comparison/CompetitorUrlInputs.tsx` - Optional competitor URL inputs
- `components/comparison/ComparisonResultCard.tsx` - Result display with match/not match
- `components/comparison/ComparisonResultActions.tsx` - Confirm/Retry action buttons
- `components/comparison/SourceProductCard.tsx` - Display Thaiwatsadu source product
- `app/(main)/comparison/page.tsx` - Manual comparison page
- `app/api/comparison/manual/route.ts` - API endpoint for manual comparison

## Step-by-Step Tasks

### Task 1: Create Type Definitions
**File**: `lib/types/manual-comparison.ts`

```typescript
// Competitor retailer type (excludes Thai Watsadu as source)
export type CompetitorRetailer =
  | 'HOMEPRO'
  | 'MEGA_HOME'
  | 'BOONTHAVORN'
  | 'GLOBAL_HOUSE'
  | 'DOHOME';

// Competitor info with display properties
export interface CompetitorInfo {
  id: CompetitorRetailer;
  name: string;
  nameTh: string;
  domain: string;
  logo?: string;
}

// Input form state
export interface ManualComparisonInput {
  thaiwatsuduInput: string; // SKU or URL
  inputType: 'sku' | 'url';
  selectedCompetitors: CompetitorRetailer[];
  competitorUrls: Partial<Record<CompetitorRetailer, string>>;
}

// Source product fetched from Thaiwatsadu
export interface SourceProduct {
  sku: string;
  name: string;
  nameTh?: string;
  price: number;
  imageUrl: string;
  productUrl: string;
  category?: string;
  brand?: string;
}

// Match result for each competitor
export interface CompetitorMatchResult {
  competitor: CompetitorRetailer;
  status: 'match' | 'not_match' | 'pending' | 'error';
  confidence: number; // 0-100
  matchedProduct?: {
    sku: string;
    name: string;
    price: number;
    imageUrl: string;
    productUrl: string;
  };
  userVerified?: boolean;
  errorMessage?: string;
}

// API request payload
export interface ManualComparisonRequest {
  sourceProduct: SourceProduct;
  competitors: CompetitorRetailer[];
  competitorUrls?: Partial<Record<CompetitorRetailer, string>>;
}

// API response
export interface ManualComparisonResponse {
  id: string;
  sourceProduct: SourceProduct;
  results: CompetitorMatchResult[];
  createdAt: string;
}

// Form state for the comparison page
export interface ComparisonFormState {
  isLoading: boolean;
  isFetchingSource: boolean;
  sourceProduct: SourceProduct | null;
  results: CompetitorMatchResult[];
  error: string | null;
}
```

### Task 2: Create Competitor Constants
**File**: `lib/constants/competitors.ts`

```typescript
import { CompetitorInfo, CompetitorRetailer } from '@/lib/types/manual-comparison';

export const COMPETITORS: Record<CompetitorRetailer, CompetitorInfo> = {
  HOMEPRO: {
    id: 'HOMEPRO',
    name: 'HomePro',
    nameTh: 'โฮมโปร',
    domain: 'homepro.co.th',
  },
  MEGA_HOME: {
    id: 'MEGA_HOME',
    name: 'Mega Home',
    nameTh: 'เมกาโฮม',
    domain: 'megahome.co.th',
  },
  BOONTHAVORN: {
    id: 'BOONTHAVORN',
    name: 'Boonthavorn',
    nameTh: 'บุญถาวร',
    domain: 'boonthavorn.com',
  },
  GLOBAL_HOUSE: {
    id: 'GLOBAL_HOUSE',
    name: 'Global House',
    nameTh: 'โกลบอลเฮ้าส์',
    domain: 'globalhouse.co.th',
  },
  DOHOME: {
    id: 'DOHOME',
    name: 'DoHome',
    nameTh: 'ดูโฮม',
    domain: 'dohome.co.th',
  },
};

export const COMPETITOR_LIST = Object.values(COMPETITORS);
```

### Task 3: Create CompetitorSelector Component
**File**: `components/comparison/CompetitorSelector.tsx`

Features:
- Checkbox list with all 5 competitors
- Select All / Deselect All toggle
- Show competitor name in English and Thai
- Disabled state during processing

### Task 4: Create ManualComparisonForm Component
**File**: `components/comparison/ManualComparisonForm.tsx`

Features:
- Text input for SKU or URL with auto-detection
- "Fetch Info" button to load product details
- Display fetched product preview
- Validation for SKU format and URL domain
- Loading state while fetching

### Task 5: Create CompetitorUrlInputs Component
**File**: `components/comparison/CompetitorUrlInputs.tsx`

Features:
- Dynamic input fields based on selected competitors
- URL validation for correct domains
- Clear button for each input
- Collapsible section (optional URLs)

### Task 6: Create SourceProductCard Component
**File**: `components/comparison/SourceProductCard.tsx`

Features:
- Display product image (with fallback)
- Show product name, SKU, price
- Link to original Thaiwatsadu listing
- "INPUT" label header

### Task 7: Create ComparisonResultCard Component
**File**: `components/comparison/ComparisonResultCard.tsx`

Features:
- Show competitor name and domain
- Display matched product URL (clickable)
- Match/Not Match action buttons (like Correct/Incorrect in reference)
- Confidence percentage badge
- Status indicator (verified, pending, error)
- Error message display when applicable

### Task 8: Create ComparisonResultActions Component
**File**: `components/comparison/ComparisonResultActions.tsx`

Features:
- "Confirm All Matches" button (batch confirm)
- "Retry Failed" button (re-process failed/not-match items)
- "Export Results" button
- Disabled states based on results

### Task 9: Create Manual Comparison Page
**File**: `app/(main)/comparison/page.tsx`

Structure:
- Page header with title and description
- Input section with form components
- Results section (shown after comparison)
- Two-panel layout: Source Product | Match Results
- Loading states and error handling

### Task 10: Create API Endpoint
**File**: `app/api/comparison/manual/route.ts`

POST endpoint:
- Accept ManualComparisonRequest
- Validate input
- Return mock results (for now)
- Generate unique comparison ID

GET endpoint (optional):
- Fetch comparison by ID
- Return stored results

### Task 11: Update Sidebar Navigation
**File**: `components/layout/Sidebar.tsx`

- Add "Manual Comparison" menu item
- Use appropriate icon (GitCompare or similar)
- Position between Products and Scraping Settings

### Task 12: Add Utility Functions
**File**: `lib/utils/comparison-utils.ts`

- `detectInputType(input: string): 'sku' | 'url'`
- `validateThaiwatsuduUrl(url: string): boolean`
- `validateCompetitorUrl(url: string, competitor: CompetitorRetailer): boolean`
- `extractSkuFromUrl(url: string): string | null`
- `getConfidenceColor(confidence: number): string`

## Validation Commands

```bash
# Type check
npm run build

# Lint check
npm run lint

# Start dev server and verify manually
npm run dev
# Navigate to http://localhost:3000/comparison
```

## UI/UX Requirements

### Color Scheme (from existing design)
- Primary: Blue (#0EA5E9)
- Success/Match: Green (#22C55E)
- Error/Not Match: Red (#EF4444)
- Warning: Amber (#F59E0B)
- Neutral: Gray (#6B7280)

### Button States
- Match button: Green background with checkmark icon
- Not Match button: Red background with X icon
- Confirm: Blue primary button
- Retry: Gray outline button

### Confidence Badge Colors
- >= 95%: Green
- 80-94%: Yellow
- < 80%: Orange/Red

### Responsive Behavior
- Desktop: Two-column layout (Input | Results)
- Tablet: Stacked layout
- Mobile: Full-width stacked

## Mock Data for Development

```typescript
const mockSourceProduct: SourceProduct = {
  sku: '1145439',
  name: 'SPC NARA CREAM 17.78X121.92X0.4 CM.',
  nameTh: 'กระเบื้อง SPC นารา ครีม',
  price: 100,
  imageUrl: '/mock/product-image.jpg',
  productUrl: 'https://www.thaiwatsadu.com/th/product/1145439',
  category: 'กระเบื้อง',
  brand: 'XX',
};

const mockResults: CompetitorMatchResult[] = [
  {
    competitor: 'HOMEPRO',
    status: 'match',
    confidence: 95,
    matchedProduct: {
      sku: 'HP-1145439',
      name: 'SPC NARA CREAM TILE',
      price: 150,
      imageUrl: '/mock/homepro-product.jpg',
      productUrl: 'https://www.homepro.co.th/p/12345',
    },
  },
  {
    competitor: 'GLOBAL_HOUSE',
    status: 'match',
    confidence: 87,
    matchedProduct: {
      sku: 'GH-1145439',
      name: 'SPC Flooring Nara Cream',
      price: 120,
      imageUrl: '/mock/gh-product.jpg',
      productUrl: 'https://www.globalhouse.co.th/product/67890',
    },
  },
  {
    competitor: 'BOONTHAVORN',
    status: 'not_match',
    confidence: 0,
    errorMessage: 'No matching product found',
  },
];
```

## Dependencies
- No new npm packages required
- Uses existing Lucide icons
- Uses existing Tailwind configuration
