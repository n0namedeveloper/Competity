import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.bot.telegram import telegram_bot
from app.config import settings

async def main():
    await telegram_bot.initialize()
    print(f"Sending test to {settings.telegram_chat_id}")
    success = await telegram_bot.send_report("This is a test report from Competity!")
    print(f"Success: {success}")

if __name__ == "__main__":
    asyncio.run(main())
