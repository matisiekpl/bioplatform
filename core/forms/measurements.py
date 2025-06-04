from django import forms
from django.utils import timezone
from core.models import Measurement


class MeasurementForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['type', 'value', 'timestamp', 'image']
        widgets = {
            'type': forms.Select(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'step': '0.01'
            }),
            'timestamp': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'type': 'datetime-local'
            }),
            'image': forms.FileInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            current_time = timezone.now().strftime('%Y-%m-%dT%H:%M')
            self.fields['timestamp'].initial = current_time

    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get("value")
        type_ = cleaned_data.get("type")
        timestamp = cleaned_data.get("timestamp")
        if value is not None and value <= 0:
            self.add_error("value", "Wartość musi być większa od zera")
        if not type_:
            self.add_error("type", "Typ pomiaru jest wymagany")
        if timestamp and timestamp > timezone.now():
            self.add_error("timestamp", "Data nie może być z przyszłości")
        return cleaned_data


class ImageAnalysisForm(forms.Form):
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'accept': 'image/*',
            'required': True
        })
    ) 