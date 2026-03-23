"""
测试与调试辅助脚本：用于测试各个独立组件与流程的行为 (Test/Debug Script)
"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=False,
            args=['--disable-http2', '--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        c = await b.new_context()
        page = await c.new_page()
        
        await page.goto('https://www.costco.com/w/-/locations', wait_until='commit')
        # Wait for page load
        for _ in range(15):
            count = await page.evaluate("() => document.querySelectorAll('input').length")
            if count > 0:
                break
            await asyncio.sleep(2)
            
        print("Page loaded inputs.")
        
        # We need to type into it like a real user so React state updates
        await page.evaluate('''() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            const searchInput = inputs.find(i => i.type === 'text' || i.type === 'search' || !i.type);
            if(searchInput) {
                searchInput.id = "my-injected-search";
            }
        }''')
        
        print("Injected ID")
        await asyncio.sleep(2)
        
        # Now Playwright can find it and type
        search_input = page.locator("#my-injected-search")
        if await search_input.count() > 0:
            await search_input.fill('91709')
            await search_input.press('Enter')
            print("Typed and Pressed Enter")
        
        # Wait 10 seconds for the search to complete
        await asyncio.sleep(10)
        
        # Count elements
        buttons = page.locator("[data-testid='warehousetile-seewarehousedetails-icon-chevron-down']")
        count = await buttons.count()
        print('Found buttons:', count)
        
        if count == 0:
            html = await page.content()
            print('Search might have failed. HTML size:', len(html))
            
        await b.close()

if __name__ == '__main__':
    asyncio.run(test())
