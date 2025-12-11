# Railway Deployment Issue: Missing Playwright Dependencies

## Root Cause
**Missing system library on Railway server:**
```
libglib-2.0.so.0: cannot open shared object file: No such file or directory
```

## What's Happening
1. **Playwright Chromium fails to launch** - The Chromium browser binary requires `libglib-2.0.so.0` (a GLib shared library) which is not installed on the Railway container

2. **Both browser mode AND text mode fail** - The crawl4ai wrapper can't initialize in either mode because both still require the browser binary to be functional

3. **Affected URLs:**
   - `https://www.thaiwatsadu.com/th/sku/60260253`
   - `https://www.boonthavorn.com/gelato-bath-1257499/`

4. **Result:** 0 products scraped, 2 errors returned

## Why the Retry Logic Fix Didn't Help
The retry logic handles **transient** browser closure errors. This is a **system dependency issue** - the required Linux libraries are simply not installed on Railway's container image.

## Solution Direction
The Railway deployment needs system-level dependencies for Playwright:
- Install `libglib-2.0` and other Chromium dependencies via `nixpacks.toml` or `Dockerfile`
- Or use `playwright install-deps` during build
- Or consider a browser-less scraping approach (httpx/requests) as fallback

## Resolution (Implemented)
**Date:** 2025-12-11
**Approach:** Updated `backend/nixpacks.toml` with comprehensive Playwright/Chromium dependency configuration

**Changes Made:**
1. **Added build phase** with `playwright install-deps` and `playwright install chromium` commands
   - This ensures all system dependencies are installed during the build phase, not at startup
   - Reduces startup time by moving browser installation to build phase

2. **Enhanced documentation** in nixpacks.toml with inline comments explaining each dependency
   - All existing Nix packages were already sufficient (glib, nss, atk, cups, etc.)
   - Added detailed comments for maintainability

3. **Updated start command** to only run the FastAPI server
   - Removed `playwright install chromium` from start command
   - Now uses: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`

**Expected Outcome:**
- Playwright Chromium should launch successfully with all required system libraries
- Faster deployment startup times (browser installation happens during build, not runtime)
- Both browser mode and text mode should work properly on Railway
