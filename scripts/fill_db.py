import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsales.settings')
django.setup()

from cars.models import Auto, Brand, BodyType, EngineType, Color, Region, SellStatus, Profile, AutoPhoto, Favorite, ContactMessage
from news.models import New, NewCategory
from django.contrib.auth.models import User

# 1. Бренды
brands = [
    'Toyota', 'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Ford', 'Hyundai', 'Kia', 'Lada', 'Renault'
]
for name in brands:
    Brand.objects.get_or_create(name=name)

# 2. Типы кузова
body_types = [
    'Седан', 'Хэтчбек', 'Универсал', 'Кроссовер', 'Внедорожник', 'Купе', 'Кабриолет', 'Минивэн', 'Пикап', 'Лифтбек'
]
for name in body_types:
    BodyType.objects.get_or_create(name=name)

# 3. Типы двигателя
engine_types = [
    'Бензин', 'Дизель', 'Гибрид', 'Электро', 'Газ', 'Бензин/Газ', 'Бензин/Электро', 'Дизель/Электро', 'Роторный', 'Водород'
]
for name in engine_types:
    EngineType.objects.get_or_create(name=name)

# 4. Цвета
colors = [
    'Черный', 'Белый', 'Серый', 'Синий', 'Красный', 'Зеленый', 'Желтый', 'Коричневый', 'Оранжевый', 'Фиолетовый'
]
for name in colors:
    Color.objects.get_or_create(name=name)

# 5. Регионы
regions = [
    'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород', 'Челябинск', 'Самара', 'Ростов-на-Дону', 'Уфа'
]
for name in regions:
    Region.objects.get_or_create(name=name)

# 6. Статусы продажи
statuses = [
    'В продаже', 'Продан', 'Резерв', 'На складе', 'Ожидает оплаты', 'В пути', 'Снят с продажи', 'Тест-драйв', 'Уценка', 'Новинка'
]
for name in statuses:
    SellStatus.objects.get_or_create(name=name)

# 7. Пользователи и профили
for i in range(1, 11):
    user, _ = User.objects.get_or_create(username=f'user{i}', defaults={'email': f'user{i}@mail.ru'})
    Profile.objects.get_or_create(user=user)

# 8. Новости и категории
categories = ['Советы', 'Обзоры', 'События', 'Тест-драйвы', 'Рынок', 'Технологии', 'Безопасность', 'Экология', 'Спорт', 'Истории']
for name in categories:
    NewCategory.objects.get_or_create(name=name)
for i in range(1, 11):
    cat = NewCategory.objects.order_by('?').first()
    New.objects.get_or_create(
        title=f'Новость {i}',
        content=f'Содержимое новости {i}.',
        status='published',
        created_at=timezone.now() - timedelta(days=i),
        defaults={'categories': [cat]}
    )

# 9. Автомобили
brands_qs = list(Brand.objects.all())
bodies_qs = list(BodyType.objects.all())
engines_qs = list(EngineType.objects.all())
colors_qs = list(Color.objects.all())
regions_qs = list(Region.objects.all())
statuses_qs = list(SellStatus.objects.all())
profiles_qs = list(Profile.objects.all())
for i in range(1, 11):
    Auto.objects.get_or_create(
        brand=random.choice(brands_qs),
        description=f'Описание автомобиля {i}',
        model=f'Модель {i}',
        year=2010 + i,
        mileage=random.randint(10000, 200000),
        price=random.randint(500000, 3000000),
        body_type=random.choice(bodies_qs),
        engine_type=random.choice(engines_qs),
        color=random.choice(colors_qs),
        region=random.choice(regions_qs),
        sell_status=random.choice(statuses_qs),
    )

# 10. Избранное
autos = list(Auto.objects.all())
users = list(User.objects.all())
for i in range(10):
    Favorite.objects.get_or_create(user=random.choice(users), auto=random.choice(autos))

# 11. Сообщения
for i in range(1, 11):
    ContactMessage.objects.get_or_create(
        name=f'Пользователь {i}',
        email=f'user{i}@mail.ru',
        message=f'Сообщение {i}',
        created_at=timezone.now() - timedelta(days=i)
    )

print('База данных успешно наполнена логичными тематическими данными!') 