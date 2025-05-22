from django import forms
from .models import ContactMessage
import re
from datetime import datetime
from cars.models import Auto, AutoPhoto, Photo

class ContactForm(forms.ModelForm):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите ваше сообщение'}),
        label='Сообщение',
        help_text='Введите ваше сообщение.',
        error_messages={
            'required': 'Сообщение обязательно для заполнения.',
            'max_length': 'Сообщение не может превышать 1000 символов.'
        }
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message', 'attachment']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ваш email'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'name': 'Ваше имя',
            'email': 'Ваш email',
            'attachment': 'Прикрепить файл (необязательно)',
        }
        help_texts = {
            'email': 'Введите действующий адрес электронной почты.',
        }
        error_messages = {
            'name': {
                'required': 'Имя обязательно для заполнения.',
                'max_length': 'Имя не может превышать 255 символов.',
            },
            'email': {
                'required': 'Email обязателен для заполнения.',
                'invalid': 'Введите корректный адрес электронной почты.',
            }
        }

    class Media:
        css = {
            'all': ('static/css/contact_form.css',) 
        }

    def clean_name(self):
        """
        Проверяет, что поле name содержит только буквы.
        """
        name = self.cleaned_data.get('name')
        if not re.match(r'^[A-Za-zА-Яа-яЁё\s]+$', name):
            raise forms.ValidationError('Имя должно содержать только буквы.')
        return name

    def save(self, commit=True):
        """
        Сохраняет объект формы. Если commit=False, возвращает несохраненный объект.
        """
        contact_message = super().save(commit=False)

        # дополнительная логика перед сохранением
        if not contact_message.created_at:
            contact_message.created_at = datetime.now()  # устанавливаем время создания вручную

        if commit:
            contact_message.save()  # сохраняем объект в базу данных

        return contact_message

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = [
            'brand', 'description', 'model', 'year', 'mileage', 'price',
            'body_type', 'engine_type', 'color', 'region', 'sell_status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Описание автомобиля'}),
            'model': forms.TextInput(attrs={'placeholder': 'Модель'}),
            'year': forms.NumberInput(attrs={'placeholder': 'Год выпуска'}),
            'mileage': forms.NumberInput(attrs={'placeholder': 'Пробег'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Цена'}),
        }
        labels = {
            'brand': 'Марка',
            'description': 'Описание',
            'model': 'Модель',
            'year': 'Год выпуска',
            'mileage': 'Пробег',
            'price': 'Цена',
            'body_type': 'Тип кузова',
            'engine_type': 'Тип двигателя',
            'color': 'Цвет',
            'region': 'Регион',
            'sell_status': 'Статус продажи',
        }

class AutoPhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['url', 'description']
