import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# gate limits, tweak these for the demo
SESSION_SPEND_CAP_INR = int(os.getenv("SESSION_SPEND_CAP_INR", "5000"))
MAX_QTY_PER_ITEM = int(os.getenv("MAX_QTY_PER_ITEM", "3"))
MIN_SECONDS_BETWEEN_ORDERS = float(os.getenv("MIN_SECONDS_BETWEEN_ORDERS", "2"))

DB_PATH = os.getenv("DB_PATH", "audit.db")
CATALOG_PATH = os.getenv("CATALOG_PATH", "data/catalog.json")

RAZORPAY_CONFIGURED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
GROQ_CONFIGURED = bool(GROQ_API_KEY)
