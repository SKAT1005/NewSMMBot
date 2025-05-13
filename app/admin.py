from django.contrib import admin
from .models import Task, Template, CommentParam

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    pass


@admin.register(CommentParam)
class CommentParamAdmin(admin.ModelAdmin):
    pass
