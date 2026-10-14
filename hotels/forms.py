from django import forms
from .models import Hotel


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ['name', 'description', 'address', 'latitude', 'longitude',
                  'approx_price', 'services', 'phone', 'cover_image', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
