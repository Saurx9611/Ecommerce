---
description: Use this when you paste an error log and need the agent to find and fix the root cause without breaking other things.
---

I have encountered a bug or error.
1. **Analyze:** Read the error trace I provide and search the codebase for the files mentioned.
2. **Diagnose:** Identify the root cause (e.g., race condition, missing import, async/await mismatch, CORS issue).
3. **Surgical Fix:** Provide the exact, minimal code change required to fix the issue. Do NOT refactor the whole file. Show me the specific lines to replace.