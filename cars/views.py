from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.cache import cache
from django.db.models import Q
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from django.http import HttpResponse
from cars.models import Auto, AutoPhoto, Brand, BodyType, EngineType, Color, Region, SellStatus, Profile
from cars.serializers import AutoSerializer, BrandSerializer, ProfileSerializer
from news.models import New
#для форм
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .forms import ContactForm
from .forms import AutoForm, AutoPhotoForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cars.models import Favorite
from django.views.decorators.http import require_POST

class AutoFilterAPIView(generics.ListAPIView):
    """
    API для фильтрации автомобилей.
    """
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer
    filter_backends = [SearchFilter]
    search_fields = ['brand__name', 'model', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        brand = self.request.GET.get('brand')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        region = self.request.GET.get('region')
        year = self.request.GET.get('year')

        if brand:
            queryset = queryset.filter(brand__name__icontains=brand)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if region:
            queryset = queryset.filter(region__name__icontains=region)
        if year:
            queryset = queryset.filter(year=year)

        return queryset

def index(request):

    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ContactForm()

    autos = Auto.objects.available()  # получаем все автомобили в продаже
    paginator = Paginator(autos, 3)  # пагинация: 3 автомобиля на одной странице

    page = request.GET.get('page')  # получаем текущую страницу из запроса
    try:
        autos_page = paginator.page(page)  # получаем автомобили для текущей страницы
    except PageNotAnInteger:
        autos_page = paginator.page(1)  # если страница не является числом, показываем первую страницу
    except EmptyPage:
        autos_page = paginator.page(paginator.num_pages)  # если страница пустая, показываем последнюю страницу

    # формируем список автомобилей с фотографиями
    autos_with_photos = [
        {"auto": auto, "photos": AutoPhoto.objects.filter(auto=auto)}
        for auto in autos_page
    ]
    latest_news = New.objects.all().order_by('-created_at')[:2]  
    # получаем новости, отсортированные по дате создания, ограничиваем 2 новостями

    # Популярные авто (по просмотрам)
    popular_autos = Auto.objects.available().order_by('-views')[:5]

    # Советы (категория 'Советы')
    advice_category = None
    advice_news = []
    from news.models import NewCategory
    try:
        advice_category = NewCategory.objects.get(name__iexact='Советы')
        advice_news = New.objects.filter(categories=advice_category, status='published').order_by('-created_at')[:3]
    except NewCategory.DoesNotExist:
        advice_news = []

    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Auto.objects.filter(favorite__user=request.user).values_list('id', flat=True))

    return render(request, 'index.html', {
        'autos_with_photos': autos_with_photos,
        'autos_page': autos_page,
        'autos': autos, 
        'latest_news': latest_news,
        'popular_autos': popular_autos,
        'advice_news': advice_news,
        'favorite_ids': favorite_ids,
    })

def auto_detail(request, pk):

    auto = get_object_or_404(Auto, pk=pk)

    # Увеличиваем счетчик просмотров
    auto.views = auto.views + 1
    auto.save(update_fields=['views'])

    photos = auto.auto_photos.all()

    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Auto.objects.filter(favorite__user=request.user).values_list('id', flat=True))

    return render(request, 'auto_detail.html', {
        'auto': auto,
        'photos': photos,
        'favorite_ids': favorite_ids
    })

def auto_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Получаем данные из тела запроса
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON data")
        serializer = AutoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])

def search_autos(request):
    query = request.GET.get('q')  # получаем поисковый запрос из URL
    results = []

    if query:
        # выполняем поиск по модели, бренду и описанию автомобиля
        results = Auto.objects.filter(
            Q(brand__name__icontains=query) |
            Q(model__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'search_results.html', {'results': results, 'query': query})

def auto_delete(request, pk):
    if request.method == "DELETE":
        auto = get_object_or_404(Auto, pk=pk)
        auto.delete()
        return JsonResponse({'message': 'Auto deleted'}, status=204)
    else:
        return HttpResponseNotAllowed(['DELETE'])


class AutoListView(generics.ListAPIView):
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer
    filter_backends = [SearchFilter]
    search_fields = ['brand__name', 'model', 'description']

    def get_queryset(self):
        sell_status = self.request.GET.get('sell_status')
        if sell_status:
            return Auto.objects.filter(sell_status=sell_status)
        return Auto.objects.all()
  
class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с марками автомобилей.
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с профилями пользователей.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer

    @action(methods=['GET'], detail=False, url_path='recommended-autos')
    def recommended_autos(self, request):
        """
        Рекомендованные автомобили с возможностью ограничения количества.
        """
        recommended_cars = Auto.objects.filter(
            (Q(brand__name__icontains="BMW") | Q(brand__name__icontains="Mercedes-Benz")) &
            ~Q(price__gte=5000000) &
            Q(year__gte=2015)
        )
        limit = request.GET.get('limit')
        if limit:
            try:
                limit = int(limit)
                recommended_cars = recommended_cars[:limit]
            except ValueError:
                pass

        if not recommended_cars.exists():
            return Response({"message": "No recommended cars found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(recommended_cars, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='luxury-autos')
    def luxury_autos(self, request):
        """
        Премиальные автомобили:
        - Марки Porsche или Lexus
        - Пробег менее 100,000
        - Доступны только в регионе "Москва"
        """
        luxury_cars = Auto.objects.filter(
            (Q(brand__name__icontains="Porsche") | Q(brand__name__icontains="Lexus")) &  # или
            ~Q(mileage__gte=100000) &  # не
            Q(region__name__icontains="Москва")  # и
        )
        if not luxury_cars.exists():
            return Response({"message": "No luxury cars found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(luxury_cars, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(methods=['POST'], detail=False, url_path='create-auto')
    def create_auto(self, request):
        """
        Метод для создания нового автомобиля через POST-запрос.
        """
        # получение данных из тела запроса
        data = request.data

        try:
            # проверка пользователя
            user = request.user
            if not user.is_authenticated:
                return Response({"error": "Вы должны быть авторизованы, чтобы создать автомобиль"}, status=status.HTTP_401_UNAUTHORIZED)

            # проверка связанного профиля
            try:
                profile = Profile.objects.get(id=user.id)
            except Profile.DoesNotExist:
                return Response({"error": "У текущего пользователя нет связанного профиля"}, status=status.HTTP_400_BAD_REQUEST)

            # получение связанных моделей
            brand = Brand.objects.get(id=data.get("brand_id"))
            body_type = BodyType.objects.get(id=data.get("body_type_id"))
            engine_type = EngineType.objects.get(id=data.get("engine_type_id"))
            color = Color.objects.get(id=data.get("color_id"))
            region = Region.objects.get(id=data.get("region_id"))
            sell_status = SellStatus.objects.get(id=data.get("sell_status_id"))

            # создание автомобиля
            auto = Auto.objects.create(
                brand=brand,
                model=data.get("model"),
                year=data.get("year"),
                description=data.get("description", ""),
                mileage=data.get("mileage"),
                price=data.get("price"),
                body_type=body_type,
                engine_type=engine_type,
                color=color,
                region=region,
                sell_status=sell_status,
                profile=profile
            )

            serializer = AutoSerializer(auto)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Brand.DoesNotExist:
            return Response({"error": "Указанная марка не найдена"}, status=status.HTTP_400_BAD_REQUEST)
        except BodyType.DoesNotExist:
            return Response({"error": "Указанный тип кузова не найден"}, status=status.HTTP_400_BAD_REQUEST)
        except EngineType.DoesNotExist:
            return Response({"error": "Указанный тип двигателя не найден"}, status=status.HTTP_400_BAD_REQUEST)
        except Color.DoesNotExist:
            return Response({"error": "Указанный цвет не найден"}, status=status.HTTP_400_BAD_REQUEST)
        except Region.DoesNotExist:
            return Response({"error": "Указанный регион не найден"}, status=status.HTTP_400_BAD_REQUEST)
        except SellStatus.DoesNotExist:
            return Response({"error": "Указанный статус продажи не найден"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Отсутствует поле: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Ошибка сервера: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# поиск по содержанию
class AutoSearchAPIView(ListAPIView):
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer
    filter_backends = [SearchFilter]
    search_fields = ['brand__name', 'model', 'description']

from django.http import JsonResponse
from django.db.models import F, Q
from cars.models import Auto

def manage_autos(request):
    """
    Универсальная функция для работы с автомобилями:
    - Получение значений (values, values_list)
    - Подсчёт записей (count, exists)
    - Обновление (update)
    - Удаление (delete)
    """
    action = request.GET.get('action')

    if action == 'values':
        # получение списка автомобилей в виде словарей
        autos = Auto.objects.values('id', 'model', 'price', 'year')
        return JsonResponse(list(autos), safe=False)

    elif action == 'values_list':
        # получение списка автомобилей в виде кортежей
        autos = Auto.objects.values_list('id', 'model', 'price', 'year')
        return JsonResponse(list(autos), safe=False)

    elif action == 'count':
        # подсчёт всех автомобилей
        total_count = Auto.objects.count()
        return JsonResponse({'total_count': total_count})

    elif action == 'exists':
        # проверка наличия автомобилей с ценой выше 10 млн
        expensive_exists = Auto.objects.filter(price__gt=10000000).exists()
        return JsonResponse({'expensive_exists': expensive_exists})

    elif action == 'update':
        # увеличение цены всех автомобилей на 10%
        updated_count = Auto.objects.update(price=F('price') * 1.1)
        return JsonResponse({'updated_count': updated_count})

    elif action == 'delete':
        # удаление автомобилей, выпущенных до 2000 года
        deleted_count, _ = Auto.objects.filter(year__lt=2000).delete()
        return JsonResponse({'deleted_count': deleted_count})

    else:
        # если параметр action не передан или неверный
        return JsonResponse({'error': 'Invalid or missing action parameter'}, status=400)


# пагинация
class CustomPagination(PageNumberPagination):
    """
    Кастомный класс пагинации с обработкой ошибок.
    """
    page_size = 3  # количество объектов на одной странице
    
    def get_paginated_responce(self, data):
        """
        Формируем кастомный ответ для клиента.
        """
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Обработка ошибок для несуществующих страниц
        """
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:
            raise NotFound("Неверный запрос: страницы с таким номером не существует.")
        
class AutoListView(ListAPIView):
    """
    API для получения списка автомобилей с пагинацией.
    """
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer
    pagination_class = CustomPagination

# redis
def get_cached_autos():
    return list(Auto.objects.select_related('brand').all())

# представление
def autos_list_view(request):
    autos = get_cached_autos()  # получаем список автомобилей из кэша или базы

    # формируем данные для ответа
    data = [
        {
            "id": auto.id,
            "brand": auto.brand.name,
            "model": auto.model,
            "year": auto.year,
            "price": float(auto.price),
        }
        for auto in autos
    ]

    return JsonResponse(data, safe=False)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        print("POST данные:", request.POST)  
        print("FILES данные:", request.FILES)  
        if form.is_valid():
            print("Данные формы валидны.")  
            form.save()
            return redirect('index')
        else:
            print("Ошибки формы:", form.errors)  
    else:
        form = ContactForm()
    
    return render(request, 'index.html', {'form': form})

def test_view(request):
    autos = Auto.objects.all()
    return render(request, 'test_template.html', {'autos_with_photos': autos})

def auto_list(request):
    autos = Auto.objects.all() 
    return render(request, 'cars/autos_list.html', {'autos': autos})

@login_required
def favorite_autos(request):
    user = request.user
    favorites = Auto.objects.filter(favorite__user=user)
    favorite_ids = list(favorites.values_list('id', flat=True))
    return render(request, 'cars/favorite_autos.html', {'favorites': favorites, 'favorite_ids': favorite_ids})

# Фильтрация по региону

def autos_by_region(request, region_id):
    autos = Auto.objects.available().filter(region_id=region_id)
    region = Region.objects.get(id=region_id)
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Auto.objects.filter(favorite__user=request.user).values_list('id', flat=True))
    return render(request, 'cars/autos_by_region.html', {'autos': autos, 'region': region, 'favorite_ids': favorite_ids})

# Ограничение редактирования объявлений только владельцем
@login_required
def edit_auto(request, pk):
    auto = get_object_or_404(Auto, pk=pk)
    if auto.profile.user != request.user:
        messages.error(request, 'Вы не можете редактировать это объявление.')
        return redirect('auto_detail', pk=pk)
    if request.method == 'POST':
        form = AutoForm(request.POST, instance=auto)
        if form.is_valid():
            form.save()
            return redirect('auto_list')
    else:
        form = AutoForm(instance=auto)
    return render(request, 'cars/edit_auto.html', {'form': form, 'auto': auto})

def delete_auto(request, pk):
    # получаем объект автомобиля по pk
    auto = get_object_or_404(Auto, pk=pk)
    auto.delete()  # удаляем объект из базы данных
    return redirect('auto_list')


# cars/views.py
def add_auto(request):
    if request.method == 'POST':
        auto_form = AutoForm(request.POST, request.FILES)
        photo_form = AutoPhotoForm(request.POST, request.FILES)

        if auto_form.is_valid() and photo_form.is_valid():
            # Сохраняем автомобиль без привязки к профилю
            auto = auto_form.save()

            # Сохраняем фотографию
            photo = photo_form.save(commit=False)
            photo.auto = auto
            photo.save()

            return redirect('auto_list')
    else:
        auto_form = AutoForm()
        photo_form = AutoPhotoForm()

    return render(request, 'cars/add_auto.html', {
        'auto_form': auto_form,
        'photo_form': photo_form
    })

@require_POST
@login_required
def toggle_favorite(request, pk):
    auto = get_object_or_404(Auto, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, auto=auto)
    if not created:
        favorite.delete()
        messages.info(request, 'Автомобиль удалён из избранного.')
    else:
        messages.success(request, 'Автомобиль добавлен в избранное!')
    return redirect(request.META.get('HTTP_REFERER', 'index'))