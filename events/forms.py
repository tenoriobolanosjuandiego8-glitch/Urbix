from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'category', 'description', 'place', 'latitude', 'longitude',
                  'start_at', 'end_at', 'cover_image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
