import asyncio
import os
import random
from datetime import timedelta

import django
from django.utils import timezone
from telethon import functions
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from django.db import transaction
from app.models import ActionTask


async def subscribe_on_channel(client, channel_url):
    try:
        try:
            await client(functions.channels.JoinChannelRequest(channel=channel_url))
        except Exception as ex:
            await client(functions.messages.ImportChatInviteRequest(channel_url[14:]))
    except Exception:
        pass


async def action_process(action_task: ActionTask):
    action = await sync_to_async(lambda: action_task.action)()
    n = random.randint(1, 100)
    percent = await sync_to_async(lambda: action.percent)()
    if n <= percent:
        delay = await sync_to_async(lambda: action.delay)()
        await asyncio.sleep(delay)
        session = await sync_to_async(lambda: action_task.session)()
        client = await constant_functions.activate_session(session)
        is_channel = await sync_to_async(lambda: action.is_channel)()
        is_smile = await sync_to_async(lambda: action.is_smile)()
        link = await sync_to_async(lambda: action.link)()
        text = await sync_to_async(lambda: action.text)()
        if is_channel:
            await subscribe_on_channel(client=client, channel_url=link)
        else:
            await client.send_message(action.link, '/start')
            if is_smile:
                pass
            else:
                await client.send_message(action.link, text)

    # Используем sync_to_async для операций с БД
    await sync_to_async(action_task.delete)()


async def main():
    while True:
        # Используем sync_to_async для синхронных запросов к БД
        action_tasks = await sync_to_async(list)(ActionTask.objects.filter(is_start=False))

        for action_task in action_tasks:
            action_task.is_start = True
            await sync_to_async(action_task.save)(update_fields=['is_start'])
            asyncio.create_task(action_process(action_task))

        await asyncio.sleep(5)
