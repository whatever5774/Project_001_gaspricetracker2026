import asyncio
import os
import logging
from dotenv import load_dotenv
from scraper import fetch_gas_prices
from notifier import format_sms_body, send_sms

# 配置全局日志规范
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # 本地测试时，将自动寻找并载入处于同一层级的 .env 记录
    load_dotenv()
    
    # 直接访问最近的 3 家门市的 URL
    target_urls = [
        "https://www.costco.com/w/-/ca/chino%20hills/473",
        "https://www.costco.com/w/-/ca/ontario-bus-ctr-ontario/947",
        "https://www.costco.com/w/-/ca/eastvale/1317"
    ]
    
    logger.info(f"🚗 开始执行 Costco 直连油价抓取任务。目标门市数: {len(target_urls)}")
    
    try:
        # 执行抓取
        prices = await fetch_gas_prices(target_urls)
        
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
