import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsales.settings')
    django.setup()

    from news.models import New, NewCategory
    from cars.models import Profile
    from django.contrib.auth.models import User

    # Создаём категорию "Советы", если её нет
    advice_category, created = NewCategory.objects.get_or_create(name='Советы')

    # Получаем первого пользователя для привязки к советам
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testuser', password='testpass')
    profile, _ = Profile.objects.get_or_create(user=user)

    # Примеры советов
    advices = [
        {
            'title': 'Как выбрать подержанный автомобиль',
            'content': 'Проверьте историю автомобиля, обратите внимание на пробег и состояние кузова.'
        },
        {
            'title': 'На что обратить внимание при покупке',
            'content': 'Осмотрите салон, проверьте документы, проведите тест-драйв.'
        },
        {
            'title': 'Преимущества покупки у официального дилера',
            'content': 'Гарантия, прозрачная история, юридическая чистота.'
        },
    ]

    for advice in advices:
        new_obj, created = New.objects.get_or_create(
            title=advice['title'],
            defaults={
                'content': advice['content'],
                'profile': profile,
                'status': 'published',
            }
        )
        new_obj.categories.add(advice_category)
        new_obj.status = 'published'
        new_obj.save()

    print('Советы успешно добавлены!')

if __name__ == '__main__':
    main() 