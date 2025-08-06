import asyncio

import os
import random
from datetime import timedelta, datetime, date

import django
from django.utils import timezone
from telethon import functions
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask


async def check_ad(task):
    pass


async def create_reaction_task(task, view_task):
    reaction_param = task.reaction
    start_ladders = []
    all_sessions = view_task.sessions.all()
    if reaction_param.start_ladder:
            start_ladders = [
                [view_task.sessions.count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                in
                reaction_param.start_ladder.split('; ')]
    for start_ladder in start_ladders:
        need_sessions = all_sessions[:start_ladder[0]]
        all_sessions = all_sessions[start_ladder[0]:]
        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
        reaction_task = ReactionTask.objects.create(
            message_id=view_task.message_id,
            task=task,
            sleep_time=sleep_time
        )
        reaction_task.sessions.add(*need_sessions)


async def create_comment_task(task, view_task):
    comment_param = task.comment
    start_ladders = []
    all_sessions = view_task.sessions.all()
    if comment_param.start_ladder:
        start_ladders = [
            [view_task.sessions.count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
            in
            comment_param.start_ladder.split('; ')]
    for start_ladder in start_ladders:
        need_sessions = all_sessions[:start_ladder[0]]
        all_sessions = all_sessions[start_ladder[0]:]
        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
        comment_task = CommentTask.objects.create(
            message_id=view_task.message_id,
            task=task,
            sleep_time=sleep_time
        )
        comment_task.sessions.add(*need_sessions)


async def view_process(view_task: ViewTask):
    task = view_task.task
    create_tasks = False
    for session in view_task.sessions.all():
        client = await constant_functions.activate_session(session)
        entity = await client.get_entity(task.channel_link)
        message_id = view_task.message_id
        if not create_tasks:
            await create_reaction_task(task=task, view_task=view_task)
            await create_comment_task(task=task, view_task=view_task)
        today = date.today()
        day_of_week = today.weekday()
        if day_of_week in [5, 6]:
            l = task.view.holiday
        else:
            l = 100
        if random.randint(1, 100) <= l:
            await client(functions.messages.GetMessagesViewsRequest(
                peer=entity,
                id=[message_id, ],
                increment=True
            ))
        await client.disconnect()
        await asyncio.sleep(view_task.sleep_time)
    view_task.delete()


async def main():
    while True:
        for view_task in ViewTask.objects.filter(is_start=False):
            view_task.is_start = True
            view_task.save(update_fields=['is_start'])
            asyncio.create_task(view_process(view_task))
        await asyncio.sleep(60)


async def add_view_task_process(task: Task):
    view_param = task.view
    all_sessions = list(task.sessions.all())
    start_ladders = []
    time_ladders = []
    while True:
        task_id = -1
        try:
            session = task.sessions.first()
            client = await constant_functions.activate_session(session)
            entity = await client.get_entity(task.channel_link)
            task_id = constant_functions.get_last_post_id(client=client, entity=entity)
            client.disconnect()
        except Exception as e:
            print(f'add_view_task_process: {e}')
        if task_id != task.last_post_id:
            task.last_post_id = task_id
            task.save(update_fields=['last_post_id'])
            for i in range(view_param.old_post + 1):
                msg_id = task_id - i
                if msg_id >= 1:
                    if view_param.start_ladder:
                        if view_param.start_ladder.is_percent:
                            start_ladders = [
                                [task.subscribers_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i
                                in
                                view_param.start_ladder.param.split('; ')]
                        else:
                            start_ladders = [list(map(int, i.split('/'))) for i in
                                             view_param.start_ladder.param.split('; ')]
                    if view_param.time_ladder:
                        if view_param.time_ladder.is_percent:
                            time_ladders = [[task.subscribers_count * int(i.split('/')[0]) // 100, i.split('/')[1]] for
                                            i in
                                            view_param.time_ladder.param.split('; ')]
                        else:
                            time_ladders = [[int(i.split('/')[0]), i.split('/')[1]] for i in
                                            view_param.time_ladder.param.split('; ')]
                    for start_ladder in start_ladders:
                        need_sessions = all_sessions[:start_ladder[0]]
                        all_sessions = all_sessions[start_ladder[0]:]
                        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 1
                        view_task = ViewTask.objects.create(
                            message_id=msg_id,
                            task=task,
                            sleep_time=sleep_time
                        )
                        view_task.sessions.add(*need_sessions)
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
                        view_task = ViewTask.objects.create(
                            message_id=msg_id,
                            task=task,
                            sleep_time=sleep_time
                        )
                        view_task.sessions.add(*need_sessions)
        await asyncio.sleep(1)


async def add_view_task_main():
    while True:
        for task in Task.objects.filter(channel_id__isnull=False, is_start_parse_messages=False):
            asyncio.create_task(add_view_task_process(task))
        await asyncio.sleep(10)
