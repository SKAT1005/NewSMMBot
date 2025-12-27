import asyncio
import os, django

import telethon.errors
from asgiref.sync import sync_to_async
from telethon import TelegramClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()
import accounts, subscribe, actions, views, reactions, comments, historys, unsubscribe
from const_sessions import session_list
from app.models import Sessions, Task, ViewTask, ReactionTask, CommentTask, ActionTask, SubscribeTask, HistoryViewTask, UnsubscribeTask, HistoryReactionTask



def update_status():
    Task.objects.all().update(is_start_parse_messages=False, is_start_parse_history=False)
    ViewTask.objects.all().update(is_start=False)
    ReactionTask.objects.all().update(is_start=False)
    CommentTask.objects.all().update(is_start=False)
    ActionTask.objects.all().update(is_start=False)
    SubscribeTask.objects.all().update(is_start=False)
    HistoryViewTask.objects.all().update(is_start=False)
    UnsubscribeTask.objects.all().update(is_start=False)
    HistoryReactionTask.objects.all().update(is_start=False)
CONSTANT_API_ID = 24122691
CONSTANT_API_HASH = 'a7b40fde1500ab2a0ffba45649cdecb1'



async def activate_sessions():
    sessions = await sync_to_async(list)(Sessions.objects.all())
    for session in sessions:
            print(1)
            client = TelegramClient(session.file.name, api_id=CONSTANT_API_ID, api_hash=CONSTANT_API_HASH,
                                    system_version="4.16.30-vxCUSTOM")
            await client.start()
            l = await client.get_me()
            if l:
                session_list[session.id] = client
            else:
                await sync_to_async(session.delete)()

async def main():
    await activate_sessions()
    await sync_to_async(update_status)()
    print('Начал работать')
    await asyncio.gather(
        accounts.main(),
        subscribe.main(),
        actions.main(),
        views.add_view_task_main(),
        views.main(),
        reactions.main(),
        comments.main(),
        comments.main_send_comment(),
        historys.main(),
        unsubscribe.main()
    )


if __name__ == "__main__":
    asyncio.run(main())