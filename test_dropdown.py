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
        
        await page.goto('https://www.costco.com/w/-/locations', wait_until='commit')
        
        print("Waiting for page load...")
        # Manually wait for user to bypass captcha and page to load
        for _ in range(30):
            inputs_count = await page.evaluate("() => document.querySelectorAll('input').length")
            if inputs_count > 0:
                break
            await asyncio.sleep(2)
            
        print("Page seems loaded, filling the first text input with 91709")
        await page.evaluate('''() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            const searchInput = inputs.find(i => i.type === 'text' || i.type === 'search' || !i.type);
            if(searchInput) {
                searchInput.value = '91709';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                searchInput.focus();
                
                // Try to find the search button or hit enter
                const form = searchInput.closest('form');
                if(form) {
                    form.dispatchEvent(new Event('submit', { bubbles: true }));
                } else {
                    const keyboardEvent = new KeyboardEvent('keydown', {
                        bubbles: true, cancelable: true, keyCode: 13, key: 'Enter'
                    });
                    searchInput.dispatchEvent(keyboardEvent);
                }
            }
        }''')
        
        print('Enter pressed. Waiting for results...')
        
        # Wait for store list
        await asyncio.sleep(10)
        
        # Now try to find the "expand" or "show location details" buttons and click them
        expand_buttons = page.locator("button:has-text('Store Details'), button:has-text('Location Detail'), button:has-text('Expand'), button[aria-expanded='false']")
        count = await expand_buttons.count()
        print('Found expand buttons:', count)
        
        for i in range(min(count, 3)):
            try:
                elem = expand_buttons.nth(i)
                text = await elem.inner_text()
                print('Clicking:', text)
                await elem.click()
                await asyncio.sleep(2)
            except Exception as e:
                print('Click failed', e)
                
        await asyncio.sleep(5)
        html = await page.content()
        with open('test_gas_click.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("HTML dumped")
        await b.close()

if __name__ == '__main__':
    asyncio.run(test())
