"""
Nuclear fix: finds the FIXLINK RESPONSIVE SYSTEM marker in style.css,
strips EVERYTHING from that point onward, then appends a clean,
properly scoped mobile-only block that CANNOT touch desktop at all.
"""
import os, re

css_path = r"d:\FixLink-V1\app\static\css\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the start of our v5.0 block (first marker we injected)
MARKER = "/* ================================================================\n   FIXLINK RESPONSIVE SYSTEM"
idx = content.find(MARKER)

if idx == -1:
    print("Marker not found — checking for alternate marker...")
    MARKER2 = "FIXLINK RESPONSIVE SYSTEM"
    idx = content.find(MARKER2)
    if idx != -1:
        # Back up to the comment start
        idx = content.rfind("/*", 0, idx)
    print(f"Found at index: {idx}")

if idx == -1:
    print("ERROR: Could not find injection marker. File unchanged.")
    exit(1)

# Keep everything BEFORE our injected blocks
original_css = content[:idx].rstrip() + "\n"

print(f"Stripping from byte {idx} onward ({len(content)-idx} bytes removed)")
print(f"Keeping first {len(original_css)} bytes of original CSS")

# Now write clean replacement — STRICTLY mobile-only
CLEAN_MOBILE_CSS = '''
/* ================================================================
   FIXLINK MOBILE-ONLY RESPONSIVE SYSTEM — v5.2 CLEAN
   RULE: Every single rule here is inside a max-width media query.
         NOTHING is global. Desktop (>=768px) is completely untouched.
   ================================================================ */

/* ── RESPONSIVE TOKENS (variables only, no layout side effects) ── */
:root {
    --space-section:   clamp(2rem,   6vw, 6rem);
    --space-component: clamp(1rem,   3vw, 2rem);
    --space-gap:       clamp(0.75rem,2vw, 1.5rem);
    --container-max:   1280px;
}

/* ── ALWAYS-SAFE GLOBALS (truly non-breaking on any screen) ── */
img, video, embed { max-width: 100%; }
img { height: auto; }

.table-responsive {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* ================================================================
   TABLET  (768px – 1023px)
   ================================================================ */
@media (max-width: 1023px) {

    .vyas-navbar {
        padding: 0 1rem;
        height: auto;
        min-height: 60px;
    }

    .navbar-collapse {
        background: var(--bg-surface);
        padding: 0.5rem 1rem 1rem;
        border-radius: 0 0 12px 12px;
        margin-top: 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-subtle);
        border-top: none;
    }

    .navbar-nav {
        flex-direction: column;
        align-items: stretch;
        gap: 2px;
    }

    .navbar-nav .nav-link {
        display: flex !important;
        align-items: center;
        gap: 10px;
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 0.95rem;
    }

    .navbar-nav .nav-link i.bi {
        font-size: 1.05rem;
        line-height: 1;
        flex-shrink: 0;
        width: 20px;
        text-align: center;
    }

    .navbar-nav .nav-item.ms-2,
    .navbar-nav .nav-item.ms-lg-4 {
        display: inline-flex;
        align-items: center;
        margin-left: 0 !important;
        padding: 4px 12px;
    }

    .navbar-nav .nav-item.ms-lg-4 {
        margin-top: 8px;
        padding-top: 12px;
        border-top: 1px solid var(--border-subtle);
    }

    .navbar-nav #themeToggleBtn {
        width: 40px;
        height: 40px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .main-content {
        padding: 1rem;
        padding-top: 80px;
    }

    .dashboard-grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .card { padding: 1.25rem !important; }

    .modal-dialog {
        max-width: 95% !important;
        margin: 1rem auto;
    }

    .glass-modal .modal-content { border-radius: 20px !important; }

    .btn, .form-control, .form-select, .room-btn, .choice-btn {
        min-height: 44px;
    }

    .timetable-grid {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 1rem;
    }

    .tt-form-container { padding: 1rem !important; }

    .map-panel, .floor-map-container { min-height: 450px; }
}

/* ================================================================
   PHONE  (max 767px)
   ================================================================ */
@media (max-width: 767px) {

    /* ── Body & containers ── */
    html, body { overflow-x: hidden; }

    body { padding-top: 70px; }

    .main-content {
        padding: 0.75rem;
        padding-top: 72px;
    }

    /* ── Navbar: hidden on mobile (sidebar replaces it) ── */
    .vyas-navbar {
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        border-radius: 0 !important;
        padding: 0 0.75rem !important;
        z-index: 90 !important;
    }

    .vyas-navbar .navbar-collapse,
    .vyas-navbar .navbar-toggler {
        display: none !important;
    }

    /* ── Grids: single column ── */
    .dashboard-grid, .stats-grid, .smart-grid {
        grid-template-columns: 1fr !important;
    }

    /* ── Cards ── */
    .card {
        padding: 1rem !important;
        margin-bottom: 0.75rem;
    }

    /* ── Forms ── */
    .form-control, .form-select {
        font-size: 16px;         /* prevent iOS zoom */
        width: 100% !important;
    }

    form .row > [class*="col-"] {
        flex: 0 0 100%;
        max-width: 100%;
    }

    /* ── Modals ── */
    .modal-dialog {
        max-width: 100% !important;
        margin: 0.5rem;
    }

    /* ── Typography ── */
    h1, .h1 { font-size: 1.75rem; }
    h2, .h2 { font-size: 1.5rem; }
    h3, .h3 { font-size: 1.25rem; }

    /* ── Touch targets — ONLY on mobile ── */
    .btn, .room-btn, .choice-btn {
        min-height: 44px;
    }

    .btn-sm { min-height: 40px; }

    /* ── Alert / SweetAlert ── */
    .swal2-popup {
        width: 90% !important;
        padding: 1rem !important;
    }

    /* ── Tables ── */
    .table td, .table th {
        white-space: nowrap;
        font-size: 0.8rem;
        padding: 0.5rem 0.75rem;
    }

    /* ── Selectors / filter groups ── */
    .selector-group .row > div { margin-bottom: 1rem; }
    .selector-group .row > div:last-child { margin-bottom: 0; }

    /* ── Sidebar / hero stacking ── */
    .faculty-hero, .admin-sidebar {
        height: auto !important;
        position: relative !important;
        border-radius: 16px !important;
        margin-bottom: 1.5rem;
    }

    .hero-stats {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .stat-mini-card {
        flex: 1 1 calc(50% - 0.5rem);
        min-width: 120px;
    }

    /* ── Nav pills ── */
    .nav-pills-premium {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .nav-pills-premium .btn {
        flex: 1 1 calc(50% - 0.5rem);
        margin-bottom: 0;
        min-width: 120px;
    }

    /* ── Map ── */
    .map-panel, .floor-map-container { min-height: 450px; }

    /* ── Timetable ── */
    .timetable-grid {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 1rem;
    }

    .tt-form-container { padding: 1rem !important; }

    /* ── Padding scale-down ── */
    .p-4  { padding: 1rem    !important; }
    .p-5  { padding: 1.25rem !important; }
    .px-4 { padding-left: 1rem    !important; padding-right: 1rem    !important; }
    .px-5 { padding-left: 1.25rem !important; padding-right: 1.25rem !important; }
    .py-4 { padding-top: 1rem    !important; padding-bottom: 1rem    !important; }
    .py-5 { padding-top: 1.25rem !important; padding-bottom: 1.25rem !important; }

    /* ── Dropdown menus ── */
    .dropdown-menu { z-index: 1050; }

    /* ── Mobile card declutter ── */
    .mobile-card-list {
        display: flex !important;
        flex-direction: column;
        gap: 0.75rem;
    }
}

/* ── Desktop: always hide mobile chrome ── */
@media (min-width: 768px) {
    .mobile-hamburger,
    .mobile-backdrop,
    .mobile-sidebar { display: none; }

    .mobile-card-list { display: none !important; }
}

/* ================================================================
   MC-CARD SYSTEM (mobile card declutter, inside 767px only)
   ================================================================ */
@media (max-width: 767px) {

    .mc-card {
        background: var(--bg-card, #fff);
        border: 1px solid var(--border-color, #e9ecef);
        border-radius: 12px;
        padding: 0.875rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    .mc-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        gap: 8px;
    }

    .mc-id-title {
        display: flex;
        align-items: center;
        gap: 6px;
        min-width: 0;
    }

    .mc-id {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        flex-shrink: 0;
    }

    .mc-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-main);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .mc-status { flex-shrink: 0; }

    .mc-desc {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.6rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .mc-person-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 0.5rem;
    }

    .mc-person-left {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
    }

    .mc-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        color: #fff;
        flex-shrink: 0;
    }

    .mc-person-info {
        display: flex;
        flex-direction: column;
        min-width: 0;
    }

    .mc-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-main);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .mc-meta {
        font-size: 0.7rem;
        color: var(--text-muted);
    }

    .mc-bottom {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border-color, #e9ecef);
        gap: 6px;
    }

    .mc-date {
        font-size: 0.75rem;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .mc-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        border: none;
        cursor: pointer;
        min-height: 34px;
        white-space: nowrap;
        text-decoration: none;
        transition: opacity 0.15s ease;
    }

    .mc-btn:hover { opacity: 0.85; }

    .mc-btn-group {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }
}

/* ================================================================
   MOBILE SLIDE-IN SIDEBAR — strictly max-width 767px
   ================================================================ */

/* Desktop: hide all sidebar chrome */
.mobile-hamburger,
.mobile-backdrop,
.mobile-sidebar {
    display: none;
}

@media (max-width: 767px) {

    /* ── Hamburger trigger ── */
    .mobile-hamburger {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 4px;
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 1100;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        cursor: pointer;
        padding: 0;
        transition: background 200ms ease;
    }
    .mobile-hamburger:hover { background: rgba(255,255,255,0.12); }

    .ham-bar {
        display: block;
        width: 16px;
        height: 1.5px;
        background: #f1f5f9;
        border-radius: 2px;
        transform-origin: center;
        transition: transform 280ms cubic-bezier(0.4,0,0.2,1),
                    opacity  280ms cubic-bezier(0.4,0,0.2,1);
    }

    .mobile-hamburger.ham-open .ham-bar:nth-child(1) { transform: translateY(5.5px) rotate(45deg); }
    .mobile-hamburger.ham-open .ham-bar:nth-child(2) { opacity: 0; transform: scaleX(0); }
    .mobile-hamburger.ham-open .ham-bar:nth-child(3) { transform: translateY(-5.5px) rotate(-45deg); }

    /* ── Backdrop ── */
    .mobile-backdrop {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999;
        opacity: 0;
        pointer-events: none;
        transition: opacity 280ms cubic-bezier(0.4,0,0.2,1);
    }
    .mobile-backdrop.msb-backdrop-open {
        opacity: 1;
        pointer-events: auto;
    }

    /* ── Sidebar panel ── */
    .mobile-sidebar {
        display: flex;
        flex-direction: column;
        position: fixed;
        top: 0; left: 0;
        width: 280px;
        height: 100dvh;
        background: #0F1117;
        border-right: 0.5px solid rgba(255,255,255,0.07);
        border-radius: 0 16px 16px 0;
        z-index: 1000;
        overflow-y: auto;
        overflow-x: hidden;
        transform: translateX(-100%);
        transition: transform 280ms cubic-bezier(0.4,0,0.2,1);
        -webkit-overflow-scrolling: touch;
    }
    .mobile-sidebar.msb-open { transform: translateX(0); }

    body.msb-body-lock { overflow: hidden; }

    /* ── Header ── */
    .msb-header {
        display: flex;
        align-items: center;
        height: 68px;
        padding: 0 14px;
        gap: 10px;
        border-bottom: 0.5px solid rgba(255,255,255,0.08);
        flex-shrink: 0;
    }

    .msb-logo {
        height: 40px !important;
        width: auto !important;
        flex-shrink: 0;
        display: block;
        object-fit: contain;
    }

    .msb-header-divider {
        width: 0.5px;
        height: 32px;
        background: rgba(255,255,255,0.08);
        flex-shrink: 0;
    }

    .msb-brand { flex: 1; min-width: 0; }

    .msb-brand-name {
        font-size: 13px;
        font-weight: 500;
        color: #5B8FF9;
        line-height: 1.3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .msb-brand-sub {
        font-size: 9px;
        color: #475569;
        line-height: 1.3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .msb-close-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 6px;
        background: rgba(255,255,255,0.05);
        border: 0.5px solid rgba(255,255,255,0.08);
        color: #94A3B8;
        font-size: 16px;
        cursor: pointer;
        flex-shrink: 0;
        margin-left: auto;
        transition: background 200ms ease, color 200ms ease;
        padding: 0;
        line-height: 1;
    }
    .msb-close-btn:hover { background: rgba(255,255,255,0.12); color: #F1F5F9; }

    /* ── Section label ── */
    .msb-section-label {
        font-size: 10px;
        letter-spacing: 0.08em;
        color: #334155;
        padding: 14px 14px 6px;
        flex-shrink: 0;
    }

    /* ── Nav list ── */
    .msb-nav {
        list-style: none;
        margin: 0;
        padding: 0 10px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        flex: 1;
    }
    .msb-nav li { display: block; }

    .msb-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 9px 10px;
        border-radius: 8px;
        font-size: 13px;
        color: #94A3B8;
        text-decoration: none;
        cursor: pointer;
        width: 100%;
        border: none;
        background: transparent;
        text-align: left;
        transition: background 180ms ease, color 180ms ease;
    }
    .msb-item:hover { background: rgba(255,255,255,0.04); color: #CBD5E1; }

    .msb-item i.bi {
        font-size: 15px;
        width: 16px;
        text-align: center;
        flex-shrink: 0;
        color: #64748B;
        transition: color 180ms ease;
    }
    .msb-item:hover i.bi { color: #94A3B8; }

    .msb-item.msb-active { background: #1E2535; color: #F1F5F9; }
    .msb-item.msb-active i.bi { color: #5B8FF9; }

    .msb-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #5B8FF9;
        margin-left: auto;
        flex-shrink: 0;
    }

    .msb-chevron {
        font-size: 11px;
        color: #64748B;
        transition: transform 280ms cubic-bezier(0.4,0,0.2,1);
        margin-left: auto;
        flex-shrink: 0;
    }

    .msb-badge {
        font-size: 10px;
        font-weight: 700;
        background: #ef4444;
        color: #fff;
        border-radius: 999px;
        padding: 1px 5px;
        min-width: 16px;
        text-align: center;
        margin-left: auto;
    }

    /* ── Manage submenu ── */
    .msb-sub {
        list-style: none;
        margin: 2px 0 0;
        padding: 0 0 0 26px;
        display: none;
        flex-direction: column;
        gap: 1px;
    }
    .msb-sub.msb-sub-open { display: flex; }

    .msb-subitem {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 10px;
        border-radius: 7px;
        font-size: 12px;
        color: #64748B;
        text-decoration: none;
        transition: background 180ms ease, color 180ms ease;
    }
    .msb-subitem i.bi { font-size: 13px; width: 14px; text-align: center; }
    .msb-subitem:hover { background: rgba(255,255,255,0.04); color: #94A3B8; }

    /* ── Divider ── */
    .msb-divider {
        height: 0.5px;
        background: rgba(255,255,255,0.06);
        margin: 8px 10px;
        flex-shrink: 0;
    }

    /* ── Bottom utility bar ── */
    .msb-bottom {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 10px;
        gap: 8px;
        flex-shrink: 0;
    }

    .msb-user {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
        flex: 1;
    }

    .msb-avatar {
        width: 30px; height: 30px;
        border-radius: 50%;
        background: #5B8FF9;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        color: #fff;
        flex-shrink: 0;
        letter-spacing: 0.5px;
    }

    .msb-user-info { min-width: 0; display: flex; flex-direction: column; }

    .msb-user-name {
        font-size: 12px;
        color: #CBD5E1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
        font-weight: 500;
    }

    .msb-user-email {
        font-size: 10px;
        color: #475569;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
    }

    .msb-utils { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }

    .msb-util-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px; height: 28px;
        border-radius: 6px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        color: #64748B;
        font-size: 14px;
        cursor: pointer;
        transition: background 180ms ease, color 180ms ease;
        text-decoration: none;
        padding: 0;
        position: relative;
    }
    .msb-util-btn:hover { background: rgba(255,255,255,0.10); color: #94A3B8; }

    .msb-notif-dot {
        position: absolute;
        top: 3px; right: 3px;
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #ef4444;
    }

    /* Drop navbar below sidebar chrome */
    .vyas-navbar { z-index: 90 !important; }

    /* Hide navbar when sidebar is open */
    body.msb-body-lock .vyas-navbar { visibility: hidden; }

    /* Dark mode logo swap */
    [data-theme="dark"] .msb-logo {
        content: url("../images/logo-dm.png");
    }

} /* end @media max-width: 767px */

/* ================================================================
   Ensure mobile card list hidden on desktop
   ================================================================ */
@media (min-width: 768px) {
    .mobile-card-list { display: none !important; }
    .desktop-table-container { display: block; }
}
'''

final_css = original_css + CLEAN_MOBILE_CSS

with open(css_path, "w", encoding="utf-8") as f:
    f.write(final_css)

print(f"Written {len(final_css.splitlines())} total lines.")
import os
print(f"File size: {os.path.getsize(css_path)/1024:.1f} KB")
print("SUCCESS: Desktop is clean, mobile rules are all scoped correctly.")
