from .forms import ContactForm
from .models import Profile


def contact_form_processor(request):
    """
    Контекстный процессор для отображения формы на всех страницах.
    """
    form = ContactForm()
    return {'form': form}


def telegram_link_processor(request):
    """Код привязки Telegram для авторизованных пользователей."""
    if not request.user.is_authenticated:
        return {}
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.telegram_link_token:
        profile.regenerate_telegram_link_token()
    return {
        'telegram_link_token': profile.telegram_link_token,
        'telegram_is_linked': profile.telegram_chat_id is not None,
    }