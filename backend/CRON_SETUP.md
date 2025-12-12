# Price Update Cron Job Setup

## Overview

The price update service scrapes all products daily to keep prices current.

**Estimated Time:** ~2-4 hours for 10,000 products

## Files

| File | Description |
|------|-------------|
| `services/price_updater.py` | Main price update service |
| `update_prices.py` | Cron job entry point |

## Railway Cron Setup

### Option 1: Same Service (Recommended for small scale)

Add a cron job to your existing Railway service:

1. Go to your Railway project
2. Click on your backend service
3. Go to **Settings** > **Cron**
4. Add cron schedule: `0 19 * * *` (2 AM Thailand = 7 PM UTC)
5. Set command: `python update_prices.py`

### Option 2: Separate Service (Recommended for production)

Create a dedicated cron service:

1. In Railway, click **New** > **Empty Service**
2. Connect to same GitHub repo
3. Set **Root Directory**: `backend`
4. Set **Start Command**: `python update_prices.py`
5. Go to **Settings** > **Deploy**
6. Set **Schedule**: `0 19 * * *`

### Environment Variables

Same as main backend:

```
DATABASE_URL=postgresql://...
UPDATE_BATCH_SIZE=50        # Optional: products per batch
UPDATE_DELAY=1.0            # Optional: delay between products (seconds)
UPDATE_PARALLEL=1           # Optional: 1=sequential, 2-6=parallel retailer workers
UPDATE_RETAILER=            # Optional: specific retailer (twd, hp, dh, btv, gbh, mgh)
```

## Local Testing

```bash
cd backend

# Test with dry run (no DB updates)
python -c "from services.price_updater import PriceUpdater; p = PriceUpdater(dry_run=True); p.run()"

# Update specific retailer
python services/price_updater.py --retailer twd

# Custom batch size
python services/price_updater.py --batch-size 100

# Sequential processing (1 worker, default)
python services/price_updater.py --parallel 1

# Parallel processing (3 retailers at once)
python services/price_updater.py --parallel 3

# Full dry run with parallel processing
python services/price_updater.py --dry-run --parallel 5
```

## CLI Options

```
python services/price_updater.py [OPTIONS]

Options:
  --retailer, -r    Specific retailer ID (twd, hp, dh, btv, gbh, mgh)
  --batch-size, -b  Batch size (default: 50)
  --delay, -d       Delay between products in seconds (default: 1.0)
  --parallel, -p    Parallel workers: 1=sequential, 2-6=parallel (default: 1)
  --dry-run         Test without updating database
  --verbose, -v     Verbose output
```

## Parallel Processing

The price updater supports parallel processing across retailers:

| Workers | Mode | Description |
|---------|------|-------------|
| 1 | Sequential | Process one retailer at a time (default, safest) |
| 2-3 | Light parallel | Good balance of speed and resource usage |
| 4-6 | Full parallel | Maximum speed, higher resource usage |

**How it works:**
- Each worker processes one retailer independently
- Products within each retailer are still processed sequentially (with rate limiting)
- Thread-safe statistics tracking across all workers
- Maximum 6 workers (one per retailer)

**Recommendations:**
- Use `--parallel 1` for initial testing or low-resource environments
- Use `--parallel 3` for balanced production runs
- Use `--parallel 6` for fastest processing (requires more memory/CPU)

## What It Does

1. **Fetches all products** from database (with valid URLs)
2. **Groups by retailer** for efficient processing
3. **Processes in batches** of 50 products
4. **For each product:**
   - Calls existing scraper to get fresh price
   - Updates `products` table:
     - `current_price` (new price)
     - `lowest_price` (if new price is lower)
     - `highest_price` (if new price is higher)
     - `last_updated_at` (timestamp)
   - Inserts record into `price_history` table
5. **Logs progress** and saves summary JSON

## Output

### Logs

```
2024-01-15 02:00:00 - INFO - Price Update Started
2024-01-15 02:00:01 - INFO - Total products to update: 10000
2024-01-15 02:00:01 - INFO - Processing retailer: twd (1500 products)
2024-01-15 02:00:02 - INFO - [1/50] Processing SKU123 - https://...
2024-01-15 02:00:05 - INFO - Updated: 299.0 -> 289.0
...
```

### Summary File

Saved to `results/price_updates/summary_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2024-01-15T04:30:00",
  "stats": {
    "total_products": 10000,
    "updated": 9500,
    "failed": 300,
    "unchanged": 200,
    "price_increased": 1200,
    "price_decreased": 800,
    "new_lowest": 150,
    "new_highest": 50
  },
  "config": {
    "batch_size": 50,
    "delay": 1.0,
    "parallel_workers": 3,
    "retailer": null
  }
}
```

## Monitoring

Check Railway logs for:
- Start/completion messages
- Failure rates (alert if > 30%)
- Duration

## Cron Schedule Examples

| Schedule | Description |
|----------|-------------|
| `0 19 * * *` | Daily at 2 AM Thailand (7 PM UTC) |
| `0 19 * * 1` | Weekly on Monday |
| `0 */6 * * *` | Every 6 hours |
| `0 19 * * 1-5` | Weekdays only |

## Troubleshooting

### High Failure Rate

- Check if retailer websites are blocking
- Increase delay: `UPDATE_DELAY=2.0`
- Run specific retailer to isolate: `UPDATE_RETAILER=twd`

### Timeout Issues

- Reduce batch size: `UPDATE_BATCH_SIZE=25`
- Check Railway memory limits

### Database Connection

- Verify `DATABASE_URL` is set correctly
- Check Neon connection pooling limits
