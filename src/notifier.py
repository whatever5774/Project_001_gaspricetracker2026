"""
消息推送模块：微信推送 (企业微信群机器人 / PushPlus / Server酱) + 邮件 + 短信
支持富文本 Markdown 排版与静态看板链接跳转。
"""
import json
import logging
import smtplib
import urllib.request
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    WECHAT_WEBHOOK_URL, PUSHPLUS_TOKEN, SERVERCHAN_KEY, DASHBOARD_URL,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_PHONE_NUMBER,
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD, REPORT_TO_EMAIL,
)

logger = logging.getLogger(__name__)
PT = ZoneInfo("America/Los_Angeles")


def _now_str() -> str:
    """返回太平洋时间格式化字符串"""
    return datetime.now(PT).strftime("%Y-%m-%d %H:%M PT")


# ══════════════════════════════════════════════════════════════
# 微信推送核心实现 (企业微信 Webhook / PushPlus / Server酱)
# ══════════════════════════════════════════════════════════════

def send_wechat(title: str, markdown_content: str) -> bool:
    """
    统一微信推送接口：优先通过配置的渠道发送 Markdown 消息
    支持：
    1. 企业微信群机器人 (WECHAT_WEBHOOK_URL)
    2. PushPlus 推送加 (PUSHPLUS_TOKEN)
    3. Server酱 Turbo (SERVERCHAN_KEY)
    """
    success = False
    has_any_channel = False
    ssl_ctx = ssl.create_default_context()

    # 1. 企业微信群机器人 Webhook
    if WECHAT_WEBHOOK_URL:
        has_any_channel = True
        try:
            payload = json.dumps({
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n\n{markdown_content}"
                }
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                WECHAT_WEBHOOK_URL,
                data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("errcode") == 0:
                    logger.info("✔ 企业微信机器人消息推送成功")
                    success = True
                else:
                    logger.error(f"企业微信机器人返回错误: {res_data}")
        except Exception as e:
            logger.error(f"发送企业微信机器人通知失败: {e}")

    # 2. PushPlus 推送加 (微信服务号通知)
    if PUSHPLUS_TOKEN:
        has_any_channel = True
        try:
            payload = json.dumps({
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": markdown_content,
                "template": "markdown"
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                "https://www.pushplus.plus/send",
                data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("code") == 200:
                    logger.info("✔ PushPlus 微信通知推送成功")
                    success = True
                else:
                    logger.error(f"PushPlus 推送返回错误: {res_data}")
        except Exception as e:
            logger.error(f"发送 PushPlus 微信通知失败: {e}")

    # 3. Server酱 Turbo (微信服务号通知)
    if SERVERCHAN_KEY:
        has_any_channel = True
        try:
            payload = json.dumps({
                "title": title,
                "desp": markdown_content
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send",
                data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("code") == 0:
                    logger.info("✔ Server酱微信通知推送成功")
                    success = True
                else:
                    logger.error(f"Server酱返回错误: {res_data}")
        except Exception as e:
            logger.error(f"发送 Server酱通知失败: {e}")

    if not has_any_channel:
        logger.warning(
            "未配置任何微信推送环境变量！请在 GitHub Secrets 或 .env 中设置 "
            "WECHAT_WEBHOOK_URL(企微机器人) / PUSHPLUS_TOKEN / SERVERCHAN_KEY 之一。"
        )
        return False

    return success


def format_change_wechat(changes: List[Dict], current_prices: List[Dict[str, str]]) -> str:
    """格式化价格变动微信 Markdown 消息"""
    lines = [
        f"> 🕒 更新时间: {_now_str()}",
        "",
        "#### 📢 价格变动重点门市:",
    ]
    for ch in changes:
        color = "warning" if "+" in ch["diff"] else "info"
        lines.append(f"- **{ch['city']}**: {ch['old_reg']} → **{ch['new_reg']}** (`{ch['diff']}`)")

    lines.append("")
    lines.append("#### ⛽ 当前全门店实时油价:")
    for item in current_prices:
        lines.append(f"- **{item['city']}**: Reg `{item['reg']}` | Pre `{item['pre']}`")

    lines.append("")
    lines.append(f"> 📊 [点击打开油价历史走势看板]({DASHBOARD_URL})")

    return "\n".join(lines)


def format_weekly_wechat(prices: List[Dict[str, str]]) -> str:
    """格式化周报微信 Markdown 消息"""
    lines = [
        f"> 🕒 统计时间: {_now_str()}",
        "",
        "#### ⛽ 本周全门店最新油价看板:",
    ]
    for item in prices:
        lines.append(f"- **{item['city']}**: Regular `{item['reg']}` | Premium `{item['pre']}`")

    lines.append("")
    lines.append(f"> 📊 [点击打开油价历史走势看板]({DASHBOARD_URL})")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# 兼容性备用支持：邮件与短信
# ══════════════════════════════════════════════════════════════

def send_email(subject: str, body: str) -> bool:
    """透过 Gmail SMTP (smtplib) 发送邮件"""
    try:
        if not all([GMAIL_ADDRESS, GMAIL_APP_PASSWORD, REPORT_TO_EMAIL]):
            logger.warning("未配置完整 Gmail SMTP 环境变量，跳过邮件发送。")
            return False

        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = REPORT_TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, REPORT_TO_EMAIL, msg.as_string())

        logger.info(f"邮件发送成功 -> {REPORT_TO_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return False


def format_weekly_report(prices: List[Dict[str, str]]) -> str:
    """格式化周报邮件纯文本内容"""
    if not prices:
        return "Costco Gas Weekly Report\n\nNo price data available this week."

    lines = [
        "Costco Gas Weekly Report",
        "=" * 30,
        f"Time: {_now_str()}",
        "",
    ]
    for item in prices:
        lines.append(f"  {item['city']}:")
        lines.append(f"    Regular: {item['reg']}")
        lines.append(f"    Premium: {item['pre']}")
        lines.append("")

    lines.append(f"Dashboard: {DASHBOARD_URL}")
    lines.append("=" * 30)
    return "\n".join(lines)


def send_sms(body: str) -> bool:
    """可选 Twilio 短信备用"""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TO_PHONE_NUMBER]):
            return False
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=TO_PHONE_NUMBER
        )
        logger.info(f"短信发送成功, 消息 SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"发送短信失败: {e}")
        return False
