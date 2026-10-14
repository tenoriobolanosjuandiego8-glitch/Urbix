"""
accounts/views.py
Registro, inicio/cierre de sesión (por correo), recuperación y cambio
de contraseña, verificación de correo y edición de perfil.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import RegisterForm, EmailLoginForm, RecoverPasswordForm, ProfileForm
from .models import ActivityLog, LoginAttempt

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            login(request, user, backend='accounts.backends.EmailBackend')
            messages.success(request, '¡Cuenta creada correctamente! Revisa tu correo para verificarla.')
            return redirect('dashboard:redirect')
        messages.error(request, 'Revisa los datos del formulario e inténtalo de nuevo.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/registro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

            if LoginAttempt.is_locked_out(email):
                messages.error(
                    request,
                    f'Demasiados intentos fallidos. Por seguridad, espera '
                    f'{LoginAttempt.LOCKOUT_WINDOW_MINUTES} minutos antes de volver a intentar, '
                    f'o recupera tu contraseña.',
                )
                return render(request, 'accounts/login.html', {'form': form})

            user = authenticate(request, username=email, email=email, password=password)
            if user is not None:
                LoginAttempt.record(email, client_ip, success=True)
                login(request, user, backend='accounts.backends.EmailBackend')
                if not form.cleaned_data.get('remember'):
                    request.session.set_expiry(0)  # expira al cerrar el navegador
                messages.success(request, f'¡Bienvenido de nuevo, {user.first_name or user.username}!')
                return redirect('dashboard:redirect')
            LoginAttempt.record(email, client_ip, success=False)
            messages.error(request, 'Correo o contraseña incorrectos.')
        else:
            messages.error(request, 'Completa correo y contraseña correctamente.')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('accounts:login')


def recover_password_view(request):
    if request.method == 'POST':
        form = RecoverPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            if user:
                _send_reset_email(request, user)
            # Por seguridad, siempre mostramos el mismo mensaje exista o no la cuenta
            return render(request, 'accounts/recuperar.html', {'form': form, 'sent': True})
    else:
        form = RecoverPasswordForm()
    return render(request, 'accounts/recuperar.html', {'form': form, 'sent': False})


def reset_password_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    valid = user is not None and default_token_generator.check_token(user, token)

    if valid and request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password1 == password2 and len(password1) >= 8:
            user.set_password(password1)
            user.save()
            messages.success(request, 'Contraseña actualizada. Ya puedes iniciar sesión.')
            return redirect('accounts:login')
        messages.error(request, 'Las contraseñas no coinciden o son muy cortas (mínimo 8 caracteres).')

    return render(request, 'accounts/reset_password_confirm.html', {'valid': valid})


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        messages.success(request, 'Tu correo fue verificado correctamente.')
    else:
        messages.error(request, 'El enlace de verificación no es válido o ya expiró.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    from interactions.models import Favorite
    from interactions.gamification import get_gamification_stats
    favorites = Favorite.objects.filter(user=request.user).select_related('content_type')[:12]
    gamification = get_gamification_stats(request.user)
    return render(request, 'accounts/perfil.html', {
        'form': form, 'favorites': favorites, 'gamification': gamification,
    })


@login_required
def change_password_view(request):
    if request.method == 'POST':
        current = request.POST.get('current_password')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if not request.user.check_password(current):
            messages.error(request, 'Tu contraseña actual no es correcta.')
        elif password1 != password2 or len(password1 or '') < 8:
            messages.error(request, 'Las contraseñas nuevas no coinciden o son muy cortas.')
        else:
            request.user.set_password(password1)
            request.user.save()
            messages.success(request, 'Contraseña actualizada. Vuelve a iniciar sesión.')
            return redirect('accounts:login')
    return redirect('accounts:profile')


@login_required
def emergency_contacts_view(request):
    from .models import EmergencyContact
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        relationship = request.POST.get('relationship', '').strip()
        if name and phone:
            EmergencyContact.objects.create(user=request.user, name=name, phone=phone, relationship=relationship)
            messages.success(request, 'Contacto de emergencia agregado.')
        return redirect('accounts:emergency_contacts')
    contacts = request.user.emergency_contacts.all()
    return render(request, 'accounts/contactos_emergencia.html', {'contacts': contacts})


@login_required
def emergency_contact_delete(request, pk):
    from .models import EmergencyContact
    contact = get_object_or_404(EmergencyContact, pk=pk, user=request.user)
    if request.method == 'POST':
        contact.delete()
        messages.info(request, 'Contacto eliminado.')
    return redirect('accounts:emergency_contacts')


@login_required
def sos_view(request):
    """
    Botón SOS: muestra los contactos de emergencia del usuario con un
    mensaje y ubicación prellenados, listos para enviar por WhatsApp/SMS
    (usamos enlaces wa.me — no requiere ninguna cuenta ni API de pago).
    """
    contacts = request.user.emergency_contacts.all()
    return render(request, 'accounts/sos.html', {'contacts': contacts})


# Helpers de correo
def _send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = request.build_absolute_uri(reverse('accounts:verify_email', args=[uid, token]))
    send_mail(
        'Verifica tu correo en URBIX',
        f'Hola {user.first_name}, confirma tu correo aquí: {link}',
        None, [user.email], fail_silently=True,
    )


def _send_reset_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = request.build_absolute_uri(reverse('accounts:reset_password_confirm', args=[uid, token]))
    send_mail(
        'Recupera tu contraseña de URBIX',
        f'Hola {user.first_name}, restablece tu contraseña aquí: {link}',
        None, [user.email], fail_silently=True,
    )
