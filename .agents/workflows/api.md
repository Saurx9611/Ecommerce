---
description: Use this when you strictly want to add a new backend route (like a new POST or GET request) without touching the frontend yet.
---

I need a new FastAPI endpoint.
1. **Schema Check:** Check `app/models` to understand the current database structure.
2. **Pydantic Setup:** Generate the necessary request/response Pydantic schemas.
3. **Router Creation:** Write the async FastAPI route function. Ensure proper dependency injection for the database (`AsyncSession`) and Redis cache if needed.
4. **Error Handling:** Include proper HTTP exceptions (404, 400, etc.).
Output the exact file paths and code blocks for the backend changes only in a clear, copy-pasteable format.