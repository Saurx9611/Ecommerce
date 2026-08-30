---
description: Use this when you want to add a completely new feature that touches the database, backend, and frontend.
---

I want to build a new feature. Follow this strict sequence:
1. **Discovery:** Search the codebase to locate the relevant SQLAlchemy models, FastAPI routers, and Next.js components.
2. **Architecture Plan:** Output a brief bulleted plan detailing: 
   - Database schema changes (Alembic/Models)
   - Backend API updates (FastAPI)
   - Frontend UI integrations (Next.js)
3. **Pause:** Stop and ask me to approve the plan.
4. **Execution:** Once I approve, execute the plan in atomic, step-by-step file edits. Provide the backend code first, wait for confirmation, then provide the frontend code.