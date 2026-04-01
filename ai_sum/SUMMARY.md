# PriceHawk — Project Summary

Price comparison platform for Thai home improvement retailers. Tracks and compares product prices across 6 stores.

**Hosting**: Frontend → Vercel | Backend → Railway | Database → Neon (serverless PostgreSQL)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, psycopg2 (sync) + asyncpg (async) |
| Database | PostgreSQL 15 (Neon) |
| Scraper | Playwright + crawl4ai |

---

## Retailers

| ID | Name | Notes |
|----|------|-------|
| `twd` | Thai Watsadu | Base retailer — all comparisons anchor to this |
| `gbh` | Global House | Has branch-level pricing |
| `dh` | Do Home | Stored as "Do Home" in DB |
| `hp` | HomePro | |
| `btv` | Boonthavorn | |
| `mgh` | Mega Home | Stored as "Mega Home" in DB (not "MegaHome") |

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `products` | All retailer products. `scrape_fail_count >= 3` = skip |
| `product_matches` | Cross-retailer matches. `verified_by_user=TRUE AND is_same=TRUE` = confirmed |
| `price_history` | Historical prices per product |
| `product_location_prices` | GBH branch-level prices |
| `location_monitored_groups` | GBH sdept groups to scrape |
| `location_monitored_locations` | GBH branch locations to scrape |
| `watchlist_groups` / `watchlist_group_products` | Category-based watchlist |
| `watchlist_sku_groups` / `watchlist_sku_group_products` | SKU-based watchlist |
| `users` | Session auth. `SESSION_EXPIRE_MINUTES = 10080` (7 days) |

---

## Features Built

### Products
- List with search (name/SKU/brand/multi-SKU paste), filter (category, brand, status, retailer, watched-only), pagination
- Price trend arrows (↑↓) showing recent price changes
- Excel export with hyperlinked prices and status column
- Detail page: price history chart (Recharts, 7D–1Y), verified matches, resync prices button

### Match Verification
- `/comparison` — verify matches as correct/incorrect, search by name or SKU
- `/products/[id]` — inline verify/undo per match
- Auto-verify: exact SKU matches auto-confirmed on scrape

### Manual Add (`/manual-add`)
- 4-step wizard: input URLs → review → scrape → results
- Validates retailer domain, requires name + price extracted

### Watchlist
- `/watchlist` — category-based groups with export
- `/watchlist-sku` — SKU groups with Excel bulk import (`SKU_Number` + `S-dept` columns) and per-group export

### Price by Location (GBH)
- `/price-by-location` — branch-level price comparison table
- `/price-by-location/[sku]` — per-SKU branch breakdown
- `/price-by-location/settings` — configure monitored groups + branches
- Separate cron: `backend/location_price_updater.py`

### Alerts
- `/alert` — manage alert email recipients
- `backend/services/alert_service.py` — detects price changes
- `backend/services/email_service.py` — builds HTML email
- `backend/alert_checker.py` — cron entry point

### Price Updater (Cron)
- `backend/update_prices.py` → `backend/services/price_updater.py`
- CLI: `--parallel`, `--batch-size`, `--retailer`, `--dry-run`, `--limit`
- Memory management: browser restart every 10 scrapes, cleanup every 2 batches

---

## Key Logic

### "Needs Review" (shared: dashboard, products filter, export)
A retailer needs review if: no `verified_by_user=TRUE AND is_same=TRUE` match AND `verified_by_user=FALSE` matches exist.

### Excel Export Status (all 3 export functions)
- All equal → `Same Price`
- TWD uniquely cheapest → `Cheapest` (dark green)
- TWD cheapest tied → `Cheapest (Shared)` (light green)
- TWD uniquely most expensive → `Most Expensive` (dark red)
- TWD most expensive tied → `Most Expensive (Shared)` (light red)
- TWD in middle → blank
- Only 1 price → `No Competitor Data`

### Retailer Name Aliases
"Mega Home" in DB ↔ "MegaHome" in frontend. Alias maps:
- Frontend: `RETAILER_NAME_ALIASES` in `products/page.tsx`
- Backend: `RETAILER_ALIASES` dict in `main.py` (module-level, added 2026-03)

---

## Backend Module-Level Helpers (added 2026-03)

Added to `backend/main.py` to reduce duplication:

```python
RETAILER_ALIASES          # dict — name normalization
_get_retailer_data()      # look up retailer in a dict by alias
_parse_search_input()     # parse search string → list (handles multi-SKU paste)
_determine_price_status() # compute cheapest/most-expensive status label
_extract_bearer_token()   # extract token from Authorization header
_sanitize_sheet_name()    # sanitize Excel sheet names
_cleanup_scraper_browsers(zombies_only)  # unified browser cleanup
cleanup_zombie_browser_processes()       # thin wrapper (zombies_only=True)
cleanup_all_scraper_browsers()           # thin wrapper (zombies_only=False)
```

---

## Frontend Shared Components

| Component | Path | Purpose |
|-----------|------|---------|
| `Button` | `ui/src/components/ui/Button.tsx` | All action buttons. Variants: `primary`, `danger`, `success`, `outline`, `ghost`, `outline-success`, `outline-primary`. Props: `loading`, `icon`, `size` |
| `MultiSelect` | `ui/src/components/ui/MultiSelect.tsx` | Resizable multi-select dropdown. Used on products, watchlist-sku, price-by-location |

---

## Session Logs

See `ai_sum/past-implement/` for detailed change history. Recent sessions:

| Date | Summary |
|------|---------|
| 2026-03-23 | Button component rollout across all pages |
| 2026-03-23 | Codebase simplification (dedup helpers, MultiSelect, logging) |
| 2026-03-05 | Location pricing optimizations |
| 2026-02-25 | Auto-verify matches + alert fixes |
| 2026-02-24 | TWD extractor fixes + email sdept |
| 2026-02-23 | Price-by-location export |
| 2026-02-17 | Price-by-location feature + export status logic |
| 2026-02-03 | Daily update mode |
| 2026-02-02 | Active/inactive product status, export enhancements, scraper fixes |
| 2026-01-29 | Memory leak + thread exhaustion fixes |
| 2026-01-28 | Multi-SKU search, price graph, watchlist filter, docs setup |
