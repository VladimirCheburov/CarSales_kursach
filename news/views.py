from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import New
from .serializers import NewSerializer
from django.db.models import Count
from .models import NewCategory
from django.shortcuts import redirect
from django.urls import reverse

def news_list(request):
    news = New.objects.all()
    return render(request, 'news.html', {'news': news})

class FilteredNewsAPIView(APIView):
    """Фильтрация новостей с использованием Q-запросов и APIView."""

    def get(self, request):
        category = request.GET.get('category')  # фильтр по категории
        title_keyword = request.GET.get('title_keyword')  # фильтр по ключевым словам в заголовке
        content_keyword = request.GET.get('content_keyword')  # фильтр по ключевым словам в контенте
        exclude_user = request.GET.get('exclude_user')  # исключить новости, созданные определенным пользователем

        # Создаем фильтры
        filters = Q()
        if category:
            filters &= Q(category__name__iexact=category)
        if title_keyword:
            filters &= Q(title__icontains=title_keyword)
        if content_keyword:
            filters |= Q(content__icontains=content_keyword)  # OR условие для контента
        if exclude_user:
            filters &= ~Q(profile__username=exclude_user)  # NOT условие для исключения пользователя

        # фильтруем новости
        news_items = New.objects.filter(filters)
        if not news_items.exists():
            return Response({"error": "No news match the given filters"}, status=status.HTTP_404_NOT_FOUND)

        # сериализуем и возвращаем данные
        serializer = NewSerializer(news_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

def category_summary(request):
    """
    Представление для отображения количества новостей в каждой категории.
    """
    categories = NewCategory.objects.annotate(news_count=Count('newcategoryassignment'))
    return render(request, 'news/category_summary.html', {'categories': categories})

def redirect_to_auto(request, pk):
    """
    Пример перенаправления на страницу автомобиля.
    """
    url = reverse('auto_detail', kwargs={'pk': pk})
    return redirect(url)

def news_detail(request, pk):
    news = get_object_or_404(New, pk=pk)
    return render(request, 'news/news_detail.html', {'news': news})
