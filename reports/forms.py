from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['kind', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe la novedad...'})}
