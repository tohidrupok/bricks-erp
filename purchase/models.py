from django.db import models
from projects.models import ProjectFirstLevelName,Suppliers,SiteSupervisor
from accounting.models import CashType, HeadOfAccount,DebitVoucher
from hrm.models import Employee
from crm.models import Customer,CustomerLead
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


class RequisitionCategory(models.Model):
    requi_category_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.requi_category_name}"
    
class HeadOfRequisition(models.Model):
    requi_category = models.ForeignKey(RequisitionCategory, on_delete=models.CASCADE, null=True, blank=True)
    head_requi_name = models.CharField(max_length=255)
    head_requi_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.head_requi_code:
            last_obj = HeadOfRequisition.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.head_requi_code = f"HRQ-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.head_requi_code} - {self.head_requi_name}"



class Requisition(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)

    type = models.CharField(max_length=50, default='')
    vendor_name = models.CharField(max_length=100, null=True, blank=True)  

    unit = models.CharField(max_length=100)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    discount = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=0.00,   
        blank=True, 
        null=True   
    )
    description = models.CharField(max_length=500, default='')
    remark = models.TextField(blank=True, null=True)

    approv_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_note = models.TextField(blank=True, null=True)

    approv_acct_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_acct_note = models.TextField(blank=True, null=True)

    approv_purch_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_purch_note = models.TextField(blank=True, null=True)

    return_requisition = models.CharField(max_length=100, null=True, blank=True)
    requisition_date = models.DateField(null=True, blank=True)
    requi_uniq_id = models.IntegerField(null=True, blank=True)
    purch_appov = models.CharField(max_length=20, null=True, blank=True)
    purch_date = models.DateField(null=True, blank=True)
    purch_id = models.IntegerField(null=True, blank=True)
    return_qty = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    return_status = models.CharField(max_length=20, null=True, blank=True)
    cash_empl = models.CharField(max_length=20, null=True, blank=True)


    # def save(self, *args, **kwargs):
    #     if self.qty and self.rate:
    #         qty = Decimal(str(self.qty))
    #         rate = Decimal(str(self.rate))
    #         # keep 2 decimal places, rounding half up
    #         self.amount = (qty * rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    #     else:
    #         self.amount = Decimal('0.00')
    #     super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        # Convert values safely and ensure 2 decimal places
        qty = Decimal(str(self.qty)) if self.qty else Decimal('0.00')
        rate = Decimal(str(self.rate)) if self.rate else Decimal('0.00')
        discount = Decimal(str(self.discount)) if self.discount else Decimal('0.00')
    
        # Round qty, rate, discount to 2 decimal places just in case
        qty = qty.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        rate = rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount = discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
        # Calculate amount = (qty * rate) - discount, rounded to 2 decimal places
        amount = (qty * rate - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
        # Ensure non-negative
        self.amount = max(amount, Decimal('0.00'))
        self.discount = discount  # ensure discount stored
    
        # Set current date if not provided
        if not self.requisition_date:
            self.requisition_date = timezone.now().date()
    
        super().save(*args, **kwargs)

        
        
    def __str__(self):
        return f"{self.project_name} - {self.item_name} - {self.purch_date}- {self.vendor_name}- {self.requi_uniq_id} - {self.purch_id} - {self.vendor_name}- {self.requisition_date} - {self.amount}"
        



class RequisitionApprovalPayment(models.Model):
    requisition = models.ForeignKey('Requisition', on_delete=models.CASCADE, related_name='approval_payments', null=True, blank=True)
    requi_item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE, null=True, blank=True)
    requi_uniq_id = models.CharField(max_length=50, verbose_name="Requisition Unique ID", null=True, blank=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    payment_type = models.CharField(max_length=50, default='requisition_pay')
    requi_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    debit_voucher = models.ForeignKey(DebitVoucher, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ add this
    requisition_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Requisition Payment #{self.id} - {self.requi_uniq_id} - {self.requisition_date} - {self.requi_amount} - {self.supplier.supplier_name if self.supplier else 'N/A'} - {self.payment_type}"
        
        
        


class BillRequisition(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)

    type = models.CharField(max_length=50, default='')
    vendor_name = models.CharField(max_length=100, null=True, blank=True)  

    unit = models.CharField(max_length=50, default='')
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    remark = models.TextField(blank=True, null=True)
    note = models.CharField(max_length=50, default='')
    head_of_account = models.ForeignKey(HeadOfAccount,on_delete=models.CASCADE,null=True,blank=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True) 

    approv_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_note = models.TextField(blank=True, null=True)

    approv_acct_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_acct_note = models.TextField(blank=True, null=True)

    approv_purch_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_purch_note = models.TextField(blank=True, null=True)

    return_requisition = models.CharField(max_length=100, null=True, blank=True)
    requisition_date = models.DateField(null=True, blank=True)
    requi_uniq_id = models.IntegerField(null=True, blank=True)
    purch_appov = models.CharField(max_length=20, null=True, blank=True)
    purch_date = models.DateField(null=True, blank=True)
    purch_id = models.IntegerField(null=True, blank=True)
    return_qty = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    return_status = models.CharField(max_length=20, null=True, blank=True)
    cash_empl = models.CharField(max_length=20, null=True, blank=True)


    def save(self, *args, **kwargs):
        if self.qty and self.rate:
            # Round to whole number but keep .00
            self.amount = (self.qty * self.rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        else:
            self.amount = Decimal('0.00')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_name} - {self.item_name} - {self.purch_date}- {self.vendor_name}- {self.requi_uniq_id}- {self.vendor_name}- {self.requisition_date} - {self.amount}"
        


class BillRequisitionApprovalPayment(models.Model):
    requisition = models.ForeignKey(
        'BillRequisition', 
        on_delete=models.CASCADE, 
        related_name='approval_bill_payments', 
        null=True, 
        blank=True
    )
    requi_item_name = models.ForeignKey(
        HeadOfRequisition, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    requi_uniq_id = models.CharField(
        max_length=50, 
        verbose_name="BillRequisition Unique ID", 
        null=True, 
        blank=True
    )
    contractors = models.ForeignKey(
        SiteSupervisor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    payment_type = models.CharField(max_length=50, default='requisition_pay')
    requi_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    debit_voucher = models.ForeignKey(DebitVoucher, on_delete=models.SET_NULL, null=True, blank=True)
    requi_id = models.CharField(max_length=50, null=True, blank=True)
    requisition_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        contractor_name = self.contractors.supervisor_name if self.contractors else 'N/A'
        return f"BillRequisition Payment #{self.id} - {self.requi_uniq_id} - {self.requisition_date} - {self.requi_amount} - {contractor_name} - {self.payment_type}"
        

class PettyCash(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)
    unit = models.CharField(max_length=100)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    remark = models.TextField(blank=True, null=True)

    approv_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_note = models.TextField(blank=True, null=True)

    approv_acct_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_acct_note = models.TextField(blank=True, null=True)

    approv_purch_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    approv_purch_note = models.TextField(blank=True, null=True)
    requisition_date = models.DateField(null=True, blank=True)
    requi_uniq_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.qty and self.rate:
            self.amount = self.qty * self.rate
        else:
            self.amount = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_name} - {self.item_name}"
        
        
        

# class Notification(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_sent')
#     recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_received')
#     project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, null=True, blank=True)
#     message = models.TextField()
#     is_read = models.BooleanField(default=False)
#     link = models.URLField(blank=True, null=True)
#     pass_url = models.CharField(max_length=50, blank=True, null=True)
#     created_at = models.DateField(null=True, blank=True)
#     role = models.CharField(max_length=50, choices=(
#         ('admin', 'Admin'),
#         ('accounts', 'Accounts'),
#         ('purchase', 'Purchase')
#     ))

#     def __str__(self):
#         return f"{self.recipient.username} - {self.message[:100]}"






class Notification(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications_received'
    )
    project_name = models.ForeignKey(
        ProjectFirstLevelName, on_delete=models.SET_NULL, null=True, blank=True
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    pass_url = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    role = models.CharField(
        max_length=50,
        choices=(
            ('admin', 'Admin'),
            ('accounts', 'Accounts'),
            ('purchase', 'Purchase'),
        ),
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.message[:40]}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"


class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token[:12]}"

    class Meta:
        verbose_name = "FCM Device"
        verbose_name_plural = "FCM Devices"



# class RequisitionComparative(models.Model):
#     project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
#     employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)    
#     item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)
#     vendor_name = models.ForeignKey(Suppliers, on_delete=models.CASCADE, null=True, blank=True)
#     unit = models.CharField(max_length=100)
#     qty = models.PositiveIntegerField()
#     rate = models.DecimalField(max_digits=10, decimal_places=2)
#     amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
#     remark = models.TextField(blank=True, null=True)
#     approv_status = models.CharField(max_length=20,choices=[
#             ('pending', 'Pending'),
#             ('approved', 'Approved'),
#             ('rejected', 'Rejected')
#         ],
#         default='pending'
#     )
#     approv_note = models.TextField(blank=True, null=True)    
#     return_requisition = models.CharField(max_length=100, null=True, blank=True) 
#     requisition_date = models.DateField(null=True, blank=True)

#     def save(self, *args, **kwargs):
#         if self.qty and self.rate:
#             self.amount = self.qty * self.rate
#         else:
#             self.amount = 0
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.project_name} - {self.item_name}"
    

class RequisitionComparative(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)    
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)
    vendor_name = models.ForeignKey(Suppliers, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.CharField(max_length=100)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    remark = models.TextField(blank=True, null=True)
    approv_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    approv_note = models.TextField(blank=True, null=True)    
    return_requisition = models.CharField(max_length=100, null=True, blank=True) 
    requisition_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.qty and self.rate:
            self.amount = (self.qty * self.rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.amount = Decimal('0.00')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_name} - {self.item_name}"
        

class HeadOfExpense(models.Model):
    head_exp_name = models.CharField(max_length=255)
    head_exp_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.head_exp_code:
            last_obj = HeadOfExpense.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.head_exp_code = f"EXC-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.head_exp_code} - {self.head_exp_name}"
    

class ExpenseVoucher(models.Model):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Bank', 'Bank'),
        ('Expense', 'Expense'),
    ]
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES,default='') 
    expense_name = models.ForeignKey(HeadOfExpense, on_delete=models.SET_NULL, null=True, blank=True)
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    bankName = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True,  blank=True, related_name='Expense_vouchers_as_bank')
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True, related_name='Expense_vouchers_as_cash')
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)    
    date = models.DateField()
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)
    approv_status = models.CharField(max_length=20,choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    approv_note = models.TextField(blank=True, null=True) 
    return_requisition = models.CharField(max_length=100, null=True, blank=True) 
    carrier = models.CharField(max_length=255, blank=True, null=True)
        
    def __str__(self):
        return f"ExpenseVoucher #{self.id} - {self.project_name} - {self.amount}"
        
        
class ExpenseRequisition(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, null=True, blank=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item_name = models.ForeignKey(HeadOfExpense, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    descript = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    approv_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    ledger_add = models.BooleanField(null=True, blank=True)
    approv_note = models.TextField(blank=True, null=True)
    requi_expense_id = models.IntegerField(null=True, blank=True)
    requisition_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    
    
    def __str__(self):
            return f"{self.project_name} - {self.item_name} - {self.descript}- {self.requisition_date} - {self.amount}"