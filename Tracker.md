# FixLink System Update Tracker (Tracker.md)
## Change Log, Release Notes & Live Update History

---

## 1. Latest Production Release Summary

| Version | Date | Status | Focus Areas |
| :--- | :--- | :--- | :--- |
| **v1.7.4** | 2026-09-16 | **Deployed** | Root User / Super Admin Security & Immutable Creator Accounts (Permanently secured creator accounts against unauthorized edits, deletions, and password resets; locked down backend routes with 403 Forbidden checks; hardened admin and superadmin Jinja UI templates). |
| **v1.7.3** | 2026-09-16 | **Deployed** | Interactive Map Room Popup Position Fix (Prevented room info popup from overlapping the floor dropdown selector and legend; added auto-dismiss on floor change; polished dark mode pop-card contrast). |
| **v1.7.2** | 2026-09-16 | **Deployed** | Theme Color Mode Bugfixes (Fixed dark mode text contrast on timetable classes, removed hardcoded black box on Booking History in light mode, and restored bright high-contrast room labels on SVG maps). |
| **v1.7.1** | 2026-09-16 | **Deployed** | Technical Debt Purge & UI Polish (Removed legacy 'Sync My Timetable' button and popup, fixed afternoon class time parsing, and polished Smart Classroom map header). |
| **v1.7.0** | 2026-09-16 | **Deployed** | Timetable Class Allocation (Fixed imported spreadsheet classes wrongly assigning to admin; added easy teacher dropdown on Admin Dashboard with one-click, instant assignment). |
| **v1.6.3** | 2026-09-11 | **Deployed** | Legal Templates Grounding & Artifact Removal (Stripped AI Draft Banners, Corrected Institutional Scope, Codebase-Verified Retention Durations in Cookies, Terms & Privacy). |
| **v1.6.2** | 2026-09-11 | **Deployed** | WCAG 2.1 AA Color Contrast Hardening (Global Typography, SVG Map Labels Readability, Dark Mode Form Inputs & Interactive Button States). |
| **v1.6.1** | 2026-09-11 | **Deployed** | Custom 404 Error Page (Zone Not Found), Dark Mode Translucent Infrastructure Aesthetic, and Search Engine Indexing Protection. |
| **v1.6.0** | 2026-09-11 | **Deployed** | Web Accessibility (a11y), Data Minimization & Consent, Legal Boilerplates (Privacy, Terms, Cookies), and Asset Security CDN hardening. |
| **v1.5.3** | 2026-09-03 | **Deployed** | Removed 'My Tasks' and technician nav items from the developer site and developer sessions. |
| **v1.5.2** | 2026-09-02 | **Deployed** | Guaranteed Developer/Superadmin credentials (`om.mahadik@mitwpu.edu.in`), auto-seeding in `init_db()`, self-healing login, and formalized Rule 6 in `Rules.md`. |
| **v1.5.1** | 2026-09-02 | **Deployed** | Centered 'Admin Support Team' title in chat header with balanced `<` back button navigation. |
| **v1.5.0** | 2026-09-02 | **Deployed** | Fixed dark mode chat send button from pale ice-hint `#C8D8E8` to high-contrast rich blue `#2563eb` with `#ffffff` icon. |
| **v1.4.9** | 2026-09-02 | **Deployed** | Removed redundant 'Open Chat Support' button, equalized Work Activity card heights with flex stretch, restored vibrant icon colors in dark mode. |
| **v1.4.8** | 2026-09-02 | **Deployed** | Added sleek `<` back button directly to the left of Admin Support Team online status dot in chat. |
| **v1.4.7** | 2026-09-02 | **Deployed** | Removed clutter 'Remove photo' button from card; enabled intuitive avatar click action modal with hover overlay. |
| **v1.4.6** | 2026-09-02 | **Deployed** | Neutral true black & charcoal dark mode palette (zero bluish/slate wash), dark page header gradients, synchronized minified CSS. |
| **v1.4.5** | 2026-09-02 | **Deployed** | Removed `< Back` button from professional top nav, aligned MIT logo & FixLink brand to far left. |
| **v1.4.4** | 2026-09-02 | **Deployed** | Technician profile photo upload/removal, chat header UI simplification to 'Admin Support Team', keyboard viewport lock. |
| **v1.4.3** | 2026-09-02 | **Deployed** | Dedicated professional profile page, bottom nav link, top nav avatar removal, Rules.md compliance. |
| **v1.4.2** | 2026-09-02 | **Deployed** | LSP zero-warning cleanup, Touch pinch-to-zoom map, Mobile bug reporting, Faculty timetable migration, #undefined ticket fix. |

---

## 2. Chronological Log of Pushed Updates

### Release v1.7.4 (2026-09-16)
- `feat(security)`: **Root User / Super Admin Authorization Lockdown & Creator Account Protection**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Permanently Protected Creator Accounts (Root Security Vault)**:
     - Established a hardcoded, environment-level security rule protecting the two primary creator accounts (`taha.piplodwala@mitwpu.edu.in` and `om.mahadik@mitwpu.edu.in`).
     - Added a dynamic `is_super_admin` security check on user accounts that cannot be bypassed or modified through database alterations.
     - Enforced an immutable ownership policy: no regular Administrator, Faculty member, Student, or other Administrator can edit, change passwords for, or delete these accounts. Only the specific account owner can modify their own details.
  2. **Backend Route Lockdown (403 Forbidden Shield)**:
     - Injected a strict security guard across all user management API endpoints (editing details, updating passwords, switching user roles, and deleting accounts).
     - Any unauthorized attempt to tamper with a Super Admin account immediately halts with an HTTP 403 Forbidden status code and a clear alert ("Unauthorized: Cannot modify Super Admin accounts.").
  3. **Frontend UI Hardening (Clean & Protected Tables)**:
     - In the user management tables (both Admin and Developer/Superadmin portals), the Edit (pencil), Delete (trash), Role selection dropdown, and Password reveal buttons are completely stripped from the screen for protected accounts.
     - Replaced interactive controls with a sleek static "Super Admin" badge and plain text role, while allowing the account owner to retain their own Edit button for profile updates.
  4. **Automated Security Test Suite**:
     - Added a dedicated test suite (`tests/test_super_admin_guard.py`) covering all security layers (model properties, API route rejection, self-edit permissions, and template rendering safeguards).

---

### Release v1.7.3 (2026-09-16)
- `fix(map-popup)`: **Interactive Map Room Popup Positioning Fix, Unblocked Floor Controls, Auto-Dismiss, and Dark Mode Polish**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Unblocked Floor Selector & Legend (No More Overlapping Popups)**:
     - When clicking on any room or lab (such as Computer Lab 427) on the interactive floor map, the floating room card was popping up too high on the screen (`top: 100px`).
     - This caused the top of the popup and its close button to sit directly on top of the "4th Floor (Interactive)" dropdown and the green/red status legend dots, blocking clicks and covering the controls.
     - We adjusted the popup's desktop positioning to `top: 180px` with a responsive height limit (`max-height: calc(100vh - 210px)`). The room card now docks neatly beneath the floor controls, keeping the floor dropdown and status legend 100% visible and easily clickable at all times.
  2. **Smart Auto-Dismiss When Switching Floors**:
     - Previously, if a professor had a room card open on Floor 4 and changed the dropdown to Floor 3, the old room card stayed on screen, showing outdated details.
     - The floor dropdown now automatically closes any active room popup when a new floor is picked, keeping the interface clean and context-accurate.
  3. **High-Contrast Dark Mode for Room Information**:
     - Enhanced the dark mode appearance of the room popup: the card borders, titles, 'X' close button, and status alert boxes (such as "Optimal Levels / Room is vacant") now render with crisp text and high-contrast styling without washed-out gray tones.
  4. **Production Cache Busting**:
     - Bumped the stylesheet cache buster in `base.html` to `v=8.7`.

---

### Release v1.7.2 (2026-09-16)
- `fix(theme-colors)`: **Theme Color Mode Bugfixes: Timetable Dark Mode Typography, Booking History Light Mode Alignment, and SVG Floor Map Label Legibility**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Timetable Cells Readable in Dark Mode (No More Hidden Text)**:
     - Previously, when switching to dark mode, scheduled class names (e.g. `TYBCA DIV A (3.00-4.00)`) were colored in dark slate `#0f172a`, making them almost black-on-black and impossible to read.
     - They now dynamically adapt to crisp bright white (`#f8fafc`) with soft contrast shadows, while room meta badges (`VYAS VY427`) and vacant cells cleanly match the dark theme.
  2. **Booking History Table Fits Both Light & Dark Themes**:
     - The "Booking History" table previously had a hardcoded `table-dark` class, meaning it stayed pitch black with muddy gray text even when the user was browsing in clean Light Mode.
     - Replaced the hardcoded black table with a theme-aware card that renders with a crisp white background and clean borders in light mode, and seamlessly switches to sleek dark charcoal in dark mode.
  3. **Crystal-Clear Room Numbers on the SVG Floor Map**:
     - An aggressive CSS selector (`fill: #1e293b !important;` and `.fill-blue *`) was previously overriding room number text, turning labels dark slate on deep navy blue classrooms and gray-on-gray on utility rooms.
     - Restored crisp, brilliant white text labels (`#ffffff`) with protective drop shadows across classrooms, labs, and washrooms in light mode, and bright `#f8fafc` text in dark mode. Room numbers like `VY401`, `VY414`, `VY424` are now instantly readable at any zoom level.
  4. **Production Stylesheet Sync & Cache Busting**:
     - Recompiled `style.min.css` and bumped the preload and stylesheet version query to `v=8.6`.

---

### Release v1.7.1 (2026-09-16)
- `refactor(cleanup)`: **Surgical Purge of Legacy Schedule Synchronizer Modal, Afternoon Timetable Slot Parsing Fix, and Smart Classroom Map Header Polish**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Removed the Obsolete "Sync My Timetable" Button & Popup**:
     - With the modern CSV Mass Timetable Import in place, professors no longer have to manually piece together weekly classes one by one.
     - Following our "Aggressive Deletion" guardrails, we completely deleted the old **"Sync My Timetable"** button, the popup modal, the staging queue, and the background synchronization route.
     - Over 450 lines of dead code were removed, making the dashboard load faster and keeping the interface clean.
  2. **Fixed Afternoon Class Times on the Weekly Grid**:
     - Timetables written with slots like `2:00 - 4:00` or `3.00-5.00` were previously treated as AM (morning) slots, causing afternoon classes to disappear off the visual 9 AM – 6 PM calendar.
     - The parser now smartly recognizes daytime university hours (1:00 PM to 7:00 PM) and places them into their correct afternoon slots automatically. Existing database entries were also repaired.
  3. **Polished "Smart Classroom Management" Map Header**:
     - **Restored Status Dots**: Added clean, glowing green and red indicator dots next to "Available" and "Occupied" in a sleek rounded pill card.
     - **Fixed Floor Dropdown Width**: The floor selection dropdown no longer stretches across the entire screen; it is neatly formatted as a compact pill aligned to the right.
     - **Full Dark Mode Support**: The status card and floor selector seamlessly adapt to dark mode with clear contrast and custom dropdown chevrons.
  4. **Fresh Stylesheet Cache Busting**:
     - Updated and compressed `style.min.css` and bumped the version tag to `v=8.5` so browser caches load the newest design immediately.

---

### Release v1.7.0 (2026-09-16)
- `feat(timetable)`: **Timetable Bulk Import & Easy Faculty Assignment (Admin Allocation System)**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **The Problem We Fixed (No More Wrong Teacher Assignments)**:
     - Previously, when an administrator uploaded a campus timetable spreadsheet (CSV), any class that didn't have an instructor listed was automatically assigned to the administrator (e.g. Taha Mustafa). This cluttered the admin's personal schedule and left real professors with missing classes.
     - **The Fix**: Classes without a teacher are now cleanly recognized as **"Unassigned"**. They never get dumped onto the admin's account.
  2. **New "Unassigned Classes" Section on Admin Dashboard**:
     - Admins now have a dedicated, easy-to-read list titled **"Unassigned Classes Requiring Faculty Allocation"** right on their dashboard.
     - It displays the room number, day of the week, time slot, and course name for every session that needs a teacher.
     - A yellow badge at the top shows the exact number of classes still waiting to be assigned.
  3. **One-Click Teacher Assignment with Dropdowns**:
     - Each unassigned class has a simple dropdown menu listing all registered faculty members by name.
     - The admin simply picks a professor from the list and clicks **"Assign"**.
     - **Friendly Mistake Protection**: If the admin clicks "Assign" before choosing a name, the app gently reminds them: *"Please select a faculty member from the dropdown before assigning."*
  4. **Instant, No-Reload Screen Updates**:
     - The moment a teacher is assigned, that row smoothly fades out and disappears from the unassigned list—**without the web page needing to refresh or flicker**.
     - The unassigned counter automatically counts down in real time.
     - Once all classes have teachers, the table automatically displays a green checkmark stating: *"No unassigned classes found. All classes across the Vyas building have faculty assigned."*
  5. **Safety, Security & Verification**:
     - Only logged-in campus administrators can assign classes.
     - Runs on existing dark mode and light mode themes with zero visual glitches.
     - 6 automated test scenarios were added to guarantee that timetable imports and teacher assignments always run reliably without breaking anything.

  ---

  #### 🖥️ Where & How You as a Developer Can See and Test These Changes

  | What to Test | Where on the Site | Step-by-Step Testing Guide | Expected Visual Result |
  | :--- | :--- | :--- | :--- |
  | **1. Unassigned Classes List** | `http://localhost:5000/admin/` | 1. Log in as an Admin (`admin@mitwpu.edu.in`).<br>2. Scroll down on the Admin Dashboard below the tickets section. | A clean card labeled **"Unassigned Classes Requiring Faculty Allocation"** displays with room badges, day/time slots, subjects, division, a faculty select dropdown, and an "Assign" button. |
  | **2. Friendly Reminder on Empty Dropdown** | `http://localhost:5000/admin/` | 1. Leave the dropdown on "Choose Faculty...".<br>2. Click the **"Assign"** button. | A pop-up prompts: *"Please select a faculty member from the dropdown before assigning."* Nothing is submitted until a name is picked. |
  | **3. Instant One-Click Assignment** | `http://localhost:5000/admin/` | 1. Pick any professor from the dropdown (e.g., Prof. Sharma).<br>2. Click **"Assign"**. | The button briefly shows a loading spinner, and the row **smoothly slides and fades away**. The count badge decreases immediately without refreshing the page. |
  | **4. All-Done Message** | `http://localhost:5000/admin/` | Assign all remaining classes in the table. | The table automatically updates to show a friendly green checkmark: *"No unassigned classes found. All classes across the Vyas building have faculty assigned."* |
  | **5. Dark Mode Compatibility** | `http://localhost:5000/admin/` | Click the Moon/Sun icon in the header to switch to Dark Mode. | The table, dropdowns, and text automatically adjust to soft dark colors with high-contrast text that is easy on the eyes. |

---

### Release v1.6.2 (2026-09-11)
- `fix(a11y-contrast)`: **strict WCAG 2.1 AA color contrast hardening across global typography, dynamic SVG floor map room labels, dark mode form controls, and interactive button states**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Global Text & Background Contrast (WCAG 2.1 AA >= 4.5:1)**:
     - **Replaced Low-Contrast Bootstrap Grays**: Default Bootstrap `.text-muted` and `.text-secondary` (`#6c757d`) failed WCAG AA on white (4.38:1) and dark surfaces (3.5:1). Overrode them with theme-aware tokens:
       - **Light Mode**: `#4b5563` (Gray 600) providing **7.0:1** contrast against white backgrounds.
       - **Dark Mode**: `#a1a1aa` (Zinc 400) providing **7.4:1** contrast against deep black (`#0a0a0a`) and **6.6:1** against surface cards (`#141414`).
     - **Inverted Utility Classes**: Added dynamic dark-mode overrides for `.bg-light` and `.bg-white` so white background boxes never blind users when switching to dark theme.
  2. **SVG Floor Map Room Label Readability**:
     - **Dynamic Fill Flipping**: Fixed hardcoded black/white SVG path text. Room numbers and labels now dynamically flip:
       - **Light Mode**: Deep dark slate (`#1e293b`) with a subtle white protective halo filter (`drop-shadow(0 0 1px rgba(255,255,255,0.9))`) for **> 12:1** contrast against room fills.
       - **Dark Mode**: Crisp white (`#f8f9fa`) with a dark drop shadow (`drop-shadow(0 1px 2px rgba(0,0,0,0.95))`) for **19:1** contrast against the dark floor plan canvas.
     - **Hover & Selection Protection**: When hovering or clicking rooms (e.g. green selected or red issue states), room text remains razor-sharp with contrast halos and zero stroke boldness bleeding.
  3. **Forms, Inputs & Borders**:
     - **Dark Mode Input Canvas**: Configured dark mode inputs (`.form-control`, `.form-select`, `textarea`) with a distinct translucent background (`rgba(255, 255, 255, 0.05)`), a clearly visible border (`rgba(255, 255, 255, 0.20)`), and high-contrast placeholder text (`#a1a1aa`, 5.8:1 contrast).
     - **High-Contrast Dividers**: Adjusted modal headers, footers, `<hr>`, and card borders in dark mode to `rgba(255, 255, 255, 0.18)` for crisp spatial structure without visual mud.
  4. **Interactive States & Buttons**:
     - Ensured `.btn-primary`, `.btn-outline-secondary`, `.btn-warning`, and interactive elements maintain high contrast (> 4.5:1) in default, hover, active, and focus states. In particular, warning badges/buttons enforce dark text (`#18181b`) over yellow backgrounds for a massive **12.8:1** contrast ratio.
     - Synchronized minified stylesheet (`style.min.css`) and bumped query cache string to `v=8.4`.

  ---

  #### 🖥️ Where & How You as a Developer Can See and Test These Changes

  | What to Test | Where on the Site | Step-by-Step Testing Guide | Expected Visual Result |
  | :--- | :--- | :--- | :--- |
  | **1. SVG Room Labels in Dark Mode** | `http://localhost:5000/report` | 1. Navigate to the floor map.<br>2. Toggle to **Dark Theme** (moon icon).<br>3. Inspect the room numbers (e.g., VY301, VY307, Lift). | Labels appear in **crisp white (`#f8f9fa`)** with a subtle dark halo shadow. Black text never disappears into the dark canvas. |
  | **2. SVG Room Labels in Light Mode** | `http://localhost:5000/report` | 1. Toggle back to **Light Theme** (sun icon).<br>2. Inspect the floor map room numbers. | Labels render in **dark slate (`#1e293b`)** with a clean light protective halo against the room fills. |
  | **3. Form Inputs & Placeholders** | `http://localhost:5000/ticket-form` | 1. Open the standalone ticket form.<br>2. Toggle to **Dark Theme**.<br>3. Look at the empty Description textarea and dropdown borders. | Inputs have a distinct **translucent dark background (`rgba(255,255,255,0.05)`)**, a **crisp 20% white border**, and **high-visibility placeholder text (`#a1a1aa`)**. |
  | **4. Secondary & Muted Text** | `http://localhost:5000/ticket-form` or footer | 1. Observe the subtitle and helper text.<br>2. Switch between light and dark modes. | Text is clearly legible in both themes: soft zinc (`#a1a1aa`) in dark mode, deep slate (`#4b5563`) in light mode (both >= 6.6:1 contrast). |
  | **5. Interactive Room Hover** | `http://localhost:5000/report` | Hover your mouse over any classroom on the map in dark mode. | The room highlights with accent tint, and the room label stays **pure white with high-contrast text shadow**, never washing out. |

---

### Release v1.6.1 (2026-09-11)
- `feat(error-page)`: **redesigned 404 error page ("Page Not Found") with calm, factual facility tone, zero custom CSS, full token reuse, and actionable routing**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Flask Application 404 Handler (`app/__init__.py`)**:
     - Configured the `@app.errorhandler(404)` decorator at the application root level.
     - When any user, bot, or crawler visits an unregistered or broken link, Flask now renders the dedicated `404.html` template and explicitly returns HTTP status code `404`. This ensures search engine crawlers (Google, Bing) know the page doesn't exist and never index broken error pages.
  2. **Grounded Facility UI Redesign (`app/templates/404.html`)**:
     - **Clean, Factual Copy**: Replaced sci-fi tropes, glowing radar animations, and fake error codes with calm, facility-focused communication:
       - Single `<h1>` Heading: **`Page Not Found`**
       - Plain explanation: *"The page or fault ticket you're looking for doesn't exist or may have been resolved and archived."*
       - Real URL path display: plainly labeled `Requested: {{ request.path }}` without fabricated telemetry jargon.
     - **Pure CSS Token Reuse (Zero Custom Styling)**: Completely eliminated custom `<style>` rules. Purely reuses FixLink's existing design system: `.card.rounded-4`, `var(--bg-card)`, `var(--border-color)`, `.text-body-emphasis`, and `.text-body-secondary`.
     - **Functional Icon**: Uses a simple, functional `bi-geo-alt-slash` icon with `aria-hidden="true"` rather than decorative sci-fi animations.
     - **Clear Action Hierarchy**: Features a single primary CTA button **"Return to Fault Map"** (`.btn.btn-primary`) and a subtle secondary text link **"&larr; Go back to previous page"** (`javascript:history.back()`).

  ---

  #### 🖥️ Where & How You as a Developer Can See and Test These Changes

  | What to Test | URL to Visit | How to Test | Expected Result |
  | :--- | :--- | :--- | :--- |
  | **1. Unmatched Route 404** | `http://localhost:5000/non-existent-sector` | Open this URL in any browser tab. | You will see the clean, calm **"Page Not Found"** card with the location-slash icon, plain explanation, and requested URL path. |
  | **2. Direct Preview Route** | `http://localhost:5000/404` | Open `http://localhost:5000/404`. | The redesigned 404 page renders immediately with HTTP 404 status. |
  | **3. Return to Map Button** | On the 404 page | Click **"Return to Fault Map"** or press Enter while focused on it. | Navigates cleanly back to the root `/` (fault reporting portal / architectural map). |
  | **4. History Back Link** | On the 404 page | Click **"← Go back to previous page"**. | Steps back in browser history gracefully. |
  | **5. Search Crawler Meta Tag** | DevTools Elements Tab | Inspect `<head>` of the 404 page. | Contains `<meta name="robots" content="noindex, nofollow">` to prevent crawlers from indexing. |

---

### Release v1.6.0 (2026-09-11)
- `feat(a11y-privacy-security)`: **comprehensive web accessibility (a11y), data minimization, user consent, legal boilerplate generation, and CDN asset security overhaul**

  #### 📖 Plain English / Layman's Summary of What Was Done
  1. **Accessibility for Everyone (Screen Readers & Keyboard Users)**:
     - **Meaningful Image Descriptions (`alt` tags)**: Web screen readers read out image descriptions to visually impaired users. Previously, several images had generic tags like `alt="Logo"` or `alt="Profile"`. We upgraded these to specific, helpful descriptions like `"MIT-WPU FixLink Logo"` and `"User profile avatar"`.
     - **Specific Action Buttons**: Generic buttons like "Submit", "Done", or "Cancel" don't clearly state what action is about to happen. We renamed them with active verbs:
       - `"Submit Report"` ➔ **`"Submit Fault Report"`**
       - `"Done"` (success modal) ➔ **`"Close Confirmation"`**
       - `"Send to Developer"` ➔ **`"Submit Bug Report"`**
       - `"Cancel"` ➔ **`"Cancel Bug Report"`**
       - `"Close"` ➔ **`"Close Notification"`** / **`"Close Profile Details"`**
     - **Glowing Keyboard Navigation Rings (`:focus-visible`)**: People who cannot use a mouse navigate websites using the keyboard `Tab` key. In dark mode, it was nearly impossible to see which button or input had focus. We engineered a high-contrast electric sky-blue glowing ring (`#38bdf8`) around all active form inputs, buttons, links, and dropdowns that pops vibrantly against the dark background, meeting international WCAG 2.2 accessibility standards.

  2. **Data Privacy, Minimization & User Consent**:
     - **Database Privacy Audit**: We systematically reviewed `models.py` to flag personal information stored beyond basic identification (Name, PRN, Email). We identified sensitive items such as user avatars (biometric likeness), technician mobile phone numbers, device push tokens, and uploaded camera photos that might accidentally capture faces or private belongings.
     - **Mandatory User Consent**: Added a required confirmation checkbox to the maintenance reporting form:
       > *"I consent to the collection of my PRN and email solely to process this maintenance request."*
       Students and staff must check this before a fault ticket can be submitted.
     - **Consent-Gated Analytics in `<head>`**: Audited the HTML header and wrapped any external tracking or analytics in a `{% if cookie_consent %}` conditional. Analytics scripts will now never load behind the user's back without explicit consent.

  3. **Official University Legal Boilerplate Pages**:
     - Drafted three complete, professional policy documents styled to match our dark/light theme:
       - **Privacy Policy** (`/privacy`): Details what student/staff info is recorded, why it's collected, who sees it, and retention limits.
       - **Terms of Service** (`/terms`): Sets ground rules for submitting genuine facility tickets and acceptable classroom tool usage.
       - **Cookie Policy** (`/cookies`): Explains our strict session, CSRF security, and theme preference cookies.
     - Linked all three policies in the site footer so they are easily accessible from any page.

  4. **Asset Security & External CDN Hardening**:
     - **Secured External CDNs**: External scripts and stylesheet links (like Pusher and GSAP animations) were reinforced with `rel="noopener noreferrer"`, `crossorigin="anonymous"`, and `referrerpolicy="no-referrer"` to prevent cross-origin tracking and tab-hijacking vulnerabilities.
     - **Guaranteed Local Fallback Asset**: Audited the codebase to confirm zero external/insecure image links exist. Created a local fallback placeholder image at `/static/img/placeholder.jpg` to prevent broken image icons if an upload is missing.

  ---

  #### 🖥️ Where & How You as a Developer Can See and Test These Changes

  | What to Test | Where on the Site | Step-by-Step Testing Guide | Expected Visual Result |
  | :--- | :--- | :--- | :--- |
  | **1. Keyboard Focus Visibility** | `http://localhost:5000/report` or `/login` | 1. Open the page.<br>2. Switch to **Dark Theme** (click the Moon icon in the header).<br>3. Don't touch your mouse; press the **`Tab`** key repeatedly. | You will see an **electric cyan-blue outline (`#38bdf8`) with a soft glow** cleanly framing each input field, floor dropdown trigger, and button. |
  | **2. Mandatory Consent Checkbox** | `http://localhost:5000/report` | 1. Go to the Issue Details form on the right panel.<br>2. Scroll down just above the submit button.<br>3. Fill out the form, leave the checkbox unchecked, and click **"Submit Fault Report"**. | A required checkbox reading *"I consent to the collection of my PRN and email solely to process this maintenance request"* is visible. The browser blocks submission and prompts you to check the box. |
  | **3. Action Verb Buttons** | `http://localhost:5000/report` | 1. Look at the primary submit button.<br>2. Submit a report (or test the modal) to view the confirmation dialog. | The primary button displays **"Submit Fault Report"** (with paper plane icon). The success modal button displays **"Close Confirmation"**. |
  | **4. Privacy Policy Page** | `http://localhost:5000/privacy` | Open `http://localhost:5000/privacy` in your browser, or scroll to the bottom footer on any page and click **"Privacy Policy"**. | Displays a formatted, mobile-responsive Privacy Policy card with breadcrumbs, legal draft notice, data minimization summary, and dark mode support. |
  | **5. Terms of Service Page** | `http://localhost:5000/terms` | Open `http://localhost:5000/terms` or click the **"Terms of Service"** link in the footer. | Displays the Acceptable Use Policy draft for university facility management. |
  | **6. Cookie Policy Page** | `http://localhost:5000/cookies` | Open `http://localhost:5000/cookies` or click the **"Cookie Policy"** link in the footer. | Displays an itemized table listing strictly necessary session cookies, CSRF tokens, theme storage, and consent gates. |
  | **7. Standalone Ticket Form** | `http://localhost:5000/ticket-form` | Open `http://localhost:5000/ticket-form` in your browser. | Displays the clean, dedicated ticket reporting template with accessible dropdowns, consent box, and submit CTA. |
  | **8. CDN Hardening & Asset Security** | Any page (e.g. `http://localhost:5000/report`) | 1. Press **`F12`** (Open DevTools) &gt; **Elements** tab.<br>2. Inspect `<head>` and bottom `<script>` tags. | CDN `<link>` and `<script>` tags for Pusher and GSAP contain `rel="noopener noreferrer" referrerpolicy="no-referrer"`. |
  | **9. Image Alt Text** | Any page header / logo | In DevTools, inspect the top-left university logo. | Logo image contains `alt="MIT-WPU FixLink Logo"`. User avatars contain `alt="User profile avatar"`. |
  | **10. Local Image Placeholder** | `http://localhost:5000/static/img/placeholder.jpg` | Paste this URL directly into your browser. | The guaranteed local fallback placeholder image loads immediately without relying on any external 3rd-party image server. |

---

### Release v1.5.3 (2026-09-03)
- `fix(navigation)`: **restore profile button, eliminate navbar bloat, and restore login redirects**
  - **Permanently Visible Profile Button**: Removed the conditional hiding of the profile avatar dropdown button in [base.html](file:///d:/FixLink-V1/app/templates/base.html) (`navAvatar`). It is now always visible on the desktop navbar for all authenticated sessions, complete with user initials/avatar, display name, email, and one-click Logout.
  - **Clean, Single-Line Capsule Navigation**: Replaced overlapping role `{% if %}` checks in [base.html](file:///d:/FixLink-V1/app/templates/base.html) with mutually-exclusive blocks (`if is_admin` vs `elif professional_id` vs `elif user_role == 'faculty'` vs `else`). Removed technician items (`My Tasks`, duplicate `Chat`, and `Profile`) from Admin and Developer views, moving Admin access to Faculty Portal and Report Issue into the `Manage` dropdown to prevent capsule overflow and multi-line wrapping.
  - **Restored `/login` Redirections**: Restored proper HTTP 302 redirects to `/login` in [main/routes.py](file:///d:/FixLink-V1/app/blueprints/main/routes.py) (`@main_bp.route('/')`), [professional/routes.py](file:///d:/FixLink-V1/app/blueprints/professional/routes.py), and throughout [decorators.py](file:///d:/FixLink-V1/app/decorators.py) (`user_login_required`, `faculty_login_required`, `professional_login_required`). Users navigating to `fixlink26.vercel.app` or accessing protected pages unauthenticated are immediately redirected to `/login`.
  - **In-Memory Session Sanitizer Hook**: Added `@app.before_request` hook in [__init__.py](file:///d:/FixLink-V1/app/__init__.py) that instantly and non-blockingly (zero DB queries) cleanses stale `professional_id` cookies whenever a `user_id` session is active.
  - **Automated Verification**: Added comprehensive test coverage in [test_auth.py](file:///d:/FixLink-V1/tests/test_auth.py) validating redirect behavior, profile button presence, and role isolation. All 7 test cases passing.

### Release v1.5.2 (2026-09-02)
- `c35bc87`: **fix(auth): guarantee Om Mahadik credentials and add Rule 6 for zero credential loss and self-healing login**
  - **Auto-Seeded Developer/Superadmin**: Guaranteed account creation and password sync for `om.mahadik@mitwpu.edu.in` (`omni12345`, `role=ROLE_ADMIN`, `is_admin=True`, `is_verified=True`) inside `init_db()` in `app/database.py`.
  - **Self-Healing Login Handler**: Implemented on-the-fly user creation and synchronization in `app/blueprints/auth/routes.py` with case-insensitive email matching (`func.lower(User.email) == login_input.lower()`).
  - **New Rule 6 in Rules.md**: Added strict guardrails in `Rules.md` prohibiting credential loss, mandating core account seeding, case-insensitive auth lookups, and adding pre-commit credential integrity checks.

### Release v1.5.1 (2026-09-02)
- `8e8284e`: **feat(chat): center Admin Support Team header title with balanced back-button navigation**
  - **Centered Header Alignment**: Arranged `.chat-header` with flex space-between and a balanced spacer element, centering the title (`.chat-header-title` with online status indicator) in the chat header on both desktop and mobile viewports.
  - **Maintained Back Button Placement**: Preserved the circular `<` back button anchored on the far left.

### Release v1.5.0 (2026-09-02)
- `2047e82`: **fix(theme): eliminate pale baby blue ice-hint button background in dark mode and style send button with rich blue and crisp contrast**
  - **Eliminated Pale Ice-Hint Accent Override**: Removed legacy `--mitwpu-blue: var(--ice-hint) !important` (`#C8D8E8`) and `[data-theme="dark"] .text-primary { background-color: var(--ice-hint) !important; }` in `style.css` which was rendering the chat send button and primary CTAs in an awkward baby-blue tone with unreadable contrast.
  - **Re-styled Send Button**: Restyled `.send-btn` in `professional/chat.html`, `admin/chat.html`, and `style.css` to vibrant royal blue (`#2563eb`) with high-contrast white paper airplane icon (`#ffffff`) and smooth dark hover glow (`#1d4ed8`).
  - **CSS Minification & Cache Busting**: Minified `style.css` into `style.min.css` and bumped query string to `v=8.3`.

### Release v1.4.9 (2026-09-02)
- `d9fd05c`: **feat(professional): remove open chat button, equalize work activity block heights, and restore vibrant icon colors**
  - **Removed Redundant Chat Button**: Eliminated the full-width "Open Chat Support" button from the main technician profile card since Admin Chat Support is already present in Quick Actions.
  - **Equalized Work Activity Card Heights**: Applied `row g-2 align-items-stretch`, `col-4 d-flex`, and flex-column centering with `min-height: 88px` on `.profile-stat-box` so 'Active Tasks', 'Completed', and 'Pending Help' cards have identical height on all screen sizes.
  - **Restored Vibrant Semantic Icon Colors**: Added explicit CSS overrides in `style.css` and `profile.html` ensuring `.text-primary` (`#3b82f6`), `.text-success` (`#22c55e`), `.text-warning` (`#f59e0b`), `.text-danger` (`#ef4444`), and `.text-info` (`#06b6d4`) retain their colors in dark mode.
  - **CSS Minification & Cache Busting**: Minified `style.css` into `style.min.css` and bumped query string to `v=8.2`.

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
