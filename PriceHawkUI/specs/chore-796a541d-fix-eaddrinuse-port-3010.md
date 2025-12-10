# Chore: Fix EADDRINUSE Error - Port 3010 Conflict

## Metadata
adw_id: `796a541d`
prompt: `Fix EADDRINUSE error - port 3010 is already in use when running npm run dev. Find and kill the process using port 3010, or configure the Next.js app to use a different available port.`

## Chore Description
When running `npm run dev`, the application fails to start with an EADDRINUSE error because port 3010 is already in use by another process. This chore will:
1. Identify and kill the process currently using port 3010
2. Alternatively, configure the Next.js application to use a different available port (default 3000 or custom)
3. Document the port configuration for future reference

## Relevant Files
- `package.json` - Contains the dev script configuration (`next dev`)
- `README.md` - Documentation showing port 3000 as the default port
- `.env.local` - (New file) To configure custom port via environment variable

### New Files
- `.env.local` - Environment configuration file for local development (optional, if changing default port)
- `.env.example` - Example environment file to document available configuration options

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Identify Process Using Port 3010
- Run `lsof -ti:3010` to find the process ID (PID) using port 3010
- Run `ps -p <PID>` to identify what application is running
- Document the process information for reference

### 2. Kill Process on Port 3010
- Run `kill -9 <PID>` to forcefully terminate the process using port 3010
- Verify the port is now free by running `lsof -ti:3010` again (should return nothing)
- This is the immediate solution if the process is an orphaned/stuck development server

### 3. Configure Next.js Port (Alternative/Preventive Solution)
- By default, Next.js uses port 3000, but the README shows `http://localhost:3000/products`
- The error mentions port 3010, suggesting a custom configuration or environment variable exists
- Update `package.json` dev script to explicitly use port 3000: `"dev": "next dev -p 3000"`
- Or create `.env.local` with `PORT=3000` to configure via environment variable

### 4. Update Documentation
- Verify README.md correctly shows port 3000 (currently does at line 49)
- If using environment variables, create `.env.example` with:
  ```
  # Server Port (default: 3000)
  PORT=3000
  ```
- Document the port configuration approach in README.md under "Getting Started"

### 5. Validate the Fix
- Run `npm run dev` and verify the application starts successfully
- Confirm the application is accessible at the configured port
- Check that no EADDRINUSE errors occur
- Verify the URL shown in terminal matches the configured port

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Kill process on port 3010 (if still running)
lsof -ti:3010 && kill -9 $(lsof -ti:3010) || echo "Port 3010 is already free"

# Verify port 3010 is free
lsof -ti:3010 || echo "✓ Port 3010 is available"

# Start development server
npm run dev
# Expected output: Server running on http://localhost:3000 (or configured port)
# Expected: No EADDRINUSE errors

# Test the application (in another terminal)
curl http://localhost:3000/products -I
# Expected: HTTP 200 response
```

## Notes
- The README documentation shows port 3000 as the default, but the error mentions port 3010, suggesting either:
  1. An environment variable (PORT=3010) exists somewhere
  2. A previous dev server is still running on port 3010
  3. The `-p 3010` flag was used in a custom script
- The immediate fix is to kill the process on port 3010
- The preventive fix is to explicitly configure the port in package.json or .env.local
- Next.js respects the PORT environment variable if set
- Using `-p` flag in package.json dev script takes precedence over PORT env var
