"""
主程序入口：Costco 油价监控脚本 (Main Entry Node)
负责调度抓取任务、比对价格变动、条件发送短信通知、更新缓存与历史记录。
主要由 GitHub Actions 每日自动触发运行。
支持 --weekly-report 参数发送周报邮件。
"""
import asyncio
import argparse
import logging
from config import TARGET_URLS
from scraper import fetch_gas_prices
from notifier import (
    format_sms_body, format_change_sms, send_sms,
    send_email, format_weekly_report,
)
from price_store import load_cache, save_cache, compare_prices, append_history

# 配置全局日志规范
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_price_check():
    """主抓取 + 变动检测 + 条件短信流程"""
    logger.info(f"🚗 开始执行 Costco 直连油价抓取任务。目标门市数: {len(TARGET_URLS)}")

    try:
        # 1. 执行抓取
        prices = await fetch_gas_prices(TARGET_URLS)

        # 如果未取到任何相关门市的标价，进行预警
        if not prices:
            logger.warning("未能正确捕获任何油价，有可能爬虫遭拦截，或者 Costco 更新了页面结构。")
            send_sms("Costco 油价抓取失败，请检查脚本或页面结构。")
            return

        logger.info(f"成功收集到 {len(prices)} 家门店油价动态")

        # 2. 追加价格到历史 CSV
        append_history(prices)

        # 3. 读取缓存的上次价格
        cached = load_cache()

        # 4. 首次运行：仅保存基线，不发短信
        if cached is None:
            logger.info("首次运行 — 保存当前价格为基线，不发送短信。")
            save_cache(prices)
            return

        # 5. 比较价格变动（仅 Ontario 和 Eastvale 的 Regular）
        changes = compare_prices(prices, cached)

        # 6. 更新缓存文件
        save_cache(prices)

        # 7. 根据变动结果决定是否发短信
        if changes:
            sms_body = format_change_sms(changes)
            success = send_sms(sms_body)
            if success:
                logger.info("🎉 价格变动短信已发送。")
            else:
                logger.error("通信断链：短信未能成功传递。")
        else:
            logger.info("价格未变，不发送短信。")

    except Exception as e:
        logger.error(f"严重崩溃：主线程发生非捕获性底层错误: {e}")
        send_sms("Costco 油价脚本运行崩溃，请登录服务器检查报错。")


async def run_weekly_report():
    """发送周报邮件，包含所有 3 家门店当前油价"""
    logger.info("📊 开始生成周报邮件...")

    try:
        prices = await fetch_gas_prices(TARGET_URLS)

        if not prices:
            logger.warning("未能正确捕获任何油价，无法生成周报。")
            return

        # 追加到历史记录
        append_history(prices)

        # 更新缓存
        save_cache(prices)

        # 格式化并发送周报
        subject = "Costco Gas Weekly Report"
        body = format_weekly_report(prices)
        success = send_email(subject, body)

        if success:
            logger.info("🎉 周报邮件发送成功。")
        else:
            logger.error("周报邮件发送失败。")

    except Exception as e:
        logger.error(f"周报生成失败: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Costco Gas Price Tracker")
    parser.add_argument(
        '--weekly-report',
        action='store_true',
        help='发送周报邮件（包含所有门店当前油价）',
    )
    args = parser.parse_args()

    if args.weekly_report:
        await run_weekly_report()
    else:
        await run_price_check()


if __name__ == "__main__":
    asyncio.run(main())
