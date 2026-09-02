# FIXLINK PROJECT DIRECTIVES & GUARDRAILS
**Project:** FixLink (MIT-WPU Digital Twin Infrastructure Tracker)  
**Objective:** Maintain 95+ Lighthouse scores, zero technical debt, pristine dark mode compatibility, and bulletproof database lifecycles.

Any AI Agent or Developer working on this codebase MUST adhere strictly to the following protocols before committing changes.

---

## 1. PERFORMANCE & LIGHTHOUSE STRICT STANDARDS
*   **Core Web Vitals:** First Contentful Paint (FCP) must remain under 1.5s. Largest Contentful Paint (LCP) under 2.5s. 
*   **Asset Loading:** NEVER import raster images (`.png`, `.jpg`) for floor plans. Only use inline `<svg>`. All heavy external libraries or non-critical components must be lazy-loaded or dynamically imported.
*   **Bundle Size:** Do not install new dependencies for tasks that can be solved with vanilla JS or native CSS. 
*   **Analytics & SEO:** Every new page or modal must possess highly semantic HTML structure (`<header>`, `<main>`, `<section>`, `<article>`). Button elements must have descriptive `aria-labels` (e.g., `aria-label="Submit ticket for Room VY103"`).

---

## 2. DIGITAL TWIN (SVG) ARCHITECTURE RULES
*   **No Raw Figma Dumps:** NEVER copy-paste raw Figma SVG exports directly into the codebase. 
*   **Inline Stripping:** You MUST strip all hardcoded inline `fill="..."` and `stroke="..."` attributes from the SVG export.
*   **Semantic Classing:** Every interactive room must be assigned the base class `.interactive-room` plus its semantic category (e.g., `.classroom`, `.lab`, `.washroom`, `.conference-room`, `.faculty-room`).
*   **Stacking Context:** The main SVG container must have `pointer-events: none;`. Only the interactive `<path>`, `<rect>`, or `<g>` elements receive `pointer-events: auto;` to prevent overlapping invisible bounding boxes from blocking UI clicks.

---

## 3. UI/UX & DARK MODE INTEGRITY
*   **No Hardcoded Colors:** Never use inline styles for colors (e.g., `style="background: #fff"`). All colors must map to CSS variables or standard utility classes that respond to the `[data-bs-theme="dark"]` or `.dark-mode` toggle.
*   **SVG Glow Aesthetic:** In dark mode, SVGs must never use solid, high-luminosity fills. They must use low-opacity fills (15%) with a solid 2px stroke. Hover states increase fill opacity to 35% without altering the stroke.
*   **Card Depth:** Metadata cards in dark mode must never be flat. They require a translucent background (`rgba(255, 255, 255, 0.05)`) and a faint border (`rgba(255, 255, 255, 0.1)`) to maintain the 2-column grid structure.

---

## 4. DATABASE & BACKEND LIFECYCLE
*   **Initialization Safety:** NEVER execute queries against the database (like searching for the 'Vyas' building) on application startup without first checking if the tables exist using `sqlalchemy.inspect(db.engine).has_table(...)`.
*   **Auto-Seeding:** If tables are missing, the app must automatically run `db.create_all()` inside an `app_context()` and trigger `init_data.py` to seed the fundamental architecture (Vyas, 8 floors, specific lifts) before accepting traffic.
*   **Migration Mandate:** If a new column or table is introduced, do not just update `models.py`. You must provide the migration logic to alter the existing database safely.

---

## 5. CODE CLEANUP & THE "BOY SCOUT" RULE
*   **Zero-Debt Policy:** When refactoring a component or fixing a bug, you are strictly required to scan the surrounding 50 lines of code.
*   **Aggressive Deletion:** You MUST actively delete dead code, unused imports, orphaned CSS classes, duplicate conditional checks, and commented-out legacy code blocks.
*   **Complexity Reduction:** Deeply nested `if/else` statements must be flattened using early returns and guard clauses. Keep functions modular and strictly adhere to DRY (Don't Repeat Yourself).

---

## 6. AUTHENTICATION, CREDENTIAL INTEGRITY & USER SESSION GUARDRAILS
*   **Zero Credential Loss:** NEVER reset, overwrite, or invalidate existing user credentials, passwords, or default administrative accounts during database operations, migrations, route updates, or code refactoring.
*   **Mandatory Core Account Seeding:** Critical system accounts (including default Admin `admin@mitwpu.edu.in`, Developer / Super Admin `om.mahadik@mitwpu.edu.in` with `omni12345`, and Professional `bottlesingh#pro` with `2424242424`) MUST be guaranteed and auto-seeded in `init_db()` upon database startup or cold boot.
*   **Case-Insensitive Email Matching:** All authentication lookups MUST perform case-insensitive comparisons using `func.lower(User.email) == login_input.lower()` so uppercase, mixed-case input, or PostgreSQL strict case collation never causes login failures.
*   **Self-Healing Authentication:** If a recognized administrative or developer account exists without a valid password hash or has not yet been seeded in a freshly created/migrated database, the login handler must gracefully auto-create/auto-repair the credential on verified match without rejecting the user.
*   **Active Session Protection:** Never invalidate, drop, or alter active user sessions across unrelated deployments or schema changes.

---

## 7. THE FINAL RECHECK (PRE-COMMIT VERIFICATION)
Before outputting any code or completing a task, you MUST silently run through this strict verification checklist. If you fail any of these checks, you must rewrite your solution before presenting it.

*   [ ] **The Credential Integrity Check:** Did I ensure all primary accounts (`om.mahadik@mitwpu.edu.in`, `admin@mitwpu.edu.in`, `bottlesingh#pro`) remain valid, auto-seeded, and case-insensitively authenticated?
*   [ ] **The Figma Check:** Did I completely strip all inline `fill` and `stroke` attributes from newly imported SVG elements?
*   [ ] **The Dark Mode Check:** Do the new UI elements strictly use established CSS variables/classes, or did I accidentally hardcode a hex color that will break the dark mode aesthetic?
*   [ ] **The DB Crash Check:** Does this code query the database on startup? If yes, is it safely wrapped in an `app_context()` and does it verify the tables actually exist first?
*   [ ] **The Lighthouse Check:** Did I introduce any heavy external dependencies, unoptimized raster images (`<img>`), or blocking JavaScript that threatens the 95+ performance score?
*   [ ] **The Boy Scout Check:** Did I actively delete the dead code, consolidate duplicate logic, or remove legacy technical debt in the surrounding area of my fix?
*   [ ] **The Constraint Check:** Did I follow the exact tech stack required (HTML, vanilla CSS, vanilla JS, Python/Flask, Bootstrap 5) without hallucinating Next.js, React, or Tailwind solutions?
