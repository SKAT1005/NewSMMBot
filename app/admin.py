from django.contrib import admin
from .models import Task, Template, Comment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentParamAdmin(admin.ModelAdmin):
    pass
