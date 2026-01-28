# PriceHawk - Price Comparison Platform

A comprehensive price comparison platform for Thai home improvement retailers that tracks and compares product prices across multiple stores.

---

## 📚 Documentation

### For AI Agents (Claude Code, etc.)
**→ Start here: [ai_sum/](./ai_sum/)** - Complete AI documentation hub

Quick links:
- **[SUMMARY.md](./ai_sum/SUMMARY.md)** - Full project documentation (architecture, features, schemas)
- **[AI_AGENT_INSTRUCTIONS.md](./ai_sum/AI_AGENT_INSTRUCTIONS.md)** - Development guidelines
- **[INDEX.md](./ai_sum/INDEX.md)** - Quick reference guide
- **[PROJECT_STRUCTURE.md](./ai_sum/PROJECT_STRUCTURE.md)** - Visual codebase guide
- **[sessions/](./ai_sum/sessions/)** - Daily session logs

### For Developers
See [ai_sum/SUMMARY.md](./ai_sum/SUMMARY.md) for complete technical documentation.

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (Frontend)
- Python 3.11+ (Backend)
- PostgreSQL 15+ (Database)

### Local Development

**Frontend:**
```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
export DATABASE_URL="postgresql://..."
uvicorn main:app --reload --port 8000
```

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   Database      │
│   (Vercel)      │     │   (Railway)     │     │   (Neon)        │
│   Next.js 14    │     │   FastAPI       │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │    Scraper      │
                        │  (Playwright +  │
                        │   crawl4ai)     │
                        └─────────────────┘
```

---

## 📁 Project Structure

```
PriceHawk/_PROD/
├── ai_sum/              # ← AI Agent Documentation Hub
│   ├── SUMMARY.md       # Complete project docs
│   ├── AI_AGENT_INSTRUCTIONS.md
│   └── sessions/        # Session logs
│
├── backend/             # FastAPI backend
├── ui/                  # Next.js frontend
├── database/init/       # SQL schemas
└── seeder/             # Data seeding scripts
```

---

## 🔑 Key Features

- **Multi-Retailer Price Tracking** - Track 6 major Thai retailers
- **Automated Scraping** - Daily price updates using Playwright
- **Product Matching** - AI-assisted product matching across retailers
- **Watchlists** - Category and SKU-based watchlists
- **Excel Import/Export** - Bulk operations with Excel files
- **Price History** - Historical price tracking with charts
- **Manual Comparison** - Wizard for manual product matching

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL 15 (Neon) |
| Scraping | Playwright, crawl4ai |
| Hosting | Vercel (Frontend), Railway (Backend) |

---

## 📖 Documentation Index

| Document | Purpose |
|----------|---------|
| [SUMMARY.md](./ai_sum/SUMMARY.md) | Main documentation - read this first |
| [AI_AGENT_INSTRUCTIONS.md](./ai_sum/AI_AGENT_INSTRUCTIONS.md) | Development guidelines for AI agents |
| [INDEX.md](./ai_sum/INDEX.md) | Quick reference guide |
| [PROJECT_STRUCTURE.md](./ai_sum/PROJECT_STRUCTURE.md) | Visual codebase structure |
| [sessions/](./ai_sum/sessions/) | Daily session logs |

---

## 🚢 Deployment

### Frontend (Vercel)
- Automatic deployment from Git
- Environment: `NEXT_PUBLIC_API_URL`

### Backend (Railway)
- Uses nixpacks for building
- Environment: `DATABASE_URL`, `CORS_ORIGINS`

### Database (Neon)
- Serverless PostgreSQL
- Connection via `DATABASE_URL`

---

## 🤖 For AI Agents

**New to this project?**
1. Read [ai_sum/SUMMARY.md](./ai_sum/SUMMARY.md) first
2. Follow guidelines in [ai_sum/AI_AGENT_INSTRUCTIONS.md](./ai_sum/AI_AGENT_INSTRUCTIONS.md)
3. Check recent work in [ai_sum/sessions/](./ai_sum/sessions/)

**Working on a task?**
- Create session log: `ai_sum/sessions/YYYY-MM-DD.md`
- Update [ai_sum/SUMMARY.md](./ai_sum/SUMMARY.md) for major features
- Follow coding patterns in the instructions

---

## 📞 Support

- Issues: Create issue in project repository
- Documentation: See [ai_sum/](./ai_sum/)

---

**Last Updated**: 2026-01-28
