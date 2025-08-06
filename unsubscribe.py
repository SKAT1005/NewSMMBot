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

from app.models import SubscribeTask, ActionTask, UnsubscribeTask


async def unsubscribe_process(unsubscribe_task: UnsubscribeTask):
    task = unsubscribe_task.task
    while True:
        if unsubscribe_task.next_action <= timezone.now():
            sessions = list(unsubscribe_task.sessions.all())
            session = sessions[unsubscribe_task.unsubscribed_sessions]
            client = await constant_functions.activate_session(session)
            entity = await client.get_entity(task.channel_link)
            client(functions.channels.DeleteChannelRequest(
                channel=entity
            ))
            client.disconnect()
        if unsubscribe_task.unsubscribed_sessions == len(unsubscribe_task.sessions.all()):
            unsubscribe_task.delete()
            break
        await asyncio.sleep(random.randint(100, 500)/100)


async def main():
    while True:
        for unsubscribe_task in UnsubscribeTask.objects.filter(is_start=False):
            unsubscribe_task.is_start = True
            unsubscribe_task.save(update_fields=['is_start'])
            asyncio.create_task(unsubscribe_process(unsubscribe_task))
        await asyncio.sleep(60)


