with open('d:/FixLink-V1/app/static/css/style.css', 'a', encoding='utf-8') as f:
    f.write('''

/* --- FINAL COMPONENT DARK MODE FIXES --- */

/* 1. Modal, Forms & Container Background Overrides */
[data-theme="dark"] .bg-light, 
[data-theme="dark"] .bg-white,
[data-theme="dark"] .form-control.bg-white,
[data-theme="dark"] .form-control.bg-transparent,
[data-theme="dark"] .input-group-text.bg-white,
[data-theme="dark"] .input-group-text.bg-transparent,
[data-theme="dark"] .card-footer.bg-white,
[data-theme="dark"] .dropdown-header.bg-light {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
}

/* Modal Content specific fixes */
[data-theme="dark"] .modal-content {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
}

/* 2. Neural Schedule Synchronizer specific buttons */
[data-theme="dark"] .room-btn, 
[data-theme="dark"] .choice-btn {
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
}

[data-theme="dark"] .room-btn:hover, 
[data-theme="dark"] .choice-btn:hover {
    background: var(--bg-overlay) !important;
}

[data-theme="dark"] .room-btn.selected, 
[data-theme="dark"] .choice-btn.selected {
    background: var(--mitwpu-blue) !important;
    color: #ffffff !important;
    border-color: #00d2ff !important;
}

/* 3. Button group for tabs (Help Requests: Pending/Approved/etc) */
[data-theme="dark"] .btn-group .btn.bg-white {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
}

/* Maintain text colors for the specific outline buttons */
[data-theme="dark"] .btn-group .btn-outline-primary.bg-white { color: var(--mitwpu-blue) !important; }
[data-theme="dark"] .btn-group .btn-outline-success.bg-white { color: #10b981 !important; }
[data-theme="dark"] .btn-group .btn-outline-danger.bg-white { color: #ef4444 !important; }
[data-theme="dark"] .btn-group .btn-outline-secondary.bg-white { color: var(--text-secondary) !important; }

/* 4. Dropdown Menus (Notifications) */
[data-theme="dark"] .dropdown-menu {
    background-color: var(--bg-overlay) !important;
    border: 1px solid var(--border-subtle) !important;
}

[data-theme="dark"] .dropdown-item {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dropdown-item:hover {
    background-color: var(--bg-surface) !important;
}

/* Form Inputs within modals */
[data-theme="dark"] .modal-content input,
[data-theme="dark"] .modal-content select {
    background-color: var(--bg-overlay) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
}
''')
print('CSS fixes appended successfully')
