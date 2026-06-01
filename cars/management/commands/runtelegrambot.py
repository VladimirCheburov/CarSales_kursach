from django.core.management.base import BaseCommand

from bots.telegram_bot import run_bot


class Command(BaseCommand):
    help = 'Запуск Telegram-бота интеграции с платформой CarSales'

    def handle(self, *args, **options):
        run_bot()
