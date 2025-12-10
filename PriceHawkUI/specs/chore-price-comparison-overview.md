# Product Price Comparison Overview Page

## Chore ID: price-comparison-overview
## Date: 2025-11-29

---

## 1. Overview

Design and implement a **Product Price Comparison Overview Page** that compares the same product (same category and SKU) sold by Thai home improvement retailers:
- **Thai Watsadu** (primary/reference retailer)
- **HomePro**
- **Global House**
- **DoHome**
- **Boonthavorn**

---

## 2. User Journey & UX Flow

### 2.1 Entry Points
1. **Sidebar Navigation** → Click "Products" menu item
2. **Dashboard** → Click on price comparison widget/card
3. **Direct URL** → `/products` or `/price-comparison`

### 2.2 Primary User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│  1. USER LANDS ON PAGE                                          │
│     └─> Sees page header "Products" with subtitle               │
│         "Compare prices across retailers"                       │
├─────────────────────────────────────────────────────────────────┤
│  2. SEARCH & FILTER SECTION                                     │
│     ├─> Search box: "Search by name, SKU, brand, or retailer"   │
│     ├─> Category dropdown: "All Categories"                     │
│     ├─> Brand dropdown: "All Brands"                            │
│     ├─> Reset button                                            │
│     └─> Export button (CSV/Excel)                               │
├─────────────────────────────────────────────────────────────────┤
│  3. PRICE COMPARISON TABLE                                      │
│     ├─> Row displays: No., Category, SKU, Product Name, Brand   │
│     ├─> Price columns for each retailer (clickable links)       │
│     ├─> Status badge showing price position                     │
│     └─> Pagination at bottom                                    │
├─────────────────────────────────────────────────────────────────┤
│  4. USER INTERACTIONS                                           │
│     ├─> Click price → Opens retailer product page (new tab)     │
│     ├─> Click row → Opens Product Detail Modal                  │
│     ├─> Filter/Search → Table updates in real-time              │
│     └─> Export → Downloads filtered data as CSV/Excel           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Product Detail Modal Journey

```
┌─────────────────────────────────────────────────────────────────┐
│  PRODUCT DETAIL MODAL (Click on table row)                      │
├─────────────────────────────────────────────────────────────────┤
│  LEFT SIDE: Thai Watsadu Product (Reference)                    │
│  ├─> Product Image                                              │
│  ├─> Product Name                                               │
│  ├─> Price: Current price + Original price                      │
│  ├─> Stock status badge                                         │
│  ├─> Promo badge (if applicable)                                │
│  ├─> SKU                                                        │
│  ├─> Brand                                                      │
│  ├─> Category                                                   │
│  └─> Store link                                                 │
├─────────────────────────────────────────────────────────────────┤
│  RIGHT SIDE: Matched Products (Competitors)                     │
│  ├─> Tabs or cards for each retailer                            │
│  ├─> Same product info layout                                   │
│  ├─> Match confidence rate                                      │
│  └─> "Similar" or "Exact Match" badge                           │
├─────────────────────────────────────────────────────────────────┤
│  BOTTOM: Price Trend Chart (optional enhancement)               │
│  └─> Historical price comparison across retailers               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. UI Components Design

### 3.1 Page Layout Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (180px)  │  MAIN CONTENT AREA                                │
│ ┌──────────────┐ │ ┌──────────────────────────────────────────────┐  │
│ │ PriceHawk    │ │ │ Header: "Price Monitoring System"            │  │
│ │ Logo         │ │ └──────────────────────────────────────────────┘  │
│ ├──────────────┤ │ ┌──────────────────────────────────────────────┐  │
│ │ 📊 Dashboard │ │ │ Page Title: "Products"                       │  │
│ ├──────────────┤ │ │ Subtitle: "Compare prices across retailers"  │  │
│ │ 🏷️ Products  │ │ └──────────────────────────────────────────────┘  │
│ │   (active)   │ │ ┌──────────────────────────────────────────────┐  │
│ ├──────────────┤ │ │ SEARCH & FILTER CARD                         │  │
│ │ ⚙️ Scraping  │ │ │ [Search Input] [Category▼] [Brand▼] [Reset]  │  │
│ │   Settings   │ │ │                                    [Export]  │  │
│ └──────────────┘ │ └──────────────────────────────────────────────┘  │
│                  │ ┌──────────────────────────────────────────────┐  │
│                  │ │ PRICE COMPARISON TABLE                       │  │
│                  │ │ ┌──────────────────────────────────────────┐ │  │
│                  │ │ │ Table Header Row                         │ │  │
│                  │ │ ├──────────────────────────────────────────┤ │  │
│                  │ │ │ Data Row 1                               │ │  │
│                  │ │ ├──────────────────────────────────────────┤ │  │
│                  │ │ │ Data Row 2                               │ │  │
│                  │ │ ├──────────────────────────────────────────┤ │  │
│                  │ │ │ ...                                      │ │  │
│                  │ │ └──────────────────────────────────────────┘ │  │
│                  │ │ Showing X of Y products    [< 1 2 3 ... >]   │  │
│                  │ └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Table Column Specifications

| Column | Width | Content | Behavior |
|--------|-------|---------|----------|
| No. | 50px | Row number | Static |
| Category | 100px | Category name (Thai) | Sortable |
| SKU | 100px | Product SKU | Sortable, Searchable |
| Product Name | 250px | Full product name | Sortable, Searchable, Truncate with tooltip |
| Brand | 100px | Brand name | Sortable, Filterable |
| Thai Watsadu | 100px | Price (฿) + link icon | Clickable → opens URL |
| HomePro | 100px | Price (฿) + link icon | Clickable → opens URL |
| Global House | 100px | Price (฿) + link icon | Clickable → opens URL |
| Do Home | 100px | Price (฿) + link icon | Clickable → opens URL |
| Boonthavorn | 100px | Price (฿) + link icon | Clickable → opens URL |
| Status | 100px | Badge (Cheapest/Higher/Same) | Color-coded |

### 3.3 Status Badge Logic

```typescript
type PriceStatus = 'cheapest' | 'higher' | 'same' | 'unavailable';

function calculateStatus(thaiWatsaduPrice: number, competitorPrices: number[]): PriceStatus {
  const validPrices = competitorPrices.filter(p => p > 0);
  if (validPrices.length === 0) return 'unavailable';

  const minCompetitorPrice = Math.min(...validPrices);
  const maxCompetitorPrice = Math.max(...validPrices);

  // Define threshold for "same" (within 2%)
  const threshold = 0.02;

  if (thaiWatsaduPrice <= minCompetitorPrice * (1 + threshold)) {
    return 'cheapest';  // Green badge
  } else if (thaiWatsaduPrice >= maxCompetitorPrice * (1 - threshold)) {
    return 'higher';    // Yellow/Orange badge
  } else {
    return 'same';      // Gray badge
  }
}
```

### 3.4 Badge Styling

```css
/* Cheapest - Green */
.badge-cheapest {
  background-color: #10B981;
  color: white;
  border-radius: 9999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Higher - Yellow/Orange */
.badge-higher {
  background-color: #F59E0B;
  color: white;
  border-radius: 9999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Same - Gray */
.badge-same {
  background-color: #6B7280;
  color: white;
  border-radius: 9999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
}
```

---

## 4. Data Models

### 4.1 Core Types

```typescript
// Retailer enum
enum Retailer {
  THAI_WATSADU = 'thai_watsadu',
  HOMEPRO = 'homepro',
  GLOBAL_HOUSE = 'global_house',
  DOHOME = 'dohome',
  BOONTHAVORN = 'boonthavorn',
}

// Retailer display names (Thai + English)
const RetailerNames: Record<Retailer, { th: string; en: string }> = {
  [Retailer.THAI_WATSADU]: { th: 'ไทวัสดุ', en: 'Thai Watsadu' },
  [Retailer.HOMEPRO]: { th: 'โฮมโปร', en: 'HomePro' },
  [Retailer.GLOBAL_HOUSE]: { th: 'โกลบอลเฮ้าส์', en: 'Global House' },
  [Retailer.DOHOME]: { th: 'ดูโฮม', en: 'DoHome' },
  [Retailer.BOONTHAVORN]: { th: 'บุญถาวร', en: 'Boonthavorn' },
};

// Price status type
type PriceStatus = 'cheapest' | 'higher' | 'same' | 'unavailable';

// Individual retailer price info
interface RetailerPrice {
  retailer: Retailer;
  price: number | null;        // null if unavailable
  originalPrice?: number;      // for discount calculation
  currency: 'THB';
  productUrl: string | null;   // URL to product page
  lastUpdated: string;         // ISO date string
  inStock: boolean;
  promoText?: string;          // e.g., "ลด 20%"
}

// Product comparison entry
interface ProductComparison {
  id: string;
  sku: string;
  name: string;
  nameTh?: string;             // Thai name if available
  category: string;
  categoryTh?: string;         // Thai category name
  brand: string;
  imageUrl: string;

  // Prices from each retailer
  prices: {
    [Retailer.THAI_WATSADU]: RetailerPrice;
    [Retailer.HOMEPRO]: RetailerPrice;
    [Retailer.GLOBAL_HOUSE]: RetailerPrice;
    [Retailer.DOHOME]: RetailerPrice;
    [Retailer.BOONTHAVORN]: RetailerPrice;
  };

  // Computed fields
  status: PriceStatus;
  lowestPrice: number | null;
  highestPrice: number | null;
  priceDifferencePercent: number | null;  // % difference between Thai Watsadu and lowest competitor
}

// Filter state
interface ProductFilterState {
  search: string;
  category: string | null;
  brand: string | null;
  status: PriceStatus | null;
  sortBy: 'name' | 'sku' | 'category' | 'brand' | 'price' | 'status';
  sortOrder: 'asc' | 'desc';
}

// Pagination state
interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}
```

### 4.2 API Response Types

```typescript
// GET /api/products/comparison
interface ProductComparisonListResponse {
  products: ProductComparison[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  filters: {
    categories: { value: string; label: string; count: number }[];
    brands: { value: string; label: string; count: number }[];
  };
  summary: {
    totalProducts: number;
    cheapestCount: number;
    higherCount: number;
    sameCount: number;
    unavailableCount: number;
  };
}

// GET /api/products/comparison/:id
interface ProductComparisonDetailResponse {
  product: ProductComparison;
  priceHistory: {
    date: string;
    prices: Record<Retailer, number | null>;
  }[];
  matchedProducts: {
    retailer: Retailer;
    confidence: number;        // 0-100%
    matchType: 'exact' | 'similar';
    product: {
      name: string;
      sku: string;
      imageUrl: string;
      price: number;
      url: string;
    };
  }[];
}
```

---

## 5. Component Architecture

### 5.1 Component Tree

```
app/
├── (main)/
│   └── products/
│       ├── page.tsx                    # Products page (Price Comparison)
│       └── [id]/
│           └── page.tsx                # Product detail page
│
components/
├── layout/
│   ├── Sidebar.tsx                     # Navigation sidebar
│   └── MainLayout.tsx                  # Main layout wrapper
│
├── products/
│   ├── PriceComparisonTable.tsx        # Main comparison table
│   ├── PriceComparisonRow.tsx          # Individual table row
│   ├── PriceCell.tsx                   # Price display with link
│   ├── StatusBadge.tsx                 # Cheapest/Higher/Same badge
│   ├── ProductSearchFilter.tsx         # Search & filter section
│   ├── ProductDetailModal.tsx          # Product detail modal
│   ├── ProductMatchCard.tsx            # Matched product card
│   ├── PriceHistoryChart.tsx           # Price trend chart
│   └── ExportButton.tsx                # Export functionality
│
├── ui/
│   ├── Badge.tsx                       # Generic badge (extend existing)
│   ├── Table.tsx                       # Table component
│   ├── Select.tsx                      # Dropdown select
│   ├── SearchInput.tsx                 # Search input
│   └── Pagination.tsx                  # Pagination component
│
lib/
├── types/
│   └── price-comparison.ts             # Type definitions
│
├── hooks/
│   ├── usePriceComparison.ts           # Data fetching hook
│   ├── useProductFilters.ts            # Filter state hook
│   └── useExport.ts                    # Export functionality hook
│
├── utils/
│   ├── price-utils.ts                  # Price calculation utilities
│   └── export-utils.ts                 # CSV/Excel export utilities
│
└── api/
    └── products/
        ├── comparison/
        │   └── route.ts                # GET /api/products/comparison
        └── [id]/
            └── route.ts                # GET /api/products/comparison/:id
```

### 5.2 Key Component Specifications

#### PriceComparisonTable.tsx
```typescript
interface PriceComparisonTableProps {
  products: ProductComparison[];
  isLoading: boolean;
  onRowClick: (product: ProductComparison) => void;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (column: string) => void;
}
```

#### PriceCell.tsx
```typescript
interface PriceCellProps {
  price: number | null;
  originalPrice?: number;
  productUrl: string | null;
  isLowest?: boolean;
  isHighest?: boolean;
}

// Renders:
// - "฿1,234" with external link icon if URL available
// - "-" if price is null
// - Green highlight if isLowest
// - Red highlight if isHighest
```

#### StatusBadge.tsx
```typescript
interface StatusBadgeProps {
  status: PriceStatus;
}

// Renders colored badge:
// - "Cheapest" (green)
// - "Higher" (yellow/orange)
// - "Same" (gray)
// - "N/A" (light gray) for unavailable
```

#### ProductSearchFilter.tsx
```typescript
interface ProductSearchFilterProps {
  filters: ProductFilterState;
  categories: { value: string; label: string }[];
  brands: { value: string; label: string }[];
  onFilterChange: (filters: Partial<ProductFilterState>) => void;
  onReset: () => void;
  onExport: () => void;
}
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Core Types & API)
1. Create type definitions in `lib/types/price-comparison.ts`
2. Implement API route `GET /api/products/comparison`
3. Create mock data for development/testing
4. Set up data loading utilities

### Phase 2: UI Components
1. Create `StatusBadge` component
2. Create `PriceCell` component
3. Create `PriceComparisonTable` component
4. Create `ProductSearchFilter` component
5. Create `Pagination` component (or extend existing)

### Phase 3: Page & Integration
1. Create products page layout with sidebar
2. Integrate table with API data
3. Implement filtering and sorting
4. Add pagination

### Phase 4: Detail Modal
1. Create `ProductDetailModal` component
2. Create `ProductMatchCard` component
3. Implement modal open/close behavior
4. Add price history chart (optional)

### Phase 5: Export & Polish
1. Implement CSV/Excel export
2. Add loading states and skeletons
3. Add error handling
4. Responsive design adjustments
5. Thai language support

---

## 7. File Changes Summary

### New Files to Create
```
lib/types/price-comparison.ts
lib/hooks/usePriceComparison.ts
lib/hooks/useProductFilters.ts
lib/hooks/useExport.ts
lib/utils/price-utils.ts
lib/utils/export-utils.ts

components/products/PriceComparisonTable.tsx
components/products/PriceComparisonRow.tsx
components/products/PriceCell.tsx
components/products/StatusBadge.tsx
components/products/ProductSearchFilter.tsx
components/products/ProductDetailModal.tsx
components/products/ProductMatchCard.tsx
components/products/PriceHistoryChart.tsx
components/products/ExportButton.tsx

components/layout/Sidebar.tsx
components/layout/MainLayout.tsx

app/(main)/products/page.tsx
app/(main)/products/[id]/page.tsx
app/api/products/comparison/route.ts
app/api/products/comparison/[id]/route.ts
```

### Files to Modify
```
app/layout.tsx              # Add sidebar layout
lib/types/index.ts          # Export new types
components/ui/index.ts      # Export new UI components
```

---

## 8. Technical Considerations

### 8.1 Performance
- Implement virtual scrolling for large datasets (>1000 products)
- Use React Query or SWR for data caching
- Debounce search input (300ms)
- Lazy load product detail modal

### 8.2 Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation for table rows
- Screen reader support for status badges
- Focus management in modal

### 8.3 Internationalization
- Support Thai (th) and English (en) languages
- Thai Baht (฿) currency formatting
- Thai category and product names
- Date formatting per locale

### 8.4 Data Refresh
- Auto-refresh prices every 5 minutes (configurable)
- Show "Last updated" timestamp
- Manual refresh button
- Real-time updates via WebSocket (future enhancement)

---

## 9. Acceptance Criteria

1. **Table Display**
   - [ ] Shows all 5 retailers in columns
   - [ ] Displays product image, name, SKU, category, brand
   - [ ] Prices are clickable and open retailer URLs
   - [ ] Status badge correctly shows Cheapest/Higher/Same

2. **Filtering & Search**
   - [ ] Search by product name, SKU, brand
   - [ ] Filter by category dropdown
   - [ ] Filter by brand dropdown
   - [ ] Reset clears all filters
   - [ ] Filters persist on page refresh (URL params)

3. **Sorting & Pagination**
   - [ ] Sort by any column (click header)
   - [ ] Pagination with configurable page size
   - [ ] Shows "Showing X of Y products"

4. **Export**
   - [ ] Export to CSV with all visible columns
   - [ ] Export respects current filters
   - [ ] Filename includes date

5. **Product Detail Modal**
   - [ ] Opens on row click
   - [ ] Shows Thai Watsadu product details
   - [ ] Shows matched competitor products
   - [ ] Close on ESC or click outside

6. **Visual Indicators**
   - [ ] Green badge for cheapest price
   - [ ] Yellow/orange badge for higher price
   - [ ] Gray badge for same price
   - [ ] "-" for unavailable prices
   - [ ] Highlight lowest/highest prices in row

---

## 10. Dependencies

### NPM Packages (to add if not present)
```json
{
  "dependencies": {
    "@tanstack/react-table": "^8.x",     // Table management
    "papaparse": "^5.x",                  // CSV export (already present)
    "xlsx": "^0.18.x",                    // Excel export
    "recharts": "^2.x"                    // Charts (already present)
  }
}
```

---

## 11. Mock Data Example

```json
{
  "products": [
    {
      "id": "1",
      "sku": "1145439",
      "name": "SPC NARA CREAM 17.78X121.92X0.4 CM.",
      "category": "กระเบื้อง",
      "brand": "XX",
      "imageUrl": "/products/spc-nara-cream.jpg",
      "prices": {
        "thai_watsadu": { "price": 100, "productUrl": "https://thaiwatsadu.com/...", "inStock": true },
        "homepro": { "price": 150, "productUrl": "https://homepro.co.th/...", "inStock": true },
        "global_house": { "price": 120, "productUrl": "https://globalhouse.co.th/...", "inStock": true },
        "dohome": { "price": 100, "productUrl": "https://dohome.co.th/...", "inStock": true },
        "boonthavorn": { "price": 100, "productUrl": "https://boonthavorn.com/...", "inStock": true }
      },
      "status": "cheapest"
    }
  ]
}
```

---

## 12. Next Steps

After approval, implementation will proceed in the following order:
1. Set up project structure and types
2. Create API endpoints with mock data
3. Build UI components bottom-up (Badge → Cell → Row → Table)
4. Create main products page
5. Add filtering, sorting, pagination
6. Implement detail modal
7. Add export functionality
8. Polish and test
