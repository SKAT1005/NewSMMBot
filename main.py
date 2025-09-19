import asyncio
import os, django

from asgiref.sync import sync_to_async
from telethon import TelegramClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()
import accounts, subscribe, actions, views, reactions, comments, historys, unsubscribe
from const_sessions import session_list
from app.models import Sessions

CONSTANT_API_ID = 24122691
CONSTANT_API_HASH = 'a7b40fde1500ab2a0ffba45649cdecb1'

async def main():
    sessions = await sync_to_async(list)(Sessions.objects.all())
    for session in sessions:
        session_list[session.id] = TelegramClient(session.file.name, api_id=CONSTANT_API_ID, api_hash=CONSTANT_API_HASH,
                                 system_version="4.16.30-vxCUSTOM")
    await asyncio.gather(
        #accounts.main(),
        #subscribe.main(),
        #actions.main(),
        #views.add_view_task_main(),
        #views.main(),
        #reactions.main(),
        #comments.main(),
        #comments.main_send_comment(),
        #historys.main(),
        unsubscribe.main()
    )


if __name__ == "__main__":
    asyncio.run(main())