import asyncio
import random
import time

from telethon import TelegramClient, functions
from telethon.client import TelegramBaseClient

from const_sessions import session_list

CONSTANT_API_ID = 24122691
CONSTANT_API_HASH = 'a7b40fde1500ab2a0ffba45649cdecb1'

async def activate_session(session, need_make_online=True) -> TelegramClient:

    client = session_list[session.id]
    while True:
        try:
            await client.connect()
            break
        except Exception as e:
            return client
    if need_make_online:
        await client(functions.account.UpdateStatusRequest(
            offline=False
        ))
    return client

async def get_entity_buy_id(client, channel_id):
    return await client.get_entity(channel_id)
async def get_last_post_id(client, entity):
    try:
        last_id = list(await client.get_messages(entity, 1))
        return last_id[0].id
    except Exception as e:
        return 0

async def get_last_story_id(client, entity):
    result = await client(functions.stories.GetPeerMaxIDsRequest([entity]))
    return result[0]
async def get_last_post_and_story_id(client, channel_id):
    try:
        entity = await get_entity_buy_id(client=client, channel_id=channel_id)
        last_post_id = await get_last_post_id(client=client, entity=entity)
        last_story_id = await get_last_story_id(client=client, entity=entity)
        return last_post_id, last_story_id
    except Exception:
        return None, None