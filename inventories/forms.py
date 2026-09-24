from django import forms
from .models import Inventories,InventoryUse

class InventoriesForm(forms.ModelForm):
    class Meta:
        model = Inventories
        exclude = ['purch_file'] 



class InventoryUseForm(forms.ModelForm):
    class Meta:
        model = InventoryUse
        fields = ['project_name', 'item_name', 'qty','total_qty','qtysub_qty', 'details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only items with qtysub > 0
        inventories = Inventories.objects.filter(qtysub__gt=0)
        self.fields['project_name'].queryset = inventories.values_list('project_name', flat=True).distinct()
        self.fields['item_name'].queryset = inventories.values_list('item_name', flat=True).distinct()
