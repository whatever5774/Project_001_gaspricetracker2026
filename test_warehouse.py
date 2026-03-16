import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=False,
            args=['--disable-http2', '--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        c = await b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = await c.new_page()
        
        target_url = "https://www.costco.com/w/-/ca/chino%20hills/473"
        print(f"Visiting direct warehouse URL: {target_url}")
        await page.goto(target_url, wait_until='commit')
        
        # Give the user 60 seconds to pass any captcha
        print("Waiting 15 seconds for page load / Captcha check...")
        await asyncio.sleep(15)
        
        html = await page.content()
        with open('test_warehouse_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        if "Regular" in html or "Premium" in html:
            print("Gas prices found directly in the HTML!")
        else:
            print("Gas prices not found. Dumping HTML to investigate if there's an expand button.")
            
        # Try to find expand buttons just in case
        expand_buttons = page.locator("button:has-text('Gas Station'), [data-testid*='chevron-down']")
        count = await expand_buttons.count()
        if count > 0:
            print(f"Found {count} potential expand buttons. Clicking them...")
            for i in range(min(count, 3)):
                try:
                    await expand_buttons.nth(i).click()
                    await asyncio.sleep(2)
                except:
                    pass
        
        # Second dump just in case click revealed something
        html_after_click = await page.content()
        with open('test_warehouse_page_clicked.html', 'w', encoding='utf-8') as f:
            f.write(html_after_click)
            
        await b.close()

if __name__ == '__main__':
    asyncio.run(test())
