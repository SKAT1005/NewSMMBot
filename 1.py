import asyncio
import datetime
import time

import emoji
from telethon import TelegramClient, types
from telethon import functions
from telethon.utils import resolve_id

client = TelegramClient('12222', 27019030, '27e28e8a538190cae3310c283d63f4b2')
async def main():
    print(1)
    await client.start(phone='+79027573093', password='1005')
    entity = await client.get_profile_photos(2044396882)
    l = await client.download_media(entity[0], '1.jpg')
    pass

async def main1():
    while True:
        print("Привет из main1!")
        await asyncio.sleep(0.5) # Неблокирующая задержка


asyncio.run(main())
