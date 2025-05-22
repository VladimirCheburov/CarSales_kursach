from django.test import TestCase
from cars.models import Auto, Brand, BodyType, EngineType, Color, Region, SellStatus, Profile

class SimpleAutoTest(TestCase):
    def test_auto_creation(self):
        brand = Brand.objects.create (name="Toyota")
        body_type = BodyType.objects.create (name="Седан")
        engine_type = EngineType.objects.create (name="Бензин")
        color = Color.objects.create (name="Чёрный")
        region = Region.objects.create (name="Москва")
        sell_status = SellStatus.objects.create (name="На продаже")
        profile = Profile.objects.create (username="testuser")


        auto = Auto.objects.create(
            brand=brand,
            description="Отличный автомобиль",
            model="Camry",
            year=2022,
            mileage=15000,
            price=2000000,
            body_type=body_type,
            engine_type=engine_type,
            color=color,
            region=region,
            sell_status=sell_status,
            profile=profile,
        )

        self.assertEqual(auto.brand.name, "Toyota")
        self.assertEqual(auto.model, "Camry")
        self.assertEqual(auto.year, 2022)
        self.assertEqual(auto.price, 2000000)
        self.assertEqual(auto.profile.username, "testuser")
