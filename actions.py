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
            client.send_message(entity, '/start')
            if action.is_smile:
                pass
            else:
                client.send_message(entity, action.text)
    action_task.delete()

async def main():
    while True:
        for action_task in ActionTask.objects.filter(is_start=False):
            action_task.is_start = True
            action_task.save(update_fields=['is_start'])
            asyncio.create_task(action_process(action_task))
        await asyncio.sleep(5)


