from django.contrib import admin
from .models import NewCategory, New, NewPhoto, NewCategoryAssignment
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.contrib.staticfiles.storage import staticfiles_storage
import os
from django.conf import settings


# Inline для связи New и Photo через NewPhoto
class NewPhotoInline(admin.TabularInline):
    model = NewPhoto
    extra = 1  # Показать одну пустую строку для добавления связи


class NewCategoryAssignmentInline(admin.TabularInline):
    """
    Inline-модель для отображения связей новостей с категориями в админке.
    """
    model = NewCategoryAssignment
    extra = 1  # Количество пустых строк для добавления новых связей
    readonly_fields = ['date_added']  # Поле только для чтения


# Админка для модели New
@admin.register(New)
class NewAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'profile', 'status', 'created_at')  # Убрано поле 'category'
    actions = ['generate_pdf']
    search_fields = ('title', 'profile__username', 'categoryassignment__category__name')  # Поиск по категории через промежуточную таблицу
    list_filter = ('status', 'created_at')  # Убрано поле 'category', так как оно связано через промежуточную таблицу
    inlines = [NewPhotoInline, NewCategoryAssignmentInline]  # Объединение Inline
    filter_horizontal = ('photos',)  # Добавляем горизонтальный фильтр для фотографий
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'profile', 'status', 'photos')
        }),
    )

    def generate_pdf(self, request, queryset):
        """
        Генерация PDF-документа со списком выбранных новостей.
        """
        # Создаём HTTP-ответ для передачи PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="news.pdf"'

        # Правильный путь к файлу шрифта
        font_path = os.path.join(settings.STATIC_ROOT, 'fonts', 'dejavusans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

        # Создаём PDF
        pdf_canvas = canvas.Canvas(response)
        pdf_canvas.setFont('DejaVuSans', 12)

        pdf_canvas.drawString(100, 800, "Список новостей:")

        y = 750  # Начальная высота для текста
        for new in queryset:
            text = f"{new.id}. {new.title} - {new.created_at.strftime('%d.%m.%Y')}"
            pdf_canvas.drawString(100, y, text)
            y -= 20

        pdf_canvas.save()
        return response

    generate_pdf.short_description = "Скачать PDF для выбранных новостей"


# Админка для категории новостей
@admin.register(NewCategory)
class NewCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

