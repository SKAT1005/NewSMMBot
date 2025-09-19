import asyncio
import os
import random
import re
from datetime import timedelta, datetime, date

import django
import telethon
from django.utils import timezone
from telethon import functions
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask, CommentParam, ViewParam, \
    ReactionParam, UnsubscribeTask


async def check_ad(client, task, message_id, entity, view_task):
    messages = await client.get_messages(entity, ids=[message_id])
    if not messages:
        return
    message = messages[0]
    message_text = message.message
    links = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', message_text)

    # Получаем параметры асинхронно
    ad_param = await sync_to_async(lambda: task.ad)()
    if not ad_param:
        return

    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(view_task.sessions.all())
    need_sessions = len(sessions) * ad_param.subscribe_percent // 100
    sessions = sessions[:need_sessions]

    for link in links:
        ad_detect = await sync_to_async(lambda: ad_param.ad_detect)()
        if link not in ad_detect.split():
            # Создаем параметры асинхронно
            view = await sync_to_async(lambda: task.view)()
            reaction = await sync_to_async(lambda: task.reactions)()
            view_param = await sync_to_async(ViewParam.objects.create)(
                start_ladder=ad_param.start_ladder,
                holiday=view.holiday,
                last_post=view.last_post,
                old_post=view.old_post,
            )

            reaction_param = await sync_to_async(ReactionParam.objects.create)(
                view_persent=ad_param.channel_reaction,
                start_ladder=reaction.start_ladder,
                basic_reactions=reaction.basic_reactions,
                text_reactions=reaction.text_reactions,
                user_reactions=reaction.user_reactions,
                ai_reactions=reaction.ai_reactions,
                last_post_reaction=reaction.last_post_reaction,
            )

            comment_param = await sync_to_async(CommentParam.objects.create)(
                min_comment=ad_param.commet,
                max_comment=ad_param.commet,
                ladder=ad_param.start_ladder
            )

            user = sync_to_async(lambda: task.user)()
            ad_task = await sync_to_async(Task.objects.create)(
                user=user,
                channel_link=link,
                subscribers_count=len(sessions),
                view=view_param,
                reaction=reaction_param,
                comment=comment_param,
            )
            await sync_to_async(ad_task.sessions.add)(*sessions)

            sleep_time = 60 * 60 * 24 // need_sessions if need_sessions > 0 else 1
            subscribe = await sync_to_async(SubscribeTask.objects.create)(
                task=task,
                next_action=timezone.now(),
                sleep_time=sleep_time
            )
            await sync_to_async(subscribe.sessions.add)(*sessions)

            # Обрабатываем отписки
            unsubscribes_param = await sync_to_async(lambda: ad_param.unsubscribes)()
            if unsubscribes_param:
                start_ladders = [[need_sessions * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i in
                                 unsubscribes_param.split('; ')]
                for start_ladder in start_ladders:
                    need_unsub_sessions = sessions[:start_ladder[0]]
                    sessions = sessions[start_ladder[0]:]
                    sleep_time = start_ladder[1] / len(need_unsub_sessions) if need_unsub_sessions else 0

                    unsubscribe_task = await sync_to_async(UnsubscribeTask.objects.create)(
                        task=ad_task,
                        next_action=timezone.now(),  # Исправлено: было ad_task.start_time
                        sleep_time=sleep_time
                    )
                    await sync_to_async(unsubscribe_task.sessions.add)(*need_unsub_sessions)


async def create_reaction_task(task, view_task):
    reaction_param = await sync_to_async(lambda: task.reaction)()
    start_ladders = []

    # Получаем сессии и счет асинхронно
    sessions_count = await sync_to_async(view_task.sessions.count)()
    all_sessions = await sync_to_async(list)(view_task.sessions.all())
    if reaction_param and await sync_to_async(lambda: reaction_param.start_ladder)():
        ladder_param = await sync_to_async(lambda: reaction_param.start_ladder.param)()
        if ladder_param:
            start_ladders = [
                [sessions_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i in
                ladder_param.split('; ')
            ]

    for start_ladder in start_ladders:
        need_sessions = all_sessions[:start_ladder[0]]
        all_sessions = all_sessions[start_ladder[0]:]
        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
        message_id = await sync_to_async(lambda: view_task.message_id)()
        reaction_task = await sync_to_async(ReactionTask.objects.create)(
            message_id=message_id,
            task=task,
            sleep_time=sleep_time
        )
        await sync_to_async(reaction_task.sessions.add)(*need_sessions)


async def create_comment_task(task, view_task):
    comment_param = await sync_to_async(lambda: task.comment)()
    start_ladders = []

    # Получаем сессии и счет асинхронно
    sessions_count = await sync_to_async(view_task.sessions.count)()
    all_sessions = await sync_to_async(list)(view_task.sessions.all())

    if comment_param and await sync_to_async(lambda: comment_param.ladder)():
        ladder_param = await sync_to_async(lambda: comment_param.ladder)()
        if ladder_param:
            start_ladders = [
                [sessions_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i in
                ladder_param.split('; ')
            ]

    for start_ladder in start_ladders:
        need_sessions = all_sessions[:start_ladder[0]]
        all_sessions = all_sessions[start_ladder[0]:]
        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
        message_id = await sync_to_async(lambda: view_task.message_id)()
        comment_task = await sync_to_async(CommentTask.objects.create)(
            message_id=message_id,
            task=task,
            sleep_time=sleep_time
        )
        await sync_to_async(comment_task.sessions.add)(*need_sessions)


async def view_process(view_task: ViewTask):
    task = await sync_to_async(lambda: view_task.task)()
    create_tasks = False

    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(view_task.sessions.all())

    for session in sessions:
        try:
            client = await constant_functions.activate_session(session)
            entity = await client.get_entity(task.channel_link)
            message_id = await sync_to_async(lambda: view_task.message_id)()

            # Проверяем наличие ad асинхронно
            has_ad = await sync_to_async(lambda: task.ad is not None)()
            if has_ad:
                await check_ad(client=client, task=task, message_id=message_id, entity=entity, view_task=view_task)

            if not create_tasks:
                if not await sync_to_async(list)(ReactionTask.objects.filter(message_id=message_id)):
                    await create_reaction_task(task=task, view_task=view_task)
                if not await sync_to_async(list)(CommentTask.objects.filter(message_id=message_id)):
                    await create_comment_task(task=task, view_task=view_task)
                create_tasks = True

            today = date.today()
            day_of_week = today.weekday()

            # Получаем параметры просмотра асинхронно
            holiday_percent = await sync_to_async(lambda: task.view.holiday if day_of_week in [5, 6] else 100)()

            if random.randint(1, 100) <= holiday_percent:
                try:
                    l = await client(functions.messages.GetMessagesViewsRequest(
                        peer=entity,
                        id=[message_id],
                        increment=True
                    ))
                except Exception as e:
                    print(f"Error incrementing views: {e}")

            await client.disconnect()
            await asyncio.sleep(view_task.sleep_time)
        except telethon.errors.rpcerrorlist.AuthKeyUnregisteredError:
            await sync_to_async(session.delete)()

    # Удаляем задачу асинхронно
    await sync_to_async(view_task.delete)()


async def main():
    while True:
        # Получаем задачи асинхронно
        view_tasks = await sync_to_async(list)(ViewTask.objects.filter(is_start=False))

        for view_task in view_tasks:
            # Обновляем задачу асинхронно
            view_task.is_start = True
            await sync_to_async(view_task.save)(update_fields=['is_start'])
            asyncio.create_task(view_process(view_task))

        await asyncio.sleep(60)


async def add_view_task_process(task: Task):
    view_param = await sync_to_async(lambda: task.view)()
    # Получаем сессии асинхронно
    all_sessions = await sync_to_async(list)(task.sessions.all())
    start_ladders = []
    time_ladders = []

    while True:
        task = await sync_to_async(Task.objects.get)(id=task.id)
        task_id = -1
        try:
            # Получаем первую сессию асинхронно
            session = await sync_to_async(lambda: task.sessions.first())()
            client = await constant_functions.activate_session(session)
            entity = await client.get_entity(task.channel_link)
            task_id = await constant_functions.get_last_post_id(client=client, entity=entity)
            await client.disconnect()
        except Exception as e:
            print(f'add_view_task_process: {e}')

        # Получаем последний post_id асинхронно
        last_post_id = await sync_to_async(lambda: task.last_post_id)()

        if task_id != last_post_id:
            # Обновляем задачу асинхронно
            task.last_post_id = task_id
            await sync_to_async(task.save)(update_fields=['last_post_id'])

            for i in range(view_param.old_post + 1):
                msg_id = task_id - i
                if msg_id >= 1:
                    if await sync_to_async(lambda: view_param.start_ladder)():
                        if await sync_to_async(lambda: view_param.start_ladder.is_percent)():
                            subscribers_count = await sync_to_async(lambda: task.subscribers_count)()
                            start_ladder_param = await sync_to_async(lambda: view_param.start_ladder.param)()
                            start_ladders = [
                                [ subscribers_count* int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                                in start_ladder_param.split('; ')]
                        else:
                            start_ladders = [list(map(int, i.split('/'))) for i in
                                             start_ladder_param.split('; ')]

                    if await sync_to_async(lambda: view_param.time_ladder)():
                        if await sync_to_async(lambda: view_param.time_ladder.is_percent)():
                            subscribers_count = await sync_to_async(lambda: task.subscribers_count)()
                            time_ladder_param = await sync_to_async(lambda: view_param.time_ladder.param)()
                            time_ladders = [[subscribers_count // 100, i.split('/')[1]] for
                                            i in time_ladder_param.split('; ')]
                        else:
                            time_ladders = [[int(i.split('/')[0]), i.split('/')[1]] for i in
                                            time_ladder_param.split('; ')]

                    for start_ladder in start_ladders:
                        need_sessions = all_sessions[:start_ladder[0]]
                        all_sessions = all_sessions[start_ladder[0]:]
                        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1

                        view_task = await sync_to_async(ViewTask.objects.create)(
                            message_id=msg_id,
                            task=task,
                            sleep_time=sleep_time
                        )
                        await sync_to_async(view_task.sessions.add)(*need_sessions)

                    for time_ladder in time_ladders:
                        today = timezone.now().date()
                        need_sessions = all_sessions[:time_ladder[0]]
                        all_sessions = all_sessions[time_ladder[0]:]
                        start_str, end_str = time_ladder[1].split('-')
                        start_time = datetime.strptime(start_str, "%H:%M").time()
                        end_time = datetime.strptime(end_str, "%H:%M").time()
                        start_datetime = datetime.combine(today, start_time)
                        end_datetime = datetime.combine(today, end_time)
                        sleep_time = (end_datetime.timestamp() - start_datetime.timestamp()) / len(need_sessions)

                        if datetime.now() > start_datetime:
                            start_datetime += timedelta(days=1)

                        view_task = await sync_to_async(ViewTask.objects.create)(
                            message_id=msg_id,
                            task=task,
                            sleep_time=sleep_time
                        )
                        await sync_to_async(view_task.sessions.add)(*need_sessions)

        await asyncio.sleep(1)


async def add_view_task_main():
    while True:
        # Получаем задачи асинхронно
        tasks = await sync_to_async(list)(Task.objects.filter(channel_id__isnull=False, is_start_parse_messages=False))

        for task in tasks:
            # Обновляем задачу асинхронно
            task.is_start_parse_messages = True
            await sync_to_async(task.save)(update_fields=['is_start_parse_messages'])
            asyncio.create_task(add_view_task_process(task))

        await asyncio.sleep(10)
