from django.db import models
from django.contrib.auth.models import User  
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import os

class PropertyOwner(models.Model):
    owner_name = models.CharField(max_length=255)
    contact_information = models.TextField()
    owner_type = models.CharField(max_length=50)
    ownership_type = models.CharField(max_length=50)

    # Owner Details (NID, Telephone, Address, and Attachments)
    nid_card_details = models.FileField(upload_to='nid_cards/', blank=False)  # NID Card upload (mandatory)
    telephone_number = models.CharField(max_length=20, blank=False, default='Not Provided')
    current_address = models.TextField(blank=False, default='Not Provided')  # Address field with default
    utility_bill = models.FileField(upload_to='utility_bills/', blank=True)  # Utility bill (optional)
    photo = models.ImageField(upload_to='owner_photos/', blank=True)  # Photo upload (optional)

    def __str__(self):
        return self.owner_name


import re

class RecordFile(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    
    AREA_CHOICES = [
        ('Acore', 'Acore'),
        ('Decimel', 'Decimel'),
        ('Kata', 'Kata'),
    ]

    FILE_TYPE_CHOICES = [
        ('RF', 'Real Estate File'),
        ('LF', 'Land File'),
        ('LGF', 'Legal File'),
        ('CF', 'Contractor File'),
        ('CCF', 'Civil Contractor File'),
        ('ECF', 'Electrical Contractor File'),
        ('PCF', 'Plumbing Contractor File'),
        ('MCF', 'Mechanical Contractor File'),
        ('FCF', 'Finishing Contractor File'),
        ('SCF', 'Supplier & Contractor File'),
    ]

    date = models.DateField(null=True, blank=True) 
    
    file_type = models.CharField(
        max_length=50,
        choices=FILE_TYPE_CHOICES,
        null=True,
        blank=True
    )
    
    file_no = models.CharField(max_length=100, blank=True, default="") 
    mouza = models.CharField(max_length=255, default="", blank=True, null=True)
    cs_dag_no = models.CharField(max_length=255, default="", blank=True, null=True)
    sa_dag_no = models.CharField(max_length=255, default="", blank=True, null=True)
    rs_dag_no = models.CharField(max_length=255, default="", blank=True, null=True)
    ct_dag_no = models.CharField(max_length=255, default="", blank=True, null=True)
    owner_client = models.CharField(max_length=255, blank=True, null=True)
    work_type = models.CharField(max_length=255, blank=True, null=True)
    
    area = models.CharField(
        max_length=50,
        choices=AREA_CHOICES,
        null=True,
        blank=True
    )
    area_value = models.CharField(max_length=255, default="", blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    responsible = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    # # 🌟 FIX: Added the missing save method definition declaration wrapper
    # def save(self, *args, **kwargs):
    #     if not self.file_no and self.file_type:
    #         last_record = (
    #             RecordFile.objects
    #             .filter(file_type=self.file_type)
    #             .order_by('-id')
    #             .first()
    #         )

    #         if last_record and last_record.file_no:
    #             try:
    #                 last_no = int(last_record.file_no.split('-')[-1])
    #             except (ValueError, IndexError):
    #                 last_no = 1000
    #         else:
    #             last_no = 1000

    #         new_no = last_no + 1
    #         self.file_no = f"{self.file_type}-{new_no}"

    #     super().save(*args, **kwargs)
    
    
    def save(self, *args, **kwargs):
        # If the record is brand new or file_no is empty/None
        if self._state.adding or not self.file_no or self.file_no.startswith("None-"):
            
            # Find the last sequence number used
            last_record = RecordFile.objects.exclude(file_no="").order_by('-id').first()
            
            if last_record and last_record.file_no:
                match = re.search(r'(\d+)$', last_record.file_no)
                if match:
                    last_no = int(match.group(1))
                else:
                    last_no = 721
            else:
                last_no = 721
            
            # Assign the proper file number using the selected file_type
            prefix = self.file_type if self.file_type else "FILE"
            self.file_no = f"{prefix}-{last_no + 1}"
            
        else:
            # If editing an existing record, ensure the prefix matches the updated file_type
            if self.file_type and '-' in self.file_no:
                number_part = self.file_no.split('-')[-1]
                self.file_no = f"{self.file_type}-{number_part}"

        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.file_no or f"Record {self.id}"        


   



class Project(models.Model):
    project_name = models.CharField(max_length=255)
    project_description = models.TextField()
    project_start_date = models.DateField()
    project_end_date = models.DateField()
    project_status = models.CharField(max_length=50, choices=[('Active', 'Active'), ('Unactive', 'Unactive')])
    
    # Land Details
    land_details_area = models.IntegerField()  # Changed from DecimalField to IntegerField
    land_purchase_price = models.IntegerField()  # Changed from DecimalField to IntegerField
    land_current_market_price = models.IntegerField()  # Changed from DecimalField to IntegerField

    # Building Details
    number_of_stories = models.IntegerField()
    flat_type_a = models.IntegerField()
    flat_type_b = models.IntegerField()
    flat_type_c = models.IntegerField()
    flat_type_d = models.IntegerField()
    parking_details = models.TextField()

    # Construction, Labor, Material, Other Costs
    construction_cost = models.IntegerField()  # Changed from DecimalField to IntegerField
    labor_cost = models.IntegerField()  # Changed from DecimalField to IntegerField
    material_cost = models.IntegerField()  # Changed from DecimalField to IntegerField
    other_costs = models.IntegerField()  # Changed from DecimalField to IntegerField

    # Unit Cost, Profit Margin, Profit Amount, Sales Price
    unit_cost = models.IntegerField(null=True, blank=True)  # Changed from DecimalField to IntegerField
    profit_margin = models.IntegerField()  # Changed from DecimalField to IntegerField
    profit_amount = models.IntegerField(null=True, blank=True)  # Changed from DecimalField to IntegerField
    sales_price = models.IntegerField(null=True, blank=True)  # Changed from DecimalField to IntegerField

    def save(self, *args, **kwargs):
        # Calculate unit cost and profit amount before saving
        self.unit_cost = self.construction_cost + self.labor_cost + self.material_cost + self.other_costs
        self.profit_amount = self.unit_cost * (self.profit_margin / 100)
        self.sales_price = self.unit_cost + self.profit_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return self.project_name 

       
class Property(models.Model):
    property_type = models.CharField(max_length=100, default='default_value')  
    address = models.TextField()
    size = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    lease_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    lease_status = models.CharField(max_length=20, default="Available")  
    sale_status = models.CharField(max_length=100, default='Not Sold') 
    purchase_date = models.DateField(default='2025-01-01')  
    construction_date = models.DateField(null=True)
    owner = models.ForeignKey(PropertyOwner, on_delete=models.CASCADE, related_name="properties")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=1)  
    

    class Meta:
        permissions = [
            ("can_view_property", "Can view property"),
            ("can_edit_property", "Can edit property"),
            ("can_delete_property", "Can delete property"),
        ]

    def __str__(self):
        return f"{self.property_type} at {self.address}"

class JointVenture(models.Model):
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.CASCADE, null=True, blank=True)
    land_owner_name = models.ForeignKey('PropertyOwner', on_delete=models.CASCADE, null=True, blank=True)
    developer_name = models.CharField(max_length=255)
    land_owner_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    developer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    developer_flat = models.IntegerField(null=True, blank=True)
    developer_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    land_owner_flat = models.IntegerField(null=True, blank=True)
    land_owner_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    profit_share = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    revenue_share = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    signing_money = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='plan_photos/', blank=True)

    JV_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ]
    
    jv_status = models.CharField(max_length=50, choices=JV_STATUS_CHOICES)

    def clean(self):
        if self.land_owner_percentage > 100:
            raise ValidationError('Land Owner percentage cannot be more than 100%.')
            
        if self.developer_percentage > 100:
            raise ValidationError('Developer percentage cannot be more than 100%.')

        if self.start_date >= self.end_date:
            raise ValidationError('Start date must be before end date.')

    def __str__(self):
        return f"Joint Venture with {self.land_owner_name}"


def validate_contribution_amount(value):
    if value <= 0:
        raise ValidationError('Contribution amount must be a positive value.')
    
class JVPartner(models.Model):
    partner_name = models.CharField(max_length=255)
    contact_information = models.TextField()
    contribution_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[validate_contribution_amount])
    joint_venture = models.ForeignKey(JointVenture, on_delete=models.CASCADE, related_name="partners")

    def __str__(self):
        return self.partner_name


class LeaseAgreement(models.Model):
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()
    lease_price = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    lease_status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Pending', 'Pending'), ('Completed', 'Completed')])
    payment_terms = models.TextField()
    agreement_document = models.FileField(upload_to='lease_documents/')

    def __str__(self):
        return f"Lease Agreement for {self.property} with {self.tenant}"

    class Meta:
        verbose_name = "Lease Agreement"
        verbose_name_plural = "Lease Agreements"


class Tenant(models.Model):
    tenant_name = models.CharField(max_length=255)
    contact_information = models.TextField()
    tenant_type = models.CharField(max_length=50)
    total_lease_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_total_lease_price(self):
        """
        Update the total lease price for this tenant based on the associated LeaseAgreements with lease_status 'Active' or 'Completed'.
        """
        total_price = LeaseAgreement.objects.filter(tenant=self, lease_status__in=['Active', 'Completed']).aggregate(Sum('lease_price'))['lease_price__sum'] or 0
        self.total_lease_price = total_price
        self.save()

    def __str__(self):
        return self.tenant_name

@receiver(post_save, sender=LeaseAgreement)
def update_tenant_total_lease_price(sender, instance, **kwargs):
    instance.tenant.update_total_lease_price()

@receiver(post_delete, sender=LeaseAgreement)
def update_tenant_total_lease_price_on_delete(sender, instance, **kwargs):
    instance.tenant.update_total_lease_price()


class LeasePayment(models.Model):
    lease_agreement = models.ForeignKey(LeaseAgreement, on_delete=models.CASCADE)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)  
    payment_status = models.CharField(max_length=50)  

    def __str__(self):
        return f"Payment of {self.payment_amount} for lease {self.lease_agreement.id}"


class Buyer(models.Model):
    buyer_name = models.CharField(max_length=255)
    contact_information = models.TextField()
    buyer_type = models.CharField(max_length=50, choices=[('Individual', 'Individual'), ('Company', 'Company')])
    total_sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # New Fields
    nid = models.CharField(max_length=20, blank=True, null=True)  # National ID
    photo = models.ImageField(upload_to='buyer_photos/', blank=True, null=True)  # Profile photo

    def update_total_sale_price(self):
        """
        Update the total sale price for this buyer based on the associated SaleRecords where payment_status is 'Paid'.
        """
        total_price = SaleRecord.objects.filter(buyer=self, payment_status='Paid').aggregate(Sum('sale_price'))['sale_price__sum'] or 0
        self.total_sale_price = total_price
        self.save()

    def __str__(self):
        return self.buyer_name


# Update the buyer's total_sale_price when a SaleRecord is saved, but only if payment_status is 'Paid'
@receiver(post_save, sender='properties.SaleRecord')
def update_buyer_total_sale_price(sender, instance, **kwargs):
    # Update only if payment_status is 'Paid'
    if instance.payment_status == 'Paid':
        instance.buyer.update_total_sale_price()

# Update the buyer's total_sale_price when a SaleRecord is deleted, but only if payment_status was 'Paid'
@receiver(post_delete, sender='properties.SaleRecord')
def update_buyer_total_sale_price_on_delete(sender, instance, **kwargs):
    # Update only if payment_status was 'Paid'
    if instance.payment_status == 'Paid':
        instance.buyer.update_total_sale_price()



class SaleRecord(models.Model):
    property = models.ForeignKey('Property', on_delete=models.CASCADE)  # Adjust the related model as per your requirement
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateField()
    buyer = models.ForeignKey('Buyer', on_delete=models.CASCADE)  # Adjust the related model as per your requirement
    sale_status = models.CharField(max_length=100)
    sale_agreement_document = models.FileField(upload_to='sale_agreements/')
    payment_status = models.CharField(max_length=50)

    # New fields for Money Receipt
    money_receipt_no = models.CharField(max_length=50, null=True, blank=True)
    money_receipt_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Sale Record {self.property} - {self.buyer}"



class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name



## Land Purchase ----
# class LandPurchase(models.Model):
#     land_supplier = models.CharField(max_length=255)
#     mouza_name = models.CharField(max_length=255, blank=True)
#     cs_dag_no = models.CharField(max_length=100, blank=True)
#     sa_dag_no = models.CharField(max_length=100, blank=True)
#     rs_dag_no = models.CharField(max_length=100, blank=True)
#     ct_dag_no = models.CharField(max_length=100, blank=True)
#     did_agreement = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")])
#     agreement_date = models.DateField(null=True, blank=True)
#     land_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     land_type = models.CharField(max_length=50, choices=[("Residential", "Residential"), ("Commercial", "Commercial"), ("Agricultural", "Agricultural")])
#     price_per_decimal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     total_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
#     payment_method = models.CharField(max_length=50, choices=[("Cash", "Cash"), ("Cheque", "Cheque"), ("Bank Transfer", "Bank Transfer")])
#     payment_status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Partial", "Partial"), ("Completed", "Completed")])
#     deed_number = models.CharField(max_length=100, blank=True)
#     registration_date = models.DateField(null=True, blank=True)
#     registration_office = models.CharField(max_length=255, blank=True)
#     mutation_done = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")])
#     legal_dispute = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")])
#     notes = models.TextField(blank=True)
#     documents = models.FileField(upload_to='land_documents/', blank=True, null=True)

#     def __str__(self):
#         return self.land_supplier


class LandPurchase(models.Model):
    LAND_TYPE_CHOICES = [
        ('Residential', 'Residential'),
        ('Commercial', 'Commercial'),
        ('Agricultural', 'Agricultural'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Completed', 'Completed'),
    ]
    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    AP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ]
    land_supplier = models.ForeignKey(PropertyOwner, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    mouza_name = models.CharField(max_length=255, blank=True, null=True)
    cs_dag_no = models.CharField(max_length=100, blank=True, null=True)
    sa_dag_no = models.CharField(max_length=100, blank=True, null=True)
    rs_dag_no = models.CharField(max_length=100, blank=True, null=True)
    ct_dag_no = models.CharField(max_length=100, blank=True, null=True)
    did_agreement = models.CharField(max_length=10, choices=YES_NO_CHOICES)
    agreement_date = models.DateField(blank=True, null=True)
    land_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    land_type = models.CharField(max_length=50, choices=LAND_TYPE_CHOICES)
    price_per_decimal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True) 
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)    
    deed_number = models.CharField(max_length=100, blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)
    mutation_done = models.CharField(max_length=10, choices=YES_NO_CHOICES)
    legal_dispute = models.CharField(max_length=10, choices=YES_NO_CHOICES)
    notes = models.TextField(blank=True, null=True)
    signature = models.FileField(upload_to='land_signatures/', blank=True, null=True) 
    documents = models.FileField(upload_to='land_documents/', blank=True, null=True)    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    lilahetalah_per = models.CharField(max_length=20, blank=False, default='')
    lilahetalah_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  
    media_per = models.CharField(max_length=20, blank=False, default='')
    media_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)        
    approval_status = models.CharField(max_length=50, choices=AP_STATUS_CHOICES, default="Pending")

    
    
    def __str__(self):
        return f"{self.land_supplier} - {self.mouza_name}"




class CashMethod(models.Model):
    method_name = models.CharField(max_length=100) 
    type_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type_note = models.CharField(max_length=255, default='')
    account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.method_name
    

class LandHeadOfAccount(models.Model):
    head_name = models.CharField(max_length=255)
    head_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.head_code:
            last = LandHeadOfAccount.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.head_code = f"LWA-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.head_code} - {self.head_name}"
        
    def get_transaction_type(self):
        return self.head_name.split()[0] 
    


class LandHeadOfExpense(models.Model):
    head_exp_name = models.CharField(max_length=255)
    head_exp_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.head_exp_code:
            last_obj = LandHeadOfExpense.objects.order_by('-id').first()
            next_id = (last_obj.id + 1) if last_obj else 1
            self.head_exp_code = f"LEC-{next_id:05d}"  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.head_exp_code} - {self.head_exp_name}"
        
        

class LandDebitVoucher(models.Model): 
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('LandHeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True)
    cash_type = models.ForeignKey('CashMethod', on_delete=models.SET_NULL, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)      
    head_of_account = models.ForeignKey('LandHeadOfAccount', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)    
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    date = models.DateField()
    remark = models.TextField()
    approval_status = models.BooleanField(null=True, blank=True)
    carrier = models.CharField(max_length=255, blank=True, null=True)
    advance_pay = models.CharField(max_length=255, blank=True, null=True)
    create_dr_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        land_name = self.land_purchase.mouza_name if self.land_purchase else "No Land"
        cash_name = self.cash_type.method_name if self.cash_type else "No Cash Type"
        owner_name = self.owner.owner_name if self.owner else "No Owner"
        return f"LandDebitVoucher #{self.id} - {land_name} - {owner_name} - {self.amount} - {self.date} - {cash_name}"




class LandCreditVoucher(models.Model):
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.SET_NULL, null=True, blank=True)  
    type = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('LandHeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True)
    cash_type = models.ForeignKey('CashMethod', on_delete=models.SET_NULL, null=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)  
    head_of_account = models.ForeignKey('LandHeadOfAccount', on_delete=models.SET_NULL, null=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)  
    date = models.DateField()  
    amount = models.DecimalField(max_digits=12, decimal_places=2) 
    remark = models.TextField() 
    approval_status = models.BooleanField(default=False)  
    carrier = models.CharField(max_length=255, blank=True, null=True)
    create_cr_by = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        land_name = self.land_purchase.mouza_name if self.land_purchase else "No Land"
        cash_name = self.cash_type.method_name if self.cash_type else "No Cash Type"
        owner_name = self.owner.owner_name if self.owner else "No Owner"
        return f"LandCreditVoucher #{self.id} - {land_name} - {owner_name} - {self.amount} - {self.date} - {cash_name}"







class LandLedgerEntry(models.Model):    
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('LandHeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True)
    cash_type = models.ForeignKey('CashMethod', on_delete=models.SET_NULL, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)  
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    head_of_account = models.ForeignKey('LandHeadOfAccount', on_delete=models.SET_NULL, null=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True) 
    date = models.DateField()
    description = models.TextField(blank=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    carrier = models.CharField(max_length=255, blank=True, null=True) 
    loan_status = models.CharField(max_length=255, blank=True, null=True)
    tbl_id = models.CharField(max_length=255, blank=True, null=True)
    tbl_name = models.CharField(max_length=255, blank=True, null=True)

   
    def __str__(self):
        land_name = self.land_purchase.mouza_name if self.land_purchase else "No Land"
        cash_name = self.cash_type.method_name if self.cash_type else "No Cash Type"
        type_name = self.type_name or "No Type"
        owner_name = self.owner.owner_name if self.owner else "No Owner"
        return f"LandLedgerEntry #{self.id} - {land_name} - {owner_name} - {self.date} - {cash_name} - {self.debit} - {type_name}"




class LandTransactionHistory(models.Model):
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('LandHeadOfExpense', on_delete=models.SET_NULL, null=True, blank=True)
    cash_type = models.ForeignKey('CashMethod', on_delete=models.SET_NULL, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)  
    head_of_account = models.ForeignKey(LandHeadOfAccount, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    type_name = models.CharField(max_length=100, null=True, blank=True) 
    reference = models.CharField(max_length=100, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)
    particulars = models.TextField(null=True, blank=True)
    tbl_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        land_name = self.land_purchase.mouza_name if self.land_purchase else "No Land"
        head_name = self.head_of_account.head_name if self.head_of_account else "No Head"
        owner_name = self.owner.owner_name if self.owner else "No Owner"
        return f"LandTransactionHistory #{self.id} - {land_name} - {owner_name} - {head_name} - {self.amount}"
    




class LandApprovalPayment(models.Model):
    land_purchase = models.ForeignKey('LandPurchase', on_delete=models.SET_NULL, null=True, blank=True) 
    owner = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True)
    land_uniq_id = models.CharField(max_length=50, verbose_name="Land Unique ID", null=True, blank=True)
    payment_type = models.CharField(max_length=50, default='purchase_pay')
    purch_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    debit_voucher = models.ForeignKey(LandDebitVoucher, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ add this
    purchase_date = models.DateField(null=True, blank=True)

    def __str__(self):
        land_name = self.land_purchase.mouza_name if self.land_purchase else "No Land"
        owner_name = self.owner.owner_name if self.owner else "No Owner"
        return f"LandApprovalPayment #{self.id} - {land_name} - {owner_name} - {self.purchase_date}"
        
        
        




class LandDocument(models.Model):
    FILE_CODE_CHOICES = [
        ('DL', 'DL (মূল দলিল)'),
        ('BY', 'BY (বায়না)'),
        ('HB', 'HB (হেবা)'),
        ('POA', 'POA (আমমোক্তারনামা)'),
        ('MT', 'MT (নামজারি)'),
        ('RS', 'RS (রেকর্ড)'),
        ('MAP', 'MAP (নকশা)'),
        ('TAX', 'TAX (খাজনা)'),
    ]

    sl_no = models.AutoField(primary_key=True, verbose_name="ক্রমিক")
    file_code = models.CharField(max_length=10, choices=FILE_CODE_CHOICES, verbose_name="ফাইল কোড")
    doc_no = models.CharField(max_length=100, verbose_name="দলিল নং")
    doc_type = models.CharField(max_length=100, verbose_name="দলিলের ধরন")
    doc_date = models.DateField(verbose_name="দলিলের তারিখ")
    seller = models.CharField(max_length=255, verbose_name="বিক্রেতা")
    buyer = models.CharField(max_length=255, verbose_name="ক্রেতা")
    mouza = models.CharField(max_length=255, verbose_name="মৌজা")
    khatian = models.CharField(max_length=100, verbose_name="খতিয়ান")
    dag_no = models.CharField(max_length=100, verbose_name="দাগ নং")
    land_amount = models.CharField(max_length=100, verbose_name="জমির পরিমাণ")
    project_block = models.CharField(max_length=255, verbose_name="প্রকল্প/ব্লক")
    file_location = models.ForeignKey(RecordFile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ফাইল লোকেশন")
    scanned_copy = models.FileField(upload_to='scanned_docs/', blank=True, null=True, verbose_name="স্ক্যান কপি")
    current_status = models.CharField(max_length=100, verbose_name="বর্তমান অবস্থা")
    assigned_person = models.CharField(max_length=255, verbose_name="দায়িত্বপ্রাপ্ত")
    last_update = models.DateTimeField(auto_now=True, verbose_name="সর্বশেষ আপডেট")
    comments = models.TextField(blank=True, null=True, verbose_name="মন্তব্য")

    def __str__(self):
        return f"{self.doc_no} - {self.file_code}"
        