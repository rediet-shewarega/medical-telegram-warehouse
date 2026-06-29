import os
import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_MESSAGES_DIR = BASE_DIR / "data" / "raw" / "telegram_messages"
RAW_IMAGES_DIR = BASE_DIR / "data" / "raw" / "images"
LOGS_DIR = BASE_DIR / "logs"

LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOGS_DIR / "scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

CHANNELS = {
    "chemed": "CheMed123",
    "lobelia_cosmetics": "lobelia4cosmetics",
    "tikvah_pharma": "tikvahpharma",
    "hakimapps_guideline": "HakimApps_Guideline" 
}    


async def scrape_channel(client, channel_name, channel_username, limit=100):
    today = datetime.now().strftime("%Y-%m-%d")

    message_folder = RAW_MESSAGES_DIR / today
    image_folder = RAW_IMAGES_DIR / channel_name

    message_folder.mkdir(parents=True, exist_ok=True)
    image_folder.mkdir(parents=True, exist_ok=True)

    output_file = message_folder / f"{channel_name}.json"

    messages = []

    logging.info(f"Started scraping channel: {channel_name}")

    async for message in client.iter_messages(channel_username, limit=limit):
        image_path = None

        if message.photo:
            image_path = image_folder / f"{message.id}.jpg"
            await client.download_media(message, file=str(image_path))

        record = {
            "message_id": message.id,
            "channel_name": channel_name,
            "message_date": str(message.date),
            "message_text": message.message,
            "has_media": bool(message.media),
            "image_path": str(image_path) if image_path else None,
            "views": message.views,
            "forwards": message.forwards
        }

        messages.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

    logging.info(f"Finished scraping {channel_name}. Total messages: {len(messages)}")


async def main():
    client = TelegramClient("telegram_session", API_ID, API_HASH)

    await client.start(phone=PHONE)

    for channel_name, channel_username in CHANNELS.items():
        try:
            await scrape_channel(client, channel_name, channel_username)
        except Exception as e:
            logging.error(f"Error scraping {channel_name}: {e}")

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())