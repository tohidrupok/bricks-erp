from django import forms
from django.contrib.auth.models import User
from .models import RestaurantCategory,RestaurantExpenseCategory,RestaurantItem,RestaurantCustomer,RestaurantDamageFood,RestRequisition,RestaurantItemAmount,RestaurantSale,RestHeadofAcct,RestaurantAccount,RestaurantSupplier,RestExpenseRequisition,RestExpense,RestPurchaseCost,RestInventoryUse, RestInventories,RestRequisitionApprovalHistory,RestaurantJewelSupplier
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP


class RestaurantCategoryForm(forms.ModelForm):
    class Meta:
        model = RestaurantCategory
        fields = ['restu_category_name']


class RestaurantExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = RestaurantExpenseCategory
        fields = ['restu_Exp_category_name']
               
        
class RestaurantItemForm(forms.ModelForm):
    class Meta:
        model = RestaurantItem
        fields = ['rest_category', 'rest_item_name', 'rest_item_type', 'rest_item_code']


class RestaurantCustomerForm(forms.ModelForm):
    class Meta:
        model = RestaurantCustomer
        fields = ['rest_customer_name', 'rest_customer_type']  

        widgets = {
            'rest_customer_name': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Enter Customer Name'
            }),
            'rest_customer_type': forms.Select(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'
            }),
        }





class RestaurantItemAmountForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=RestaurantCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'id': 'id_category'})
    )
    item_name = forms.ModelChoiceField(
        queryset=RestaurantItem.objects.none(),
        widget=forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'id': 'id_item_name'})
    )

    class Meta:
        model = RestaurantItemAmount
        exclude = ['item_code']
        widgets = {
            'opening_stock': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'min': 0}),
            'purchase_price': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'step': '0.01', 'min': 0}),
            'selling_price': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'step': '0.01', 'min': 0}),
            'reorder_warning': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'min': 0}),
            'reorder_size': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2', 'min': 1}),
            'unit': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 w-28', 'placeholder': 'e.g. Kg, Ltr, Pcs'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['item_name'].queryset = RestaurantItem.objects.filter(rest_category_id=category_id)
            except (ValueError, TypeError):
                self.fields['item_name'].queryset = RestaurantItem.objects.none()
        elif self.instance.pk:
            self.fields['item_name'].queryset = RestaurantItem.objects.filter(rest_category=self.instance.category)
        else:
            self.fields['item_name'].queryset = RestaurantItem.objects.none()





# class RestaurantSaleForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantSale
#         fields = ['invoice_no', 'customer', 'sale_date','discount','total_amount','note']
#         exclude=['final_amount']
#         widgets = {
#             'invoice_no': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Invoice No'
#             }),
#             'customer': forms.Select(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500'
#             }),            
#         }



# class RestaurantSaleForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantSale
#         fields = ['invoice_no', 'customer', 'sale_date', 'discount', 'total_amount', 'note']
#         exclude=['final_amount']
#         widgets = {
#             'invoice_no': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Invoice No'
#             }),
#             'customer': forms.Select(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500'
#             }),
#             'sale_date': forms.DateInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'type': 'date'
#             }),
#             'discount': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Discount'
#             }),
#             'total_amount': forms.NumberInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'readonly': True,  # Optional: make total_amount read-only
#             }),
#             'final_amount': forms.NumberInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'readonly': True,  # Optional: calculated automatically
#             }),
#             'note': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Note'
#             }),
#         }
        
        


# from django import forms
# from .models import RestaurantSale

# class RestaurantSaleForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantSale
#         fields = [
#             'invoice_no', 
#             'customer', 
#             'sale_date', 
#             'discount', 
#             'total_amount', 
#             'paid_amount', 
#             'return_amount', 
#             'note'
#         ]
#         exclude = ['final_amount']
#         widgets = {
#             'invoice_no': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Invoice No',
#                 'readonly': True
#             }),
#             'customer': forms.Select(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500'
#             }),
#             'sale_date': forms.DateInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'type': 'date'
#             }),
#             'discount': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Discount'
#             }),
#             'total_amount': forms.NumberInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'readonly': True,
#             }),
#             'paid_amount': forms.NumberInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Paid Amount',
#                 'step': '0.01'
#             }),
#             'return_amount': forms.NumberInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Return Amount',
#                 'readonly': True,
#             }),
#             'note': forms.TextInput(attrs={
#                 'class': 'w-full border rounded px-3 py-2 focus:outline-yellow-500',
#                 'placeholder': 'Enter Note'
#             }),
#         }
        
from django import forms
from .models import RestaurantSale


class RestaurantSaleForm(forms.ModelForm):
    class Meta:
        model = RestaurantSale
        fields = [
            'invoice_no',
            'customer',
            'sale_date',
            'total_amount',
            'discount',
            'final_amount',
            'received_amount',
            'return_amount',
        ]
        widgets = {
            'invoice_no': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.TextInput(attrs={'class': 'form-control'}),
            'sale_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'total_amount': forms.NumberInput(
                attrs={'class': 'form-control', 'id': 'id_total_amount'}
            ),
            'discount': forms.NumberInput(
                attrs={'class': 'form-control', 'id': 'id_discount'}
            ),
            'final_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'id': 'id_final_amount',
                    'readonly': 'readonly',
                }
            ),
            'received_amount': forms.NumberInput(
                attrs={'class': 'form-control', 'id': 'id_received_amount'}
            ),
            'return_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'id': 'id_return_amount',
                    'readonly': 'readonly',
                }
            ),
        }
        
class RestHeadofAcctForm(forms.ModelForm):
    class Meta:
        model = RestHeadofAcct
        fields = ['restu_headofacct_name']


class RestaurantAccountForm(forms.ModelForm):
    class Meta:
        model = RestaurantAccount
        fields = ['rest_head_name', 'rest_acct_name', 'rest_acct_code']




# class RestaurantSupplierForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantSupplier
#         fields = ['rest_supplier_name']  

#         widgets = {
#             'rest_supplier_name': forms.TextInput(attrs={
#                 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
#                 'placeholder': 'Enter Supplier Name'
#             }),            
#         }




class RestaurantSupplierForm(forms.ModelForm):
    class Meta:
        model = RestaurantSupplier
        fields = [
            'rest_supplier_code',
            'rest_supplier_name',
            'contact_person',
            'address',
            'phone_mobile',
            'purchase_commission',
            'opening_balance'
        ]

        widgets = {

            'rest_supplier_code': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2 bg-gray-100',
                'readonly': 'readonly'
            }),

            'rest_supplier_name': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Account Name'
            }),

            'contact_person': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Contact Person'
            }),

            'address': forms.Textarea(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'rows': 2,
                'placeholder': 'Address'
            }),

            'phone_mobile': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Phone / Mobile'
            }),

            'purchase_commission': forms.NumberInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Purchase Commission %'
            }),

            'opening_balance': forms.NumberInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Opening Balance'
            }),
        }
        


class RestaurantJewelSupplierForm(forms.ModelForm):
    class Meta:
        model = RestaurantJewelSupplier
        fields = [
            'rest_supplier_code',
            'rest_supplier_name',
            'contact_person',
            'address',
            'phone_mobile',
            'purchase_commission',
            'opening_balance'
        ]

        widgets = {

            'rest_supplier_code': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2 bg-gray-100',
                'readonly': 'readonly'
            }),

            'rest_supplier_name': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Account Name'
            }),

            'contact_person': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Contact Person'
            }),

            'address': forms.Textarea(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'rows': 2,
                'placeholder': 'Address'
            }),

            'phone_mobile': forms.TextInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Phone / Mobile'
            }),

            'purchase_commission': forms.NumberInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Purchase Commission %'
            }),

            'opening_balance': forms.NumberInput(attrs={
                'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2',
                'placeholder': 'Opening Balance'
            }),
        }

        
        
class RestExpenseForm(forms.ModelForm):
    class Meta:
        model = RestExpense
        fields = ['expense_name', 'expense_code']
        
        
        
class RestPurchaseCostForm(forms.ModelForm):
    class Meta:
        model = RestPurchaseCost
        fields = ['pur_cost_name', 'pur_cost_code']
        
        
        
class RestExpenseRequisitionForm(forms.ModelForm):
    class Meta:
        model = RestExpenseRequisition
        # Either use fields to list all editable fields
        fields = [
            'project_name', 'type','cash_type','cheque_number','mr_or_bill_no','head_of_account','item_name', 'qty', 'rate', 'amount', 
            'descript', 'remark', 'approv_status'
        ]
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'item_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'qty': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'rate': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'descript': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
            'remark': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded p-2', 'rows': 3}),
            'approv_status': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
        }
        
        


from .models import RestaurantKitchenLedger


class RestaurantKitchenLedgerForm(forms.ModelForm):
    class Meta:
        model = RestaurantKitchenLedger
        fields = ['project', 'employee', 'debit', 'credit']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control-input'}),
            'employee': forms.Select(attrs={'class': 'form-control-input'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control-input', 'step': '0.01'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control-input', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit') or 0
        credit = cleaned_data.get('credit') or 0
        if debit < 0 or credit < 0:
            raise forms.ValidationError("Debit and credit amounts cannot be negative.")
        return cleaned_data


class LedgerPaymentForm(forms.Form):
    ledger_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_ledger_id(self):
        ledger_id = self.cleaned_data['ledger_id']
        try:
            ledger = RestaurantKitchenLedger.objects.get(id=ledger_id)
        except RestaurantKitchenLedger.DoesNotExist:
            raise forms.ValidationError("Ledger entry not found.")
        if ledger.balance <= 0:
            raise forms.ValidationError("This ledger entry has no outstanding balance.")
        return ledger_id


class RestRequisitionItemForm(forms.ModelForm):
    """Optional: for validating a single item row server-side if you want it."""
    class Meta:
        model = RestRequisition
        fields = ['qty', 'rate', 'discount', 'calc_mode', 'remark']
        widgets = {
            'qty': forms.NumberInput(attrs={'class': 'form-control-input qty-field', 'step': '0.01'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control-input rate-field', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control-input discount-field', 'step': '0.01'}),
            'remark': forms.TextInput(attrs={'class': 'form-control-input'}),
        }

# class RestRequisitionForm(forms.ModelForm):

#     vendor_name = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={'class': 'form-input'})
#     )

#     discount = forms.DecimalField(
#         required=False,
#         min_value=0,
#         decimal_places=2,
#         max_digits=20,
#         widget=forms.NumberInput(attrs={
#             'class': 'form-input',
#             'step': '0.01'
#         })
#     )

#     amount = forms.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#         required=False,
#         widget=forms.NumberInput(attrs={
#             'readonly': 'readonly',
#             'class': 'form-input'
#         })
#     )

#     class Meta:
#         model = RestRequisition
#         exclude = [
#             'approv_status', 'approv_note',
#             'approv_acct_status', 'approv_acct_note',
#             'approv_store', 'approv_store',
#             'approv_purch_status', 'approv_purch_note',
#             'return_requisition', 'requi_uniq_id',
#             'purch_appov', 'purch_date', 'purch_id',
#             'return_qty', 'return_status', 'cash_empl'
#         ]

#     def clean(self):
#         cleaned_data = super().clean()

#         qty = cleaned_data.get("qty")
#         rate = cleaned_data.get("rate")
#         discount = cleaned_data.get("discount") or 0

#         if qty is None or rate is None:
#             raise forms.ValidationError("Quantity and Rate cannot be empty.")

#         try:
#             qty = Decimal(qty)
#             rate = Decimal(rate)
#             discount = Decimal(discount)
#         except:
#             raise forms.ValidationError("Invalid numeric values.")

#         if qty <= 0 or rate <= 0:
#             raise forms.ValidationError("Quantity and Rate must be greater than 0.")

#         # ✅ SAFE CALCULATION (NO SAVE OVERWRITE ISSUE)
#         cleaned_data["amount"] = (qty * rate - discount).quantize(Decimal("0.01"))

#         return cleaned_data


from django import forms
from decimal import Decimal
from .models import RestRequisition

class RestRequisitionForm(forms.ModelForm):
    vendor_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    discount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=20,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-input'})
    )

    class Meta:
        model = RestRequisition
        exclude = [
            'approv_status', 'approv_note',
            'approv_acct_status', 'approv_acct_note',
            'approv_store', 'approv_purch_status', 'approv_purch_note',
            'return_requisition', 'requi_uniq_id',
            'purch_appov', 'purch_date', 'purch_id',
            'return_qty', 'return_status', 'cash_empl'
        ]

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")
        discount = cleaned_data.get("discount") or 0
        calc_mode = cleaned_data.get("calc_mode") or "unit"

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")

        try:
            qty = Decimal(qty)
            rate = Decimal(rate)
            discount = Decimal(discount)
        except (ValueError, TypeError):
            raise forms.ValidationError("Invalid numeric values.")

        if qty <= 0 or rate <= 0:
            raise forms.ValidationError("Quantity and Rate must be greater than 0.")

        if calc_mode == "whole":
            cleaned_data["amount"] = (rate - discount).quantize(Decimal("0.01"))
        else:
            cleaned_data["amount"] = (qty * rate - discount).quantize(Decimal("0.01"))

        return cleaned_data
        
        



class RestRequisitionApprovalHistoryForm(forms.ModelForm):

    class Meta:
        model = RestRequisitionApprovalHistory

        fields = [
            'requi_uniq_id',
            'pur_verify',
            'purch_appov',
            'project_name',
            'employee_name',
            'cash_empl',
            'total_amount',
            'approv_acct_status',
            'approv_acct_note',
        ]

        widgets = {

            'requi_uniq_id': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'purch_appov': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'cash_empl': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'total_amount': forms.NumberInput(
                attrs={'class': 'form-control'}
            ),

            'approv_acct_note': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }
        


      

class PublicRestRequisitionForm(forms.ModelForm):

    class Meta:
        model = RestRequisition

        exclude = [
            'approv_status',
            'approv_note',
            'approv_acct_status',
            'approv_acct_note',
            'approv_purch_status',
            'approv_purch_note',
            'return_requisition',
            'requi_uniq_id',
            'purch_appov',
            'purch_date',
            'purch_id',
            'return_qty',
            'return_status',
            'cash_empl'
        ]

    def clean(self):
        cleaned_data = super().clean()

        qty = cleaned_data.get('qty')

        if not qty:
            raise forms.ValidationError(
                "Quantity is required."
            )

        cleaned_data['rate'] = Decimal('1.00')

        cleaned_data['amount'] = (
            Decimal(qty) * Decimal('1.00')
        )

        return cleaned_data
        
        

# class RestInventoriesForm(forms.ModelForm):
#     class Meta:
#         model = RestInventories
#         exclude = ['purch_file'] 



# class RestInventoryUseForm(forms.ModelForm):
#     class Meta:
#         model = RestInventoryUse 
#         fields = ['project_name', 'item_name', 'qty','total_qty','qtysub_qty', 'details']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Filter to show only items with qtysub > 0
#         inventories = RestInventories.objects.filter(qtysub__gt=0)
#         self.fields['project_name'].queryset = inventories.values_list('project_name', flat=True).distinct()
#         self.fields['item_name'].queryset = inventories.values_list('item_name', flat=True).distinct()


from django import forms
from django.core.exceptions import ValidationError
from .models import RestInventories, RestInventoryUse

class RestInventoriesForm(forms.ModelForm):
    class Meta:
        model = RestInventories
        exclude = ['purch_file_1', 'purch_file_2', 'purch_file_3'] 


class RestInventoryUseForm(forms.ModelForm):
    class Meta:
        model = RestInventoryUse 
        fields = ['project_name', 'item_name', 'qty', 'total_qty', 'qtysub_qty', 'details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Find active inventory item distributions where qty > 0
        active_inventories = RestInventories.objects.filter(qty__gt=0)
        
        # Isolate distinct relational ID fields 
        active_project_ids = active_inventories.values_list('project_name_id', flat=True).distinct()
        active_item_ids = active_inventories.values_list('item_name_id', flat=True).distinct()
        
        # Populate operational dropdown structures cleanly using matching database records
        if 'project_name' in self.fields:
            self.fields['project_name'].queryset = ProjectFirstLevelName.objects.filter(id__in=active_project_ids)
        if 'item_name' in self.fields:
            self.fields['item_name'].queryset = RestaurantItem.objects.filter(id__in=active_item_ids)
            
            

# from .models import RestaurantPublicExpense

# class RestaurantPublicExpenseForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantPublicExpense
#         fields = [
#             'project_name', 
#             'restu_cate_name', 
#             'restu_expense_name', 
#             'restu_expense_amount'
#         ]
#         labels = {
#             'project_name': 'Project Name',
#             'restu_cate_name': 'Expense Category',
#             'restu_expense_name': 'Expense Description/Name',
#             'restu_expense_amount': 'Amount',
#         }
#         widgets = {
#             'project_name': forms.Select(attrs={'class': 'form-control'}),
#             'restu_cate_name': forms.Select(attrs={'class': 'form-control'}),
#             'restu_expense_name': forms.TextInput(attrs={
#                 'class': 'form-control', 
#                 'placeholder': 'e.g., Rice bag purchase'
#             }),
#             'restu_expense_amount': forms.NumberInput(attrs={
#                 'class': 'form-control', 
#                 'placeholder': '0.00',
#                 'step': '0.01'
#             }),
#         }



from django import forms
from .models import RestaurantPublicExpense


from django import forms
from projects.models import ProjectFirstLevelName
from .models import RestaurantPublicExpense


class RestaurantPublicExpenseForm(forms.ModelForm):

    class Meta:
        model = RestaurantPublicExpense
        fields = [
            'project_name',
            'restu_cate_name',
            'restu_expense_type',
            'restu_expense_name',
            'restu_expense_amount',
        ]

        widgets = {
            'project_name': forms.Select(attrs={'class': 'form-control'}),
            'restu_cate_name': forms.Select(attrs={'class': 'form-control'}),
            'restu_expense_type': forms.Select(attrs={'class': 'form-control'}),
            'restu_expense_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expense Description'
            }),
            'restu_expense_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['project_name'].queryset = (
            ProjectFirstLevelName.objects.filter(
                project_first_name__in=[
                    "The Galleria Restauent Cafe",
                    "The Galleria Live Kitchen"
                ]
            )
        )
        


class RestaurantDamageFoodForm(forms.ModelForm):
    class Meta:
        model = RestaurantDamageFood
        fields = ['item', 'quantity', 'damage_date', 'reason']
        widgets = {
            'item': forms.Select(attrs={'class': 'w-full border p-1 bg-white'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full border p-1', 'min': 1}),
            'damage_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border p-1 bg-white'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border p-1', 'placeholder': 'Enter reason for damage/wastage...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sort items alphabetically by name in the dropdown
        self.fields['item'].queryset = RestaurantItem.objects.all().order_by('rest_item_name')
        
        

from .models import ApprovalRange, RestaurantBudget

class ApprovalRangeForm(forms.ModelForm):
    class Meta:
        model = ApprovalRange
        fields = ['user', 'min_amount', 'max_amount']
        widgets = {
            'user': forms.Select(attrs={'class': 'w-full border p-2 rounded bg-white'}),
            'min_amount': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
        }

class RestaurantBudgetForm(forms.ModelForm):
    class Meta:
        model = RestaurantBudget
        fields = ['category', 'budget_type', 'amount', 'fiscal_year']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full border p-2 rounded bg-white'}),
            'budget_type': forms.Select(attrs={'class': 'w-full border p-2 rounded bg-white'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
            'fiscal_year': forms.TextInput(attrs={'class': 'w-full border p-2 rounded', 'placeholder': '2026-2027'}),
        }