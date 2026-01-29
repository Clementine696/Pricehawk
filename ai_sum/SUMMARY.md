# PriceHawk - Price Comparison Platform

A price comparison platform for Thai home improvement retailers that tracks and compares product prices across multiple stores.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   Database      │
│   (Vercel)      │     │   (Railway)     │     │   (Neon)        │
│   Next.js 14    │     │   FastAPI       │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │    Scraper      │
                        │  (Playwright +  │
                        │   crawl4ai)     │
                        └─────────────────┘
```

## Tech Stack

| Component | Technology | Hosting |
|-----------|------------|---------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Vercel |
| Backend | FastAPI, Python 3.11 | Railway |
| Database | PostgreSQL 15 | Neon |
| Scraper | Playwright, crawl4ai | Railway (via backend) |

---

## Project Structure

```
PriceHawk/_PROD/
├── backend/                    # FastAPI backend
│   ├── main.py                 # Main API endpoints
│   ├── database.py             # Database connection
│   ├── requirements.txt        # Python dependencies
│   ├── railway.toml            # Railway config (force nixpacks)
│   ├── nixpacks.toml           # Nixpacks config (Playwright deps)
│   └── scraper-url/adws/       # Scraper modules
│       ├── adw_ecommerce_product_scraper.py
│       └── adw_modules/
│           ├── crawl4ai_wrapper.py   # Browser scraping wrapper
│           ├── product_extractor.py  # Retailer-specific extractors
│           └── data_models.py        # Product data models
│
├── ui/                         # Next.js frontend
│   ├── src/app/
│   │   ├── page.tsx            # Home (redirects to login)
│   │   ├── login/page.tsx      # Login page
│   │   ├── dashboard/page.tsx  # Dashboard
│   │   ├── products/page.tsx   # Products list
│   │   ├── products/[id]/page.tsx  # Product detail + matches
│   │   ├── comparison/page.tsx # Match verification
│   │   └── manual-add/page.tsx # Manual comparison wizard
│   ├── src/components/
│   │   └── layout/             # MainLayout, Sidebar
│   └── src/context/
│       └── AuthContext.tsx     # Auth state management
│
├── database/init/
│   └── 01_schema.sql           # Database schema
│
├── seeder/                     # Data seeding scripts
│   ├── seed_products.py        # Seed products from JSON
│   ├── upload_matches.py       # Upload product matches
│   └── *.json                  # Product data files
│
└── results/                    # Scraper output files
```

---

## Database Schema

### Tables

#### 1. `retailers`
Stores retailer information.
```sql
retailer_id VARCHAR(10) PRIMARY KEY  -- twd, hp, dh, btv, gbh, mgh
name TEXT NOT NULL
domain TEXT UNIQUE
```

**Retailers:**
| ID | Name | Domain |
|----|------|--------|
| twd | Thai Watsadu | thaiwatsadu.com |
| hp | HomePro | homepro.co.th |
| dh | Do Home | dohome.co.th |
| btv | Boonthavorn | boonthavorn.com |
| gbh | Global House | globalhouse.co.th |
| mgh | MegaHome | megahome.co.th |

#### 2. `products`
Stores all product information from all retailers.
```sql
product_id SERIAL PRIMARY KEY
retailer_id VARCHAR(10) REFERENCES retailers
sku TEXT NOT NULL
name TEXT
brand TEXT
category TEXT
link TEXT NOT NULL              -- Product URL for scraping
image TEXT
current_price DECIMAL(10, 2)
original_price DECIMAL(10, 2)
lowest_price DECIMAL(10, 2)     -- Historical lowest
highest_price DECIMAL(10, 2)    -- Historical highest
last_updated_at TIMESTAMP
scrape_fail_count INTEGER DEFAULT 0  -- Consecutive scrape failures (skip at 3)
UNIQUE (retailer_id, sku)
```

#### 3. `product_matches`
Stores matches between Thai Watsadu products and competitor products.
```sql
match_id SERIAL PRIMARY KEY
base_product_id INTEGER REFERENCES products      -- Thai Watsadu product
candidate_product_id INTEGER REFERENCES products -- Competitor product
retailer_id VARCHAR(10)
is_same BOOLEAN                 -- Match result
confidence_score NUMERIC(5,4)   -- 0.0000 to 1.0000
match_type TEXT                 -- 'auto', 'manual', 'exact', 'fuzzy'
verified_by_user BOOLEAN        -- Human verified?
UNIQUE (base_product_id, candidate_product_id)
```

#### 4. `price_history`
Tracks price changes over time.
```sql
price_id SERIAL PRIMARY KEY
product_id INTEGER REFERENCES products
price DECIMAL(10, 2)
scraped_at TIMESTAMP DEFAULT NOW()
```

#### 5. `users`
Application users.
```sql
user_id SERIAL PRIMARY KEY
username VARCHAR(50) UNIQUE
hashed_password VARCHAR(255)
is_active BOOLEAN DEFAULT TRUE
```

---

## Backend API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with username/password, returns token |
| POST | `/api/auth/logout` | Logout and clear session |
| GET | `/api/auth/me` | Get current user info |

**Authentication Methods:**
- **Bearer Token** (recommended): Store token from login response in localStorage, send as `Authorization: Bearer <token>` header
- **Cookie** (fallback): HTTP-only session cookie with `SameSite=None; Secure; Partitioned` for cross-origin

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List products with pagination, search, filters |
| GET | `/api/products/{id}` | Get product detail with all matches |
| GET | `/api/products/export` | Export products to Excel (.xlsx) with hyperlinked prices |
| POST | `/api/products/{id}/rescrape` | Rescrape prices for product and verified matches |

### Matches
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/matches/pending` | Get unverified matches |
| POST | `/api/matches/{id}/verify` | Verify a match (is_same: true/false) |

### Scraping
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scrape` | Scrape product URLs |
| POST | `/api/comparison/manual` | Manual comparison wizard |

---

## Frontend Pages

### `/login`
Login page with username/password authentication.

### `/dashboard`
Overview with statistics:
- Total products count
- Products by retailer
- Match verification progress

### `/products`
Product listing with:
- Search by name/SKU/brand
- Filter by category (multi-select), brand (multi-select), status (single-select), retailer (single-select)
- Pagination
- Export to Excel (.xlsx) with hyperlinked prices

### `/products/[id]`
Product detail view:
- Thai Watsadu product info
- Matched products from all retailers
- Verify/reject matches
- Add manual matches
- **Rescrape Prices** button - updates prices for base product + all verified matches

### `/manual-add`
4-step manual comparison wizard:
1. **Input**: Enter Thai Watsadu SKU + competitor URLs
2. **Review**: Confirm URLs to scrape
3. **Scraping**: Live progress of scraping (validates name AND price extracted)
4. **Results**: Side-by-side comparison table

Features:
- URL domain validation (ensures URL matches selected retailer)
- Scraped data validation (requires both name and price to proceed)
- Shows existing matches for the SKU
- Clear errors when navigating back to edit inputs

---

## Deployment

### Frontend (Vercel)
```bash
# Automatic deployment from Git
# Environment variables:
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Backend (Railway)
```bash
# Uses nixpacks for building
# Key files:
railway.toml     # Forces nixpacks builder
nixpacks.toml    # Installs Playwright dependencies

# Environment variables:
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://your-frontend.vercel.app
```

#### nixpacks.toml Configuration
```toml
[phases.setup]
nixPkgs = [
  "glib", "nss", "nspr", "atk", "cups", "dbus", "expat",
  "libdrm", "libxkbcommon", "pango", "cairo", "alsa-lib",
  "mesa", "gtk3", "xorg.libX11", "xorg.libXcomposite",
  "xorg.libXdamage", "xorg.libXext", "xorg.libXfixes",
  "xorg.libXrandr", "xorg.libxcb", "freetype", "fontconfig",
  "gdk-pixbuf"
]

[phases.build]
cmds = [
  "playwright install-deps",
  "playwright install chromium"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

### Database (Neon)
- Serverless PostgreSQL
- Connection string in `DATABASE_URL`

---

## Scraper Details

### Supported Retailers
| Retailer | Extractor Class | Notes |
|----------|-----------------|-------|
| Thai Watsadu | `ThaiWatsaduExtractor` | Base retailer |
| HomePro | `HomeProExtractor` | |
| Do Home | `DoHomeExtractor` | |
| Boonthavorn | `BoonthavornExtractor` | |
| Global House | `GlobalHouseExtractor` | |
| MegaHome | `MegaHomeExtractor` | |

### Scraping Flow
1. Receive URL via API
2. Detect retailer from domain
3. Use Playwright browser to fetch page
4. Execute JavaScript to:
   - Scroll page (lazy loading)
   - Click "Read More" buttons
   - Click specification tabs
5. Extract data with retailer-specific patterns
6. Return structured product data

### Data Extracted
- Product name
- SKU
- Brand
- Category
- Current price
- Original price
- Discount info
- Images
- Description
- Specifications (dimensions, volume, etc.)

---

## Data Flow

### Adding Products
```
1. Seed products from JSON files
   seeder/seed_products.py → products table

2. Upload matches from Excel files
   seeder/upload_matches.py → product_matches table
```

### Manual Comparison
```
1. User enters Thai Watsadu URL + competitor URLs
2. Backend scrapes all URLs
3. Frontend displays comparison table
4. User verifies matches
5. Matches saved to product_matches table
```

### Price Updates
```
1. Cron job runs daily
2. Fetch all products from database (grouped by retailer)
3. Scrape each product URL using retailer-specific extractors
4. Update current_price, lowest_price, highest_price in products table
5. Insert record into price_history table
```

#### Price Updater CLI
```bash
cd backend

# Update all products (sequential)
python services/price_updater.py

# Parallel processing (3 retailers at once) - recommended
python services/price_updater.py --parallel 3

# or up to 20 workers
python services/price_updater.py --parallel 20

# Update specific retailer only
python services/price_updater.py --retailer twd

# Custom batch size
python services/price_updater.py --batch-size 100

# Test without updating database
python services/price_updater.py --dry-run

# Full options
python services/price_updater.py --parallel 3 --batch-size 50 --delay 1.0
```

#### CLI Options
| Option | Description |
|--------|-------------|
| `--retailer, -r` | Specific retailer (twd, hp, dh, btv, gbh, mgh) |
| `--batch-size, -b` | Products per batch (default: 50) |
| `--delay, -d` | Delay between products in seconds (default: 1.0) |
| `--parallel, -p` | Parallel workers: 1=sequential, 2-20=parallel (default: 1) |
| `--dry-run` | Test without updating database |
| `--verbose, -v` | Verbose output |

#### Environment Variables (for cron)
```env
UPDATE_BATCH_SIZE=50      # Products per batch (default: 50)
UPDATE_DELAY=1.0          # Delay between products in seconds (default: 1.0)
UPDATE_PARALLEL=3         # Parallel workers (default: 1)
UPDATE_RETAILER=          # Optional: specific retailer (twd, hp, dh, etc.)
UPDATE_LIMIT=100          # Optional: limit to N oldest products (for hourly cron)
```

#### Failure Tracking
Products that fail to scrape are tracked with `scrape_fail_count`:
- Each failed scrape increments the counter
- Products with 3+ consecutive failures are automatically skipped
- Counter resets to 0 on successful scrape
- Prevents broken URLs from clogging the update queue

#### Browser Memory Management
The scraper includes memory management to prevent crashes on Railway:
- Proactive browser restart every 10 scrapes
- Memory cooldown pause every 15 products (10 second pause)
- Automatic cleanup of Playwright temp directories
- Batch cleanup every 3 batches

---

## Environment Variables

### Backend
```env
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
CORS_ORIGINS=https://pricehawk.vercel.app
```

### Frontend
```env
NEXT_PUBLIC_API_URL=https://pricehawk-api.railway.app
```

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Set environment variables
export DATABASE_URL="postgresql://..."

# Run
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd ui
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run
npm run dev
```

---

## Cron Job Setup (Railway)

### Price Update Cron Service
Create a separate Railway service for the cron job:

1. **Service Setup**
   - Create new service in Railway
   - Set command: `python update_prices.py`
   - Set schedule: `0 * * * *` (hourly) or `0 2 * * *` (daily at 2 AM UTC)

2. **Environment Variables**
   ```env
   DATABASE_URL=postgresql://...
   UPDATE_BATCH_SIZE=50
   UPDATE_DELAY=1.0
   UPDATE_PARALLEL=3
   UPDATE_LIMIT=100          # For hourly: process 100 oldest products
   ```

3. **How It Works**
   - Fetches N oldest products (by `last_updated_at ASC NULLS FIRST`)
   - Skips products with 3+ consecutive failures
   - Splits work among parallel workers
   - Updates prices and records failures
   - Cleans up browser resources to prevent memory leaks

### Recommended Configurations

**Hourly Cron (Incremental)**
```env
UPDATE_LIMIT=100
UPDATE_PARALLEL=3
```
- Processes 100 oldest products each hour
- Good for keeping prices fresh without overloading

**Daily Cron (Full Update)**
```env
UPDATE_LIMIT=           # No limit - process all
UPDATE_PARALLEL=3
```
- Processes all products once per day
- Run during off-peak hours (e.g., 2 AM)


3. **How It Works**
   - Fetches N oldest products (by `last_updated_at ASC NULLS FIRST`)
   - Skips products with 3+ consecutive failures
   - Splits work among parallel workers
   - Updates prices and records failures
   - Cleans up browser resources to prevent memory leaks

### Recommended Configurations

**Hourly Cron (Incremental)**
```env
UPDATE_LIMIT=100
UPDATE_PARALLEL=3
```
- Processes 100 oldest products each hour
- Good for keeping prices fresh without overloading

**Daily Cron (Full Update)**
```env
UPDATE_LIMIT=           # No limit - process all
UPDATE_PARALLEL=3
```
- Processes all products once per day
- Run during off-peak hours (e.g., 2 AM)

---

## Recent Changes (January 2026)

### Production Stability Fixes (2026-01-29)
- **Memory Leak Fixes in Price Updater**
  - Fixed memory exhaustion limiting cron job to ~150 products
  - Now handles 1000+ products with stable memory (48% at 150 products)
  - Added psutil-based browser cleanup
  - Real-time memory monitoring with auto-pause at 80% threshold
  - Aggressive cleanup: every 10 products + every 2 batches
  - Test results: 150 products in 14min 33sec, 82% success rate

- **Thread Exhaustion Fix in Manual Scraping**
  - Fixed `RuntimeError: can't start new thread` during manual product addition
  - Changed subprocess.run to subprocess.Popen for better process control
  - Uses psutil to kill entire process trees (parent + Chrome children)
  - Added cleanup_zombie_browser_processes() function

- **Safe Browser Cleanup**
  - Only kills scraper browsers (playwright/crawl4ai), NOT user's Chrome
  - Checks for --headless, --disable-dev-shm-usage flags
  - Excludes processes with user profile directories

- **Excel Upload Routing Fix**
  - Fixed 405 "Method Not Allowed" error for Excel uploads
  - Added Vercel-to-Railway routing configuration (vercel.json)
  - Created environment-specific configs (vercel.uat.json, vercel.prd.json)
  - Added OPTIONS handler for CORS pre-flight requests

- **See:** `ai_sum/sessions/2026-01-29_memory-leak-and-thread-exhaustion-fixes.md`

### Session & Authentication
- **Session expiry extended to 7 days** (previously 30 minutes)
  - `SESSION_EXPIRE_MINUTES = 10080` in `backend/main.py` line 44

### Products Page Enhancements
- **"Watched Only" filter** - Checkbox to filter products table and export to only categories in user's watchlist
- **Export from Watchlist page** - Simple export button on watchlist page
- **Category/Brand dropdowns filter** - When "Watched Only" is enabled, dropdowns only show watched categories
- **Price change indicators** - Trending arrows (green down ↓, red up ↑) on products list showing recent price changes

### Product Detail Page
- **Price History Graph** - Interactive chart with time range toggles (7D, 1M, 3M, 6M, 1Y) using Recharts
- **Last Updated timestamps** - Shows when each product (base and matched) was last scraped
  - Format: "Just now", "X mins ago", "X hours ago", "X days ago", or full date
  - UTC timezone handling: timestamps from DB (UTC) are properly converted to local time
- **Image loading improvements** - ProductImage component with:
  - Loading spinner
  - 8-second timeout with auto-retry (up to 3 times)
  - Manual retry button

### Retailer Name Aliasing
MegaHome is stored as "Mega Home" in database but frontend expects "MegaHome". Added alias handling:

**Frontend** (`ui/src/app/products/page.tsx`):
```typescript
const RETAILER_NAME_ALIASES: Record<string, string> = {
  'Mega Home': 'MegaHome',
  'megahome': 'MegaHome',
  'DoHome': 'Do Home',
  'GlobalHouse': 'Global House',
  'Home Pro': 'HomePro',
};
```

**Backend Export** (`backend/main.py` ~line 730):
```python
retailer_aliases = {
    'MegaHome': ['Mega Home', 'megahome'],
    'Do Home': ['DoHome', 'dohome'],
    'Global House': ['GlobalHouse', 'globalhouse'],
    'HomePro': ['Home Pro', 'homepro'],
}
```

### Export Verification Filter Fix
Fixed export to use same verification logic as products table:
- **Before**: Export's "verified" filter was stricter (required NO unreviewed matches)
- **After**: Matches table filter logic (verified = no retailers needing review)
- This ensures export count matches table count when filtering

### Boonthavorn Scraping Fix
Fixed scraping failures on Railway (worked locally):
- Added `wait_for` condition in `crawl4ai_wrapper.py` specifically for Boonthavorn URLs
- Waits for JSON-LD with price or price element to appear before extracting data

### Google Analytics
Added Google Analytics tracking (`G-Y4YCTMYX01`) in `ui/src/app/layout.tsx`:
- Uses Next.js `<Script>` component with `strategy="afterInteractive"`
- Automatically tracks page views across all pages

### Dashboard Statistics
The dashboard (`/api/dashboard/stats`) calculates:
| Stat | Calculation |
|------|-------------|
| Total Products | Count of Thai Watsadu products only |
| Retailers | Count of all retailers |
| Pending Reviews | TWD products with at least 1 retailer needing review |
| Product Matches | `Total Products - Pending Reviews` |

**"Needs Review" logic**: A retailer needs review if:
1. No verified correct match exists (`verified_by_user = TRUE AND is_same = TRUE`)
2. AND there are still unreviewed matches (`verified_by_user = FALSE`)

This same logic is used in:
- Dashboard pending reviews count
- Products table verified/unverified filter
- Export verified/unverified filter

---

## Watchlist SKU Groups (Added January 2026)

A new feature for tracking products by SKU numbers across retailers, with bulk import/export capabilities.

### Database Schema
```sql
-- Watchlist SKU Groups
CREATE TABLE watchlist_sku_groups (
    group_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SKU Group Products (many-to-many)
CREATE TABLE watchlist_sku_group_products (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES watchlist_sku_groups(group_id) ON DELETE CASCADE,
    sku VARCHAR(50) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, sku)
);
```

### Features

#### 1. Excel Bulk Import
- **Endpoint**: `POST /api/watchlist/sku-groups/import-excel`
- **Format**: Reads `SKU_Number` and `S-dept` columns from Excel file
- **Logic**:
  - Groups SKUs by `S-dept` column value
  - Auto-creates watchlist groups (name = `s_dept.lower().replace(' ', '-')`)
  - Validates SKUs against products table (retailer_id='twd')
  - Returns detailed results: groups_created, groups_updated, skus_added, skus_not_found
- **Frontend**: Green "Import Excel" button with import result modal

#### 2. Group Management
- **List Groups**: `GET /api/watchlist/sku-groups` - Returns all groups with product count
- **Create Group**: `POST /api/watchlist/sku-groups` - Create new group
- **Delete Group**: `DELETE /api/watchlist/sku-groups/{group_id}` - Cascade deletes products
- **Add Product**: `POST /api/watchlist/sku-groups/{group_id}/products/{sku}`
- **Remove Product**: `DELETE /api/watchlist/sku-groups/{group_id}/products/{sku}`

#### 3. Excel Export
- **Endpoint**: `GET /api/watchlist/sku-groups/{group_id}/export`
- **Format**: Same as products page export (Excel with hyperlinked prices)
- **Includes**:
  - All 6 retailers (Thai Watsadu, HomePro, MegaHome, Do Home, Boonthavorn, Global House)
  - Prices are hyperlinked to product pages
  - Status column (cheapest/same/higher)
  - Products sorted by SKU
- **Frontend**: Green "Export" button next to "Manage Products"

#### 4. UI Features
- **Main Page**: Full-width single-column layout showing group cards
  - Each card shows: display name, description, product count
  - Actions: Export (green), Manage Products (cyan), Delete (red)
- **Manage Products Modal**: Fullscreen split view
  - **Left side**: Added products in group (green background)
  - **Right side**: Available products to add (white background)
  - Format: `SKU | Price | Name` in single line, sorted by SKU
  - Small 8x8 product images
  - Search bar to filter available products
- **Sidebar**: Navigation updated
  - "Watchlist Category" (was "Watchlist Groups")
  - "Watchlist SKU" (was "Watchlist SKU Groups")

### Technical Details
- Uses pandas for Excel processing (`pandas>=2.0.0`)
- Frontend uses Next.js 14 with TypeScript and Tailwind CSS
- Product display uses monospace font for SKU alignment
- Export generates timestamped filename: `{group_name}_export_YYYYMMDD_HHMMSS.xlsx`

### Recent UI Updates (January 2026)

#### Import Results Modal Redesign
Updated the Excel import results modal with cleaner design ([page.tsx:596-779](ui/src/app/watchlist-sku/page.tsx#L596-L779)):
- **Styling Improvements**:
  - Border colors changed to `border-gray-300` for better definition
  - White backgrounds for headers and statistics sections
  - Gray-50 background for main content area
  - Rounded-2xl card with shadow-sm for modern look

- **Equal Height Tables**:
  - Both "Groups Updated" and "SKUs Added" tables set to `h-[300px]`
  - Scrollable overflow for consistent layout

- **Unified Button Group**:
  - Combined "Export" and "Expand All" buttons at SKUs Not Found section
  - Single border with separator between buttons
  - Aligned at same level as section header

- **Text Updates**:
  - Changed "ไฟล์ถูกประมวลผลเรียบร้อยแล้ว" to English: "File has been processed successfully"

#### Custom Sidebar Icon
Added custom list-checks SVG icon for Watchlist SKU ([Sidebar.tsx:10-30](ui/src/components/layout/Sidebar.tsx#L10-L30)):
```typescript
const ListChecks: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
       fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m3 17 2 2 4-4"></path>
    <path d="m3 7 2 2 4-4"></path>
    <path d="M13 6h8"></path>
    <path d="M13 12h8"></path>
    <path d="M13 18h8"></path>
  </svg>
);
```

#### Comparison Page Search Enhancement
Enhanced product search to support both name and SKU ([page.tsx:138-145](ui/src/app/comparison/page.tsx#L138-L145)):
```typescript
const filteredProducts = products.filter((product) => {
  const lowerSearch = searchTerm.toLowerCase();
  return (
    product.base_product.name?.toLowerCase().includes(lowerSearch) ||
    product.base_product.sku?.toLowerCase().includes(lowerSearch)
  );
});
```
- Placeholder updated to "Search by name or SKU..."
- Case-insensitive search across both fields

---

## Recent Changes (January 2026)

### Session & Authentication
- **Session expiry extended to 7 days** (previously 30 minutes)
  - `SESSION_EXPIRE_MINUTES = 10080` in `backend/main.py` line 44

### Products Page Enhancements
- **"Watched Only" filter** - Checkbox to filter products table and export to only categories in user's watchlist
- **Export from Watchlist page** - Simple export button on watchlist page
- **Category/Brand dropdowns filter** - When "Watched Only" is enabled, dropdowns only show watched categories
- **Price change indicators** - Trending arrows (green down ↓, red up ↑) on products list showing recent price changes

### Product Detail Page
- **Price History Graph** - Interactive chart with time range toggles (7D, 1M, 3M, 6M, 1Y) using Recharts
- **Last Updated timestamps** - Shows when each product (base and matched) was last scraped
  - Format: "Just now", "X mins ago", "X hours ago", "X days ago", or full date
  - UTC timezone handling: timestamps from DB (UTC) are properly converted to local time
- **Image loading improvements** - ProductImage component with:
  - Loading spinner
  - 8-second timeout with auto-retry (up to 3 times)
  - Manual retry button

### Retailer Name Aliasing
MegaHome is stored as "Mega Home" in database but frontend expects "MegaHome". Added alias handling:

**Frontend** (`ui/src/app/products/page.tsx`):
```typescript
const RETAILER_NAME_ALIASES: Record<string, string> = {
  'Mega Home': 'MegaHome',
  'megahome': 'MegaHome',
  'DoHome': 'Do Home',
  'GlobalHouse': 'Global House',
  'Home Pro': 'HomePro',
};
```

**Backend Export** (`backend/main.py` ~line 730):
```python
retailer_aliases = {
    'MegaHome': ['Mega Home', 'megahome'],
    'Do Home': ['DoHome', 'dohome'],
    'Global House': ['GlobalHouse', 'globalhouse'],
    'HomePro': ['Home Pro', 'homepro'],
}
```

### Export Verification Filter Fix
Fixed export to use same verification logic as products table:
- **Before**: Export's "verified" filter was stricter (required NO unreviewed matches)
- **After**: Matches table filter logic (verified = no retailers needing review)
- This ensures export count matches table count when filtering

### Boonthavorn Scraping Fix
Fixed scraping failures on Railway (worked locally):
- Added `wait_for` condition in `crawl4ai_wrapper.py` specifically for Boonthavorn URLs
- Waits for JSON-LD with price or price element to appear before extracting data

### Google Analytics
Added Google Analytics tracking (`G-Y4YCTMYX01`) in `ui/src/app/layout.tsx`:
- Uses Next.js `<Script>` component with `strategy="afterInteractive"`
- Automatically tracks page views across all pages

### Dashboard Statistics
The dashboard (`/api/dashboard/stats`) calculates:
| Stat | Calculation |
|------|-------------|
| Total Products | Count of Thai Watsadu products only |
| Retailers | Count of all retailers |
| Pending Reviews | TWD products with at least 1 retailer needing review |
| Product Matches | `Total Products - Pending Reviews` |

**"Needs Review" logic**: A retailer needs review if:
1. No verified correct match exists (`verified_by_user = TRUE AND is_same = TRUE`)
2. AND there are still unreviewed matches (`verified_by_user = FALSE`)

This same logic is used in:
- Dashboard pending reviews count
- Products table verified/unverified filter
- Export verified/unverified filter

---

## Future Features (Planned)

1. **Price Alerts**
   - Notify when price drops
   - Configurable thresholds

2. **Analytics Dashboard**
   - Price trends over time
   - Retailer price comparison charts
   - Category-level insights
