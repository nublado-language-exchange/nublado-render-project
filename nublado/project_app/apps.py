import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger('django')


class ProjectAppConfig(AppConfig):
    name = "project_app"

    def ready(self):
        dt = settings.DJANGO_TELEGRAM
        if dt['mode'] == settings.BOT_MODE_WEBHOOK:
            from django_telegram.apps import DjangoTelegramConfig
            for bot, conf in settings.DJANGO_TELEGRAM['bots'].items():
                try:
                    #bot_token = settings.DJANGO_TELEGRAM['bots'][settings.NUBLADO_BOT]['token']
                    bot_token = conf['token']
                    bot = DjangoTelegramConfig.bot_registry.get_bot(bot_token)
                    if bot:
                        bot.start()
                except:
                    error = "Bot {} doesn't exist or is improperly configured.".format(settings.NUBLADO_BOT)
                    logger.error(error)