# Price by Location Feature - Implementation Session

**Date**: 2026-02-11
**Status**: Phase 3 Complete - Backend & Scraper Ready
**Next**: Testing with real product URL

---

## ✅ Completed Work

### Phase 1: Database Schema ✅
**Files**:
- `database/init/08_location_pricing.sql` - 5 tables created
- `database/init/09_location_pricing_seed.sql` - 102 GlobalHouse locations seeded

**Tables**:
1. `locations` - Store location data (102 locations pre-populated)
2. `location_monitored_groups` - Which S-dept groups to monitor
3. `location_monitored_locations` - Which locations to scrape
4. `product_location_prices` - Current prices per product per location
5. `location_price_history` - Historical price tracking

**Status**: ✅ Already deployed to production database

---

### Phase 2: Backend API ✅
**File**: `backend/main.py` (lines 1158-1675)

**Endpoints Created**:
```python
# Location CRUD
GET    /api/locations                          # List all locations
POST   /api/locations                          # Add custom location
PATCH  /api/locations/{location_id}            # Update location
DELETE /api/locations/{location_id}            # Remove location

# Monitoring Settings
GET    /api/location-watch/available-groups    # List all S-dept groups
GET    /api/location-watch/monitored-groups    # Get monitored groups
POST   /api/location-watch/monitored-groups    # Set monitored groups
GET    /api/location-watch/monitored-locations # Get monitored locations
POST   /api/location-watch/monitored-locations # Set monitored locations
GET    /api/location-watch/settings            # Get complete settings

# Price Data
GET    /api/location-prices                    # Get location prices
GET    /api/location-prices/export             # Export to Excel
```

**Status**: ✅ Already deployed with backend

---

### Phase 3: Location Price Updater Service ✅

#### 3.1 Location Selection JavaScript ✅
**File**: `backend/scraper-url/adws/adw_modules/crawl4ai_wrapper.py`

**Changes Made**:
- Added `gbh_location` parameter to `scrape_url()` method
- Implemented JavaScript automation for GlobalHouse location selection:
  ```javascript
  // Steps automated:
  1. Click navbar location button ("กำลังช็อปที่")
  2. Wait for modal to open
  3. Search for location name (e.g., "นครปฐม")
  4. Click matching location from results
  5. Click "เลือกช้อปที่สาขานี้" (confirm button)
  6. Wait for price to update
  ```

**Backward Compatible**: Yes - parameter is optional, defaults to None

---

#### 3.2 Scraper CLI Enhancement ✅
**File**: `backend/scraper-url/adws/adw_ecommerce_product_scraper.py`

**Changes Made**:
- Added `--gbh-location` CLI parameter
- Passes location parameter through to `extract_product_data()`
- All retry logic includes location parameter

**Usage**:
```bash
# Regular scrape (no location)
python adw_ecommerce_product_scraper.py --url "https://..."

# With location selection
python adw_ecommerce_product_scraper.py --url "https://..." --gbh-location "นครปฐม"
```

**Backward Compatible**: Yes - existing scripts work unchanged

---

#### 3.3 Location Price Updater Service ✅
**File**: `backend/location_price_updater.py` (NEW)

**What It Does**:
1. Fetches monitored groups from `location_monitored_groups`
2. Fetches monitored locations from `location_monitored_locations`
3. For each group:
   - Gets Thai Watsadu SKUs in the group
   - Finds matched GlobalHouse products
   - For each product × each location:
     - Scrapes price with location selection
     - Updates `product_location_prices`
     - Inserts into `location_price_history`

**Features**:
- Batch processing with configurable batch size
- Memory cleanup (browser process killing)
- Retry logic with exponential backoff
- Dry-run mode for testing
- Comprehensive logging

**Usage**:
```bash
# Full run
python backend/location_price_updater.py

# Test with limited scope
python backend/location_price_updater.py --limit-groups 1 --limit-locations 2

# Dry run (no database updates)
python backend/location_price_updater.py --dry-run --limit-groups 1

# Custom configuration
python backend/location_price_updater.py --batch-size 5 --delay 3.0 --timeout 180
```

**Configuration** (Environment Variables):
```bash
LOC_UPDATE_BATCH_SIZE=10          # Products per batch
LOC_UPDATE_DELAY=2.0              # Delay between products (seconds)
LOC_UPDATE_PARALLEL=1             # Sequential processing
LOC_UPDATE_TIMEOUT=120            # Timeout per product (seconds)
UPDATER_WRITE_LOG=true            # Write log files
```

---

#### 3.4 Deployment Documentation ✅
**File**: `backend/LOCATION_PRICING_DEPLOYMENT.md` (NEW)

**Contents**:
- Complete Railway deployment guide
- Two deployment options (separate service vs existing cron)
- Environment variable configuration
- Local testing instructions
- Troubleshooting guide
- Monitoring and logging guide

---

## 🔧 Testing Status

### Current Issue:
Testing encountered Windows console encoding issues with Thai characters. The scraper runs successfully but we need a **real GlobalHouse product URL** to verify location selection works correctly.

### Test Files Created:
- `backend/test_location_scraper.py` - Async test script for location scraping
- `backend/test_quick.py` - Quick URL validation test

### What Works:
✅ Scraper accepts `--gbh-location` parameter
✅ JavaScript code is injected into page
✅ Browser automation initializes successfully
✅ Pages load and HTML is retrieved

### What Needs Testing:
❌ Location selection automation (need real product URL)
❌ Price extraction after location change
❌ Full end-to-end test with database updates

**Next Step**: Need a working GlobalHouse product URL (with English slug) to test location selection automation.

---

## 📋 Remaining Work

### Phase 4: Frontend (NOT STARTED)
**Pages to Build**:

1. **`/price-by-location/settings`**
   - Multi-select checkboxes for S-dept groups
   - Multi-select checkboxes for locations
   - Save button calls:
     - `POST /api/location-watch/monitored-groups`
     - `POST /api/location-watch/monitored-locations`

2. **`/price-by-location`**
   - Display location prices grouped by TWD SKU
   - Filter by group and location
   - Highlight cheapest location
   - Show price differences
   - Export to Excel button

3. **Navigation**
   - Add links to sidebar/menu

---

## 🚀 Deployment Checklist

### When Ready to Deploy:

#### Option 1: Separate Railway Cron Service (Recommended)
1. Create new Railway service: `location-price-cron`
2. Connect to GitHub repository
3. Set environment variables (copy from main backend)
4. Set start command: `python backend/location_price_updater.py`
5. Set cron schedule: `0 3 * * *` (daily at 3 AM)
6. Deploy

#### Option 2: Add to Existing Backend Cron
1. Update existing cron script to run both updaters
2. Add 1 hour delay between them
3. Redeploy existing cron service

**See**: `backend/LOCATION_PRICING_DEPLOYMENT.md` for detailed instructions

---

## 📝 Notes

### Key Design Decisions:

1. **Location Selection Method**: Browser automation (clicking UI elements) instead of URL parameters
   - Reason: GlobalHouse requires interactive location selection
   - Implementation: JavaScript automation in scraper

2. **Separate Cron Service**: Recommended over single service
   - Pros: Better isolation, independent scheduling, easier debugging
   - Cons: One more service to manage

3. **Backward Compatibility**: All changes are additive
   - Existing price updater works unchanged
   - Location parameter is optional
   - No breaking changes

4. **Data Model**: Simple monitoring lists instead of complex many-to-many
   - `location_monitored_groups` - just group_ids
   - `location_monitored_locations` - just location_ids
   - Easy to configure via API

### Potential Issues to Watch:

1. **GlobalHouse UI Changes**: If they change their location selector UI, JavaScript selectors will need updating
2. **Memory Usage**: Each location scrape opens a browser - memory cleanup is critical
3. **Rate Limiting**: Too many requests might get blocked - delay settings are important
4. **Product URL Format**: Need to verify correct URL format for testing

---

## 🔗 Related Files

**Database**:
- `database/init/08_location_pricing.sql`
- `database/init/09_location_pricing_seed.sql`

**Backend**:
- `backend/main.py` (API endpoints, lines 1158-1675)
- `backend/location_price_updater.py` (NEW)

**Scraper**:
- `backend/scraper-url/adws/adw_modules/crawl4ai_wrapper.py` (location selection JS)
- `backend/scraper-url/adws/adw_ecommerce_product_scraper.py` (CLI parameter)

**Documentation**:
- `backend/LOCATION_PRICING_DEPLOYMENT.md`

**Testing**:
- `backend/test_location_scraper.py`
- `backend/test_quick.py`

---

## 📊 Progress Summary

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| 1 | Database Schema | ✅ Complete | 5 tables, 102 locations seeded |
| 2 | Backend API | ✅ Complete | 11 endpoints implemented |
| 3.1 | Location Selection JS | ✅ Complete | Browser automation added |
| 3.2 | Scraper CLI | ✅ Complete | `--gbh-location` parameter |
| 3.3 | Updater Service | ✅ Complete | Full service with retry/cleanup |
| 3.4 | Deployment Docs | ✅ Complete | Railway guide written |
| 3.5 | Testing | ⏸️ Paused | Need real product URL |
| 4.1 | Settings Page | ❌ Not Started | Frontend implementation |
| 4.2 | Results Page | ❌ Not Started | Frontend implementation |
| 4.3 | Navigation | ❌ Not Started | Frontend implementation |

**Overall Progress**: ~75% complete (backend done, frontend pending)

---

---

## 🎯 Quick Resume Guide (For Next Session)

### Current State:
- **Backend**: 100% complete and ready
- **Database**: Deployed and seeded with 102 locations
- **Scraper**: Enhanced with location selection automation
- **Testing**: Incomplete - need real GlobalHouse product URL
- **Frontend**: Not started

### To Resume Work:

#### Option 1: Continue Testing
```bash
# 1. Get a real GlobalHouse product URL from their website
# 2. Test the location scraper:
cd backend
python test_location_scraper.py

# 3. Test the full updater (dry run):
python location_price_updater.py --dry-run --limit-groups 1 --limit-locations 2
```

#### Option 2: Start Frontend Development
**First**: Read `ai_sum/SUMMARY.md` for frontend architecture
**Then**: Build `/price-by-location/settings` page:
- Use existing UI components from other pages
- Two multi-select lists (groups + locations)
- Save button that calls the API endpoints

#### Option 3: Deploy to Railway
**Prerequisite**: Testing must pass first
**Follow**: `backend/LOCATION_PRICING_DEPLOYMENT.md` step-by-step

### Important Context for Next Session:

**The JavaScript Location Selection Code** is in:
- File: `backend/scraper-url/adws/adw_modules/crawl4ai_wrapper.py`
- Lines: ~656-756 (search for "GlobalHouse location selection")
- What it does:
  1. Detects if URL is GlobalHouse + `gbh_location` parameter is set
  2. Executes JavaScript to click location selector
  3. Searches for location name in Thai (e.g., "นครปฐม")
  4. Clicks matching location
  5. Clicks confirm button
  6. Waits for price update

**The Location Updater Service** is in:
- File: `backend/location_price_updater.py`
- Entry point: `main()` function at bottom
- Key method: `scrape_product_with_location()` - calls scraper with `--gbh-location` parameter
- Database updates: `update_location_price()` - upserts to `product_location_prices` and inserts to history

**Testing Was Blocked By**:
- Windows console encoding issues with Thai characters (solved with UTF-8 wrapper)
- Invalid product URL format (Thai characters in slug caused 404)
- Need: A real, working GlobalHouse product URL (English slug format)

**Example of What Works**:
```python
# This is the pattern that works:
url = "https://www.globalhouse.co.th/product/[english-slug]"
location = "นครปฐม"  # Thai location name

# Scraper will:
# 1. Load the page
# 2. Click location selector
# 3. Search for "นครปฐม"
# 4. Select it
# 5. Extract the price
```

### Files You'll Need to Review:

**For Testing**:
- `backend/test_location_scraper.py` - Test script (ready to use)
- `backend/location_price_updater.py` - Full service (ready to use)

**For Frontend**:
- `ui/app/price-by-location/` - Create this directory
- `ui/app/price-by-location/settings/page.tsx` - Settings page
- `ui/app/price-by-location/page.tsx` - Results page
- Reference: `ui/app/compare/page.tsx` for similar multi-select UI

**For Deployment**:
- `backend/LOCATION_PRICING_DEPLOYMENT.md` - Complete guide

### Known Issues & Gotchas:

1. **Windows Console Encoding**: Already solved with UTF-8 wrapper in test scripts
2. **GlobalHouse URL Format**: Must use English slug, not Thai characters
3. **Location Names**: Database has Thai names (`name_th`) and English names (`name_en`)
4. **Scraper Uses**: Thai names for searching in the UI
5. **Browser Cleanup**: Critical for Railway - already implemented in updater
6. **Memory Management**: Batch size of 10 is safe, don't go too high

### Environment Variables Needed:

```bash
# Already in .env (no changes needed)
DATABASE_URL=<neon_postgres_url>

# New variables for location updater (optional, have defaults)
LOC_UPDATE_BATCH_SIZE=10
LOC_UPDATE_DELAY=2.0
LOC_UPDATE_PARALLEL=1
LOC_UPDATE_TIMEOUT=120
UPDATER_WRITE_LOG=true
```

### API Endpoints Ready to Use:

```javascript
// Get all locations
GET /api/locations?retailer_id=gbh

// Get monitored groups (empty initially)
GET /api/location-watch/monitored-groups

// Set monitored groups
POST /api/location-watch/monitored-groups
Body: { "group_ids": [1, 2, 3] }

// Get monitored locations (empty initially)
GET /api/location-watch/monitored-locations

// Set monitored locations
POST /api/location-watch/monitored-locations
Body: { "location_ids": [1, 2, 3] }

// Get location prices (after scraping)
GET /api/location-prices?group_id=1&location_id=2
```

### Critical Implementation Details:

**How Location Selection Works** (in case you need to debug):
```javascript
// The JavaScript code looks for these selectors:
1. Navbar button: document.querySelectorAll('button') with text "กำลังช็อปที่"
2. Search input: document.querySelector('input[placeholder*="ค้นหา"]')
3. Location result: Element containing location name + "สาขา"
4. Confirm button: Button with text "เลือกช้อปที่สาขานี้"

// Timing is critical:
- Wait 1.5s after clicking navbar button (for modal to open)
- Wait 1s after typing in search (for results to filter)
- Wait 1s after clicking location (for selection)
- Wait 2s after clicking confirm (for price to update)
```

**Database Flow**:
```
User configures settings page
    ↓
POST /api/location-watch/monitored-groups { group_ids: [1, 2] }
POST /api/location-watch/monitored-locations { location_ids: [5, 10] }
    ↓
location_monitored_groups: [1, 2]
location_monitored_locations: [5, 10]
    ↓
Cron runs location_price_updater.py
    ↓
For group 1:
  - Get TWD SKUs in group
  - Find matched GBH products
  - For each GBH product:
      For location 5:
        - Scrape with --gbh-location "นครปฐม"
        - Update product_location_prices
        - Insert location_price_history
      For location 10:
        - Scrape with --gbh-location "ขอนแก่น"
        - Update product_location_prices
        - Insert location_price_history
```

### Next Steps Decision Tree:

**If you want to deploy quickly**:
1. Skip frontend for now
2. Manually configure monitoring via API (Postman/curl)
3. Deploy cron service
4. Build frontend later

**If you want to test thoroughly first**:
1. Get real GlobalHouse product URL
2. Run `test_location_scraper.py`
3. Verify location selection works
4. Run dry-run of full updater
5. Then deploy

**If you want full feature**:
1. Build frontend first
2. Test end-to-end manually
3. Deploy everything together

### Questions to Ask User:

1. Do you have a working GlobalHouse product URL we can test with?
2. Do you want to test locally before deploying?
3. Do you want to build frontend first or deploy backend first?
4. Do you have access to Railway dashboard to create new service?

---

**Last Updated**: 2026-02-11 01:00 AM
