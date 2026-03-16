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
                
                # 提取 Regular
                reg_match = re.search(r'Regular</dt><dd[^>]*><span[^>]*>\$([0-9.]+)', content_text, re.IGNORECASE)
                if reg_match:
                    reg_price = f"${reg_match.group(1)}9" # 补足 .9 尾巴
                    
                # 提取 Premium    
                pre_match = re.search(r'Premium</dt><dd[^>]*><span[^>]*>\$([0-9.]+)', content_text, re.IGNORECASE)
                if pre_match:
                    pre_price = f"${pre_match.group(1)}9" # 补足 .9 尾巴
                    
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
