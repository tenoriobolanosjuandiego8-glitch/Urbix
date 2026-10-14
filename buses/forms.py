from django import forms
from .models import Bus


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['code', 'plate', 'capacity', 'model_year', 'route', 'status', 'is_active']
