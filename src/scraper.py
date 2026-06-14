"""
前端页面抓取模块：Costco 油价防反爬逻辑
通过访问 Costco 门店页面建立浏览器会话，然后调用内部 AjaxGetGasPricesService API
直接获取 JSON 格式油价数据，不再依赖 DOM 选择器。
"""
import asyncio
import logging
import re
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

logger = logging.getLogger(__name__)


def _warehouse_id(url: str) -> str:
    """从 URL 末尾提取仓库 ID，例如 /473 → 473"""
    m = re.search(r'/(\d+)$', url.rstrip('/'))
    if not m:
        raise ValueError(f"无法从 URL 提取 warehouse ID: {url}")
    return m.group(1)


def _city_name(url: str) -> str:
    """从 URL 路径中提取城市名，例如 /ca/chino%20hills/473 → Chino Hills"""
    segment = url.rstrip('/').split('/')[-2]
    return segment.replace('%20', ' ').replace('-', ' ').title()


async def fetch_gas_prices(urls: List[str]) -> List[Dict[str, str]]:
    """通过 AjaxGetGasPricesService API 直接获取每家门市的油价"""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            # 先访问第一个仓库页面建立浏览器会话（API 需要合法 session cookie）
            first_url = urls[0]
            logger.info(f"建立会话: 访问 {first_url}")
            await page.goto(first_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(8)

            for i, target_url in enumerate(urls):
                wid = _warehouse_id(target_url)
                city = _city_name(target_url)
                logger.info(f"查询油价 [{i+1}/{len(urls)}]: {city} (ID: {wid})")

                resp = await page.evaluate(
                    f'async () => {{ const r = await fetch("/AjaxGetGasPricesService?warehouseid={wid}"); return await r.json(); }}'
                )

                data = resp.get(wid, {}) if isinstance(resp, dict) else {}
                reg = data.get("regular")
                pre = data.get("premium")

                if reg is None and pre is None:
                    logger.warning(f"API 未返回 {city} 的油价数据: {resp}")
                    continue

                results.append({
                    "city": city,
                    "reg": f"${reg}" if reg else "N/A",
                    "pre": f"${pre}" if pre else "N/A",
                })
                logger.info(f"成功提取 -> {city}: Reg ${reg}, Pre ${pre}")

        except Exception as e:
            logger.error(f"抓取流程遭遇错误: {e}", exc_info=True)
        finally:
            await browser.close()

    return results
