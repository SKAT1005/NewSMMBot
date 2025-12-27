import asyncio
import os
import random
import time
from datetime import timedelta, datetime, date

import django
from django.utils import timezone
from telethon import functions, types
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from django.db import transaction
from app.models import Task, ViewTask, HistoryViewTask, HistoryReactionTask


async def history_reactions_process(history_reactions_task: HistoryReactionTask):
    task = await sync_to_async(lambda: history_reactions_task.task)()
    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(task.sessions.all().order_by('id'))

    for session in sessions:
        client = await constant_functions.activate_session(session)
        channel_link = await sync_to_async(lambda: task.channel_link)()
        story_id = await sync_to_async(lambda: history_reactions_task.story_id)()
        try:
            await client(functions.stories.SendReactionRequest(channel_link, story_id, types.ReactionEmoji(emoticon='❤️')))
        except Exception as e:
            print(f'history_reactions_process: {e}')
        await asyncio.sleep(history_reactions_task.sleep_time)

    # Удаляем задачу асинхронно
    await sync_to_async(history_reactions_task.delete)()


async def history_view_process(history_view_task: HistoryViewTask):
    task = await sync_to_async(lambda: history_view_task.task)()

    channel_link = await sync_to_async(lambda: task.channel_link)()
    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(task.sessions.all().order_by('id'))

    for session in sessions:
        client = await constant_functions.activate_session(session)
        story_id = await sync_to_async(lambda: history_view_task.story_id)()
        try:
            await client(functions.stories.ReadStoriesRequest(channel_link, [story_id]))
        except Exception as e:
            print(f'history_view_process: {e}')
        await asyncio.sleep(history_view_task.sleep_time)

    # Удаляем задачу асинхронно
    await sync_to_async(history_view_task.delete)()


async def history_view():
    while True:
        # Получаем задачи асинхронно
        history_view_tasks = await sync_to_async(list)(HistoryViewTask.objects.filter(is_start=False))

        for history_view_task in history_view_tasks:
            # Обновляем задачу асинхронно
            history_view_task.is_start = True
            await sync_to_async(history_view_task.save)(update_fields=['is_start'])
            asyncio.create_task(history_view_process(history_view_task))

        await asyncio.sleep(5)


async def history_reaction():
    while True:
        # Исправлено: было ViewTask, должно быть HistoryReactionTask
        history_reaction_tasks = await sync_to_async(list)(HistoryReactionTask.objects.filter(is_start=False))

        for history_reaction_task in history_reaction_tasks:
            # Обновляем задачу асинхронно
            history_reaction_task.is_start = True
            await sync_to_async(history_reaction_task.save)(update_fields=['is_start'])
            asyncio.create_task(history_reactions_process(history_reaction_task))

        await asyncio.sleep(5)


async def add_history_task_process(task: Task):
    story_param = task.history
    # Получаем сессии асинхронно
    all_sessions = await sync_to_async(list)(task.sessions.all().order_by('id'))
    view_ladders = []
    reaction_ladders = []
    channel_url = await sync_to_async(lambda: task.channel_link)()

    while True:
        try:
            task = await sync_to_async(Task.objects.get)(id=task.id)
            subscribed_sessions = await sync_to_async(list)(task.subscribed_sessions.all())
            session = random.choice(subscribed_sessions)
            client = await constant_functions.activate_session(session)
            try:
                # Получаем первую сессию асинхронно
                last_story_id = constant_functions.get_last_story_id(client=client, channel_url=channel_url)
            except Exception as e:
                last_story_id = False
                print(f'add_history_task_process: {e}')

            # Получаем последний story_id асинхронно
            current_last_story_id = await sync_to_async(lambda: task.last_story_id)()

            if last_story_id != False and current_last_story_id != last_story_id:
                # Обновляем задачу асинхронно
                task.last_story_id = last_story_id
                await sync_to_async(task.save)(update_fields=['last_story_id'])

                if story_param and story_param.view_ladder:
                    view_ladders = [
                        [story_param.view_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                        in story_param.view_ladder.param.split('; ')]

                if story_param and story_param.reaction_ladder:
                    reaction_ladders = [
                        [story_param.reaction_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                        in story_param.reaction_ladder.param.split('; ')]

                # Создаем задачи просмотра
                for start_ladder in view_ladders:
                    need_sessions = all_sessions[:start_ladder[0]]
                    all_sessions = all_sessions[start_ladder[0]:]
                    sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1

                    # Создаем задачу асинхронно
                    view_task = await sync_to_async(HistoryViewTask.objects.create)(
                        story_id=last_story_id,
                        task=task,
                        sleep_time=sleep_time
                    )
                    await sync_to_async(view_task.sessions.add)(*need_sessions)

                # Создаем задачи реакций
                for reaction_ladder in reaction_ladders:
                    need_sessions = all_sessions[:reaction_ladder[0]]
                    all_sessions = all_sessions[reaction_ladder[0]:]
                    sleep_time = reaction_ladder[1] / len(need_sessions) if need_sessions else 1

                    # Создаем задачу асинхронно
                    reaction_task = await sync_to_async(HistoryReactionTask.objects.create)(
                        story_id=last_story_id,
                        task=task,
                        sleep_time=sleep_time
                    )
                    await sync_to_async(reaction_task.sessions.add)(*need_sessions)

            await asyncio.sleep(60)
        except Exception as e:
            print(f'add_history_task_process_final: {e}')


async def add_view_task_main():
    while True:
        # Получаем задачи асинхронно
        tasks = await sync_to_async(list)(Task.objects.filter(
            channel_id__isnull=False,
            is_start_parse_history=False,
            history__isnull=False
        ))

        for task in tasks:
            # Обновляем задачу асинхронно
            task.is_start_parse_history = True
            await sync_to_async(task.save)(update_fields=['is_start_parse_history'])
            asyncio.create_task(add_history_task_process(task))

        await asyncio.sleep(10)

async def main():
    asyncio.create_task(history_view())
    asyncio.create_task(history_reaction())
    asyncio.create_task(add_view_task_main())
