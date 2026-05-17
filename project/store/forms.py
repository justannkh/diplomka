from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Order


class RegisterForm(UserCreationForm):
    """Форма регистрации пользователя."""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Логин'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Подтверждение пароля'
        })


class LoginForm(AuthenticationForm):
    """Форма входа."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Логин'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Пароль'
        })


class OrderForm(forms.ModelForm):
    """Форма оформления заказа.

    Дополнительно к базовым полям клиент указывает способ оплаты и, при выборе
    онлайн-оплаты, номер тестовой карты. Поле `card_number` вынесено из
    модели, так как реквизиты карты нельзя хранить в БД (требование PCI DSS).
    """

    payment_method = forms.ChoiceField(
        label='Способ оплаты',
        choices=Order.PAYMENT_METHOD_CHOICES,
        initial=Order.PAYMENT_METHOD_COD,
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'}),
    )

    card_number = forms.CharField(
        label='Номер карты (тестовая)',
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '4242 4242 4242 4242',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
        help_text='Для онлайн-оплаты. Тест: 4242 4242 4242 4242.',
    )

    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'phone', 'address', 'comment')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Фамилия'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+996 XXX XXX XXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Адрес доставки',
                'rows': 3
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Комментарий к заказу (необязательно)',
                'rows': 2
            }),
        }

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        card = (cleaned.get('card_number') or '').strip()

        if method == Order.PAYMENT_METHOD_ONLINE:
            digits = ''.join(ch for ch in card if ch.isdigit())
            if not digits:
                self.add_error('card_number',
                               'Для онлайн-оплаты необходимо ввести номер карты.')
            elif not 12 <= len(digits) <= 19:
                self.add_error('card_number',
                               'Номер карты должен содержать 12–19 цифр.')
        return cleaned
