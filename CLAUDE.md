# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start of Every Session
Read `ai_sum/SUMMARY.md` first for full project context before making any changes.
Check recent work in `ai_sum/past-implement/` to understand what was last done.

## After Every Implementation Session
Always save a session summary to `ai_sum/past-implement/YYYY-MM-DD_short-description.md`.
Use the template at `ai_sum/past-implement/TEMPLATE.md` as a guide. Cover: what was built/changed and why, files modified with line ranges, key decisions, bugs fixed, pending next steps. Do this automatically without being asked.

---

## Project Structure
```
backend/          # FastAPI + psycopg2 (PostgreSQL) — all API endpoints in main.py
  services/       # alert_service.py, email_service.py, price_updater.py
  scraper-url/adws/  # Playwright-based scraper modules
backend/db_pool.py            # asyncpg connection pool (used by alert/email services)
backend/location_price_updater.py  # GBH branch price scraper (run as cron)
backend/update_prices.py     # Cron entry point — calls services/price_updater.py
backend/alert_checker.py     # Cron entry point — runs alert checks
ui/               # Next.js 14 App Router, TypeScript, Tailwind CSS
  src/app/        # Pages (App Router)
  src/components/ # Shared components (layout, ui)
  src/lib/api.ts  # apiFetch() utility + auth token helpers
  src/context/AuthContext.tsx # Auth state management
database/init/    # SQL schemas (01_schema.sql)
temp/             # One-off scripts, not deployed
ai_sum/           # Documentation hub
  SUMMARY.md      # Main project docs — read this first
  sessions/       # Session logs
```

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

### Price Updater (manual run)
```bash
cd backend
python services/price_updater.py --parallel 3 --batch-size 50
python services/price_updater.py --retailer twd --dry-run  # Test without DB writes
```

### Location Price Updater (GBH branches)
```bash
cd backend
python location_price_updater.py
```

---

## Deployment
- **Frontend**: Vercel — env var `NEXT_PUBLIC_API_URL`
- **Backend**: Railway — env vars `DATABASE_URL`, `CORS_ORIGINS`, `FRONTEND_URL`
- **Database**: Neon (serverless PostgreSQL)
- Backend start: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Railway uses `nixpacks.toml` to install Playwright/Chromium deps at build time

## DB Connection
Two connection systems exist side by side:
- **Sync** (`get_db()` in `main.py`): psycopg2 + `RealDictCursor` — used by all API endpoints in `main.py`
- **Async** (`db_pool.py`): asyncpg pool — used exclusively by `services/alert_service.py` and `services/email_service.py`

Backend reads `backend/.env` for individual vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`.
Scripts in `temp/` can use `temp/.env` if present. `DATABASE_URL` is supported as fallback in `db_pool.py`.

---

## Key Conventions

### Retailer IDs
- `twd` — Thai Watsadu (base retailer for all comparisons)
- `gbh` — Global House
- `dh` — Do Home
- `hp` — HomePro
- `btv` — Boonthavorn
- `mgh` — Mega Home

### Database Tables
- `products` — all retailer products (retailer_id + sku + link + current_price; `scrape_fail_count >= 3` = skip)
- `product_matches` — cross-retailer matches; `verified_by_user=TRUE AND is_same=TRUE` = confirmed match
- `price_history` — historical prices per product
- `product_location_prices` — GlobalHouse branch-level prices
- `location_monitored_groups` / `location_monitored_locations` — GBH branch scraping config
- `watchlist_sku_groups` / `watchlist_sku_group_products` — SKU-based watchlist feature
- `users` — session-based auth (7-day expiry, `SESSION_EXPIRE_MINUTES = 10080`)

### Authentication
- Session-based, 7-day expiry
- Bearer token in localStorage (primary) + HTTP-only cookie (fallback)
- All API endpoints require `user: dict = Depends(get_current_user)`

### Frontend Patterns
- Primary color: `cyan-500` / `cyan-600`; Success: `emerald-500`; Danger: `red-500`
- Icons: `lucide-react`
- All pages wrapped in `<MainLayout>`
- Pages using `useSearchParams` must be wrapped in `<Suspense>`
- `apiFetch()` from `@/lib/api` for all API calls — handles auth headers, 401 redirect, and optional timeout
- Shared UI components in `ui/src/components/ui/`:
  - `Button` — use for all action buttons; variants: `primary`, `danger`, `success`, `outline`, `ghost`, `outline-success`, `outline-primary`; props: `loading`, `icon`, `size` (sm/md/lg)
  - `MultiSelect` — multi-select dropdown; used on products, watchlist-sku, price-by-location pages

### Backend Patterns
- All endpoints in `backend/main.py` (~5000+ lines)
- Use `get_db()` context manager for DB connections with `RealDictCursor`
- Excel exports use `openpyxl`, return as `Response` with `content-disposition` header
- Scraping runs as subprocess via `subprocess.Popen` (not `subprocess.run`) to allow process tree cleanup
- `cleanup_zombie_browser_processes()` in `main.py` kills headless Chrome processes safely (checks for `--headless` flag, excludes user-profile Chrome)

### Excel Export Status Logic (consistent across all 3 export functions)
- All prices equal → `Same Price`, no color
- TWD uniquely cheapest → `Cheapest`, dark green
- TWD cheapest tied → `Cheapest (Shared)`, light green
- TWD uniquely most expensive → `Most Expensive`, dark red
- TWD most expensive tied → `Most Expensive (Shared)`, light red
- TWD in middle → blank status
- Only 1 price → `No Competitor Data`

### "Needs Review" Logic (shared across dashboard, products filter, export filter)
A retailer needs review if: no verified correct match (`verified_by_user=TRUE AND is_same=TRUE`) AND unreviewed matches exist (`verified_by_user=FALSE`).

### Retailer Name Aliases
MegaHome stored as "Mega Home" in DB. Alias maps exist in:
- Frontend: `RETAILER_NAME_ALIASES` in `ui/src/app/products/page.tsx`
- Backend export: `retailer_aliases` dict in `backend/main.py` (~line 730)

---

## Frontend Pages
- `/login` — auth
- `/dashboard` — stats overview
- `/products` — list with search/filter/export; "Watched Only" checkbox; price trend arrows
- `/products/[id]` — detail with matches, price history chart (Recharts), rescrape button
- `/comparison` — match verification (search by name or SKU)
- `/manual-add` — 4-step wizard: input URLs → review → scrape → compare
- `/watchlist` — category-based watchlist with export
- `/watchlist-sku` — SKU group watchlist with Excel bulk import/export
- `/price-by-location` — GBH branch-level price view
- `/price-by-location/settings` — manage monitored GBH locations
- `/price-by-location/[sku]` — per-SKU branch prices

## Important Files
- `backend/main.py` — all API endpoints (~4800+ lines)
- `backend/services/email_service.py` — email alert HTML builder
- `backend/services/alert_service.py` — price change detection logic
- `ui/src/components/layout/Sidebar.tsx` — navigation (add new pages here)
- `database/init/01_schema.sql` — DB schema
