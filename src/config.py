import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
TO_PHONE_NUMBER = os.environ.get("TO_PHONE_NUMBER")

env_urls = os.environ.get("COSTCO_TARGET_URLS")
TARGET_URLS = [url.strip() for url in env_urls.split(",") if url.strip()] if env_urls else [
    "https://www.costco.com/w/-/ca/chino%20hills/473",
    "https://www.costco.com/w/-/ca/ontario-bus-ctr-ontario/947",
    "https://www.costco.com/w/-/ca/eastvale/1317"
]
