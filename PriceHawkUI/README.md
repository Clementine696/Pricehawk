# PriceHawk - Price Monitoring System

A comprehensive **Product Price Comparison Overview Page** for monitoring and comparing product prices across five major Thai home improvement retailers.

## Overview

PriceHawk allows users to compare the same products (by category and SKU) across:
- **Thai Watsadu** (reference/primary retailer)
- **HomePro**
- **Global House**
- **DoHome**
- **Boonthavorn**

## Features

- ✅ **Price Comparison Table** - View prices from all 5 retailers in one table
- ✅ **Clickable Price Links** - Opens product page on retailer's website
- ✅ **Status Badges** - Shows Thai Watsadu's competitive position (Cheapest/Higher/Same)
- ✅ **Search & Filter** - By name, SKU, brand, and category
- ✅ **CSV Export** - Export filtered data for reporting
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile
- ✅ **Real-time Filtering** - Instant table updates as you filter

## Technology Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with Lucide icons
- **Export**: PapaParse for CSV generation
- **Build Tool**: Webpack (via Next.js)

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server (runs on port 3000)
npm run dev

# Open http://localhost:3000/products
```

**Note**: The development server is configured to run on port 3000 by default. If you encounter an EADDRINUSE error, you can:
- Kill any existing process on the port: `lsof -ti:3000 && kill -9 $(lsof -ti:3000)`
- Or modify the port in `package.json` dev script: `"dev": "next dev -p <port>"`

### Build for Production

```bash
# Type check
npm run type-check

# Lint code
npm run lint

# Build application
npm run build

# Start production server
npm start
```

## Project Structure

```
PriceHack/
├── app/
│   ├── (main)/
│   │   └── products/
│   │       └── page.tsx          # Main products page
│   ├── api/
│   │   └── products/
│   │       └── comparison/
│   │           ├── route.ts      # List API endpoint
│   │           └── [id]/
│   │               └── route.ts  # Detail API endpoint
│   ├── layout.tsx                # Root layout
│   ├── globals.css               # Global styles
│   └── page.tsx                  # Home page (redirects to /products)
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   └── MainLayout.tsx        # Main layout wrapper
│   └── products/
│       ├── PriceComparisonTable.tsx
│       ├── PriceComparisonRow.tsx
│       ├── PriceCell.tsx
│       ├── StatusBadge.tsx
│       ├── ProductSearchFilter.tsx
│       └── ExportButton.tsx
│
├── lib/
│   ├── types/
│   │   └── price-comparison.ts   # TypeScript type definitions
│   └── utils/
│       ├── price-utils.ts        # Price calculation utilities
│       └── export-utils.ts       # CSV export utilities
│
├── data/
│   └── mock-products.json        # Mock product data
│
├── public/                       # Static assets
├── specs/                        # Specification documents
├── expected/                     # UI reference images
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Key Components

### Status Badge Logic

The system determines price status using a 2% threshold:

- **Cheapest** (Green): Thai Watsadu price ≤ minimum competitor price + 2%
- **Higher** (Yellow/Orange): Thai Watsadu price ≥ maximum competitor price - 2%
- **Same** (Gray): Thai Watsadu price within ±2% of competitor range
- **N/A** (Light Gray): No competitor prices available

### API Endpoints

#### GET /api/products/comparison

Returns paginated product list with filtering and sorting support.

**Query Parameters:**
- `search` - Search by name, SKU, brand
- `category` - Filter by category
- `brand` - Filter by brand
- `status` - Filter by price status
- `page` - Page number (default: 1)
- `pageSize` - Items per page (default: 10)
- `sortBy` - Sort field (name, sku, category, brand, price, status)
- `sortOrder` - Sort direction (asc, desc)

**Response:**
```json
{
  "products": [...],
  "pagination": { "page": 1, "pageSize": 10, "total": 50, "totalPages": 5 },
  "filters": { "categories": [...], "brands": [...] },
  "summary": { "totalProducts": 50, "cheapestCount": 20, ... }
}
```

#### GET /api/products/comparison/:id

Returns detailed product information with price history.

### Data Model

See `lib/types/price-comparison.ts` for complete type definitions.

## Development

### Mock Data

The application uses mock data from `data/mock-products.json` for development. In production, this should be replaced with actual database queries.

### Adding New Retailers

1. Add retailer to `Retailer` enum in `lib/types/price-comparison.ts`
2. Add display name to `RetailerNames` mapping
3. Update `ProductComparison` interface prices object
4. Add table column in `PriceComparisonTable.tsx`
5. Add price cell in `PriceComparisonRow.tsx`

## Deployment

### Environment Variables

No environment variables required for basic functionality. Add as needed for production database connections.

### Build Artifacts

- `.next/` - Build output (gitignored)
- `node_modules/` - Dependencies (gitignored)

## Validation Commands

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build

# Start dev server
npm run dev
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Performance

- Server-side rendering for initial page load
- Client-side filtering and sorting for instant updates
- Debounced search input (300ms)
- Pagination for large datasets

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast meets WCAG AA standards

## License

Proprietary - Internal use only

## Contributors

- Built with Claude Code
- Specification: `specs/chore-0422addd-product-price-comparison-overview.md`

## Support

For issues or questions, refer to the specification documents in the `specs/` directory.
# PriceHawkUI
