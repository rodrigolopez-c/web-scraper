from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Intercept network requests to see what URL/POST data is being sent
        page.on("request", lambda req: print(f"REQ: {req.method} {req.url} data={req.post_data}"))
        
        page.goto("https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php", wait_until="networkidle")
        
        print("\n--- Selecting Legislatura LXIII ---")
        page.select_option("select[name='C_Legis']", value="LXIII")
        page.wait_for_timeout(2000)
        
        print("\n--- Clicking Submit ---")
        submit_btn = page.query_selector("input[type='submit']") or page.query_selector("input[name='Submit']")
        if submit_btn:
            submit_btn.click()
            page.wait_for_timeout(3000)
            
        print("\n--- Form html ---")
        forms = page.query_selector_all("form")
        for i, f in enumerate(forms):
            print(f"Form {i}: action={f.get_attribute('action')}, method={f.get_attribute('method')}, innerHTML={f.inner_html()[:200]}")
            
        browser.close()

if __name__ == "__main__":
    main()
