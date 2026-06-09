"""
消息推送模块：Twilio SMS 客户端
封装了短信的格式化逻辑和发送逻辑，用于将提取到的油价简报直发至目标手机。
依赖环境变量中配置的 TWILIO 密钥和手机号。
"""
import logging
from typing import List, Dict
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_PHONE_NUMBER

logger = logging.getLogger(__name__)

def format_sms_body(prices: List[Dict[str, str]]) -> str:
    """遵循极简要求组合短信，确保前 3 家油站信息合在一条发，去除一切 Emoji 和特殊符号以防运营商拦截"""
    if not prices:
        return "Costco Gas Error: No prices found or DOM changed."
        
    lines = ["Costco Gas Update:"]
    for i, data in enumerate(prices, 1):
        lines.append(f"{i}. {data['city']}: Reg {data['reg']}, Pre {data['pre']}")
        
    return "\n".join(lines)

def send_sms(body: str) -> bool:
    """透过 Twilio SDK 对目标手机投递生成的简报"""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_PHONE_NUMBER]):
            logger.error("缺少 Twilio 相关的环境变量配置！请检查您的系统设定 (或 .env 文件)。")
            return False

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=TO_PHONE_NUMBER
        )
        logger.info(f"✅ 短信发送成功, 消息 SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"❌ 发送短信失败，请校验凭证正确性: {e}")
        return False
