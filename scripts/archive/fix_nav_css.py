"""
Fixes the broken @media (max-width: 1023px) block in style.css.
Reads the file, removes the mangled section, and injects a clean replacement.
"""
import re

css_path = r"d:\FixLink-V1\app\static\css\style.css"

with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

# The broken section starts at @media (max-width: 1023px) and was corrupted.
# We'll replace from that marker up to (but not including) the PHONE ONLY block
# which starts with @media (max-width: 767px) used for main content padding.

BROKEN_START = "@media (max-width: 1023px) {"
# Find the broken block start
idx_start = content.find(BROKEN_START)

# Find the start of the PHONE ONLY @media block (the one that contains .main-content padding: 0.75rem)
PHONE_ONLY_MARKER = "/* ----------------------------------\n   PHONE ONLY (max-width: 767px)\n   ---------------------------------- */"
idx_phone = content.find("/* ----------------------------------")
# Actually just find the next clean @media after the broken start
# The broken version has @media (max-width: 767px) embedded inside the 1023px block
# Let's find the line with "padding: 0.75rem;" which belongs to phone-only main-content
idx_phone_media = content.find("padding: 0.75rem;\n        padding-top: 70px;")
# Back up to the @media line before it
search_region = content[idx_start:idx_phone_media]
# Find the last @media within search_region
last_media_in_broken = search_region.rfind("@media (max-width: 767px)")
idx_phone_block_start = idx_start + last_media_in_broken

REPLACEMENT_1023 = """@media (max-width: 1023px) {
    html, body {
        overflow-x: hidden;
    }

    /* Navbar */
    .vyas-navbar {
        padding: 0 1rem;
        height: auto;
        min-height: 60px;
    }

    /* ---- Hamburger toggler: flush left, no floating gap ---- */
    .navbar-toggler {
        margin-left: 0;
        padding: 6px 10px;
        border-radius: 8px;
    }

    /* ---- Collapsed panel: borderless top, seamless with navbar ---- */
    .navbar-collapse {
        background: var(--bg-surface);
        padding: 0.5rem 1rem 1rem;
        border-radius: 0 0 12px 12px;
        margin-top: 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-subtle);
        border-top: none;
    }

    /* ---- Nav list: compact vertical rhythm ---- */
    .navbar-nav {
        flex-direction: column;
        align-items: stretch;
        gap: 2px;
    }

    /* ---- Nav links: icon + label on same baseline ---- */
    .navbar-nav .nav-link {
        display: flex !important;
        align-items: center;
        gap: 10px;
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 0.95rem;
    }

    /* Uniform icon size with fixed width for vertical-axis alignment */
    .navbar-nav .nav-link i.bi {
        font-size: 1.05rem;
        line-height: 1;
        flex-shrink: 0;
        width: 20px;
        text-align: center;
    }

    /* ---- Utility icons (bell, theme, avatar): left-aligned row ---- */
    .navbar-nav .nav-item.ms-2,
    .navbar-nav .nav-item.ms-lg-4 {
        display: inline-flex;
        align-items: center;
        margin-left: 0 !important;
        padding: 4px 12px;
    }

    /* Divider above the utility strip */
    .navbar-nav .nav-item.ms-lg-4 {
        margin-top: 8px;
        padding-top: 12px;
        border-top: 1px solid var(--border-subtle);
    }

    /* Utility icon buttons: fixed size, centered */
    .navbar-nav #themeToggleBtn {
        width: 40px;
        height: 40px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Main Layout */
    .main-content {
        padding: 1rem;
        padding-top: 80px;
    }

    .dashboard-grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
    }

    .card {
        padding: 1.25rem !important;
    }

    /* Modals */
    .modal-dialog {
        max-width: 95% !important;
        margin: 1rem auto;
    }

    .glass-modal .modal-content {
        border-radius: 20px !important;
    }

    /* Touch targets */
    .btn, .form-control, .form-select, .room-btn, .choice-btn {
        min-height: 44px;
    }

    /* Timetable Grid */
    .timetable-grid {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 1rem;
    }

    .tt-form-container {
        padding: 1rem !important;
    }

    /* Map Layouts */
    .map-panel, .floor-map-container {
        min-height: 450px;
    }
}

/* ----------------------------------
   PHONE ONLY (max-width: 767px)
   ---------------------------------- */
"""

# Replace from BROKEN_START to the phone block start (exclusive)
new_content = content[:idx_start] + REPLACEMENT_1023 + content[idx_phone_block_start + len("@media (max-width: 767px) {"):]
# The phone block content already starts with what was there before
# but we need to restore the opening brace since we consumed it above
# Let's re-check: idx_phone_block_start points to "@media (max-width: 767px)"
# We want to keep the full phone-only block so we include it:
new_content = content[:idx_start] + REPLACEMENT_1023 + content[idx_phone_block_start:]

with open(css_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done! Lines around fix:")
lines = new_content.split("\n")
for i, line in enumerate(lines):
    if "@media (max-width: 1023px)" in line or "@media (max-width: 767px)" in line:
        print(f"  Line {i+1}: {line[:80]}")
