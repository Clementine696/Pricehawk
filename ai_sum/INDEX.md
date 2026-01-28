# AI Documentation Index

Quick reference guide for navigating PriceHawk AI documentation.

## 🎯 Start Here

### For New AI Agents
1. Read [SUMMARY.md](./SUMMARY.md) - Complete project overview
2. Read [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md) - Development guidelines
3. Check [sessions/](./sessions/) - Review recent work

### For Continuing Work
1. Check latest session log in [sessions/](./sessions/)
2. Review [SUMMARY.md](./SUMMARY.md) for current state
3. Follow [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md) workflow

---

## 📚 Documentation Files

### Core Documentation

| File | Purpose | Read When |
|------|---------|-----------|
| [SUMMARY.md](./SUMMARY.md) | Complete project documentation | Every session (first) |
| [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md) | Development guidelines & patterns | Before implementing |
| [README.md](./README.md) | Folder overview | Getting oriented |
| [INDEX.md](./INDEX.md) | This file - quick reference | Finding documentation |

### Session Logs

| Date | Key Changes | Files Modified |
|------|-------------|----------------|
| [2026-01-28](./sessions/2026-01-28.md) | Import modal redesign, sidebar icon, search enhancement | watchlist-sku/page.tsx, Sidebar.tsx, comparison/page.tsx |

---

## 🗂️ Folder Structure

```
ai_sum/
├── INDEX.md                     # ← Quick reference (this file)
├── README.md                    # Folder overview
├── SUMMARY.md                   # ← START HERE - Main project docs
├── AI_AGENT_INSTRUCTIONS.md    # ← Development guidelines
└── sessions/                    # Session logs by date
    └── 2026-01-28.md           # Latest session
```

---

## 🔍 Finding Information

### "How do I...?"
→ Check [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md)
- Section: "Common Tasks & Patterns"

### "What is the current state of...?"
→ Check [SUMMARY.md](./SUMMARY.md)
- Database schema
- API endpoints
- Features implemented

### "What was done recently?"
→ Check [sessions/](./sessions/)
- Latest session log
- Recent changes

### "What are the coding standards?"
→ Check [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md)
- Section: "Code Quality Standards"
- Section: "Common Component Patterns"

---

## ⚡ Quick References

### Tech Stack
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Backend: FastAPI + Python 3.11
- Database: PostgreSQL 15 (Neon)
- Icons: lucide-react

### Color Scheme
- Primary: cyan-500, cyan-600
- Success: emerald-500, emerald-600
- Warning: amber-500, amber-600
- Danger: red-500, red-600

### Important Files
```
backend/main.py                 # API endpoints
ui/src/app/layout.tsx          # Root layout
ui/src/components/layout/       # Layout components
database/init/01_schema.sql    # Database schema
```

### Common Commands
```bash
# Frontend
cd ui && npm run dev

# Backend
cd backend && uvicorn main:app --reload

# Git
git status
git log --oneline -10
```

---

## 📝 Creating New Session Logs

**Template**: Copy structure from [sessions/2026-01-28.md](./sessions/2026-01-28.md)

**Include:**
- Session overview
- Tasks completed with file references
- Code snippets for important changes
- Decisions made and reasoning
- Files modified summary
- Next steps

**Save as**: `sessions/YYYY-MM-DD.md`

---

## 🎓 Best Practices

1. ✅ Always read SUMMARY.md first
2. ✅ Follow patterns in AI_AGENT_INSTRUCTIONS.md
3. ✅ Create session log for every work session
4. ✅ Update SUMMARY.md for major features
5. ✅ Include file paths and line numbers in logs
6. ✅ Document decisions and reasoning

---

## 🔗 External References

- Project Root: `c:\Users\kanat\Desktop\PriceHawk\_PROD\`
- Frontend: `ui/src/`
- Backend: `backend/`
- Database: `database/init/`

---

**Last Updated**: 2026-01-28
