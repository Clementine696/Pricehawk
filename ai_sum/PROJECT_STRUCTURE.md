# PriceHawk Project Structure

Visual guide to the codebase organization.

## 📁 Complete Directory Tree

```
PriceHawk/_PROD/
│
├── ai_sum/                          # ← AI Agent Documentation Hub
│   ├── INDEX.md                     # Quick reference guide
│   ├── README.md                    # Folder overview
│   ├── SUMMARY.md                   # ← MAIN DOCS - Read this first!
│   ├── AI_AGENT_INSTRUCTIONS.md    # Development guidelines
│   ├── PROJECT_STRUCTURE.md        # This file
│   └── sessions/                    # Session logs
│       └── 2026-01-28.md           # Latest session
│
├── backend/                         # FastAPI Backend (Python)
│   ├── main.py                      # ← Main API endpoints
│   ├── database.py                  # Database connection
│   ├── requirements.txt             # Python dependencies
│   ├── railway.toml                 # Railway deployment config
│   ├── nixpacks.toml               # Nixpacks build config
│   │
│   ├── services/                    # Background services
│   │   └── price_updater.py        # Cron job for price updates
│   │
│   └── scraper-url/adws/           # Web scraping modules
│       ├── adw_ecommerce_product_scraper.py
│       └── adw_modules/
│           ├── crawl4ai_wrapper.py      # Browser automation
│           ├── product_extractor.py     # Retailer-specific extractors
│           └── data_models.py           # Product data models
│
├── ui/                              # Next.js Frontend (TypeScript)
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   │
│   ├── public/
│   │   └── logos/
│   │       └── pricehawk_logo.svg
│   │
│   └── src/
│       ├── app/                     # Next.js 14 App Router
│       │   ├── layout.tsx           # Root layout (Google Analytics)
│       │   ├── page.tsx             # Home (redirects to login)
│       │   │
│       │   ├── login/
│       │   │   └── page.tsx         # Login page
│       │   │
│       │   ├── dashboard/
│       │   │   └── page.tsx         # Dashboard with statistics
│       │   │
│       │   ├── products/
│       │   │   ├── page.tsx         # Product listing & filters
│       │   │   └── [id]/
│       │   │       └── page.tsx     # Product detail + matches
│       │   │
│       │   ├── manual-add/
│       │   │   └── page.tsx         # Manual comparison wizard
│       │   │
│       │   ├── watchlist-category/
│       │   │   └── page.tsx         # Category watchlist
│       │   │
│       │   ├── watchlist-sku/
│       │   │   └── page.tsx         # ← SKU watchlist with import
│       │   │
│       │   └── comparison/
│       │       └── page.tsx         # ← Match verification table
│       │
│       ├── components/
│       │   └── layout/
│       │       ├── MainLayout.tsx   # Main app layout wrapper
│       │       └── Sidebar.tsx      # ← Navigation sidebar
│       │
│       ├── context/
│       │   └── AuthContext.tsx      # Authentication state
│       │
│       └── lib/
│           └── api.ts               # API fetch wrapper
│
├── database/
│   └── init/
│       └── 01_schema.sql           # ← Database schema (PostgreSQL)
│
├── seeder/                          # Data seeding scripts
│   ├── seed_products.py            # Seed products from JSON
│   ├── upload_matches.py           # Upload product matches
│   └── *.json                      # Product data files
│
├── results/                         # Scraper output files
│
└── logs/                           # Application logs (if any)
```

---

## 🎯 Key Files by Function

### Authentication & Session
```
backend/main.py (lines 40-50)       # Session configuration
ui/src/context/AuthContext.tsx     # Auth state management
ui/src/app/login/page.tsx          # Login UI
```

### Product Management
```
backend/main.py (lines 200-400)    # Product endpoints
ui/src/app/products/page.tsx       # Product listing
ui/src/app/products/[id]/page.tsx  # Product detail
```

### Price Comparison
```
backend/main.py (lines 500-600)    # Match endpoints
ui/src/app/comparison/page.tsx     # Match verification UI
```

### Watchlist Features
```
backend/main.py (lines 700-900)    # Watchlist endpoints
ui/src/app/watchlist-category/page.tsx
ui/src/app/watchlist-sku/page.tsx  # Excel import/export
```

### Web Scraping
```
backend/scraper-url/adws/
  ├── adw_ecommerce_product_scraper.py  # Main scraper
  └── adw_modules/
      ├── crawl4ai_wrapper.py           # Playwright browser
      └── product_extractor.py          # Retailer extractors
```

### Database
```
database/init/01_schema.sql        # Schema definition
backend/database.py                # Connection setup
```

---

## 🗺️ Navigation Map

### By Feature

**Dashboard**
- Entry point: `ui/src/app/dashboard/page.tsx`
- API: `GET /api/dashboard/stats`
- Shows: Product counts, pending reviews, statistics

**Product Listing**
- Entry point: `ui/src/app/products/page.tsx`
- API: `GET /api/products`
- Features: Search, filters, pagination, export

**Product Detail**
- Entry point: `ui/src/app/products/[id]/page.tsx`
- API: `GET /api/products/{id}`
- Features: Price history, matches, rescrape

**Watchlist (Category)**
- Entry point: `ui/src/app/watchlist-category/page.tsx`
- API: `GET /api/watchlist/groups`
- Features: Group management, export

**Watchlist (SKU)**
- Entry point: `ui/src/app/watchlist-sku/page.tsx`
- API: `GET /api/watchlist/sku-groups`
- Features: Excel import/export, SKU management

**Comparison**
- Entry point: `ui/src/app/comparison/page.tsx`
- API: `GET /api/matches/grouped`
- Features: Match verification, search

**Manual Add**
- Entry point: `ui/src/app/manual-add/page.tsx`
- API: `POST /api/comparison/manual`
- Features: URL scraping, comparison wizard

---

## 📦 Module Dependencies

### Frontend Dependencies (package.json)
- next (14.x) - React framework
- react (18.x)
- typescript
- tailwindcss - Styling
- lucide-react - Icons
- recharts - Charts (price history)

### Backend Dependencies (requirements.txt)
- fastapi - Web framework
- sqlalchemy - Database ORM
- playwright - Browser automation
- crawl4ai - Web scraping
- pandas - Excel processing
- openpyxl - Excel export
- python-multipart - File uploads

---

## 🔌 API Endpoint Map

### Authentication
```
POST   /api/auth/login       → backend/main.py:~100
POST   /api/auth/logout      → backend/main.py:~120
GET    /api/auth/me          → backend/main.py:~130
```

### Products
```
GET    /api/products                → backend/main.py:~200
GET    /api/products/{id}           → backend/main.py:~300
GET    /api/products/export         → backend/main.py:~400
POST   /api/products/{id}/rescrape  → backend/main.py:~500
```

### Matches
```
GET    /api/matches/pending         → backend/main.py:~600
GET    /api/matches/grouped         → backend/main.py:~650
POST   /api/matches/{id}/verify     → backend/main.py:~700
```

### Watchlist (Category)
```
GET    /api/watchlist/groups           → backend/main.py:~800
POST   /api/watchlist/groups           → backend/main.py:~850
DELETE /api/watchlist/groups/{id}     → backend/main.py:~900
GET    /api/watchlist/groups/{id}/export → backend/main.py:~950
```

### Watchlist (SKU)
```
GET    /api/watchlist/sku-groups              → backend/main.py:~1000
POST   /api/watchlist/sku-groups              → backend/main.py:~1050
POST   /api/watchlist/sku-groups/import-excel → backend/main.py:~1100
GET    /api/watchlist/sku-groups/{id}/export  → backend/main.py:~1150
```

### Dashboard
```
GET    /api/dashboard/stats         → backend/main.py:~1200
```

---

## 🎨 Frontend Component Hierarchy

```
layout.tsx (Root)
└── AuthProvider
    └── MainLayout
        ├── Sidebar
        │   ├── Logo
        │   ├── Navigation Menu
        │   │   ├── Dashboard
        │   │   ├── Products
        │   │   ├── Manual Add
        │   │   ├── Watchlist Category
        │   │   ├── Watchlist SKU
        │   │   └── Comparison
        │   └── User Section
        └── Main Content (page.tsx)
            └── Page-specific components
```

---

## 🗄️ Database Schema Overview

```
retailers
├── retailer_id (PK)
├── name
└── domain

products
├── product_id (PK)
├── retailer_id (FK)
├── sku
├── name
├── current_price
├── last_updated_at
└── scrape_fail_count

product_matches
├── match_id (PK)
├── base_product_id (FK)
├── candidate_product_id (FK)
├── is_same
├── confidence_score
└── verified_by_user

price_history
├── price_id (PK)
├── product_id (FK)
├── price
└── scraped_at

watchlist_groups
├── group_id (PK)
├── name
└── display_name

watchlist_group_products
├── id (PK)
├── group_id (FK)
├── product_id (FK)
└── added_at

watchlist_sku_groups
├── group_id (PK)
├── name
└── display_name

watchlist_sku_group_products
├── id (PK)
├── group_id (FK)
├── sku
└── added_at

users
├── user_id (PK)
├── username
└── hashed_password
```

---

## 🔄 Data Flow Examples

### Product Search Flow
```
User Input (products/page.tsx)
    ↓
API Request: GET /api/products?search=...
    ↓
Backend: main.py → database.py → PostgreSQL
    ↓
SQL: SELECT * FROM products WHERE name LIKE %...%
    ↓
Response: JSON product list
    ↓
Frontend: Render product table
```

### Excel Import Flow (Watchlist SKU)
```
User Upload Excel (watchlist-sku/page.tsx)
    ↓
API Request: POST /api/watchlist/sku-groups/import-excel
    ↓
Backend: pandas reads Excel → process groups/SKUs
    ↓
Database: INSERT INTO watchlist_sku_groups, watchlist_sku_group_products
    ↓
Response: Import results (groups_updated, skus_added, skus_not_found)
    ↓
Frontend: Display import result modal
```

### Price Update Flow
```
Cron Job: services/price_updater.py (hourly/daily)
    ↓
Fetch products needing update (oldest first)
    ↓
For each product:
    ├─→ scraper-url/adws/crawl4ai_wrapper.py (Playwright)
    ├─→ scraper-url/adws/product_extractor.py (parse HTML)
    └─→ Extract price, name, etc.
    ↓
Database: UPDATE products SET current_price, last_updated_at
    ↓
Database: INSERT INTO price_history
```

---

## 🎯 Where to Make Changes

### Adding a New Feature
1. Backend API: `backend/main.py` (new endpoint)
2. Frontend UI: `ui/src/app/[feature]/page.tsx`
3. Sidebar: `ui/src/components/layout/Sidebar.tsx` (add menu item)
4. Database: `database/init/01_schema.sql` (if needed)
5. Documentation: `ai_sum/SUMMARY.md`

### Modifying Styling
- Global styles: `ui/src/app/globals.css`
- Tailwind config: `ui/tailwind.config.ts`
- Component styles: Inline Tailwind classes

### Adding a New Retailer
1. Database: Add to `retailers` table
2. Scraper: `backend/scraper-url/adws/adw_modules/product_extractor.py`
3. Frontend: Update retailer lists/filters

### Changing Database Schema
1. Update: `database/init/01_schema.sql`
2. Migration: Create migration script (if production)
3. Backend: Update models/queries in `backend/main.py`
4. Documentation: Update `ai_sum/SUMMARY.md`

---

**Last Updated**: 2026-01-28
