# PriceHawk — CFW/Makro

Food wholesale price comparison platform. Tracks and compares prices between **CFW** (Central Food Wholesale) and **Makro**.

**Live**: Frontend → Vercel | Backend → Railway | Database → Neon (PostgreSQL)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL (Neon serverless) |
| Scraper | Playwright |

---

## Features

- **Products** — browse CFW catalog, view matched Makro prices, search/filter, Excel export
- **Price History** — chart showing price changes over time (7D / 30D / 90D / 1Y)
- **Match Verification** — confirm or reject CFW ↔ Makro product matches
- **Price Formula** — configure markup/discount rules per match
- **Watchlist** — category-based and SKU-based watchlists with export
- **Price by Location** — Makro branch-level price comparison
- **Alerts** — email notifications on price changes
- **Manual Add** — wizard to manually add and scrape product URLs

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # fill in DB credentials
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Deployment

### Vercel (Frontend)
1. Connect repo, set Framework Preset to **Next.js**
2. Set env var: `NEXT_PUBLIC_API_URL=https://<your-railway-url>` (include `https://`)

### Railway (Backend)
Set env vars:
```
CORS_ORIGINS=https://<your-vercel-url>
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=5432
DB_SSLMODE=require
PRODUCTION=true
```

> Both `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` **must include `https://`** prefix.

Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Database (Neon)
Run migrations in order:
```
database/cfw/01_schema.sql
database/cfw/02_schema.sql
database/cfw/03_product_matches.sql
...
```

---

## Project Structure

```
backend/
  main.py               # Entry point — FastAPI + CORS + routers
  database.py           # Sync DB connection (psycopg2)
  db_pool.py            # Async DB pool (asyncpg) — alerts only
  routers/              # One file per feature domain
  services/             # alert_service.py, email_service.py, price_updater.py
  scraper-url/adws/     # Playwright scraper modules

ui/
  src/app/              # Pages (Next.js App Router)
  src/components/       # Shared layout + UI components
  src/lib/api.ts        # apiFetch() utility

database/cfw/           # SQL migration files
temp/                   # One-off scripts (not deployed)
ai_sum/                 # Dev documentation + session logs
```

---

## Cron Jobs

| Script | Purpose |
|--------|---------|
| `backend/update_prices.py` | Scrape and update product prices |
| `backend/alert_checker.py` | Check for price changes, send email alerts |
| `backend/location_price_updater.py` | Scrape Makro branch-level prices |

```bash
# Manual runs
cd backend
python update_prices.py
python services/price_updater.py --parallel 3 --batch-size 50 --dry-run
python location_price_updater.py
```
