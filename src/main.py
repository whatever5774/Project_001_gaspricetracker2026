"""
主程序入口：Costco 油价监控脚本 (Main Entry Node)
负责调度抓取任务、比对价格变动、推送微信提醒 (企业微信/PushPlus/Server酱)、
更新缓存与历史记录 CSV（驱动 GitHub Pages 静态看板）。
主要由 GitHub Actions 每日自动触发运行。
支持 --weekly-report 参数发送周报消息。
"""
import asyncio
import argparse
import logging
from config import TARGET_URLS, DASHBOARD_URL
from scraper import fetch_gas_prices
from notifier import (
    send_wechat, format_change_wechat, format_weekly_wechat,
    send_sms, send_email, format_weekly_report,
)
from price_store import load_cache, save_cache, compare_prices, append_history

# 配置全局日志规范
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_price_check():
    """主抓取 + 变动检测 + 微信提醒流程"""
    logger.info(f"🚗 开始执行 Costco 直连油价抓取任务。目标门市数: {len(TARGET_URLS)}")

    try:
        # 1. 执行抓取
        prices = await fetch_gas_prices(TARGET_URLS)

        # 如果未取到任何相关门市的标价，进行预警
        if not prices:
            logger.warning("未能正确捕获任何油价，有可能爬虫遭拦截，或者 Costco 更新了页面结构。")
            send_wechat("⚠️ Costco 油价抓取异常", "未能正确捕获任何油价，有可能爬虫遭拦截或页面结构已变动。")
            return

        logger.info(f"成功收集到 {len(prices)} 家门店油价动态")

        # 2. 追加价格到历史 CSV (供静态看板渲染)
        append_history(prices)

        # 3. 读取缓存的上次价格
        cached = load_cache()

        # 4. 首次运行：仅保存基线，不发提醒
        if cached is None:
            logger.info("首次运行 — 保存当前价格为基线，不发送变动提醒。")
            save_cache(prices)
            return

        # 5. 比较价格变动（仅 Ontario 和 Eastvale 的 Regular）
        changes = compare_prices(prices, cached)

        # 6. 更新缓存文件
        save_cache(prices)

        # 7. 根据变动结果决定是否发微信提醒
        if changes:
            wechat_body = format_change_wechat(changes, prices)
            success = send_wechat("⛽ Costco 油价变动提醒", wechat_body)
            if success:
                logger.info("🎉 价格变动微信通知已成功送达。")
            else:
                logger.warning("未能成功发送微信通知（请检查 WECHAT_WEBHOOK_URL / PUSHPLUS_TOKEN 配置）。")
        else:
            logger.info("价格未变或变动 < $0.05，跳过微信推送。")

    except Exception as e:
        logger.error(f"严重崩溃：主线程发生非捕获性底层错误: {e}")
        send_wechat("🚨 Costco 油价监控运行崩溃", f"脚本运行发生未捕获异常: `{e}`")


async def run_weekly_report():
    """发送周报消息（包含所有门店当前油价与看板链接）"""
    logger.info("📊 开始生成周报消息...")

    try:
        prices = await fetch_gas_prices(TARGET_URLS)

        if not prices:
            logger.warning("未能正确捕获任何油价，无法生成周报。")
            return

        # 追加到历史记录
        append_history(prices)

        # 更新缓存
        save_cache(prices)

        # 1. 发送微信周报推送
        wechat_body = format_weekly_wechat(prices)
        wx_ok = send_wechat("📊 Costco 油价每周简报", wechat_body)
        if wx_ok:
            logger.info("🎉 微信周报推送成功。")
        else:
            logger.warning("微信周报未发送（无有效微信推送凭证）。")

        # 2. 备选：如果配置了 Gmail，也发一份邮件
        email_body = format_weekly_report(prices)
        send_email("Costco Gas Weekly Report", email_body)

    except Exception as e:
        logger.error(f"周报生成失败: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Costco Gas Price Tracker")
    parser.add_argument(
        '--weekly-report',
        action='store_true',
        help='发送周报消息（包含所有门店当前油价）',
    )
    args = parser.parse_args()

    if args.weekly_report:
        await run_weekly_report()
    else:
        await run_price_check()


if __name__ == "__main__":
    asyncio.run(main())
