"""
主程序入口：Costco 油价监控脚本 (Main Entry Node)
负责调度抓取任务、记录日志，并在获取油价后触发 Twilio 短信通知。
主要由 GitHub Actions 每日自动触发运行。
"""
import asyncio
import logging
from config import TARGET_URLS
from scraper import fetch_gas_prices
from notifier import format_sms_body, send_sms

# 配置全局日志规范
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info(f"🚗 开始执行 Costco 直连油价抓取任务。目标门市数: {len(TARGET_URLS)}")

    try:
        # 执行抓取
        prices = await fetch_gas_prices(TARGET_URLS)
        
        # 如果未取到任何相关门市的标价，进行预警
        if not prices:
            logger.warning("未能正确捕获任何油价，有可能爬虫遭拦截，或者 Costco 更新了 DOM 节点。")
            send_sms("Costco 油价抓取失败，请检查脚本或页面结构。")
            return
            
        logger.info(f"成功收集到前 {len(prices)} 家门店油价动态，准备投递短消息...")
        
        # 封装文本形态并透过 Twilio 直发用户
        sms_body = format_sms_body(prices)
        success = send_sms(sms_body)
        
        if success:
            logger.info("🎉 核心任务顺利完结。")
        else:
            logger.error("通信断链：短信未能成功传递。")
            
    except Exception as e:
        logger.error(f"严重崩溃：主线程发生非捕获性底层错误: {e}")
        send_sms("Costco 油价脚本运行崩溃，请登录服务器检查报错。")

if __name__ == "__main__":
    asyncio.run(main())
