---
description: Upgrades UI with Shadcn-like design and Framer Motion animations without needing external UI libraries.
---

I want to upgrade the UI and animations of this component/page. Follow this strict sequence:
1. **Analyze:** Read the specified file. Identify data-fetching logic and state. You MUST preserve all backend API connections and idempotency logic.
2. **Design as Shadcn:** You will act as a Shadcn-UI generator. I do not have the Shadcn CLI installed. When you need a component (like a Card, Badge, or Toast), write the raw Tailwind HTML/React from scratch to perfectly mimic the Shadcn aesthetic (clean borders, subtle rounded corners, slate/gray color palettes, and glassmorphism).
3. **Animate with Framer Motion:** Propose specific `motion` animations (e.g., `initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}`). Prioritize spring physics over linear tweens.
4. **Plan:** Output a brief bulleted list of the visual changes and animations you are going to inject.
5. **Pause:** Wait for my approval.
6. **Execution:** Apply the changes surgically. Ensure `import { motion } from "motion/react"` is correctly placed for Next.js App Router Client Components.