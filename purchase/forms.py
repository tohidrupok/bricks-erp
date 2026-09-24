from django import forms
from .models import Notification
from django.contrib.auth.models import User
from .models import Requisition,RequisitionCategory,HeadOfRequisition,RequisitionComparative,HeadOfExpense,ExpenseVoucher,PettyCash,ExpenseRequisition,BillRequisition,RequisitionApprovalPayment,FCMDevice
from projects.models import SiteSupervisor,Suppliers
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP
from accounting.models import DebitVoucher




class RequisitionForm(forms.ModelForm):
    vendor_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-input'})
    )

    class Meta:
        model = Requisition
        exclude = [
            'approv_status', 'approv_note',
            'approv_acct_status', 'approv_acct_note',
            'approv_purch_status', 'approv_purch_note',
            'return_requisition', 'requi_uniq_id','purch_appov',
            'purch_date', 'purch_id','return_qty', 'return_status','cash_empl'
        ]
        widgets = {
            'requisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'qty': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'discount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'unit': forms.TextInput(attrs={'class': 'form-input'}),
            'remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'type': forms.HiddenInput(),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None:
            try:
                return Decimal(amount).quantize(Decimal('0.01'))
            except InvalidOperation:
                raise forms.ValidationError("Invalid amount value.")
        return Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")

        try:
            qty = Decimal(qty)
            rate = Decimal(rate)
        except InvalidOperation:
            raise forms.ValidationError("Quantity and Rate must be valid decimal numbers.")

        if qty <= 0 or rate <= 0:
            raise forms.ValidationError("Quantity and Rate must be greater than zero.")

        cleaned_data['amount'] = (qty * rate).quantize(Decimal('0.01'))
        self.instance.amount = cleaned_data['amount']
        return cleaned_data
        



class RequisitionApprovalPaymentForm(forms.ModelForm):
    class Meta:
        model = RequisitionApprovalPayment
        fields = ['requisition', 'requi_item_name','requi_uniq_id', 'supplier', 'payment_type', 'requi_amount','requisition_date','debit_voucher']





class BillRequisitionForm(forms.ModelForm):
    vendor_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-input'})
    )

    class Meta:
        model = BillRequisition
        exclude = [
            'note','head_of_account','mr_or_bill_no',
            'approv_status', 'approv_note',
            'approv_acct_status', 'approv_acct_note',
            'approv_purch_status',
            'return_requisition', 'requi_uniq_id','purch_appov',
            'purch_date', 'purch_id','return_qty', 'return_status','cash_empl'
        ]
        widgets = {
            'requisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'qty': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'unit': forms.TextInput(attrs={'class': 'form-input'}),
            'remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'type': forms.HiddenInput(),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None:
            try:
                return Decimal(amount).quantize(Decimal('0.01'))
            except InvalidOperation:
                raise forms.ValidationError("Invalid amount value.")
        return Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")

        try:
            qty = Decimal(qty)
            rate = Decimal(rate)
        except InvalidOperation:
            raise forms.ValidationError("Quantity and Rate must be valid decimal numbers.")

        if qty <= 0 or rate <= 0:
            raise forms.ValidationError("Quantity and Rate must be greater than zero.")

        cleaned_data['amount'] = (qty * rate).quantize(Decimal('0.01'))
        self.instance.amount = cleaned_data['amount']
        return cleaned_data
        
        

from .models import (
    RequisitionApprovalPayment,
    BillRequisitionApprovalPayment,  
    HeadOfRequisition,
)

class BillRequisitionApprovalPaymentForm(forms.ModelForm):
    class Meta:
        model = BillRequisitionApprovalPayment
        fields = [
            'requisition', 
            'requi_item_name', 
            'requi_uniq_id', 
            'contractors', 
            'payment_type', 
            'requi_amount', 
            'requisition_date', 
            'debit_voucher',
            'requi_id'
        ]
        
        

class PettyCashForm(forms.ModelForm):
    vendor_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-input'})
    )

    class Meta:
        model = PettyCash
        exclude = [
            'approv_status', 'approv_note',
            'approv_acct_status', 'approv_acct_note',
            'approv_purch_status', 'approv_purch_note',
            'requi_uniq_id'
        ]
        widgets = {
            'requisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'qty': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-input'}),
            'unit': forms.TextInput(attrs={'class': 'form-input'}),
            'remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'type': forms.HiddenInput(),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None:
            try:
                return Decimal(amount).quantize(Decimal('0.01'))
            except InvalidOperation:
                raise forms.ValidationError("Invalid amount value.")
        return Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")

        try:
            qty = Decimal(qty)
            rate = Decimal(rate)
        except InvalidOperation:
            raise forms.ValidationError("Quantity and Rate must be valid decimal numbers.")

        if qty <= 0 or rate <= 0:
            raise forms.ValidationError("Quantity and Rate must be greater than zero.")

        cleaned_data['amount'] = (qty * rate).quantize(Decimal('0.01'))
        self.instance.amount = cleaned_data['amount']
        return cleaned_data
        
        
        

class RequisitionCategoryForm(forms.ModelForm):
    class Meta:
        model = RequisitionCategory
        fields = ['requi_category_name']


class HeadOfRequisitionForm(forms.ModelForm):
    class Meta:
        model = HeadOfRequisition
        fields = ['requi_category', 'head_requi_name', 'head_requi_code']




class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = [
            'sender',
            'recipient',
            'project_name',
            'message',
            'is_read',
            'link',
            'pass_url',
            'role',
        ]
        widgets = {
            'sender': forms.Select(attrs={'class': 'form-select'}),
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'project_name': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea w-full', 'rows': 3}),
            'is_read': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'link': forms.URLInput(attrs={'class': 'form-input w-full'}),
            'pass_url': forms.TextInput(attrs={'class': 'form-input w-full', 'placeholder': 'Optional internal link key'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class FCMDeviceForm(forms.ModelForm):
    class Meta:
        model = FCMDevice
        fields = ['user', 'token']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'token': forms.TextInput(attrs={'class': 'form-input w-full'}),
        }

        
        

# class RequisitionComparativeForm(forms.ModelForm):
#     class Meta:
#         model = RequisitionComparative
#         exclude = ['approv_status', 'approv_note', 'return_requisition']
#         widgets = {
#             'requisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
#             'amount': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-input'}),
#             'qty': forms.NumberInput(attrs={'class': 'form-input'}),
#             'rate': forms.NumberInput(attrs={'class': 'form-input'}),
#             'unit': forms.TextInput(attrs={'class': 'form-input'}),
#             'remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
#             'vendor_name': forms.Select(attrs={'class': 'form-select'}),
#             'project_name': forms.Select(attrs={'class': 'form-select'}),
#             'employee_name': forms.Select(attrs={'class': 'form-select'}),
#             'item_name': forms.Select(attrs={'class': 'form-select'}),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         qty = cleaned_data.get("qty")
#         rate = cleaned_data.get("rate")

#         if qty is None or rate is None:
#             raise forms.ValidationError("Quantity and Rate cannot be empty.")
#         if qty <= 0 or rate <= 0:
#             raise forms.ValidationError("Quantity and Rate must be greater than zero.")

#         cleaned_data['amount'] = qty * rate
#         self.instance.amount = cleaned_data['amount']
#         return cleaned_data


class RequisitionComparativeForm(forms.ModelForm):
    class Meta:
        model = RequisitionComparative
        exclude = ['approv_status', 'approv_note', 'return_requisition', 'amount']  # 💡 Exclude amount
        widgets = {
            'requisition_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'qty': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'form-input',
                'id': 'id_qty'
            }),
            'rate': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'form-input',
                'id': 'id_rate'
            }),
            'unit': forms.TextInput(attrs={'class': 'form-input'}),
            'remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'vendor_name': forms.Select(attrs={'class': 'form-select'}),
            'project_name': forms.Select(attrs={'class': 'form-select'}),
            'employee_name': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")
        if qty <= 0 or rate <= 0:
            raise forms.ValidationError("Quantity and Rate must be greater than zero.")

        # Quantize safely
        amount = (qty * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.instance.amount = amount  # Do not trust POST — use internal calculation
        return cleaned_data
        
        

class HeadOfExpenseForm(forms.ModelForm):
    class Meta:
        model = HeadOfExpense
        fields = ['head_exp_name', 'head_exp_code']


class ExpenseVoucherForm(forms.ModelForm):
    class Meta:
        model = ExpenseVoucher
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approv_status'].required = False
        
        
        
# class ExpenseRequisitionForm(forms.ModelForm):
#     class Meta:
#         model = ExpenseRequisition
#         exclude = ['requi_expense_id']  # Exclude this field
#         widgets = {
#             'remark': forms.Textarea(attrs={'rows': 2}),
#             'approv_note': forms.Textarea(attrs={'rows': 2}),
#         }
        
        
        
# class ExpenseRequisitionForm(forms.ModelForm):
#     class Meta:
#         model = ExpenseRequisition
#         exclude = ['requi_expense_id','ledger_add']
#         fields = ['project_name', 'item_name', 'qty', 'rate', 'amount', 'approv_status']
#         widgets = {
#             'project_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'item_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'qty': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'rate': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'approv_status': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#         }



# class ExpenseRequisitionForm(forms.ModelForm):
#     class Meta:
#         model = ExpenseRequisition
#         # Either use fields to list all editable fields
#         fields = [
#             'project_name', 'item_name', 'qty', 'rate', 'amount', 
#             'descript', 'remark', 'approv_status'
#         ]
#         widgets = {
#             'project_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'item_name': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'qty': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'rate': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'descript': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#             'remark': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded p-2', 'rows': 3}),
#             'approv_status': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
#         }




class ExpenseRequisitionForm(forms.ModelForm):
    class Meta:
        model = ExpenseRequisition
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