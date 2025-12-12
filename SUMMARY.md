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
| POST | `/api/login` | Login with username/password |
| GET | `/api/me` | Get current user info |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List products with pagination, search, filters |
| GET | `/api/products/{id}` | Get product detail with all matches |
| GET | `/api/products/export` | Export products to CSV |

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
- Filter by category, brand
- Pagination
- Export to CSV

### `/products/[id]`
Product detail view:
- Thai Watsadu product info
- Matched products from all retailers
- Verify/reject matches
- Add manual matches

### `/manual-add`
4-step manual comparison wizard:
1. **Input**: Enter Thai Watsadu SKU + competitor URLs
2. **Review**: Confirm URLs to scrape
3. **Scraping**: Live progress of scraping
4. **Results**: Side-by-side comparison table

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
| `--parallel, -p` | Parallel workers: 1=sequential, 2-6=parallel (default: 1) |
| `--dry-run` | Test without updating database |
| `--verbose, -v` | Verbose output |

#### Environment Variables (for cron)
```env
UPDATE_BATCH_SIZE=50
UPDATE_DELAY=1.0
UPDATE_PARALLEL=3
UPDATE_RETAILER=        # Optional: specific retailer
```

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

## Future Features (Planned)

1. **Daily Price Updates**
   - Automated scraping of all products
   - Price history tracking
   - Lowest/highest price updates

2. **Price Alerts**
   - Notify when price drops
   - Configurable thresholds

3. **Analytics Dashboard**
   - Price trends over time
   - Retailer price comparison charts
   - Category-level insights
