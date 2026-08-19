import sys

with open('d:/FixLink-V1/app/static/css/style.css', 'a', encoding='utf-8') as f:
    f.write('\n\n/* Dark Mode Overrides for Statuses and Badges */\n')
    f.write('[data-theme="dark"] .status-open { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }\n')
    f.write('[data-theme="dark"] .status-in-progress { background: rgba(245, 158, 11, 0.15); color: #fcd34d; }\n')
    f.write('[data-theme="dark"] .status-fixed { background: rgba(34, 197, 94, 0.15); color: #86efac; }\n')
    f.write('[data-theme="dark"] .status-cancelled { background: rgba(220, 53, 69, 0.15); color: #fca5a5; border-color: transparent; box-shadow: none; }\n')
    f.write('[data-theme="dark"] .floor-nav-display { background: var(--bg-surface); border-color: var(--border-subtle); color: var(--text-primary); box-shadow: var(--shadow-sm); }\n')
    f.write('[data-theme="dark"] .badge-it { background-color: rgba(78, 115, 223, 0.2); color: #a5b4fc; }\n')
    f.write('[data-theme="dark"] .badge-electrician { background-color: rgba(246, 194, 62, 0.2); color: #fde68a; }\n')
    f.write('[data-theme="dark"] .badge-plumber { background-color: rgba(54, 185, 204, 0.2); color: #67e8f9; }\n')
    f.write('[data-theme="dark"] .badge-carpenter { background-color: rgba(231, 74, 59, 0.2); color: #fca5a5; }\n')
print('CSS appended successfully!')
