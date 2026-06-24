from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cars.views import (
    AutoListView, AutoViewSet,  AutoFilterAPIView, AutoSearchAPIView, BrandViewSet, ProfileViewSet, index, auto_create, auto_delete, auto_detail
)
from cars.views import autos_list_view
from cars.views import search_autos
from news import views as news_views
from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from cars.views import manage_autos
from cars.views import contact_view
from news.views import category_summary
from cars.views import test_view
from cars.views import favorite_autos
from cars.views import autos_by_region, toggle_favorite
from cars.views import my_autos, reviews_list, conversations_list, conversation_detail, send_message
from cars.integration_api import (
    IntegrationLinkView, IntegrationLinkTokenView, IntegrationAutoSearchView,
    IntegrationAutoFilterView, IntegrationBrandsView, IntegrationRegionsView,
    IntegrationAutoDetailView, IntegrationFavoritesView, IntegrationInboxView,
    IntegrationSendMessageView, IntegrationUnlinkView, IntegrationLinkStatusView,
)
from cars.api import (
    ReviewViewSet, FavoriteViewSet, SellStatusViewSet, RegionViewSet,
    BodyTypeViewSet, EngineTypeViewSet, ColorViewSet
)
router = DefaultRouter()
router.register(r'autos', AutoViewSet, basename='autos')
router.register(r'brands', BrandViewSet, basename='brands')
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'favorites', FavoriteViewSet, basename='favorites')
router.register(r'sellstatuses', SellStatusViewSet, basename='sellstatuses')
router.register(r'regions', RegionViewSet, basename='regions')
router.register(r'bodytypes', BodyTypeViewSet, basename='bodytypes')
router.register(r'enginetypes', EngineTypeViewSet, basename='enginetypes')
router.register(r'colors', ColorViewSet, basename='colors')
from cars.views import index
from cars.views import auto_detail
from cars.views import add_auto, edit_auto, delete_auto, auto_list
urlpatterns = [
    path('', index, name='index'),
    path('autos/', auto_list, name='auto_list'),
    path('autos/add/', add_auto, name='add_auto'),
    path('autos/<int:pk>/edit/', edit_auto, name='edit_auto'),
    path('autos/<int:pk>/delete/', delete_auto, name='delete_auto'),
    path('reviews/', reviews_list, name='reviews_list'),

    # path('', contact_view, name='contact'),
    path('test-template/', test_view, name='test_template'),
    path('auth/', include('social_django.urls', namespace='social')),  # Social Auth
    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('search/', search_autos, name='search_autos'),
    path('auto/<int:pk>/', auto_detail, name='auto_detail'),

    path('', contact_view, name='index'),  # путь для contact_view
    path('test/', test_view, name='test_view'),

    path('api/autos/manage/', manage_autos, name='manage_autos'),
    # админка
    path('admin/', admin.site.urls),

    path('api/autos/', AutoListView.as_view(), name='auto-list'),

    # авторизация с помощью allauth
    path('accounts/', include('allauth.urls')),  # URL-ы для входа/выхода и авторизации
    path('api/autos/filter/', AutoFilterAPIView.as_view(), name='auto-filter'),

    path('api/autos/search/', AutoSearchAPIView.as_view(), name='auto-search'),


    path('api/autos/create/', auto_create, name='auto-create'),
    path('api/autos/<int:pk>/delete/', auto_delete, name='auto-delete'),
    
    path('autos/', autos_list_view, name='autos-list'),

    # Маршруты для приложения news
    path('news/', news_views.news_list, name='news_list'),
    path('api/autos/search/', AutoSearchAPIView.as_view(), name='auto-search'),
    path('api/', include(router.urls)),
    path('news/category-summary/', category_summary, name='category_summary'),
    path('news/', include('news.urls')),
    path('favorite-autos/', favorite_autos, name='favorite_autos'),
    path('autos/region/<int:region_id>/', autos_by_region, name='autos_by_region'),
    path('autos/<int:pk>/toggle_favorite/', toggle_favorite, name='toggle_favorite'),
    path('my-autos/', my_autos, name='my_autos'),
    path('conversations/', conversations_list, name='conversations_list'),
    path('conversations/<int:auto_id>/', conversation_detail, name='conversation_detail'),
    path('autos/<int:auto_id>/send_message/', send_message, name='send_message'),

    # Integration API (Telegram bot ↔ Django)
    path('api/integration/link/', IntegrationLinkView.as_view(), name='integration_link'),
    path('api/integration/unlink/', IntegrationUnlinkView.as_view(), name='integration_unlink'),
    path('api/integration/status/', IntegrationLinkStatusView.as_view(), name='integration_status'),
    path('api/integration/link-token/', IntegrationLinkTokenView.as_view(), name='integration_link_token'),
    path('api/integration/autos/search/', IntegrationAutoSearchView.as_view(), name='integration_auto_search'),
    path('api/integration/autos/filter/', IntegrationAutoFilterView.as_view(), name='integration_auto_filter'),
    path('api/integration/brands/', IntegrationBrandsView.as_view(), name='integration_brands'),
    path('api/integration/regions/', IntegrationRegionsView.as_view(), name='integration_regions'),
    path('api/integration/autos/<int:auto_id>/', IntegrationAutoDetailView.as_view(), name='integration_auto_detail'),
    path('api/integration/favorites/', IntegrationFavoritesView.as_view(), name='integration_favorites'),
    path('api/integration/messages/inbox/', IntegrationInboxView.as_view(), name='integration_inbox'),
    path('api/integration/messages/', IntegrationSendMessageView.as_view(), name='integration_send_message'),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

