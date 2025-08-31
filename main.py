from asyncio import create_task
import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewSMMBot.settings')
django.setup()
import accounts, subscribe, actions, views, reactions, comments, historys, unsubscribe

create_task(accounts.main())
create_task(subscribe.main())
create_task(actions.main())
create_task(views.add_view_task_main())
create_task(views.main())
create_task(reactions.main())
create_task(comments.main())
create_task(comments.main_send_comment())
create_task(historys.main())
create_task(unsubscribe.main())
