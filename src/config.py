import os
from dotenv import load_dotenv

load_dotenv()

# ── 微信推送配置 (企业微信 Webhook / PushPlus / Server酱) ──────────
# 1. 企业微信群机器人 Webhook (推荐: 群设置 -> 添加机器人 -> 获取 Webhook 地址)
WECHAT_WEBHOOK_URL = os.environ.get("WECHAT_WEBHOOK_URL")

# 2. PushPlus 推送加 (微信服务号推送: https://www.pushplus.plus/)
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")

# 3. Server酱 Turbo (微信服务号推送: https://sct.ftqq.com/)
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY")

# 静态看板地址 (Cloudflare Pages 托管)
DASHBOARD_URL = os.environ.get(
    "DASHBOARD_URL",
    "https://costco-gas-tracker.pages.dev"
)

# ── Twilio 凭证 (可选，保留向后兼容) ─────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
TO_PHONE_NUMBER = os.environ.get("TO_PHONE_NUMBER")

# ── 目标门店 URL ─────────────────────────────────────────
env_urls = os.environ.get("COSTCO_TARGET_URLS")
TARGET_URLS = [url.strip() for url in env_urls.split(",") if url.strip()] if env_urls else [
    "https://www.costco.com/w/-/ca/chino%20hills/473",
    "https://www.costco.com/w/-/ca/ontario-bus-ctr-ontario/947",
    "https://www.costco.com/w/-/ca/eastvale/1317"
]

# ── 价格变动检测配置 ─────────────────────────────────────
# 仅 Regular 价格变动 ≥ $0.05 才触发微信提醒
PRICE_CHANGE_THRESHOLD = 0.05

# 触发提醒的门店列表（城市名须与 scraper._city_name() 输出一致）
ALERT_CITIES = ["Ontario Bus Ctr Ontario", "Eastvale"]

# ── 文件路径 ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 价格缓存文件（存储上次抓取的价格，用于变动比对）
PRICE_CACHE_FILE = os.environ.get("PRICE_CACHE_FILE", os.path.join(BASE_DIR, "prices_cache.json"))

# 价格历史 CSV 文件（每次抓取追加一行，供 Dashboard 使用）
PRICE_HISTORY_FILE = os.environ.get("PRICE_HISTORY_FILE", os.path.join(BASE_DIR, "../docs/price_history.csv"))

# ── Gmail SMTP 配置（可选周报邮件备份）──────────────────
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
REPORT_TO_EMAIL = os.environ.get("REPORT_TO_EMAIL")
