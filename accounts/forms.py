"""
accounts/forms.py
Formularios de registro, inicio de sesión (por correo) y edición de perfil.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(UserCreationForm):
    name = forms.CharField(
        label='Nombre completo', max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com'})
    )
    terms = forms.BooleanField(label='Acepto los términos y condiciones', required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['placeholder'] = 'Mínimo 8 caracteres'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repite tu contraseña'

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe una cuenta registrada con ese correo.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data['name'].strip()
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
        user.email = self.cleaned_data['email']
        # username interno único derivado del correo (el login real es por email)
        user.username = self.cleaned_data['email'].split('@')[0][:140] + '_' + User.objects.count().__str__()
        user.role = User.Role.USUARIO
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))
    remember = forms.BooleanField(label='Recordar sesión', required=False, initial=True)


class RecoverPasswordForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'city', 'avatar']
        labels = {
            'first_name': 'Nombre', 'last_name': 'Apellido',
            'phone': 'Teléfono', 'city': 'Ciudad', 'avatar': 'Foto de perfil',
        }
