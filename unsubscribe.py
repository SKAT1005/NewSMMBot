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
from app.models import SubscribeTask, ActionTask, UnsubscribeTask


async def unsubscribe_process(unsubscribe_task: UnsubscribeTask):
    task = await sync_to_async(lambda: unsubscribe_task.task)()
    channel_link = await sync_to_async(lambda: task.channel_link)()
    sessions = await sync_to_async(list)(unsubscribe_task.sessions.all().order_by('id'))
    total_sessions = len(sessions)

    while True:
        current_time = timezone.now()
        # Получаем next_action асинхронно
        next_action_time = await sync_to_async(lambda: unsubscribe_task.next_action)()

        if next_action_time <= current_time:
            # Получаем текущий счетчик асинхронно
            current_unsubscribed = await sync_to_async(lambda: unsubscribe_task.unsubscribed_sessions)()

            if current_unsubscribed < total_sessions:
                session = sessions[current_unsubscribed]
                client = await constant_functions.activate_session(session)

                try:
                    await client(functions.channels.LeaveChannelRequest(
                        channel=channel_link
                    ))
                except Exception as e:
                    print(f"Error unsubscribing from channel: {e}")

                # Обновляем счетчик асинхронно
                unsubscribe_task.unsubscribed_sessions = current_unsubscribed + 1
                await sync_to_async(unsubscribe_task.save)(update_fields=['unsubscribed_sessions'])

                # Обновляем next_action для следующей сессии
                unsubscribe_task.next_action = timezone.now() + timedelta(seconds=random.randint(100, 500) / 100)
                await sync_to_async(unsubscribe_task.save)(update_fields=['next_action'])

        # Проверяем завершение асинхронно
        current_unsubscribed = await sync_to_async(lambda: unsubscribe_task.unsubscribed_sessions)()
        if current_unsubscribed == total_sessions:
            await sync_to_async(unsubscribe_task.delete)()
            break

        await asyncio.sleep(1)  # Уменьшил время сна для более responsive проверки
    try:
        task.is_active = False
        await sync_to_async(task.save)(update_fields=['is_active'])
        await sync_to_async(unsubscribe_task.delete)()
    except Exception:
        pass


async def main():
    while True:
        # Получаем задачи асинхронно
        unsubscribe_tasks = await sync_to_async(list)(UnsubscribeTask.objects.filter(is_start=False))

        for unsubscribe_task in unsubscribe_tasks:
            # Обновляем задачу асинхронно
            unsubscribe_task.is_start = True
            await sync_to_async(unsubscribe_task.save)(update_fields=['is_start'])
            asyncio.create_task(unsubscribe_process(unsubscribe_task))

        await asyncio.sleep(5)
