from django import forms
from .models import CashRestType,SalesRestType, DailyPayment,RestHeadOfAccount,CreditRestVoucher,Customer,CustomerLead,CapitalRestAccount,Collection,DebitRestVoucher,RestLoanVoucher,RestTransactionHistory,LedgerRestEntry,RestBalanceTransfer,RestMainChequeBook,RestMainCheque
from decimal import Decimal
from projects.models import ProjectFirstLevelName,SiteSupervisor,Suppliers
from purchase.models import HeadOfExpense
from restahrm.models import RestaurantEmployee
from restaurant.models import RestaurantSupplier,RestExpense,RestPurchaseCost

class CashRestTypeForm(forms.ModelForm):
    class Meta:
        model = CashRestType
        exclude = ['type_amount', 'type_note']
        fields = ['cash_type_name','account_number','type_amount','type_note']
        
class SalesRestTypeForm(forms.ModelForm):
    class Meta:
        model = SalesRestType
        exclude = ['type_amount', 'type_note']
        fields = ['sales_type_name','account_number','type_amount','type_note']
        
        
class RestHeadOfAccountForm(forms.ModelForm):
    class Meta:
        model = RestHeadOfAccount
        fields = ['head_name', 'head_code']
   
   


class RestMainChequeBookForm(forms.ModelForm):
    class Meta:
        model = RestMainChequeBook
        fields = ['account', 'book_name', 'book_number', 'start_number', 'end_number', 'issue_date', 'is_active']
        widgets = {
            'issue_date': forms.DateInput(
                attrs={
                    'type': 'date',  # this shows the calendar
                    'class': 'btp-input-date'
                }
            )
        }


class RestMainChequeForm(forms.ModelForm):
    class Meta:
        model = RestMainCheque
        fields = ['cheque_book', 'cheque_number', 'issue_date', 'payee_name', 'amount', 'status', 'remarks']


     

class CreditRestVoucherForm(forms.ModelForm):
    customer_name = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
    )

    lead_name = forms.ModelChoiceField(
        queryset=CustomerLead.objects.none(),  # Initially empty
        required=False,
    )

    class Meta:
        model = CreditRestVoucher
        fields = [
            'project_name',
            'type',
            'contructor',
            'vendor',
            'customer_name',
            'lead_name',
            'capi_name',
            'invest_name',
            'reve_name',
            'empl_name',
            'others',
            'cash_type',
            'cheque_number',
            'bill_date',
            'head_of_account',
            'mr_or_bill_no',
            'date',
            'amount',
            'particulars',
            'is_confirmed',
            'carrier',
            'reqs_id',
            'res_status',
            'create_cr',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'particulars': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['project_name'].queryset = ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        )
        
        self.fields['lead_name'].queryset = CustomerLead.objects.filter(status='open')
        self.fields['capi_name'].queryset = CapitalRestAccount.objects.filter(status='active')

   
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
        
        
        
        
class CapitalRestAccountForm(forms.ModelForm):
    class Meta:
        model = CapitalRestAccount
        fields = '__all__'
        widgets = {
            'head_of_account': forms.Select(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
            'person_name': forms.TextInput(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
            'address': forms.Textarea(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md', 'rows': 3}),
            'contact_number': forms.TextInput(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
            'status': forms.Select(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
            'note': forms.Textarea(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full border border-slate-300 p-2 rounded-md'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter using the correct field name: 'head_name'
        self.fields['head_of_account'].queryset = RestHeadOfAccount.objects.filter(
            head_name__in=['Capital Account', 'Investment Account', 'Revenue Account']
        )
        
        


# class DebitRestVoucherForm(forms.ModelForm):
#     class Meta:
#         model = DebitRestVoucher
#         fields = [
#             'type',
#             'contructor',
#             'vendor',
#             'expense',
#             'purchase',
#             'empl_name',
#             'capi_name',
#             'reve_name',
#             'invest_name',
#             'customer_name',
#             'bill_phase',
#             'bill_date',
#             'project_name',
#             'cash_type',
#             'cheque_number',
#             'head_of_account',
#             'amount',
#             'mr_or_bill_no',
#             'date',
#             'particulars',
#             'is_confirmed',
#             'advance_pay',
#             'requi_id',
#             'return_requisition',
#             'carrier',
#             'create_dr',
#         ]
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#             'amount': forms.NumberInput(attrs={'step': '0.01'}),
#             'particulars': forms.Textarea(attrs={'rows': 4}),
#         }

#     def clean_amount(self):
#         amount = self.cleaned_data.get('amount')
#         if amount <= 0:
#             raise forms.ValidationError("Amount must be greater than zero.")
#         return amount

#     # ✅ Correct mappings
#     contructor = forms.ModelChoiceField(
#         queryset=SiteSupervisor.objects.all(),
#         required=False,
#     )
#     vendor = forms.ModelChoiceField(
#         queryset=RestaurantSupplier.objects.all(),
#         required=False,
#     )
#     expense = forms.ModelChoiceField(
#         queryset=RestExpense.objects.all(),
#         required=False,
#     )
#     purchase = forms.ModelChoiceField(
#         queryset=RestPurchaseCost.objects.all(),
#         required=False,
#     )
#     empl_name = forms.ModelChoiceField(
#         queryset=RestaurantEmployee.objects.all(),
#         required=False,
#     )
#     capi_name = forms.ModelChoiceField(   # ✅ FIXED
#         queryset=CapitalRestAccount.objects.all(),
#         required=False,
#     )
#     reve_name = forms.ModelChoiceField(   # ✅ FIXED
#         queryset=CapitalRestAccount.objects.all(),
#         required=False,
#     )
#     invest_name = forms.ModelChoiceField(  # ✅ FIXED
#         queryset=CapitalRestAccount.objects.all(),
#         required=False,
#     )
#     customer_name = forms.ModelChoiceField(  # ✅ FIXED
#         queryset=Customer.objects.all(),
#         required=False,
#     )
    
    


class DebitRestVoucherForm(forms.ModelForm):
    class Meta:
        model = DebitRestVoucher
        fields = [
            'type',
            'contructor',
            'vendor',
            'expense',
            'purchase',
            'empl_name',
            'capi_name',
            'reve_name',
            'invest_name',
            'customer_name',
            'bill_phase',
            'bill_date',
            'project_name',
            'cash_type',
            'cheque_number',
            'head_of_account',
            'amount',
            'mr_or_bill_no',
            'date',
            'particulars',
            'is_confirmed',
            'advance_pay',
            'requi_id',
            'return_requisition',
            'carrier',
            'create_dr',
        ]

    # ✅ ADD THIS FILTER
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['project_name'].queryset = ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        )

    widgets = {
        'date': forms.DateInput(attrs={'type': 'date'}),
        'amount': forms.NumberInput(attrs={'step': '0.01'}),
        'particulars': forms.Textarea(attrs={'rows': 4}),
    }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
        
    
        # ✅ Correct mappings
    contructor = forms.ModelChoiceField(
        queryset=SiteSupervisor.objects.all(),
        required=False,
    )
    vendor = forms.ModelChoiceField(
        queryset=RestaurantSupplier.objects.all(),
        required=False,
    )
    expense = forms.ModelChoiceField(
        queryset=RestExpense.objects.all(),
        required=False,
    )
    purchase = forms.ModelChoiceField(
        queryset=RestPurchaseCost.objects.all(),
        required=False,
    )
    empl_name = forms.ModelChoiceField(
        queryset=RestaurantEmployee.objects.all(),
        required=False,
    )
    capi_name = forms.ModelChoiceField(   # ✅ FIXED
        queryset=CapitalRestAccount.objects.all(),
        required=False,
    )
    reve_name = forms.ModelChoiceField(   # ✅ FIXED
        queryset=CapitalRestAccount.objects.all(),
        required=False,
    )
    invest_name = forms.ModelChoiceField(  # ✅ FIXED
        queryset=CapitalRestAccount.objects.all(),
        required=False,
    )
    customer_name = forms.ModelChoiceField(  # ✅ FIXED
        queryset=Customer.objects.all(),
        required=False,
    )
    
    



class LedgerRestEntryForm(forms.ModelForm):
    class Meta:
        model = LedgerRestEntry
        exclude=['tbl_id','tbl_name']
        fields = ['project_name', 'type','contructor','vendor','customer_name','bankName', 'capi_name', 'reve_name','exp_name','purchase','empl_name', 'invest_name', 'balance_trf','type_name', 'head', 'mr_or_bill_no','cash_type', 'cheque_number','date', 'description', 'debit', 'credit', 'carrier', 'entry_date','loan_status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'Hand Cash' from bankName dropdown
        self.fields['bankName'].queryset = CashRestType.objects.exclude(cash_type_name__iexact="Cash in Hand")


    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    contructor = forms.ModelChoiceField(
        queryset=SiteSupervisor.objects.all(),
        required=False,  
    )
    vendor = forms.ModelChoiceField(
        queryset=Suppliers.objects.all(),
        required=False, 
    )
    customer_name = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False, 
    )
    bankName = forms.ModelChoiceField(
        queryset=CashRestType.objects.all(),
        required=False, 
    )
    capi_name = forms.ModelChoiceField(
        queryset=CapitalRestAccount.objects.all(),
        required=False, 
    )
    reve_name = forms.ModelChoiceField(
        queryset=CapitalRestAccount.objects.all(),
        required=False, 
    )
    exp_name = forms.ModelChoiceField(
        queryset=RestExpense.objects.all(),
        required=False, 
    )
    purchase = forms.ModelChoiceField(
        queryset=RestPurchaseCost.objects.all(),
        required=False, 
    )
    invest_name = forms.ModelChoiceField(
        queryset=CapitalRestAccount.objects.all(),
        required=False, 
    )


class LedgerRestFilterForm(forms.Form):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Bank', 'Bank'),
        ('Expense', 'Expense'),
        ('Capital', 'Capital'),
        ('Revenue', 'Revenue'),
        ('Investment', 'Investment'),
        ('Balance_Trf', 'Balance_Trf'),
    ]
    type = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
    contructor = forms.ModelChoiceField(queryset=SiteSupervisor.objects.all(), required=False)
    vendor = forms.ModelChoiceField(queryset=RestaurantSupplier.objects.all(), required=False)
    customer_name = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    bankName = forms.ModelChoiceField(queryset=CashRestType.objects.all(), required=False)
    capi_name = forms.ModelChoiceField(queryset=CashRestType.objects.all(), required=False)
    reve_name = forms.ModelChoiceField(queryset=CashRestType.objects.all(), required=False)
    exp_name = forms.ModelChoiceField(queryset=CashRestType.objects.all(), required=False)
    


class RestTransactionHistoryForm(forms.ModelForm):
    class Meta:
        model = RestTransactionHistory
        fields = [
            'project',
            'transaction_type',
            'head_of_account',
            'cash_type',
            'cheque_number',
            'amount',
            'date',
            'reference',
            'type_name',
            'create_by',
            'particulars',
            'tbl_id',
            'tbl_name',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'transaction_type': forms.TextInput(attrs={'placeholder': 'e.g. Credit, Debit'}),
            'reference': forms.TextInput(attrs={'placeholder': 'Reference or MR/Bill No'}),
        }





# class RestLoanVoucherForm(forms.ModelForm):
#     class Meta:
#         model = RestLoanVoucher
#         fields = [
#             'project_name', 'source_name', 'type', 'customer_name', 'conductor_name', 'expense_name','purchase_name','vendor_name','empl_name','bankName',
#             'mr_or_bill_no', 'headAcct', 'date', 'cash_type', 'amount', 'particulars', 'is_confirmed', 'carrier', 'loan_status'
#         ]
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#             'amount': forms.NumberInput(attrs={'step': '0.01'}),
#             'particulars': forms.Textarea(attrs={'rows': 4}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['mr_or_bill_no'].required = False

#     def clean_amount(self):
#         amount = self.cleaned_data.get('amount')
#         if amount <= 0:
#             raise forms.ValidationError("Amount must be greater than zero.")
#         return amount
        
        


class RestLoanVoucherForm(forms.ModelForm):
    class Meta:
        model = RestLoanVoucher
        fields = [
            'project_name', 'source_name', 'type', 'customer_name', 'conductor_name', 'expense_name',
            'purchase_name', 'vendor_name', 'empl_name', 'bankName', 'mr_or_bill_no', 'headAcct', 
            'date', 'cash_type', 'amount', 'particulars', 'is_confirmed', 'carrier', 'loan_status'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'particulars': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mr_or_bill_no'].required = False

        # Filter project_name to show only the 2 specified projects
        if 'project_name' in self.fields:
            self.fields['project_name'].queryset = ProjectFirstLevelName.objects.filter(
                project_first_name__in=[
                    "The Galleria Restauent Cafe",
                    "The Galleria Live Kitchen"
                ]
            )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
        
        

# class CollectionForm(forms.ModelForm):
#     class Meta:
#         model = Collection
#         fields = ['sales_type', 'amount', 'cash_type']

#         widgets = {
#             'sales_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),
#             'cash_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),
#             'amount': forms.NumberInput(
#                 attrs={
#                     'class': 'form-control',
#                     'step': '0.01',
#                     'placeholder': 'Amount'
#                 }
#             ),
#         }
        
        
# class CollectionHeaderForm(forms.Form):
#     date = forms.DateField(
#         widget=forms.DateInput(
#             attrs={'type': 'date', 'class': 'form-control'}
#         )
#     )

#     project = forms.ModelChoiceField(
#         queryset=ProjectFirstLevelName.objects.all(),
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )




# class CollectionForm(forms.ModelForm):
#     class Meta:
#         model = Collection
#         fields = [
#             'type',
#             'employee',
#             'customer_name',
#             'sales_type',
#             'amount',
#             'cash_type',
#         ]

#         widgets = {
#             'type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),

#             'employee': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),

#             'customer_name': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),

#             'sales_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),

#             'cash_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),

#             'amount': forms.NumberInput(
#                 attrs={
#                     'class': 'form-control',
#                     'step': '0.01',
#                     'placeholder': 'Amount'
#                 }
#             ),
#         }

#     # ✅ Conditional validation
#     def clean(self):
#         cleaned_data = super().clean()
#         type_value = cleaned_data.get("type")
#         employee = cleaned_data.get("employee")
#         customer = cleaned_data.get("customer_name")

#         if type_value == "Employee" and not employee:
#             self.add_error("employee", "Employee is required when type is Employee.")

#         if type_value == "Customer" and not customer:
#             self.add_error("customer_name", "Customer is required when type is Customer.")

#         return cleaned_data
        




class CollectionForm(forms.ModelForm):

    class Meta:
        model = Collection
        fields = [
            'type',
            'employee',
            'customer_name',
            'sales_type',
            'amount',
            'cash_type',
        ]

        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.Select(attrs={'class': 'form-control'}),
            'sales_type': forms.Select(attrs={'class': 'form-control'}),
            'cash_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Amount'
            }),
        }

    # ✅ Conditional validation
    def clean(self):
        cleaned_data = super().clean()

        type_value = cleaned_data.get("type")
        employee = cleaned_data.get("employee")
        customer = cleaned_data.get("customer_name")

        if type_value == "Employee" and not employee:
            self.add_error("employee", "Employee is required when type is Employee.")

        if type_value == "Customer" and not customer:
            self.add_error("customer_name", "Customer is required when type is Customer.")

        return cleaned_data
        
        
class CollectionHeaderForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )

    project = forms.ModelChoiceField(
        queryset=ProjectFirstLevelName.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# class DailyPaymentForm(forms.ModelForm):
#     class Meta:
#         model = DailyPayment
#         fields = ['sales_type', 'amount', 'cash_type']

#         widgets = {
#             'sales_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),
#             'cash_type': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),
#             'amount': forms.NumberInput(
#                 attrs={
#                     'class': 'form-control',
#                     'step': '0.01',
#                     'placeholder': 'Amount'
#                 }
#             ),
#         }
        
        
# class DailyPaymentHeaderForm(forms.Form):
#     date = forms.DateField(
#         widget=forms.DateInput(
#             attrs={'type': 'date', 'class': 'form-control'}
#         )
#     )

#     project = forms.ModelChoiceField(
#         queryset=ProjectFirstLevelName.objects.all(),
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )




class DailyPaymentForm(forms.ModelForm):

    class Meta:
        model = DailyPayment
        fields = [
            'type',
            'rest_exp',
            'pur_cost',
            'sales_type',
            'amount',
            'cash_type',
        ]

        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'rest_exp': forms.Select(attrs={'class': 'form-control'}),
            'pur_cost': forms.Select(attrs={'class': 'form-control'}),
            'sales_type': forms.Select(attrs={'class': 'form-control'}),
            'cash_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Amount'
            }),
        }

    # ✅ Conditional validation
    def clean(self):
        cleaned_data = super().clean()

        type_value = cleaned_data.get("type")
        employee = cleaned_data.get("employee")
        customer = cleaned_data.get("customer_name")

        if type_value == "Employee" and not employee:
            self.add_error("employee", "Employee is required when type is Employee.")

        if type_value == "Customer" and not customer:
            self.add_error("customer_name", "Customer is required when type is Customer.")

        return cleaned_data
        
        
class DailyPaymentHeaderForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )

    project = forms.ModelChoiceField(
        queryset=ProjectFirstLevelName.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    
    
class RestBalanceTransferForm(forms.ModelForm):
    class Meta:
        model = RestBalanceTransfer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the project_name field queryset to show only the 2 specified projects
        self.fields['project_name'].queryset = ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        )
