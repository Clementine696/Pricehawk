# PriceHawk — Claude Instructions

## Start of Every Session
Read `ai_sum/SUMMARY.md` first for full project context before making any changes.
Check recent work in `ai_sum/sessions/` to understand what was last done.

## After Every Implementation Session
Always save a session summary to `ai_sum/sessions/YYYY-MM-DD_short-description.md`.

Use the template at `ai_sum/sessions/TEMPLATE.md` as a guide.

The summary should cover:
- What was built/changed and why
- Files modified with line ranges
- Key decisions made
- Bugs fixed
- Any pending next steps

Do this automatically at the end of each session without being asked.

---

## Project Structure
```
backend/          # FastAPI + psycopg2 (PostgreSQL) — all API endpoints in main.py
ui/               # Next.js 14 App Router, TypeScript, Tailwind CSS
  src/app/        # Pages (App Router)
  src/components/ # Shared components (layout, ui)
database/init/    # SQL schemas (01_schema.sql)
temp/             # One-off scripts, not deployed
ai_sum/           # Documentation hub
  SUMMARY.md      # Main project docs — read this first
  sessions/       # Session logs
```

## Deployment
- **Frontend**: Vercel — env var `NEXT_PUBLIC_API_URL`
- **Backend**: Railway — env vars `DATABASE_URL`, `CORS_ORIGINS`
- **Database**: Neon (serverless PostgreSQL)
- Build command: `npm run build` in `ui/`
- Backend start: `uvicorn main:app --reload --port 8000`

## DB Connection
- Use `backend/.env` for DB credentials (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
- Scripts in `temp/` can use `temp/.env` if present (overrides backend/.env)
- Backend does NOT use DATABASE_URL — uses individual DB_* vars with psycopg2

## Key Conventions

### Retailer IDs
- `twd` — Thai Watsadu (base retailer for all comparisons)
- `gbh` — Global House
- `dh` — Do Home
- `hp` — HomePro
- `btv` — Boonthavorn
- `mgh` — Mega Home

### Database Tables
- `products` — all retailer products (retailer_id + sku + link + current_price)
- `product_matches` — cross-retailer matches; `verified_result=TRUE` = confirmed match
- `price_history` — historical prices
- `product_location_prices` — GlobalHouse branch-level prices
- `location_monitored_groups` / `location_monitored_locations` — what to scrape for location prices

### Authentication
- Session-based, 7-day expiry
- Bearer token in localStorage (primary) + HTTP-only cookie (fallback)
- All API endpoints require `user: dict = Depends(get_current_user)`

### Frontend Patterns
- Primary color: `cyan-500` / `cyan-600`
- Success: `emerald-500` / `green-500`
- Danger: `red-500`
- Neutral: gray scale
- Icons: `lucide-react`
- All pages wrapped in `<MainLayout>`
- Pages using `useSearchParams` must be wrapped in `<Suspense>`
- `apiFetch()` from `@/lib/api` for all API calls

### Backend Patterns
- All endpoints in `backend/main.py`
- Use `get_db()` context manager for DB connections
- Use `RealDictCursor` for dict-style row access
- Excel exports use `openpyxl`, return as `Response` with content-disposition header
- Scraping runs as subprocess via `subprocess.Popen`

### Excel Export Status Logic (all 3 export functions)
- All prices equal → `Same Price`, no color on any cell
- TWD uniquely cheapest → `Cheapest`, dark green
- TWD cheapest tied → `Cheapest (Shared)`, light green
- TWD uniquely most expensive → `Most Expensive`, dark red
- TWD most expensive tied → `Most Expensive (Shared)`, light red
- TWD in middle → blank status
- Only 1 price (no competitors) → `No Competitor Data`

## Important Files
- `backend/main.py` — all API endpoints (~4800+ lines)
- `ui/src/components/layout/Sidebar.tsx` — navigation (add new pages here)
- `database/init/01_schema.sql` — DB schema
- `backend/location_price_updater.py` — GBH branch price scraper (run as cron)
