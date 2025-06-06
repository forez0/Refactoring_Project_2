"""
Форми аутентифікації користувача для додатку shop.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    """
    Форма реєстрації користувача з додатковими полями та кастомними віджетами.
    """
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Введіть дійсну електронну пошту',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    username = forms.CharField(
        max_length=150,
        help_text=(
            'Обов’язкове. До 150 символів. Латинські літери, цифри та @/./+/-/_'
        ),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ім’я користувача'})
    )
    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
        help_text='Пароль має бути достатньо складним'
    )
    password2 = forms.CharField(
        label="Підтвердження пароля",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Підтвердження пароля'}),
        strip=False,
        help_text='Введіть той самий пароль для підтвердження'
    )

    class Meta:
        """Мета-інформація для SignUpForm."""
        model = User
        fields = ('username', 'email', 'password1', 'password2')
