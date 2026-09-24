from django import forms
from .models import PropertyOwner,Project,Property,RecordFile,JointVenture,JVPartner,Tenant,LeaseAgreement,LeasePayment,Buyer,SaleRecord,LandPurchase,LandDebitVoucher,CashMethod,LandCreditVoucher,LandHeadOfAccount,LandApprovalPayment,LandLedgerEntry,LandTransactionHistory,LandHeadOfExpense
from projects.models import ProjectFirstLevelName

class PropertyOwnerForm(forms.ModelForm):
    class Meta:
        model = PropertyOwner
        fields = ['owner_name', 'contact_information', 'owner_type', 'ownership_type', 
                  'nid_card_details', 'telephone_number', 'current_address', 'utility_bill', 'photo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nid_card_details'].required = True  # NID Card is required
        self.fields['telephone_number'].required = True  # Telephone is required





class RecordFileForm(forms.ModelForm):

    class Meta:
        model = RecordFile
        # 🌟 FIX: Included 'area' within the explicit layout fields tracking list
        fields = [
            'date',
            'file_type',
            'mouza',
            'cs_dag_no',
            'sa_dag_no',
            'rs_dag_no',
            'ct_dag_no',
            'owner_client',
            'work_type',
            'area',
            'area_value',
            'status',
            'responsible',
            'remarks',
        ]

        TAILWIND_CLASS = (
            'w-full px-3 py-2 text-xs border border-slate-200 '
            'bg-white text-slate-700 rounded-xl '
            'focus:ring-4 focus:ring-primary/20 '
            'focus:border-primary transition outline-none'
        )

        widgets = {
            'date': forms.DateInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'type': 'date'
                }
            ),
            'file_type': forms.Select(
                attrs={
                    'class': TAILWIND_CLASS,
                    'id': 'id_file_type'
                }
            ),
            
            'mouza': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter Mouza Name'
                }
            ),
            'cs_dag_no': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter CS Dag NO'
                }
            ),
            'sa_dag_no': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter SA Dag NO'
                }
            ),
            'rs_dag_no': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter RS Dag NO'
                }
            ),
            'ct_dag_no': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter CT Dag NO'
                }
            ),
            
            'owner_client': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter Owner / Client Name'
                }
            ),
            'work_type': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter Work Type'
                }
            ),
            'area': forms.Select(
                attrs={
                    'class': TAILWIND_CLASS
                }
            ),
            'area_value': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Enter Area Value'
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': TAILWIND_CLASS
                }
            ),
            'responsible': forms.TextInput(
                attrs={
                    'class': TAILWIND_CLASS,
                    'placeholder': 'Person Responsible'
                }
            ),
            'remarks': forms.Textarea(
                attrs={
                    'class': TAILWIND_CLASS,
                    'rows': 3
                }
            ),
        }
        
        

class ProjectForm(forms.ModelForm): 
    project_name = forms.ModelChoiceField(queryset=ProjectFirstLevelName.objects.all(), required=True, label="Project Name")
      
    class Meta:
        model = Project
        fields = [
            'project_name', 'project_description', 'project_start_date', 'project_end_date', 'project_status',
            'land_details_area', 'land_purchase_price', 'land_current_market_price',
            'number_of_stories', 'flat_type_a', 'flat_type_b', 'flat_type_c', 'flat_type_d', 'parking_details',
            'construction_cost', 'labor_cost', 'material_cost', 'other_costs', 'profit_margin'
        ]
        widgets = {
            'project_start_date': forms.DateInput(attrs={'type': 'date'}),
            'project_end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# Property Form
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['property_type', 'address', 'size', 'sale_price', 'lease_price', 'sale_status', 'lease_status', 'purchase_date', 'construction_date', 'owner', 'project']

# JointVenture Form
# class JointVentureForm(forms.ModelForm):
#     class Meta:
#         model = JointVenture
#         fields = ['land_purchase', 'land_owner_name', 'developer_name', 'partner_ownership_percentage', 'developer_flat','developer_sqft','land_owner_flat','land_owner_sqft','start_date', 'end_date', 'profit_share', 'revenue_share', 'signing_money','jv_status']



class JointVentureForm(forms.ModelForm):
    class Meta:
        model = JointVenture
        fields = "__all__"
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "developer_flat": forms.NumberInput(attrs={"class": "form-input"}),
            "developer_sqft": forms.NumberInput(attrs={"step": "0.01", "class": "form-input"}),
            "land_owner_flat": forms.NumberInput(attrs={"class": "form-input"}),
            "land_owner_sqft": forms.NumberInput(attrs={"step": "0.01", "class": "form-input"}),
            "signing_money": forms.NumberInput(attrs={"step": "0.01", "class": "form-input"}),
        }
        
        
        
# JVPartner Form
class JVPartnerForm(forms.ModelForm):
    class Meta:
        model = JVPartner
        fields = ['partner_name', 'contact_information', 'contribution_amount', 'joint_venture']   

# Tenant Form
class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['tenant_name', 'contact_information', 'tenant_type']


class LeaseAgreementForm(forms.ModelForm):
    class Meta:
        model = LeaseAgreement
        fields = ['land_purchase', 'tenant', 'lease_start_date', 'lease_end_date', 'lease_price', 'security_deposit', 'lease_status', 'payment_terms', 'agreement_document']


# LeasePayment Form
class LeasePaymentForm(forms.ModelForm):
    class Meta:
        model = LeasePayment
        fields = ['lease_agreement', 'payment_amount', 'payment_date', 'payment_method', 'payment_status']

# Buyer Form
class BuyerForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['buyer_name', 'contact_information', 'buyer_type', 'nid', 'photo']

    # Custom error messages for each field
    buyer_name = forms.CharField(
        required=True, 
        error_messages={'required': 'Please enter the buyer name.'}
    )
    contact_information = forms.CharField(
        required=True, 
        error_messages={'required': 'Please enter contact information.'}
    )
    buyer_type = forms.ChoiceField(
        choices=[('Individual', 'Individual'), ('Company', 'Company')],
        required=True, 
        error_messages={'required': 'Please select a buyer type.'}
    )
    nid = forms.CharField(
        required=True, 
        error_messages={'required': 'Please enter the National ID.'}
    )
    photo = forms.ImageField(
        required=True, 
        error_messages={'required': 'Please upload a photo.'}
    )


class SaleRecordForm(forms.ModelForm):
    class Meta:
        model = SaleRecord
        fields = ['property', 'sale_price', 'sale_date', 'buyer', 'sale_status', 'sale_agreement_document', 'payment_status', 'money_receipt_no', 'money_receipt_date']



## land purchase ---
class LandPurchaseForm(forms.ModelForm):
    class Meta:
        model = LandPurchase
        exclude = ['approval_status']
        fields = '__all__'
        widgets = {
            'land_supplier': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            # Add other widgets if needed
        }


class CashMethodFrom(forms.ModelForm):
    class Meta:
        model = CashMethod
        fields = ['method_name','account_number','type_amount','type_note']


class LandHeadOfAccountForm(forms.ModelForm):
    class Meta:
        model = LandHeadOfAccount
        fields = ['head_name', 'head_code']


class LandDebitVoucherForm(forms.ModelForm):
    class Meta:
        model = LandDebitVoucher
        fields = [
            'land_purchase','type','owner', 'expense', 'head_of_account', 'cash_type', 'cheque_number',
            'amount', 'mr_or_bill_no', 'date', 'remark', 'carrier','advance_pay', 'create_dr_by'
        ]
        widgets = {
            'land_purchase': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'remark': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border p-2 rounded-md'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border p-2 rounded-md'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make remark optional to allow auto-fill
        self.fields['remark'].required = False


class LandCreditVoucherForm(forms.ModelForm):
    class Meta:
        model = LandCreditVoucher
        fields = ['land_purchase', 'type', 'owner','cash_type', 'cheque_number', 'head_of_account', 'amount', 'mr_or_bill_no', 'date', 'remark', 'approval_status', 'carrier','create_cr_by']



class LandApprovalPaymentFrom(forms.ModelForm):
    class Meta:
        model = LandApprovalPayment
        fields = ['land_purchase', 'owner','land_uniq_id', 'payment_type', 'purch_amount', 'debit_voucher', 'purchase_date']



class LandLedgerEntryForm(forms.ModelForm):
    class Meta:
        model = LandLedgerEntry
        fields = [
            'land_purchase',
            'type',
            'owner',
            'expense',
            'cash_type',
            'cheque_number',
            'type_name',
            'head_of_account',
            'mr_or_bill_no',
            'date',
            'description',
            'debit',
            'credit',
            'carrier',
            'loan_status',
            'tbl_id',
            'tbl_name',
        ]

        widgets = {
            'land_purchase': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'owner': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'type_name': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'mr_or_bill_no': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border p-2 rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full border p-2 rounded', 'rows': 3}),
            'debit': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
            'credit': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
            'carrier': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'loan_status': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'tbl_id': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'tbl_name': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
        }


class LandTransactionHistoryForm(forms.ModelForm):
    class Meta:
        model = LandTransactionHistory
        fields = [
            'land_purchase',
            'type',
            'owner',
            'expense',
            'cash_type',
            'cheque_number',
            'head_of_account',
            'amount',
            'date',
            'type_name',
            'reference',
            'create_by',
            'particulars',
            'tbl_id',
        ]

        widgets = {
            'land_purchase': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'owner': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border p-2 rounded', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border p-2 rounded'}),
            'type_name': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'reference': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'create_by': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'particulars': forms.Textarea(attrs={'class': 'w-full border p-2 rounded', 'rows': 3}),
            'tbl_id': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
        }
        
        
class LandHeadOfExpenseForm(forms.ModelForm):
    class Meta:
        model = LandHeadOfExpense
        fields = ['head_exp_name', 'head_exp_code']
        
        
        
        
from django import apps
from django import forms
from .models import LandDocument

class LandDocumentForm(forms.ModelForm):
    class Meta:
        model = LandDocument
        fields = '__all__'
        widgets = {
            'doc_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply unified styling across all fields dynamically
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border'
            })
