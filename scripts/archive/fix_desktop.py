"""
Emergency desktop-restoration patch.
The previous responsive block added global rules that broke desktop.
This script appends a targeted @media (min-width: 768px) reset block
that undoes every harmful global override for desktop screens.
"""

FIX_BLOCK = '''

/* ================================================================
   EMERGENCY DESKTOP RESTORATION — v5.1
   Undoes every global rule from v5.0 that bled into desktop layout.
   These overrides ONLY apply at >= 768px (desktop / tablet).
   ================================================================ */

@media (min-width: 768px) {

    /* ── 1. UNDO TOUCH-TARGET OVERRIDES ON DESKTOP ── */
    /* The global "min-height: 44px + display:inline-flex" rule
       completely broke nav links, dropdown items, and anchor tags
       used as block-level layout elements on desktop. Reset them. */

    a, button {
        min-height: unset;
        display: revert;
        align-items: unset;
    }

    .btn {
        min-height: unset;
        display: inline-block;
        align-items: unset;
    }

    .nav-link {
        min-height: unset;
        display: flex;         /* keep flex — needed for icon+label alignment */
        align-items: center;
    }

    .dropdown-item {
        min-height: unset;
        display: block;
        align-items: unset;
    }

    /* Navbar brand — restore normal display */
    .navbar-brand {
        display: flex;
        align-items: center;
        overflow: visible;     /* undo clip from mobile rule */
        min-width: unset;
    }

    /* ── 2. UNDO FLUID HEADING OVERRIDES ON DESKTOP ── */
    /* The global h1/h2/h3 clamp() rules override page-specific
       heading sizes that were already correct on desktop. Reset. */

    h1, .h1 { font-size: 2.5rem; }
    h2, .h2 { font-size: 2rem;   }
    h3, .h3 { font-size: 1.75rem; }
    h4, .h4 { font-size: 1.5rem; }
    h5, .h5 { font-size: 1.25rem; }
    h6, .h6 { font-size: 1rem;   }

    /* ── 3. UNDO FORM FONT-SIZE OVERRIDE ON DESKTOP ── */
    /* 16px minimum was for mobile iOS zoom prevention only.
       Desktop forms look fine at their original sizes. */
    input, select, textarea,
    .form-control, .form-select {
        font-size: 0.9375rem;   /* Bootstrap default ~15px equivalent */
    }

    /* ── 4. UNDO CARD / PADDING MOBILE OVERRIDES ── */
    .card { padding: revert !important; }

    /* ── 5. UNDO FLEX-DIRECTION OVERRIDES ── */
    .d-flex.justify-content-between,
    .d-flex.justify-content-end {
        flex-wrap: nowrap;
    }

    /* Page headers stay horizontal on desktop */
    .page-header,
    .tickets-header,
    .section-header {
        flex-direction: row;
        align-items: center !important;
        gap: 0;
    }

    /* ── 6. UNDO FULL-WIDTH BUTTON OVERRIDES ── */
    .card .btn,
    .card-footer .btn {
        width: auto;
        justify-content: unset;
    }

    form [type="submit"],
    form .btn-primary,
    form .btn-submit {
        width: auto;
        justify-content: unset;
    }

    /* ── 7. UNDO MODAL FULL-SCREEN ON DESKTOP ── */
    .modal-dialog {
        max-width: 500px !important;
        height: auto;
        margin: 1.75rem auto;
    }

    .modal-content {
        border-radius: var(--border-radius-lg) !important;
        height: auto;
        overflow-y: visible;
    }

    /* ── 8. UNDO NAVBAR POSITION OVERRIDES ── */
    /* Restore the desktop pill-shaped floating navbar */
    .vyas-navbar {
        left: 16px !important;
        right: 16px !important;
        top: 12px !important;
        border-radius: 14px !important;
        z-index: 1030 !important;
    }

    body {
        padding-top: 90px;     /* restore original desktop body offset */
        font-size: revert;     /* undo fluid body font override */
    }

    .main-content {
        padding-top: revert;
        padding-inline: revert;
    }

    /* ── 9. UNDO FORM LAYOUT COLLAPSE ── */
    /* Multi-column form layouts stay multi-column on desktop */
    form .row > [class*="col-"] {
        flex: revert;
        max-width: revert;
        margin-bottom: 0;
    }

    /* ── 10. UNDO SECTION PADDING OVERRIDES ── */
    .p-4  { padding: 1.5rem !important; }
    .p-5  { padding: 3rem !important;   }
    .px-4 { padding-inline: 1.5rem !important; }
    .px-5 { padding-inline: 3rem !important;   }
    .py-4 { padding-block: 1.5rem !important;  }
    .py-5 { padding-block: 3rem !important;    }

    /* ── 11. UNDO WORD-BREAK / OVERFLOW-WRAP GLOBAL ── */
    /* This was too aggressive — headings on desktop don\'t need it */
    h1, h2, h3, h4, h5, h6 {
        overflow-wrap: normal;
        word-break: normal;
    }

    /* ── 12. UNDO BRAND-TEXT CLIP ── */
    .brand-text-wrapper { overflow: visible; }
    .brand-text {
        white-space: nowrap;
        overflow: visible;
        text-overflow: clip;
    }

    /* ── 13. UNDO GRID COLUMN OVERRIDES ── */
    /* Auto-fit is fine — but ensure grids that had 3+ columns keep them */
    .dashboard-grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    }

    /* ── 14. RESTORE BOOTSTRAP BUTTON SIZES ── */
    .btn-sm {
        min-height: unset;
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
    }

    .btn {
        padding: 0.375rem 0.75rem;
        font-size: 1rem;
    }

    /* ── 15. UNDO FLEX BLOWOUT GUARD — too broad on desktop ── */
    /* "min-width: 0 on ALL .d-flex > *" is useful on mobile but
       can cause layout issues on complex desktop flex grids */
    .d-flex > * {
        min-width: revert;
    }

    /* Re-apply only where actually needed for text overflow */
    .navbar-brand > *,
    .stat-card > *,
    .card-body > *,
    .mc-card > * {
        min-width: 0;
    }
}

/* ── ALSO RESTORE: global "a" display was not inside @media ── */
/* The global touch-target rule set display:inline-flex on ALL <a>.
   This must be reset globally (not just >=768px) because it breaks
   block-level anchor usage (sidebar items, card wrappers, etc.) */
a {
    display: revert;
}

/* But keep flex for nav-link and btn (they need it explicitly) */
.nav-link {
    display: flex;
    align-items: center;
}
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

/* ================================================================
   END — DESKTOP RESTORATION v5.1
   ================================================================ */
'''

css_path = r"d:\FixLink-V1\app\static\css\style.css"
with open(css_path, "a", encoding="utf-8") as f:
    f.write(FIX_BLOCK)

print(f"Appended {len(FIX_BLOCK.splitlines())} lines.")
import os
print(f"File size: {os.path.getsize(css_path)/1024:.1f} KB")
print("Done.")
