from django.urls import path

from .views import auth_view, logout_view, task_list, template_list, TaskDetail, TemplateDetail

urlpatterns = [
    path('', auth_view, name='auth'),
    path('logout/', logout_view, name='logout'),
    path('task_list/', task_list, name='task_list'),
    path('template_list/', template_list, name='template_list'),
    path('task', TaskDetail.as_view(), name='task_detail'),
    path('template', TemplateDetail.as_view(), name='template_detail'),
]
