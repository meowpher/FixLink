import sys

with open('d:/FixLink-V1/app/static/css/style.css', 'a', encoding='utf-8') as f:
    f.write('\n\n/* Final Header & Legend Dark Mode Overrides */\n')
    f.write('[data-theme="dark"] .status-legend-section { background: var(--bg-surface) !important; border-bottom: 1px solid var(--border-subtle) !important; }\n')
    f.write('[data-theme="dark"] .status-map-header { background: var(--bg-overlay) !important; border-bottom: 1px solid var(--border-subtle) !important; }\n')
print('CSS appended successfully!')
