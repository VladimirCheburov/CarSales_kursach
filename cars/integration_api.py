from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .integration_auth import IntegrationAPIKeyPermission
from .models import Auto, Brand, Favorite, Message, Profile, Region


def _get_profile_by_telegram(telegram_chat_id):
    if not telegram_chat_id:
        return None
    return Profile.objects.filter(telegram_chat_id=telegram_chat_id).select_related('user').first()


def _site_base_url():
    return getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')


def _serialize_auto(auto):
    photo_url = None
    first_photo = auto.auto_photos.select_related('photo').first()
    if first_photo:
        photo_url = first_photo.photo.url

    return {
        'id': auto.id,
        'brand': auto.brand.name,
        'brand_id': auto.brand_id,
        'model': auto.model,
        'year': auto.year,
        'price': int(auto.price),
        'mileage': auto.mileage,
        'region': auto.region.name,
        'region_id': auto.region_id,
        'sell_status': auto.sell_status.name if auto.sell_status else '',
        'description': auto.description[:500],
        'photo_url': photo_url,
        'web_url': f"{_site_base_url()}{auto.get_absolute_url()}",
    }


def _autos_queryset():
    return Auto.objects.available().select_related(
        'brand', 'region', 'sell_status',
    ).prefetch_related('auto_photos__photo')


def _paginate_autos(queryset, page, page_size=8):
    page = max(1, int(page or 1))
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = [_serialize_auto(auto) for auto in queryset.order_by('-created_at')[start:end]]
    return {
        'results': items,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_next': end < total,
        'has_prev': page > 1,
    }


class IntegrationLinkView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def post(self, request):
        token = request.data.get('token', '').strip()
        telegram_chat_id = request.data.get('telegram_chat_id')
        telegram_username = request.data.get('telegram_username', '')

        if not token or telegram_chat_id is None:
            return Response(
                {'detail': 'Укажите token и telegram_chat_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = Profile.objects.filter(telegram_link_token=token).select_related('user').first()
        if not profile:
            return Response({'detail': 'Неверный код привязки.'}, status=status.HTTP_404_NOT_FOUND)

        Profile.objects.filter(telegram_chat_id=telegram_chat_id).exclude(pk=profile.pk).update(
            telegram_chat_id=None,
            telegram_username=None,
        )
        profile.telegram_chat_id = int(telegram_chat_id)
        profile.telegram_username = telegram_username or None
        profile.telegram_link_token = None
        profile.save(update_fields=['telegram_chat_id', 'telegram_username', 'telegram_link_token'])

        return Response({
            'username': profile.user.username,
            'message': 'Telegram успешно привязан к аккаунту.',
        })


class IntegrationLinkStatusView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        profile = _get_profile_by_telegram(request.query_params.get('telegram_chat_id'))
        if not profile or not profile.telegram_chat_id:
            return Response({'linked': False})
        return Response({
            'linked': True,
            'username': profile.user.username,
        })


class IntegrationUnlinkView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def post(self, request):
        profile = _get_profile_by_telegram(request.data.get('telegram_chat_id'))
        if not profile:
            return Response(
                {'detail': 'Telegram не привязан к аккаунту.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile.telegram_chat_id = None
        profile.telegram_username = None
        profile.regenerate_telegram_link_token()
        profile.save(update_fields=[
            'telegram_chat_id', 'telegram_username', 'telegram_link_token',
        ])
        return Response({'message': 'Аккаунт отвязан от Telegram.'})


@method_decorator(login_required, name='dispatch')
class IntegrationLinkTokenView(APIView):
    """Генерация одноразового кода привязки Telegram (для веб-пользователя)."""

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        token = profile.regenerate_telegram_link_token()
        return Response({'token': token, 'expires_note': 'Код одноразовый, действует до привязки.'})


class IntegrationAutoSearchView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        page = request.query_params.get('page', 1)
        autos = _autos_queryset()
        if query:
            autos = autos.filter(
                Q(brand__name__icontains=query)
                | Q(model__icontains=query)
                | Q(description__icontains=query)
            )
        data = _paginate_autos(autos, page)
        data['query'] = query
        return Response(data)


class IntegrationAutoFilterView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        autos = _autos_queryset()
        brand_id = request.query_params.get('brand_id')
        region_id = request.query_params.get('region_id')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        year = request.query_params.get('year')
        page = request.query_params.get('page', 1)

        if brand_id:
            autos = autos.filter(brand_id=brand_id)
        if region_id:
            autos = autos.filter(region_id=region_id)
        if min_price:
            autos = autos.filter(price__gte=min_price)
        if max_price:
            autos = autos.filter(price__lte=max_price)
        if year:
            autos = autos.filter(year=year)

        return Response(_paginate_autos(autos, page))


class IntegrationBrandsView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        brands = Brand.objects.filter(
            auto__sell_status__name__iexact='В продаже',
        ).distinct().order_by('name')
        return Response([{'id': b.id, 'name': b.name} for b in brands])


class IntegrationRegionsView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        regions = Region.objects.filter(
            auto__sell_status__name__iexact='В продаже',
        ).distinct().order_by('name')
        return Response([{'id': r.id, 'name': r.name} for r in regions])


class IntegrationAutoDetailView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request, auto_id):
        auto = get_object_or_404(_autos_queryset(), pk=auto_id)
        return Response(_serialize_auto(auto))


class IntegrationFavoritesView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        profile = _get_profile_by_telegram(request.query_params.get('telegram_chat_id'))
        if not profile:
            return Response({'detail': 'Telegram не привязан к аккаунту.'}, status=status.HTTP_404_NOT_FOUND)

        favorites = Favorite.objects.filter(user=profile.user).select_related(
            'auto__brand', 'auto__region', 'auto__sell_status',
        )[:10]
        return Response([_serialize_auto(fav.auto) for fav in favorites])


class IntegrationInboxView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def get(self, request):
        profile = _get_profile_by_telegram(request.query_params.get('telegram_chat_id'))
        if not profile:
            return Response({'detail': 'Telegram не привязан к аккаунту.'}, status=status.HTTP_404_NOT_FOUND)

        unread = Message.objects.filter(
            receiver=profile.user,
            is_read=False,
        ).select_related('auto', 'sender').order_by('-created_at')[:10]

        data = [{
            'id': msg.id,
            'auto_id': msg.auto_id,
            'auto_title': str(msg.auto),
            'sender': msg.sender.username,
            'message': msg.message[:200],
            'created_at': msg.created_at.isoformat(),
        } for msg in unread]
        return Response({'unread_count': len(data), 'messages': data})


class IntegrationSendMessageView(APIView):
    permission_classes = [IntegrationAPIKeyPermission]

    def post(self, request):
        profile = _get_profile_by_telegram(request.data.get('telegram_chat_id'))
        auto_id = request.data.get('auto_id')
        text = (request.data.get('message') or '').strip()

        if not profile:
            return Response({'detail': 'Telegram не привязан к аккаунту.'}, status=status.HTTP_404_NOT_FOUND)
        if not auto_id or not text:
            return Response({'detail': 'Укажите auto_id и message.'}, status=status.HTTP_400_BAD_REQUEST)

        auto = get_object_or_404(Auto, pk=auto_id)
        if not auto.profile or not auto.profile.user:
            return Response({'detail': 'У объявления нет продавца.'}, status=status.HTTP_400_BAD_REQUEST)
        if auto.profile.user == profile.user:
            return Response({'detail': 'Нельзя писать самому себе.'}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            auto=auto,
            sender=profile.user,
            receiver=auto.profile.user,
            message=text,
        )
        return Response({
            'id': message.id,
            'message': 'Сообщение отправлено продавцу.',
        }, status=status.HTTP_201_CREATED)
