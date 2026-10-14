from django import forms
from .models import Route, Operator


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['operator', 'code', 'name', 'origin', 'destination', 'description', 'color',
                  'duration_minutes', 'distance_km', 'is_active']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class OperatorForm(forms.ModelForm):
    class Meta:
        model = Operator
        fields = ['name', 'brand_color', 'phone', 'website', 'fleet_size', 'is_active']
        widgets = {'brand_color': forms.TextInput(attrs={'type': 'color'})}
