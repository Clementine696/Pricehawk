# Daily Price Update Architecture (Once-Per-Day Mode)

## Overview

The daily price update system ensures each product is updated **only once per day** using date-based filtering. This replaces the previous continuous update approach that updated products multiple times throughout the day.

## Key Concepts

### Date-Based Filtering

The SQL query in `price_updater.py` filters products using:
```sql
WHERE (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL)
```

This means:
- Products with `last_updated_at = today` are **excluded** (already updated)
- Products with `last_updated_at < today` are **included** (needs update)
- Products with `last_updated_at = NULL` are **included** (never updated)

### Parallel Job Coordination

**Why OFFSET is still needed**:

When 6 cron jobs start simultaneously (e.g., at 02:00), without OFFSET they would ALL query:
```sql
SELECT ... WHERE DATE < CURRENT_DATE ORDER BY last_updated_at LIMIT 200
```

All 6 jobs would get the **same 200 oldest products** and scrape them simultaneously (wasteful and problematic).

**With OFFSET**: Each job gets a different slice:
```sql
Job 1: LIMIT 200 OFFSET 0    → Products 0-199
Job 2: LIMIT 200 OFFSET 200  → Products 200-399
Job 3: LIMIT 200 OFFSET 400  → Products 400-599
Job 4: LIMIT 200 OFFSET 600  → Products 600-799
Job 5: LIMIT 200 OFFSET 800  → Products 800-999
Job 6: LIMIT 200 OFFSET 1000 → Products 1000-1199
```

**Combined with date filtering**:
- First run (02:00): ~12,000 products available, each job gets 200 unique products = 1,200 total
- Second run (02:20): ~10,800 products available, each job gets 200 unique products = 1,200 total
- ...continues until all products updated...
- After completion: 0 products available (all updated today), all jobs get 0 results

The OFFSET values stay the same, but the **available pool shrinks** as products get updated.

### Daily Cycle

1. **Morning (first run)**: 12,000 products eligible
2. **First 20 min**: 1,200 products updated (6 jobs × 200 products)
3. **Second 20 min**: Next 1,200 products updated
4. **After ~3.33 hours**: All products updated
5. **Rest of day**: Jobs return 0 products (all updated today)
6. **Next day midnight**: All products become eligible again

## Files Modified

### 1. `backend/services/price_updater.py`

**Changes**:
- Added `daily_mode` parameter to `get_all_products()`
- Added `daily_mode` parameter to `run()`
- Added date filter: `AND (DATE(p.last_updated_at) < CURRENT_DATE OR p.last_updated_at IS NULL)`

**Method Signature**:
```python
def get_all_products(
    self, 
    retailer_id: Optional[str] = None, 
    limit: Optional[int] = None, 
    offset: int = 0, 
    daily_mode: bool = False  # NEW
) -> List[Dict]:
```

### 2. `backend/update_prices_daily.py` (NEW)

**Purpose**: Cron entry point for daily mode updates

**Key Features**:
- Sets `daily_mode=True` when calling `updater.run()`
- Uses OFFSET for parallel job coordination (prevents duplicate scraping)
- Keeps LIMIT=200 for memory management
- Logs "DAILY MODE" in startup banner
- Handles 0 products gracefully (when all updated today)

## Railway Cron Setup

### Old Approach (Continuous Updates)
```bash
# 6 jobs running every 20 minutes with different OFFSETs
Job 1: UPDATE_OFFSET=0    UPDATE_LIMIT=200  # Products 1-200
Job 2: UPDATE_OFFSET=250  UPDATE_LIMIT=200  # Products 251-450
Job 3: UPDATE_OFFSET=500  UPDATE_LIMIT=200  # Products 501-700
Job 4: UPDATE_OFFSET=750  UPDATE_LIMIT=200  # Products 751-950
Job 5: UPDATE_OFFSET=1000 UPDATE_LIMIT=200  # Products 1001-1200
Job 6: UPDATE_OFFSET=1250 UPDATE_LIMIT=200  # Products 1251-1450

Problem: Products updated multiple times per day
```

### New Approach (Once-Daily Updates)
```bash
# 6 jobs running every 20 minutes with different OFFSETs
# OFFSET needed for parallel coordination + date filtering for daily limit

Job 1:
  Command: python update_prices_daily.py
  Schedule: */20 * * * *
  Environment:
    UPDATE_LIMIT=200
    UPDATE_OFFSET=0

Job 2:
  UPDATE_LIMIT=200
  UPDATE_OFFSET=200

Job 3:
  UPDATE_LIMIT=200
  UPDATE_OFFSET=400

Job 4:
  UPDATE_LIMIT=200
  UPDATE_OFFSET=600

Job 5:
  UPDATE_LIMIT=200
  UPDATE_OFFSET=800

Job 6:
  UPDATE_LIMIT=200
  UPDATE_OFFSET=1000

Common Environment (all jobs):
  UPDATE_BATCH_SIZE=50
  UPDATE_DELAY=1.0
  UPDATE_PARALLEL=1
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UPDATE_LIMIT` | None | Max products per run (use 200 for memory safety) |
| `UPDATE_OFFSET` | 0 | Skip N oldest products (for parallel jobs: 0, 200, 400, 600, 800, 1000) |
| `UPDATE_BATCH_SIZE` | 50 | Products per batch within a run |
| `UPDATE_DELAY` | 1.0 | Seconds between products |
| `UPDATE_PARALLEL` | 1 | Worker threads (1=sequential, 2-6=parallel) |
| `UPDATE_RETAILER` | None | Filter by retailer (twd, hp, dh, btv, mgh) |

## Timeline Example

Assuming 12,000 products total:

```
00:00 - Midnight: All products become eligible (DATE < CURRENT_DATE)

02:00 - First run (6 jobs):
  - Job 1: Products 1-200     → 200 updated
  - Job 2: Products 201-400   → 200 updated
  - Job 3: Products 401-600   → 200 updated
  - Job 4: Products 601-800   → 200 updated
  - Job 5: Products 801-1000  → 200 updated
  - Job 6: Products 1001-1200 → 200 updated
  Total: 1,200 products updated, 10,800 remaining

02:20 - Second run (6 jobs):
  - Each job: Next 200 oldest products
  Total: 2,400 updated, 9,600 remaining

02:40 - Third run...
03:00 - Fourth run...
03:20 - Fifth run...
03:40 - Sixth run...
04:00 - Seventh run...
04:20 - Eighth run...
04:40 - Ninth run...
05:00 - Tenth run...
05:20 - Final run: Last 1,200 products

05:40 onwards - All runs return 0 products (all updated today)
  - Jobs idle but keep running every 20 min
  - No wasted resources (query is fast with no results)
  - Ready for next day's batch
```

## Database Query Behavior

### First Run (02:00) - All Products Available

**Job 1** (OFFSET=0):
```sql
SELECT product_id, retailer_id, sku, link, last_updated_at
FROM products
WHERE link IS NOT NULL
  AND (retailer_id = 'twd' OR EXISTS (...verified matches...))
  AND retailer_id != 'gbh'
  AND (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL)  -- ~12,000 products
ORDER BY last_updated_at ASC NULLS FIRST
LIMIT 200 OFFSET 0;  -- Gets products 0-199
```

**Job 2** (OFFSET=200):
```sql
-- Same WHERE clause (~12,000 products available)
LIMIT 200 OFFSET 200;  -- Gets products 200-399
```

**Result**: 1,200 unique products updated (6 jobs × 200)

### Second Run (02:20) - Pool Shrunk

**Job 1** (OFFSET=0):
```sql
-- Date filter now excludes 1,200 products updated at 02:00
-- Only ~10,800 products match WHERE clause
LIMIT 200 OFFSET 0;  -- Gets products 0-199 from remaining 10,800
```

**Result**: Another 1,200 unique products updated

### After All Products Updated

**All Jobs**:
```sql
-- Date filter excludes all 12,000 products (all updated today)
-- WHERE clause matches 0 products
LIMIT 200 OFFSET 0;  -- Returns empty result
```

**Result**: Jobs idle until next day

## Memory Safety

**Critical**: Keep `UPDATE_LIMIT=200` to avoid memory leak

- Memory leak in scraper requires small batches with breaks
- 200 products takes ~20 minutes (1s delay + processing)
- 20-minute cron cycle allows memory cleanup between runs
- DO NOT increase limit above 200 without testing memory usage

## Advantages Over Old System

| Feature | Old (Offset-Based Continuous) | New (Offset + Date Filter) |
|---------|-------------------------------|----------------------------|
| Updates per day per product | Multiple (continuous) | Exactly 1 |
| Coordination | Manual OFFSET values | OFFSET + automatic date filter |
| After completion | Still process products | Return 0 results (fast) |
| Configuration | 6 different OFFSET values | Same 6 OFFSET values |
| Daily reset | Manual/time-based | Automatic at midnight |
| Predictability | Always runs | Completes cycle then idles |

## Monitoring

### Check if update is complete today:

```sql
-- Count products not updated today
SELECT COUNT(*) 
FROM products 
WHERE link IS NOT NULL 
  AND (retailer_id = 'twd' OR EXISTS (...verified...))
  AND retailer_id != 'gbh'
  AND (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL);

-- If 0: All products updated today ✓
-- If >0: Still in progress or stalled
```

### Check last update time:

```sql
-- Latest updates
SELECT retailer_id, COUNT(*), MAX(last_updated_at)
FROM products
WHERE DATE(last_updated_at) = CURRENT_DATE
GROUP BY retailer_id;
```

## Fallback to Continuous Mode

To revert to continuous updates (multiple times per day):

1. Change cron command back to: `python update_prices.py`
2. Add environment variables:
   - Job 1: `UPDATE_OFFSET=0`
   - Job 2: `UPDATE_OFFSET=250`
   - Job 3: `UPDATE_OFFSET=500`
   - Job 4: `UPDATE_OFFSET=750`
   - Job 5: `UPDATE_OFFSET=1000`
   - Job 6: `UPDATE_OFFSET=1250`

## Testing Daily Mode Locally

```bash
# Test with 10 products
cd backend
UPDATE_LIMIT=10 python update_prices_daily.py

# Check logs for "DAILY MODE" message
# Check that products are filtered by date

# Run again immediately - should get 0 products
# (all 10 already updated today)
UPDATE_LIMIT=10 python update_prices_daily.py
```

## Next Steps

1. Deploy `price_updater.py` changes to Railway
2. Deploy `update_prices_daily.py` to Railway
3. Update cron jobs to use `update_prices_daily.py`
4. Remove `UPDATE_OFFSET` from all job environment variables
5. Monitor first day to ensure all 12,000 products get updated
6. Monitor subsequent days to ensure jobs idle after completion

## Related Files

- `backend/services/price_updater.py` - Core update service (modified)
- `backend/update_prices_daily.py` - Daily mode entry point (NEW)
- `backend/update_prices.py` - Continuous mode entry point (old)
- `backend/update_globalhouse_prices.py` - GBH-specific updater (separate)
- `backend/CRON_SETUP.md` - General cron documentation

## Pattern Tracking Integration

This daily update mode works seamlessly with the pattern tracking system:

- Each price update saves `extraction_pattern` to `price_history`
- Pattern mismatches will be detected by the alert system (future)
- Date-based filtering ensures consistent pattern history (one entry per day)
