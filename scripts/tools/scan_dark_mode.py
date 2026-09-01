import os
import re

template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'templates')
issues = []

patterns = [
    (re.compile(r'class="[^"]*\btext-dark\b[^"]*"', re.I), 'text-dark class'),
    (re.compile(r'class="[^"]*\bbg-white\b[^"]*"', re.I), 'bg-white class'),
    (re.compile(r'class="[^"]*\btable-light\b[^"]*"', re.I), 'table-light class'),
    (re.compile(r'class="[^"]*\bbadge bg-light\b[^"]*"', re.I), 'badge bg-light class'),
    (re.compile(r'style="[^"]*background(?:-color)?:\s*(?:#fff\b|#ffffff\b|white\b)[^"]*"', re.I), 'inline white background'),
    (re.compile(r'style="[^"]*color:\s*(?:#000\b|#000000\b|#111\b|#222\b|#333\b|#0f172a\b|#1e293b\b|black\b)[^"]*"', re.I), 'inline dark text color'),
]

for root, dirs, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as fp:
                lines = fp.readlines()
            for idx, line in enumerate(lines, 1):
                for pat, desc in patterns:
                    if pat.search(line):
                        issues.append((os.path.relpath(filepath, template_dir), idx, desc, line.strip()))

print(f"Total potential dark mode color issues found: {len(issues)}")
for path, line_no, desc, snippet in issues:
    print(f"{path}:{line_no} [{desc}] -> {snippet[:120]}")
