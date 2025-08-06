import asyncio

import os
import random
from datetime import timedelta, datetime, date

import django
from django.utils import timezone
import ai
from telethon import functions
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest

import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask, Comment


async def generate_comment(text):
    prompt = "Напиши комментарий для этого поста"
    comment = ai.get_answer(prompt=prompt, text=text)
    return comment

async def comment_process(comment_task: CommentTask):
    task = comment_task.task
    for session in comment_task.sessions.all():
        client = await constant_functions.activate_session(session)
        entity = await client.get_entity(task.channel_link)
        message_id = comment_task.message_id
        message = await client.get_messages(entity, ids=[message_id])[0]
        message_text = message.message
        text = await generate_comment(text=message_text)
        if text:
            Comment.objects.create(
                post_text=message_text,
                message_id=message_id,
                session=session,
                comment=text,
                end_check=timezone.now() + timedelta(minutes=task.comment.auto_moderation)
            )
            await client.disconnect()
    comment_task.delete()


async def main():
    while True:
        for comment_task in CommentTask.objects.filter(is_start=False):
            comment_task.is_start = True
            comment_task.save(update_fields=['is_start'])
            asyncio.create_task(comment_process(comment_task))
        await asyncio.sleep(60)




async def send_message(comment):
    task = comment.task
    client = await constant_functions.activate_session(comment.session)
    entity = await client.get_entity(task.channel_link)
    message_id = comment.message_id
    post = await client.get_messages(entity, ids=[message_id])[0]
    comment_text = comment.comment
    await client.send_message(entity=entity, message=comment_text, comment_to=post)


async def main_send_comment():
    while True:
        for comment in Comment.objects.all():
            if comment.is_check:
                asyncio.create_task(send_message(comment))
            elif comment.end_check >= timezone.now():
                comment.is_check = True
                comment.save(update_fields=['is_check'])
                asyncio.create_task(send_message(comment))
        await asyncio.sleep(60)
