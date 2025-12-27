import asyncio
import random
import time

import telethon
from asgiref.sync import sync_to_async
from telethon import TelegramClient, functions
from telethon.client import TelegramBaseClient

from const_sessions import session_list

CONSTANT_API_ID = 24122691
CONSTANT_API_HASH = 'a7b40fde1500ab2a0ffba45649cdecb1'


async def activate_session(session, need_make_online=True) -> TelegramClient:
    l = session_list
    client = session_list[session.id]
    if need_make_online:
        await client(functions.account.UpdateStatusRequest(
            offline=False
        ))
    return client


async def get_last_post_id(client, channel_url):
    try:
        last_id = list(await client.get_messages(channel_url, 1))
        return last_id[0].id
    except Exception as e:
        return 0


async def get_last_story_id(client, channel_url):
    result = await client(functions.stories.GetPeerMaxIDsRequest([channel_url]))
    return result[0]


async def get_last_post_and_story_id(client, channel_url):
    try:
        last_post_id = await get_last_post_id(client=client, channel_url=channel_url)
        last_story_id = await get_last_story_id(client=client, channel_url=channel_url)
        return last_post_id, last_story_id
    except Exception:
        return None, None
