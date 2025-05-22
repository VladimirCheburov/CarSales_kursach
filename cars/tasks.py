from carsales.celery import app
from cars.models import Auto, SellStatus
from celery import shared_task
from django.db.models import F
from carsales.celery import app

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