from django import forms
from .models import CashType, HeadOfAccount,CreditVoucher,DebitVoucher,JournalVoucher,ContraVoucher,TransactionHistory,BalanceTransfer, BalanceItem,BalanceSheetHead,MainChequeBook,MainCheque,ProjectProfitRecord
from .models import DebitVoucher, SiteSupervisor, Suppliers,Customer,CustomerLead,LedgerEntry,LoanVoucher,OpenBlanceVoucher,CapitalAccount
from projects.models import ProjectFirstLevelName,Donation
from .models import AccountReconciliation, BankStatementTransaction, LedgerEntry
from purchase.models import HeadOfExpense
from hrm.models import Employee
from django.forms import inlineformset_factory
from decimal import Decimal



class CashTypeForm(forms.ModelForm):
    class Meta:
        model = CashType
        exclude = ['type_amount', 'type_note']
        fields = ['cash_type_name','account_number','type_amount','type_note']


class MainChequeBookForm(forms.ModelForm):
    class Meta:
        model = MainChequeBook
        fields = ['account', 'book_name', 'book_number', 'start_number', 'end_number', 'issue_date', 'is_active']
        widgets = {
            'issue_date': forms.DateInput(
                attrs={
                    'type': 'date',  # this shows the calendar
                    'class': 'btp-input-date'
                }
            )
        }


class MainChequeForm(forms.ModelForm):
    class Meta:
        model = MainCheque
        fields = ['cheque_book', 'cheque_number', 'issue_date', 'payee_name', 'amount', 'status', 'remarks']




class HeadOfAccountForm(forms.ModelForm):
    class Meta:
        model = HeadOfAccount
        fields = ['head_name', 'head_code']

class CreditVoucherForm(forms.ModelForm):
    customer_name = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
    )

    lead_name = forms.ModelChoiceField(
        queryset=CustomerLead.objects.none(),  # Initially empty
        required=False,
    )

    class Meta:
        model = CreditVoucher
        fields = [
            'project_name',
            'type',
            'contructor',
            'vendor',
            'customer_name',
            'lead_name',
            'capi_name',
            'donation_name',
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
            'create_cr',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'particulars': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_name'].queryset = CustomerLead.objects.filter(status='open')
        self.fields['capi_name'].queryset = CapitalAccount.objects.filter(status='active')

   
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     # Filter capi_name to only Capital Accounts
    #     self.fields['capi_name'].queryset = CapitalAccount.objects.filter(
    #         head_of_account__head_name__icontains='Capital Account'
    #     )

    #     # Filter invest_name to only Investment Accounts
    #     self.fields['invest_name'].queryset = CapitalAccount.objects.filter(
    #         head_of_account__head_name__icontains='Investment Account'
    #     )
    



class DebitVoucherForm(forms.ModelForm):
    class Meta:
        model = DebitVoucher
        fields = [
            'type',
            'contructor',
            'vendor',
            'expense',
            'empl_name',
            'capi_name',
            'reve_name',
            'invest_name',
            'customer_name',
            'donation_name',
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
        queryset=Suppliers.objects.all(),
        required=False,
    )
    expense = forms.ModelChoiceField(
        queryset=HeadOfExpense.objects.all(),
        required=False,
    )
    empl_name = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
    )
    capi_name = forms.ModelChoiceField(   # ✅ FIXED
        queryset=CapitalAccount.objects.all(),
        required=False,
    )
    reve_name = forms.ModelChoiceField(   # ✅ FIXED
        queryset=CapitalAccount.objects.all(),
        required=False,
    )
    invest_name = forms.ModelChoiceField(  # ✅ FIXED
        queryset=CapitalAccount.objects.all(),
        required=False,
    )
    customer_name = forms.ModelChoiceField(  # ✅ FIXED
        queryset=Customer.objects.all(),
        required=False,
    )
    donation_name = forms.ModelChoiceField(  # ✅ FIXED
        queryset=Donation.objects.all(),
        required=False,
    )
    
    

# class JournalVoucherForm(forms.ModelForm):
#     class Meta:
#         model = JournalVoucher
#         fields = [
#             'date',
#             'project',
#             'head_of_account',
#             'cheque_number',
#             'amount',
#             'mr_or_bill_no',
#             'description',
#             'carrier',
#             'is_confirmed',
#             'party_combined',
#         ]
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'cheque_number': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'mr_or_bill_no': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'carrier': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
#             'party_combined': forms.HiddenInput(),
#         }



class JournalVoucherForm(forms.ModelForm):
    class Meta:
        model = JournalVoucher
        fields = [
            'date',
            'project',
            'head_of_account_to',
            'head_of_account_from',
            'cheque_number',
            'amount',
            'mr_or_bill_no',
            'description',
            'carrier',
            'is_confirmed',
            'party_to_combined',
            'party_from_combined',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'cheque_number': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'mr_or_bill_no': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'carrier': forms.TextInput(attrs={'class': 'w-full text-sm border border-slate-300 shadow-sm rounded-md p-2'}),
            'party_to_combined': forms.HiddenInput(),
            'party_from_combined': forms.HiddenInput(),
        }


class ContraVoucherForm(forms.ModelForm):
    class Meta:
        model = ContraVoucher
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class LedgerReportForm(forms.ModelForm):
    class Meta:
        model = LedgerEntry
        exclude=['tbl_id','tbl_name']
        fields = ['project_name', 'type','contructor','vendor','customer_name','bankName', 'capi_name', 'reve_name','exp_name','empl_name', 'donation_name', 'invest_name', 'balance_trf','type_name', 'head', 'mr_or_bill_no','cash_type', 'cheque_number','date', 'description', 'debit', 'credit', 'carrier', 'loan_status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'Hand Cash' from bankName dropdown
        self.fields['bankName'].queryset = CashType.objects.exclude(cash_type_name__iexact="Cash in Hand")


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
        queryset=CashType.objects.all(),
        required=False, 
    )
    capi_name = forms.ModelChoiceField(
        queryset=CapitalAccount.objects.all(),
        required=False, 
    )
    reve_name = forms.ModelChoiceField(
        queryset=CapitalAccount.objects.all(),
        required=False, 
    )
    exp_name = forms.ModelChoiceField(
        queryset=HeadOfExpense.objects.all(),
        required=False, 
    )
    donation_name = forms.ModelChoiceField(
        queryset=Donation.objects.all(),
        required=False, 
    )
    invest_name = forms.ModelChoiceField(
        queryset=CapitalAccount.objects.all(),
        required=False, 
    )


class LedgerFilterForm(forms.Form):
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
    vendor = forms.ModelChoiceField(queryset=Suppliers.objects.all(), required=False)
    customer_name = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    bankName = forms.ModelChoiceField(queryset=CashType.objects.all(), required=False)
    capi_name = forms.ModelChoiceField(queryset=CashType.objects.all(), required=False)
    reve_name = forms.ModelChoiceField(queryset=CashType.objects.all(), required=False)
    exp_name = forms.ModelChoiceField(queryset=CashType.objects.all(), required=False)
    


class TransactionHistoryForm(forms.ModelForm):
    class Meta:
        model = TransactionHistory
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
        


from django import forms
from .models import ProjectBalanceTransfer

class ProjectBalanceTransferForm(forms.ModelForm):
    class Meta:
        model = ProjectBalanceTransfer
        fields = '__all__'


class BalanceTransferForm(forms.ModelForm):
    class Meta:
        model = BalanceTransfer
        fields = '__all__'


# class LoanVoucherForm(forms.ModelForm):
#     customer_name = forms.ModelChoiceField(
#         queryset=Customer.objects.all(),
#         required=False,
#     )    

#     class Meta:
#         model = LoanVoucher
#         fields = [
#             'project_name',
#             'type',
#             'customer_name',
#             'conductor_name', 
#             'expense_name',
#             'mr_or_bill_no',
#             'date',
#             'amount',
#             'particulars',
#             'is_confirmed',
#             'carrier',
#             'loan_status',
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
    

# class LoanVoucherForm(forms.ModelForm):
#     class Meta:
#         model = LoanVoucher
#         fields = [
#             'project_name', 'type', 'customer_name', 'conductor_name', 'expense_name',
#             'mr_or_bill_no', 'date', 'amount', 'particulars', 'is_confirmed', 'carrier', 'loan_status'
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
    


class LoanVoucherForm(forms.ModelForm):
    class Meta:
        model = LoanVoucher
        fields = [
            'project_name', 'source_name', 'type', 'customer_name', 'conductor_name', 'expense_name', 'vendor_name','empl_name','bankName',
            'mr_or_bill_no', 'headAcct', 'date', 'cash_type', 'amount', 'particulars', 'is_confirmed', 'carrier', 'loan_status'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'particulars': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mr_or_bill_no'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
        
        

class OpenBlanceVoucherForm(forms.ModelForm):
    class Meta:
        model = OpenBlanceVoucher
        fields = [
            'project_name',
            'type',
            'contructor',
            'vendor',
            'customer_name',
            'bankName',
            'head_of_account',
            'amount',
            'cash_type',
            'cheque_number',
            'date',
            'particulars',
            'is_confirmed',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'particulars': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'Hand Cash' from bankName dropdown
        self.fields['bankName'].queryset = CashType.objects.exclude(cash_type_name__iexact="Cash in Hand")


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
        queryset=CashType.objects.all(),
        required=False, 
    )


#--------- Extra Code account reconsolution-----

class BankStatementUploadForm(forms.Form):
    file = forms.FileField(label="Upload Bank Statement CSV")

class ReconciliationForm(forms.ModelForm):
    statement_txn = forms.ModelChoiceField(
        queryset=BankStatementTransaction.objects.none(),
        label="Bank Statement Transaction",
        widget=forms.Select(attrs={'class': 'w-full border rounded p-2'})
    )

    ledger_entry = forms.ModelChoiceField(
        queryset=LedgerEntry.objects.all(),
        label="Ledger Entry",
        widget=forms.Select(attrs={'class': 'w-full border rounded p-2'})
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full border rounded p-2', 'rows': 3}),
        label="Note (optional)"
    )

    class Meta:
        model = AccountReconciliation
        fields = ['statement_txn', 'ledger_entry', 'note']

    def __init__(self, *args, **kwargs):
        bank = kwargs.pop('bank', None)
        super().__init__(*args, **kwargs)
        if bank:
            self.fields['statement_txn'].queryset = BankStatementTransaction.objects.filter(bank=bank, matched=False)
        else:
            self.fields['statement_txn'].queryset = BankStatementTransaction.objects.none()

from django import forms
from .models import CapitalAccount, HeadOfAccount

class CapitalAccountForm(forms.ModelForm):
    class Meta:
        model = CapitalAccount
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
        self.fields['head_of_account'].queryset = HeadOfAccount.objects.filter(
            head_name__in=['Capital Accounts', 'Investment Account', 'Revenue Account']
        )
        
        
        

class BalanceSheetHeadForm(forms.ModelForm):
    class Meta:
        model = BalanceSheetHead
        fields = ['head_name', 'type_name', 'name']
        widgets = {
            'head_name': forms.Select(attrs={'id': 'head_name'}),
            'type_name': forms.Select(attrs={'id': 'type_name'}),
        }



class BalanceItemForm(forms.ModelForm):
    class Meta:
        model = BalanceItem
        fields = ['project_name','head', 'type_name', 'name', 'value', 'date']
        exclude = ['status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded p-2'}),
            'value': forms.NumberInput(attrs={'class': 'w-full border rounded p-2'}),
            'type_name': forms.TextInput(attrs={'class': 'w-full border rounded p-2'}),
            'name': forms.TextInput(attrs={'class': 'w-full border rounded p-2'}),
            'status': forms.TextInput(attrs={'class': 'w-full border rounded p-2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].queryset = BalanceSheetHead.objects.all()
        self.fields['head'].widget.attrs.update({'class': 'w-full border rounded p-2', 'id': 'head_select'})





class ProjectProfitRecordForm(forms.ModelForm):
    
    class Meta:
        model = ProjectProfitRecord
        fields = [
            'project',
            'profit',
            'profit_25',
            'final_profit',
        ]

        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-select border rounded px-3 py-2 w-full'
            }),
            'profit': forms.NumberInput(attrs={
                'class': 'form-input border rounded px-3 py-2 w-full',
                'step': '0.01'
            }),
            'profit_25': forms.NumberInput(attrs={
                'class': 'form-input border rounded px-3 py-2 w-full',
                'readonly': True,
                'step': '0.01'
            }),
            'final_profit': forms.NumberInput(attrs={
                'class': 'form-input border rounded px-3 py-2 w-full',
                'readonly': True,
                'step': '0.01'
            }),
        }

