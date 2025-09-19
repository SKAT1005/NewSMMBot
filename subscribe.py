import asyncio
import os
from datetime import timedelta

import django
import telethon.errors.rpcerrorlist
from django.utils import timezone
from telethon import functions
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from app.models import SubscribeTask, ActionTask


async def create_action(task, session):
    # Получаем действия асинхронно
    actions = await sync_to_async(list)(task.action.all())

    for action in actions:
        start_time = timezone.now() + timedelta(minutes=action.delay)
        # Создаем ActionTask асинхронно
        await sync_to_async(ActionTask.objects.create)(
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
    task = await sync_to_async(lambda: subscribe_task.task)()

    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(subscribe_task.sessions.all())
    total_sessions = len(sessions)

    while True:
        current_time = timezone.now()
        next_action_time = await sync_to_async(lambda: subscribe_task.next_action)()

        if next_action_time <= current_time:
            current_subscribed = await sync_to_async(lambda: subscribe_task.subscribed_sessions)()

            if current_subscribed < total_sessions:
                try:
                    session = sessions[current_subscribed]
                    client = await constant_functions.activate_session(session)
                    channel_id = await subscribe_on_channel(client=client, channel_url=task.channel_link)

                    # Обновляем счетчик асинхронно
                    subscribe_task.subscribed_sessions = current_subscribed + 1
                    await sync_to_async(subscribe_task.save)(update_fields=['subscribed_sessions'])

                    # Проверяем и обновляем channel_id асинхронно
                    task_channel_id = await sync_to_async(lambda: task.channel_id)()
                    if not task_channel_id:
                        task.channel_id = channel_id
                        await sync_to_async(task.save)(update_fields=['channel_id'])

                    # Проверяем и обновляем last_post_id и last_story_id асинхронно
                    task_last_post_id = await sync_to_async(lambda: task.last_post_id)()
                    if not task_last_post_id:
                        last_post_id, last_story_id = await constant_functions.get_last_post_and_story_id(client=client,
                                                                                                          channel_id=task.channel_link)
                        task.last_post_id = last_post_id
                        task.last_story_id = last_story_id
                        await sync_to_async(task.save)(update_fields=['last_post_id', 'last_story_id'])

                    await client.disconnect()
                    await create_action(task=task, session=session)
                except (telethon.errors.rpcerrorlist.AuthKeyUnregisteredError, telethon.errors.rpcerrorlist.SessionRevokedError):
                    current_subscribed += 1
                    await sync_to_async(session.delete)()

            # Обновляем next_action для следующей сессии
            subscribe_task.next_action = timezone.now() + timedelta(seconds=subscribe_task.sleep_time)
            await sync_to_async(subscribe_task.save)(update_fields=['next_action'])

        # Проверяем завершение асинхронно
        current_subscribed = await sync_to_async(lambda: subscribe_task.subscribed_sessions)()
        if current_subscribed == total_sessions:
            await sync_to_async(subscribe_task.delete)()
            break

        await asyncio.sleep(1)  # Уменьшил время сна для более responsive проверки


async def main():
    while True:
        print(1)
        subscribe_tasks = await sync_to_async(list)(SubscribeTask.objects.filter(is_start=False))

        for subscribe_task in subscribe_tasks:
            # Обновляем задачу асинхронно
            subscribe_task.is_start = True
            await sync_to_async(subscribe_task.save)(update_fields=['is_start'])
            asyncio.create_task(subscribe_process(subscribe_task))

        await asyncio.sleep(60)
