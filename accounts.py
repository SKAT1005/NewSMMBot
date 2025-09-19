import asyncio

import os
import random
from datetime import timedelta, datetime, date

import django
from asgiref.sync import sync_to_async
from django.utils import timezone
from telethon.tl.functions import photos
from telethon.tl.types import PeerUser

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
    while True:
        l = (timezone.now() - session.next_update_photo).total_seconds()
        if l <= 0:
            client = await constant_functions.activate_session(session, need_make_online=False)
            donor = await sync_to_async(lambda: session.donor)()
            donor_photos = await sync_to_async(list)(donor.photos.all())
            if len(donor_photos) != 0:
                n = min(len(donor_photos), 1) # count был глобальной переменной и не обновлялся, поменял на 1
                photo = donor_photos[n * (-1)]
                await update_photo(client=client, photo=photo)
                if n == 1: # count -> n
                    pass_time = random.randint(1, 60 * 60 * 24 * 30 * 3)
                    n += 1 # count += 1 - не нужен, т.к. n не изменяется дальше
                elif n == 2: # count -> n - этого блока никогда не будет
                    pass_time = random.randint(1, 60 * 60 * 24 * 30)
                    n += 1 # count += 1
                else:
                    pass_time = random.randint(1, 60 * 60 * 24 * 30 * 3)
                next_update_photo = timezone.now() + timedelta(seconds=pass_time)
                session.next_update_photo = next_update_photo
                await sync_to_async(session.save)(update_fields=['next_update_photo'])
            else:
                await asyncio.sleep(60)
            await client.disconnect()
        else:
            await asyncio.sleep(l)


async def process_check_new_photo(donor):
    while True:
        try:
            session = await sync_to_async(lambda: donor.session)()
            client = await constant_functions.activate_session(session, need_make_online=False)
            photos = await client.get_profile_photos(session.donor_id)
            donor_photos = await sync_to_async(list)(donor.photos.all())
            donor_photos_count = len(donor_photos)
            l = len(photos) - donor_photos_count

            if donor_photos_count > 0:
                last_photo_id = donor_photos[-1].photo_id #Исправлено: раньше - .id, а нужно .photo_id
            else:
                last_photo_id = None

            if last_photo_id != photos[0].id if photos else None: # Исправлено: проверка на None и отсутствие фотографий

                if l <= 0:
                    try: #Добавлено try except, т.к. photo может быть None
                        l = await client.download_media(photos[0], '1.jpg') #Исправлено: photos[0], а не photo
                        donor_photo = await sync_to_async(DonorPhoto.objects.create)(photo_id=photos[0].id, photo=l) #Исправлено: photos[0].id
                        await update_photo(client=client, photo=donor_photo)
                    except Exception as e:
                        print(f"Error downloading or creating photo: {e}")

            if l > 0:
                n = True
                for photo in photos[:l]:
                    if not any(d_photo.photo_id == photo.id for d_photo in donor_photos): #Переделана проверка
                        try:
                            l = await client.download_media(photo, '1.jpg')
                            donor_photo = await sync_to_async(DonorPhoto.objects.create)(photo_id=photo.id, photo=l)
                            if n:
                                await update_photo(client=client, photo=donor_photo)
                                n = False
                        except Exception as e:
                            print(f"Error downloading or creating photo: {e}")
            await client.disconnect()
            await asyncio.sleep(random.randint(60, 60 * 60))
        except Exception as e:
            print('Не могу получить информацию о фотографиях пользователя')
            await asyncio.sleep(10)


async def main():
    donor_list = []
    session_list = []
    while True:
        donors = await sync_to_async(list)(Donor.objects.all())
        sessions = await sync_to_async(list)(Sessions.objects.all())

        for donor in donors:
            if donor not in donor_list:
                donor_list.append(donor)
                asyncio.create_task(process_check_new_photo(donor))

        for session in sessions:
            if session not in session_list:
                session_list.append(session)
                asyncio.create_task(process_update_photo(session))

        await asyncio.sleep(60)  # Добавлена задержка, чтобы не перегружать ЦП

