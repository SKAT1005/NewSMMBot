from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from app.models import Task, Template
from app.task import task_action


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
                authenticate(request, user)
                return redirect('task_list')  # Замените на нужный URL

    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


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


def template_list(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth')
    if request.method == 'GET':
        templates = Template.objects.filter(user=user)
        return render(request, 'template_list.html', context={'templates': templates})
