import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsales.settings')
    django.setup()

    from cars.models import Auto, Brand, BodyType, EngineType, Color, Region, SellStatus, Profile
    from django.contrib.auth.models import User

    # Получаем или создаём необходимые справочники
    brand1, _ = Brand.objects.get_or_create(name='Toyota')
    brand2, _ = Brand.objects.get_or_create(name='BMW')
    brand3, _ = Brand.objects.get_or_create(name='Lada')
    body_sedan, _ = BodyType.objects.get_or_create(name='Седан')
    body_suv, _ = BodyType.objects.get_or_create(name='Внедорожник')
    engine_petrol, _ = EngineType.objects.get_or_create(name='Бензин')
    engine_diesel, _ = EngineType.objects.get_or_create(name='Дизель')
    color_black, _ = Color.objects.get_or_create(name='Чёрный')
    color_white, _ = Color.objects.get_or_create(name='Белый')
    region_moscow, _ = Region.objects.get_or_create(name='Москва')
    region_spb, _ = Region.objects.get_or_create(name='Санкт-Петербург')
    status_sale, _ = SellStatus.objects.get_or_create(name='В продаже')

    # Получаем пользователя для профиля
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testuser', password='testpass')
    profile, _ = Profile.objects.get_or_create(user=user)

    # Примеры объявлений
    autos = [
        {
            'brand': brand1,
            'model': 'Camry',
            'year': 2018,
            'mileage': 45000,
            'price': 1700000,
            'body_type': body_sedan,
            'engine_type': engine_petrol,
            'color': color_black,
            'region': region_moscow,
            'sell_status': status_sale,
            'description': 'Надёжный седан, один владелец, сервисная книжка.'
        },
        {
            'brand': brand2,
            'model': 'X5',
            'year': 2020,
            'mileage': 25000,
            'price': 4200000,
            'body_type': body_suv,
            'engine_type': engine_diesel,
            'color': color_white,
            'region': region_spb,
            'sell_status': status_sale,
            'description': 'Премиальный внедорожник, максимальная комплектация.'
        },
        {
            'brand': brand3,
            'model': 'Vesta',
            'year': 2022,
            'mileage': 12000,
            'price': 950000,
            'body_type': body_sedan,
            'engine_type': engine_petrol,
            'color': color_white,
            'region': region_moscow,
            'sell_status': status_sale,
            'description': 'Экономичный автомобиль, новый аккумулятор.'
        },
    ]

    for auto in autos:
        Auto.objects.get_or_create(
            brand=auto['brand'],
            model=auto['model'],
            year=auto['year'],
            mileage=auto['mileage'],
            price=auto['price'],
            body_type=auto['body_type'],
            engine_type=auto['engine_type'],
            color=auto['color'],
            region=auto['region'],
            sell_status=auto['sell_status'],
            description=auto['description'],
        )

    print('Объявления успешно добавлены!')

if __name__ == '__main__':
    main() 