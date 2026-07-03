import asyncio
import re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Load stealth explicitly if available, or just ignore for simple test
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        except Exception:
            try:
                from playwright_stealth import Stealth
                await Stealth().use_async(page)
            except:
                pass
                
        print("Visiting Costco Chino Hills...")
        await page.goto("https://www.costco.com/w/-/ca/chino%20hills/473", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        html = await page.content()
        with open("debug_costco.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Saved to debug_costco.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
