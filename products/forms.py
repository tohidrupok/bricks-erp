from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'product_type', 'quantity', 'unit', 'rate', 'amount']
        widgets = {
            'product_name': forms.TextInput(attrs={'placeholder': 'Product Name'}),
            'product_type': forms.TextInput(attrs={'placeholder': 'Product Type'}),
            'quantity': forms.NumberInput(attrs={'step': 1}),
            'unit': forms.TextInput(attrs={'placeholder': 'Unit (e.g., kg, unit)'}),
            'rate': forms.NumberInput(attrs={'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'readonly': 'readonly'}),  # Amount is read-only
        }
