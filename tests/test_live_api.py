"""
Costco 油价真实接口实时探测脚本 (无 Mock，真实网络请求)
用于验证对 Costco AjaxGetGasPricesService API 的连通性与数据准确性
"""
import json
import logging
import re
import urllib.request
import ssl
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LiveApiTest")

TARGET_URLS = [
    "https://www.costco.com/w/-/ca/chino%20hills/473",
    "https://www.costco.com/w/-/ca/ontario-bus-ctr-ontario/947",
    "https://www.costco.com/w/-/ca/eastvale/1317"
]

def extract_warehouse_id(url: str) -> str:
    m = re.search(r'/(\d+)$', url.rstrip('/'))
    return m.group(1) if m else ""

def extract_city_name(url: str) -> str:
    segment = url.rstrip('/').split('/')[-2]
    return segment.replace('%20', ' ').replace('-', ' ').title()

def test_fetch_live() -> List[Dict[str, str]]:
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
    }
    ssl_context = ssl.create_default_context()

    logger.info("=== 开始探测 Costco 官方油价接口 (真实请求) ===")
    for url in TARGET_URLS:
        wid = extract_warehouse_id(url)
        city = extract_city_name(url)
        api_url = f"https://www.costco.com/AjaxGetGasPricesService?warehouseid={wid}"
        logger.info(f"正在查询门市: {city} (ID: {wid}) -> {api_url}")

        req = urllib.request.Request(api_url, headers={**headers, "Referer": url})
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                store_data = data.get(wid, {})
                reg = store_data.get("regular")
                pre = store_data.get("premium")

                logger.info(f"状态码: {status} | 返回原始数据: {data}")
                logger.info(f"解析结果 -> {city}: Regular=${reg}, Premium=${pre}")

                results.append({
                    "city": city,
                    "wid": wid,
                    "regular": f"${reg}" if reg else "N/A",
                    "premium": f"${pre}" if pre else "N/A",
                })
        except Exception as e:
            logger.error(f"门市 {city} (ID: {wid}) 查询失败: {e}")

    logger.info("=== 探测完毕，汇总结果 ===")
    return results

if __name__ == "__main__":
    res = test_fetch_live()
    print("\n" + "=" * 50)
    print("真实油价接口探测汇总表:")
    for item in res:
        print(f"  [{item['wid']}] {item['city']:<25} | Reg: {item['regular']:<7} | Pre: {item['premium']:<7}")
    print("=" * 50 + "\n")
