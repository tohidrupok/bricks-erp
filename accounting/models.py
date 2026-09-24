from django.db import models
from projects.models import ProjectFirstLevelName,SiteSupervisor,Suppliers,Donation
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

class CashType(BaseModel):
    cash_type_name = models.CharField(max_length=100) 
    type_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type_note = models.CharField(max_length=255, default='')
    account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.cash_type_name
        
        


class MainChequeBook(models.Model):
    account = models.ForeignKey(CashType, on_delete=models.CASCADE, related_name='cheque_books')
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


class MainCheque(models.Model):
    STATUS_CHOICES = [
        ('unused', 'Unused'),
        ('used', 'Used'),
        ('issued', 'Issued'),
        ('discount', 'Discount'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
    ]

    cheque_book = models.ForeignKey(MainChequeBook, on_delete=models.CASCADE, related_name='cheques')
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


@receiver(post_save, sender=MainChequeBook)
def create_cheques_for_book(sender, instance, created, **kwargs):
    if created:
        cheque_list = []
        for number in range(instance.start_number, instance.end_number + 1):
            cheque_list.append(
                MainCheque(cheque_book=instance, cheque_number=str(number))
            )
        MainCheque.objects.bulk_create(cheque_list)




class HeadOfAccount(BaseModel):
    head_name = models.CharField(max_length=255)
    head_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.head_code:
            last = HeadOfAccount.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.head_code = f"HAC-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.head_code} - {self.head_name}"
        
    def get_transaction_type(self):
        return self.head_name.split()[0] 
    


class CreditVoucher(BaseModel):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100)  
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    lead_name = models.ForeignKey(CustomerLead, on_delete=models.SET_NULL, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True) 
    donation_name = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)
    capi_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_capt')
    reve_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_reve')
    invest_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='creditVoucher_invt')
    others = models.CharField(max_length=255, blank=True, null=True) 
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)  
    bill_date = models.DateField(null=True, blank=True)
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)  
    date = models.DateField()  
    amount = models.DecimalField(max_digits=12, decimal_places=2) 
    particulars = models.TextField() 
    is_confirmed = models.BooleanField(default=False) 
    approval_cr_status = models.BooleanField(default=False)  
    carrier = models.CharField(max_length=255, blank=True, null=True)
    create_cr = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"CreditVoucher #{self.id} - {self.project_name} - {self.customer_name} - {self.amount} - {self.date} - {self.cash_type}"



class DebitVoucher(BaseModel):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Expense', 'Expense'),
        ('Employee', 'Employee'),
        ('Customer', 'Customer'),
        ('Capital', 'Capital'),
        ('Revenue', 'Revenue'),
        ('Donation', 'Donation'),
        ('Investment', 'Investment'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES) 
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.CharField(max_length=100, null=True, blank=True) 
    empl_name = models.CharField(max_length=100, null=True, blank=True) 
    capi_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_captal_vr')
    invest_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_invest_vr')
    reve_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_reve_vr')
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    donation_name = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)
    bill_phase = models.CharField(max_length=100, null=True, blank=True)  
    bill_date = models.DateField(null=True, blank=True)
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)      
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
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
        return f"DebitVoucher #{self.id} - {self.project_name} - {self.amount}"
    


# class JournalVoucher(models.Model):
#     date = models.DateField()
#     project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True, related_name='journal_project_dr')
#     head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True, related_name='journal_head_dr')
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     cheque_number = models.CharField(max_length=100, null=True, blank=True, default='')
#     mr_or_bill_no = models.CharField(max_length=100, null=True, blank=True)
#     description = models.TextField(null=True, blank=True)
#     carrier = models.CharField(max_length=100, null=True, blank=True)
#     is_confirmed = models.BooleanField(default=False)
#     party_combined = models.CharField(max_length=100, null=True, blank=True)

#     def __str__(self):
#         return f"JournalVoucher #{self.id} - {self.date}"

class JournalVoucher(models.Model):
    date = models.DateField()
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True, related_name='journal_project_dr')
    
    head_of_account_to = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True, related_name='journal_head_to')
    head_of_account_from = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True, related_name='journal_head_from')

    party_to_combined = models.CharField(max_length=100, null=True, blank=True)
    party_from_combined = models.CharField(max_length=100, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cheque_number = models.CharField(max_length=100, null=True, blank=True, default='')
    mr_or_bill_no = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    carrier = models.CharField(max_length=100, null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"JournalVoucher #{self.id} - {self.date}"



class ContraVoucher(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    TYPE_CHOICES = [
    ('Dr', 'Dr'),
    ('Cr', 'Cr'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Dr')
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Contra Voucher - {self.project_name} - {self.date}"


class LedgerEntry(models.Model):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Bank', 'Bank'),
        ('Expense', 'Expense'),
        ('Capital', 'Capital'),
        ('Revenue', 'Revenue'),
        ('Investment', 'Investment'),
        ('Employee', 'Employee'),
        ('Balance_Trf', 'Balance_Trf'),
        ('Donation', 'Donation'),
        
    ]
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES,default='') 
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    bankName = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_vouchers_as_bank')
    capi_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_capital_vr')
    reve_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_revenue_vr')
    exp_name = models.ForeignKey('purchase.HeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True)
    donation_name = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)
    invest_name = models.ForeignKey('CapitalAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_invest_vr')
    balance_trf = models.CharField(max_length=100, null=True, blank=True)
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True, related_name='ledger_vouchers_as_cash')
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True) 
    head = models.ForeignKey(HeadOfAccount, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField(blank=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    carrier = models.CharField(max_length=255, blank=True, null=True) 
    loan_status = models.CharField(max_length=255, blank=True, null=True)
    tbl_id = models.CharField(max_length=255, blank=True, null=True)
    tbl_name = models.CharField(max_length=255, blank=True, null=True)


    def save(self, *args, **kwargs):
        if self.type == "Contructor" and self.contructor:
            self.type_name = self.contructor.supervisor_name
        elif self.type == "Vendor" and self.vendor:
            self.type_name = self.vendor.supplier_name
        elif self.type == "Customer" and self.customer_name:
            self.type_name = self.customer_name.customer_name
        elif self.type == "Bank" and self.bankName:
            self.type_name = self.bankName.cash_type_name
        elif self.type != "Expense":
            self.type_name = self.get_type_display()
        # else: Do not override type_name for 'Expense'

        super().save(*args, **kwargs)




    def __str__(self):
        return f"{self.type} - {self.head.head_name} - {self.date} - {self.cash_type}  - {self.debit} - {self.credit} - {self.type_name}  - {self.loan_status}"


class TransactionHistory(models.Model):
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=100, blank=True, null=True) 
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)  
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


from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class ProjectBalanceTransfer(models.Model):
    source_project = models.ForeignKey(
        ProjectFirstLevelName,
        on_delete=models.CASCADE,
        related_name='transfers_out'
    )
    destination_project = models.ForeignKey(
        ProjectFirstLevelName,
        on_delete=models.CASCADE,
        related_name='transfers_in'
    )
    source_cash_type = models.ForeignKey(
        CashType,
        on_delete=models.CASCADE,
        related_name='project_transfers_out'
    )
    destination_cash_type = models.ForeignKey(
        CashType,
        on_delete=models.CASCADE,
        related_name='project_transfers_in'
    )
    transfer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    transfer_date = models.DateField(
        default=timezone.now
    )
    note = models.CharField(
        max_length=255,
        blank=True
    )
    cheque_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    carrier = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"[{self.source_project}] {self.source_cash_type} → [{self.destination_project}] {self.destination_cash_type} : {self.transfer_amount}"
        

# class BalanceTransfer(BaseModel):
#     source_type = models.ForeignKey(CashType, related_name='transfers_out', on_delete=models.CASCADE)
#     destination_type = models.ForeignKey(CashType, related_name='transfers_in', on_delete=models.CASCADE)
#     transfer_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     transfer_date = models.DateField(default=timezone.now)
#     note = models.CharField(max_length=255, blank=True)

#     def __str__(self):
#         return f"{self.source_type} → {self.destination_type} : {self.transfer_amount}"

class BalanceTransfer(BaseModel):
    project_name = models.ForeignKey(
        ProjectFirstLevelName,
        on_delete=models.SET_NULL,
        null=True
    )

    source_type = models.ForeignKey(
        CashType,
        related_name='transfers_out',
        on_delete=models.CASCADE
    )

    destination_type = models.ForeignKey(
        CashType,
        related_name='transfers_in',
        on_delete=models.CASCADE
    )

    transfer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transfer_date = models.DateField(
        default=timezone.now
    )

    note = models.CharField(
        max_length=255,
        blank=True
    )

    cheque_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    carrier = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.source_type} → {self.destination_type} : {self.transfer_amount}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new:
            try:
                source = CashType.objects.select_for_update().get(
                    id=self.source_type.id
                )

                # Allow negative balance
                source.type_amount -= self.transfer_amount
                source.type_note = f"Debited {self.transfer_amount} on BalanceTransfer"
                source.save()

                dest = CashType.objects.select_for_update().get(
                    id=self.destination_type.id
                )

                dest.type_amount += self.transfer_amount
                dest.type_note = f"Credited {self.transfer_amount} on BalanceTransfer"
                dest.save()

            except CashType.DoesNotExist:
                raise ValidationError("Invalid Cash Type selected.")

        super().save(*args, **kwargs)
        


class LoanVoucher(BaseModel):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    source_name = models.ForeignKey('purchase.HeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True, related_name='Loan_voucher_sn')
    type = models.CharField(max_length=100)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    conductor_name = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    expense_name = models.ForeignKey('purchase.HeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True, related_name='Loan_voucher_dn')
    vendor_name = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    empl_name = models.CharField(max_length=100, null=True, blank=True)
    
    bankName = models.ForeignKey(
        CashType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_vouchers_as_bank'  # changed to avoid clash
    )
    
    cash_type = models.ForeignKey(
        CashType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_vouchers_as_cash'  # changed to avoid clash
    )
    
    mr_or_bill_no = models.CharField(max_length=100)
    headAcct = models.ForeignKey(HeadOfAccount, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)
    carrier = models.CharField(max_length=255, blank=True, null=True)
    loan_status = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"LoanVoucher #{self.id} - {self.project_name} - {self.customer_name} - {self.amount} - {self.type} - {self.date} - {self.cash_type}"





class OpenBlanceVoucher(BaseModel):
    TYPE_CHOICES = [
        ('Contructor', 'Contructor'),
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Bank', 'Bank'),
    ]
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES) 
    contructor = models.ForeignKey(SiteSupervisor, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    bankName = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True, related_name='open_blance_vouchers_as_bank')
    head_of_account = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True) 
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    amount = models.DecimalField(max_digits=12, decimal_places=2)  
    date = models.DateField()
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"OpenBlanceVoucher #{self.id} - {self.type} - {self.amount} - {self.vendor} - {self.date}"
    


# =================== নতুন মডেলগুলো ===================

class BankStatementTransaction(models.Model):
    bank = models.ForeignKey(CashType, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    matched = models.BooleanField(default=False)
    ledger_entry = models.ForeignKey(LedgerEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name='bank_matches')

    def __str__(self):
        return f"{self.date} | {self.amount} | {self.description}"

class AccountReconciliation(models.Model):
    bank_account = models.ForeignKey(CashType, on_delete=models.CASCADE)
    ledger_entry = models.ForeignKey(LedgerEntry, on_delete=models.CASCADE)
    statement_txn = models.ForeignKey(BankStatementTransaction, on_delete=models.CASCADE)
    matched_on = models.DateTimeField(auto_now_add=True)
    reconciled_by = models.CharField(max_length=150, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('bank_account', 'ledger_entry', 'statement_txn')

    def __str__(self):
        return f"Reconcile: {self.statement_txn} ↔ {self.ledger_entry}"
    



STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)

class CapitalAccount(models.Model):
    head_of_account = models.ForeignKey('HeadOfAccount', on_delete=models.CASCADE)
    person_name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    note = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='capital_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.person_name} - {self.head_of_account.head_name} (৳{self.amount})"
        
        
        
        
class BalanceSheetHead(models.Model):
    HEAD_CHOICES = (
        ('Assets', 'Assets'),
        ('Liabilities', 'Liabilities'),
        ('Equity', 'Equity'),
    )

    TYPE_CHOICES = (
        ('Current Assets', 'Current Assets'),
        ('Fixed Assets', 'Fixed Assets'),
        ('Current Liabilities', 'Current Liabilities'),
        ('Long Term Liabilities', 'Long Term Liabilities'),
        ('Equity Capital', 'Equity Capital'),
        ('Retained Earnings', 'Retained Earnings'),
    )

    head_name = models.CharField(max_length=50, choices=HEAD_CHOICES)
    type_name = models.CharField(max_length=50, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.head_name} - {self.type_name})"


class BalanceItem(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    head = models.ForeignKey(BalanceSheetHead, on_delete=models.CASCADE)
    type_name = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, default='Pending')

    def __str__(self):
        return f"{self.head.head_name if self.head else 'No Head'} - {self.value}"





class ProjectProfitRecord(models.Model):
    project = models.OneToOneField(
        ProjectFirstLevelName, on_delete=models.CASCADE, related_name="profit_record"
    )
    profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    profit_25 = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    final_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.project_first_name} - {self.final_profit} Profit Record"
