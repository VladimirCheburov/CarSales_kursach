from .forms import ContactForm

def contact_form_processor(request):
    """
    Контекстный процессор для отображения формы на всех страницах.
    """
    form = ContactForm()
    return {'form': form}