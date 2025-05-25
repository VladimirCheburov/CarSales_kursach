from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now 
from datetime import timedelta 
from django.urls import reverse
from django.contrib.auth.models import User

class Profile(models.Model):
    # Связь с моделью User
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=1)

    # Дополнительные поля профиля
    phone_num = models.CharField(max_length=20, blank=True, null=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='profile_groups',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='profile_permissions',
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name_plural = "Пользователи"
        
def default_token_expiry():
    """Функция для вычисления срока действия токена."""
    return now() + timedelta(hours=1)

class GoogleOAuthProfile(models.Model):
    user = models.ForeignKey(
        'cars.Profile',  # ссылка на модель пользователя
        on_delete=models.CASCADE,
        related_name='google_oauth_profiles'
    )
    google_user_id = models.CharField(max_length=255, unique=True)  # ID пользователя Google
    access_token = models.TextField()  # Access Token
    refresh_token = models.TextField()  # Refresh Token
    token_expiry = models.DateTimeField(default=default_token_expiry)  # срок действия токена
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Профили Google OAuth"

    def __str__(self):
        return f"GoogleOAuthProfile({self.user.username})"
    
class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Автомобильные марки"

    def __str__(self):
        return self.name


class BodyType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Типы кузова"

    def __str__(self):
        return self.name


class EngineType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Типы двигателей"

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Цвета"

    def __str__(self):
        return self.name


class SellStatus(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Статусы продажи"

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Местоположение"
        
    def __str__(self):
        return self.name


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django автоматически задаст значение этого поля при создании объекта. 
    # после этого его нельзя изменить

    class Meta:
        abstract = True 

class AutoManager(models.Manager):
    def available(self):
        """
        Возвращает автомобили, доступные для продажи (не проданы).
        """
        return self.filter(sell_status__name__iexact="В продаже")

class Auto(TimeStamped):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT) 
    # on_delete=models.PROTECT предотвращает удаление бренда, если он связан с автомобилем
    description = models.TextField()
    model = models.CharField(max_length=255)
    year = models.IntegerField(verbose_name="Год выпуска")
    mileage = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0) # кол-во знаков после запятой
    body_type = models.ForeignKey(BodyType, on_delete=models.PROTECT)
    engine_type = models.ForeignKey(EngineType, on_delete=models.PROTECT)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    sell_status = models.ForeignKey(SellStatus, on_delete=models.PROTECT, null=True, blank=True)
    # on_delete=models.CASCADE удаляет автомобиль, если связанный пользователь удалён
    views = models.PositiveIntegerField(default=0)  # Новое поле для подсчёта просмотров
    objects = AutoManager()
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "Автомобили"

    def __str__(self):
        return f"{self.brand.name} {self.model} ({self.year})"
    
    def get_absolute_url(self):
        """
        Возвращает URL для просмотра деталей автомобиля.
        """
        return reverse('auto_detail', kwargs={'pk': self.pk})


class Photo(models.Model):
    url = models.URLField(max_length=700)
    description = models.TextField(blank=False, null=False) # описание = название

    class Meta:
        verbose_name_plural = "Фото"

    def __str__(self):
        return self.description 

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Переопределяем метод save для автоматического преобразования имени в заглавный регистр.
        """
        self.name = self.name.title()  # преобразуем имя в заглавный регистр
        super().save(*args, **kwargs)  # вызываем метод save()

    def __str__(self):
        return f"{self.name} - {self.email}"
    
class AutoPhoto(models.Model):
    auto = models.ForeignKey(Auto, on_delete=models.CASCADE, related_name="auto_photos")
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Фото автомобилей"

    def __str__(self):
        return f"{self.auto.brand.name} {self.auto.model} ({self.auto.year})"
    
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auto = models.ForeignKey('Auto', on_delete=models.CASCADE, related_name='favorite')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'auto')
        verbose_name_plural = 'Избранные'
    def __str__(self):
        return f"{self.user.username} - {self.auto}"
    
