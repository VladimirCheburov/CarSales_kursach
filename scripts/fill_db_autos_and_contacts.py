import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsales.settings')
django.setup()

from cars.models import Auto, Brand, BodyType, EngineType, Color, Region, SellStatus, ContactMessage

# Получаем объекты для связей (берём по названию, чтобы не было рандома)
brand_map = {b.name: b for b in Brand.objects.all()}
body_map = {b.name: b for b in BodyType.objects.all()}
engine_map = {e.name: e for e in EngineType.objects.all()}
color_map = {c.name: c for c in Color.objects.all()}
region_map = {r.name: r for r in Region.objects.all()}
status_map = {s.name: s for s in SellStatus.objects.all()}

# Используем существующие регионы
cars_data = [
    {
        'brand': 'Toyota', 'model': 'Camry', 'year': 2018, 'description': 'Один владелец, сервисная книжка, пробег 60 000 км.',
        'mileage': 60000, 'price': 1850000, 'body_type': 'Седан', 'engine_type': 'Бензин', 'color': 'Черный', 'region': 'Москва', 'sell_status': 'В продаже'
    },
    {
        'brand': 'BMW', 'model': 'X5', 'year': 2017, 'description': 'Полный привод, кожа, панорама, пробег 80 000 км.',
        'mileage': 80000, 'price': 3200000, 'body_type': 'Кроссовер', 'engine_type': 'Дизель', 'color': 'Белый', 'region': 'Санкт-Петербург', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Kia', 'model': 'Rio', 'year': 2020, 'description': 'Гарантия до 2025 года, пробег 25 000 км.',
        'mileage': 25000, 'price': 1100000, 'body_type': 'Седан', 'engine_type': 'Бензин', 'color': 'Синий', 'region': 'Самарская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Hyundai', 'model': 'Creta', 'year': 2019, 'description': 'Оригинальный ПТС, один владелец, пробег 40 000 км.',
        'mileage': 40000, 'price': 1450000, 'body_type': 'Кроссовер', 'engine_type': 'Бензин', 'color': 'Серый', 'region': 'Новосибирская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Lada', 'model': 'Vesta', 'year': 2021, 'description': 'Новая резина, пробег 15 000 км.',
        'mileage': 15000, 'price': 950000, 'body_type': 'Седан', 'engine_type': 'Бензин', 'color': 'Красный', 'region': 'Нижегородская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Volkswagen', 'model': 'Polo', 'year': 2016, 'description': 'Пробег 90 000 км, кондиционер, сигнализация.',
        'mileage': 90000, 'price': 870000, 'body_type': 'Седан', 'engine_type': 'Бензин', 'color': 'Белый', 'region': 'Московская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Mitsubishi', 'model': 'Outlander', 'year': 2018, 'description': 'Полноприводный, пробег 70 000 км.',
        'mileage': 70000, 'price': 1200000, 'body_type': 'Кроссовер', 'engine_type': 'Дизель', 'color': 'Зеленый', 'region': 'Республика Башкортостан', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Ford', 'model': 'Focus', 'year': 2015, 'description': 'Пробег 100 000 км, два комплекта резины.',
        'mileage': 100000, 'price': 750000, 'body_type': 'Хетчбэк', 'engine_type': 'Бензин', 'color': 'Серый', 'region': 'Московская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Audi', 'model': 'A4', 'year': 2019, 'description': 'Премиум комплектация, пробег 30 000 км.',
        'mileage': 30000, 'price': 2100000, 'body_type': 'Седан', 'engine_type': 'Бензин', 'color': 'Черный', 'region': 'Московская область', 'sell_status': 'В продаже'
    },
    {
        'brand': 'Mercedes-Benz', 'model': 'GLC', 'year': 2020, 'description': 'Пробег 20 000 км, AMG пакет.',
        'mileage': 20000, 'price': 3900000, 'body_type': 'Кроссовер', 'engine_type': 'Бензин', 'color': 'Белый', 'region': 'Москва', 'sell_status': 'В продаже'
    },
]

for car in cars_data:
    Auto.objects.create(
        brand=brand_map[car['brand']],
        model=car['model'],
        year=car['year'],
        description=car['description'],
        mileage=car['mileage'],
        price=car['price'],
        body_type=body_map[car['body_type']],
        engine_type=engine_map[car['engine_type']],
        color=color_map[car['color']],
        region=region_map[car['region']],
        sell_status=status_map[car['sell_status']],
    )

# 10 реальных сообщений
messages_data = [
    {'name': 'Иван Петров', 'email': 'ivan.petrov@mail.ru', 'message': 'Здравствуйте! Интересует Toyota Camry. Можно ли посмотреть авто сегодня?'},
    {'name': 'Мария Иванова', 'email': 'maria.ivanova@mail.ru', 'message': 'Добрый день! Актуален ли BMW X5? Возможен ли торг?'},
    {'name': 'Алексей Смирнов', 'email': 'alexey.smirnov@mail.ru', 'message': 'Здравствуйте! Kia Rio на гарантии? Есть ли сервисная книжка?'},
    {'name': 'Ольга Кузнецова', 'email': 'olga.kuz@mail.ru', 'message': 'Интересует Hyundai Creta. Какой расход топлива?'},
    {'name': 'Дмитрий Соколов', 'email': 'dmitry.sokolov@mail.ru', 'message': 'Lada Vesta: был ли автомобиль в ДТП?'},
    {'name': 'Екатерина Попова', 'email': 'ekaterina.popova@mail.ru', 'message': 'Volkswagen Polo: сколько владельцев у авто?'},
    {'name': 'Сергей Лебедев', 'email': 'sergey.lebedev@mail.ru', 'message': 'Renault Duster: есть ли зимняя резина?'},
    {'name': 'Анна Новикова', 'email': 'anna.novikova@mail.ru', 'message': 'Ford Focus: возможен обмен?'},
    {'name': 'Павел Морозов', 'email': 'pavel.morozov@mail.ru', 'message': 'Audi A4: какой реальный расход топлива?'},
    {'name': 'Юлия Васильева', 'email': 'yulia.vasilieva@mail.ru', 'message': 'Mercedes-Benz GLC: есть ли сервисная история?'},
]

for i, msg in enumerate(messages_data):
    ContactMessage.objects.create(
        name=msg['name'],
        email=msg['email'],
        message=msg['message'],
        created_at=timezone.now() - timedelta(days=i)
    )

print('Добавлено 10 реальных объявлений и 10 реальных сообщений!') 