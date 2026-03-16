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
        
        async def handle_response(response):
            try:
                if 'graphql' in response.url.lower():
                    if 'json' in response.headers.get('content-type', ''):
                        text = await response.text()
                        if 'Regular' in text or '917' in text or 'locations' in text.lower():
                            print('\\n!!! FOUND API !!!')
                            print('URL:', response.url)
                            req = response.request
                            print('Method:', req.method)
                            print('Headers:', req.headers)
                            print('Post Data:', req.post_data)
            except Exception as e:
                pass

        page.on('response', handle_response)
        
        await page.goto('https://www.costco.com/w/-/locations', wait_until='commit')
        # Wait for page load
        for _ in range(15):
            try:
                count = await page.evaluate("() => document.querySelectorAll('input').length")
                if count > 0:
                    break
            except Exception:
                pass
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
        
        await asyncio.sleep(2)
        search_input = page.locator('#my-injected-search')
        await search_input.fill('91709')
        print("Filled 91709")
        
        # Instead of pressing Enter which submits the form, wait a bit and click the first suggestion
        await asyncio.sleep(2)
        print("Pressing arrow down and enter")
        await search_input.press('ArrowDown')
        await asyncio.sleep(1)
        await search_input.press('Enter')
        
        await asyncio.sleep(8)
        
        expand_buttons = page.locator("[data-testid='warehousetile-seewarehousedetails-icon-chevron-down']")
        count = await expand_buttons.count()
        print('Found expand buttons:', count)
        for i in range(min(count, 3)):
            try:
                await expand_buttons.nth(i).click()
                await asyncio.sleep(1.5)
            except:
                pass
                
        await asyncio.sleep(5)
        await b.close()

asyncio.run(test())
