"""
Costco 油价真实 Playwright 探测脚本 (无 Mock，真实网络请求)
用于验证在真实无头浏览器环境下绕过防爬并提取各门店油价
"""
import asyncio
import json
import logging
import re
import sys
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LivePlaywrightTest")

TARGET_URLS = [
    "https://www.costco.com/w/-/ca/chino%20hills/473",
    "https://www.costco.com/w/-/ca/ontario-bus-ctr-ontario/947",
    "https://www.costco.com/w/-/ca/eastvale/1317"
]

def _warehouse_id(url: str) -> str:
    m = re.search(r'/(\d+)$', url.rstrip('/'))
    if not m:
        raise ValueError(f"无法从 URL 提取 warehouse ID: {url}")
    return m.group(1)

def _city_name(url: str) -> str:
    segment = url.rstrip('/').split('/')[-2]
    return segment.replace('%20', ' ').replace('-', ' ').title()

async def fetch_gas_prices_live(urls: List[str]) -> List[Dict[str, str]]:
    results = []
    async with async_playwright() as p:
        logger.info("启动 Chromium (Headless 模式)...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            # 1. 访问首个门店页面，触发并执行 Akamai 脚本，获取有效 Cookie
            first_url = urls[0]
            logger.info(f"建立会话: 访问基准门市页面以初始化会话: {first_url}")
            await page.goto(first_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)

            # 2. 依次通过页面直接导航获取各门市 JSON 价格
            for i, target_url in enumerate(urls):
                wid = _warehouse_id(target_url)
                city = _city_name(target_url)
                logger.info(f"查询油价 [{i+1}/{len(urls)}]: {city} (ID: {wid})")

                api_url = f"https://www.costco.com/AjaxGetGasPricesService?warehouseid={wid}"
                try:
                    await page.goto(api_url, timeout=15000)
                    body_text = await page.inner_text("body")
                    
                    data = json.loads(body_text.strip())
                    store_data = data.get(wid, {}) if isinstance(data, dict) else {}
                    reg = store_data.get("regular")
                    pre = store_data.get("premium")

                    if reg is None and pre is None:
                        logger.warning(f"门市 {city} 未能解析出油价: {body_text}")
                        continue

                    item = {
                        "city": city,
                        "wid": wid,
                        "reg": f"${reg}" if reg else "N/A",
                        "pre": f"${pre}" if pre else "N/A",
                    }
                    results.append(item)
                    logger.info(f"✔ 成功提取 -> {city}: Regular={item['reg']}, Premium={item['pre']}")

                except Exception as store_err:
                    logger.error(f"门市 {city} 提取异常: {store_err}")

        except Exception as e:
            logger.error(f"抓取流程遭遇严重错误: {e}", exc_info=True)
        finally:
            await browser.close()
            logger.info("浏览器已关闭")

    return results

if __name__ == "__main__":
    prices = asyncio.run(fetch_gas_prices_live(TARGET_URLS))
    print("\n" + "=" * 60)
    print("Costco 真实抓取数据汇总结果:")
    for p in prices:
        print(f"  [{p['wid']}] {p['city']:<25} | Regular: {p['reg']:<8} | Premium: {p['pre']:<8}")
    print("=" * 60 + "\n")
