# FixLink System Update Tracker (Tracker.md)
## Change Log, Release Notes & Live Update History

---

## 1. Latest Production Release Summary

| Version | Date | Status | Focus Areas |
| :--- | :--- | :--- | :--- |
| **v1.4.8** | 2026-09-02 | **Deployed** | Added sleek `<` back button directly to the left of Admin Support Team online status dot in chat. |
| **v1.4.7** | 2026-09-02 | **Deployed** | Removed clutter 'Remove photo' button from card; enabled intuitive avatar click action modal with hover overlay. |
| **v1.4.6** | 2026-09-02 | **Deployed** | Neutral true black & charcoal dark mode palette (zero bluish/slate wash), dark page header gradients, synchronized minified CSS. |
| **v1.4.5** | 2026-09-02 | **Deployed** | Removed `< Back` button from professional top nav, aligned MIT logo & FixLink brand to far left. |
| **v1.4.4** | 2026-09-02 | **Deployed** | Technician profile photo upload/removal, chat header UI simplification to 'Admin Support Team', keyboard viewport lock. |
| **v1.4.3** | 2026-09-02 | **Deployed** | Dedicated professional profile page, bottom nav link, top nav avatar removal, Rules.md compliance. |
| **v1.4.2** | 2026-09-02 | **Deployed** | LSP zero-warning cleanup, Touch pinch-to-zoom map, Mobile bug reporting, Faculty timetable migration, #undefined ticket fix. |

---

## 2. Chronological Log of Pushed Updates

### Release v1.4.8 (2026-09-02)
- `649befc`: **feat(chat): add sleek back button to the left of Admin Support Team online status**
  - **Header Back Navigation**: Added circular back button (`.chat-back-btn`) with chevron icon positioned immediately to the left of the green online status dot in `chat.html`.
  - **Smooth History Fallback**: Wires to `window.history.back()` with a graceful fallback to `/professional/dashboard`.

### Release v1.4.7 (2026-09-02)
- `8fe212f`: **feat(professional): remove clutter remove-photo button and enable intuitive photo change on avatar click**
  - **Eliminated Clutter Button**: Removed the standalone `Remove photo` button from beside the category badge on `profile.html`.
  - **Interactive Avatar Click Flow**: Clicking directly on the profile avatar or camera badge triggers the photo change workflow (or opens a modal offering Change Photo / Remove Photo if an image is present).
  - **Hover Overlay**: Added a smooth camera icon overlay upon hovering/tapping the profile avatar.

### Release v1.4.6 (2026-09-02)
- `923a7d5`: **fix(theme): convert dark mode palette from bluish tint to deep black and charcoal shades**
  - **Eliminated Blue/Navy Wash**: Removed slate-blue base/surface/overlay backgrounds (`#0F1117`, `#161B27`, `#1E2535`, `#1E293B`, `#334155`) in favor of neutral dark charcoal & true black shades (`--bg-base: #0a0a0a`, `--bg-surface: #141414`, `--bg-overlay: #1e1e1e`, `--border-default: #262626`).
  - **Dark Page Headers**: Overrode `.profile-page-header`, `.history-header`, and `.admin-header` in dark mode from light blue gradients into sleek black gradients (`linear-gradient(180deg, #111111 0%, #161616 100%)`).
  - **Profile & Chat Dark Redesign**: Converted technician profile cards, avatar containers, stat boxes, action rows, and chat bubbles into pure black & dark charcoal tones.
  - **CSS Minification & Cache Busting**: Minified `style.css` into `style.min.css` and bumped query string to `v=8.1`.

### Release v1.4.5 (2026-09-02)
- `775d42d`: **feat(nav): remove back button from professional top bar and align brand logo to the left**
  - **Removed Back Button for Professionals**: Added `session.get('professional_id')` and `request.endpoint.startswith('professional.')` exclusion to `#mobile-topbar-back-btn` in `base.html`.
  - **Left-Aligned Branding**: Positioned the MIT-WPU logo and FixLink brand text cleanly on the left side of `#mobile-top-bar` without offset.

### Release v1.4.4 (2026-09-02)
- `25ab42b`: **feat(professional): add profile picture upload and simplify chat header to intact Admin Support Team**
  - **Profile Picture Upload & Cropping**: Added interactive avatar circle with camera edit badge on `/professional/profile`. Images are processed and square-cropped to 320x320 on client-side canvas before uploading to `/professional/api/profile/picture`, storing directly in DB for 100% Vercel serverless persistence. Includes one-click photo removal.
  - **Chat Header Simplification**: Stripped back button, shield button, trash reset button, and dashboard button from `/professional/chat` header. Renamed cleanly to **Admin Support Team** with live online indicator.
  - **Keyboard Viewport Lock**: Added `interactive-widget=resizes-content` to viewport meta tag, sticky header positioning, and visualViewport scroll guards so the chat header stays firmly intact and never disappears when the mobile keyboard pops up.

### Release v1.4.3 (2026-09-02)
- `ac7b4a8`: **fix(auth): seed Bottle Singh and enable seamless technician login**
  - **Account Seeding**: Seeded `Bottle Singh` (`bottlesingh#pro`) into both PostgreSQL and SQLite databases, and embedded permanent auto-seeding in `init_db`.
  - **Flexible Authentication**: Configured fallback password authentication and automatic password sync on login for technician `bottlesingh#pro`.
- `f6bb33c`: **fix(vercel): eliminate 500 internal server error from stale sessions and missing db tables**
  - **Database Auto-Healing**: Removed blanket skip on Vercel; the app now safely inspects tables and auto-initializes missing tables via `scripts/init_data.py` non-interactively without throwing `EOFError`.
  - **Session Stale Guarding**: Protected `user_login_required`, `admin_required`, and `professional_login_required` decorators as well as `auth.login` and professional routes (`dashboard`, `chat`, `history`, `profile`) to clear orphaned session IDs and redirect to login instead of crashing with `AttributeError`.
- `5905248`: **feat(professional): add dedicated profile page, bottom nav link, and remove top bar avatar**
  - **Dedicated Profile Route & View**: Created `/professional/profile` and template `app/templates/professional/profile.html` featuring technician trade icon, specialty badge, contact info, "Open Chat Support" pill button, work activity counters, and account sign-out.
  - **Bottom Navigation**: Added the **Profile** tab (`bi-person-badge`) to `#mobile-bottom-nav` for technicians alongside Tasks and Chat.
  - **Top Navigation Bar Cleanup**: Removed redundant top bar profile avatar dropdown for technicians across mobile `#mobile-top-bar` and desktop capsule nav.
  - **Dashboard Cleanup**: Removed the sidebar "My Profile" card from `app/templates/professional/dashboard.html` to keep the dashboard focused on active tasks and help requests.
  - **Rules.md Compliance**: Zero hardcoded color breaks, CSS variable mapping, dark mode compatibility, semantic structure, and 100% test pass on `tests/test_auth.py` and `tests/test_ticket_lifecycle.py`.

### Release v1.4.2 (2026-09-02)
- `c008e5e`: **ci(pages): add .nojekyll and root index.html to resolve failing GitHub Pages build check**
  - Added `.nojekyll` to bypass Jekyll engine processing and eliminate Liquid template parsing crashes on markdown/template braces.
  - Added clean root `index.html` forwarding to the live Vercel production deployment (`https://fixlink26.vercel.app/`).
- `7878748`: **perf(lighthouse): boost performance to 95+ and accessibility to 100 on Admin Dashboard**
  - **CSS Optimization**: Synchronized preload query strings to prevent 326 KB duplicate stylesheet downloads; minified `style.css` into `style.min.css` saving 50 KB.
  - **Render Blocking Script Elimination**: Deferred `pusher.min.js`, removed unused external GSAP CDN plugins (`Flip.min.js`), and removed duplicate Pusher import in `admin.html`.
  - **FCP & Layout Recalculation**: Moved in-body `<style>` in `admin.html` into `<head>` `{% block extra_css %}` and deleted dead timetable import handlers.
  - **Duplicate Network Calls**: Eliminated redundant second `/api/me` call from mobile sidebar and deferred chat badge count.
  - **100% Accessibility**: Added `aria-labelledby` referencing modal titles on `ticketModal`, `cancellationModal`, and `notificationModal`.
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
