from django import forms
from .models import Business, BusinessPromotion


class BusinessRegisterForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'business_type', 'description', 'address', 'latitude', 'longitude',
                  'phone', 'whatsapp', 'website', 'instagram', 'facebook', 'opening_hours', 'cover_image']
        widgets = {'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntale a la gente qué hace especial a tu negocio...'})}


class BusinessEditForm(BusinessRegisterForm):
    """Igual al registro, pero lo usa el dueño para editar su perfil ya creado."""
    pass


class PromotionForm(forms.ModelForm):
    class Meta:
        model = BusinessPromotion
        fields = ['title', 'description', 'discount_text', 'valid_until', 'is_active']
        widgets = {'valid_until': forms.DateInput(attrs={'type': 'date'})}


class BusinessRejectForm(forms.Form):
    reason = forms.CharField(label='Motivo de rechazo', widget=forms.Textarea(attrs={'rows': 3}), required=True)
