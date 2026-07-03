import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def main():
    p = await async_playwright().start()
    b = await p.chromium.launch()
    c = await b.new_context()
    page = await c.new_page()
    await stealth(page)
    await b.close()
    p.stop()

asyncio.run(main())
