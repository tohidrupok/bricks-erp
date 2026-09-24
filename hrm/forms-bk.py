
from django.contrib.auth.models import User, Group, Permission
from django import forms
from django.utils import timezone
from .models import Employee,Attendance,Payroll, Payslip, AdvancePayment, Leave,Allowances,SalaryPayment,RdaEmployee,UserBreak,LoanPayment,SalaryVoucher,Iom,Note,RdaPayEmpSalary
import re


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Username")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name = forms.CharField(max_length=150, label="Last Name", required=False)
    is_active = forms.BooleanField(required=False, initial=True)
    is_staff = forms.BooleanField(required=False, initial=False)
    is_superuser = forms.BooleanField(required=False, initial=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded'})
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded'})
    )

    class Meta:
        model = Employee
        fields = [
           'emp_name','employee_name', 'emp_type', 'project_name', 'salary','phone', 'email', 'nid', 'position',
            'address', 'active_status', 'photo','password'
        ]
        widgets = {
            'emp_type': forms.Select(attrs={'class': 'w-full border rounded'}),
        }
        
        
    def clean_phone(self):
        phone_input = self.cleaned_data.get('phone', '')
        phones = [p.strip() for p in phone_input.split(',') if p.strip()]

        if len(phones) > 3:
            raise forms.ValidationError("You can only enter up to 3 phone numbers separated by commas.")

        pattern = re.compile(r'^(?:\+88|88)?01[3-9]\d{8}$')
        for phone in phones:
            if not pattern.match(phone):
                raise forms.ValidationError(f"Invalid phone number format: {phone}")

        return ', '.join(phones)
        

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.") 
        return cleaned_data

    def save(self, commit=True):       
        employee = super().save(commit=False)
        
        # Check if user exists or create new user
        username = self.cleaned_data['username']
        password = self.cleaned_data['password1']
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data.get('last_name', '')
        is_active = self.cleaned_data['is_active']
        is_staff = self.cleaned_data['is_staff']
        is_superuser = self.cleaned_data['is_superuser']
        groups = self.cleaned_data['groups']
        user_permissions = self.cleaned_data['user_permissions']

        user = None
        if employee.user:
            # Update existing user
            user = employee.user
            user.username = username
            if password:
                user.set_password(password)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
       
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
       
        employee.user = user
       
        if password:
            employee.password = password

        if commit:
            employee.save()
        return employee


class MyUserForm(forms.Form):
    username = forms.CharField(required=True)
    first_name = forms.CharField(required=True)

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'groups', 'user_permissions', 'is_active']  # include is_active
        widgets = {
            'password': forms.PasswordInput(),
        }




class EmployeeAllowanceUpdateForm(forms.ModelForm):
    # Show current password (read-only)
    current_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full',
            'readonly': 'readonly'
        })
    )

    # Fields for setting new password
    password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input w-full'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input w-full'})
    )

    class Meta:
        model = Employee
        fields = ['photo', 'salary', 'active_status']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-input w-full'}),
            'salary': forms.NumberInput(attrs={'class': 'form-input w-full'}),            
            'active_status': forms.Select(choices=[(True, 'Active'), (False, 'Inactive')], attrs={'class': 'form-input w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.password:
            self.fields['current_password'].initial = self.instance.password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data



class EmployeePhotoUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['photo']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-input w-full'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # You can optionally validate file type or size here
        return cleaned_data




class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'att_status']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'check_in': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'check_out': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'att_status': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
        }


class AttendanceCheckoutForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['check_out']
        widgets = {
            'check_out': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
        }
        
        

class AttendanceUploadForm(forms.Form):
    file = forms.FileField(
        label='Upload CSV',
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-slate-700 border border-slate-300 rounded-md'
        })
    )
    
    
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'month', 'year', 'basic_salary', 'allowances', 'deductions', 'net_salary']


class PayslipForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['payroll', 'notes']


class AdvancePaymentForm(forms.ModelForm):
    class Meta:
        model = AdvancePayment
        fields = ['project_name','employee', 'date', 'cash_type','cheque_number', 'head_of_account','amount', 'reason', 'status']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'cheque_number': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }


# class SalaryPaymentForm(forms.ModelForm):
#     class Meta:
#         model = SalaryPayment
#         fields = ['project_name','employee', 'date', 'cash_type','cheque_number', 'head_of_account','monthofsalary','amount', 'reason']
#         widgets = {
#             'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
#             'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'cheque_number': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'monthofsalary': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
#             'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
#         }
        


class SalaryPaymentForm(forms.ModelForm):
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ]
    
    monthofsalary = forms.ChoiceField(
        choices=[('', 'Select Month')] + MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full border border-slate-300 shadow-sm rounded-md p-2', 'id': 'id_monthofsalary'})
    )

    class Meta:
        model = SalaryPayment
        fields = ['project_name', 'employee', 'date', 'cash_type', 'cheque_number', 'head_of_account', 'monthofsalary', 'amount', 'reason']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2', 'id': 'id_project_name'}),
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2', 'id': 'id_employee'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'cheque_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2', 'placeholder': 'Enter Cheque Number'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            
            # Ensure 'amount' is an editable NumberInput without any readonly attributes
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border border-slate-300 shadow-sm rounded-md p-2', 
                'placeholder': 'Enter Amount',
                'step': '0.01'
            }),
            
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = RdaEmployee.objects.filter(rda_active_status=True)



class AllowancesForm(forms.ModelForm):
    class Meta:
        model = Allowances
        fields = ['project_name','employee', 'date', 'amount', 'reason', 'status']
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }

        



class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'handover_person', 'reason', 'medical_certificate', 'approved']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'leave_type': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'handover_person': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'medical_certificate': forms.FileInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
        }

    def __init__(self, *args, **kwargs):
        department = kwargs.pop('department', None)
        super().__init__(*args, **kwargs)
        # Filter active employees
        self.fields['employee'].queryset = RdaEmployee.objects.filter(rda_active_status=True)
        self.fields['handover_person'].queryset = RdaEmployee.objects.filter(rda_active_status=True)
        


from django import forms
from .models import Leave, LeaveAllocation, RdaEmployee

class LeaveAllocationForm(forms.ModelForm):
    class Meta:
        model = LeaveAllocation
        fields = [
            'employee', 'year', 
            'casual_leave_allocated', 'sick_leave_allocated', 
            'earned_leave_allocated', 'earned_leave_carried_forward'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'casual_leave_allocated': forms.NumberInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'sick_leave_allocated': forms.NumberInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'earned_leave_allocated': forms.NumberInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'earned_leave_carried_forward': forms.NumberInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = RdaEmployee.objects.filter(rda_active_status=True)
        


# class IomForm(forms.ModelForm):
#     class Meta:
#         model = Iom
#         fields = ['employee', 'start_date', 'end_date', 'check_in', 'check_out', 'reason', 'approved']
#         widgets = {
#             'start_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'end_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'check_in': forms.TimeInput(attrs={
#                 'type': 'time',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'check_out': forms.TimeInput(attrs={
#                 'type': 'time',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'reason': forms.Textarea(attrs={
#                 'rows': 3,
#                 'class': 'form-textarea w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#         }

#     def __init__(self, *args, department=None, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Exclude Admin
#         self.fields['employee'].queryset = RdaEmployee.objects.exclude(
#             rda_emp_name__iexact='Admin'
#         ).filter(rda_active_status=True)

#         # Show employee with position
#         self.fields['employee'].label_from_instance = lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"

#         # Hide approved field for non-admins
#         if department != 'admin':
#             self.fields['approved'].widget = forms.HiddenInput()
#             self.initial.setdefault('approved', False)
            

from datetime import time

class IomForm(forms.ModelForm):
    class Meta:
        model = Iom
        fields = ['employee', 'start_date', 'end_date', 'check_in', 'check_out', 'reason', 'approved']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['employee'].queryset = RdaEmployee.objects.exclude(
            rda_emp_name__iexact='Admin'
        ).filter(rda_active_status=True)

        self.fields['employee'].label_from_instance = lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"

        if department != 'admin':
            self.fields['approved'].widget = forms.HiddenInput()
            self.initial.setdefault('approved', False)

        # Default values
        if not self.is_bound:
            today = timezone.localdate()
            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today
            self.fields['check_in'].initial = time(10, 0)
            self.fields['check_out'].initial = time(19, 30)
            
            
            
        
class RdaEmployeeForm(forms.ModelForm):
    class Meta:
        model = RdaEmployee
        fields = '__all__'
        widgets = {
            'rda_emp_type': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md placeholder:text-slate-400/90 focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary',
            }),
        }



class RdaPayEmpSalaryForm(forms.ModelForm):
    class Meta:
        model = RdaPayEmpSalary
        fields = '__all__'
        widgets = {
            'rda_emp_type': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md placeholder:text-slate-400/90 focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary',
            }),
        }
        

class LoanPaymentForm(forms.ModelForm):
    class Meta:
        model = LoanPayment
        fields = ['project_name','employee', 'date', 'cash_type','cheque_number', 'head_of_account','amount','deduction_amount','start_month','end_month','month_name','reason', 'status']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'cheque_number': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2', 'placeholder': 'Enter Loan Amount'}),
            'deduction_amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2', 'placeholder': 'Enter Deduction Amount'}),
            'start_month': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'end_month': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'month_name': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }

class UserBreakForm(forms.ModelForm):
    class Meta:
        model = UserBreak
        fields = ['user', 'break_start', 'break_end', 'is_on_break']
        widgets = {
            'break_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'break_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'is_on_break': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
        }



class SalaryVoucherForm(forms.ModelForm):
    class Meta:
        model = SalaryVoucher
        fields = ['project', 'month_name', 'approval_salary_status']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'month_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., August 2025'
            }),
            'approval_salary_status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['employee', 'date','reason']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
        }