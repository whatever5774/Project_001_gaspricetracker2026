"""
前端页面抓取模块：Costco 油价防反爬逻辑
使用 playwright-stealth 模拟真实的人类浏览器操作，直接访问指定 Costco 门店页面，
提取 Regular 与 Premium 标号的汽油价格，并格式化返回。
"""
import asyncio
import random
import logging
import re
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

async def fetch_gas_prices(urls: List[str]) -> List[Dict[str, str]]:
    """通过直接访问 Costco 门店独立 URL，抓取油价"""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-http2",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = await context.new_page()
        stealth_plugin = Stealth()
        await stealth_plugin.apply_stealth_async(page)
        
        try:
            for i, target_url in enumerate(urls):
                logger.info(f"访问门店页面 [{i+1}/{len(urls)}]: {target_url}")
                await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                
                # 第一个页面给予较多时间用于处理可能出现的人机验证
                if i == 0:
                    logger.info("如果遇到防护，请在弹出的浏览器中手动点按确认 (限时 60 秒) ...")
                    await asyncio.sleep(15)
                else:
                    await asyncio.sleep(8)
                    
                content_text = await page.content()
                
                # 解析门店名称 (可以从 URL 推断或从 title 推断)
                city_match = re.search(r'<title>(.*?)Warehouse.*?Costco</title>', content_text, re.IGNORECASE)
                if city_match:
                    city_name = city_match.group(1).strip()
                else:
                    city_name = target_url.split('/')[-2].replace('%20', ' ').title()
                
                reg_price = "暂无数据"
                pre_price = "暂无数据"
                
                # 提取 Regular (动态获取完整的页面显示的文本，去除硬代码 .9)
                try:
                    reg_elem = page.locator("dt:has-text('Regular') + dd").first
                    if await reg_elem.count() > 0:
                        reg_price = (await reg_elem.inner_text()).replace('\n', '').replace(' ', '').strip()
                except Exception as e:
                    logger.debug(f"Regular price locate error: {e}")
                    
                # 提取 Premium (动态获取完整的页面显示的文本，去除硬代码 .9)
                try:
                    pre_elem = page.locator("dt:has-text('Premium') + dd").first
                    if await pre_elem.count() > 0:
                        pre_price = (await pre_elem.inner_text()).replace('\n', '').replace(' ', '').strip()
                except Exception as e:
                    logger.debug(f"Premium price locate error: {e}")
                    
                if reg_price != "暂无数据" or pre_price != "暂无数据":
                    results.append({
                        "city": city_name,
                        "reg": reg_price,
                        "pre": pre_price
                    })
                    logger.info(f"成功提取 -> {city_name}: Reg {reg_price}, Pre {pre_price}")
                else:
                    logger.warning(f"页面未找到 {city_name} 的油价信息。")
                    
        except Exception as e:
            logger.error(f"抓取流程遭遇错误或连接超时: {e}")
        finally:
            await browser.close()
            
    return results
