import os

css_path = r'd:\FixLink-V1\app\static\css\style.css'

css = """
/* ============================================
   STRICT DARK MODE - MOBILE EDGE CASES
   ============================================ */
html[data-theme="dark"] {
    /* Prevent white flashes on pull-to-refresh, use void for deepest background */
    background-color: var(--void) !important;
    color-scheme: dark !important;
}

[data-theme="dark"] body {
    /* Ensure body stays on base */
    background-color: var(--base) !important;
}

/* Mobile Navbars & Drawers (Bottom Navigation) */
[data-theme="dark"] .mobile-bottom-nav {
    background-color: var(--surface) !important;
    border-top: 1px solid var(--border) !important;
    padding-bottom: env(safe-area-inset-bottom) !important;
}

[data-theme="dark"] .mobile-bottom-nav .nav-link {
    color: var(--sub-text) !important;
}

[data-theme="dark"] .mobile-bottom-nav .nav-link.active,
[data-theme="dark"] .mobile-bottom-nav .nav-link:hover {
    color: var(--ice-hint) !important;
}

[data-theme="dark"] .mobile-bottom-nav .nav-link i {
    color: inherit !important;
}

/* Form Inputs deeply */
[data-theme="dark"] input:-webkit-autofill,
[data-theme="dark"] input:-webkit-autofill:hover, 
[data-theme="dark"] input:-webkit-autofill:focus, 
[data-theme="dark"] input:-webkit-autofill:active{
    -webkit-box-shadow: 0 0 0 30px var(--surface) inset !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    transition: background-color 5000s ease-in-out 0s;
}

/* Third-party library overrides (SweetAlert, DataTables, etc if any) */
[data-theme="dark"] .swal2-popup {
    background: var(--card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}

[data-theme="dark"] .swal2-title,
[data-theme="dark"] .swal2-html-container {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .modal-header {
    border-bottom: 1px solid var(--border) !important;
}

[data-theme="dark"] .modal-footer {
    border-top: 1px solid var(--border) !important;
}
"""

with open(css_path, 'a', encoding='utf-8') as f:
    f.write(css)

print("Mobile Edge Cases appended.")
