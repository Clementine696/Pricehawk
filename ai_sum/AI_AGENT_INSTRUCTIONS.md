# AI Agent Instructions for PriceHawk Project

## 📋 Overview
This document provides guidelines for AI agents (like Claude Code) working on the PriceHawk price comparison platform. Follow these instructions to maintain consistency, quality, and proper documentation.

---

## 🚀 Getting Started (First Steps)

### 1. **Read the Project Summary First**
Before making ANY changes, read the main documentation:
```bash
c:\Users\kanat\Desktop\PriceHawk\_PROD\SUMMARY.md
```

This file contains:
- Architecture overview
- Database schema
- API endpoints
- Frontend pages structure
- Recent changes and features
- Tech stack details

### 2. **Understand the Current Context**
- Check the git branch: `git status`
- Review recent commits: `git log --oneline -10`
- Look for any TODO comments in code
- Check for existing issues or feature requests

### 3. **Explore the Codebase Structure**
```
PriceHawk/_PROD/
├── backend/          # FastAPI + Python
├── ui/              # Next.js + TypeScript
├── database/init/   # SQL schemas
├── seeder/          # Data seeding scripts
└── SUMMARY.md       # Main documentation
```

---

## 🛠️ Development Workflow

### Before Making Changes

1. **Read Before You Write**
   - ALWAYS read files before editing them
   - Never propose changes to code you haven't seen
   - Use the Read tool to understand existing patterns

2. **Plan Complex Tasks**
   - For multi-step tasks, use TodoWrite to create a task list
   - Break down large features into smaller, manageable steps
   - Mark tasks as in_progress → completed as you work

3. **Ask Questions When Unclear**
   - Use AskUserQuestion if requirements are ambiguous
   - Don't make assumptions about design decisions
   - Clarify before implementing, not after

### During Implementation

1. **Follow Existing Patterns**
   - Match the coding style of existing files
   - Use the same component structure (see ui/src/components/)
   - Follow naming conventions already in use

2. **Key Tech Stack Patterns**
   - **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS
   - **Backend**: FastAPI with async/await, SQLAlchemy
   - **Styling**: Tailwind utility classes, avoid inline styles
   - **Icons**: lucide-react library
   - **State**: React hooks (useState, useEffect)

3. **Common Component Patterns**
   ```typescript
   // Tailwind color scheme
   Primary: cyan-500, cyan-600
   Success: emerald-500, emerald-600, green-500
   Warning: amber-500, amber-600, yellow-500
   Danger: red-500, red-600
   Neutral: gray-50 to gray-900

   // Button styles
   Primary: bg-cyan-500 hover:bg-cyan-600 text-white
   Success: bg-emerald-500 hover:bg-emerald-600 text-white
   Danger: bg-red-500 hover:bg-red-600 text-white

   // Card/Container
   bg-white rounded-lg border border-gray-200 shadow-sm
   ```

4. **Database Changes**
   - Always check existing schema in `database/init/01_schema.sql`
   - Create migration scripts for schema changes
   - Update SUMMARY.md with new tables/columns

5. **API Changes**
   - Follow RESTful conventions
   - Add proper error handling
   - Update SUMMARY.md API endpoints section
   - Test with both success and error cases

### Code Quality Standards

1. **Security**
   - NO SQL injection vulnerabilities
   - NO XSS vulnerabilities
   - Validate user input
   - Use parameterized queries
   - Sanitize data before rendering

2. **Error Handling**
   ```typescript
   // Frontend
   try {
     const response = await apiFetch('/api/endpoint');
     if (!response.ok) throw new Error('Failed to fetch');
     const data = await response.json();
   } catch (error) {
     console.error('Error:', error);
     // Show user-friendly error message
   }
   ```

   ```python
   # Backend
   from fastapi import HTTPException

   try:
       # operation
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
   ```

3. **TypeScript Types**
   - Define interfaces for all data structures
   - Use strict typing, avoid `any` when possible
   - Keep interfaces near the components that use them

4. **Performance**
   - Use pagination for large datasets
   - Implement lazy loading where appropriate
   - Optimize database queries (avoid N+1 queries)
   - Use indexes for frequently queried columns

---

## 📝 Documentation Requirements

### 1. **Update SUMMARY.md After Major Changes**

When you complete a significant feature or fix, update the SUMMARY.md file with:
- What was changed
- File paths with line numbers (e.g., `[page.tsx:138-145](path/to/file.tsx#L138-L145)`)
- Code snippets for important changes
- Why the change was made

**Example entry:**
```markdown
### Feature Name (Date)
Description of what was implemented.

**Files Changed:**
- [component.tsx:50-100](ui/src/components/component.tsx#L50-L100)
  - Added new functionality
  - Updated styling to match design

**Technical Details:**
- Uses X library for Y
- Implements Z pattern
```

### 2. **Create a Session Log**

For each work session, create a log file:
```bash
c:\Users\kanat\Desktop\PriceHawk\_PROD\logs\session_YYYY-MM-DD.md
```

**Log Format:**
```markdown
# Session Log - YYYY-MM-DD

## Tasks Completed
1. [✓] Task description
   - File: path/to/file.tsx
   - Changes: Brief description

2. [✓] Another task
   - File: path/to/file.py
   - Changes: Brief description

## Issues Encountered
- Issue description and resolution

## Files Modified
- path/to/file1.tsx
- path/to/file2.py

## Next Steps / TODO
- [ ] Pending task 1
- [ ] Pending task 2

## Notes
Any important observations or decisions made.
```

### 3. **Code Comments**
- Add comments for complex logic
- Explain "why" not "what"
- Document workarounds with reason
- Mark TODOs with context

```typescript
// Good comment
// Using setTimeout to avoid race condition with state updates
// TODO: Replace with useEffect cleanup when React 19 is stable

// Bad comment
// Set timeout to 300ms
```

---

## 🔍 Common Tasks & Patterns

### Adding a New Page

1. Create page file: `ui/src/app/[page-name]/page.tsx`
2. Use MainLayout wrapper
3. Add to sidebar navigation: `ui/src/components/layout/Sidebar.tsx`
4. Add API endpoint if needed: `backend/main.py`
5. Update SUMMARY.md

### Adding a Database Table

1. Add schema to `database/init/01_schema.sql`
2. Create model in backend if using ORM
3. Add API endpoints for CRUD operations
4. Create frontend components
5. Document in SUMMARY.md under "Database Schema"

### Creating a Modal/Dialog

```typescript
// Use state to control visibility
const [showModal, setShowModal] = useState(false);

// Modal structure
{showModal && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
      {/* Modal content */}
    </div>
  </div>
)}
```

### Excel Export

- Use existing pattern from products page
- Backend: openpyxl library
- Include hyperlinks for URLs
- Add timestamp to filename
- Return as StreamingResponse

---

## ⚠️ Things to Avoid

1. **Don't Over-Engineer**
   - Keep solutions simple and focused
   - Don't add features that weren't requested
   - Don't refactor unrelated code
   - Avoid premature abstractions

2. **Don't Break Existing Features**
   - Test your changes don't break other pages
   - Check console for errors after changes
   - Verify API responses match frontend expectations

3. **Don't Ignore Existing Conventions**
   - Don't mix styling approaches (stick to Tailwind)
   - Don't introduce new libraries without justification
   - Don't change naming patterns

4. **Don't Skip Documentation**
   - Every major change needs SUMMARY.md update
   - Create session logs
   - Update comments in code

---

## 🧪 Testing Checklist

Before marking a task complete:

- [ ] Code compiles/runs without errors
- [ ] No console errors in browser
- [ ] API returns expected response format
- [ ] UI matches requested design
- [ ] Responsive on mobile (if UI change)
- [ ] Error cases handled gracefully
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated
- [ ] Session log created/updated

---

## 📊 Project-Specific Context

### Retailer Information
The platform tracks 6 retailers:
- **Thai Watsadu** (twd) - Base retailer for comparisons
- HomePro (hp)
- Do Home (dh) - Note: Space in database name
- Boonthavorn (btv)
- Global House (gbh)
- MegaHome (mgh) - Note: "Mega Home" in database

### Name Aliasing
Some retailers have name variations between frontend/backend. Check SUMMARY.md for alias mappings.

### Authentication
- Session-based with 7-day expiry
- Bearer token in localStorage (primary)
- HTTP-only cookie (fallback)
- All API calls need authentication

### Color Scheme
- Primary: Cyan (cyan-500, cyan-600)
- Success: Emerald/Green
- Warning: Amber/Yellow
- Danger: Red
- Neutral: Gray scale

---

## 🎯 Success Criteria

A well-executed task should:

1. ✅ Solve the user's request completely
2. ✅ Follow existing code patterns
3. ✅ Include proper error handling
4. ✅ Be documented (SUMMARY.md + session log)
5. ✅ Have no security issues
6. ✅ Work on all screen sizes (if UI)
7. ✅ Not break existing features

---

## 💡 Tips for Efficiency

1. **Read Multiple Files in Parallel**
   - When you need to check several files, read them all at once
   - Use parallel tool calls

2. **Use Search Tools Effectively**
   - Glob for finding files by pattern
   - Grep for searching code content
   - Explore agent for complex codebase questions

3. **Batch Related Changes**
   - Group related edits together
   - Update documentation in same session

4. **Save Progress Regularly**
   - Update session log as you work
   - Commit logical units of work

---

## 📚 Quick Reference

### Important Files
```
SUMMARY.md                          # Main documentation
AI_AGENT_INSTRUCTIONS.md           # This file
backend/main.py                     # API endpoints
ui/src/app/layout.tsx              # Root layout
ui/src/components/layout/          # Layout components
database/init/01_schema.sql        # Database schema
```

### Common Commands
```bash
# Frontend
cd ui
npm run dev                 # Start dev server
npm run build              # Build for production

# Backend
cd backend
uvicorn main:app --reload  # Start dev server
python services/price_updater.py  # Update prices

# Git
git status                 # Check status
git log --oneline -10     # Recent commits
```

---

## 🔄 Session Workflow Summary

```
1. Read SUMMARY.md
   ↓
2. Understand the task
   ↓
3. Create TodoWrite plan (if complex)
   ↓
4. Read relevant files
   ↓
5. Make changes following patterns
   ↓
6. Test changes
   ↓
7. Update SUMMARY.md (if major feature)
   ↓
8. Create/update session log
   ↓
9. Mark todos complete
```

---

## 📞 When in Doubt

1. Check SUMMARY.md first
2. Look for similar existing code
3. Ask the user for clarification
4. Keep changes minimal and focused
5. Document your decisions

---

**Remember**: The goal is to help the user efficiently while maintaining code quality and proper documentation. Always prioritize understanding before implementing.
