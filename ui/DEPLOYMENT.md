# PriceHawk Frontend Deployment Guide

## Environment Configuration

The frontend can be deployed to three environments:
1. **Local Development** - Development machine
2. **UAT** - User Acceptance Testing (pricehawk-nonprod.vercel.app)
3. **Production** - Live environment (pricehawk-production.vercel.app)

## Backend URLs

- **UAT Backend**: `https://pricehawk-uat.up.railway.app`
- **PRD Backend**: `https://pricehawk-production-d139.up.railway.app`

---

## Deployment Methods

### Method 1: Using Separate Vercel.json Files (Recommended)

We maintain separate `vercel.json` files for each environment:

- `vercel.json` - Currently configured for **UAT**
- `vercel.uat.json` - UAT configuration
- `vercel.prd.json` - Production configuration

#### Deploy to UAT
```bash
# vercel.json is already set to UAT, just deploy
git push origin sit

# Or use Vercel CLI
cd ui
npx vercel --prod
```

#### Deploy to Production
```bash
# 1. Backup current vercel.json
cp vercel.json vercel.json.backup

# 2. Copy production config
cp vercel.prd.json vercel.json

# 3. Commit and push
git add vercel.json
git commit -m "Switch to production backend"
git push origin main

# 4. Restore UAT config for future UAT deployments
cp vercel.uat.json vercel.json
git add vercel.json
git commit -m "Restore UAT configuration"
```

---

### Method 2: Using Git Branches

Maintain separate branches with different `vercel.json`:

- `sit` branch → Uses `vercel.uat.json` (points to UAT backend)
- `main` branch → Uses `vercel.prd.json` (points to PRD backend)

#### Setup (one-time)
```bash
# On sit branch
git checkout sit
cp vercel.uat.json vercel.json
git add vercel.json
git commit -m "Configure for UAT"
git push origin sit

# On main branch
git checkout main
cp vercel.prd.json vercel.json
git add vercel.json
git commit -m "Configure for production"
git push origin main
```

#### Deploy
```bash
# UAT deployment
git checkout sit
git push origin sit

# Production deployment
git checkout main
git merge sit  # Merge latest changes from UAT
# Don't commit vercel.json changes (keep PRD config)
git checkout main -- vercel.json
git push origin main
```

---

## Environment Variables (.env)

The `NEXT_PUBLIC_API_URL` should remain **empty** for all Vercel deployments.

### .env Configuration

```bash
# Default (leave empty for all Vercel deployments)
NEXT_PUBLIC_API_URL=

# Only uncomment for local development direct connection:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Why Leave Empty?

When `NEXT_PUBLIC_API_URL` is empty:
- Frontend makes requests to relative paths like `/api/products`
- Vercel intercepts these requests using `vercel.json` rewrites
- Requests are proxied to the appropriate Railway backend

This approach:
- ✅ Keeps configuration in one place (`vercel.json`)
- ✅ No need to rebuild frontend for different environments
- ✅ Works seamlessly with Vercel's edge network
- ✅ Avoids CORS issues

---

## Vercel.json Structure

### UAT Configuration (vercel.uat.json)
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://pricehawk-uat.up.railway.app/api/:path*"
    }
  ]
}
```

### Production Configuration (vercel.prd.json)
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://pricehawk-production-d139.up.railway.app/api/:path*"
    }
  ]
}
```

---

## Local Development

For local development, use `next.config.js` proxy (already configured):

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Start frontend (in another terminal)
cd ui
npm run dev
```

The frontend will proxy `/api/*` requests to `http://localhost:8000` via `next.config.js`.

---

## Troubleshooting

### 405 Method Not Allowed Error
- **Cause**: `vercel.json` is missing or points to wrong backend
- **Fix**: Ensure `vercel.json` exists and has correct Railway URL

### CORS Errors
- **Cause**: `NEXT_PUBLIC_API_URL` is set to direct Railway URL
- **Fix**: Set `NEXT_PUBLIC_API_URL=` (empty) and use `vercel.json` rewrites

### API requests fail in production
- **Cause**: `vercel.json` not deployed or incorrect backend URL
- **Fix**: Check Vercel deployment logs, ensure `vercel.json` is in root of `ui/` directory

---

## Quick Reference

| Environment | Branch | vercel.json Points To | Deploy Command |
|-------------|--------|-----------------------|----------------|
| Local | any | N/A (uses next.config.js) | `npm run dev` |
| UAT | sit | pricehawk-uat.up.railway.app | `git push origin sit` |
| Production | main | pricehawk-production-d139.up.railway.app | `git push origin main` |

---

## Current Configuration

As of 2026-01-28:
- ✅ `vercel.json` → Points to **UAT** backend
- ✅ `vercel.uat.json` → UAT configuration
- ✅ `vercel.prd.json` → Production configuration
- ✅ `.env` → `NEXT_PUBLIC_API_URL` is empty (correct for Vercel)
