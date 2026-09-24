from django.db import models
from projects.models import ProjectFirstLevelName
from datetime import date
from django.core.exceptions import ValidationError 
from django.utils import timezone 
from decimal import Decimal
from django.dispatch import receiver 
from django.db.models.signals import post_save


class Varatiya(models.Model):
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='tenant/varatiya_images/', null=True, blank=True)
    nid = models.ImageField(upload_to='tenant/varatiya_nid_images/', null=True, blank=True)
    contact = models.CharField(max_length=20, unique=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    permanent_address = models.TextField()
    number_of_members = models.PositiveIntegerField(default=1)
    reference_name = models.CharField(max_length=255, null=True, blank=True)
    reference_contact = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    type = models.CharField(max_length=100, null=True, blank=True)
    head_of_account = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.type:
            self.type = "customer"
        if not self.head_of_account:
            self.head_of_account = "customer account"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.contact}"


class ProjectName(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        "projects.ProjectFirstLevelName", 
        on_delete=models.CASCADE,
        related_name='project_names' ,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name
  
 
class Room(models.Model):
    FLAT_CHOICES = [(f'F{i}', f'F{i}') for i in range(1, 16)]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Deactive', 'Deactive'),
        ('Warning', 'Warning'),
    ]

    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10, choices=FLAT_CHOICES)
    project = models.ForeignKey(
        ProjectName, on_delete=models.CASCADE, related_name='rooms'
    )
    client = models.ForeignKey(
        Varatiya, on_delete=models.SET_NULL, null=True, blank=True, related_name='rooms'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Deactive')

    core_room_rent = models.DecimalField(max_digits=10, decimal_places=2)
    parking_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gas_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    garbage_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)

    meter_number = models.CharField(max_length=50, blank=True, null=True)
    opening_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    last_month_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    unit_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)


    created_at = models.DateTimeField(auto_now_add=True , blank=True, null=True)
    def __str__(self):
        return f"{self.room_name} ({self.flat}) - {self.project.name}"

    @property
    def total_monthly_rent(self):
        """Calculate the total monthly rent including all costs."""
        return sum([
            self.core_room_rent or Decimal('0'),
            self.parking_cost or Decimal('0'),
            self.service_rent or Decimal('0'),
            self.gas_rent or Decimal('0'),
            self.water_rent or Decimal('0'),
            self.garbage_rent or Decimal('0'),
            self.electricity_rent or Decimal('0'),
            self.other_cost or Decimal('0'),
        ])



class Rent(models.Model):
    projectref = models.ForeignKey(
        "ProjectName",
        on_delete=models.CASCADE,
        related_name='rents'
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rents'
    )
    varatiya = models.ForeignKey(
        "Varatiya",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rents'
    )
    startmonths = models.DateField(null=True, blank=True)
    endmonths = models.DateField(null=True, blank=True)

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Deactive', 'Deactive'),
        ('Warning', 'Warning'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )

    def clean(self):
        # Ensure a Varatiya doesn't have more than one active rent
        if self.varatiya and self.status == 'Active':
            active_rent = Rent.objects.filter(varatiya=self.varatiya, status='Active')
            if self.pk:
                active_rent = active_rent.exclude(pk=self.pk)
            if active_rent.exists():
                raise ValidationError(f"{self.varatiya} already has an active rent.")

    def save(self, *args, **kwargs):
        self.clean()  # enforce validation on save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rent for {self.varatiya} in {self.room}" 


class Bill(models.Model):
    
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    core_room_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=[('Generated','Generated'),('Admin Approved','Admin Approved'),('Partial Payment','Partial Payment'),('Payment Clear','Payment Clear')], default='Generated')
  
    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(Rent, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    
    def __str__(self):
        return f"Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}"


class GasBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    gas_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=[('Generated','Generated'),('Admin Approved','Admin Approved'),('Partial Payment','Partial Payment'),('Payment Clear','Payment Clear')], default='Generated')

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='gas_bills'
    )
    
    def __str__(self):
        return f"Gas Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}"


class WaterBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    water_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=[('Generated','Generated'),('Admin Approved','Admin Approved'),('Partial Payment','Partial Payment'),('Payment Clear','Payment Clear')], default='Generated')

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='water_bills'
    )

    def __str__(self):
        return f"Water Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}"


class ParkingBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    parking_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=[('Generated','Generated'),('Admin Approved','Admin Approved'),('Partial Payment','Partial Payment'),('Payment Clear','Payment Clear')], default='Generated')

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='parking_bills'
    )
    
    def __str__(self):
        return f"Parking Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}" 


class ServiceBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    service_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Generated', 'Generated'),
            ('Admin Approved', 'Admin Approved'),
            ('Partial Payment', 'Partial Payment'),
            ('Payment Clear', 'Payment Clear')
        ],
        default='Generated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='service_bills'
    )
    
    def __str__(self):
        return f"Service Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}"



class GarbageBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    garbage_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    bill_month = models.DateField(default=date.today)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Generated','Generated'),
            ('Admin Approved','Admin Approved'),
            ('Partial Payment','Partial Payment'),
            ('Payment Clear','Payment Clear')
        ],
        default='Generated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='garbage_bills'
    )

    def __str__(self):
        return f"Garbage Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}"
 

    
class ElectricityBill(models.Model):
    room_name = models.CharField(max_length=255)
    flat = models.CharField(max_length=10)
    varatiya_name = models.CharField(max_length=255, null=True, blank=True)

    electricity_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    used_units = models.DecimalField(max_digits=10, decimal_places=2, default=0, null = True, blank=True)
    bill_month = models.DateField(default=date.today)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Generated','Generated'),
            ('Admin Approved','Admin Approved'),
            ('Partial Payment','Partial Payment'),
            ('Payment Clear','Payment Clear')
        ],
        default='Generated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    rent = models.ForeignKey(
        "Rent", on_delete=models.SET_NULL, null=True, blank=True, related_name='electricity_bills'
    )
    
    def __str__(self):
        return f"Electricity Bill: {self.varatiya_name} - {self.bill_month.strftime('%B %Y')}" 
    

        
#rupok -diu - lanavo okey 

class MainBill(models.Model):
    project = models.ForeignKey("ProjectName", on_delete=models.SET_NULL, null=True, blank=True)
    tenant = models.ForeignKey("Varatiya", on_delete=models.SET_NULL, null=True, blank=True)
    month = models.DateField(default=date.today)

    #  Linked individual bills
    rent_bill = models.ForeignKey("Bill", on_delete=models.SET_NULL, null=True, blank=True)
    gas_bill = models.ForeignKey("GasBill", on_delete=models.SET_NULL, null=True, blank=True)
    water_bill = models.ForeignKey("WaterBill", on_delete=models.SET_NULL, null=True, blank=True)
    parking_bill = models.ForeignKey("ParkingBill", on_delete=models.SET_NULL, null=True, blank=True)
    service_bill = models.ForeignKey("ServiceBill", on_delete=models.SET_NULL, null=True, blank=True)
    electricity_bill = models.ForeignKey("ElectricityBill", on_delete=models.SET_NULL, null=True, blank=True)
    garbage_bill = models.ForeignKey("GarbageBill", on_delete=models.SET_NULL, null=True, blank=True)

    #  Financial totals
    generated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    adjusted_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    #  Status
    status = models.CharField(
        max_length=30,
        choices=[
            ('Generated', 'Generated'),
            ('Approved', 'Approved'),
            ('Partial Payment', 'Partial Payment'),
            ('Payment Clear', 'Payment Clear'),
        ],
        default='Generated'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Main Bill - {self.tenant or 'N/A'} ({self.month.strftime('%B %Y')})"

    #  Step 1: Generate total from linked bills

    def calculate_generated_amount(self):
        """
        Calculates total from all linked bills.
        Ensures both generated_amount and adjusted_amount are updated correctly,
        including on first creation.
        """
        total = Decimal('0.00')

        if self.rent_bill: total += getattr(self.rent_bill, 'subtotal', 0)
        if self.gas_bill: total += getattr(self.gas_bill, 'gas_rent', 0)
        if self.water_bill: total += getattr(self.water_bill, 'water_rent', 0)
        if self.parking_bill: total += getattr(self.parking_bill, 'parking_cost', 0)
        if self.service_bill: total += getattr(self.service_bill, 'service_rent', 0)
        if self.electricity_bill: total += getattr(self.electricity_bill, 'electricity_rent', 0)
        if self.garbage_bill: total += getattr(self.garbage_bill, 'garbage_rent', 0)

        # If it's a new object, we must save first to get a PK
        if not self.pk:
            self.generated_amount = total
            self.adjusted_amount = total
            self.total_due = total
            super(MainBill, self).save()  # Save first time to generate PK
        else:
            self.generated_amount = total
            # If no discount has been applied yet, keep adjusted = generated
            if self.discount_amount == 0:
                self.adjusted_amount = total

        # Recalculate total_due
        self.total_due = self.adjusted_amount - self.total_paid
        if self.total_due < 0:
            self.total_due = Decimal('0.00')

        # Status update
        if self.total_due == 0:
            self.status = "Payment Clear"
        elif self.total_paid > 0:
            self.status = "Partial Payment"
        else:
            self.status = "Approved"

        self.save(update_fields=["generated_amount", "adjusted_amount", "total_due", "status"])
        return self.generated_amount 
        

    # Step 2: Add discount logic
    def add_discount_amount(self, discount_value):
        """
        Apply or update discount amount.
        adjusted_amount = generated_amount - discount_amount
        total_due = adjusted_amount - total_paid
        """
        discount_value = Decimal(discount_value or 0)
        self.discount_amount = discount_value

        # Adjusted = Generated - Discount
        self.adjusted_amount = self.generated_amount - self.discount_amount
        if self.adjusted_amount < 0:
            self.adjusted_amount = Decimal('0.00')

        # Update total due
        self.total_due = self.adjusted_amount - self.total_paid
        if self.total_due < 0:
            self.total_due = Decimal('0.00')

        #  Auto-status
        if self.total_due == 0:
            self.status = "Payment Clear"
        elif self.total_paid > 0:
            self.status = "Partial Payment"
        else:
            self.status = "Approved"

        self.save(update_fields=[
            "discount_amount", "adjusted_amount", "total_due", "status"
        ])
        return {
            "discount_amount": self.discount_amount,
            "adjusted_amount": self.adjusted_amount,
            "total_due": self.total_due,
            "status": self.status
        }

    #  Step 3: Payment addition logic
    def add_payment(self, amount):
        """
        When payment received, update total_paid and total_due.
        total_due = adjusted_amount - total_paid
        """
        if not amount or amount <= 0:
            return self.total_paid, self.total_due

        amount = Decimal(amount)
        self.total_paid += amount

        self.total_due = self.adjusted_amount - self.total_paid
        
        if self.total_due < 0:
            self.total_due = Decimal('0.00')

        #  Status update
        if self.total_due == 0:
            self.status = "Payment Clear"
        elif self.total_paid > 0:
            self.status = "Partial Payment"
        else:
            self.status = "Approved"

        self.save(update_fields=["total_paid", "total_due", "status"])
        return self.total_paid, self.total_due 




class TenantCashType(models.Model):
    ACCOUNT_TYPES = [
        ('bank', 'Bank Account'),
        ('mobile', 'Mobile Banking'),
        ('cash', 'Cash in Hand'),
        ('other', 'Other'),
    ]

    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)  
    account_name = models.CharField(max_length=100)      
    account_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  
    bank_name = models.CharField(max_length=100, null=True, blank=True)    
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  
    is_active = models.BooleanField(default=True)                          
    description = models.TextField(null=True, blank=True)                  
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()})"
    
    def add_money(self, amount):
        if amount <= 0:
            return "Invalid amount"
        self.balance += amount
        self.save()
        if self.account_type == 'bank':
            return f"Tk {amount} added to Bank Account: {self.account_name}"
        elif self.account_type == 'mobile':
            return f"Tk {amount} added to Mobile Banking: {self.account_name}"
        elif self.account_type == 'cash':
            return f"Tk {amount} added to Cash in Hand"
        else:
            return f"Tk {amount} added to {self.account_name}"
        
    def deduct_money(self, amount):
        if amount <= 0:
            return "Invalid amount"

        if amount > self.balance:
            return f"Insufficient balance! Current balance: Tk {self.balance}"

        self.balance -= amount
        self.save()

        if self.account_type == 'bank':
            return f"Tk {amount} deducted from Bank Account: {self.account_name}"
        elif self.account_type == 'mobile':
            return f"Tk {amount} deducted from Mobile Banking: {self.account_name}"
        elif self.account_type == 'cash':
            return f"Tk {amount} deducted from Cash in Hand"
        else:
            return f"Tk {amount} deducted from {self.account_name}"


class ChequeBook(models.Model):
    account = models.ForeignKey(TenantCashType, on_delete=models.CASCADE, related_name='cheque_books')
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
        return f"{self.book_name} ({self.book_number}) - {self.account.account_name}"

    class Meta:
        ordering = ['-issue_date']


class Cheque(models.Model):
    STATUS_CHOICES = [
        ('unused', 'Unused'),
        ('used', 'Used'),
        ('issued', 'Issued'),
        ('discount', 'Discount'),
        ('cleared', 'Cleared'),
        ('cancelled', 'Cancelled'),
    ]

    cheque_book = models.ForeignKey(ChequeBook, on_delete=models.CASCADE, related_name='cheques')
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


@receiver(post_save, sender=ChequeBook)
def create_cheques_for_book(sender, instance, created, **kwargs):
    if created:
        cheque_list = []
        for number in range(instance.start_number, instance.end_number + 1):
            cheque_list.append(
                Cheque(cheque_book=instance, cheque_number=str(number))
            )
        Cheque.objects.bulk_create(cheque_list)



class TenantAdvance(models.Model):
    varatiya = models.ForeignKey(Varatiya, on_delete=models.CASCADE, related_name="advances")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    # To track adjustment with bills later
    adjusted_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def remaining_balance(self):
        """Unadjusted advance balance"""
        return self.amount - self.adjusted_amount

    def __str__(self):
        return f"Advance - {self.varatiya.name} ({self.amount} Tk)" 


class ReceiveVoucher(models.Model):
    project_name = models.ForeignKey(ProjectName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100, editable=False)  # optional, readonly
    tenant_name = models.ForeignKey(Varatiya, on_delete=models.SET_NULL, null=True, blank=True)
    cash_type = models.ForeignKey(TenantCashType, on_delete=models.SET_NULL, null=True)
    cheque_number = models.ForeignKey(Cheque,on_delete=models.SET_NULL,null=True,blank=True, related_name='receive_vouchers')
    bill_date = models.DateField(null=True, blank=True)
    head_of_account = models.CharField(max_length=100, editable=False)  # optional, readonly
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    generated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    particulars = models.TextField()
    is_confirmed = models.BooleanField(default=False)
    approval_rv_status = models.BooleanField(default=False)
    carrier = models.CharField(max_length=255, blank=True, null=True)
    
    # Billing references
    rent_bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')
    gas_bill = models.ForeignKey(GasBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')
    water_bill = models.ForeignKey(WaterBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')
    parking_bill = models.ForeignKey(ParkingBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')
    service_bill = models.ForeignKey(ServiceBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')
    electricity_bill = models.ForeignKey(ElectricityBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='receive_vouchers')

    tenant_advance = models.ForeignKey(TenantAdvance, on_delete=models.SET_NULL, null=True, blank=True, related_name="receive_vouchers")
    mainbill = models.ForeignKey(MainBill, on_delete=models.SET_NULL, null=True, blank=True, related_name="main_bill")

    def save(self, *args, **kwargs):
        # Automatically set type and head_of_account from tenant
        if self.tenant_name:
            self.type = self.tenant_name.type
            self.head_of_account = self.tenant_name.head_of_account
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ReceiveVoucher #{self.id} - {self.project_name} - {self.tenant_name} - {self.amount} - {self.generated_amount} - {self.date}"


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    company_name = models.CharField(max_length=255, blank=True, null=True)
    head_of_account = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
        
        
class PaymentVoucher(models.Model):
    project_name = models.ForeignKey(ProjectName, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100, editable=False)  #auto from varatiya 
    tenant_name = models.ForeignKey(Varatiya, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_vouchers"
    )
    cash_type = models.ForeignKey(TenantCashType, on_delete=models.SET_NULL, null=True)  
    cheque_number = models.ForeignKey(Cheque,on_delete=models.SET_NULL,null=True,blank=True, related_name='payment_vouchers')
    bill_date = models.DateField(auto_now_add=True, null=True, blank=True)
    head_of_account = models.CharField(max_length=100, editable=False)  #auto from varatiya
    pv_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Payment Voucher no.
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    particulars = models.TextField()

    approval_pv_status = models.BooleanField(default=False)
    carrier = models.CharField(max_length=255, blank=True, null=True)

    tenant_advance = models.ForeignKey(TenantAdvance, on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_vouchers")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def clean(self):
        if self.tenant_name and self.supplier:
            raise ValidationError("You cannot select both Tenant and Supplier.")

        if not self.tenant_name and not self.supplier:
            raise ValidationError("You must select either Tenant or Supplier.")

    def save(self, *args, **kwargs):

        if self.tenant_name:
            self.type = self.tenant_name.type
            self.head_of_account = self.tenant_name.head_of_account

        if self.supplier:
            self.type = "Supplier Payment"
            self.head_of_account = self.supplier.head_of_account

        super().save(*args, **kwargs)

    def __str__(self):
        return f"PaymentVoucher #{self.id} - {self.project_name} - {self.tenant_name or self.supplier or 'N/A'} - {self.amount} - {self.date}"
 

 
class LedgerEntry(models.Model):
    tenant = models.ForeignKey(Varatiya, on_delete=models.CASCADE, related_name="ledger_entries",null=True, blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
        null=True,
        blank=True
    )
    bill_month = models.DateField(null=True, blank=True)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    bill_no = models.CharField(max_length=50, null=True, blank=True)
    debit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_opening = models.BooleanField(default=False)  
    receive_voucher = models.ForeignKey( ReceiveVoucher, on_delete=models.SET_NULL,  null=True, blank=True, related_name="ledger_entries" )
    payment_voucher = models.ForeignKey( PaymentVoucher, on_delete=models.SET_NULL,  null=True, blank=True, related_name="ledger_entries" )
   
    class Meta:
        ordering = ["date"]

    def __str__(self):
        if self.tenant:
            name = self.tenant.name
        elif self.supplier:
            name = self.supplier.name
        else:
            name = "Unknown"

        return f"{name} - {self.description} ({self.date})"
        
     
        
# tenant/models.py

from django.conf import settings


class TenantBulkSMS(models.Model):
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


class TenantBulkSMSRecipient(models.Model):
    bulk_sms = models.ForeignKey(
        TenantBulkSMS,
        on_delete=models.CASCADE,
        related_name="recipients"
    )
    tenant_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)
        
        
        
        
        
        
        
class Attendance(models.Model):
    user_id = models.IntegerField()
    punch_time = models.DateTimeField()
    status = models.IntegerField()
    check_type = models.IntegerField()
    field1 = models.IntegerField(default=0)
    field2 = models.IntegerField(default=0)
    field3 = models.IntegerField(default=0)
    field4 = models.IntegerField(default=0)
    field5 = models.IntegerField(default=0)
    field6 = models.IntegerField(default=0)
    device_sn = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.punch_time}  - {self.device_sn}"
        
        
