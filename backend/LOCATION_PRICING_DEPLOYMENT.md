# Location-Based Pricing Deployment Guide

This guide covers deploying the location-based pricing feature for GlobalHouse products.

---

## Overview

The location-based pricing feature allows tracking GlobalHouse product prices across different physical store locations. It consists of:

1. **Database Schema** - 5 new tables for locations and location-specific prices
2. **Backend API** - Endpoints for managing locations, monitored groups/locations, and viewing prices
3. **Location Price Updater** - Cron service that scrapes location-specific prices
4. **Frontend** (to be implemented) - UI for settings and viewing location prices

---

## Components Already Deployed

### ✅ Database Schema
Location: `database/init/08_location_pricing.sql` and `09_location_pricing_seed.sql`

Tables created:
- `locations` - 102 GlobalHouse locations (pre-seeded)
- `location_monitored_groups` - Which S-dept groups to monitor
- `location_monitored_locations` - Which locations to scrape
- `product_location_prices` - Current prices per product per location
- `location_price_history` - Historical price tracking

**Status**: ✅ Already created via database migrations

### ✅ Backend API
Location: `backend/main.py` (lines 1158-1675)

Endpoints available:
```python
# Location CRUD
GET    /api/locations                          # List all locations
POST   /api/locations                          # Add custom location
PATCH  /api/locations/{location_id}            # Update location
DELETE /api/locations/{location_id}            # Remove location

# Monitoring Settings
GET    /api/location-watch/available-groups    # List all S-dept groups
GET    /api/location-watch/monitored-groups    # Get monitored groups
POST   /api/location-watch/monitored-groups    # Set monitored groups (array of group_ids)
GET    /api/location-watch/monitored-locations # Get monitored locations
POST   /api/location-watch/monitored-locations # Set monitored locations (array of location_ids)
GET    /api/location-watch/settings            # Get complete settings

# Price Data
GET    /api/location-prices                    # Get location prices (filterable)
POST   /api/location-prices/scrape             # Manual scrape trigger (placeholder)
GET    /api/location-prices/export             # Export to Excel
```

**Status**: ✅ Already deployed with backend

---

## New Component to Deploy

### 📦 Location Price Updater Service

**File**: `backend/location_price_updater.py`

This is a **standalone cron service** that runs on Railway alongside the main backend.

#### What It Does:
1. Fetches monitored S-dept groups from `location_monitored_groups`
2. Fetches monitored locations from `location_monitored_locations`
3. For each group:
   - Gets Thai Watsadu SKUs in the group
   - Finds matched GlobalHouse products
   - For each GlobalHouse product × each location:
     - Scrapes the price with location selection (using browser automation)
     - Updates `product_location_prices`
     - Inserts into `location_price_history`

#### How It Works:
The scraper uses **browser automation** (Playwright) to:
1. Click the location selector button in GlobalHouse navbar
2. Search for the desired location name (e.g., "นครปฐม")
3. Click the matching location
4. Click "เลือกช้อปที่สาขานี้" (Select this branch)
5. Wait for price to update
6. Extract the location-specific price

---

## Railway Deployment Steps

### Option 1: Create New Cron Service (Recommended)

1. **Go to Railway Dashboard** → Your project

2. **Create New Service**:
   - Click "New" → "Empty Service"
   - Name: `location-price-cron`

3. **Connect to GitHub Repository**:
   - Settings → Connect to GitHub
   - Select your PriceHawk repository
   - Set root directory: `/` (same as main backend)

4. **Configure Environment Variables**:
   Copy all environment variables from your main backend service:
   ```bash
   DATABASE_URL=<your_neon_postgres_url>
   LOC_UPDATE_BATCH_SIZE=10          # Products per batch
   LOC_UPDATE_DELAY=2.0              # Delay between products (seconds)
   LOC_UPDATE_PARALLEL=1             # Sequential processing (default)
   LOC_UPDATE_TIMEOUT=120            # Timeout per product (seconds)
   UPDATER_WRITE_LOG=true            # Write log files
   ```

5. **Set Start Command**:
   - Settings → Start Command:
   ```bash
   python backend/location_price_updater.py
   ```

6. **Configure Cron Schedule**:
   - Settings → Cron Schedule:
   ```
   0 3 * * *
   ```
   (Runs daily at 3 AM, 1 hour after main price updater)

7. **Deploy**:
   - Railway will automatically deploy on push
   - Or manually trigger: Settings → Redeploy

---

### Option 2: Add to Existing Backend Cron (Alternative)

If you want to run it from your existing backend cron service:

1. **Update existing cron script**:
   ```bash
   # Run main price updater
   python backend/services/price_updater.py --limit 500

   # Run location price updater (1 hour later)
   sleep 3600
   python backend/location_price_updater.py
   ```

2. **Pros**:
   - Single service to manage
   - Shares same environment

3. **Cons**:
   - Longer total runtime
   - Single point of failure
   - Less flexible scheduling

**Recommendation**: Use Option 1 (separate service) for better isolation and independent scheduling.

---

## Testing Locally

### Test with Limited Scope:

```bash
# Test with 1 group and 2 locations
python backend/location_price_updater.py --limit-groups 1 --limit-locations 2

# Dry run (no database updates)
python backend/location_price_updater.py --dry-run --limit-groups 1 --limit-locations 1

# Test with specific batch size
python backend/location_price_updater.py --batch-size 5 --limit-groups 1
```

### Expected Output:

```
============================================================
Location Price Update Started: 2026-02-11 10:30:00
Configuration: batch_size=10, parallel_workers=1, dry_run=False
Memory at start: 15.5% (1.23GB used)
============================================================

Monitored groups: 1
  - อุปกรณ์ช่าง (ID: 5)

Monitored locations: 2
  - นครปฐม (GBH-002)
  - ขอนแก่น (GBH-015)

============================================================
Processing Group: อุปกรณ์ช่าง
============================================================
Found 15 GlobalHouse products in this group
Total combinations to scrape: 15 products × 2 locations = 30

Batch 1: products 1-10
  [1/10] Processing GBH123 - สว่านไฟฟ้า...
    → Location: นครปฐม
    Updated: ฿950.00
    → Location: ขอนแก่น
    Updated: ฿920.00
  ...

============================================================
LOCATION PRICE UPDATE COMPLETE
============================================================
Duration: 0:45:30
Total Combinations: 30
Updated: 28
Failed: 2
Memory at end: 18.2% (1.45GB used)
============================================================
```

---

## Configuration Options

### Environment Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOC_UPDATE_BATCH_SIZE` | `10` | Products per batch (smaller = more frequent cleanup) |
| `LOC_UPDATE_DELAY` | `2.0` | Seconds between products (rate limiting) |
| `LOC_UPDATE_PARALLEL` | `1` | Parallel workers (1 = sequential, safer) |
| `LOC_UPDATE_TIMEOUT` | `120` | Timeout per product scrape (seconds) |
| `UPDATER_WRITE_LOG` | `true` | Write log files |

### Command-Line Options:

```bash
python backend/location_price_updater.py --help

Options:
  --batch-size, -b      Batch size (default: 10)
  --delay, -d           Delay between products in seconds (default: 2.0)
  --parallel, -p        Parallel workers (default: 1)
  --timeout, -t         Timeout per product in seconds (default: 120)
  --dry-run             Test without updating database
  --limit-groups        Limit to N groups for testing
  --limit-locations     Limit to N locations for testing
  --verbose, -v         Verbose output
```

---

## Monitoring & Logs

### Railway Logs:

1. Go to Railway Dashboard → `location-price-cron` service
2. Click "Logs" tab
3. Look for:
   - Successful scrapes: `Updated: ฿XXX.XX`
   - Failures: `Failed to scrape price`
   - Completion summary at the end

### Log Files:

If `UPDATER_WRITE_LOG=true`, logs are written to:
```
location_price_update_YYYYMMDD.log
```

### Database Checks:

```sql
-- Check latest location prices
SELECT
    l.name_th,
    p.name,
    plp.price,
    plp.last_updated_at
FROM product_location_prices plp
JOIN locations l ON plp.location_id = l.location_id
JOIN products p ON plp.product_id = p.product_id
ORDER BY plp.last_updated_at DESC
LIMIT 20;

-- Check history
SELECT
    COUNT(*) as total_records,
    MIN(scraped_at) as first_scrape,
    MAX(scraped_at) as last_scrape
FROM location_price_history;
```

---

## Troubleshooting

### Issue: Location selection fails

**Symptoms**: Logs show `Failed to select location` or prices are not updating

**Solutions**:
1. Check if GlobalHouse changed their UI (button selectors may need updating)
2. Increase timeout: `--timeout 180`
3. Check browser is launching: Look for Playwright errors in logs
4. Test locally with verbose mode: `--verbose`

### Issue: High memory usage on Railway

**Solutions**:
1. Reduce batch size: `LOC_UPDATE_BATCH_SIZE=5`
2. Ensure Railway service has adequate memory (2GB+ recommended)
3. Check cleanup is running (browser processes being killed)

### Issue: Scraper timing out

**Solutions**:
1. Increase timeout per product: `LOC_UPDATE_TIMEOUT=180`
2. Reduce concurrent products: `LOC_UPDATE_BATCH_SIZE=5`
3. Check network connectivity to GlobalHouse

### Issue: No location prices found

**Check**:
1. Are groups monitored? `SELECT * FROM location_monitored_groups;`
2. Are locations monitored? `SELECT * FROM location_monitored_locations;`
3. Are there verified GlobalHouse matches? Check `product_matches` table

---

## Next Steps

### Frontend Implementation:

1. **Settings Page** (`/price-by-location/settings`):
   - Checkboxes to select S-dept groups to monitor
   - Checkboxes to select locations to monitor
   - Save button calls API endpoints

2. **Results Page** (`/price-by-location`):
   - Display location prices grouped by TWD SKU
   - Highlight cheapest location
   - Filter by group and location
   - Export to Excel button

See `ai_sum/SUMMARY.md` for detailed frontend requirements.

---

## Estimated Resource Usage

### For 50 products × 5 locations = 250 scrapes:

- **Time**: ~45 minutes (with 2s delay between products)
- **Memory**: ~2GB peak (with cleanup)
- **CPU**: Moderate (browser rendering)
- **Network**: ~250 HTTP requests to GlobalHouse

### Railway Cost Estimate:

- Using Railway's $5/month Starter plan
- Runs once daily (3 AM)
- Estimated: ~$2-3/month additional cost for cron service

---

## Success Criteria

After deployment, verify:

1. ✅ Cron runs daily at 3 AM
2. ✅ Location prices are being scraped and stored
3. ✅ History table is growing
4. ✅ No critical errors in Railway logs
5. ✅ Memory usage stable (no leaks)
6. ✅ API endpoints return location price data

---

## Support

For issues or questions:
1. Check logs in Railway Dashboard
2. Review `ai_sum/sessions/` for similar issues
3. Test locally with `--dry-run` first
4. Verify database state with SQL queries above

---

**Last Updated**: 2026-02-11
