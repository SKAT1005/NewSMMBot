import asyncio
import os
import random
from datetime import timedelta, datetime, date

import django
import telethon.errors
from django.utils import timezone
import ai
from telethon import functions
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest

import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from django.db import transaction
from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask, Comment


async def generate_comment(text):
    prompt = "Напиши комментарий для этого поста"
    comment = ai.get_answer(prompt=prompt, text=text)
    return comment


async def comment_process(comment_task: CommentTask):
    task = await sync_to_async(lambda: comment_task.task)()
    task_id = await sync_to_async(lambda: task.id)()
    # Используем sync_to_async для получения связанных объектов
    sessions = await sync_to_async(list)(comment_task.sessions.all().order_by('id'))
    max_comment = await sync_to_async(lambda: task.comment.max_comment)()
    message_text = await sync_to_async(lambda: comment_task.message_text)()
    message_id = await sync_to_async(lambda: comment_task.message_id)()
    comment_count = 0
    while True:
        task = await sync_to_async(Task.objects.get)(id=task_id)
        subscribed_sessions = await sync_to_async(list)(task.subscribed_sessions.all())
        for session in sessions:
            if session in subscribed_sessions:
                if max_comment and comment_count == max_comment:
                    sessions = []
                    break

                if message_text:
                    text = await generate_comment(text=message_text)
                    if text:
                        # Создаем комментарий асинхронно
                        await sync_to_async(Comment.objects.create)(
                            task=task,
                            post_text=message_text,
                            message_id=message_id,
                            session=session,
                            comment=text,
                            end_check=timezone.now() + timedelta(
                                minutes=await sync_to_async(lambda: task.comment.auto_moderation)())
                        )
                        sessions.remove(session)
        if len(sessions) == 0:
            break
        await asyncio.sleep(5)
    await sync_to_async(comment_task.delete)()


async def main():
    while True:
        # Получаем задачи асинхронно
        comment_tasks = await sync_to_async(list)(CommentTask.objects.filter(is_start=False))

        for comment_task in comment_tasks:
            # Обновляем задачу асинхронно
            comment_task.is_start = True
            await sync_to_async(comment_task.save)(update_fields=['is_start'])
            asyncio.create_task(comment_process(comment_task))

        await asyncio.sleep(5)


async def send_message(comment):
    task = await sync_to_async(lambda: comment.task)()
    session = await sync_to_async(lambda: comment.session)()
    client = await constant_functions.activate_session(session)
    message_id = comment.message_id
    messages = await client.get_messages(task.channel_link, ids=[message_id])
    post = messages[0] if messages else None

    if post:
        comment_text = await sync_to_async(lambda: comment.comment)()
        await client.send_message(task.channel_link, message=comment_text, comment_to=post)
    await sync_to_async(comment.delete)()


async def main_send_comment():
    while True:
        # Получаем комментарии асинхронно
        comments = await sync_to_async(list)(Comment.objects.all())

        for comment in comments:
            end_check = await sync_to_async(lambda: comment.end_check)()
            if await sync_to_async(lambda: comment.is_check)():
                asyncio.create_task(send_message(comment))
            elif end_check <= timezone.now():
                # Обновляем комментарий асинхронно
                comment.is_check = True
                await sync_to_async(comment.save)(update_fields=['is_check'])
                asyncio.create_task(send_message(comment))

        await asyncio.sleep(60)
