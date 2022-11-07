import logging

from django.conf import settings
from django.apps import AppConfig

from django_telegram.apps import DjangoTelegramConfig
from django_telegram.bot import Bot

logger = logging.getLogger('django')


class NubladoBotConfig(AppConfig):
    name = 'nublado_bot'
    bot_key = settings.NUBLADO_BOT_TOKEN

    def ready(self):
        from .bot_commands.group_notes import (
            group_notes,
            save_group_note,
            remove_group_note,
            get_group_note_handler
        )
        from .bot_commands.group_admin import(
            update_group_admins,
            get_non_members,
            member_join_handler,
            member_exit_handler,
            welcome_button_handler,
            set_bot_language
        )
        from .bot_commands.misc import (
            start, echo, reverse_text, hello, roll,
            roll_sum
        )
        from .bot_commands.language_days import (
            schedule, language_day, initiate_language_day_c,
            initiate_language_day
        )
        from .bot_commands.group_points import (
            add_points_handler, remove_points_handler
        )

        bot_registry = DjangoTelegramConfig.bot_registry
        bot = Bot(settings.NUBLADO_BOT_TOKEN)

        # Register handlers
        # group_admin
        bot.add_command_handler('update_group_admins', update_group_admins)
        bot.add_command_handler('get_non_members', get_non_members)
        bot.add_command_handler('set_bot_language', set_bot_language)
        bot.add_handler(member_join_handler, handler_group=2)
        bot.add_handler(member_exit_handler, handler_group=2)
        bot.add_handler(welcome_button_handler, handler_group=2)
        # misc
        bot.add_command_handler('start', start)
        bot.add_command_handler('reverse', reverse_text)
        bot.add_command_handler('echo', echo)
        bot.add_command_handler('hello', hello)
        bot.add_command_handler('roll', roll)
        bot.add_command_handler('roll_sum', roll_sum)
        # language_days
        bot.add_command_handler('schedule', schedule)
        bot.add_command_handler('language_day', language_day)
        bot.add_command_handler('initiate_language_day', initiate_language_day)
        # bot.schedule_daily_task(
        #     initiate_language_day_c,
        #     hour=settings.LANGUAGE_DAY_HOUR_CHANGE,
        #     minute=settings.LANGUAGE_DAY_MINUTE_CHANGE,
        #     name="Initiate language day"         
        # )
        # group_points
        bot.add_handler(add_points_handler, handler_group=2)
        bot.add_handler(remove_points_handler, handler_group=2)
        # notes
        bot.add_command_handler('group_notes', group_notes)
        bot.add_command_handler('save_group_note', save_group_note)
        bot.add_command_handler('remove_group_note', remove_group_note)
        bot.add_handler(get_group_note_handler, handler_group=2)
        # Add the bot to the registry.
        bot_registry.add_bot(NubladoBotConfig.bot_key, bot)

