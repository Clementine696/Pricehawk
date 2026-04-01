# PriceHawk — System Architecture

**Last Updated**: 2026-03-31

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  USER                                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │  browser
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Vercel · Next.js 14)                                │
│                                                                 │
│  Dashboard      — stats overview                                │
│  Products       — search, filter, export, price trend arrows    │
│  Product Detail — price history chart, match verify, resync     │
│  Comparison     — bulk match verification                       │
│  Manual Add     — 4-step scrape & compare wizard                │
│  Watchlist      — category + SKU groups, Excel import/export    │
│  Price by Loc   — GBH branch-level price table                  │
│  Alert          — manage email recipients                       │
└────────────────────────────┬────────────────────────────────────┘
                             │  REST API · Bearer token
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND  (Railway · FastAPI)                                   │
│                                                                 │
│  API          main.py (~5000 lines) — all endpoints             │
│  Cron         price_updater.py — daily price scraping           │
│  Cron         location_price_updater.py — GBH branch prices     │
│  Cron         alert_checker.py — detect changes, send email     │
└──────────────────┬──────────────────────┬───────────────────────┘
                   │  SQL                 │  subprocess
                   ▼                      ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│  DATABASE  (Neon)        │  │  SCRAPER (Playwright + crawl4ai) │
│  PostgreSQL 15           │◄─│  headless Chromium               │
│                          │  │                                  │
│  products                │  │  thaiwatsadu.com   (twd)         │
│  product_matches         │  │  globalhouse.co.th (gbh)         │
│  price_history           │  │  dohome.co.th      (dh)          │
│  product_location_prices │  │  homepro.co.th     (hp)          │
│  watchlist_*             │  │  boonthavorn.com   (btv)         │
│  users                   │  │  megahome.co.th    (mgh)         │
└──────────────────────────┘  └──────────────────────────────────┘
```

---

## Database Layer

```
retailers ──────────────────────────────────────────────────
  retailer_id PK  |  name  |  domain

products ───────────────────────────────────────────────────
  product_id PK  |  retailer_id FK  |  sku  |  name
  current_price  |  lowest_price  |  highest_price
  last_updated_at  |  scrape_fail_count  |  link  |  image

product_matches ─────────────────────────────────────────────
  match_id PK  |  base_product_id FK (twd)
  candidate_product_id FK  |  is_same  |  verified_by_user

price_history ───────────────────────────────────────────────
  price_id PK  |  product_id FK  |  price  |  scraped_at

product_location_prices ─────────────────────────────────────
  id PK  |  twd_product_id FK  |  gbh_product_id FK
  location_id FK  |  price  |  scraped_at

location_monitored_groups ───────────────────────────────────
  group_id PK  |  sdept  |  description

location_monitored_locations ────────────────────────────────
  location_id FK  (many-to-many via junction table)

watchlist_groups / watchlist_group_products ─────────────────
  category-based watchlist

watchlist_sku_groups / watchlist_sku_group_products ─────────
  SKU-based watchlist (Excel import/export)

users ───────────────────────────────────────────────────────
  user_id PK  |  username  |  hashed_password
  session_token  |  expires_at  (7-day expiry)
```

---

## DB Connection Systems

Two systems run side-by-side — do NOT mix them:

| System | Module | Used by |
|--------|--------|---------|
| **Sync** | psycopg2 + `RealDictCursor` via `get_db()` | All API endpoints in `main.py` |
| **Async** | asyncpg pool via `db_pool.py` | `alert_service.py`, `email_service.py` only |

Backend env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE` (from `backend/.env`).

---

## Authentication Flow

```
Login (POST /api/auth/login)
  → hashed password check
  → generate session token
  → store in users table (expires 7 days)
  → return token

Every API request
  → read Authorization: Bearer <token>  (primary)
  → fallback: HTTP-only cookie
  → validate token → get_current_user()
  → 401 if expired/invalid → frontend redirects to /login
```

---

## Price Update Flow (Cron)

```
update_prices.py  (Railway cron, hourly or daily)
  │
  └─► price_updater.py
        ├─ Fetch N oldest products (last_updated_at ASC)
        ├─ Skip scrape_fail_count >= 3
        ├─ Parallel workers (--parallel 1–20)
        │
        └─ For each product:
             ├─ subprocess.Popen → adw_ecommerce_product_scraper.py
             ├─ Playwright headless Chromium fetches page
             ├─ product_extractor.py parses HTML (retailer-specific patterns)
             ├─ UPDATE products SET current_price, last_updated_at
             ├─ INSERT INTO price_history
             └─ Reset scrape_fail_count (or increment on failure)

Memory management:
  - Browser restart every 10 scrapes
  - Cleanup pause every 15 products
  - psutil kills orphan Chrome processes (--headless flag check)
```

---

## GBH Location Price Flow (Cron)

```
location_price_updater.py  (separate Railway cron)
  │
  ├─ Load monitored groups + locations from DB
  ├─ For each (twd_product, gbh_branch):
  │    ├─ Playwright navigates to GBH product page
  │    ├─ JavaScript injection: click location dropdown → select branch
  │    ├─ Wait for price update (6 × 500ms polling)
  │    └─ Extract price → UPSERT product_location_prices
  └─ Batch query optimization (1 query vs 4200+)
```

---

## Alert Flow (Cron)

```
alert_checker.py  (Railway cron)
  │
  └─► alert_service.py  (asyncpg)
        ├─ Compare latest price_history vs previous
        ├─ Detect: price change, product inactive, product active
        ├─ Load alert email recipients from DB
        └─► email_service.py
              ├─ Build HTML email (product images, price diff, status)
              └─ Send via SMTP
```

---

## Frontend Architecture

```
layout.tsx (Root)
└── AuthProvider (AuthContext.tsx)
    └── MainLayout
        ├── Sidebar.tsx  ← navigation, add pages here
        └── Page Content
            └── apiFetch()  ← all API calls, handles 401 redirect
```

### Shared UI Components

| Component | Variants / Props |
|-----------|-----------------|
| `Button` | `primary` `danger` `success` `outline` `ghost` `outline-success` `outline-primary` · `loading` `icon` `size` |
| `MultiSelect` | `options` `selected` `onChange` `placeholder` · `resizable` (default true) |
| `SingleSelect` | local to `products/page.tsx` — single-value dropdown |

### Pages

| Route | Purpose |
|-------|---------|
| `/login` | Auth |
| `/dashboard` | Stats overview |
| `/products` | List + search/filter/export |
| `/products/[id]` | Detail, price history chart, match verify |
| `/comparison` | Bulk match verification |
| `/manual-add` | 4-step scrape wizard |
| `/watchlist` | Category watchlist + export |
| `/watchlist-sku` | SKU watchlist, Excel import/export |
| `/price-by-location` | GBH branch price table |
| `/price-by-location/[sku]` | Per-SKU branch breakdown |
| `/price-by-location/settings` | Monitored groups + branches config |
| `/alert` | Alert email recipients |

---

## Scraper Architecture

```
adw_ecommerce_product_scraper.py  (entry point)
  └─► crawl4ai_wrapper.py  (Playwright browser manager)
        └─► product_extractor.py  (retailer-specific HTML parsing)
              ├─ ThaiWatsaduExtractor   (twd)
              ├─ GlobalHouseExtractor  (gbh)
              ├─ DoHomeExtractor       (dh)
              ├─ HomeProExtractor      (hp)
              ├─ BoonthavornExtractor  (btv)
              └─ MegaHomeExtractor     (mgh)
```

Extraction priority per retailer:
1. Retailer-specific HTML patterns (custom class/attribute anchors)
2. JSON-LD structured data (`@type: Product`)
3. `__NEXT_DATA__` / GTM / analytics data
4. Generic HTML fallback patterns
5. Meta tags

See `ai_sum/PRODUCT_EXTRACTION_PATTERNS.md` for full regex patterns per retailer.

---

## Deployment

| Service | Platform | Config |
|---------|----------|--------|
| Frontend | Vercel | `NEXT_PUBLIC_API_URL` env var |
| Backend + Scrapers | Railway | `nixpacks.toml` installs Playwright/Chromium deps |
| Database | Neon | Serverless PostgreSQL, `DATABASE_URL` |
| Cron jobs | Railway (separate services) | `update_prices.py`, `alert_checker.py`, `location_price_updater.py` |

Backend start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
