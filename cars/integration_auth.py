from django.conf import settings
from rest_framework.permissions import BasePermission


class IntegrationAPIKeyPermission(BasePermission):
    """Проверка ключа интеграции в заголовке X-Integration-Key."""

    message = 'Неверный или отсутствующий ключ интеграции.'

    def has_permission(self, request, view):
        expected = getattr(settings, 'INTEGRATION_API_KEY', '')
        if not expected:
            return False
        provided = request.headers.get('X-Integration-Key', '')
        return provided == expected
