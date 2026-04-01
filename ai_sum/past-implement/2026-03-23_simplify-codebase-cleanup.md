# Session: Codebase Simplification & Cleanup
**Date:** 2026-03-23

## What Was Done
Full codebase review using three parallel review agents (reuse, quality, efficiency), then fixed all high/medium severity findings.

## Changes Made

### backend/main.py
**Module-level helpers added** (lines ~40-90, after logger definition):
- `RETAILER_ALIASES` — module-level constant replacing 2 inline dicts
- `_get_retailer_data(retailer_data_dict, retailer_name)` — replaces 2 identical nested function definitions
- `_parse_search_input(search)` — replaces 3 inline search normalization blocks
- `_determine_price_status(base_price, all_prices)` — replaces 3 identical 18-line status logic blocks across export functions
- `_extract_bearer_token(authorization)` — replaces 3 inline `authorization[7:]` extractions
- `_sanitize_sheet_name(name)` — replaces char-loop with `re.sub(r'[/\\?*\[\]]', '-', name[:31])`
- Added `import re` at top

**Bearer token extraction** — 3 instances in `get_current_user`, `logout`, `page_unload` replaced with `_extract_bearer_token(authorization) or session_token`

**Price status logic** — 3 identical 18-line blocks in `export_sku_group`, `export_products`, `export_price_history` replaced with `_determine_price_status(base_price, all_prices)`

**Search normalization** — 3 inline blocks replaced with `_parse_search_input(search)`

**Browser cleanup functions merged** — `cleanup_zombie_browser_processes` and `cleanup_all_scraper_browsers` (2 nearly identical 60-line functions) merged into:
- `_is_scraper_browser(pinfo)` — shared safety-check logic
- `_cleanup_scraper_browsers(zombies_only=False)` — single implementation
- Public wrappers `cleanup_zombie_browser_processes()` and `cleanup_all_scraper_browsers()` kept for call-site compatibility

**print() → logger** — Converted all `print()` calls to `logger.*` across:
- `import_excel_to_sku_groups` endpoint (~60 prints → ~10 logger calls)
- `test_file_upload` endpoint
- `/api/scrape` endpoint
- `scrape_single_url` function (parallel scraper)
- `manual_comparison` endpoint
- psutil import warning

### backend/services/alert_service.py
- `BANGKOK_OFFSET_HOURS = 7` promoted to module-level constant (line 22)
- Removed 2 redundant local definitions inside `should_send_alert_now` and `_calculate_next_alert` methods

### ui/src/components/ui/MultiSelect.tsx (NEW FILE)
Created shared MultiSelect component consolidating 3 near-identical implementations:
- Supports `string[]` or `{ value, label }[]` options
- Optional `resizable` prop (default: true) for corner-drag resize handle
- Used by products, price-by-location, and watchlist-sku pages

### ui/src/app/products/page.tsx
- Removed local `MultiSelect` component (~150 lines)
- Added `import { MultiSelect } from '@/components/ui/MultiSelect'`
- Removed unused lucide icons (`X`, `Check`) from import

### ui/src/app/price-by-location/page.tsx
- Removed local `MultiSelect` component (~160 lines)
- Added `import { MultiSelect } from '@/components/ui/MultiSelect'`
- Removed unused lucide icons (`X`, `Check`) from import

### ui/src/app/watchlist-sku/page.tsx
- Removed local `MultiSelect` component (~138 lines)
- Added `import { MultiSelect } from '@/components/ui/MultiSelect'`
- Removed unused lucide icons (`ChevronDown`, `Check`) from import

## Lines Removed / Consolidated
- ~180 lines of duplicate price status logic (3x → shared function)
- ~150 lines of duplicate retailer alias + getter (2x → module-level)
- ~60 lines of duplicate search normalization (3x → utility)
- ~70 lines of duplicate browser cleanup (2x → merged)
- ~60 debug print() calls replaced with structured logger calls
- ~448 lines of duplicate MultiSelect JSX (3x → shared component)

## Key Decisions
- Kept `cleanup_zombie_browser_processes()` and `cleanup_all_scraper_browsers()` as public wrappers (call sites unchanged)
- MultiSelect shared component defaults `resizable=true` to match existing behavior of products/price-by-location pages; watchlist-sku uses `resizable={false}` implicitly (defaults fine since the simplier version didn't have resize)
- Did NOT address N+1 DB query patterns (too risky without tests, requires significant refactor)
- Did NOT address in-memory session TTL cleanup (separate infrastructure concern)

## Pending
- N+1 price history queries in export functions (each product fires separate DB query)
- In-memory `sessions` dict has no proactive TTL cleanup
- Frontend API fetch pattern could be unified with a custom hook
