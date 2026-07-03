"""
消息推送模块：Twilio SMS 客户端 + Gmail 周报邮件
封装了短信的格式化逻辑和发送逻辑，以及通过 Gmail SMTP 发送周报邮件。
依赖环境变量中配置的 TWILIO 密钥、手机号以及 Gmail 凭证。
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from twilio.rest import Client
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_PHONE_NUMBER,
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD, REPORT_TO_EMAIL,
)

logger = logging.getLogger(__name__)


def format_sms_body(prices: List[Dict[str, str]]) -> str:
    """遵循极简要求组合短信，确保前 3 家油站信息合在一条发，去除一切 Emoji
    和特殊符号以防运营商拦截"""
    if not prices:
        return "Costco Gas Error: No prices found or DOM changed."

    lines = ["Costco Gas Update:"]
    for i, data in enumerate(prices, 1):
        lines.append(f"{i}. {data['city']}: Reg {data['reg']}, Pre {data['pre']}")

    return "\n".join(lines)


def format_change_sms(changes: List[Dict]) -> str:
    """将价格变动详情格式化为新旧对比短信：
    Costco Gas Price Change:
    1. Ontario: $4.59 → $4.69 (+$0.10)
    2. Eastvale: $4.55 → $4.60 (+$0.05)
    """
    if not changes:
        return ""

    lines = ["Costco Gas Price Change:"]
    for i, ch in enumerate(changes, 1):
        lines.append(f"{i}. {ch['city']}: {ch['old_reg']} → {ch['new_reg']} ({ch['diff']})")

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
        logger.info(f"短信发送成功, 消息 SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"发送短信失败，请校验凭证正确性: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    """透过 Gmail SMTP (smtplib) 发送邮件，使用 App Password 认证"""
    try:
        if not all([GMAIL_ADDRESS, GMAIL_APP_PASSWORD, REPORT_TO_EMAIL]):
            logger.error("缺少 Gmail SMTP 相关的环境变量配置！")
            return False

        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = REPORT_TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, REPORT_TO_EMAIL, msg.as_string())

        logger.info(f"周报邮件发送成功 -> {REPORT_TO_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return False


def format_weekly_report(prices: List[Dict[str, str]]) -> str:
    """格式化周报邮件正文，包含所有门店当前油价"""
    if not prices:
        return "Costco Gas Weekly Report\n\nNo price data available this week."

    lines = [
        "Costco Gas Weekly Report",
        "=" * 30,
        "",
    ]

    for item in prices:
        lines.append(f"  {item['city']}:")
        lines.append(f"    Regular: {item['reg']}")
        lines.append(f"    Premium: {item['pre']}")
        lines.append("")

    lines.append("=" * 30)
    lines.append("Sent by Costco Gas Price Tracker")
    return "\n".join(lines)
