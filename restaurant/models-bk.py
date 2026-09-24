from django.db import models
from restahrm.models import RestaurantEmployee
from hrm.models import Employee
from projects.models import ProjectFirstLevelName
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.
class RestaurantCategory(models.Model):
    restu_category_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.restu_category_name}"

class RestaurantExpenseCategory(models.Model):
    restu_Exp_category_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.restu_Exp_category_name}"


class RestaurantItem(models.Model):
    rest_category = models.ForeignKey(RestaurantCategory, on_delete=models.CASCADE, null=True, blank=True)
    rest_item_name = models.CharField(max_length=255)
    rest_item_type = models.CharField(max_length=255, null=True, blank=True)
    rest_item_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.rest_item_code:
            last_obj = RestaurantItem.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.rest_item_code = f"RIT-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.rest_item_code} - {self.rest_item_name}"
    



# --- New Models ---
class ApprovalRange(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_ranges')
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.min_amount} - {self.max_amount}"

class RestaurantBudget(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('Purchase', 'Purchase'),
        ('Expense', 'Expense'),
    ]
    
    category = models.ForeignKey(RestaurantCategory, on_delete=models.CASCADE, related_name='budgets')
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fiscal_year = models.CharField(max_length=9, blank=True, null=True)  # Fixed: Removed placeholder argument
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.restu_category_name} ({self.budget_type}) - {self.amount}"
        

class RestaurantCustomer(models.Model):
    rest_customer_name = models.CharField(max_length=255)
    rest_customer_type = models.CharField(max_length=255, null=True, blank=True)
    rest_customer_account = models.CharField(max_length=255, default="Customer Account")
    rest_customer_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.rest_customer_code:
            last_obj = RestaurantCustomer.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.rest_customer_code = f"RCS-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rest_customer_code} - {self.rest_customer_name}"
    

# class RestaurantItemAmount(models.Model):
#     category = models.ForeignKey(RestaurantCategory, on_delete=models.CASCADE, related_name="products")
#     item_code = models.CharField(max_length=50, unique=True)
#     item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE, null=True, blank=True)
#     opening_stock = models.PositiveIntegerField(default=0)
#     purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     reorder_warning = models.PositiveIntegerField(default=0)
#     reorder_size = models.PositiveIntegerField(default=0)
#     unit = models.CharField(max_length=50, default="PRCE")

#     def save(self, *args, **kwargs):
#         if not self.item_code:
#             last_obj = RestaurantItemAmount.objects.order_by('-id').first()
#             next_id = (last_obj.id + 1) if last_obj else 1
#             self.item_code = f"RTC-{next_id:05d}"  
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.item_name} ({self.item_code})"



from django.db import models
from django.db.models import Sum

class RestaurantItemAmount(models.Model):
    category = models.ForeignKey(RestaurantCategory, on_delete=models.CASCADE, related_name="products")
    item_code = models.CharField(max_length=50, unique=True)
    item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE, null=True, blank=True)
    opening_stock = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reorder_warning = models.PositiveIntegerField(default=0)
    reorder_size = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default="PRCE")

    def save(self, *args, **kwargs):
        if not self.item_code:
            last_obj = RestaurantItemAmount.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.item_code = f"RTC-{next_id:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} ({self.item_code})"

    @property
    def available_qty(self):
        """
        Safely calculates available stock using item_name_id to align with RestInventories
        """
        purchased = 0
        used = 0

        # Safely query RestInventories using item_name_id
        if self.item_name_id:
            purchased = RestInventories.objects.filter(
                item_name_id=self.item_name_id
            ).aggregate(total=Sum('qty'))['total'] or 0

            # Kitchen usage tracking (if linked to RestaurantItem)
            used = RestInventoryUse.objects.filter(
                item_name_id=self.item_name_id
            ).aggregate(total=Sum('qty'))['total'] or 0

        # POS sales tracked directly against RestaurantItemAmount (self.id)
        sold = RestaurantSaleItem.objects.filter(
            item_id=self.id
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # Damaged food tracked directly against RestaurantItemAmount (self.id)
        damaged = RestaurantDamageFood.objects.filter(
            item_id=self.id
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # Formula: (Opening + Purchased) - (Kitchen Used + POS Sold + Damaged)
        total_available = (self.opening_stock + purchased) - (used + sold + damaged)
        return max(0, total_available)
        
        

from decimal import Decimal
from django.db import models


class RestaurantSale(models.Model):
    invoice_no = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        RestaurantCustomer,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sale_date = models.DateField()
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    final_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    received_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    return_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

    def save(self, *args, **kwargs):
        # Auto-calculate final_amount if needed
        self.final_amount = (self.total_amount or Decimal("0.00")) - (
            self.discount or Decimal("0.00")
        )

        # Set received_amount equal to final_amount if not explicitly passed
        if not self.received_amount or self.received_amount == Decimal("0.00"):
            self.received_amount = self.final_amount

        # Calculate return amount (Change given back to customer)
        if self.received_amount > self.final_amount:
            self.return_amount = self.received_amount - self.final_amount
        else:
            self.return_amount = Decimal("0.00")

        super().save(*args, **kwargs)


# class RestaurantSale(models.Model):
#     invoice_no = models.CharField(max_length=50, unique=True)
#     customer = models.ForeignKey(RestaurantCustomer, on_delete=models.SET_NULL, null=True)
#     sale_date  = models.DateField() 
#     discount = models.CharField(max_length=255, null=True, blank=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     note = models.CharField(max_length=255, null=True, blank=True)

    
#     def __str__(self):
#         return f"{self.invoice_no} - {self.customer}"


class RestaurantSaleItem(models.Model):
    sale = models.ForeignKey(RestaurantSale, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(RestaurantItemAmount, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.CharField(max_length=255, null=True, blank=True) 
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    

    def __str__(self):
        return f"{self.item} x {self.quantity}"
        
        
        

class RestHeadofAcct(models.Model):
    restu_headofacct_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.restu_headofacct_name}"
    


class RestaurantAccount(models.Model):
    rest_head_name = models.ForeignKey(RestHeadofAcct, on_delete=models.CASCADE, null=True, blank=True)
    rest_acct_name = models.CharField(max_length=255)
    rest_acct_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.rest_acct_code:
            last_obj = RestaurantAccount.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.rest_acct_code = f"RHA-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rest_acct_code} - {self.rest_head_name}"
    


class RestaurantSupplier(models.Model):
    rest_supplier_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Account Information
    rest_supplier_account = models.CharField(max_length=255, default="Supplier Account")
    rest_supplier_name = models.CharField(max_length=255)

    # Contact Information
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_mobile = models.CharField(max_length=20, blank=True, null=True)

    # Financial Information
    purchase_commission = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.rest_supplier_code:
            last_obj = RestaurantSupplier.objects.order_by('-id').first()
            if last_obj and last_obj.rest_supplier_code:
                last_number = int(last_obj.rest_supplier_code.split('-')[1])
                next_id = last_number + 1
            else:
                next_id = 1
    
            self.rest_supplier_code = f"RCS-{next_id:05d}"
    
        super().save(*args, **kwargs)
        

    def __str__(self):
        return f"{self.rest_supplier_code} - {self.rest_supplier_name}"
        
        

class RestaurantJewelSupplier(models.Model):
    rest_supplier_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Account Information
    rest_supplier_account = models.CharField(max_length=255, default="Supplier Account")
    rest_supplier_name = models.CharField(max_length=255)

    # Contact Information
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_mobile = models.CharField(max_length=20, blank=True, null=True)

    # Financial Information
    purchase_commission = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.rest_supplier_code:
            last_obj = RestaurantJewelSupplier.objects.order_by('-id').first()
            if last_obj and last_obj.rest_supplier_code:
                last_number = int(last_obj.rest_supplier_code.split('-')[1])
                next_id = last_number + 1
            else:
                next_id = 1
    
            self.rest_supplier_code = f"RCS-{next_id:05d}"
    
        super().save(*args, **kwargs)
        

    def __str__(self):
        return f"{self.rest_supplier_code} - {self.rest_supplier_name}"
        


class RestExpense(models.Model):
    expense_name = models.CharField(max_length=200)
    expense_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):

        if not self.expense_code:
            last_expense = RestExpense.objects.order_by('-id').first()

            if last_expense and last_expense.expense_code:
                try:
                    last_number = int(last_expense.expense_code.replace('EXP', ''))
                    new_number = last_number + 1
                except:
                    new_number = last_expense.id + 1
            else:
                new_number = 1

            self.expense_code = f"EXP{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.expense_name
        
        


class RestPurchaseCost(models.Model):
    pur_cost_name = models.CharField(max_length=200)
    pur_cost_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):

        if not self.pur_cost_code:
            last_cost = RestPurchaseCost.objects.order_by('-id').first()

            if last_cost and last_cost.pur_cost_code:
                try:
                    last_number = int(last_cost.pur_cost_code.replace('PC', ''))
                    new_number = last_number + 1
                except:
                    new_number = last_cost.id + 1
            else:
                new_number = 1

            self.pur_cost_code = f"PC{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.pur_cost_name
        
        

class RestExpenseRequisition(models.Model):
    project_name = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, null=True, blank=True)
    cash_type = models.ForeignKey('restaccounting.CashRestType', on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True) 
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    head_of_account = models.ForeignKey('restaccounting.RestHeadOfAccount', on_delete=models.SET_NULL, null=True)
    employee_name = models.ForeignKey('hrm.Employee', on_delete=models.CASCADE)
    item_name = models.ForeignKey(RestExpense, on_delete=models.CASCADE)
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
            
            
            

class RestRequisition(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(RestaurantEmployee, on_delete=models.CASCADE)
    item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE)

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
    approv_store = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
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
    calc_mode = models.CharField(
        max_length=10, 
        choices=[('normal', 'Normal'), ('unit', 'Unit')], 
        default='normal'
    )
   
    
    def save(self, *args, **kwargs):
        qty = Decimal(str(self.qty or 0)).quantize(Decimal('0.01'))
        rate = Decimal(str(self.rate or 0)).quantize(Decimal('0.01'))
    
        if self.discount is None or self.discount == "":
            discount = Decimal("0.00")
        else:
            discount = Decimal(str(self.discount))
        discount = discount.quantize(Decimal('0.01'))
    
        calc_mode = getattr(self, 'calc_mode', 'unit') 
        
        if calc_mode == "whole":
            # ✅ Whole mode: Baseline is just the direct rate value
            amount = (rate - discount).quantize(Decimal('0.01'))  
        else:
            # ✅ Unit mode: Baseline is qty * rate
            amount = (qty * rate - discount).quantize(Decimal('0.01'))  
    
        self.amount = max(amount, Decimal("0.00"))
        self.discount = discount
    
        if not self.requisition_date:
            self.requisition_date = timezone.now().date()
    
        super().save(*args, **kwargs)

        
        
    def __str__(self):
        return f"{self.project_name} - {self.item_name} - {self.purch_date}- {self.vendor_name} - {self.purch_id} - {self.vendor_name}- {self.requisition_date} - {self.amount}"




class RestRequisitionApprovalHistory(models.Model):

    requi_uniq_id = models.IntegerField(
        null=True,
        blank=True
    )
    pur_verify = models.CharField(max_length=255, blank=True, null=True)
    purch_appov = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    project_name = models.ForeignKey(
        ProjectFirstLevelName,
        on_delete=models.SET_NULL,
        null=True
    )

    employee_name = models.ForeignKey(
        RestaurantEmployee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    cash_empl = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )

    approv_acct_status = models.CharField(
        max_length=20
    )

    approv_acct_note = models.TextField(
        null=True,
        blank=True
    )

    # ✅ instead of Django User
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requisitions"
    )

    approved_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.requi_uniq_id} - {self.purch_appov}"



class RestaurantKitchenLedger(models.Model):
    TYPE_CHOICES = [
        ('Expense', 'Expense'),
        ('Purchase', 'Purchase'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    requisition = models.ForeignKey(
        RestRequisition,
        on_delete=models.CASCADE,
        related_name='ledger_entries',
        null=True, blank=True
    )
    project = models.ForeignKey(
        ProjectFirstLevelName, on_delete=models.CASCADE, related_name='ledger_entries'
    )
    employee = models.ForeignKey(
        RestaurantEmployee, on_delete=models.CASCADE, related_name='ledger_entries'
    )
    item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE, default='')
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    tbl_id = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.balance = self.debit - self.credit
        self.is_paid = (self.balance == 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project} / {self.id} / {self.employee} — Dr:{self.debit} Cr:{self.credit} Bal:{self.balance}"      
        
        
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError  

class RestInventories(models.Model):
    requi_id = models.IntegerField(null=True, blank=True) 
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(RestaurantEmployee, on_delete=models.CASCADE)    
    item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE)
    vendor_name = models.ForeignKey(RestaurantSupplier, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    remark = models.TextField(blank=True, null=True)    
    approv_note = models.TextField(blank=True, null=True)    
    approv_acct_note = models.TextField(blank=True, null=True)
    approv_purch_note = models.TextField(blank=True, null=True)
    requisition_date = models.DateField(null=True, blank=True)
    qtysub = models.PositiveIntegerField(default=0)
    purch_id = models.IntegerField(null=True, blank=True) 
    purch_date = models.DateField(null=True, blank=True)
    purch_file_1 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)
    purch_file_2 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)
    purch_file_3 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)

    def __str__(self):
        return f"{self.purch_id} - {self.project_name} - {self.item_name} - {self.vendor_name}"


class RestInventoryUse(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    item_name = models.ForeignKey(RestaurantItem, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    total_qty = models.PositiveIntegerField(default=0)
    qtysub_qty = models.PositiveIntegerField(default=0)
    details = models.TextField(blank=True, null=True)
    use_date = models.DateField(default=timezone.now)
    remark = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            remaining_qty = self.qty
            
            with transaction.atomic():
                # Fetch and lock rows before calculating totals to ensure data safety
                inventories = list(
                    RestInventories.objects.filter(
                        project_name=self.project_name,
                        item_name=self.item_name,
                        qty__gt=0
                    ).order_by('id').select_for_update()
                )

                total_available = sum(inv.qty for inv in inventories)        
                if total_available < self.qty:
                    raise ValidationError(f"Your requested deduction of {self.qty} exceeds total available branch stock ({total_available}).")        
                
                # Execute FIFO batch updates
                for inv in inventories:
                    if remaining_qty <= 0:
                        break
                    if inv.qty >= remaining_qty:
                        inv.qty -= remaining_qty
                        inv.save(update_fields=['qty'])
                        remaining_qty = 0
                    else:
                        remaining_qty -= inv.qty
                        inv.qty = 0
                        inv.save(update_fields=['qty'])            
                
                # Update history metric tracker field balance
                self.total_qty = total_available - self.qty

        super().save(*args, **kwargs)
            
    def __str__(self):
        return f"{self.project_name} - {self.item_name} - {self.qty}"




from django.db import models
from django.db.models import Sum
from django.utils import timezone

class RestaurantDamageFood(models.Model):
    item = models.ForeignKey('RestaurantItemAmount', on_delete=models.CASCADE, related_name='damage_records')
    quantity = models.PositiveIntegerField()
    damage_date = models.DateField(default=timezone.now)
    reason = models.TextField(blank=True, null=True)
    reported_by = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.item} - {self.quantity} Damaged on {self.damage_date}"
        
        


class RestaurantPublicExpense(models.Model):

    EXPENSE_TYPE_CHOICES = (
        ('Expense', 'Expense'),
    )

    project_name = models.ForeignKey(
        'projects.ProjectFirstLevelName',
        on_delete=models.CASCADE
    )

    restu_expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPE_CHOICES,
        default='Expense'
    )

    restu_cate_name = models.ForeignKey(
        'RestaurantExpenseCategory',
        on_delete=models.CASCADE
    )

    restu_expense_name = models.CharField(max_length=255)

    restu_expense_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    def __str__(self):
        return self.restu_expense_name
        