import asyncio

import os
import random
from datetime import timedelta, datetime, date

import django
from django.utils import timezone
from telethon.tl.functions import photos

import ai
from telethon import functions
from telethon.tl import types
from telethon.tl.functions.messages import SendReactionRequest

import constant_functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()

from app.models import DonorPhoto, Donor, Sessions


async def update_photo(client, photo):
    await client(photos.UploadProfilePhotoRequest(file=await client.upload_file(photo.photo)))



async def update_description(cliend, description):
    pass


async def process_update_photo(session):
    count = 1
    while True:
        l = (timezone.now() - session.next_update_photo).total_seconds()
        if l <= 0:
            client = await constant_functions.activate_session(session, need_make_online=False)
            donor = session.donor
            donor_photos = list(donor.photos.all())
            if len(donor_photos) != 0:
                n = min(len(donor_photos), count)
                photo = donor_photos[n * (-1)]
                await update_photo(client=client, photo=photo)
                if count == 1:
                    pass_time = random.randint(1, 60 * 60 * 24 * 30 * 3)
                    count += 1
                elif count == 2:
                    pass_time = random.randint(1, 60 * 60 * 24 * 30)
                    count += 1
                else:
                    pass_time = random.randint(1, 60 * 60 * 24 * 30 * 3)
                next_update_photo = timezone.now() + timedelta(seconds=pass_time)
                session.next_update_photo = next_update_photo
                session.save(update_fields=['next_update_photo'])
            else:
                await asyncio.sleep(60)
            await client.disconnect()
        else:
            await asyncio.sleep(l)


async def process_check_new_photo(donor):
    while True:
        client = await constant_functions.activate_session(donor.session, need_make_online=False)
        photos = client.get_profile_photos(donor.session.donor_id)
        donor_photos = donor.photos.all()
        l = len(photos) - donor_photos.count()
        if donor_photos.last().id != photos[0].id:
            if l <= 0:
                l = await client.download_media(photo, '1.jpg')
                donor_photo = DonorPhoto.objects.create(photo_id=photo.id, photo=l)
                await update_photo(client=client, photo=donor_photo)
        if l > 0:
            n = True
            for photo in photos[:l]:
                if not donor_photos.filter(photo_id=photo.id):
                    l = await client.download_media(photo, '1.jpg')
                    donor_photo = DonorPhoto.objects.create(photo_id=photo.id, photo=l)
                    if n:
                        await update_photo(client=client, photo=donor_photo)
                        n = False
        await client.disconnect()
        await asyncio.sleep(random.randint(60, 60 * 60))


async def main():
    for donor in Donor.objects.all():
        asyncio.create_task(process_check_new_photo(donor))

    for session in Sessions.object.all():
        asyncio.create_task(process_update_photo(session))
