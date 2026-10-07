import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
