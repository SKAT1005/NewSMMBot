from django.contrib import admin
from .models import Task, Template, Comment, SubscribeTask, Sessions, Donor, ViewTask, ReactionTask, CommentTask, UnsubscribeTask

@admin.register(SubscribeTask)
class TaskAdmin(admin.ModelAdmin):
    pass

@admin.register(UnsubscribeTask)
class UnsubscribeTaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(ReactionTask)
class ReactionTaskAdmin(admin.ModelAdmin):
    pass


@admin.register(CommentTask)
class CommentTaskAdmin(admin.ModelAdmin):
    pass

@admin.register(Sessions)
class TemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(Template)
class TemplateeAdmin(admin.ModelAdmin):
    pass

@admin.register(Donor)
class CommentParamAdmin(admin.ModelAdmin):
    pass


@admin.register(ViewTask)
class ViewTaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass

