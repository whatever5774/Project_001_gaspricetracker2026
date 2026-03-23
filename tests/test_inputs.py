"""
测试与调试辅助脚本：用于测试各个独立组件与流程的行为 (Test/Debug Script)
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=True,
            args=['--disable-http2', '--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        c = await b.new_context()
        page = await c.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        await page.goto('https://www.costco.com/warehouse-locations', timeout=30000)
        await asyncio.sleep(10)
        
        html = await page.content()
        with open('new_layout.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print('Dumped HTML. Length:', len(html))
        
        inputs = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('input')).map(i => {
                return {id: i.id, placeholder: i.placeholder, className: i.className}
            });
        }''')
        print('Inputs on page:', inputs)
        await b.close()

asyncio.run(test())
