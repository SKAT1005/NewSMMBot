from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Sessions(models.Model):
    phone = models.CharField(max_length=128, blank=True, null=True, verbose_name='Номер телефона')
    is_male = models.BooleanField(verbose_name='Пол пользователя')
    api_id = models.CharField(max_length=128, blank=True, null=True, verbose_name='api id')
    api_hash = models.CharField(max_length=128, blank=True, null=True, verbose_name='api hash ')
    donor_id = models.CharField(max_length=128, blank=True, null=True, verbose_name='id донора')
    password = models.CharField(max_length=128, blank=True, null=True, verbose_name='2FA пароль')
    file = models.FileField(upload_to='sessions', verbose_name='Файл сессии')
    next_update_photo = models.DateTimeField(verbose_name='Время обновления фотографии')


class Donor(models.Model):
    session = models.OneToOneField('Sessions', on_delete=models.CASCADE, related_name='donor', verbose_name='сессия')
    photos = models.ManyToManyField('DonorPhoto', verbose_name='Фотографии донора')

class DonorPhoto(models.Model):
    photo_id = models.CharField(max_length=128, verbose_name='ID фотографии')
    photo = models.ImageField(upload_to='photos', verbose_name='Фотография')

class Ladder(models.Model):
    is_percent = models.BooleanField(default=True, verbose_name='Тип лесенки')
    param = models.CharField(max_length=512, default='20/5; 10/20; 70/60', verbose_name='Параметры лесенки')
    spread = models.CharField(max_length=16, blank=True, null=True, verbose_name='Разброс')


class SubscribeParam(models.Model):
    male = models.IntegerField(default=50, verbose_name='Процент мужчин')
    female = models.IntegerField(default=50, verbose_name='Процент женщин')
    start_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='subscribe_start_ladder',
                                        null=True, blank=True,
                                        verbose_name='Лесенка к старту')
    time_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='subscribe_time_ladder',
                                       blank=True, null=True,
                                       verbose_name='Лесенка ко времени')
    unsubscribes = models.CharField(max_length=512, default='100/44640', verbose_name='Параметры отписки')


class ViewParam(models.Model):
    start_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='view_start_ladder', null=True,
                                        blank=True,
                                        verbose_name='Лесенка к старту')
    time_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='view_time_ladder',
                                       blank=True, null=True,
                                       verbose_name='Лесенка ко времени')
    holiday = models.IntegerField(default=50, verbose_name='Охват в выходные дни')
    last_post = models.CharField(max_length=512, default='1/20; 2/10; 3/5', verbose_name='На предыдущие посты')
    old_post = models.IntegerField(default=2, verbose_name='Сколько смотреть старых постов при подписке')


class Reaction(models.Model):
    reactions = models.CharField(max_length=128, verbose_name='Реакции')
    type_count = models.IntegerField(default=1, verbose_name='Количество типов')
    min_reaction = models.IntegerField(default=10, verbose_name='Минимальное количество реакций')
    max_reaction = models.IntegerField(default=10, verbose_name='Максимальное количество реакций')


class ReactionParam(models.Model):
    view_persent = models.IntegerField(default=100, verbose_name='Количество реакций от просмотра')
    start_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, null=True, blank=True,
                                        verbose_name='Лесенка к старту')
    basic_reactions = models.ForeignKey('Reaction', on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='basic_reactions',
                                           verbose_name='Основные реакции')
    text_reactions = models.ForeignKey('Reaction', on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='text_reactions',
                                          verbose_name='Реакции из текста')
    user_reactions = models.ForeignKey('Reaction', on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='user_reactions',
                                          verbose_name='Реакции от пользователей')
    ai_reactions = models.ForeignKey('Reaction', on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='ai_reactions',
                                        verbose_name='Реакции от ИИ')
    last_post_reaction = models.IntegerField(default=2, verbose_name='На сколько старых постов будут ставиться реакции')


class AdParam(models.Model):
    ad_detect = models.TextField(default='', verbose_name='Ссылки, которые не будут определяться, как рекламные')
    subscribe_percent = models.IntegerField(default=10, verbose_name='% аккаунтов, которые подпишутся на рекламу')
    start_ladder = models.CharField(max_length=512,
                                    default='5/10; 4/35; 3/45; 6/150;13/280; 11/390; 28/1440; 22/2880; 8/4740',
                                    verbose_name='% от подписавшихся на рекламу, которые будут читать контент')
    unsubscribes = models.CharField(max_length=512, default='40/1440; 60/44640', verbose_name='Процент отписок/минуты')
    channel_reaction = models.IntegerField(default=20, verbose_name='% реакций от количества просмотров')
    ad_reaction = models.IntegerField(default=20, verbose_name='% от общего числа реакций для рекламных постов')
    comment = models.IntegerField(default=0, verbose_name='Количество комментариев под рекламными постами')


class HistoryParam(models.Model):
    view_count = models.IntegerField(verbose_name='Количество просмотров', blank=True, null=True)
    view_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='history_view_ladder',
                                       null=True, blank=True,
                                       verbose_name='Лесенка просмотров')
    reaction_count = models.IntegerField(verbose_name='Количество реакций', blank=True, null=True)
    reaction_ladder = models.OneToOneField('Ladder', on_delete=models.CASCADE, related_name='history_reaction_ladder',
                                           null=True, blank=True,
                                           verbose_name='Лесенка реакций')


class CommentParam(models.Model):
    min_comment = models.IntegerField(default=0, verbose_name='Минимальное количество комментариев')
    max_comment = models.IntegerField(default=5, verbose_name='Максимальное количество комментариев')
    ladder = models.CharField(max_length=512, default='', verbose_name='Лесенка для комментариев')
    auto_moderation = models.IntegerField(default=10, verbose_name='Автоматическая модерация комментариев')


class VotingParam(models.Model):
    pass


class Action(models.Model):
    link = models.CharField(max_length=128, verbose_name='Ссылка на бота/канал')
    is_channel = models.BooleanField(default=True, verbose_name='Канал ли для прохождения')
    is_smile = models.BooleanField(default=False, verbose_name='Тест смайликом')
    text = models.CharField(max_length=128, blank=True, null=True, verbose_name='Текст для прохождения теста')
    percent = models.IntegerField(default=100, verbose_name='Процент прохождения')
    delay = models.IntegerField(default=5, verbose_name='Задержка для прохождения')


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks',
                             verbose_name='Пользователь, создавший задачу')
    channel_link = models.CharField(max_length=128, blank=True, null=True, verbose_name='Ссылка на канал')
    channel_id = models.CharField(max_length=128, blank=True, null=True, verbose_name='Id канала')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Сессии')
    start_time = models.DateTimeField(default=timezone.now)
    subscribers_count = models.IntegerField(default=0, verbose_name='Количество аккаунтов')
    subscribe = models.ForeignKey('SubscribeParam', on_delete=models.CASCADE, related_name='task_subscribe', null=True,
                                  blank=True,
                                  verbose_name='tasks_for_subscribe')
    view = models.ForeignKey('ViewParam', on_delete=models.CASCADE, related_name='task_view', null=True, blank=True,
                             verbose_name='tasks_for_view')
    reaction = models.ForeignKey('ReactionParam', on_delete=models.CASCADE, related_name='task_reaction', blank=True,
                                 null=True,
                                 verbose_name='tasks_for_reaction')
    ad = models.ForeignKey('AdParam', on_delete=models.CASCADE, related_name='task_ad', blank=True, null=True,
                           verbose_name='tasks_for_ad')
    history = models.ForeignKey('HistoryParam', on_delete=models.CASCADE, related_name='task_history', blank=True,
                                null=True,
                                verbose_name='tasks_for_ad')
    comment = models.ForeignKey('CommentParam', on_delete=models.CASCADE, related_name='task_comment', blank=True,
                                null=True,
                                verbose_name='tasks_for_comment')
    voting = models.ForeignKey('VotingParam', on_delete=models.CASCADE, related_name='task_voting', blank=True,
                               null=True,
                               verbose_name='tasks_for_voting')
    action = models.ManyToManyField('Action', blank=True,
                                    verbose_name='tasks_for_action')

    is_active = models.BooleanField(default=False, verbose_name='Активна ли')
    is_start_parse_messages = models.BooleanField(default=False, verbose_name='Начался ли парсинг сообщений')
    is_start_parse_history = models.BooleanField(default=False, verbose_name='Начался ли парсинг историй')
    last_post_id = models.IntegerField(blank=True, null=True, verbose_name='Id последнего поста')
    last_story_id = models.IntegerField(blank=True, null=True, verbose_name='Id последней истории')

    def date_str(self):
        dt = self.start_time
        if dt:
            return dt.strftime('%Y-%m-%dT%H:%M')
        return None


class Template(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates',
                             verbose_name='Пользователь, создавший задачу')
    name = models.CharField(max_length=128, null=True, blank=True, verbose_name='Название шаблона')
    subscribe = models.ForeignKey('SubscribeParam', on_delete=models.CASCADE, related_name='template_subscribe',
                                  null=True, blank=True,
                                  verbose_name='tasks_for_subscribe')
    view = models.ForeignKey('ViewParam', on_delete=models.CASCADE, related_name='template_view', null=True, blank=True,
                             verbose_name='tasks_for_view')
    reaction = models.ForeignKey('ReactionParam', on_delete=models.CASCADE, related_name='template_reaction',
                                 blank=True, null=True,
                                 verbose_name='tasks_for_reaction')
    ad = models.ForeignKey('AdParam', on_delete=models.CASCADE, blank=True, related_name='template_ad', null=True,
                           verbose_name='tasks_for_ad')
    history = models.ForeignKey('HistoryParam', on_delete=models.CASCADE, related_name='template_history', blank=True,
                                null=True,
                                verbose_name='tasks_for_ad')
    comment = models.ForeignKey('CommentParam', on_delete=models.CASCADE, related_name='template_comment', blank=True,
                                null=True,
                                verbose_name='tasks_for_comment')
    voting = models.ForeignKey('VotingParam', on_delete=models.CASCADE, related_name='template_voting', blank=True,
                               null=True,
                               verbose_name='tasks_for_voting')

class HistoryReactionTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    story_id = models.IntegerField(verbose_name='Id поста, на который ставим реакции')
    task = models.ForeignKey('Task', related_name='history_reaction_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    sleep_time = models.IntegerField(default=1, verbose_name='')

class HistoryViewTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    story_id = models.IntegerField(verbose_name='Id поста, на который ставим реакции')
    task = models.ForeignKey('Task', related_name='history_view_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    sleep_time = models.IntegerField(default=1, verbose_name='')
class Comment(models.Model):
    is_check = models.BooleanField(default=False)
    post_text = models.TextField(verbose_name='Текст поста')
    task = models.ForeignKey('Task', related_name='comments', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся комментарии')
    message_id = models.IntegerField(verbose_name='Id поста, на который ставим реакции')
    session = models.ForeignKey('Sessions', on_delete=models.CASCADE, related_name='comment_tasks_for_session',
                                verbose_name='Пользователь, выполняющий задачу')
    comment = models.TextField(verbose_name='Комментарий')
    end_check = models.DateTimeField(verbose_name='Время когда автоматически принимается комментарий')


class CommentTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    message_id = models.IntegerField(verbose_name='Id поста, на который ставим реакции')
    task = models.ForeignKey('Task', related_name='comment_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    sleep_time = models.IntegerField(default=1, verbose_name='')


class ReactionTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    message_id = models.IntegerField(verbose_name='Id поста, на который ставим реакции')
    task = models.ForeignKey('Task', related_name='reaction_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    sleep_time = models.IntegerField(default=1, verbose_name='')


class ViewTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    message_id = models.IntegerField(verbose_name='Id поста')
    task = models.ForeignKey('Task', related_name='view_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    sleep_time = models.IntegerField(default=1, verbose_name='')


class ActionTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    session = models.ForeignKey('Sessions', on_delete=models.CASCADE, related_name='action_tasks_for_session',
                                verbose_name='Пользователь, выполняющий задачу')
    action = models.ForeignKey('Action', on_delete=models.CASCADE, related_name='action_tasks_for_action',
                               verbose_name='Целевое действие')
    start_time = models.DateTimeField(verbose_name='Время начала выполнения целевого действия')


class UnsubscribeTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    task = models.ForeignKey('Task', related_name='unsubscribe_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    next_action = models.DateTimeField(verbose_name='Время начала отписок')
    sleep_time = models.FloatField(default=1, verbose_name='Время до следующего действия')
    unsubscribed_sessions = models.IntegerField(default=0, verbose_name='Сколько пользователей отписалось')


class SubscribeTask(models.Model):
    is_start = models.BooleanField(default=False, verbose_name='Запущена ли задача')
    task = models.ForeignKey('Task', related_name='subscribe_tasks', on_delete=models.CASCADE,
                             verbose_name='Задача, к которой относятся задания на подписку')
    sessions = models.ManyToManyField('Sessions', blank=True, verbose_name='Пользователи, выполняющие задачу')
    next_action = models.DateTimeField(verbose_name='Время следующего действия')
    sleep_time = models.FloatField(default=1, verbose_name='Время до следующего действия')
    subscribed_sessions = models.IntegerField(default=0, verbose_name='Сколько пользователей подписалось')
