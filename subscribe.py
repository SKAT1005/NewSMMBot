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
from app.models import SubscribeTask, ActionTask, ViewTask, Task


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
    while True:
        try:
            try:
                l = await client(functions.channels.JoinChannelRequest(channel=channel_url))
                return l.chats[0].id
            except Exception as ex:
                l = await client(functions.messages.ImportChatInviteRequest(channel_url[14:]))
                return l.chats[0].id
        except telethon.errors.UserAlreadyParticipantError:
            return False
        except Exception as e:
            print('Подписка на канал: ', e)
            await asyncio.sleep(300)


async def make_views(task, client, last_post_id):
    view_param = await sync_to_async(lambda: task.view)()
    channel_link = await sync_to_async(lambda: task.channel_link)()
    last_post_id_need_watch = await sync_to_async(lambda: view_param.old_post)()
    messages_id = [last_post_id-i for i in range(last_post_id_need_watch) if i < last_post_id]
    messages_id = await client.get_messages(channel_link, ids=messages_id)
    for msg in messages_id:
        all_sessions = await sync_to_async(list)(task.sessions.all().order_by('id'))
        if await sync_to_async(lambda: view_param.last_post)():
                subscribers_count = await sync_to_async(lambda: task.subscribers_count)()
                start_ladder_param = await sync_to_async(lambda: view_param.last_post)()
                task.subscribed_count += 1
                await sync_to_async(task.save)(update_fields=['subscribed_count'])
                start_ladders = [
                    [subscribers_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                    in start_ladder_param.split('; ')]
                for start_ladder in start_ladders:
                    need_sessions = all_sessions[:start_ladder[0]]
                    all_sessions = all_sessions[start_ladder[0]:]
                    sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1

                    view_task = await sync_to_async(ViewTask.objects.create)(
                        message_id=msg.id,
                        task=task,
                        sleep_time=sleep_time,
                        message_text=msg.message
                    )
                    await sync_to_async(view_task.sessions.add)(*need_sessions)
        else:
                view_task = await sync_to_async(ViewTask.objects.create)(
                    message_id=msg.id,
                    task=task,
                    sleep_time=3,
                    message_text=msg.message
                )
                await sync_to_async(view_task.sessions.add)(*all_sessions)


async def subscribe_process(subscribe_task: SubscribeTask):
    start_time = timezone.now()
    task = await sync_to_async(lambda: subscribe_task.task)()
    task_id = await sync_to_async(lambda: task.id)()
    channel_link = await sync_to_async(lambda: task.channel_link)()
    sessions = await sync_to_async(list)(subscribe_task.sessions.all().order_by('id'))
    total_sessions = len(sessions)
    #create_view_task = await sync_to_async(lambda: subscribe_task.create_view_task)()
    print(f'Начал работать в {start_time}')
    while True:
        current_time = timezone.now()
        next_action_time = await sync_to_async(lambda: subscribe_task.next_action)()

        if next_action_time <= current_time:
            task = await sync_to_async(Task.objects.get)(id=task_id)
            current_subscribed = await sync_to_async(lambda: subscribe_task.subscribed_sessions)()

            if current_subscribed < total_sessions:
                try:
                    session = sessions[current_subscribed]
                    client = await constant_functions.activate_session(session)
                    channel_id = await subscribe_on_channel(client=client, channel_url=task.channel_link)
                    await sync_to_async(task.subscribed_sessions.add)(session)
                    subscribe_task.subscribed_sessions = current_subscribed + 1
                    await sync_to_async(subscribe_task.save)(update_fields=['subscribed_sessions'])
                    if channel_id != False:
                        # Обновляем счетчик асинхронно

                        # Проверяем и обновляем channel_id асинхронно
                        task_channel_id = await sync_to_async(lambda: task.channel_id)()
                        if not task_channel_id:
                            task.channel_id = channel_id
                            await sync_to_async(task.save)(update_fields=['channel_id'])

                        # Проверяем и обновляем last_post_id и last_story_id асинхронно
                        task_last_post_id = await sync_to_async(lambda: task.last_post_id)()
                        if not task_last_post_id:
                            last_post_id, last_story_id = await constant_functions.get_last_post_and_story_id(
                                client=client, channel_url=channel_link)
                            task.last_post_id = last_post_id
                            task.last_story_id = last_story_id
                            await sync_to_async(task.save)(update_fields=['last_post_id', 'last_story_id'])
                        last_post_id = await sync_to_async(lambda: task.last_post_id)()
                        if create_view_task:
                            await make_views(task, client, last_post_id)
                            create_view_task = False
                            subscribe_task.create_view_task = False
                            await sync_to_async(subscribe_task.save)(update_fields=['create_view_task'])
                        await create_action(task=task, session=session)
                except (telethon.errors.rpcerrorlist.AuthKeyUnregisteredError,
                        telethon.errors.rpcerrorlist.SessionRevokedError):
                    current_subscribed += 1
                    await sync_to_async(session.delete)()

            # Обновляем next_action для следующей сессии
            subscribe_task.next_action = timezone.now() + timedelta(minutes=subscribe_task.sleep_time)
            await sync_to_async(subscribe_task.save)(update_fields=['next_action'])

        # Проверяем завершение асинхронно
        current_subscribed = await sync_to_async(lambda: subscribe_task.subscribed_sessions)()
        if current_subscribed == total_sessions:
            await sync_to_async(subscribe_task.delete)()
            print('Закончил подписываться')
            break

        await asyncio.sleep(1)  # Уменьшил время сна для более responsive проверки

    end_time = timezone.now()
    print(f'Задача Выполнялась: {end_time-start_time}')


async def main():
    while True:
        subscribe_tasks = await sync_to_async(list)(SubscribeTask.objects.filter(is_start=False))

        for subscribe_task in subscribe_tasks:
            # Обновляем задачу асинхронно
            subscribe_task.is_start = True
            await sync_to_async(subscribe_task.save)(update_fields=['is_start'])
            asyncio.create_task(subscribe_process(subscribe_task))

        await asyncio.sleep(5)
