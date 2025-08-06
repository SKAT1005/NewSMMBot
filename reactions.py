import asyncio

import os
import random
from datetime import timedelta, datetime, date

import django
import emoji
from django.utils import timezone
from telethon import functions
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest

import ai
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask


async def get_ai_reaction(text):
    prompt = "Напиши эмодзи, которые подходят к этому посту через ;"
    text = ai.get_answer(prompt=prompt, text=text)
    if text:
        reactions = await get_text_reactions(text)
        return reactions
    else:
        return []


async def get_text_reactions(text):
    n = emoji.emoji_list(text)
    reactions = []
    for i in n:
        reactions.append(i['emoji'])
    return reactions
async def get_reactions_list(client, task, entity, message_id):
    reactions_list = []
    reactions_list += task.reaction.basic_reactions.reactions.split(' ')
    message = await client.get_messages(entity, ids=[message_id])[0]
    for reaction in message.reactions.results:
        reaction_str = reaction.reaction.emoticon
        if reaction_str not in reactions_list:
            reactions_list.append(reaction_str)
    reactions_list += await get_ai_reaction(message.message)

    reactions_list += await get_text_reactions(message.message)
    return reactions_list




async def reaction_process(reaction_task: ReactionTask):
    task = reaction_task.task
    for session in reaction_task.sessions.all():
        client = await constant_functions.activate_session(session)
        entity = await client.get_entity(task.channel_link)
        message_id = reaction_task.message_id
        reactions_list = await get_reactions_list(client=client, task=task, entity=entity, message_id=message_id)
        try:
            await client(SendReactionRequest(
                peer=entity,
                msg_id=message_id,
                reaction=[types.ReactionEmoji(emoticon=random.choice(reactions_list))]
            ))
        except Exception as e:
            print(f'reaction_process: {e}')
        await client.disconnect()
    reaction_task.delete()


async def main():
    while True:
        for reaction_task in ReactionTask.objects.filter(is_start=False):
            reaction_task.is_start = True
            reaction_task.save(update_fields=['is_start'])
            asyncio.create_task(reaction_task(reaction_task))
        await asyncio.sleep(60)
