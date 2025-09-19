import random
from datetime import datetime, timedelta

from django.db import models
from django.db.models import Count
from django.utils import timezone

from app.models import Template, Ladder, SubscribeParam, ViewParam, ReactionParam, Reaction, AdParam, HistoryParam, \
    CommentParam, Action, Task, Sessions, SubscribeTask, UnsubscribeTask


def create_ladder(is_percent, param, spread=None):
    ladder = Ladder.objects.create(is_percent=is_percent)
    if param:
        ladder.param = param
        ladder.save(update_fields=['param'])
    if spread:
        ladder.spread = spread
        ladder.save(update_fields=['spread'])
    return ladder


def change_main(task, subscribers_count, channel_link, start_time):
    update_fields = []
    if task.subscribers_count < int(subscribers_count):
        task.subscribers_count = subscribers_count
        update_fields.append('subscribers_count')
    if task.channel_link != channel_link:
        task.channel_link = channel_link
        update_fields.append('channel_link')
    if start_time and task.date_str() != start_time:
        task.start_time = start_time
        update_fields.append('start_time')

    if update_fields:
        task.save(update_fields=update_fields)


def add_template(task, template_id):
    if template_id:
        template = Template.objects.filter(id=template_id).first()
        if template:
            task.subscribe = template.subscribe
            task.view = template.view
            task.reaction = template.reaction
            task.ad = template.ad
            task.history = template.history
            task.comment = template.comment
            task.voting = template.voting
            task.save(update_fields=['subscribe', 'view', 'reaction', 'ad', 'history', 'comment', 'voting'])
            return False
    return True


def change_subscribe(task, male, female, start_ladder_type, start_ladder_param, time_ladder_type,
                     time_ladder_param,
                     unsubscribes):
    subscribe = task.subscribe
    if not subscribe:
        subscribe = SubscribeParam.objects.create()
        task.subscribe = subscribe
        task.save(update_fields=['subscribe'])
    if start_ladder_type and start_ladder_param:
        if start_ladder_type == 'percent':
            start_ladder_type = True
        else:
            start_ladder_type = False
        start_ladder = subscribe.start_ladder
        if start_ladder:
            start_ladder.is_percent = start_ladder_type
            start_ladder.param = start_ladder_param
            start_ladder.save()
        else:
            start_ladder = create_ladder(start_ladder_type, start_ladder_param)
            subscribe.start_ladder = start_ladder

    if time_ladder_type and time_ladder_param:
        if time_ladder_type == 'percent':
            view_time_ladder_type = True
        else:
            view_time_ladder_type = False
        time_ladder = subscribe.time_ladder
        if time_ladder:
            time_ladder.is_percent = view_time_ladder_type
            time_ladder.param = time_ladder_param
            time_ladder.save()
        else:
            time_ladder = create_ladder(view_time_ladder_type, time_ladder_param)
            subscribe.time_ladder = time_ladder

    if male:
        subscribe.male = male
    if female:
        subscribe.female = female
    if unsubscribes:
        subscribe.unsubscribes = unsubscribes
    subscribe.save()


def change_view(task, view_start_ladder_type, view_start_ladder_param, view_start_ladder_spread,
                view_time_ladder_type,
                view_time_ladder_param, view_time_ladder_spread, holiday, last_post, old_post):
    view = task.view

    if not view:
        view = ViewParam.objects.create()
        task.view = view
        task.save(update_fields=['view'])
    if view_start_ladder_type and view_start_ladder_param and view_start_ladder_spread:
        if view_start_ladder_type == 'percent':
            view_start_ladder_type = True
        else:
            view_start_ladder_type = False
        start_ladder = view.start_ladder
        if start_ladder:
            start_ladder.is_percent = view_start_ladder_type
            start_ladder.param = view_start_ladder_param
            start_ladder.spread = view_start_ladder_spread
            start_ladder.save()
        else:
            start_ladder = create_ladder(view_start_ladder_type, view_start_ladder_param, view_start_ladder_spread)
            view.start_ladder = start_ladder

    if view_time_ladder_type and view_time_ladder_param and view_time_ladder_spread:
        if view_time_ladder_type == 'percent':
            view_time_ladder_type = True
        else:
            view_time_ladder_type = False
        time_ladder = view.time_ladder
        if time_ladder:
            time_ladder.is_percent = view_time_ladder_type
            time_ladder.param = view_time_ladder_param
            time_ladder.spread = view_time_ladder_spread
            time_ladder.save()
        else:
            time_ladder = create_ladder(view_time_ladder_type, view_time_ladder_param, view_time_ladder_spread)
            view.time_ladder = time_ladder

    if holiday:
        view.holiday = holiday
    if last_post:
        view.last_post = last_post
    if old_post:
        view.old_post = old_post
    view.save()


def reaction_create(reaction, type_count, min_reaction, max_reaction):
    if reaction:
        reaction.type_count = type_count
        reaction.min_reaction = min_reaction
        reaction.max_reaction = max_reaction
        reaction.save()
    elif type_count and min_reaction and max_reaction:
        reaction = Reaction.objects.create(type_count=type_count, min_reaction=min_reaction,
                                           max_reaction=max_reaction)
    return reaction


def change_reaction(task, reaction_start_ladder, reaction_name, basic_min_number, basic_max_number,
                    text_reaction_number, text_min_number, text_max_number, user_reaction_number, user_min_number,
                    user_max_number, ai_reaction_number, ai_min_number, ai_max_number, reaction_old_post):
    reaction = task.reaction
    if not reaction:
        reaction = ReactionParam.objects.create()
        task.reaction = reaction
        task.save(update_fields=['reaction'])
    if reaction_start_ladder:
        ladder = create_ladder(True, reaction_start_ladder)
        reaction.start_ladder = ladder
        reaction.save(update_fields=['start_ladder'])

        basic_reactions = reaction.basic_reactions
        if basic_reactions:
            basic_reactions.reactions = reaction_name
            basic_reactions.min_reaction = basic_min_number
            basic_reactions.max_reaction = basic_max_number
            basic_reactions.save()
        elif reaction_name and basic_min_number and basic_max_number:
            basic_reactions = Reaction.objects.create(reactions=reaction_name, min_reaction=basic_min_number,
                                                      max_reaction=basic_max_number)
            reaction.basic_reactions = basic_reactions
            reaction.save(update_fields=['basic_reactions'])

        text_reactions = reaction_create(reaction.text_reactions, text_reaction_number, text_min_number,
                                         text_max_number)
        reaction.text_reactions = text_reactions

        user_reactions = reaction_create(reaction.user_reactions, user_reaction_number, user_min_number,
                                         user_max_number)
        reaction.user_reactions = user_reactions

        ai_reactions = reaction_create(reaction.ai_reactions, ai_reaction_number, ai_min_number, ai_max_number)
        reaction.ai_reactions = ai_reactions
        reaction.last_post_reaction = reaction_old_post
        reaction.save()


def change_ad(task, ad_detect, ad_subscribe_percent, ad_start_ladder, ad_unsubscribes, ad_channel_reaction, ad_reaction,
              ad_comment):
    ad = task.ad
    if ad:
        ad.ad_detect = ad_detect
        ad.subscribe_percent = ad_subscribe_percent
        ad.start_ladder = ad_start_ladder
        ad.unsubscribes = ad_unsubscribes
        ad.channel_reaction = ad_channel_reaction
        ad.ad_reaction = ad_reaction
        ad.comment = ad_comment
    elif ad_detect:
        ad = AdParam.objects.create(ad_detect=ad_detect)
        if ad_subscribe_percent:
            ad.subscribe_percent = ad_subscribe_percent
        if ad_start_ladder:
            ad.start_ladder = ad_start_ladder
        if ad_unsubscribes:
            ad.unsubscribes = ad_unsubscribes
        if ad_channel_reaction:
            ad.channel_reaction = ad_channel_reaction
        if ad_reaction:
            ad.ad_reaction = ad_reaction
        if ad_comment:
            ad.comment = ad_comment
        ad.save()
        task.ad = ad
        task.save(update_fields=['ad'])


def change_history(task, history_view_count, history_view_ladder_param, history_view_ladder_spread,
                   history_reaction_count, history_reaction_ladder_param, history_reaction_ladder_spread):
    history = task.history
    if history:
        view_ladder = history.view_ladder
        reaction_ladder = history.reaction_ladder
        view_ladder.param = history_view_ladder_param
        view_ladder.spread = history_view_ladder_spread
        view_ladder.save()
        reaction_ladder.param = history_reaction_ladder_param
        reaction_ladder.spread = history_reaction_ladder_spread
        reaction_ladder.save()
        history.view_count = history_view_count
        history.reaction_count = history_reaction_count
        history.save()
    else:
        history = HistoryParam.objects.create()
        l = False
        if history_view_count and history_view_ladder_param and history_view_ladder_spread:
            l = True
            view_ladder = create_ladder(True, history_view_ladder_param, history_view_ladder_spread)
            history.view_count = history_view_count
            history.view_ladder = view_ladder
        if history_reaction_count and history_reaction_ladder_param and history_reaction_ladder_spread:
            l = True
            reaction_ladder = create_ladder(True, history_reaction_ladder_param, history_reaction_ladder_spread)
            history.reaction_count = history_reaction_count
            history.reaction_ladder = reaction_ladder
        if l:
            history.save()
            task.history = history
            task.save(update_fields=['history'])
        else:
            history.delete()


def change_comment(task, min_comment, max_comment, ladder, auto_moderation):
    comment = task.comment
    if comment:
        comment.min_comment = min_comment
        comment.max_comment = max_comment
        comment.ladder = ladder
        comment.auto_moderation = auto_moderation
        comment.save()
    else:
        if min_comment and max_comment and ladder and auto_moderation:
            comment = CommentParam.objects.create(min_comment=min_comment, max_comment=max_comment, ladder=ladder,
                                                  auto_moderation=auto_moderation)
            task.comment = comment
            task.save(update_fields=['comment'])


def add_action(task, link, action_delay, action_percent, action_is_channel, action_is_smile, action_text):
    if link and action_delay and action_percent:
        if action_is_channel == 'channel':
            action_is_channel = True
        else:
            action_is_channel = False
        if action_is_smile == 'emoji':
            action_is_smile = True
        else:
            action_is_smile = False
        action = Action.objects.create(
            link=link,
            is_channel=action_is_channel,
            is_smile=action_is_smile,
            text=action_text,
            delay=action_delay,
            percent=action_percent
        )
        task.action.add(action)


def change_task(task: Task, data_post):
    change_main(task, data_post['subscribers_count'], data_post['channel_link'], data_post['start_time'])
    if add_template(task, data_post['template']):
        change_subscribe(task, data_post['male'], data_post['female'], data_post['start_ladder_type'],
                         data_post['start_ladder_param'], data_post['time_ladder_type'], data_post['time_ladder_param'],
                         data_post['unsubscribes'])
        change_view(task, data_post['view_start_ladder_type'], data_post['view_start_ladder_param'],
                    data_post['view_start_ladder_spread'],
                    data_post['view_time_ladder_type'], data_post['view_time_ladder_param'],
                    data_post['view_time_ladder_spread'], data_post['holiday'], data_post['last_post'],
                    data_post['old_post'])
        change_reaction(task, data_post['reaction_start_ladder'], data_post['reaction_name'],
                        data_post['basic_min_number'], data_post['basic_max_number'],
                        data_post['text_reaction_number'], data_post['text_min_number'], data_post['text_max_number'],
                        data_post['user_reaction_number'], data_post['user_min_number'],
                        data_post['user_max_number'], data_post['ai_reaction_number'], data_post['ai_min_number'],
                        data_post['ai_max_number'], data_post['reaction_old_post'])
        change_ad(task, data_post['ad_detect'], data_post['ad_subscribe_percent'], data_post['ad_start_ladder'],
                  data_post['ad_unsubscribes'], data_post['ad_channel_reaction'],
                  data_post['ad_reaction'], data_post['ad_comment'])
        change_history(task, data_post['history_view_count'], data_post['history_view_ladder_param'],
                       data_post['history_view_ladder_spread'],
                       data_post['history_reaction_count'], data_post['history_reaction_ladder_param'],
                       data_post['history_reaction_ladder_spread'])
        change_comment(task, data_post['min_comment'], data_post['max_comment'], data_post['ladder'],
                       data_post['auto_moderation'])
        add_action(task, data_post['action_link'], data_post['action_delay'], data_post['action_percent'],
                   data_post['action_is_channel'], data_post['action_is_smile'], data_post['action_text'])


def change_template(template: Template, data_post):
    template.name = data_post['name']
    template.save(update_fields=['name'])
    change_subscribe(template, data_post['male'], data_post['female'], data_post['start_ladder_type'],
                     data_post['start_ladder_param'], data_post['time_ladder_type'], data_post['time_ladder_param'],
                     data_post['unsubscribes'])
    change_view(template, data_post['view_start_ladder_type'], data_post['view_start_ladder_param'],
                data_post['view_start_ladder_spread'],
                data_post['view_time_ladder_type'], data_post['view_time_ladder_param'],
                data_post['view_time_ladder_spread'], data_post['holiday'], data_post['last_post'],
                data_post['old_post'])
    change_reaction(template, data_post['reaction_start_ladder'], data_post['reaction_name'],
                    data_post['basic_min_number'], data_post['basic_max_number'],
                    data_post['text_reaction_number'], data_post['text_min_number'], data_post['text_max_number'],
                    data_post['user_reaction_number'], data_post['user_min_number'],
                    data_post['user_max_number'], data_post['ai_reaction_number'], data_post['ai_min_number'],
                    data_post['ai_max_number'], data_post['reaction_old_post'])
    change_ad(template, data_post['ad_detect'], data_post['ad_subscribe_percent'], data_post['ad_start_ladder'],
              data_post['ad_unsubscribes'], data_post['ad_channel_reaction'],
              data_post['ad_reaction'], data_post['ad_comment'])
    change_history(template, data_post['history_view_count'], data_post['history_view_ladder_param'],
                   data_post['history_view_ladder_spread'],
                   data_post['history_reaction_count'], data_post['history_reaction_ladder_param'],
                   data_post['history_reaction_ladder_spread'])
    change_comment(template, data_post['min_comment'], data_post['max_comment'], data_post['ladder'],
                   data_post['auto_moderation'])


def add_session_in_task(task):
    total_sessions = Sessions.objects.count()

    # Корректируем количество подписчиков, если нужно
    if task.subscribers_count > total_sessions:
        task.subscribers_count = total_sessions
        task.save(update_fields=['subscribers_count'])

    subscribe_param = task.subscribe
    total_needed = task.subscribers_count

    # Рассчитываем количество мужских и женских сессий
    male_count = total_needed * int(subscribe_param.male) // 100
    female_count = total_needed * int(subscribe_param.female) // 100

    # Корректируем остаток
    remainder = total_needed - male_count - female_count
    if remainder != 0:
        if male_count:
            male_count += remainder
        else:
            female_count += remainder

    # Получаем количество доступных сессий каждого пола за один запрос
    gender_counts = Sessions.objects.aggregate(
        male_count=Count('pk', filter=models.Q(is_male=True)),
        female_count=Count('pk', filter=models.Q(is_male=False))
    )
    available_male = gender_counts['male_count']
    available_female = gender_counts['female_count']

    # Корректируем распределение, если нужно
    if male_count > available_male:
        female_count += male_count - available_male
        male_count = available_male

    if female_count > available_female:
        male_count += female_count - available_female
        female_count = available_female

    if male_count + female_count == total_sessions:
        task.sessions.set(Sessions.objects.all())
        return

    need_sessions = []

    if female_count > 0:
        female_sessions = list(Sessions.objects.filter(is_male=False).values_list('id', flat=True))
        selected_female = random.sample(female_sessions, min(female_count, len(female_sessions)))
        need_sessions.extend(selected_female)

    if male_count > 0:
        male_sessions = list(Sessions.objects.filter(is_male=True).values_list('id', flat=True))
        selected_male = random.sample(male_sessions, min(male_count, len(male_sessions)))
        need_sessions.extend(selected_male)

    task.sessions.add(*need_sessions)


def create_subscribe_task(task: Task):
    add_session_in_task(task)
    subscribe_param = task.subscribe
    all_sessions = list(task.sessions.all())
    unsubscribe_persent, unsubscribe_time = map(int, subscribe_param.unsubscribes.split('/'))
    unsubscribe_list = all_sessions[:len(all_sessions)*unsubscribe_persent//100]
    start_ladders = []
    time_ladders = []
    if subscribe_param.start_ladder:
        if subscribe_param.start_ladder.is_percent:
            start_ladders = [[task.subscribers_count * int(i.split('/')[0]) // 100, int(i.split('/')[1]) * 60] for i in
                            subscribe_param.start_ladder.param.split('; ')]
        else:
            start_ladders = [list(map(int, i.split('/'))) for i in subscribe_param.start_ladder.param.split('; ')]
    if subscribe_param.time_ladder:
        if subscribe_param.time_ladder.is_percent:
            time_ladders = [[task.subscribers_count * int(i.split('/')[0]) // 100, i.split('/')[1]] for i in
                           subscribe_param.time_ladder.param.split('; ')]
        else:
            time_ladders = [[int(i.split('/')[0]), i.split('/')[1]] for i in
                           subscribe_param.time_ladder.param.split('; ')]
    for start_ladder in start_ladders:
        need_sessions = all_sessions[:start_ladder[0]]
        all_sessions = all_sessions[start_ladder[0]:]
        sleep_time = start_ladder[1] / len(need_sessions) if need_sessions else 0
        subscribe_task = SubscribeTask.objects.create(
                task=task,
                next_action=task.start_time,
                sleep_time=sleep_time
        )
        subscribe_task.sessions.add(*need_sessions)
    for time_ladder in time_ladders:
        today = datetime.now().date()
        need_sessions = all_sessions[:time_ladder[0]]
        all_sessions = all_sessions[time_ladder[0]:]
        start_str, end_str = time_ladder[1].split('-')
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        start_datetime = datetime.combine(today, start_time)
        end_datetime = datetime.combine(today, end_time)
        sleep_time = (end_datetime.timestamp() - start_datetime.timestamp()) / len(need_sessions)
        if datetime.now() > start_datetime:
            start_datetime += timedelta(days=1)
        subscribe_task = SubscribeTask.objects.create(
            task=task,
            next_action=task.start_time,
            sleep_time=sleep_time
        )
        subscribe_task.sessions.add(*need_sessions)
    if unsubscribe_list:
        unsubscribe_task = UnsubscribeTask.objects.create(
            task=task,
            next_action=timezone.now()+timedelta(minutes=unsubscribe_time)
        )
        unsubscribe_task.sessions.add(*unsubscribe_list)


