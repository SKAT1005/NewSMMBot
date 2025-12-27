import asyncio
import os, django

import telethon
from asgiref.sync import sync_to_async
from telethon import TelegramClient
from telethon.tl import types, functions
from telethon.tl.functions import photos
from telethon.tl.functions.messages import SendReactionRequest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()
from app.models import Sessions, DonorPhoto, Task

CONSTANT_API_ID = 24122691
CONSTANT_API_HASH = 'a7b40fde1500ab2a0ffba45649cdecb1'

# l = DonorPhoto.objects.all()
# l.delete()

channel_id = 'https://t.me/+s_081QojQtY1YTJi'
print(channel_id)
async def main():
    sessions = await sync_to_async(list)(Sessions.objects.all())
    for session in sessions:
        try:
            client = TelegramClient(session.file.name, api_id=CONSTANT_API_ID, api_hash=CONSTANT_API_HASH,
                                     system_version="4.16.30-vxCUSTOM")
            await client.connect()
            l = await client(functions.messages.GetMessagesViewsRequest(
                    peer=channel_id,
                    id=[2,3,4],
                    increment=True
                ))
            print(l)
            # photoss = await client.get_profile_photos('me')
            # l = await client(photos.DeletePhotosRequest(photoss))
            # pass
            break
        except Exception as e:
            print(e)
            break
            # session_id = await sync_to_async(lambda: session.id)()
            # print(f'Удалил сессию с ID {session_id}')
            # await sync_to_async(session.delete)()


if __name__ == '__main__':
    asyncio.run(main())