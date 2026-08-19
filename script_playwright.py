from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("file:///C:/Users/Taha%20Mustafa/Desktop/Fixlink/doc.html")
        page.pdf(path="FixLink_Documentation_V2.pdf", format="A4", margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"})
        browser.close()

run()
