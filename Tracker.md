# FixLink System Update Tracker (Tracker.md)
## Change Log, Release Notes & Live Update History

---

## 1. Latest Production Release Summary

| Version | Date | Status | Focus Areas |
| :--- | :--- | :--- | :--- |
| **v1.4.2** | 2026-09-02 | **Deployed** | LSP zero-warning cleanup, Touch pinch-to-zoom map, Mobile bug reporting, Faculty timetable migration, #undefined ticket fix. |

---

## 2. Chronological Log of Pushed Updates

### Release v1.4.2 (2026-09-02)
- `542c55c`: **feat(compliance): implement Rules.md directives across backend, SVG twin, and dark mode styling**
  - **Rule 4 (DB Lifecycle)**: Added `sqlalchemy.inspect(db.engine).has_table(...)` guards to `app/database.py` before querying, preventing cold-start crashes, and added auto-seeding fallbacks for missing tables.
  - **Rule 2 (Digital Twin Architecture)**: Set `svgDoc.style.pointerEvents = 'none'` on root SVG container, dynamically stripped hardcoded inline `fill`/`stroke` attributes, and assigned base `.interactive-room` plus semantic classes (`.classroom`, `.lab`, `.washroom`, etc.) with `pointer-events: auto`.
  - **Rule 3 (UI/UX & Dark Mode Glow)**: Implemented 15% opacity fills with 2px solid strokes and 35% hover fills in dark mode for SVGs; added 5% translucent background with 10% faint borders for card depth (`.metadata-card`, `.stat-card`, `.card-depth`).
  - **Rule 1 & Rule 5 (Lighthouse & Semantic HTML)**: Wrapped room details panel in semantic `<aside>`, added descriptive `aria-label` to buttons, and purged legacy dead code.
- `02fee82`: **fix(lsp): resolve template JS syntax errors in status_map.html and pyright SQLAlchemy call issues in scripts**
  - Converted raw Jinja inline bindings inside `<script>` into clean `application/json` data islands with `JSON.parse()`.
  - Added Pyright type suppression directives to `init_data.py` and `fix_user.py` to eliminate false-positive SQLAlchemy model constructor warnings.
  - Made `sys.path` resolution dynamic and cross-platform in utility scripts.
- `938ba62`: **fix(status_map): consolidate CSS into extra_css block and clean up extra_js syntax**
  - Extracted 200+ lines of misplaced styles from the `extra_js` block into `<head>`'s `extra_css`.
  - Fixed unbalanced CSS braces that were crashing the template parser.
- `e9bac53`: **fix: resolve #undefined ticket ID on submission, fix mobile signup password eye toggle, and add mobile touch pinch zoom while removing zoom buttons**
  - Resolved `#undefined` ticket reference issue by harmonizing client response parsing across `data.data.ticket_id` and top-level `data.ticket_id`.
  - Upgraded signup password input with `.password-input-wrapper` and integrated toggle button to prevent mobile line-wrapping.
  - Added natural mobile touch gesture engine (two-finger pinch to zoom, single finger pan when zoomed, double tap zoom) to floor maps.
  - Stripped redundant zoom button toolbar from the status map header for a clean mobile header.
- `d1d5091`: **feat(faculty): move Import Timetable button+modal from admin dashboard to faculty portal**
  - Removed "Import Timetable" button and `#importTimetableModal` from admin dashboard.
  - Added "Import Timetable" button and full modal into the Faculty Upcoming Agenda dashboard with CSV file parsing.

### Release v1.4.1 (2026-09-01)
- `85b7a45`: **fix(signup): fix eye toggle button layout using proper Bootstrap input-group append**
  - Fixed floating absolute button alignment on password inputs.
- `a8b6d1f`: **feat(mobile): add icon-only Report Bug button to mobile top bar next to theme toggle**
  - Streamlined mobile top header by placing an icon-only bug button beside the theme switch.
- `576286d` / `1a74921`: **fix(developer): restore vivid status badge and action button colors in dark mode**
  - Overrode desaturated dark mode colors for Bootstrap badges and icons in the developer and superadmin dashboards.
- `2fe0a79`: **fix(mobile): declutter status map legend and map header on small screens**
  - Organized map legend into two compact, pill-chip rows and improved touch spacing.
- `bb1a880`: **feat(mobile): replace bottom nav Report Bug page link with modal trigger; hide floating pill on mobile**
  - Replaced full-page navigation with modal popup and removed duplicate floating UI elements.
- `828b940`: **fix(auth): synchronize and support credentials for om.mahadik@mitwpu.edu.in across Developer and Main login**
  - Updated password hash and user verification records.
- `e696da9`: **style(signup): optimize signup card vertical rhythm and padding for full viewport visibility**
  - Refined signup card margins and padding for small mobile screens.
- `95d64c3`: **feat(auth): add Create Password block with visibility toggle to Student Sign Up and enable direct login**
  - Enabled password creation on student signup with validation.
- `7fa59dc`: **feat(auth): grant Super Admin access to om.mahadik@mitwpu.edu.in alongside primary developer credentials**
- `4bb1e9d`: **feat(map): make floor maps significantly larger with responsive scaling and interactive zoom controls**
  - Scaled floor plans to responsive viewport height with improved visibility.

---

## 3. Active Roadmap & Future Milestones

- [x] Natural Touch Gestures on Floor Maps (Pinch-to-zoom & Two-Finger Pan).
- [x] Zero-clutter Mobile Topbar & Status Map Header.
- [x] Robust Ticket Reference ID Generation.
- [x] Faculty Timetable CSV Ingestion.
- [ ] Automated Email Notifications via background worker queue for ticket state changes.
- [ ] Push Notifications for Technicians on work assignment via Web Push API.
- [ ] Offline PWA Service Worker caching for floor maps during intermittent campus Wi-Fi.
