from django.db import models
from django.contrib.auth.models import User
from accounting.models import CashType
from django.utils import timezone
import calendar
from django.core.exceptions import ValidationError
from datetime import date, timedelta

EMP_TYPE_CHOICES = [
    ('employee', 'Employee'),
    ('accounts', 'Accounts'),
    ('purchase', 'Purchase'),
    ('hrm', 'HRM'),
    ('admin', 'Admin'),
    ('engineer', 'Engineer'),
    ('restaurant', 'Restaurant'),
    ('tenant', 'Tenant'),
    ('designer', 'Designer'),
    ('manager', 'Manager'),
]

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    emp_name = models.CharField(max_length=100, default='')
    employee_name = models.CharField(max_length=100)
    emp_type = models.CharField(max_length=20, choices=EMP_TYPE_CHOICES, default='employee')
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    nid = models.CharField(max_length=20)
    position = models.CharField(max_length=100)
    address = models.TextField()
    active_status = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.employee_name




class RdaEmployee(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='rda_employee',
        null=True,
        blank=True)
    rda_emp_name = models.CharField(max_length=100)
    rda_emp_type = models.CharField(max_length=20)
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    rda_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rda_phone = models.CharField(max_length=50)
    rda_email = models.EmailField()
    rda_position = models.CharField(max_length=100)
    rda_address = models.TextField()
    rda_nid = models.CharField(max_length=100, default='') 
    rda_dofb = models.CharField(max_length=100, default='')
    rda_active_status = models.BooleanField(default=True)
    rda_photo = models.ImageField(upload_to='rda_emp_photos/', blank=True, null=True)

    def __str__(self):
        return self.rda_emp_name
        


class RdaPayEmpSalary(models.Model):
    rda_emp_name = models.ForeignKey('hrm.RdaEmployee', on_delete=models.SET_NULL, null=True)
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    rda_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rda_pay_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rda_absent_days = models.IntegerField(default=0)
    pay_date = models.DateField()

    def __str__(self):
        return f"{self.rda_emp_name} - {self.pay_date}"
        
        
        
class Attendance(models.Model):
    ATTENDANCE_STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
        ('Off Day', 'Off Day'),
    ]
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    att_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='Present'
    )

    def __str__(self):
        return f"{self.employee} - {self.date}"


from django.conf import settings
from django.utils import timezone

from .models import Attendance   # already in same file, no import needed if same file


class AttendanceLocation(models.Model):
    attendance = models.OneToOneField(
        Attendance, on_delete=models.CASCADE, related_name='location_info'
    )

    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='verified_hrm_attendance_locations'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [
            ('can_verify_attendance_location', 'Can verify HRM attendance location'),
        ]

    def __str__(self):
        return f"Location for {self.attendance}"
        
        


class AttendanceAccessControl(models.Model):
    """Admin uses this to allow/select which employees can access
    the public attendance punch page. Existing models are untouched."""
    name = models.CharField(max_length=100, default='BTP Office Attendance Access')
    allowed_employees = models.ManyToManyField(
        RdaEmployee, blank=True, related_name='attendance_allowed'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
        
        
class Payroll(models.Model):
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.employee} - {self.month} {self.year}"

class Payslip(models.Model):
    payroll = models.OneToOneField(Payroll, on_delete=models.CASCADE)
    generated_on = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payslip for {self.payroll}"

class AdvancePayment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('due', 'Due'),
    ]
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    employee = models.ForeignKey('hrm.RdaEmployee', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    cash_type = models.ForeignKey(CashType, on_delete=models.CASCADE, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    head_of_account = models.ForeignKey('accounting.HeadOfAccount', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='due')

    def __str__(self):
        return f"Advance to {self.employee} on {self.date}"


class SalaryPayment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('due', 'Due'),
    ]
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    employee = models.ForeignKey('hrm.RdaEmployee', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    cash_type = models.ForeignKey(CashType, on_delete=models.CASCADE, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    head_of_account = models.ForeignKey('accounting.HeadOfAccount', on_delete=models.SET_NULL, null=True)
    monthofsalary = models.CharField(max_length=100, null=True, blank=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()

    def __str__(self):
        return f"Advance to {self.employee} on {self.date}"
        
        

class Allowances(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('due', 'Due'),
        ('approved', 'Approved'), 
    ]
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='due')

    def __str__(self):
        return f"Allowances to {self.employee} on {self.date}"
        

# class Leave(models.Model):
#     employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     reason = models.TextField()
#     approved = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Leave: {self.employee} from {self.start_date} to {self.end_date}"
        


class LeaveAllocation(models.Model):
    """
    Tracks yearly allocations according to Policy:
    CL = 10, SL = 10, EL = 15 (Max Carry Forward 30)
    """
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE, related_name='leave_allocations')
    year = models.PositiveIntegerField(default=date.today().year)
    
    casual_leave_allocated = models.FloatField(default=10.0)
    casual_leave_used = models.FloatField(default=0.0)
    
    sick_leave_allocated = models.FloatField(default=10.0)
    sick_leave_used = models.FloatField(default=0.0)
    
    earned_leave_allocated = models.FloatField(default=15.0)
    earned_leave_carried_forward = models.FloatField(default=0.0)  # Capped at 30 max
    earned_leave_used = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('employee', 'year')

    @property
    def remaining_casual_leave(self):
        return max(0.0, self.casual_leave_allocated - self.casual_leave_used)

    @property
    def remaining_sick_leave(self):
        return max(0.0, self.sick_leave_allocated - self.sick_leave_used)

    @property
    def total_earned_leave(self):
        return min(30.0, self.earned_leave_carried_forward + self.earned_leave_allocated)

    @property
    def remaining_earned_leave(self):
        return max(0.0, self.total_earned_leave - self.earned_leave_used)

    def __str__(self):
        return f"Leave Balance ({self.year}) - {self.employee.rda_emp_name}"


class Leave(models.Model):
    LEAVE_TYPES = [
        ('CL', 'Casual Leave (CL)'),
        ('SL', 'Sick Leave (SL)'),
        ('EL', 'Earned Leave (EL)'),
        ('LOP', 'Loss of Pay (LOP)'),
    ]

    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES, default='CL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    handover_person = models.ForeignKey(RdaEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='handover_tasks')
    medical_certificate = models.FileField(upload_to='leave_docs/', null=True, blank=True)
    approved = models.BooleanField(default=False)

    @property
    def total_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End Date cannot be earlier than Start Date.")

        # Sick Leave policy rule: medical cert required if > 3 days
        if self.leave_type == 'SL' and self.total_days > 3 and not self.medical_certificate:
            raise ValidationError("Medical certificate is mandatory for Sick Leave over 3 days.")

    def __str__(self):
        return f"Leave: {self.employee} from {self.start_date} to {self.end_date}"
        
        

class Iom(models.Model):
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Leave: {self.employee} from {self.start_date} to {self.check_in}"
        
        

class LoanPayment(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('due', 'Due'),
    ]

    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    employee = models.ForeignKey('hrm.RdaEmployee', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    cash_type = models.ForeignKey(CashType, on_delete=models.CASCADE, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)
    head_of_account = models.ForeignKey('accounting.HeadOfAccount', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_month = models.DateField()
    end_month = models.DateField()
    month_name = models.CharField(max_length=500, null=True, blank=True)  # allow long text
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='due')

    def save(self, *args, **kwargs):
        if self.start_month and self.end_month:
            months = []
            current = self.start_month.replace(day=1)
            end = self.end_month.replace(day=1)

            while current <= end:
                months.append(f"{calendar.month_name[current.month]} {current.year}")
                # go to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            self.month_name = ", ".join(months)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Loan to {self.employee} on {self.date}"
        
        
        
class UserBreak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    is_on_break = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'On Break' if self.is_on_break else 'Working'}"
        
        



class SalaryVoucher(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
    ]
    project = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.SET_NULL, null=True)
    month_name = models.CharField(max_length=20)   # Example: "August 2025"
    generate_date = models.DateTimeField(default=timezone.now)

    approval_salary_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"{self.project} - {self.month_name} ({self.approval_salary_status})"
        


class Note(models.Model):
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField()
    
    def __str__(self):
        return f"Leave: {self.employee} from {self.date}"
