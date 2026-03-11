# Session: Daily Update Mode Implementation

**Date**: 2026-02-03  
**Focus**: Cron job redesign for once-daily product updates using date-based filtering

---

## Context

User explained current cron architecture:
- 6 parallel jobs running every 20 minutes
- Each job updates 200 products using different OFFSET values (0, 250, 500, 750, 1000, 1250)
- Total: 12,000 SKUs requiring ~3.33 hours for full cycle
- **Problem**: Products updated multiple times per day (continuous updates)

**Goal**: Change to update each product **only once per day**

**Constraint**: Must keep small batches (200 products) with 20-minute breaks to avoid memory leak

---

## Solution Chosen: Option A (Date-Based Filtering)

### Approach
- Filter products using: `WHERE (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL)`
- Keep 6 jobs running every 20 min with LIMIT=200 and different OFFSETs
- **OFFSET required** for parallel execution to prevent duplicate scraping
- Jobs self-coordinate through date filter + OFFSET
- After all products updated today, jobs idle (return 0 products)

### Advantages
- Exactly 1 update per day per product
- Date filter prevents multiple daily updates
- OFFSET prevents parallel jobs from duplicate scraping
- Jobs idle after completion (no wasted processing)
- Automatic daily reset at midnight

---

## Changes Made

### 1. **backend/services/price_updater.py** (Modified)

#### Line ~407: Added `daily_mode` parameter to `get_all_products()`
```python
def get_all_products(
    self, 
    retailer_id: Optional[str] = None, 
    limit: Optional[int] = None, 
    offset: int = 0, 
    daily_mode: bool = False  # NEW
) -> List[Dict]:
```

#### Line ~458: Added date filter to SQL query
```python
# Daily mode: only fetch products not updated today
if daily_mode:
    query += " AND (DATE(p.last_updated_at) < CURRENT_DATE OR p.last_updated_at IS NULL)"
```

#### Line ~1040: Added `daily_mode` parameter to `run()`
```python
def run(
    self, 
    retailer_id: Optional[str] = None, 
    limit: Optional[int] = None, 
    offset: int = 0, 
    daily_mode: bool = False  # NEW
) -> UpdateStats:
```

#### Line ~1054: Log daily mode status
```python
if daily_mode:
    logger.info("DAILY MODE: Only updating products not updated today")
```

#### Line ~1068: Pass `daily_mode` to query
```python
all_products = self.get_all_products(retailer_id, limit, offset, daily_mode)
```

---

### 2. **backend/update_prices_daily.py** (NEW FILE)

New cron entry point for daily mode updates.

**Key Features**:
- Sets `daily_mode=True` when calling `updater.run()`
- Uses OFFSET for parallel job coordination (prevents duplicate scraping)
- Keeps LIMIT=200 for memory management
- Enhanced logging for daily mode
- Handles 0 products gracefully (when all updated today)

**Usage**:
```bash
UPDATE_LIMIT=200 python update_prices_daily.py
```

**Environment Variables**:
- `UPDATE_LIMIT` - Max products per run (recommended: 200)
- `UPDATE_OFFSET` - Skip N oldest products (required for parallel jobs)
- `UPDATE_BATCH_SIZE` - Products per batch (default: 50)
- `UPDATE_DELAY` - Seconds between products (default: 1.0)
- `UPDATE_PARALLEL` - Worker threads (default: 1)
- `UPDATE_RETAILER` - Optional retailer filter

---

### 3. **backend/DAILY_UPDATE_MODE.md** (NEW FILE)

Comprehensive documentation covering:
- Date-based filtering concept
- Parallel job coordination with OFFSET
- Daily cycle timeline (3.33 hours to complete)
- Railway cron setup (6 jobs with different OFFSETs)
- Environment variables
- Database query behavior
- Memory safety requirements
- Monitoring queries
- Comparison with old offset-based system
- Testing instructions
- Fallback to continuous mode

---

## Files Modified Summary

| File | Type | Lines Changed |
|------|------|---------------|
| `backend/services/price_updater.py` | Modified | ~5 additions across 3 methods |
| `backend/update_prices_daily.py` | Created | 160 lines |
| `backend/DAILY_UPDATE_MODE.md` | Created | 350+ lines |

---

## Railway Cron Configuration

### Old (Offset-Based - Continuous)
```bash
Job 1: UPDATE_OFFSET=0    UPDATE_LIMIT=200
Job 2: UPDATE_OFFSET=250  UPDATE_LIMIT=200
Job 3: UPDATE_OFFSET=500  UPDATE_LIMIT=200
Job 4: UPDATE_OFFSET=750  UPDATE_LIMIT=200
Job 5: UPDATE_OFFSET=1000 UPDATE_LIMIT=200
Job 6: UPDATE_OFFSET=1250 UPDATE_LIMIT=200
```

### New (Date-Based - Once Daily)
```bash
# 6 jobs with same command but different OFFSETs
Command: python update_prices_daily.py
Schedule: */20 * * * *

Job 1 Environment:
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
```

---

## How It Works

### Daily Cycle Timeline

```
00:00 - All 12,000 products become eligible (date < today)

02:00 - Run 1 (6 jobs × 200 products = 1,200 updated)
02:20 - Run 2 (1,200 more updated, 10,800 remaining)
02:40 - Run 3 (1,200 more updated, 9,600 remaining)
...
05:20 - Run 10 (last 1,200 updated, 0 remaining)

05:40 onwards - All jobs return 0 products (idle)
```

Total time: **~3.33 hours** to update all 12,000 products  
Rest of day: Jobs idle (fast query, no processing)

### SQL Query with Date Filter

```sql
SELECT product_id, retailer_id, sku, link, last_updated_at
FROM products
WHERE link IS NOT NULL
  AND (retailer_id = 'twd' OR EXISTS (...verified matches...))
  AND retailer_id != 'gbh'
  AND (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL)  -- NEW
ORDER BY last_updated_at ASC NULLS FIRST
LIMIT 200;
```

### OFFSET + Date Filter Coordination

**Why both are needed**:
- **Date filter**: Ensures products only updated once per day
- **OFFSET**: Prevents simultaneous jobs from scraping same products

**How it works**:
1. At 02:00, all 6 jobs start simultaneously
2. Job 1: Fetches OFFSET 0 from products where date < today (gets products 0-199)
3. Job 2: Fetches OFFSET 200 from products where date < today (gets products 200-399)
4. Job 3: Fetches OFFSET 400 from products where date < today (gets products 400-599)
5. Each job processes different products - no duplicates
6. After all jobs finish, 1,200 products have today's timestamp
7. At 02:20, the pool of eligible products shrinks to 10,800
8. Jobs fetch their OFFSET ranges from the remaining 10,800 products
9. Process repeats until all products updated

---

## Testing Instructions

### Test 1: Daily Mode Works
```bash
cd backend
UPDATE_LIMIT=10 python update_prices_daily.py
# Should see "DAILY MODE" in logs
# Should update 10 products
```

### Test 2: Date Filter Works
```bash
# Run again immediately
UPDATE_LIMIT=10 python update_prices_daily.py
# Should get 0 products (all updated today already)
```

### Test 3: Check Database
```sql
-- Count products not updated today
SELECT COUNT(*) 
FROM products 
WHERE link IS NOT NULL 
  AND (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL);

-- Should decrease after each run
-- Should reach 0 after ~3.33 hours
```

---

## Deployment Checklist

- [ ] Deploy `price_updater.py` changes to Railway
- [ ] Deploy `update_prices_daily.py` to Railway
- [ ] Update 6 cron jobs in Railway:
  - [ ] Change command to `python update_prices_daily.py`
  - [ ] Set `UPDATE_OFFSET` values: 0, 200, 400, 600, 800, 1000
  - [ ] Keep `UPDATE_LIMIT=200`
  - [ ] Keep schedule `*/20 * * * *`
- [ ] Monitor first day logs:
  - [ ] Check "DAILY MODE" appears in logs
  - [ ] Verify each job processes ~200 products per run
  - [ ] Verify total 1,200 products per 20-minute cycle
  - [ ] Verify all 12,000 updated within 3.33 hours
  - [ ] Verify jobs return 0 products after completion
- [ ] Monitor second day:
  - [ ] Verify cycle repeats correctly
  - [ ] Check no products missed

---

## Pattern Tracking Integration

Daily mode works seamlessly with pattern tracking:
- Each update saves `extraction_pattern` to `price_history`
- One update per day = one pattern entry per day
- Consistent pattern history for alert system (future)
- NULL patterns for old data (before pattern tracking deployed)

---

## Next Steps

1. **Deploy database migration**: `database/init/12_extraction_pattern.sql`
   - Adds `extraction_pattern VARCHAR(100)` to price_history

2. **Deploy code changes**:
   - Pattern tracking changes (already completed in previous session)
   - This session's daily mode changes

3. **Switch cron jobs to daily mode**:
   - Update Railway configuration as per checklist above

4. **Monitor for 1 week**:
   - Collect pattern data
   - Verify daily updates working correctly

5. **Implement alert system** (after 1 week):
   - Pattern mismatch detection
   - Email/Slack notifications

---

## Key Decisions

1. **Combined date-based filtering WITH offset-based parallelization**:
   - Date filter: Ensures each product updated only once per day
   - OFFSET: Required for parallel jobs to avoid duplicate scraping
   - Together: Date filter handles daily reset, OFFSET handles parallelization

2. **Kept 6 parallel jobs with small batches**:
   - Memory leak constraint forces small batches
   - 200 products × 6 jobs = 1,200/run (optimal throughput)
   - 20-minute cycles allow memory cleanup

3. **Kept OFFSET values (0, 200, 400, 600, 800, 1000)**:
   - Prevents simultaneous jobs from scraping same products
   - Simple configuration (fixed values)
   - Works with shrinking product pool as date filter handles reset

---

## Monitoring Queries

### Check update progress today:
```sql
SELECT 
    retailer_id, 
    COUNT(*) as updated_today,
    MAX(last_updated_at) as latest_update
FROM products
WHERE DATE(last_updated_at) = CURRENT_DATE
GROUP BY retailer_id
ORDER BY retailer_id;
```

### Check products still pending:
```sql
SELECT COUNT(*) as pending
FROM products
WHERE link IS NOT NULL
  AND (retailer_id = 'twd' OR EXISTS (
      SELECT 1 FROM product_matches pm
      WHERE pm.candidate_product_id = product_id
      AND pm.verified_result = TRUE
  ))
  AND retailer_id != 'gbh'
  AND (DATE(last_updated_at) < CURRENT_DATE OR last_updated_at IS NULL);
```

### Check last 10 updates:
```sql
SELECT 
    retailer_id, 
    sku, 
    current_price,
    last_updated_at
FROM products
WHERE DATE(last_updated_at) = CURRENT_DATE
ORDER BY last_updated_at DESC
LIMIT 10;
```

---

## Related Sessions

- **2026-01-29**: Memory leak and thread exhaustion fixes
- **2026-02-02**: Price updater and scraper fixes
- **2026-02-03**: Pattern tracking implementation (earlier today)
- **2026-02-03**: Daily update mode implementation (this session)

---

## Notes

- Old `update_prices.py` still exists (fallback for continuous mode)
- GlobalHouse still uses separate updater (`update_globalhouse_prices.py`)
- Pattern tracking ready to deploy (waiting for this daily mode deployment)
- Alert system deferred until 1 week of pattern data collected
