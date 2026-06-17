# PriceHawk CFW/Makro — Full Context

This document captures the full technical and business context for the CFW/Makro branch of PriceHawk. Read this when onboarding or resuming after a long break.

---

## What This Is

**PriceHawk** originally compared **Thai Watsadu (TWD)** prices against home improvement competitors (HomePro, Global House, MegaHome, Do Home). That original code is on the `main` branch.

This branch (`cfw-main` / `cfw-uat`) is the same codebase **adapted for food wholesale**:
- **CFW** (Central Food Wholesale) replaces TWD as the base retailer
- **Makro** replaces the home improvement competitors

The buyer wants to know:
- Which CFW products have a Makro equivalent?
- How do prices compare?
- Has the Makro price changed recently?

This is an **internal tool**, not a public-facing product.

---

## Retailers

| ID | Full Name | Role |
|----|-----------|------|
| `cfw` | Central Food Wholesale | Base retailer — all comparisons anchor here |
| `makro` | Makro | Competitor |

---

## Architecture

```
Vercel (Next.js)  ──HTTPS──►  Railway (FastAPI)  ──SSL──►  Neon (PostgreSQL)
```

- Frontend calls backend via `NEXT_PUBLIC_API_URL` (set in Vercel env vars)
- Backend allows CORS from Vercel URL (set in `CORS_ORIGINS` Railway env var)
- Both env vars must include `https://` prefix — this is a common deployment mistake

---

## Backend Structure

The backend was refactored from a monolithic `main.py` into router files:

```
backend/main.py          ← App init, CORS, includes all routers
backend/database.py      ← get_db() — sync psycopg2 connection
backend/routers/
  deps.py                ← sessions dict, get_current_user(), shared helpers
  auth.py                ← /api/auth/login, logout, me, /api/health
  dashboard.py           ← /api/dashboard/stats, /api/retailers
  products.py            ← /api/products/* (list, detail, price-history, export)
  matches.py             ← /api/matches/:id/verify, undo
  price_formula.py       ← /api/price-formula/*
  price_by_location.py   ← /api/pbl/*
  alerts.py              ← /api/price-alerts/settings, emails
  categories.py          ← /api/categories
  watchlists.py          ← /api/watchlists/*
  scraper.py             ← /api/scrape, rescrape, /api/comparison/manual
```

**42 routes** total registered at startup.

### Auth Flow
- `POST /api/auth/login` → returns bearer token stored in localStorage
- All subsequent requests: `Authorization: Bearer <token>` header
- Sessions stored in memory dict in `deps.py` — lost on server restart (acceptable for internal tool)
- 7-day session expiry (`SESSION_EXPIRE_MINUTES = 10080`)

---

## Database Schema

### Core Tables

**`products`**
```sql
id            SERIAL PRIMARY KEY
retailer_id   TEXT  -- 'cfw' or 'makro'
sku           TEXT
barcode       TEXT
name          TEXT
current_price DECIMAL
link          TEXT
scrape_fail_count INT DEFAULT 0
```
> PK is `id`, not `product_id` — do not confuse these.

**`product_matches`**
```sql
id               SERIAL PRIMARY KEY
cfw_product_id   INT REFERENCES products(id)
makro_product_id INT REFERENCES products(id)
match_score      DECIMAL
is_verified      BOOLEAN DEFAULT FALSE
created_at       TIMESTAMPTZ
updated_at       TIMESTAMPTZ
UNIQUE (cfw_product_id, makro_product_id)
```
> CFW schema uses `is_verified` only. TWD schema uses `verified_by_user` + `is_same` — don't mix these up.

**`price_history`**
```sql
id          SERIAL PRIMARY KEY
product_id  INT REFERENCES products(id)
price       DECIMAL
recorded_at TIMESTAMPTZ
```

**`users`**
```sql
id            SERIAL PRIMARY KEY
username      TEXT UNIQUE
password_hash TEXT
```

### Watchlist Tables
- `watchlist_groups` / `watchlist_group_products` — category-based
- `watchlist_sku_groups` / `watchlist_sku_group_products` — SKU-based

### Location Tables
- `location_monitored_groups` / `location_monitored_locations` — which Makro branches to scrape
- `product_location_prices` — branch-level prices

---

## Frontend Pages

| Route | File | Description |
|-------|------|-------------|
| `/login` | `app/login/page.tsx` | Auth |
| `/dashboard` | `app/dashboard/page.tsx` | Stats + overview |
| `/products` | `app/products/page.tsx` | Product list, search, filter, export |
| `/products/[id]` | `app/products/[id]/page.tsx` | Detail: price history chart, matches |
| `/comparison` | `app/comparison/page.tsx` | Verify/reject matches |
| `/manual-add` | `app/manual-add/page.tsx` | 4-step scrape wizard |
| `/watchlist` | `app/watchlist/page.tsx` | Category-based watchlist |
| `/watchlist-sku` | `app/watchlist-sku/page.tsx` | SKU-based watchlist + bulk import |
| `/price-by-location` | `app/price-by-location/page.tsx` | Branch price comparison |
| `/price-by-location/settings` | `app/price-by-location/settings/page.tsx` | Manage branches |
| `/price-formula` | `app/price-formula/page.tsx` | Markup/discount rules |
| `/alert` | `app/alert/page.tsx` | Alert email recipients |

---

## Matching System

CFW and Makro products are matched by an external Python script (in `temp/import_match_cfw/`).

### Match File Format
```json
{
  "summary": { "cfw_total": 193, "fuzzy_matches": 47, ... },
  "matches": [
    {
      "cfw_sku": "10006712", "cfw_barcode": "...", "cfw_name_en": "...",
      "makro_sku": "860617", "makro_barcode": "...", "makro_name": "...",
      "score": 0.6642
    }
  ],
  "review_queue": [ ... ],   // score 0.38–0.42, needs manual review
  "unmatched": [ ... ]       // score < 0.38, no good candidate
}
```

### Import Script (`temp/import_match_cfw/import_matches_interest.py`)
- Auto-detects latest `matched_release*.json`
- Filters to SKUs in `interest.txt` (or `--no-interest` for all)
- Upserts with `ON CONFLICT DO UPDATE SET match_score = EXCLUDED.match_score`
- Run `--dry-run` first to preview

```bash
python temp/import_match_cfw/import_matches_interest.py --dry-run
python temp/import_match_cfw/import_matches_interest.py --include-review
```

---

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| `CORS_ORIGINS` without `https://` | Add `https://` — e.g. `https://pricehawk-cfw-nonprod.vercel.app` |
| `NEXT_PUBLIC_API_URL` without `https://` | Add `https://` — e.g. `https://pricehawk-cfw-uat.up.railway.app` |
| Vercel Framework Preset = "Other" | Change to "Next.js" |
| `INTERVAL '%s days'` in psycopg2 | Use `make_interval(days => %s)` instead |
| `WHERE product_id = %s` | Column is `id`, not `product_id` |
| `pm.verified_by_user` in query | CFW uses `pm.is_verified` (single boolean) |
| Route shadowing: `/products/export` after `/products/{sku}` | Keep export router included before sku router |
| Lucide import `{ X }` missing | Always import explicitly — no barrel re-exports |

---

## Environment Variables Reference

### Railway (Backend)
```
CORS_ORIGINS=https://pricehawk-cfw-nonprod.vercel.app
DB_HOST=ep-xxx.ap-southeast-1.aws.neon.tech
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=...
DB_PORT=5432
DB_SSLMODE=require
PRODUCTION=true
SCRAPER_VERBOSE=true
SCRAPER_ONLY_TEXT=false
UPDATE_PARALLEL=1
```

### Vercel (Frontend)
```
NEXT_PUBLIC_API_URL=https://pricehawk-cfw-uat.up.railway.app
```

### Local (backend/.env)
```
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=5432
DB_SSLMODE=require
```

### Local (ui/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Session History

| Date | Work Done |
|------|-----------|
| 2026-06 | CFW/Makro branch: price history fix, backend refactor into routers, Vercel/Railway deployment, CORS fixes, match import script |
| 2026-03 | TWD branch: Button component rollout, codebase simplification, MultiSelect |
| 2026-02 | TWD branch: price-by-location, auto-verify, alerts, export |

Full session logs: `ai_sum/past-implement/`
