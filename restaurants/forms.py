from django import forms
from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'tag', 'description', 'address', 'latitude', 'longitude',
                  'price_range', 'phone', 'opening_hours', 'cover_image', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
