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

from app.models import Task, ViewTask, HistoryViewTask, HistoryReactionTask



async def history_reactions_process(history_reactios_task: HistoryReactionTask):
    task = history_reactios_task.task
    for session in task.sessions.all():
        client = await constant_functions.activate_session(session)
        entity = await client.get_entity(task.channel_link)
        story_id = history_reactios_task.story_id
        try:
            await client(functions.stories.SendReactionRequest(entity, story_id, types.ReactionEmoji(emoticon='❤️')))
        except Exception as e:
            print(f'history_reactions_process: {e}')
        await client.disconnect()
        await asyncio.sleep(history_reactios_task.sleep_time)
    history_reactios_task.delete()


async def history_view_process(history_view_task: HistoryViewTask):
    task = history_view_task.task
    for session in task.sessions.all():
        client = await constant_functions.activate_session(session)
        entity = await client.get_entity(task.channel_link)
        story_id = history_view_task.story_id
        try:
            await client(functions.stories.ReadStoriesRequest(entity, story_id))
        except Exception as e:
            print(f'history_view_process: {e}')
        await client.disconnect()
        await asyncio.sleep(history_view_task.sleep_time)
    history_view_task.delete()


async def history_view():
    while True:
        for history_view_task in HistoryViewTask.objects.filter(is_start=False):
            history_view_task.is_start = True
            history_view_task.save(update_fields=['is_start'])
            asyncio.create_task(history_view_process(history_view_task))
        await asyncio.sleep(60)


async def history_reaction():
    while True:
        for history_reactios_task in ViewTask.objects.filter(is_start=False):
            history_reactios_task.is_start = True
            history_reactios_task.save(update_fields=['is_start'])
            asyncio.create_task(history_reactions_process(history_reactios_task))
        await asyncio.sleep(60)


async def main():
    asyncio.create_task(history_view())
    asyncio.create_task(history_reaction())


async def add_history_task_process(task: Task):
    story_param = task.history
    all_sessions = list(task.sessions.all())
    view_ladders = []
    reaction_ladders = []
    while True:
        try:
            session = task.sessions.first()
            client = await constant_functions.activate_session(session)
            entity = await client.get_entity(task.channel_link)
            last_story_id = entity.stories_max_id
            client.disconnect()
        except Exception as e:
            last_story_id = False
            print(f'add_view_task_process: {e}')
        if last_story_id != False and task.last_story_id != last_story_id:
            task.last_story_id = last_story_id
            task.save(update_fields=['last_story_id'])
            if story_param.view_ladder:
                view_ladders = [
                    [story_param.view_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                    in
                    story_param.view_ladder.param.split('; ')]
            if story_param.reaction_ladder:
                reaction_ladders = [
                    [story_param.reaction_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                    in
                    story_param.reaction_ladder.param.split('; ')]
            for start_ladder in view_ladders:
                need_sessions = all_sessions[:start_ladder[0]]
                all_sessions = all_sessions[start_ladder[0]:]
                sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
                view_task = HistoryViewTask.objects.create(
                    story_id=last_story_id,
                    task=task,
                    sleep_time=sleep_time
                )
                view_task.sessions.add(*need_sessions)
            for reaction_ladder in reaction_ladders:
                need_sessions = all_sessions[:reaction_ladder[0]]
                all_sessions = all_sessions[reaction_ladder[0]:]
                sleep_time = reaction_ladder[1] / len(need_sessions) if need_sessions else 1
                view_task = HistoryReactionTask.objects.create(
                    story_id=last_story_id,
                    task=task,
                    sleep_time=sleep_time
                )
                view_task.sessions.add(*need_sessions)
        await asyncio.sleep(5)


async def add_view_task_main():
    while True:
        for task in Task.objects.filter(channel_id__isnull=False, is_start_parse_history=False, history__isnull=False):
            asyncio.create_task(add_history_task_process(task))
        await asyncio.sleep(10)
