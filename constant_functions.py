from telethon import TelegramClient, functions

CONSTANT_API_ID = 122222
CONSTANT_API_HASH = '2121212121'



async def activate_session(session, need_make_online=True):
    client = TelegramClient(session.file, api_id=CONSTANT_API_ID, api_hash=CONSTANT_API_HASH,
                                 system_version="4.16.30-vxCUSTOM")
    await client.start(phone=session.phone, password=session.password)
    if need_make_online:
        await client(functions.account.UpdateStatusRequest(
            offline=False
        ))
    return client

async def get_entity_buy_id(client, channel_id):
    return client.get_entity(channel_id)
async def get_last_post_id(client, entity):
    try:
        last_id = list(await client.get_messages(entity, 1))
        return last_id[0].id
    except Exception:
        return 0

async def get_last_story_id(client, entity):
    result = await client(functions.stories.GetPeerMaxIDsRequest([entity]))
    return result[0]
async def get_last_post_and_story_id(client, channel_id):
    entity = await get_entity_buy_id(client=client, channel_id=channel_id)
    last_post_id = await get_last_post_id(client=client, entity=entity)
    last_story_id = await get_last_story_id(client=client, entity=entity)
    return last_post_id, last_story_id