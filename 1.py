import asyncio

import emoji
from telethon import TelegramClient, types
from telethon import functions
from telethon.utils import resolve_id

client = TelegramClient('12222', 27019030, '27e28e8a538190cae3310c283d63f4b2')
async def main():
    print(1)
    await client.start(phone='+79027573093', password='1005')
    entity = await client.get_entity(-1001380230142)
    #print(entity.stringify())
    #result = await client(functions.stories.GetPeerMaxIDsRequest([861924750, 1795070154, 1795070154]))
    result = await client(functions.stories.SendReactionRequest(entity, entity.stories_max_id, types.ReactionEmoji(emoticon='❤️')))
    print(result)

async def main1():
    while True:
        print("Привет из main1!")
        await asyncio.sleep(0.5) # Неблокирующая задержка

async def main3():
    while True:
        asyncio.create_task(main1())
        asyncio.create_task(main())
        print(111111111)
        await asyncio.sleep(10)


asyncio.run(main3())