import asyncio
import datetime
import json
import random
import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from app.models import Task, Template, Sessions, Comment, Donor
from app.task import task_action
import telethon

from const_sessions import session_list
from constant_functions import CONSTANT_API_ID, CONSTANT_API_HASH


def get_post_data(post):
    post_data = {}
    for key in post:
        post_data[key] = post.get(key)
    return post_data


def auth_view(request):
    context = {}
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        # Авторизация
        if 'login' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('task_list')  # Замените на нужный URL
            else:
                context['login_error'] = 'Неверный логин или пароль.'

        # Регистрация
        elif 'registration' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                context['register_error'] = 'Пароли не совпадают.'
            elif User.objects.filter(username=username).exists():
                context['register_error'] = 'Пользователь уже существует.'
            else:
                user = User.objects.create_user(username=username, password=password)
                authenticated_user = authenticate(username=username, password=password)
                login(request, authenticated_user)
                return redirect('task_list')  # Замените на нужный URL

    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('auth')


def task_list(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    if request.method == 'GET':
        tasks = Task.objects.filter(user=user)

        return render(request, 'task_list.html', context={'tasks': tasks})


class TaskDetail(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('auth')
        task_id = request.GET.get('task_id')
        task = Task.objects.filter(id=task_id, user=user).first()
        if not task:
            task = Task.objects.create(user=user)
            url = reverse('task_detail') + f'?task_id={task.id}'
            return redirect(url)
        return render(request, 'create_and_edit_task.html', context={'task': task})

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('auth')
        task_id = request.GET.get('task_id')
        task = Task.objects.filter(id=task_id, user=user).first()
        data_post = get_post_data(request.POST)
        if 'delete' in data_post:
            task.delete()
            return redirect('task_list')
        task_action.change_task(task=task, data_post=data_post)
        if 'start' in data_post:
            task_action.create_subscribe_task(task=task)
            task.is_active = True
            task.save(update_fields=['is_active'])
            return redirect('task_list')
        url = reverse('task_detail') + f'?task_id={task.id}'
        return redirect(url)


class TemplateDetail(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('auth')
        template_id = request.GET.get('template_id')
        template = Template.objects.filter(id=template_id, user=user).first()
        if not template:
            template = Template.objects.create(user=user)
            url = reverse('template_detail') + f'?template_id={template.id}'
            return redirect(url)
        return render(request, 'create_and_edit_template.html', context={'template': template})

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('auth')
        template_id = request.GET.get('template_id')
        template = Template.objects.filter(id=template_id, user=user).first()
        data_post = get_post_data(request.POST)
        if 'delete' in data_post:
            template.delete()
            return redirect('template_list')
        task_action.change_template(template=template, data_post=data_post)
        url = reverse('template_detail') + f'?template_id={template.id}'
        return redirect(url)


@csrf_exempt
def get_code(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # Получаем параметры
        phone = data.get('phone')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        # Запускаем асинхронный код синхронно
        async def async_get_code():
            client = telethon.TelegramClient(f'{phone}', api_id, api_hash,
                                     system_version="4.16.30-vxCUSTOM")
            await client.connect()

            try:
                send_code = await client.send_code_request(phone=phone)
                phone_code_hash = send_code.phone_code_hash
                return phone_code_hash
            except Exception as e:
                return {"error": str(e)}
            finally:
                await client.disconnect()

        # Выполняем асинхронную функцию
        result = asyncio.run(async_get_code())

        if isinstance(result, dict) and "error" in result:
            return JsonResponse({"status": "error", "message": result["error"]}, status=400)
        else:
            return JsonResponse({"status": "success", "phone_code_hash": result})
    else:
        return JsonResponse({"status": "error", "message": "Only POST method is allowed"}, status=405)


class AddSessionView(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('auth')
        return render(request, 'add_session.html')

    def post(self, request):
        file = request.FILES.get('session_file')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        api_id = request.POST.get('api_id')
        api_hash = request.POST.get('api_hash')
        donor_id = request.POST.get('donor_id')
        password = request.POST.get('password')
        code = request.POST.get('code')
        phone_code_hash = request.POST.get('phone_code_hash')
        if gender == 'male':
            gender = True
        else:
            gender = False
        session_file = f'sessions/{phone}'
        client = None
        if not file:
            async def create_session():
                client = telethon.TelegramClient(session_file, api_id, api_hash,
                                                 system_version="4.16.30-vxCUSTOM")
                await client.connect()
                try:
                    await client.sign_in(phone, code=code, phone_code_hash=phone_code_hash)
                    return session_file, client
                except Exception as e:
                    await client.sign_in(phone, code=code, phone_code_hash=phone_code_hash, password=password)
                    return session_file, client
                finally:
                    await client.disconnect()
            file, client = asyncio.run(create_session())
        if file:

            async def create_session():
                client = telethon.TelegramClient(session_file, api_id=CONSTANT_API_ID,
                                                 api_hash=CONSTANT_API_HASH,
                                                 system_version="4.16.30-vxCUSTOM")
                return client
            if not client:
                client = asyncio.run(create_session())
            pass_time = random.randint(1, 60*60*24*30*3)
            next_update_photo = timezone.now() + datetime.timedelta(seconds=pass_time)
            session = Sessions.objects.create(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                donor_id=donor_id,
                password=password,
                file=file,
                is_male=gender,
                next_update_photo=next_update_photo
            )
            session_list[session.id] = client
            Donor.objects.create(session=session)
        return render(request, 'add_session.html')


def template_list(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    if request.method == 'GET':
        templates = Template.objects.filter(user=user)
        return render(request, 'template_list.html', context={'templates': templates})



def comments(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    comments = Comment.objects.filter(task__user=user, is_check=False)
    return render(request, 'comment_check.html', context={'comments': comments})



def confirm_comment(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    comment_id = request.GET.get('comment_id')
    comment = Comment.objects.get(id=comment_id)
    if comment.task.user == user:
        comment.is_check = True
        comment.save(update_fields=['is_check'])
    return redirect('comments')

def cancel_comment(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    comment_id = request.GET.get('comment_id')
    comment = Comment.objects.get(id=comment_id)
    if comment.task.user == user:
        comment.delete()
    return redirect('comments')