import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER = int(os.getenv("BOT_OWNER"))
GUILD = int(os.getenv("DISCORD_GUILD")
