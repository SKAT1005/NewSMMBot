from django.contrib import admin
from .models import Task, Template, Comment, SubscribeTask, Sessions, Donor, ViewTask, \
    ReactionTask, CommentTask, UnsubscribeTask, ReactionParam, ViewParam, SubscribeParam, Ladder, CommentParam, ActionTask, DonorPhoto

@admin.register(DonorPhoto)
class DonorPhotoAdmin(admin.ModelAdmin):
    pass
@admin.register(SubscribeTask)
class TaskAdmin(admin.ModelAdmin):
    pass

@admin.register(ActionTask)
class ActionTaskAdmin(admin.ModelAdmin):
    pass
@admin.register(CommentParam)
class CommentParamAdmin(admin.ModelAdmin):
    pass
@admin.register(UnsubscribeTask)
class UnsubscribeTaskAdmin(admin.ModelAdmin):
    pass

@admin.register(Ladder)
class LadderAdmin(admin.ModelAdmin):
    pass
@admin.register(ReactionParam)
class ReactionParamAdmin(admin.ModelAdmin):
    pass

@admin.register(ViewParam)
class ViewParamAdmin(admin.ModelAdmin):
    pass

@admin.register(SubscribeParam)
class SubscribeParamAdmin(admin.ModelAdmin):
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
    list_display = ['task', 'message_id']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass

