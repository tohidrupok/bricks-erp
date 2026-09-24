from django import forms
from .models import Varatiya, Room, ProjectName, Rent, ChequeBook, Cheque, TenantCashType, ReceiveVoucher, TenantBulkSMS
from django.forms.widgets import DateInput 


class ProjectNameForm(forms.ModelForm):
    class Meta:
        model = ProjectName
        fields = ['name'] 

class VaratiyaForm(forms.ModelForm):
    class Meta:
        model = Varatiya
        exclude = ['type', 'head_of_account'] 

    def __init__(self, *args, **kwargs):
        super(VaratiyaForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                css_class = 'block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500'
            elif isinstance(field.widget, forms.Textarea):
                css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'
            else:
                css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'
            field.widget.attrs['class'] = css_class 


# class RoomForm(forms.ModelForm):
#     class Meta:
#         model = Room
#         fields = [
#             'project',
#             'flat',
#             'room_name',                     
#             'core_room_rent',           
#             'gas_rent',
#             'water_rent',
#             'service_rent',
#             'parking_cost',
#             'garbage_rent',          
#         ]


#     def __init__(self, *args, **kwargs):
#         super(RoomForm, self).__init__(*args, **kwargs)
#         for field_name, field in self.fields.items():
#             if isinstance(field.widget, forms.FileInput):
#                 css_class = 'block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500'
#             elif isinstance(field.widget, forms.Select):
#                 css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'
#             else:
#                 css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'

#             field.widget.attrs['class'] = css_class




class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'project',
            'flat',
            'room_name',                     
            'core_room_rent',           
            'gas_rent',
            'water_rent',
            'service_rent',
            'parking_cost',
            'garbage_rent',
        ]

    def __init__(self, *args, **kwargs):
        super(RoomForm, self).__init__(*args, **kwargs)

        # Include extra fields only when editing an existing instance
        if self.instance and self.instance.pk:
            self.fields['meter_number'] = forms.CharField(
                required=False, max_length=50, label="Meter Number",
                initial=self.instance.meter_number
            )
            self.fields['opening_reading'] = forms.DecimalField(
                required=False, max_digits=10, decimal_places=2, label="Opening Reading",
                initial=self.instance.opening_reading
            )
            self.fields['last_month_reading'] = forms.DecimalField(
                required=False, max_digits=10, decimal_places=2, label="Last Month Reading",
                initial=self.instance.last_month_reading
            )
            self.fields['unit_charge'] = forms.DecimalField(
                required=False, max_digits=10, decimal_places=2, label="Unit Charge",
                initial=self.instance.unit_charge
            )

        # Apply CSS classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                css_class = 'block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500'
            elif isinstance(field.widget, forms.Select):
                css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'
            else:
                css_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-blue-500 focus:border-blue-500'

            field.widget.attrs['class'] = css_class

    def save(self, commit=True):
        # Save the standard fields first
        instance = super(RoomForm, self).save(commit=False)

        # Save the extra meter fields manually
        if 'meter_number' in self.cleaned_data:
            instance.meter_number = self.cleaned_data['meter_number']
        if 'opening_reading' in self.cleaned_data:
            instance.opening_reading = self.cleaned_data['opening_reading'] or 0
        if 'last_month_reading' in self.cleaned_data:
            instance.last_month_reading = self.cleaned_data['last_month_reading'] or 0
        if 'unit_charge' in self.cleaned_data:
            instance.unit_charge = self.cleaned_data['unit_charge'] or 0

        if commit:
            instance.save()
        return instance

            
            


class RentForm(forms.ModelForm):
    flat = forms.ChoiceField(
        choices=[('', '---------')] + [(f'F{i}', f'F{i}') for i in range(1, 16)],
        required=False,
        label="Flat"
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        required=False,
        label="Room"
    )

    class Meta:
        model = Rent
        fields = ['projectref', 'room', 'varatiya', 'startmonths']
        widgets = {
            'startmonths': DateInput(attrs={'type': 'text', 'autocomplete': 'off'}),
            'endmonths': DateInput(attrs={'type': 'text', 'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ProjectRef dropdown
        self.fields['projectref'].queryset = ProjectName.objects.all()

        # Varatiya dropdown
        self.fields['varatiya'].queryset = Varatiya.objects.all()

        # if POST have room queryset can filter
        if 'projectref' in self.data and 'flat' in self.data:
            try:
                projectref_id = int(self.data.get('projectref'))
                flat = self.data.get('flat')
                projectref = ProjectName.objects.get(id=projectref_id)
                self.fields['room'].queryset = Room.objects.filter(
                    project=projectref,
                    flat=flat, status='Deactive'
                ).order_by('room_name')
            except (ValueError, ProjectName.DoesNotExist):
                pass

    def clean(self):
        cleaned_data = super().clean()
        varatiya = cleaned_data.get('varatiya')
        startmonths = cleaned_data.get('startmonths')

        if not varatiya:
            raise forms.ValidationError("Please select a Tenant before creating a rent.")

        if not startmonths:
            raise forms.ValidationError("Please select a start date for the rent.")

        return cleaned_data 


    def save(self, commit=True):
        rent = super().save(commit=False)

        # jei room select kora hobe, se room ar status automatically Active hobe
        if rent.room:
            rent.status = 'Active'  # Rent status set
            rent.room.status = 'Active'
            rent.room.save()

        if commit:
            rent.save()
        return rent
    



  

class ChequeBookForm(forms.ModelForm):
    class Meta:
        model = ChequeBook
        fields = ['account', 'book_name', 'book_number', 'start_number', 'end_number', 'issue_date', 'is_active']
        widgets = {
            'issue_date': forms.DateInput(
                attrs={
                    'type': 'date',  # this shows the calendar
                    'class': 'btp-input-date'
                }
            )
        }


class ChequeForm(forms.ModelForm):
    class Meta:
        model = Cheque
        fields = ['cheque_book', 'cheque_number', 'issue_date', 'payee_name', 'amount', 'status', 'remarks']



class TenantCashForm(forms.ModelForm):
    class Meta:
        model = TenantCashType
        fields = [
            'account_type',
            'account_name',
            'account_number',
            'bank_name',
            'branch_name',
            'balance',
            'is_active',
            'description',
        ]

        widgets = {
            'account_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account name',
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account number (optional)',
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name (if applicable)',
            }),
            'branch_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter branch name (if applicable)',
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a short note about this account (optional)',
            }),
        }

        labels = {
            'account_type': 'Account Type',
            'account_name': 'Account Name',
            'account_number': 'Account Number',
            'bank_name': 'Bank Name',
            'branch_name': 'Branch Name',
            'balance': 'Balance (Tk)',
            'is_active': 'Active',
            'description': 'Description',
        }
        


# class ReceiveVoucherForm(forms.ModelForm):
#     class Meta:
#         model = ReceiveVoucher
#         fields = '__all__'  # include all model fields
#         widgets = {
#             'project_name': forms.Select(attrs={'class': 'form-control'}),
#             'tenant_name': forms.Select(attrs={'class': 'form-control'}),
#             'cash_type': forms.Select(attrs={'class': 'form-control'}),
#             'cheque_number': forms.Select(attrs={'class': 'form-control'}),
#             'bill_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'head_of_account': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
#             'type': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
#             'mr_or_bill_no': forms.TextInput(attrs={'class': 'form-control'}),
#             'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'amount': forms.NumberInput(attrs={'class': 'form-control'}),
#             'generated_amount': forms.NumberInput(attrs={'class': 'form-control'}),
#             'particulars': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'is_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'carrier': forms.TextInput(attrs={'class': 'form-control'}),
#             'rent_bill': forms.Select(attrs={'class': 'form-control'}),
#             'gas_bill': forms.Select(attrs={'class': 'form-control'}),
#             'water_bill': forms.Select(attrs={'class': 'form-control'}),
#             'parking_bill': forms.Select(attrs={'class': 'form-control'}),
#             'service_bill': forms.Select(attrs={'class': 'form-control'}),
#             'electricity_bill': forms.Select(attrs={'class': 'form-control'}),
#             'tenant_advance': forms.Select(attrs={'class': 'form-control'}),
#             'mainbill': forms.Select(attrs={'class': 'form-control'}),
#         }





class ReceiveVoucherForm(forms.ModelForm):
    class Meta:
        model = ReceiveVoucher
        exclude = [
            'particulars',
            'is_confirmed',
            'carrier',
            'rent_bill',
            'gas_bill',
            'water_bill',
            'parking_bill',
            'service_bill',
            'electricity_bill',
            'tenant_advance',
            'mainbill',
        ]  # these fields will not appear in the form
        widgets = {
            'project_name': forms.Select(attrs={'class': 'form-control'}),
            'tenant_name': forms.Select(attrs={'class': 'form-control'}),
            'cash_type': forms.Select(attrs={'class': 'form-control'}),
            'cheque_number': forms.Select(attrs={'class': 'form-control'}),
            'head_of_account': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'mr_or_bill_no': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'generated_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }




# tenant/forms.py
from .models import TenantBulkSMS

class TenantBulkSMSForm(forms.ModelForm):
    class Meta:
        model = TenantBulkSMS
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8
            })
        }