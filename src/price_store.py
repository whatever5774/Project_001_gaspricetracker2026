"""
价格缓存与比较引擎
负责读取/写入 prices_cache.json，比较新旧价格，检测变动 ≥ $0.05，
并将每次抓取结果追加到 price_history.csv。
"""
import json
import os
import csv
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional
from config import PRICE_CHANGE_THRESHOLD, ALERT_CITIES, PRICE_CACHE_FILE, PRICE_HISTORY_FILE

logger = logging.getLogger(__name__)

# 太平洋时间 (自动处理夏令时/冬令时)
PT = ZoneInfo("America/Los_Angeles")


def _pt_now() -> str:
    """返回当前太平洋时间的 ISO 格式字符串"""
    return datetime.now(PT).isoformat()


def _parse_price(price_str: str) -> Optional[float]:
    """将 '$4.59' 或 'N/A' 转为 float，无法解析返回 None"""
    if not price_str or price_str == 'N/A':
        return None
    try:
        return float(price_str.replace('$', ''))
    except (ValueError, AttributeError):
        return None


def load_cache() -> Optional[Dict]:
    """从 prices_cache.json 读取上次价格缓存，如文件不存在则返回 None"""
    if not os.path.exists(PRICE_CACHE_FILE):
        logger.info("未找到价格缓存文件，本次将视为首次运行。")
        return None
    try:
        with open(PRICE_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        logger.info(f"已加载价格缓存，上次更新: {cache.get('last_updated', '未知')}")
        return cache
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"读取价格缓存失败: {e}，将视为首次运行。")
        return None


def save_cache(prices: List[Dict[str, str]]) -> None:
    """将当前价格写入 prices_cache.json"""
    prices_dict = {}
    for item in prices:
        prices_dict[item['city']] = {
            'reg': item['reg'].replace('$', '') if item['reg'] != 'N/A' else 'N/A',
            'pre': item['pre'].replace('$', '') if item['pre'] != 'N/A' else 'N/A',
        }

    cache = {
        'last_updated': _pt_now(),
        'prices': prices_dict,
    }

    # 确保目录存在
    cache_dir = os.path.dirname(os.path.abspath(PRICE_CACHE_FILE))
    os.makedirs(cache_dir, exist_ok=True)

    with open(PRICE_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    logger.info(f"价格缓存已更新: {PRICE_CACHE_FILE}")


def compare_prices(current: List[Dict[str, str]], cached: Optional[Dict]) -> List[Dict]:
    """
    比较当前价格与缓存价格，返回变动详情列表。
    仅关注 ALERT_CITIES 中的门店，且仅比较 Regular 价格。
    变动 ≥ PRICE_CHANGE_THRESHOLD ($0.05) 才计入。

    返回格式:
    [
        {
            'city': 'Ontario Bus Ctr Ontario',
            'old_reg': '$4.59',
            'new_reg': '$4.69',
            'diff': '+$0.10',
            'diff_val': 0.10,
        },
    ]
    """
    if cached is None or 'prices' not in cached:
        return []

    changes = []
    cached_prices = cached['prices']
    alert_cities_lower = [c.strip().lower() for c in ALERT_CITIES]

    matched_any = False
    for item in current:
        city = item['city']
        if city.strip().lower() not in alert_cities_lower:
            continue
        matched_any = True

        if city not in cached_prices:
            logger.info(f"{city} 首次出现在缓存中，跳过变动检测。")
            continue

        new_reg_str = item['reg']
        old_reg_data = cached_prices[city].get('reg', 'N/A')
        old_reg_str = f"${old_reg_data}" if old_reg_data != 'N/A' else 'N/A'

        new_val = _parse_price(new_reg_str)
        old_val = _parse_price(old_reg_str)

        if new_val is None or old_val is None:
            continue

        diff_val = round(new_val - old_val, 2)
        if abs(diff_val) >= PRICE_CHANGE_THRESHOLD:
            sign = '+' if diff_val > 0 else '-'
            changes.append({
                'city': city,
                'old_reg': old_reg_str,
                'new_reg': new_reg_str,
                'diff': f"{sign}${abs(diff_val):.2f}",
                'diff_val': diff_val,
            })

    if not matched_any:
        logger.warning(
            f"未匹配到任何 ALERT_CITIES 门店！当前抓取的城市: "
            f"{[p['city'] for p in current]}，配置的 ALERT_CITIES: {ALERT_CITIES}"
        )

    if changes:
        logger.info(f"检测到 {len(changes)} 个门店价格变动 ≥ ${PRICE_CHANGE_THRESHOLD}")
    else:
        logger.info("价格未变 — 无门店 Regular 价格变动 ≥ $0.05")

    return changes


def append_history(prices: List[Dict[str, str]]) -> None:
    """将当前价格追加到 price_history.csv"""
    timestamp = _pt_now()

    history_dir = os.path.dirname(os.path.abspath(PRICE_HISTORY_FILE))
    os.makedirs(history_dir, exist_ok=True)

    file_exists = os.path.exists(PRICE_HISTORY_FILE)

    with open(PRICE_HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'city', 'reg', 'pre'])
        for item in prices:
            reg = item['reg'].replace('$', '') if item['reg'] != 'N/A' else 'N/A'
            pre = item['pre'].replace('$', '') if item['pre'] != 'N/A' else 'N/A'
            writer.writerow([timestamp, item['city'], reg, pre])

    logger.info(f"价格历史已追加至: {PRICE_HISTORY_FILE}")
