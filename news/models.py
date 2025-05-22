from django.db import models
from cars.models import Profile
from PIL import Image
class NewCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Категории новостей"

    def __str__(self):
        return self.name


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class New(TimeStamped):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'Архивировано'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    categories = models.ManyToManyField('NewCategory', through='NewCategoryAssignment')
    photos = models.ManyToManyField('NewPhoto', blank=True, related_name="news")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft' 
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title


class NewCategoryAssignment(models.Model):
    """
    Промежуточная модель для связи между New и NewCategory с дополнительным полем date_added.
    """
    new = models.ForeignKey(New, on_delete=models.CASCADE)
    category = models.ForeignKey(NewCategory, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('new', 'category')
        verbose_name_plural = "Связи новостей с категориями"

    def __str__(self):
        return f"Новость: {self.new.title}, Категория: {self.category.name}, Дата добавления: {self.date_added}"


class NewPhoto(models.Model):
    new = models.ForeignKey(New, on_delete=models.CASCADE, related_name="new_photos")
    image = models.ImageField(upload_to='news_photos/')  # поле для хранения картинок
    photofile = models.FileField(upload_to='news_photos/', default='default_image.jpg')  
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Фото для новости"

    def __str__(self):
        return f"{self.new.title} - {self.description or 'Фото'}"
    
    def save(self, *args, **kwargs):
        """
        Переопределяем метод save для изменения размера изображения.
        """
        super().save(*args, **kwargs)  # cначала сохраняем изображение

        img_path = self.image.path  # путь к сохраненному изображению
        img = Image.open(img_path)  # открываем изображение с помощью Pillow

        # проверяем, если изображение больше 800x800, уменьшаем его
        max_size = (300, 300)
        if img.height > 300 or img.width > 300:
            img.thumbnail(max_size)  # изменяем размер изображения
            img.save(img_path)  # сохраняем измененное изображение
        
        # thumbnail изменяет размер изображения, сохраняя его пропорции