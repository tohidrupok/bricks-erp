from django import forms
from .models import Customer,CustomerLead,CustomerFollowup,Sale,CustInfoBank,BulkSMS


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name',
            'profession',
            'lead_status',
            'lead_source',
            'project',
            'contact_no',
            'address',
            'description',
            'organization',
            'email',
            'assign_to_user',
            'date',
            'photo',
            'status',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
 
 
 
class CustInfoBankForm(forms.ModelForm):
    class Meta:
        model = CustInfoBank
        fields = [
            'customer_name',
            'profession',
            'contact_no',
            'address',
            'description',
            'email',
            'nid',
            'dateofbrith',
            'date',
            'photo',
            'status',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
        

class CustomerLeadForm(forms.ModelForm):
    class Meta:
        model = CustomerLead
        fields = [
            'customer',
            'lead_name',
            'project_name',
            'first_contact_date',
            'first_contact_note',
            'followup_date',
            'followup_note',
            'note',
            'status',
        ]
        widgets = {
            'first_contact_date': forms.DateInput(attrs={'type': 'date'}),
            'second_contact_date': forms.DateInput(attrs={'type': 'date'}),
            'third_contact_date': forms.DateInput(attrs={'type': 'date'}),
            'first_contact_note': forms.Textarea(attrs={'rows': 3}),
            'second_contact_note': forms.Textarea(attrs={'rows': 3}),
            'third_contact_note': forms.Textarea(attrs={'rows': 3}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }



class CustomerFollowupForm(forms.ModelForm):
    class Meta:
        model = CustomerFollowup
        fields = ['followup_date', 'followup_note']
        
        
        

class SaleForm(forms.ModelForm):
    sale_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Sale Date"
    )

    booking_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        label="Booking Amount"
    )
    
    total_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        label="Total Amount"
    )
    
    sales_discount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        label="Sales Discount"
    )
    
    payment_received = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        initial=0,
        label="Payment Received"
    )
    
    balance_due = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'readonly': 'readonly'}),
        label="Balance Due",
        required=False,
    )
    
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Remarks"
    )
    
    class Meta:
        model = Sale
        fields = [
            'project_name',
            'customer',
            'sales_agent',
            'sale_date',
            'booking_amount',
            'total_amount',
            'sales_discount',
            'payment_mode',
            'sale_status',
            'payment_received',
            'balance_due',
            'remarks',
        ]
        widgets = {
            'project_name': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'sales_agent': forms.Select(attrs={'class': 'form-select'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'sale_status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount')
        sales_discount = cleaned_data.get('sales_discount') or 0
        payment_received = cleaned_data.get('payment_received')

        if sales_discount < 0:
            self.add_error('sales_discount', 'Discount cannot be negative.')

        if total_amount is not None and sales_discount is not None:
            if sales_discount > total_amount:
                self.add_error('sales_discount', 'Discount cannot exceed total amount.')

        if total_amount is not None and payment_received is not None and sales_discount is not None:
            discounted_price = total_amount - sales_discount
            if payment_received > discounted_price:
                self.add_error('payment_received', 'Payment received cannot exceed total amount minus discount.')
            cleaned_data['balance_due'] = discounted_price - payment_received

        return cleaned_data
        
        



# class BulkSMSForm(forms.Form):
#     recipients = forms.ModelMultipleChoiceField(
#         queryset=Customer.objects.filter(status=True),  # only active customers
#         widget=forms.CheckboxSelectMultiple,          # use checkboxes
#         label="Select Recipients"
#     )
#     message = forms.CharField(
#         widget=forms.Textarea(attrs={
#             'rows': 4,
#             'placeholder': 'Enter your message here'
#         }),
#         label="Message"
#     )





class BulkSMSForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.filter(status=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-1'  # optional spacing between checkboxes
        }),
        label="Select Recipients"
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Enter your message here',
            'class': 'w-full border border-gray-300 rounded p-2 bg-gray-50'
        }),
        label="Message"
    )

