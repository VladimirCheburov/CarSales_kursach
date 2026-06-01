from carsales.celery import app
from cars.models import Auto, SellStatus, Message, Profile
from celery import shared_task
from django.db.models import F
from django.conf import settings
import logging
import requests

logger = logging.getLogger(__name__)

@app.task
def increase_auto_prices():
    """
    Повышает цену всех автомобилей на 10% каждую пятницу.
    """
    Auto.objects.update(price=F('price') * 1.10)  
    print("Цены на автомобили увеличены на 10%")

@app.task
def mark_autos_as_sold():
    """
    Переводит автомобили в статус "Успейте купить", если их цена ниже 100,000.
    """
    try:
        sold_status = SellStatus.objects.get(name="Успейте купить")
        autos_updated = Auto.objects.filter(price__lt=100000).update(sell_status=sold_status)

        print(f"{autos_updated} автомобилей переведены в статус 'Успейте купить'")
    except SellStatus.DoesNotExist:
        print("Статус 'Успейте купить' не найден. Убедитесь, что он существует в базе данных.")


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def notify_telegram_new_message(self, message_id):
    """
    Асинхронная отправка уведомления в Telegram при новом сообщении на сайте.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        logger.info('TELEGRAM_BOT_TOKEN не задан, уведомление пропущено.')
        return

    try:
        message = Message.objects.select_related(
            'auto', 'sender', 'receiver',
        ).get(pk=message_id)
    except Message.DoesNotExist:
        return

    try:
        profile = Profile.objects.get(user=message.receiver)
    except Profile.DoesNotExist:
        return

    if not profile.telegram_chat_id:
        return

    text = (
        f"Новое сообщение по объявлению {message.auto}\n"
        f"От: {message.sender.username}\n"
        f"Текст: {message.message[:500]}\n\n"
        f"Ответьте в боте: /message {message.auto_id} ваш текст"
    )
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(
        url,
        json={'chat_id': profile.telegram_chat_id, 'text': text},
        timeout=10,
    )
    if response.status_code != 200:
        logger.error('Telegram API error: %s', response.text)
        raise self.retry(exc=Exception(response.text))
