import markdown
import sys

with open(r"c:\Users\Taha Mustafa\.gemini\antigravity-ide\brain\3005871d-c9fe-4f17-bad5-d5aa66732de9\fixlink_documentation.md", "r", encoding="utf-8") as f:
    text = f.read()

html = markdown.markdown(text, extensions=["tables"])
html = f"<html><head><meta charset='utf-8'><style>body{{font-family: sans-serif; line-height: 1.6; padding: 2em;}} table{{border-collapse: collapse; width: 100%; margin-bottom: 1em;}} th, td{{border: 1px solid #ddd; padding: 8px; text-align: left;}} th{{background-color: #f2f2f2;}} code{{background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px;}} pre{{background-color: #f4f4f4; padding: 1em; overflow-x: auto;}}</style></head><body>{html}</body></html>"

with open(r"c:\Users\Taha Mustafa\Desktop\Fixlink\doc.html", "w", encoding="utf-8") as f:
    f.write(html)
