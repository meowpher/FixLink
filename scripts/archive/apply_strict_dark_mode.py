import os
import re

css_path = r'd:\FixLink-V1\app\static\css\style.css'

css = """
/* ============================================
   STRICT DARK MODE ECOSYSTEM OVERRIDE
   ============================================ */
:root[data-theme="dark"],
[data-theme="dark"] {
    /* Core Design Tokens */
    --void: #040404 !important;
    --base: #080809 !important;
    --surface: #0F0F11 !important;
    --card: #161618 !important;
    --raised: #222226 !important;
    
    --text-primary: #EDEDF0 !important;
    --smoke-white: #C8C8D0 !important;
    --sub-text: #8A8A96 !important;
    --muted: #383840 !important;
    
    --ice-hint: #C8D8E8 !important;
    
    --border: rgba(255,255,255,0.06) !important;
    --border-hover: rgba(255,255,255,0.12) !important;

    /* Semantic Variable Remapping (Overrides existing) */
    --bg-main: var(--base) !important;
    --bg-base: var(--base) !important;
    --bg-card: var(--card) !important;
    --bg-surface: var(--surface) !important;
    --bg-overlay: var(--raised) !important;
    --bg-card-hover: var(--raised) !important;
    
    --text-main: var(--text-primary) !important;
    --text-body: var(--smoke-white) !important;
    --text-muted: var(--sub-text) !important;
    --text-disabled: var(--muted) !important;
    --text-secondary: var(--sub-text) !important;
    
    --border-color: var(--border) !important;
    --border-default: var(--border) !important;
    --border-subtle: var(--border) !important;
    
    --nav-bg: var(--surface) !important;
    --modal-bg: var(--card) !important;
    --input-bg: var(--surface) !important;
    --input-border: var(--border) !important;
    --input-text: var(--text-primary) !important;
    
    --mitwpu-blue: var(--ice-hint) !important;
    --mitwpu-blue-dark: var(--ice-hint) !important;
    --mitwpu-blue-light: var(--ice-hint) !important;
    --accent-primary: var(--ice-hint) !important;
    --accent-primary-hover: var(--smoke-white) !important;
    --accent-primary-active: var(--text-primary) !important;
    --accent-primary-focus: var(--ice-hint) !important;
    
    --success-color: var(--ice-hint) !important;
    --warning-color: var(--ice-hint) !important;
    --danger-color: var(--ice-hint) !important;
    --info-color: var(--ice-hint) !important;
    
    --mitwpu-red: var(--muted) !important;
    --mitwpu-red-dark: var(--muted) !important;
    --lab-teal: var(--ice-hint) !important;
    --lab-teal-dark: var(--ice-hint) !important;
    
    --shadow-sm: 0 2px 4px var(--void) !important;
    --shadow-md: 0 4px 12px var(--void) !important;
    --shadow-lg: 0 8px 24px var(--void) !important;
}

/* Base Body and Void Backgrounds */
html[data-theme="dark"], 
[data-theme="dark"] body,
[data-theme="dark"] .main-content {
    background-color: var(--base) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .vyas-hero {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border) !important;
}

/* Safe Area / Void implementations */
[data-theme="dark"] .mobile-bottom-nav,
[data-theme="dark"] .bottom-sheet,
[data-theme="dark"] .offcanvas,
[data-theme="dark"] .sidebar {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
    box-shadow: 0 -4px 16px var(--void) !important;
}

[data-theme="dark"] body::after {
    /* Mobile safe area background fix */
    content: '';
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: env(safe-area-inset-bottom);
    background-color: var(--void) !important;
    z-index: 9999;
}

/* Navbars */
[data-theme="dark"] .vyas-navbar,
[data-theme="dark"] .navbar {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
    box-shadow: var(--shadow-md) !important;
}

/* Cards & Modals */
[data-theme="dark"] .card,
[data-theme="dark"] .stat-card,
[data-theme="dark"] .filter-card,
[data-theme="dark"] .tickets-card,
[data-theme="dark"] .login-card,
[data-theme="dark"] .modal-content,
[data-theme="dark"] .dropdown-menu,
[data-theme="dark"] .profile-dropdown,
[data-theme="dark"] .mc-card {
    background-color: var(--card) !important;
    border-color: var(--border) !important;
    box-shadow: var(--shadow-md) !important;
    color: var(--text-primary) !important;
}

/* Raised Elements (Hover states, menus) */
[data-theme="dark"] .card:hover,
[data-theme="dark"] .mc-card:hover,
[data-theme="dark"] .dropdown-item:hover,
[data-theme="dark"] .list-group-item:hover {
    background-color: var(--raised) !important;
    border-color: var(--border-hover) !important;
}

/* Typography Overrides */
[data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3, 
[data-theme="dark"] h4, [data-theme="dark"] h5, [data-theme="dark"] h6,
[data-theme="dark"] .h1, [data-theme="dark"] .h2, [data-theme="dark"] .h3, 
[data-theme="dark"] .h4, [data-theme="dark"] .h5, [data-theme="dark"] .h6,
[data-theme="dark"] .text-dark,
[data-theme="dark"] strong, [data-theme="dark"] b {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .text-muted,
[data-theme="dark"] .text-secondary,
[data-theme="dark"] .small,
[data-theme="dark"] small,
[data-theme="dark"] .mc-date,
[data-theme="dark"] .mc-meta {
    color: var(--sub-text) !important;
}

/* Primary CTAs & Active States (Ice-Hint ONLY) */
[data-theme="dark"] .btn-primary,
[data-theme="dark"] .nav-link.active,
[data-theme="dark"] .active > .page-link,
[data-theme="dark"] .badge-primary,
[data-theme="dark"] .text-primary {
    background-color: var(--ice-hint) !important;
    color: var(--void) !important;
    border-color: var(--ice-hint) !important;
}

[data-theme="dark"] .btn-primary:hover {
    background-color: var(--text-primary) !important; /* brighter on hover */
    color: var(--void) !important;
}

[data-theme="dark"] .btn-outline-primary {
    color: var(--ice-hint) !important;
    border-color: var(--ice-hint) !important;
    background: transparent !important;
}

[data-theme="dark"] .btn-outline-primary:hover,
[data-theme="dark"] .btn-outline-primary:active {
    background-color: var(--ice-hint) !important;
    color: var(--void) !important;
}

[data-theme="dark"] a {
    color: var(--ice-hint);
}
[data-theme="dark"] a:hover {
    color: var(--smoke-white);
}

/* Secondary Buttons & Muted States */
[data-theme="dark"] .btn-secondary,
[data-theme="dark"] .btn-light,
[data-theme="dark"] .btn-dark,
[data-theme="dark"] .btn:not(.btn-primary):not(.btn-outline-primary) {
    background-color: var(--surface) !important;
    color: var(--smoke-white) !important;
    border-color: var(--border) !important;
}

[data-theme="dark"] .btn-secondary:hover,
[data-theme="dark"] .btn-light:hover,
[data-theme="dark"] .btn-dark:hover,
[data-theme="dark"] .btn:not(.btn-primary):not(.btn-outline-primary):hover {
    background-color: var(--raised) !important;
    border-color: var(--border-hover) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .btn:disabled,
[data-theme="dark"] .btn.disabled {
    background-color: var(--surface) !important;
    color: var(--muted) !important;
    border-color: var(--border) !important;
    opacity: 0.7 !important;
}

/* Forms & Inputs */
[data-theme="dark"] .form-control,
[data-theme="dark"] .form-select,
[data-theme="dark"] .input-group-text {
    background-color: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}

[data-theme="dark"] .form-control:focus,
[data-theme="dark"] .form-select:focus {
    background-color: var(--raised) !important;
    border-color: var(--ice-hint) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 0 3px rgba(200, 216, 232, 0.2) !important; /* ice-hint shadow */
}

[data-theme="dark"] .form-control::placeholder {
    color: var(--sub-text) !important;
}

/* Switches & Checkboxes */
[data-theme="dark"] .form-check-input {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
}

[data-theme="dark"] .form-check-input:checked {
    background-color: var(--ice-hint) !important;
    border-color: var(--ice-hint) !important;
}

/* Tables */
[data-theme="dark"] .table,
[data-theme="dark"] .table th,
[data-theme="dark"] .table td {
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
    background-color: transparent !important;
}

[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) > * {
    background-color: var(--surface) !important;
}

[data-theme="dark"] .table-hover > tbody > tr:hover > * {
    background-color: var(--raised) !important;
}

/* Badges & Tags */
[data-theme="dark"] .badge {
    background-color: var(--surface) !important;
    color: var(--smoke-white) !important;
    border: 1px solid var(--border) !important;
}

/* Remove hardcoded color classes overrides (from append_css5 and maps) */
[data-theme="dark"] .mc-btn-view,
[data-theme="dark"] .mc-btn-update,
[data-theme="dark"] .mc-btn-resolve,
[data-theme="dark"] .mc-btn-locate,
[data-theme="dark"] .mc-btn-delete,
[data-theme="dark"] .text-success,
[data-theme="dark"] .text-danger,
[data-theme="dark"] .text-warning,
[data-theme="dark"] .text-info,
[data-theme="dark"] .bg-success,
[data-theme="dark"] .bg-danger,
[data-theme="dark"] .bg-warning,
[data-theme="dark"] .bg-info,
[data-theme="dark"] .badge-success,
[data-theme="dark"] .badge-danger,
[data-theme="dark"] .badge-warning,
[data-theme="dark"] .badge-info {
    /* STRICT ADHERENCE: Override all semantic colors to the allowed tokens */
    background-color: var(--surface) !important;
    color: var(--ice-hint) !important;
    border-color: var(--border) !important;
}

[data-theme="dark"] .mc-btn-view:hover,
[data-theme="dark"] .mc-btn-update:hover,
[data-theme="dark"] .mc-btn-resolve:hover,
[data-theme="dark"] .mc-btn-locate:hover,
[data-theme="dark"] .mc-btn-delete:hover {
    background-color: var(--raised) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-hover) !important;
}

/* Scrollbars */
[data-theme="dark"] ::-webkit-scrollbar {
    width: 8px !important;
    height: 8px !important;
    background-color: var(--base) !important;
}

[data-theme="dark"] ::-webkit-scrollbar-track {
    background: var(--base) !important;
}

[data-theme="dark"] ::-webkit-scrollbar-thumb {
    background: var(--muted) !important;
    border-radius: 4px !important;
}

[data-theme="dark"] ::-webkit-scrollbar-thumb:hover {
    background: var(--sub-text) !important;
}

/* Map Polygons overrides */
[data-theme="dark"] .room-poly,
[data-theme="dark"] .room-poly.fill-silver,
[data-theme="dark"] .room-poly.fill-orange,
[data-theme="dark"] .room-poly.fill-red,
[data-theme="dark"] .room-poly.fill-blue,
[data-theme="dark"] .room-poly.fill-teal,
[data-theme="dark"] .room-poly.fill-pink,
[data-theme="dark"] .building-outline {
    fill: var(--surface) !important;
    stroke: var(--border) !important;
}

[data-theme="dark"] .room-group:hover .room-poly {
    fill: var(--raised) !important;
    stroke: var(--border-hover) !important;
    filter: none !important;
}

[data-theme="dark"] .room-group.selected .room-poly {
    fill: var(--ice-hint) !important;
    stroke: var(--text-primary) !important;
    filter: drop-shadow(0 0 8px rgba(200, 216, 232, 0.4)) !important;
}

[data-theme="dark"] .legend-color,
[data-theme="dark"] .legend-box,
[data-theme="dark"] .room-block {
    background-color: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}
"""

with open(css_path, 'a', encoding='utf-8') as f:
    f.write(css)

print("Strict Dark Mode CSS appended successfully!")
