from django import forms
from .models import Sales,FlatPlot,PropertyFlatPlot,PropertySales,InstallmentPayment, SharePlot, SharePerson,ShareInstallmentPayment
from django.forms import inlineformset_factory



class SalesForm(forms.ModelForm):
    class Meta:
        model = Sales
        fields = '__all__'
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'floor_no': forms.TextInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'unit_no': forms.TextInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'unit_count': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'unit_price': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'total_amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'pay_amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'head': forms.Select(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'details': forms.Textarea(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'status': forms.Select(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'create_date': forms.DateInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded', 'type': 'date'}),
        }



# class FlatPlotForm(forms.ModelForm):
#     class Meta:
#         model = FlatPlot
#         fields = '__all__'



class FlatPlotForm(forms.ModelForm):
    class Meta:
        model = FlatPlot
        exclude=['status']
        fields = ['project_name', 'flat_no', 'unit_no', 'type', 'status']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border-slate-200 rounded-md px-2 py-1'}),
            'flat_no': forms.NumberInput(attrs={'class': 'w-full border-slate-200 rounded-md px-2 py-1'}),
            'unit_no': forms.NumberInput(attrs={'class': 'w-full border-slate-200 rounded-md px-2 py-1'}),
            'type': forms.Select(attrs={'class': 'w-full border-slate-200 rounded-md px-2 py-1'}),
            'status': forms.Select(attrs={'class': 'w-full border-slate-200 rounded-md px-2 py-1'}),
        }


class PropertyFlatPlotForm(forms.ModelForm):
    class Meta:
        model = PropertyFlatPlot
        fields = '__all__'



class PropertySalesForm(forms.ModelForm):
    class Meta:
        model = PropertySales
        fields = '__all__'



class InstallmentPaymentForm(forms.ModelForm):
    class Meta:
        model = InstallmentPayment
        fields = '__all__'
        


class ShareInstallmentPaymentForm(forms.ModelForm):
    class Meta:
        model = ShareInstallmentPayment
        fields = '__all__'
        
        
        
class SharePlotForm(forms.ModelForm):
    class Meta:
        model = SharePlot
        fields = ['project_name', 'persion_no', 'decimal', 'area', 'value', 'share_val']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'persion_no': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'decimal': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'area': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'value': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
            'share_val': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 p-2 rounded'}),
        }

class SharePersonForm(forms.ModelForm):
    class Meta:
        model = SharePerson
        fields = ['name']
        exclude = ['pay_status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control border border-gray-300 p-2 rounded w-full'}),
        }

SharePersonFormSet = inlineformset_factory(
    SharePlot, SharePerson, form=SharePersonForm, extra=1, can_delete=True
)
