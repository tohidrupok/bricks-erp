from django import forms
from django.utils import timezone
from .models import RestaurantEmployee,RestaurantSalaryVoucher,RestaurantAttendance,RestaurantAdvancePayment,RestaurantFoodBillPayment,RestaurantPayroll, RestIom, RestaurantPayslip, RestaurantLeave,RestaurantAllowances,RestaurantSalaryPayment,RestaurantLoanPayment,RestaurantSalaryVoucher,RestaurantShiftSchedule

class RestaurantEmployeeForm(forms.ModelForm):
    class Meta:
        model = RestaurantEmployee
        fields = '__all__'
        widgets = {
            'rda_emp_type': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md placeholder:text-slate-400/90 focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary',
            }),
        }
        
        
class RestaurantSalaryVoucherForm(forms.ModelForm):
    class Meta:
        model = RestaurantSalaryVoucher
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
        
        
        
class RestaurantAttendanceForm(forms.ModelForm):
    class Meta:
        model = RestaurantAttendance
        fields = ['employee', 'emp_shift', 'date', 'check_in', 'check_out', 'att_status']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'emp_shift': forms.Select(attrs={
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


class RestaurantAttendanceCheckoutForm(forms.ModelForm):
    class Meta:
        model = RestaurantAttendance
        fields = ['check_out']
        widgets = {
            'check_out': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
        }
        
        

class RestaurantAttendanceUploadForm(forms.Form):
    file = forms.FileField(
        label='Upload CSV',
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-slate-700 border border-slate-300 rounded-md'
        })
    )
    

class RestaurantPayrollForm(forms.ModelForm):
    class Meta:
        model = RestaurantPayroll
        fields = ['employee', 'month', 'year', 'basic_salary', 'allowances', 'deductions', 'net_salary']


class RestaurantPayslipForm(forms.ModelForm):
    class Meta:
        model = RestaurantPayslip
        fields = ['payroll', 'notes']


  
    
class RestaurantAdvancePaymentForm(forms.ModelForm):
    class Meta:
        model = RestaurantAdvancePayment
        fields = ['project_name','employee', 'date', 'cash_type','cheque_number', 'head_of_account','amount', 'reason', 'status','debit_voucher']
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
    
    
# class RestaurantSalaryPaymentForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantSalaryPayment
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
        
        

class RestaurantSalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = RestaurantSalaryPayment
        fields = [
            'project_name','employee', 'date', 'cash_type',
            'cheque_number', 'head_of_account','monthofsalary',
            'amount', 'reason'
        ]
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'cheque_number': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'monthofsalary': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ ONLY ACTIVE EMPLOYEES
        self.fields['employee'].queryset = RestaurantEmployee.objects.filter(
            rda_active_status=True
        )
        

class RestaurantFoodBillPaymentForm(forms.ModelForm):
    class Meta:
        model = RestaurantFoodBillPayment
        fields = [
            'customer_type',
            'project_name',
            'employee',
            'customer_name',
            'date',
            'cash_type',
            'cheque_number',
            'head_of_account',
            'monthofsalary',
            'amount',
            'reason'
        ]

        widgets = {
            'customer_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'customer_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'cash_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'cheque_number': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'head_of_account': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'monthofsalary': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 3}),
        }
        
        
        
class RestaurantAllowancesForm(forms.ModelForm):
    class Meta:
        model = RestaurantAllowances
        fields = ['project_name','employee', 'date','amount', 'reason', 'status']
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'reason': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }



# from django import forms
# from .models import RestaurantLeave, RestaurantEmployee


# class RestaurantLeaveForm(forms.ModelForm):
#     class Meta:
#         model = RestaurantLeave
#         fields = ['employee', 'start_date', 'end_date', 'device_sn', 'reason', 'approved']
#         widgets = {
#             'start_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'end_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'device_sn': forms.Select(attrs={   # <-- CHANGE HERE
#                 'class': 'form-select w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'reason': forms.Textarea(attrs={
#                 'rows': 3,
#                 'class': 'form-textarea w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#         }

#     def __init__(self, *args, department=None, **kwargs):
#         """
#         department: optional argument from view (e.g., request.session.get('department'))
#         """
#         super().__init__(*args, **kwargs)  # ✅ FIXED

#         # Exclude Admin & inactive employees
#         self.fields['employee'].queryset = RestaurantEmployee.objects.exclude(
#             rda_emp_name__iexact='Admin'
#         ).filter(rda_active_status=True)

#         # Show employee name + position in dropdown
#         self.fields['employee'].label_from_instance = (
#             lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"
#         )

#         # Hide approval field for non-admin users
#         if department != 'admin':
#             self.fields['approved'].widget = forms.HiddenInput()
#             self.initial.setdefault('approved', False)

            

from django import forms
from .models import RestaurantLeave, RestaurantLeaveAllocation, RestaurantEmployee

class RestaurantLeaveForm(forms.ModelForm):
    class Meta:
        model = RestaurantLeave
        fields = [
            'employee', 'leave_type', 'start_date', 'end_date', 
            'device_sn', 'handover_person', 'medical_certificate', 
            'reason', 'approved'
        ]
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
            'device_sn': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'handover_person': forms.Select(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'medical_certificate': forms.FileInput(attrs={
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Exclude Admin & inactive employees
        active_emps = RestaurantEmployee.objects.exclude(
            rda_emp_name__iexact='Admin'
        ).filter(rda_active_status=True)

        self.fields['employee'].queryset = active_emps
        self.fields['handover_person'].queryset = active_emps

        # Custom label display
        self.fields['employee'].label_from_instance = (
            lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"
        )
        self.fields['handover_person'].label_from_instance = (
            lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"
        )

        # Hide approval field for non-admin users
        if department != 'admin':
            self.fields['approved'].widget = forms.HiddenInput()
            self.initial.setdefault('approved', False)


class RestaurantLeaveAllocationForm(forms.ModelForm):
    class Meta:
        model = RestaurantLeaveAllocation
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
        self.fields['employee'].queryset = RestaurantEmployee.objects.filter(rda_active_status=True)
        
        


class RestaurantLoanPaymentForm(forms.ModelForm):
    class Meta:
        model = RestaurantLoanPayment
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




class RestaurantShiftScheduleForm(forms.ModelForm):
    
    class Meta:
        model = RestaurantShiftSchedule
        fields = ["shift_name", "checkin_time", "checkout_time"]

        labels = {
            "shift_name": "Shift Name",
            "checkin_time": "Check-in Time",
            "checkout_time": "Check-out Time",
        }

        widgets = {
            "shift_name": forms.Select(
                attrs={"class": "border rounded px-3 py-2 w-full"}
            ),
            "checkin_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "border rounded px-3 py-2 w-full"
                },
            ),
            "checkout_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "border rounded px-3 py-2 w-full"
                },
            ),
        }




# class RestIomForm(forms.ModelForm):
#     class Meta:
#         model = RestIom
#         fields = ['employee', 'start_date', 'end_date', 'device_sn', 'check_in', 'check_out', 'reason', 'approved']
#         widgets = {
#             'start_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'end_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
#             }),
#             'device_sn': forms.Select(attrs={   # <-- CHANGE HERE
#                 'class': 'form-select w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
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

#         # Exclude Admin employees and only active
#         self.fields['employee'].queryset = RestaurantEmployee.objects.exclude(
#             rda_emp_name__iexact='Admin'
#         ).filter(rda_active_status=True)

#         # Show employee with position in dropdown
#         self.fields['employee'].label_from_instance = lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"

#         # Hide approved field for non-admins
#         if department != 'admin':
#             self.fields['approved'].widget = forms.HiddenInput()
#             self.initial['approved'] = False




from datetime import time
from django.utils import timezone

class RestIomForm(forms.ModelForm):
    class Meta:
        model = RestIom
        fields = ['employee', 'start_date', 'end_date', 'device_sn', 'check_in', 'check_out', 'reason', 'approved']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'device_sn': forms.Select(attrs={
                'class': 'form-select w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'check_in': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'check_out': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-input w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea w-full border-slate-200 shadow-sm rounded-md focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary'
            }),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Exclude Admin employees and only active
        self.fields['employee'].queryset = RestaurantEmployee.objects.exclude(
            rda_emp_name__iexact='Admin'
        ).filter(rda_active_status=True)

        # Show employee with position
        self.fields['employee'].label_from_instance = lambda obj: f"{obj.rda_emp_name} ({obj.rda_position})"

        # Hide approved field for non-admins
        if department != 'admin':
            self.fields['approved'].widget = forms.HiddenInput()
            self.initial.setdefault('approved', False)

        # ✅ DEFAULT VALUES
        if not self.is_bound:
            today = timezone.localdate()

            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today

            self.fields['check_in'].initial = time(9, 0)    # 09:00 AM
            self.fields['check_out'].initial = time(23, 59) # 23:59 (11:59 PM)