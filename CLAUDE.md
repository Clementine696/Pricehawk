# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start of Every Session
Read `ai_sum/SUMMARY.md` first for full project context before making any changes.
Check recent work in `ai_sum/past-implement/` to understand what was last done.

## After Every Implementation Session
Always save a session summary to `ai_sum/past-implement/YYYY-MM-DD_short-description.md`.
Use the template at `ai_sum/past-implement/TEMPLATE.md` as a guide. Cover: what was built/changed and why, files modified with line ranges, key decisions, bugs fixed, pending next steps. Do this automatically without being asked.

---

## Project Overview

**PriceHawk** started as a home improvement price comparison tool for **Thai Watsadu (TWD)** vs competitors (HomePro, Global House, MegaHome, Do Home). That original codebase lives on the `main` branch.

This branch (`cfw-main` / `cfw-uat`) is a **copy of that codebase adapted for food wholesale**:
- **CFW** (Central Food Wholesale) = base retailer (replaces TWD)
- **Makro** = competitor (replaces the home improvement competitors)

The code structure, patterns, and conventions are the same — only the retailer IDs and some schema details differ.

**Hosting**: Frontend → Vercel | Backend → Railway | Database → Neon (serverless PostgreSQL)

---

## Project Structure

```
backend/
  main.py                     # App entry point — FastAPI init + CORS + router includes
  main_cfw.py                 # Alternative entry point (same as main.py)
  database.py                 # get_db() sync connection (psycopg2 + RealDictCursor)
  db_pool.py                  # asyncpg pool — used by alert/email services only
  routers/
    deps.py                   # Shared: sessions dict, get_current_user(), SESSION_EXPIRE_MINUTES
    auth.py                   # /api/auth/* (login, logout, me, health)
    dashboard.py              # /api/dashboard/stats, /api/retailers
    products.py               # /api/products/* (list, detail, export, price-history)
    matches.py                # /api/matches/* (verify, undo)
    price_formula.py          # /api/price-formula/*
    price_by_location.py      # /api/pbl/*
    alerts.py                 # /api/price-alerts/*
    categories.py             # /api/categories
    watchlists.py             # /api/watchlists/*
    scraper.py                # /api/scrape, /api/*/rescrape, /api/comparison/manual
  services/
    alert_service.py          # Price change detection (async)
    email_service.py          # HTML email builder (async)
    price_updater.py          # Cron: scrape + update prices
  scraper-url/adws/           # Playwright scraper modules
  update_prices.py            # Cron entry point → services/price_updater.py
  alert_checker.py            # Cron entry point → services/alert_service.py
  location_price_updater.py   # Makro branch price scraper (cron)

ui/
  src/app/                    # Next.js 14 App Router pages
  src/components/
    layout/Sidebar.tsx        # Navigation — add new pages here
    ui/Button.tsx             # Shared button component
    ui/MultiSelect.tsx        # Shared multi-select dropdown
  src/lib/api.ts              # apiFetch() — auth headers, 401 redirect, timeout
  src/context/AuthContext.tsx # Auth state

database/
  cfw/                        # SQL migration files (01_schema.sql → 09_*.sql)

temp/
  import_match_cfw/           # Match import scripts (not deployed)
    import_matches_interest.py  # Reusable match importer (see --help)
    matched_release*.json       # Match datasets — script auto-picks latest
    interest.txt                # 193 CFW SKUs of interest

ai_sum/
  SUMMARY.md                  # Main project docs — read this first
  past-implement/             # Session summaries
```

---

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
npm run build   # Production build (used by Vercel)
```

### Match Import (temp script)
```bash
# Auto-detects latest matched_release*.json, imports only interest.txt SKUs
python temp/import_match_cfw/import_matches_interest.py --dry-run
python temp/import_match_cfw/import_matches_interest.py

# Options
--include-review    # Also import review_queue items (score 0.38-0.42)
--min-score 0.45   # Override score threshold
--no-interest       # Import all SKUs, not just interest.txt
--file path.json    # Use specific file instead of auto-detect
```

---

## Deployment

| | Service | Key Env Vars |
|--|---------|-------------|
| Frontend | Vercel | `NEXT_PUBLIC_API_URL=https://<railway-url>` (must include `https://`) |
| Backend | Railway | `CORS_ORIGINS=https://<vercel-url>` (must include `https://`), `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, `DB_SSLMODE` |
| Database | Neon | — |

- Backend start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Railway uses `nixpacks.toml` to install Playwright/Chromium at build time
- Vercel Framework Preset **must be "Next.js"** (not "Other")
- **Common CORS mistake**: `CORS_ORIGINS` value must have `https://` prefix — e.g. `https://pricehawk-cfw-nonprod.vercel.app`, not just `pricehawk-cfw-nonprod.vercel.app`

---

## DB Connection

Two systems side by side:
- **Sync** (`get_db()` in `backend/database.py`): psycopg2 + `RealDictCursor` — used by all router endpoints
- **Async** (`db_pool.py`): asyncpg pool — used only by `services/alert_service.py` and `services/email_service.py`

Env vars read from `backend/.env`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`.
Scripts in `temp/` read from `temp/.env`.

---

## Key Conventions

### Retailer IDs
- `cfw` — Central Food Wholesale (base retailer)
- `makro` — Makro (competitor)

### Database Tables (CFW/Makro schema)
- `products` — all retailer products (`retailer_id` + `sku` + `barcode` + `link` + `current_price`; PK is `id`)
- `product_matches` — CFW ↔ Makro matches; `is_verified=TRUE` = confirmed match
- `price_history` — historical prices per product
- `product_location_prices` — Makro branch-level prices
- `location_monitored_groups` / `location_monitored_locations` — branch scraping config
- `watchlist_groups` / `watchlist_group_products` — category-based watchlist
- `watchlist_sku_groups` / `watchlist_sku_group_products` — SKU-based watchlist
- `users` — session auth (`SESSION_EXPIRE_MINUTES = 10080`, 7 days)

### product_matches schema (CFW)
- Uses `is_verified` (single boolean) — NOT `verified_by_user`/`is_same` (that's the TWD schema)
- Conflict key: `(cfw_product_id, makro_product_id)`

### Authentication
- Session-based, 7-day expiry
- Bearer token in localStorage (primary) + HTTP-only cookie (fallback)
- All endpoints require `user: dict = Depends(get_current_user)` from `routers/deps.py`
- Sessions stored in memory dict in `routers/deps.py` — resets on server restart

### SQL Parameterization
- Use `make_interval(days => %s)` instead of `INTERVAL '%s days'` — psycopg2 quotes the param, breaking the latter
- Products PK is `id` — never `product_id`

### Frontend Patterns
- Primary color: `cyan-500` / `cyan-600`; Success: `emerald-500`; Danger: `red-500`
- Icons: `lucide-react` — always import explicitly (e.g. `import { X, Check, ChevronDown } from 'lucide-react'`)
- All pages wrapped in `<MainLayout>`
- Pages using `useSearchParams` must be wrapped in `<Suspense>`
- `apiFetch()` from `@/lib/api` for all API calls

### Backend Patterns
- Router files in `backend/routers/` — one file per feature domain
- Use `get_db()` from `backend/database.py` for all DB connections
- Excel exports use `openpyxl`, return as `Response` with `content-disposition` header
- Scraping runs as `subprocess.Popen` (not `subprocess.run`) for process tree cleanup
- `BACKEND_DIR` in `routers/scraper.py` = `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (one level up from routers/)

---

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/login` | Auth |
| `/dashboard` | Stats overview |
| `/products` | List with search/filter/export; price trend arrows |
| `/products/[id]` | Detail: price history chart (Recharts), matches, rescrape |
| `/comparison` | Match verification (search by name or SKU) |
| `/manual-add` | 4-step wizard: URLs → review → scrape → compare |
| `/watchlist` | Category-based watchlist with export |
| `/watchlist-sku` | SKU group watchlist with Excel bulk import/export |
| `/price-by-location` | Makro branch-level price view |
| `/price-by-location/settings` | Manage monitored branches |
| `/price-formula` | Price formula configuration per match |
| `/alert` | Price alert email recipients |

## Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | App entry — router includes, CORS setup |
| `backend/routers/deps.py` | Shared auth state + `get_current_user()` |
| `backend/routers/products.py` | Products list, detail, export, price history |
| `backend/database.py` | `get_db()` sync connection |
| `ui/src/components/layout/Sidebar.tsx` | Navigation — add new routes here |
| `ui/src/lib/api.ts` | `apiFetch()` with auth + timeout |
| `database/cfw/01_schema.sql` | Base DB schema |
