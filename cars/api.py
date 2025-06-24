from rest_framework import viewsets
from .models import Review, Favorite, SellStatus, Region, BodyType, EngineType, Color
from .serializers import ReviewSerializer, FavoriteSerializer, SellStatusSerializer, RegionSerializer, BodyTypeSerializer, EngineTypeSerializer, ColorSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

class SellStatusViewSet(viewsets.ModelViewSet):
    queryset = SellStatus.objects.all()
    serializer_class = SellStatusSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

class BodyTypeViewSet(viewsets.ModelViewSet):
    queryset = BodyType.objects.all()
    serializer_class = BodyTypeSerializer

class EngineTypeViewSet(viewsets.ModelViewSet):
    queryset = EngineType.objects.all()
    serializer_class = EngineTypeSerializer

class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer 