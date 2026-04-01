# Backend User Session Logging - Implementation

## ✅ What Was Added

Comprehensive backend logging to track user sessions, login/logout times, and page activity.

## 📁 Files Modified

### Backend:
1. **`backend/main.py`**
   - Added logging configuration
   - Enhanced login endpoint with detailed logging
   - Enhanced logout endpoint with session duration tracking
   - Added page unload tracking endpoint
   - Added active sessions monitoring endpoint
   - Added session activity tracking in authentication

### Frontend:
1. **`ui/src/components/PageUnloadTracker.tsx`** (New)
   - Tracks when users close browser/tab
   - Uses `sendBeacon` for reliable tracking
   
2. **`ui/src/app/layout.tsx`**
   - Added PageUnloadTracker component

## 📊 What Gets Logged

### 1. Login Events
```
LOGIN | User: admin | IP: 192.168.1.1 | Time: 2026-01-14T10:30:00 | User-Agent: Mozilla/5.0...
```

**Tracked Data:**
- Username
- IP Address
- Login timestamp
- User-Agent (browser/device info)

### 2. Failed Login Attempts
```
WARNING: Failed login attempt for username: admin from IP: 192.168.1.1
```

**Tracked Data:**
- Username (attempted)
- IP Address
- Warning level for security monitoring

### 3. Logout Events
```
LOGOUT | User: admin | IP: 192.168.1.1 | Login: 2026-01-14T10:30:00 | Logout: 2026-01-14T10:45:00 | Duration: 900 seconds (15.0 minutes)
```

**Tracked Data:**
- Username
- IP Address
- Login time
- Logout time
- Session duration (seconds and minutes)

### 4. Page Unload Events (Browser Close)
```
PAGE_UNLOAD | User: admin | IP: 192.168.1.1 | Login: 2026-01-14T10:30:00 | Unload: 2026-01-14T10:45:00 | Duration: 900 seconds (15.0 minutes)
```

**Tracked Data:**
- Username
- IP Address
- Login time
- Page unload time
- Total session duration

**Note:** This tracks when users close the browser/tab without explicitly logging out.

## 📝 Log File Location

All session logs are written to: **`backend/user_sessions.log`**

Also displayed in: **Console output** (Railway logs)

## 🔍 Viewing Logs

### On Railway (Production):
1. Go to Railway dashboard
2. Select your backend service
3. Click **Deployments** → Select active deployment
4. View logs in real-time

### Local Development:
```bash
cd backend
tail -f user_sessions.log
```

### Search Logs:
```bash
# Find all logins by specific user
grep "LOGIN | User: admin" user_sessions.log

# Find all logouts
grep "LOGOUT" user_sessions.log

# Find sessions longer than 30 minutes
grep "Duration: [3-9][0-9][0-9][0-9]" user_sessions.log

# Find all activity for specific IP
grep "IP: 192.168.1.1" user_sessions.log
```

## 📊 New API Endpoints

### 1. Track Page Unload
```http
POST /api/auth/page-unload
Authorization: Bearer {token}
```

**Purpose:** Called automatically when user closes browser/tab

**Response:**
```json
{
  "message": "Page unload tracked"
}
```

### 2. Get Active Sessions
```http
GET /api/auth/sessions
Authorization: Bearer {token}
```

**Purpose:** View all currently active user sessions (admin monitoring)

**Response:**
```json
{
  "active_sessions": [
    {
      "username": "admin",
      "login_time": "2026-01-14T10:30:00",
      "last_activity": "2026-01-14T10:35:00",
      "session_duration_seconds": 300,
      "session_duration_minutes": 5.0,
      "idle_time_seconds": 120,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "total_active": 1
}
```

## 🎯 Session Tracking Features

### Automatic Activity Tracking
Every API request updates the user's `last_activity` timestamp, so you can track:
- When users are idle
- How long they're actively using the app
- Total session duration

### Session Data Stored (In-Memory):
```python
{
  "user": {"user_id": 1, "username": "admin"},
  "expires": datetime(2026, 01, 21, 10, 30, 0),
  "login_time": datetime(2026, 01, 14, 10, 30, 0),
  "last_activity": datetime(2026, 01, 14, 10, 35, 0),
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

## 📈 Use Cases

### 1. Security Monitoring
- Track failed login attempts by IP
- Identify suspicious login patterns
- Monitor unusual session durations

### 2. User Activity Analysis
- See when users are most active
- Track average session duration
- Identify power users vs casual users

### 3. Support & Debugging
- Verify user login issues
- Check session duration complaints
- Track connection problems by IP/device

### 4. Business Metrics
- Peak usage hours
- Average session length
- User engagement patterns

## 🔧 Log Format

```
Timestamp - Logger - Level - Message

2026-01-14 10:30:00,123 - __main__ - INFO - LOGIN | User: admin | IP: 192.168.1.1 | Time: 2026-01-14T10:30:00.123456 | User-Agent: Mozilla/5.0...
```

**Components:**
- **Timestamp:** When the event occurred
- **Logger:** Python module name
- **Level:** INFO, WARNING, ERROR
- **Message:** Event details

## 📊 Sample Log Output

```
2026-01-14 10:30:00,123 - __main__ - INFO - LOGIN | User: admin | IP: 192.168.1.1 | Time: 2026-01-14T10:30:00.123456 | User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0
2026-01-14 10:30:15,456 - __main__ - WARNING - Failed login attempt for username: hacker from IP: 203.0.113.1
2026-01-14 10:45:30,789 - __main__ - INFO - PAGE_UNLOAD | User: admin | IP: 192.168.1.1 | Login: 2026-01-14T10:30:00.123456 | Unload: 2026-01-14T10:45:30.789012 | Duration: 930 seconds (15.5 minutes)
2026-01-14 11:00:00,111 - __main__ - INFO - LOGOUT | User: admin | IP: 192.168.1.1 | Login: 2026-01-14T10:30:00.123456 | Logout: 2026-01-14T11:00:00.111222 | Duration: 1800 seconds (30.0 minutes)
```

## ⚠️ Important Notes

### Browser Close Detection
- Uses `sendBeacon` API for reliable tracking
- Works even when page is closing/refreshing
- Tracks both desktop and mobile browser closes
- Falls back to `visibilitychange` for mobile browsers

### Session Persistence
- Page unload does NOT delete the session
- Users can return within 7 days without re-logging
- Only explicit logout or session expiry removes the session

### Log Rotation (Recommended)
For production, add log rotation to prevent file from growing too large:

```python
# Add to main.py logging configuration
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'user_sessions.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## 🚀 Deployment

Changes are ready to deploy:
1. **Backend:** Push to Railway (auto-deploys)
2. **Frontend:** Push to Vercel (auto-deploys)
3. **Check logs:** Railway dashboard → Backend service → Logs

## 🔍 Testing

### Test Login Tracking:
1. Login to the app
2. Check `backend/user_sessions.log` for LOGIN entry
3. Verify IP and timestamp are correct

### Test Page Unload Tracking:
1. Login to the app
2. Close the browser tab (don't logout)
3. Check logs for PAGE_UNLOAD entry

### Test Logout Tracking:
1. Login to the app
2. Click logout button
3. Check logs for LOGOUT entry with session duration

### Test Active Sessions:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/auth/sessions
```

---

**Status:** ✅ All implemented and ready for deployment!
