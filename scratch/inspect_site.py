import asyncio
from playwright.sync_api import sync_playwright
import json

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        print("Navigating to URL...")
        page.goto("https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php", wait_until="networkidle")
        print("Title:", page.title())
        
        # Check select options for Legislatura
        leg_select = page.query_selector("select[name='C_Legis']")
        if leg_select:
            options = page.query_selector_all("select[name='C_Legis'] option")
            opts = [{'text': o.inner_text().strip(), 'value': o.get_attribute('value')} for o in options]
            print("Legislatura options:", opts)
        
        # Select LXIII (or LX)
        print("\nSelecting Legislatura LXIII...")
        page.select_option("select[name='C_Legis']", value="LXIII")
        page.wait_for_timeout(2000)
        
        # Check session options
        ns_options = page.query_selector_all("select[name='C_NS'] option")
        ns_opts = [{'text': o.inner_text().strip(), 'value': o.get_attribute('value')} for o in ns_options]
        print(f"Session (C_NS) options count: {len(ns_opts)}, first 10: {ns_opts[:10]}")
        
        # Click search
        print("\nClicking Submit search button...")
        submit_btn = page.query_selector("input[type='submit']") or page.query_selector("input[name='Submit']")
        if submit_btn:
            submit_btn.click()
            page.wait_for_timeout(3000)
            
        print("Page URL after search:", page.url)
        
        # Check table / results
        tables = page.query_selector_all("table")
        print(f"Tables found: {len(tables)}")
        
        rows = page.query_selector_all("tr")
        print(f"Total rows on page: {len(rows)}")
        
        links = page.query_selector_all("a")
        print(f"Total links on page: {len(links)}")
        for i, a in enumerate(links[:20]):
            print(f"Link {i}: text='{a.inner_text().strip()}', href='{a.get_attribute('href')}'")
            
        # Check images, icons, download buttons, onClick attributes, etc.
        onclicks = page.eval_on_selector_all("[onclick]", "elements => elements.map(e => e.getAttribute('onclick'))")
        print(f"\nOnclick elements count: {len(onclicks)}, first 10: {onclicks[:10]}")

        # Print all text in main tables to see structure
        for idx, t in enumerate(tables):
            t_text = t.inner_text()
            print(f"\n--- Table {idx} snippet (first 300 chars) ---")
            print(t_text[:300])

        browser.close()

if __name__ == "__main__":
    main()
