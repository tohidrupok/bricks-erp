from django.db import models
from projects.models import ProjectFirstLevelName,SiteSupervisor,Suppliers
from purchase.models import HeadOfExpense 
from restahrm.models import RestaurantEmployee
from restaurant.models import RestaurantSupplier,RestExpense,RestPurchaseCost,RestaurantSupplier
from crm.models import Customer,CustomerLead
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.dispatch import receiver 
from django.db.models.signals import post_save
from decimal import Decimal

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CashRestType(BaseModel):
    cash_type_name = models.CharField(max_length=100) 
    type_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type_note = models.CharField(max_length=255, default='')
    account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.cash_type_name
        
        


class RestMainChequeBook(models.Model):
    account = models.ForeignKey(CashRestType, on_delete=models.CASCADE, related_name='cheque_books')
    book_name = models.CharField(max_length=100)
    book_number = models.CharField(max_length=50, unique=True)
    start_number = models.PositiveIntegerField()
    end_number = models.PositiveIntegerField()
    total_cheques = models.PositiveIntegerField(blank=True, null=True)
    issue_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # calculate total_cheques automatically
        if not self.total_cheques:
            self.total_cheques = (self.end_number - self.start_number) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book_name} ({self.book_number}) - {self.account.cash_type_name}"

    class Meta:
        ordering = ['-issue_date']


class RestMainCheque(models.Model):
    STATUS_CHOICES = [
        ('unused', 'Unused'),
        ('used', 'Used'),
        ('issued', 'Issued'),
        ('discount', 'Discount'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
    ]

    cheque_book = models.ForeignKey(RestMainChequeBook, on_delete=models.CASCADE, related_name='cheques')
    cheque_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(blank=True, null=True)
    payee_name = models.CharField(max_length=150, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unused')
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cheque_number} ({self.status.capitalize()})"

    class Meta:
        ordering = ['cheque_number']


@receiver(post_save, sender=RestMainChequeBook)
def create_cheques_for_book(sender, instance, created, **kwargs):
    if created:
        cheque_list = []
        for number in range(instance.start_number, instance.end_number + 1):
            cheque_list.append(
                RestMainCheque(cheque_book=instance, cheque_number=str(number))
            )
        RestMainCheque.objects.bulk_create(cheque_list)
        


class SalesRestType(BaseModel):
    sales_type_name = models.CharField(max_length=100) 
    type_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type_note = models.CharField(max_length=255, default='')
    account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.sales_type_name
        
        
class RestHeadOfAccount(BaseModel):
    head_name = models.CharField(max_length=255)
    head_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.head_code:
            last = RestHeadOfAccount.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.head_code = f"HAC-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.head_code} - {self.head_name}"
        
    def get_transaction_type(self):
        return self.head_name.split()[0] 


STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)

class CapitalRestAccount(models.Model):
    head_of_account = models.ForeignKey('RestHeadOfAccount', on_delete=models.CASCADE)
    person_name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    note = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='capital_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.person_name} - {self.head_of_account.head_name} (Tk. {self.amount})"
        
        
        
class CreditRestVoucher(BaseModel):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100)  
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(RestaurantSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    lead_name = models.ForeignKey(CustomerLead, on_delete=models.SET_NULL, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True) 
    capi_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_capt')
    reve_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_reve')
    invest_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_invt')
    others = models.CharField(max_length=255, blank=True, null=True) 
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)  
    bill_date = models.DateField(null=True, blank=True)
    head_of_account = models.ForeignKey(RestHeadOfAccount, on_delete=models.SET_NULL, null=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)  
    date = models.DateField()  
    amount = models.DecimalField(max_digits=12, decimal_places=2) 
    particulars = models.TextField() 
    is_confirmed = models.BooleanField(default=False) 
    approval_cr_status = models.BooleanField(default=False)  
    carrier = models.CharField(max_length=255, blank=True, null=True)
    reqs_id = models.IntegerField(null=True, blank=True)
    res_status = models.CharField(max_length=255, blank=True, null=True)
    create_cr = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"RestCreditVoucher #{self.id} - {self.project_name} - {self.customer_name} - {self.amount} - {self.date} - {self.cash_type}"




class Collection(models.Model):

    TYPE_CHOICES = [
        ('Customer', 'Customer'),
        ('Employee', 'Employee'),
    ]

    date = models.DateField()
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    employee = models.ForeignKey(RestaurantEmployee, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    sales_type = models.ForeignKey(SalesRestType, on_delete=models.SET_NULL, null=True, related_name='collection_sales')
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True, related_name='collection_cash')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cret_id = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} | {self.project} | {self.amount}"



class DailyPayment(models.Model):
    TYPE_CHOICES = [
        ('Expense', 'Expense'),
        ('Purchase', 'Purchase'),
    ]
    date = models.DateField()
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    rest_exp = models.ForeignKey(RestExpense, on_delete=models.CASCADE, null=True, blank=True)
    pur_cost = models.ForeignKey(RestPurchaseCost, on_delete=models.SET_NULL, null=True, blank=True)
    sales_type = models.ForeignKey(SalesRestType, on_delete=models.SET_NULL, null=True, related_name='daily_payment_sales')
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True, related_name='daily_payment_cash')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pay_id = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.date} | {self.project} | {self.amount}"




class DebitRestVoucher(BaseModel):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Expense', 'Expense'),
        ('Employee', 'Employee'),
        ('Customer', 'Customer'),
        ('Capital', 'Capital'),
        ('Revenue', 'Revenue'),
        ('Investment', 'Investment'),
        ('Purchase', 'Purchase'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES) 
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(RestaurantSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey(RestExpense, on_delete=models.CASCADE, null=True, blank=True)
    purchase = models.ForeignKey(RestPurchaseCost, on_delete=models.CASCADE, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True) 
    capi_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='rest_debit_captal_vr')
    invest_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='rest_debit_invest_vr')
    reve_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='rest_debit_reve_vr')
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    bill_phase = models.CharField(max_length=100, null=True, blank=True)  
    bill_date = models.DateField(null=True, blank=True)
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)      
    head_of_account = models.ForeignKey(RestHeadOfAccount, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)    
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    date = models.DateField()
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)
    advance_pay = models.BooleanField(default=False)
    approval_dr_status = models.BooleanField(null=True, blank=True)
    requi_id = models.IntegerField(null=True, blank=True)
    return_requisition = models.CharField(max_length=100, null=True, blank=True) 
    carrier = models.CharField(max_length=255, blank=True, null=True)
    create_dr = models.CharField(max_length=255, blank=True, null=True)

   
        
    def __str__(self):
        return f"DebitRestVoucher #- {self.project_name} - {self.type} - {self.empl_name} - {self.amount} - {self.purchase}"
        
        
        


class LedgerRestEntry(models.Model):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Bank', 'Bank'),
        ('Expense', 'Expense'),
        ('Purchase', 'Purchase'),
        ('Capital', 'Capital'),
        ('Revenue', 'Revenue'),
        ('Investment', 'Investment'),
        ('Employee', 'Employee'),
        ('Balance_Trf', 'Balance_Trf'),
        
    ]
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES,default='') 
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(RestaurantSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    bankName = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_vouchers_as_bank')
    capi_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_capital_vr')
    reve_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_revenue_vr')
    exp_name = models.ForeignKey(RestExpense, on_delete=models.SET_NULL, null=True, blank=True)
    purchase = models.ForeignKey(RestPurchaseCost, on_delete=models.CASCADE, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True)
    invest_name = models.ForeignKey('CapitalRestAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_invest_vr')
    balance_trf = models.CharField(max_length=100, null=True, blank=True)
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True, related_name='ledger_vouchers_as_cash')
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True) 
    head = models.ForeignKey(RestHeadOfAccount, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField(blank=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    carrier = models.CharField(max_length=255, blank=True, null=True) 
    entry_date = models.DateField(null=True, blank=True)
    loan_status = models.CharField(max_length=255, blank=True, null=True)
    tbl_id = models.CharField(max_length=255, blank=True, null=True)
    tbl_name = models.CharField(max_length=255, blank=True, null=True)


    def save(self, *args, **kwargs):

        if self.type == "Contructor" and self.contructor:
            self.type_name = self.contructor.supervisor_name
    
        elif self.type == "Vendor" and self.vendor:
            self.type_name = self.vendor.rest_supplier_name   # FIXED
    
        elif self.type == "Customer" and self.customer_name:
            self.type_name = self.customer_name.customer_name
    
        elif self.type == "Bank" and self.bankName:
            self.type_name = self.bankName.cash_type_name
    
        elif self.type == "Expense" and self.exp_name:
            self.type_name = self.exp_name.expense_name
        
        elif self.type == "Purchase" and self.purchase:
            self.type_name = self.purchase.pur_cost_name
    
        elif self.type != "Expense":
            self.type_name = self.get_type_display()
    
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type} - {self.head.head_name} - {self.date} - {self.cash_type}  - {self.debit} - {self.credit} - {self.type_name}  - {self.loan_status} - {self.type} - {self.purchase}"




class RestTransactionHistory(models.Model):
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=100, blank=True, null=True) 
    head_of_account = models.ForeignKey(RestHeadOfAccount, on_delete=models.SET_NULL, null=True)
    cash_type = models.ForeignKey(CashRestType, on_delete=models.SET_NULL, null=True)  
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    reference = models.CharField(max_length=100, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)
    particulars = models.TextField(null=True, blank=True)
    tbl_id = models.CharField(max_length=255, blank=True, null=True)
    tbl_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.project.project_first_name} - {self.transaction_type} - {self.amount}"
        
        
        
class RestLoanVoucher(BaseModel):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    source_name = models.ForeignKey(RestExpense, on_delete=models.SET_NULL, null=True, blank=True, related_name='rest_Loan_voucher_sn')
    type = models.CharField(max_length=100)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    conductor_name = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    expense_name = models.ForeignKey(RestExpense, on_delete=models.SET_NULL, null=True, blank=True, related_name='rest_Loan_voucher_dn')
    purchase_name = models.ForeignKey(RestPurchaseCost, on_delete=models.SET_NULL, null=True, blank=True)
    vendor_name = models.ForeignKey(RestaurantSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True)
    
    bankName = models.ForeignKey(
        CashRestType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_vouchers_as_bank'  # changed to avoid clash
    )
    
    cash_type = models.ForeignKey(
        CashRestType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_vouchers_as_cash'  # changed to avoid clash
    )
    
    mr_or_bill_no = models.CharField(max_length=100)
    headAcct = models.ForeignKey(RestHeadOfAccount, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)
    carrier = models.CharField(max_length=255, blank=True, null=True)
    loan_status = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"RestLoanVoucher #{self.id} - {self.project_name} - {self.customer_name} - {self.amount} - {self.type} - {self.date} - {self.cash_type}"


class RestBalanceTransfer(BaseModel):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    source_type = models.ForeignKey(CashRestType, related_name='rest_transfers_out', on_delete=models.CASCADE)
    destination_type = models.ForeignKey(CashRestType, related_name='rest_transfers_in', on_delete=models.CASCADE)
    transfer_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transfer_date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)
    cheque_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.source_type} → {self.destination_type} : {self.transfer_amount}"

    # def save(self, *args, **kwargs):
    #     # If the object is being created (not updated)
    #     is_new = self._state.adding

    #     if is_new:
    #         try:
    #             # Debit from source
    #             source = CashRestType.objects.select_for_update().get(id=self.source_type.id)
    #             if source.type_amount < self.transfer_amount:
    #                 raise ValidationError("Insufficient balance in Source Cash Type.")
    #             source.type_amount -= self.transfer_amount
    #             source.type_note = f"Debited {self.transfer_amount} on BalanceTransfer"
    #             source.save()

    #             # Credit to destination
    #             dest = CashRestType.objects.select_for_update().get(id=self.destination_type.id)
    #             dest.type_amount += self.transfer_amount
    #             dest.type_note = f"Credited {self.transfer_amount} on BalanceTransfer"
    #             dest.save()
    #         except CashRestType.DoesNotExist:
    #             raise ValidationError("Invalid Cash Type selected.")
    #     super().save(*args, **kwargs)

