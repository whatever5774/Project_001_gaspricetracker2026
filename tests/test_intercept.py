"""
测试与调试辅助脚本：用于测试各个独立组件与流程的行为 (Test/Debug Script)
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        c = await b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await c.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        async def handle_response(response):
            try:
                if "json" in response.headers.get("content-type", ""):
                    url = response.url
                    # print("JSON Response:", url)
                    body = await response.text()
                    if "Regular" in body and "Premium" in body:
                        print(f"!!! FOUND GAS PRICES in {url}")
                        with open("gas_api_dump.json", "w", encoding="utf-8") as f:
                            f.write(body)
            except Exception:
                pass

        page.on("response", handle_response)
        
        try:
            print("Navigating...")
            await page.route("**/*.{png,jpg,jpeg,svg,css,woff2}", lambda route: route.abort())
            await page.goto('https://www.costco.com/warehouse-locations?zipCode=91709', wait_until='commit', timeout=15000)
            print("Committed. Waiting 10s...")
            await asyncio.sleep(10)
        except Exception as e:
            print("Exception during navigation:", e)
            await asyncio.sleep(5)
            
        print("Done.")

asyncio.run(run())
