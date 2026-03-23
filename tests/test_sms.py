"""
测试与调试辅助脚本：用于测试各个独立组件与流程的行为 (Test/Debug Script)
"""
from dotenv import load_dotenv
import logging
from notifier import send_sms, format_sms_body

logging.basicConfig(level=logging.INFO)
load_dotenv()

# Test data identical to what the scraper would pull
prices = [
    {"city": "Chino Hills, CA", "reg": "$5.199", "pre": "$5.559"},
    {"city": "Ontario Business Center Ontario, CA", "reg": "$4.959", "pre": "$5.199"},
    {"city": "Eastvale, CA", "reg": "$5.059", "pre": "$5.599"}
]

body = format_sms_body(prices)
print(f"Sending formatted body:\n{body}\n")
send_sms(body)
