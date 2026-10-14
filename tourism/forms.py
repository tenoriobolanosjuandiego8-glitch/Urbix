from django import forms
from .models import TouristPlace


class TouristPlaceForm(forms.ModelForm):
    class Meta:
        model = TouristPlace
        fields = ['name', 'tag', 'history', 'curiosities', 'latitude', 'longitude', 'cover_image', 'is_active']
        widgets = {
            'history': forms.Textarea(attrs={'rows': 4}),
            'curiosities': forms.Textarea(attrs={'rows': 3}),
        }
