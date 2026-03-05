# Location Price Updater - Batch Processing Guide

## Problem Solved

The location price updater can process hundreds or thousands of product×location combinations. Processing all at once can cause:
- Memory exhaustion
- Browser process accumulation
- Timeouts and failures

## Solution: LIMIT + OFFSET

Process combinations in chunks, just like `update_prices.py`.

---

## Environment Variables

```env
GBH_UPDATE_BATCH_SIZE=20       # Products per batch (for rate limiting)
GBH_UPDATE_DELAY=2.0           # Delay between products (seconds)
GBH_UPDATE_TIMEOUT=120         # Timeout per product (seconds)
GBH_UPDATE_LIMIT=100           # Process only 100 combinations per run
GBH_UPDATE_OFFSET=0            # Skip first N combinations (continue from previous)
```

---

## Usage Examples

### 1. Process All (Default)
```bash
python backend/location_price_updater.py
```
Processes ALL combinations (may fail with large datasets)

### 2. Process First 100 Combinations
```bash
python backend/location_price_updater.py --limit 100
```
Or set in `.env`:
```env
GBH_UPDATE_LIMIT=100
```

### 3. Continue from Combination 100 (Next Batch)
```bash
python backend/location_price_updater.py --limit 100 --offset 100
```
Or set in `.env`:
```env
GBH_UPDATE_LIMIT=100
GBH_UPDATE_OFFSET=100
```

### 4. Multiple Cron Jobs (Recommended)

**Cron Job 1** - Every 20 minutes, offset 0:
```bash
# .env
GBH_UPDATE_LIMIT=100
GBH_UPDATE_OFFSET=0
```

**Cron Job 2** - Every 20 minutes, offset 100:
```bash
# .env
GBH_UPDATE_LIMIT=100
GBH_UPDATE_OFFSET=100
```

**Cron Job 3** - Every 20 minutes, offset 200:
```bash
# .env
GBH_UPDATE_LIMIT=100
GBH_UPDATE_OFFSET=200
```

---

## How It Works

1. **Collect All Combinations**
   - Get all monitored groups × monitored locations
   - Get GlobalHouse products for each group
   - Create product×location combinations
   - Sort by least recently updated (NULL first)

2. **Apply Offset** (skip already processed)
   ```
   Total: 500 combinations
   Offset: 100
   → Skip first 100, start at combination 101
   ```

3. **Apply Limit** (process only N)
   ```
   After offset: 400 combinations remaining
   Limit: 100
   → Process combinations 101-200
   ```

4. **Process**
   - Scrape each combination
   - Update database
   - Track progress

5. **Output Shows Next Offset**
   ```
   💡 To continue: --offset 200 (remaining: 300 combinations)
   ```

---

## Example Output

```
============================================================
Location Price Update Started: 2026-03-05 10:30:00
Configuration: batch_size=20, parallel_workers=1, dry_run=False
Limit: 100, Offset: 0
Memory at start: 15.5% (1.23GB used)
============================================================

Collecting all product×location combinations...
Total combinations available: 500

Processing range: combinations 1 to 100 of 500
Will process: 100 combinations
  - 25 unique products
  - 4 unique locations

============================================================
Starting Price Scraping
============================================================
[1/100] 60223771 @ ร้อยเอ็ด (GH-101)
  ✓ ฿24.75
[2/100] 60223771 @ ขอนแก่น (GH-102)
  ✓ ฿24.25
...
[100/100] 60087982 @ อุดรธานี (GH-115)
  ✓ ฿25.00

============================================================
LOCATION PRICE UPDATE COMPLETE
============================================================
Duration: 0:45:23
Processed: 100 combinations
Updated: 98
Failed: 2
Success Rate: 98.0%
Memory at end: 18.2% (1.45GB used)
============================================================

💡 To continue: --offset 100 (remaining: 400 combinations)
```

---

## Railway Cron Setup

### Option 1: Single Job with Gradual Progress

Schedule: Every 20 minutes
```bash
python backend/location_price_updater.py --limit 100 --offset 0
```

Manually increment offset after each successful run, or use a script to track progress.

### Option 2: Multiple Parallel Jobs (Recommended)

Create 3 separate Railway services:

**Service 1: location-price-cron-1**
- Schedule: `*/20 * * * *` (every 20 minutes)
- Env: `GBH_UPDATE_LIMIT=100`, `GBH_UPDATE_OFFSET=0`
- Processes: combinations 1-100

**Service 2: location-price-cron-2**
- Schedule: `*/20 * * * *` (every 20 minutes)
- Env: `GBH_UPDATE_LIMIT=100`, `GBH_UPDATE_OFFSET=100`
- Processes: combinations 101-200

**Service 3: location-price-cron-3**
- Schedule: `*/20 * * * *` (every 20 minutes)
- Env: `GBH_UPDATE_LIMIT=100`, `GBH_UPDATE_OFFSET=200`
- Processes: combinations 201-300

This way all 300 combinations complete in ~20 minutes instead of ~60 minutes.

---

## Testing Locally

### Test with Small Limit
```bash
python backend/location_price_updater.py --limit 5 --dry-run
```

### Test Specific Range
```bash
python backend/location_price_updater.py --limit 10 --offset 50
```

### Test with Test Filters
```bash
python backend/location_price_updater.py --limit-groups 1 --limit-locations 2
```
(Note: `--limit-groups` and `--limit-locations` override `--limit`/`--offset`)

---

## Combination Sorting

Combinations are sorted by **least recently updated** first:
1. NULL (never updated) → Highest priority
2. Oldest timestamp
3. Newest timestamp

This ensures that:
- New products get scraped first
- Stale prices get refreshed
- Recently updated prices are skipped

---

## Monitoring

Check logs for:
- `Total combinations available: X` - Total work to do
- `Processing range: combinations A to B of X` - Current chunk
- `💡 To continue: --offset N` - Next offset to use
- `Success Rate: X%` - Quality check

If success rate < 50%, the script exits with error code 1.

---

## Summary

✅ **Before**: Process all 500 combinations → 2+ hours, memory issues
✅ **After**: Process 100 combinations → 20-30 minutes, stable
✅ **Multiple jobs**: Process 300 combinations in parallel → 20-30 minutes total
