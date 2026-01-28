# AI Agent Quick Start Guide

**Welcome! This is your 5-minute guide to getting started on PriceHawk.**

---

## ⚡ First 5 Minutes

### 1. Read This Section (1 min)
You're an AI agent working on PriceHawk, a Thai price comparison platform.

**Your mission**: Help implement features, fix bugs, and maintain code quality.

### 2. Understand the Project (2 min)
- **What**: Price comparison for 6 Thai home improvement retailers
- **Tech**: Next.js 14 (frontend) + FastAPI (backend) + PostgreSQL
- **Colors**: Cyan (primary), Emerald (success), Red (danger)
- **Icons**: lucide-react library

### 3. Read Essential Docs (2 min)
**Must read**: [SUMMARY.md](./SUMMARY.md) - Skim through these sections:
- Architecture Overview
- Project Structure
- Database Schema
- Recent Changes (bottom of file)

---

## 🎯 Before You Code

### Checklist
- [ ] Read [SUMMARY.md](./SUMMARY.md) (at least skim it)
- [ ] Check latest session log: [sessions/](./sessions/)
- [ ] Understand the user's request
- [ ] Plan your approach (use TodoWrite for complex tasks)

### Important Files to Know
```
ai_sum/SUMMARY.md                    # ← Main docs (read this!)
ai_sum/AI_AGENT_INSTRUCTIONS.md     # Development guidelines
backend/main.py                      # API endpoints
ui/src/app/                         # All pages
ui/src/components/layout/Sidebar.tsx # Navigation
database/init/01_schema.sql         # Database schema
```

---

## 💻 Common Tasks

### Adding a New Page
1. Create: `ui/src/app/[page-name]/page.tsx`
2. Use: `MainLayout` wrapper
3. Add to: `Sidebar.tsx` navigation
4. Create API endpoint if needed in `backend/main.py`

### Modifying UI
- **Always read file first** with Read tool
- Use Tailwind classes (no inline styles)
- Follow color scheme: cyan-500, emerald-500, red-500
- Match existing component patterns

### Creating API Endpoint
```python
# backend/main.py
@app.get("/api/your-endpoint")
async def your_endpoint(db: Session = Depends(get_db)):
    # Your code
    return {"status": "success"}
```

### Updating Database
1. Modify: `database/init/01_schema.sql`
2. Update backend queries in `main.py`
3. Document in SUMMARY.md

---

## 📋 Workflow

```
1. Read SUMMARY.md
   ↓
2. Understand task
   ↓
3. Read relevant files (never edit without reading!)
   ↓
4. Make changes (follow existing patterns)
   ↓
5. Test (no console errors, works as expected)
   ↓
6. Document (create session log, update SUMMARY.md if major)
```

---

## 🚫 Don't Do This

- ❌ Edit files you haven't read
- ❌ Add features not requested
- ❌ Change code style/patterns
- ❌ Skip documentation
- ❌ Ignore security (no SQL injection, XSS, etc.)
- ❌ Mix styling approaches (stick to Tailwind)

---

## ✅ Do This

- ✅ Read files before editing
- ✅ Follow existing patterns
- ✅ Use Tailwind utility classes
- ✅ Handle errors gracefully
- ✅ Create session logs
- ✅ Ask questions if unclear (AskUserQuestion tool)
- ✅ Test your changes

---

## 🎨 Code Patterns

### Frontend Component
```typescript
'use client';

import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';

export default function YourPage() {
  const [data, setData] = useState([]);

  return (
    <MainLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Your Page
        </h1>
        {/* Content */}
      </div>
    </MainLayout>
  );
}
```

### Backend Endpoint
```python
from fastapi import HTTPException
from database import get_db

@app.get("/api/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    try:
        result = db.query(Model).all()
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Tailwind Button
```typescript
// Primary button
<button className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg">
  Click Me
</button>

// Success button
<button className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg">
  Save
</button>

// Danger button
<button className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg">
  Delete
</button>
```

---

## 📝 After You Finish

### Documentation Checklist
- [ ] Create session log: `ai_sum/sessions/YYYY-MM-DD.md` (use TEMPLATE.md)
- [ ] Update SUMMARY.md if major feature added
- [ ] Include file paths with line numbers
- [ ] Document decisions made

### Session Log Format
```markdown
# Session Log - 2026-01-28

## Tasks Completed
1. [✓] Task description
   - File: path/to/file.tsx:100-150
   - Changes: What was changed

## Files Modified
- path/to/file1.tsx
- path/to/file2.py

## Next Steps
- [ ] Pending task
```

---

## 🔍 Quick Reference

### Colors
- Primary: `cyan-500`, `cyan-600`
- Success: `emerald-500`, `emerald-600`
- Warning: `amber-500`, `amber-600`
- Danger: `red-500`, `red-600`
- Neutral: `gray-50` to `gray-900`

### Retailers (6 total)
- Thai Watsadu (twd) - Base retailer
- HomePro (hp)
- Do Home (dh)
- Boonthavorn (btv)
- Global House (gbh)
- MegaHome (mgh)

### Common Imports
```typescript
// Frontend
import { MainLayout } from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { Search, Check, X } from 'lucide-react';

// Backend
from fastapi import Depends, HTTPException
from database import get_db, Session
```

---

## 🆘 Need Help?

### "Where is...?"
- API endpoints: `backend/main.py`
- Pages: `ui/src/app/[page-name]/page.tsx`
- Database: `database/init/01_schema.sql`
- Navigation: `ui/src/components/layout/Sidebar.tsx`

### "How do I...?"
- Check [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md) section "Common Tasks & Patterns"

### "What changed recently?"
- Check [sessions/](./sessions/) for latest session logs
- Bottom of [SUMMARY.md](./SUMMARY.md) has "Recent Changes"

### "What's the current state?"
- Read [SUMMARY.md](./SUMMARY.md) - it's the source of truth

---

## 🎓 Learn More

| Document | When to Read |
|----------|--------------|
| [SUMMARY.md](./SUMMARY.md) | **Start here** - Every session |
| [AI_AGENT_INSTRUCTIONS.md](./AI_AGENT_INSTRUCTIONS.md) | Before implementing |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | When navigating codebase |
| [INDEX.md](./INDEX.md) | Finding specific info |
| [sessions/](./sessions/) | Understanding recent work |

---

## ⏱️ Time Investment

- **Quick task** (< 10 min): Skim SUMMARY.md, check latest session
- **Medium task** (30 min): Read SUMMARY.md, read AI_AGENT_INSTRUCTIONS.md patterns section
- **Major feature** (> 1 hour): Read all docs, plan with TodoWrite, create detailed session log

---

## 🚀 Ready to Start?

1. Read [SUMMARY.md](./SUMMARY.md) (10 min)
2. Check [latest session](./sessions/)
3. Ask user to clarify if needed
4. Start coding (following patterns)
5. Document your work

**Remember**: Read before you write, follow existing patterns, and document everything!

---

**Good luck! 🎉**
