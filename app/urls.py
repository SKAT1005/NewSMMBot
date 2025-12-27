from django.urls import path

from .views import auth_view, logout_view, task_list, template_list, TaskDetail, TemplateDetail, AddSessionView, \
    get_code, comments, confirm_comment, cancel_comment, delite_action

urlpatterns = [
    path('', auth_view, name='auth'),
    path('logout/', logout_view, name='logout'),
    path('task_list/', task_list, name='task_list'),
    path('template_list/', template_list, name='template_list'),
    path('task/', TaskDetail.as_view(), name='task_detail'),
    path('template/', TemplateDetail.as_view(), name='template_detail'),
    path('add_session/', AddSessionView.as_view(), name='add_session'),
    path('get_code/', get_code, name='get_code'),
    path('comments/', comments, name='comments'),
    path('confirm_comment/', confirm_comment, name='confirm_comment'),
    path('cancel_comment/', cancel_comment, name='cancel_comment'),
    path('delite_action/<int:pk>', delite_action, name='delite_action')
]
