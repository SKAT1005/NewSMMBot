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
    entity = await client.get_entity(channel_url)
    try:
        await client(functions.channels.JoinChannelRequest(channel=entity))
    except Exception as ex:
        await client(functions.messages.ImportChatInviteRequest(channel_url[14:]))
    return entity.id


async def action_process(action_task: ActionTask):
    action = action_task.action
    n = random.randint(1, 100)
    if n <= action.percent:
        await asyncio.sleep(action.delay)
        session = action_task.session
        client = await constant_functions.activate_session(session)

        if action.is_channel:
            await subscribe_on_channel(client=client, channel_url=action.link)
        else:
            entity = await client.get_entity(action.link)
            await client.send_message(entity, '/start')
            if action.is_smile:
                pass
            else:
                await client.send_message(entity, action.text)

    # Используем sync_to_async для операций с БД
    await sync_to_async(action_task.delete)()


async def main():
    while True:
        # Используем sync_to_async для синхронных запросов к БД
        action_tasks = await sync_to_async(list)(ActionTask.objects.filter(is_start=False))

        for action_task in action_tasks:
            # Обновляем запись асинхронно
            await sync_to_async(action_task.save)(update_fields=['is_start'])
            asyncio.create_task(action_process(action_task))

        await asyncio.sleep(5)
