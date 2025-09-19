import asyncio
import os
import random
from datetime import timedelta, datetime, date

import django
import emoji
import telethon
from django.utils import timezone
from telethon import functions
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest

import ai
import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from asgiref.sync import sync_to_async
from app.models import SubscribeTask, ActionTask, Task, ViewTask, ReactionTask, CommentTask


async def get_ai_reaction(text, index):
    prompt = "Напиши эмодзи, которые подходят к этому посту через ;"
    text = ai.get_answer(prompt=prompt, text=text)
    if text:
        reactions = await get_text_reactions(text, index=index)
        return reactions
    else:
        return []


async def get_text_reactions(text, index=None):
    n = emoji.emoji_list(text)
    reactions = []
    l = 0
    for i in n:
        reactions.append(i['emoji'])
        if index != None and l == index:
            break
        l += 1
    return reactions


async def get_reactions_list(client, task, entity, message_id):
    reactions_list = []
    if await sync_to_async(lambda: task.reaction.basic_reactions)():
        basic_reactions = await sync_to_async(lambda: task.reaction.basic_reactions.reactions)()
        reactions_list += await get_text_reactions(basic_reactions)

    # Получаем сообщение с проверкой
    messages = await client.get_messages(entity, ids=[message_id])
    if not messages:
        return reactions_list

    message = messages[0]

    if await sync_to_async(lambda: task.reaction.user_reactions)():
        if hasattr(message, 'reactions') and message.reactions and hasattr(message.reactions, 'results'):
            for reaction in message.reactions.results:
                if hasattr(reaction, 'reaction') and hasattr(reaction.reaction, 'emoticon'):
                    reaction_str = reaction.reaction.emoticon
                    if reaction_str not in reactions_list:
                        reactions_list.append(reaction_str)

    if await sync_to_async(lambda: task.reaction.ai_reactions)():
        ai_reactions_count = await sync_to_async(lambda: task.reaction.ai_reactions.type_count)()
        ai_reactions = await get_ai_reaction(message.message, ai_reactions_count)
        reactions_list += ai_reactions

    # Добавляем текстовые реакции
    if await sync_to_async(lambda: task.reaction.text_reactions)():
        text_reactions_count = await sync_to_async(lambda: task.reaction.text_reactions.type_count)()
        text_reactions = await get_text_reactions(message.message, index=text_reactions_count)
        reactions_list += text_reactions

    return reactions_list


async def reaction_process(reaction_task: ReactionTask):
    task = await sync_to_async(lambda: reaction_task.task)()
    # Получаем сессии асинхронно
    sessions = await sync_to_async(list)(reaction_task.sessions.all())

    for session in sessions:
        view_persent = await sync_to_async(lambda: task.reaction.view_persent)()
        random_percent = random.randint(1, 100)
        if random_percent <= view_persent:
            try:
                client = await constant_functions.activate_session(session)
                entity = await client.get_entity(task.channel_link)
                message_id = await sync_to_async(lambda: reaction_task.message_id)()
                reactions_list = await get_reactions_list(client=client, task=task, entity=entity, message_id=message_id)

                if reactions_list:  # Проверяем, что есть реакции для выбора
                    try:
                        while True:
                            if not reactions_list:
                                break
                            reaction = random.choice(reactions_list)
                            try:
                                await client(SendReactionRequest(
                                    peer=entity,
                                    msg_id=message_id,
                                    reaction=[types.ReactionEmoji(emoticon=reaction)]
                                ))
                                break
                            except Exception:
                                reactions_list.remove(reaction)

                    except Exception as e:
                        print(f'reaction_process: {e}')
            except telethon.errors.rpcerrorlist.AuthKeyUnregisteredError:
                await sync_to_async(session.delete)()
            await client.disconnect()
        await asyncio.sleep(reaction_task.sleep_time)

    # Удаляем задачу асинхронно
    await sync_to_async(reaction_task.delete)()


async def main():
    while True:
        # Получаем задачи асинхронно
        reaction_tasks = await sync_to_async(list)(ReactionTask.objects.filter(is_start=False))

        for reaction_task in reaction_tasks:
            # Обновляем задачу асинхронно
            reaction_task.is_start = True
            await sync_to_async(reaction_task.save)(update_fields=['is_start'])
            # Исправлено: было reaction_task(reaction_task), должно быть reaction_process(reaction_task)
            asyncio.create_task(reaction_process(reaction_task))

        await asyncio.sleep(60)
