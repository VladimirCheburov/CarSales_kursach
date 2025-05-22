from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ExportMixin
from import_export.formats.base_formats import XLS
from django.utils.timezone import now
from .models import Auto, AutoPhoto, Profile, Brand, BodyType, EngineType, Color, SellStatus, Region, Photo
from .models import ContactMessage

# для экспорта данных из Auto с использованием django-import-export
class AutoResource(resources.ModelResource):
    brand_name = fields.Field(column_name='Brand Name', readonly=True)
    model_year = fields.Field(column_name='Model Year', readonly=True)
    price_in_rubles = fields.Field(column_name='Price in Rubles', attribute='price', readonly=True)

    class Meta:
        model = Auto
        fields = ('id', 'brand_name', 'model_year', 'description', 'price_in_rubles', 'mileage', 'region__name')
        export_order = ('id', 'brand_name', 'model_year', 'description', 'price_in_rubles', 'mileage', 'region__name')
        
    def dehydrate_brand_name(self, auto):
        """Кастомизация поля 'brand_name': Преобразование названия бренда в верхний регистр."""
        return auto.brand.name.upper()

    def dehydrate_model_year(self, auto):
        """Кастомизация поля 'model_year': Форматирование модели и года выпуска."""
        return f"{auto.model} ({auto.year})"
    
    def get_export_queryset(self, queryset):
        """
        Фильтруем экспортируемые данные:
        Экспортируются только автомобили, выпущенные за последние несколько лет.
        """
        current_year = now().year
        filtered_queryset = queryset.filter(year__gte=current_year - 30)

        return filtered_queryset

    def get_price_in_rubles(self, auto):
        """Кастомизация поля 'price_in_rubles': Преобразование цены в удобный формат."""
        return f"{int(auto.price):,} ₽".replace(",", " ")

    
# добавление/редактирование AutoPhoto в интерфейсе админки Auto
class AutoPhotoInline(admin.TabularInline):
    model = AutoPhoto
    extra = 1
    fields = ['photo']
    autocomplete_fields = ['photo']

# управление photo
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['url', 'description']  # Добавляем колонку для длины описания
    search_fields = ['url', 'description']

# управление auto
class AutoAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = AutoResource
    formats = [XLS]
    
    list_display = ('id', 'brand', 'model', 'year', 'price', 'sell_status', 'display_mileage')
    list_display_links = ('model', 'brand')
    search_fields = ('brand__name', 'model', 'sell_status__name')
    list_filter = ('brand', 'year', 'sell_status')
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'brand', 'model', 'year', 'price', 'description', 'sell_status')
        }),
        ('Дополнительная информация', {
            'fields': ('mileage', 'body_type', 'engine_type', 'color', 'region')
        }),
    )
    inlines = [AutoPhotoInline]
    raw_id_fields = ['brand']
    readonly_fields = ('id',)
    
    # собственный метод
    @admin.display(description='Пробег в километрах')  # устанавливаем заголовок для колонки
    def display_mileage(self, obj):
        return f"{obj.mileage:,} км"  # форматируем пробег с разделителями
    
    display_mileage.short_description = 'Пробег (км)'

# управление autoPhoto
class AutoPhotoAdmin(admin.ModelAdmin):
    list_display = ['auto', 'photo']
    search_fields = ['auto__brand__name', 'auto__model']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    Настройки отображения модели ContactMessage в админке.
    """
    list_display = ('id', 'name', 'email', 'created_at')  # поля, которые будут отображаться в списке сообщений
    list_display_links = ('name', 'email')  # поля, по которым можно кликнуть для перехода в редактирование
    search_fields = ('name', 'email', 'message')  # поля, по которым можно выполнять поиск
    list_filter = ('created_at',)  # фильтр по дате создания
    readonly_fields = ('created_at',)  # поля, которые нельзя редактировать

admin.site.register(Profile)
admin.site.register(Brand)
admin.site.register(BodyType)
admin.site.register(EngineType)
admin.site.register(Color)
admin.site.register(SellStatus)
admin.site.register(Region)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Auto, AutoAdmin)
admin.site.register(AutoPhoto, AutoPhotoAdmin)