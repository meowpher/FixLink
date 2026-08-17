"""
FixLink Responsive Audit — appends the full responsive CSS system to style.css.
Safe: only appends, never overwrites existing rules.
"""

CSS_BLOCK = '''

/* ================================================================
   FIXLINK RESPONSIVE SYSTEM — v5.0
   Full audit per Steps 1–7 of the Responsive Design Spec.
   ALL rules are scoped so they only OVERRIDE, never break, desktop.
   ================================================================ */

/* ────────────────────────────────────────────────────────────────
   STEP 1 — RESPONSIVE TOKENS
   ──────────────────────────────────────────────────────────────── */
:root {
    /* Breakpoint reference (comment-only — use in @media directly) */
    /* --bp-xs: 375px  --bp-sm: 480px  --bp-md: 768px              */
    /* --bp-lg: 1024px --bp-xl: 1280px --bp-2xl: 1536px            */

    /* Fluid spacing tokens */
    --space-section:   clamp(2rem,   6vw, 6rem);
    --space-component: clamp(1rem,   3vw, 2rem);
    --space-gap:       clamp(0.75rem,2vw, 1.5rem);

    /* Fluid type scale */
    --text-h1:   clamp(1.75rem, 4vw + 1rem,  3.5rem);
    --text-h2:   clamp(1.4rem,  3vw + 0.8rem, 2.5rem);
    --text-h3:   clamp(1.1rem,  2vw + 0.6rem, 1.75rem);
    --text-body: clamp(0.9rem,  1vw + 0.5rem, 1.1rem);

    /* Container */
    --container-max:     1280px;
    --container-padding: clamp(1rem, 5vw, 2rem);
}

/* ────────────────────────────────────────────────────────────────
   STEP 2 — GLOBAL OVERFLOW & BASE FIXES (all widths)
   ──────────────────────────────────────────────────────────────── */

/* Root overflow guard */
html { overflow-x: hidden; max-width: 100%; }

/* Images always responsive */
img, video, svg, iframe, embed {
    max-width: 100%;
}
img { height: auto; }

/* Flex blowout prevention — apply globally */
.d-flex > *, .row > * {
    min-width: 0;
}

/* Word-break on any dynamic text container */
.card-title, .card-text, .badge, .alert,
h1, h2, h3, h4, h5, h6 {
    overflow-wrap: break-word;
    word-break: break-word;
}

/* Line-height polish */
h1, h2, h3, h4, h5, h6 { line-height: 1.2; }
p, li { line-height: 1.65; }

/* Fluid type on headings (desktop-safe: clamp floor is the small value) */
h1, .h1 { font-size: var(--text-h1); }
h2, .h2 { font-size: var(--text-h2); }
h3, .h3 { font-size: var(--text-h3); }

/* Form input minimum 16px (prevents iOS zoom) */
input, select, textarea, .form-control, .form-select {
    font-size: max(1rem, 16px);
}

/* Touch targets — min 44×44px on all interactive elements */
button, a, .btn, [role="button"],
.nav-link, .dropdown-item {
    min-height: 44px;
    display: inline-flex;
    align-items: center;
}

/* Undo min-height on purely structural anchors/buttons */
.dropdown-menu .dropdown-item { min-height: 36px; }

/* Aspect ratio on card images */
.card-img-top {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
}

/* Table scroll wrapper (applied globally — safe on desktop too) */
.table-responsive {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    max-width: 100%;
}

/* ────────────────────────────────────────────────────────────────
   STEP 3 — TABLETS  @media (max-width: 1023px)
   Refined version replacing the existing block with specificity wins
   ──────────────────────────────────────────────────────────────── */
@media (max-width: 1023px) {

    /* Navbar pill layout — ensure it doesn\'t overflow */
    .vyas-navbar {
        left: 8px;
        right: 8px;
        top: 8px;
    }

    /* Body top padding matches new navbar height */
    body { padding-top: 80px; }

    /* Dashboard grids — 2-col on tablet */
    .dashboard-grid,
    .stats-grid {
        grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
        gap: var(--space-gap);
    }

    /* Prevent card padding blowout on tablet */
    .card { padding: 1.25rem !important; }

    /* Modals — don\'t let them get too wide */
    .modal-dialog {
        max-width: min(95%, 600px) !important;
        margin: 1rem auto;
    }

    /* Main content breathing room */
    .main-content {
        padding: var(--space-component);
        padding-top: 80px;
    }
}

/* ────────────────────────────────────────────────────────────────
   STEP 4 — PHONES  @media (max-width: 767px)
   ──────────────────────────────────────────────────────────────── */
@media (max-width: 767px) {

    /* ── GLOBAL PHONE BASE ── */
    body {
        padding-top: 70px;
        font-size: var(--text-body);
    }

    /* Every section gets breathing room */
    section, .section, [class*="-section"] {
        padding-inline: 1rem;
    }

    /* Containers: full width with consistent gutter */
    .container, .container-fluid, .container-sm,
    .container-md, .container-lg, .container-xl {
        padding-inline: 1rem;
        max-width: 100%;
    }

    /* Single-column grids */
    .dashboard-grid, .stats-grid, .smart-grid,
    [class*="row-cols"] {
        grid-template-columns: 1fr !important;
    }

    /* Bootstrap rows: allow wrapping */
    .row { flex-wrap: wrap; }

    /* ── NAVBAR ── */
    .vyas-navbar {
        left: 0;
        right: 0;
        top: 0;
        border-radius: 0;
        padding: 0 0.75rem;
        z-index: 90 !important;   /* sidebar/backdrop sit above */
    }

    body { padding-top: 60px; }

    /* ── CARDS ── */
    .card {
        padding: 1rem !important;
        margin-bottom: 0.75rem;
        overflow: hidden;
    }

    /* Card actions — wrap if needed */
    .card .d-flex.gap-2,
    .card .btn-group,
    .card-footer .d-flex {
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    /* Full-width buttons on small screens */
    .card .btn,
    .card-footer .btn {
        width: 100%;
        justify-content: center;
    }

    /* ── FORMS ── */
    .form-control, .form-select, .input-group {
        width: 100% !important;
        font-size: 16px; /* prevents iOS zoom */
    }

    /* Multi-col form layouts → single column */
    form .row > [class*="col-"] {
        flex: 0 0 100%;
        max-width: 100%;
    }

    /* Labels above inputs */
    .form-label {
        display: block;
        margin-bottom: 0.25rem;
    }

    /* Submit buttons — full width */
    form [type="submit"],
    form .btn-primary,
    form .btn-submit {
        width: 100%;
        justify-content: center;
    }

    /* ── TABLES ── */
    .table-responsive,
    .table-wrapper {
        border: 0;
        box-shadow: none;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    /* Prevent table cells from forcing extreme width */
    .table td, .table th {
        white-space: nowrap;
        font-size: 0.8rem;
        padding: 0.5rem 0.75rem;
    }

    /* ── MODALS ── */
    .modal-dialog {
        max-width: 100% !important;
        width: 100%;
        margin: 0;
        height: 100dvh;
    }

    .modal-content {
        border-radius: 0 !important;
        height: 100dvh;
        overflow-y: auto;
    }

    /* Close button always reachable */
    .modal-header .btn-close {
        position: sticky;
        top: 0;
        z-index: 10;
    }

    /* ── TYPOGRAPHY ── */
    h1, .h1 { font-size: clamp(1.5rem, 6vw, 2rem); }
    h2, .h2 { font-size: clamp(1.25rem, 5vw, 1.75rem); }
    h3, .h3 { font-size: clamp(1.1rem, 4vw, 1.4rem); }
    p, .text-body { font-size: clamp(0.875rem, 3.5vw, 1rem); }

    /* Prevent long text from overflowing narrow cards */
    .card-title, .fw-bold, .fw-semibold {
        overflow-wrap: break-word;
        word-break: break-word;
    }

    /* ── BUTTONS / TOUCH ── */
    .btn {
        min-height: 44px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }

    /* Icon-only buttons */
    .btn.btn-icon,
    .btn-sm.icon-btn,
    .mc-btn {
        min-width: 44px;
        min-height: 44px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    /* ── STAT CARDS ── */
    .stat-card {
        padding: 1rem;
    }

    .stat-card .display-4,
    .stat-card .fs-1 {
        font-size: clamp(1.5rem, 8vw, 2.5rem) !important;
    }

    /* ── HERO / BANNER ── */
    .faculty-hero,
    .admin-sidebar,
    [class*="-hero"] {
        height: auto !important;
        min-height: unset !important;
        padding: 1.25rem;
        border-radius: 12px !important;
    }

    /* ── FLEX LAYOUTS ── */
    /* Horizontal action rows → wrap */
    .d-flex.justify-content-between,
    .d-flex.justify-content-end {
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    /* Page header (title + actions) */
    .page-header,
    .tickets-header,
    .section-header {
        flex-direction: column;
        align-items: flex-start !important;
        gap: 0.75rem;
    }

    /* ── CHART CONTAINERS ── */
    canvas, .chart-container, [id*="Chart"] {
        max-width: 100% !important;
        height: auto !important;
    }

    /* ── STATUS MAP ── */
    .map-panel, .floor-map-container {
        min-height: 350px;
        overflow-x: auto;
    }

    /* ── TIMETABLE ── */
    .timetable-grid {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        font-size: 0.75rem;
    }

    /* ── DROPDOWNS ── */
    .dropdown-menu {
        min-width: min(280px, 90vw);
        max-width: 90vw;
    }

    /* Notification dropdown — full width on phone */
    .notification-dropdown {
        min-width: min(320px, 92vw) !important;
        width: 92vw !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
    }

    /* ── FOOTER ── */
    footer .row > [class*="col-"],
    .footer-grid > * {
        flex: 0 0 100%;
        max-width: 100%;
        text-align: center;
    }

    footer a, footer li {
        padding: 8px 0;
        display: block;
    }
}

/* ────────────────────────────────────────────────────────────────
   STEP 5 — EXTRA SMALL PHONES  @media (max-width: 374px)
   ──────────────────────────────────────────────────────────────── */
@media (max-width: 374px) {

    /* Even tighter gutters on 320px phones */
    .container, .container-fluid {
        padding-inline: 0.75rem;
    }

    h1, .h1 { font-size: 1.4rem; }
    h2, .h2 { font-size: 1.2rem; }

    /* Stack badge + title in mc-card */
    .mc-top {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }

    /* Tighten card padding */
    .mc-card {
        padding: 0.75rem !important;
    }
}

/* ────────────────────────────────────────────────────────────────
   STEP 6 — LARGE SCREENS  @media (min-width: 1280px)
   Prevent content from stretching too wide
   ──────────────────────────────────────────────────────────────── */
@media (min-width: 1280px) {
    .container, .container-xl, .container-lg {
        max-width: var(--container-max);
    }
}

/* ────────────────────────────────────────────────────────────────
   STEP 7 — Z-INDEX AUDIT (global, all breakpoints)
   ──────────────────────────────────────────────────────────────── */

/* Ensure stacking never breaks across the app */
.vyas-navbar          { z-index: 1030; }    /* desktop */
.dropdown-menu        { z-index: 1050; }
.modal-backdrop       { z-index: 1040; }
.modal                { z-index: 1055; }
.mobile-backdrop      { z-index: 999; }     /* mobile sidebar backdrop */
.mobile-sidebar       { z-index: 1000; }    /* mobile sidebar panel */
.mobile-hamburger     { z-index: 1100; }    /* always on top on mobile */

/* On mobile, navbar goes BELOW sidebar chrome */
@media (max-width: 767px) {
    .vyas-navbar { z-index: 90 !important; }
}

/* ────────────────────────────────────────────────────────────────
   STEP 8 — SPECIFIC COMPONENT PATCHES (audit findings)
   ──────────────────────────────────────────────────────────────── */

/* 1. Main content padding-top — mobile sidebar replaces navbar */
@media (max-width: 767px) {
    .main-content {
        padding-top: 72px;
        padding-inline: 0.75rem;
    }
}

/* 2. Navbar brand clip prevention */
.navbar-brand {
    min-width: 0;
    flex-shrink: 1;
    overflow: hidden;
}

.brand-text-wrapper {
    overflow: hidden;
}

.brand-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* 3. Nav links — flex blowout guard */
.navbar-nav .nav-link {
    min-width: 0;
    white-space: nowrap;
}

/* 4. Profile dropdown — don\'t overflow viewport on mobile */
@media (max-width: 767px) {
    .profile-dropdown {
        min-width: min(290px, 90vw);
        right: 0;
        left: auto;
    }
}

/* 5. Stat cards — text overflow on very small screens */
.stat-number, .stat-value, .kpi-value {
    overflow-wrap: break-word;
    word-break: break-word;
    min-width: 0;
}

/* 6. Map / Floor plan — always scrollable on small screens */
@media (max-width: 767px) {
    .floor-map-wrapper,
    .map-canvas-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    .room-grid,
    .floor-grid {
        min-width: 600px; /* keep map usable but inside a scroll wrapper */
    }
}

/* 7. Chat interface — messages never overflow */
.chat-message, .message-bubble {
    max-width: min(80%, 500px);
    overflow-wrap: break-word;
    word-break: break-word;
}

@media (max-width: 767px) {
    .chat-message, .message-bubble {
        max-width: 90%;
        font-size: 0.875rem;
    }
}

/* 8. Login / Auth cards — full width on mobile */
@media (max-width: 767px) {
    .login-card, .auth-card, .form-panel {
        width: 100% !important;
        max-width: 100%;
        margin: 0;
        border-radius: 12px;
    }
}

/* 9. Timetable form — collapse on mobile */
@media (max-width: 767px) {
    .tt-form-container .row > [class*="col-"] {
        flex: 0 0 100%;
        max-width: 100%;
        margin-bottom: 0.75rem;
    }
}

/* 10. Analytics charts — cap height on mobile */
@media (max-width: 767px) {
    .chart-card canvas {
        max-height: 220px !important;
    }
}

/* 11. Faculty portal hero stats */
@media (max-width: 767px) {
    .hero-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
    }

    .stat-mini-card {
        min-width: 0;
    }
}

/* 12. Action buttons in table rows — min touch target */
.btn-sm {
    min-height: 36px;
    padding: 0.3rem 0.6rem;
}

@media (max-width: 767px) {
    .btn-sm {
        min-height: 44px;
        padding: 0.5rem 0.75rem;
        font-size: 0.85rem;
    }
}

/* 13. Badge overflow fix */
.badge {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
}

/* 14. Responsive padding on section containers */
@media (max-width: 767px) {
    .p-4 { padding: 1rem !important; }
    .p-5 { padding: 1.25rem !important; }
    .px-4 { padding-inline: 1rem !important; }
    .px-5 { padding-inline: 1.25rem !important; }
    .py-4 { padding-block: 1rem !important; }
    .py-5 { padding-block: 1.25rem !important; }
}

/* 15. Prevent horizontal overflow from any fixed-position element */
@media (max-width: 767px) {
    [style*="width: 100vw"],
    [style*="width:100vw"] {
        width: 100% !important;
    }
}

/* ────────────────────────────────────────────────────────────────
   END — FIXLINK RESPONSIVE SYSTEM v5.0
   ──────────────────────────────────────────────────────────────── */
'''

css_path = r"d:\FixLink-V1\app\static\css\style.css"

with open(css_path, "a", encoding="utf-8") as f:
    f.write(CSS_BLOCK)

# Count lines added
print(f"Appended {len(CSS_BLOCK.splitlines())} lines to style.css")

# Verify file size
import os
size_kb = os.path.getsize(css_path) / 1024
print(f"New file size: {size_kb:.1f} KB")
print("Done.")
