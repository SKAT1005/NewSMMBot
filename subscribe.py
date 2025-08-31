import asyncio
import os
from datetime import timedelta

import django
from django.utils import timezone
from telethon import functions
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()


from app.models import SubscribeTask, ActionTask


async def create_action(task, session):
    for action in task.action.all():
        start_time = timezone.now() + timedelta(minutes=action.delay)
        ActionTask.objects.create(
            action=action,
            session=session,
            start_time=start_time
        )


async def subscribe_on_channel(client, channel_url):
    entity = await client.get_entity(channel_url)
    try:
        await client(functions.channels.JoinChannelRequest(channel=entity))
    except Exception as ex:
        await client(functions.messages.ImportChatInviteRequest(channel_url[14:]))
    return entity.id

async def subscribe_process(subscribe_task: SubscribeTask):
    task = subscribe_task.task
    while True:
        if subscribe_task.next_action <= timezone.now():
            sessions = list(subscribe_task.sessions.all())
            session = sessions[subscribe_task.subscribed_sessions]
            client = await constant_functions.activate_session(session)
            channel_id = await subscribe_on_channel(client=client, channel_url=task.channel_link)
            subscribe_task.subscribed_sessions += 1
            subscribe_task.save(update_fields=['subscribed_sessions'])
            if not task.channel_id:
                task.channel_id = channel_id
                task.save(update_fields=['channel_id'])
            if not task.last_post_id:
                last_post_id, last_story_id = await constant_functions.get_last_post_and_story_id(client=client, channel_id=channel_id)
                task.last_post_id = last_post_id
                task.last_story_id = last_story_id
                task.save(update_fields=['last_post_id', 'last_story_id'])
                await client.disconnect()
            await create_action(task=task, session=session)
        if subscribe_task.subscribed_sessions == len(subscribe_task.sessions.all()):
            subscribe_task.delete()
            break
        await asyncio.sleep(subscribe_task.sleep_time)

async def main():
    while True:
        for subscribe_task in SubscribeTask.objects.filter(is_start=False):
            subscribe_task.is_start = True
            subscribe_task.save(update_fields=['is_start'])
            asyncio.create_task(subscribe_process(subscribe_task))
        await asyncio.sleep(60)


