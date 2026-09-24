from django.db import models
#from .models import Project
from properties.models import Project,PropertyOwner
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import calendar


class ProjectLocation(models.Model):
    location_name = models.CharField(max_length=255)
    area = models.CharField(max_length=255)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location_name} ({self.area})"
    
    
class ProjectFirstLevelName(models.Model):
    PROJECT_TYPE_CHOICES = [
        ('Own Project', 'Own Project'),
        ('Joint Venture Project', 'Joint Venture Project'),
        ('Only Construction Company', 'Only Construction Company'),
    ]
    project_first_name = models.CharField(max_length=255, default='')
    location = models.ForeignKey(ProjectLocation, on_delete=models.SET_NULL, null=True, blank=True)
    project_type = models.CharField(max_length=255,choices=PROJECT_TYPE_CHOICES,default='Own Project')
    project_owner = models.ForeignKey(PropertyOwner, on_delete=models.SET_NULL, null=True, blank=True)
    project_start_month = models.CharField(max_length=50, default='April 2025')  
    project_duration = models.PositiveIntegerField(default=12, help_text="Duration in months")
    project_size_sq_ft = models.PositiveIntegerField(default=1000)
    number_of_units = models.PositiveIntegerField(default=1)
    number_of_floors = models.PositiveIntegerField(default=1)
    units_per_floor = models.PositiveIntegerField(default=1)
    soil_test_completed = models.BooleanField(default=False)
    drawing_test_completed = models.BooleanField(default=False)
    agreement_completed = models.BooleanField(default=False)
    current_date = models.DateTimeField(auto_now_add=True)
    soil_test = models.FileField(upload_to='soil_documents/', null=True, blank=True)
    drawing_test = models.FileField(upload_to='drawing_documents/', null=True, blank=True)
    agreement_document = models.FileField(upload_to='agreement_documents/', null=True, blank=True)


    # Costing fields
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    percentage_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    final_total_with_extra = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # New fields
    project_start_date = models.DateField(null=True, blank=True)
    project_end_date = models.DateField(null=True, blank=True)

    
    def __str__(self):
        return f"{self.project_first_name} - {self.location}"

  


class ProjectDocument(models.Model):

    DOCUMENT_TYPE_CHOICES = [
        ('agreement', 'Agreement / Land Papers'),
        ('test', 'Test'),
        ('drawing', 'Drawing'),
        ('certification', 'Certification'),
        ('approval', 'Approvals'),
    ]

    project = models.ForeignKey(
        'ProjectFirstLevelName',
        on_delete=models.CASCADE,
        related_name='project_documents'
    )

    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES
    )

    document = models.FileField(
        upload_to='project_documents/'
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.project.project_first_name} - {self.document_type}"
        

class ProjectSchedule(models.Model):

    project = models.OneToOneField(
        'ProjectFirstLevelName',
        on_delete=models.CASCADE,
        related_name='project_schedule'
    )

    sub_structure = models.PositiveIntegerField(
        default=0,
        help_text="Duration in months"
    )

    super_structure = models.PositiveIntegerField(
        default=0,
        help_text="Duration in months"
    )

    finishing = models.PositiveIntegerField(
        default=0,
        help_text="Duration in months"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Schedule - {self.project.project_first_name}"
        
class ProjectScheduleItem(models.Model):

    SCHEDULE_TYPE_CHOICES = [
        ('sub_structure', 'Sub Structure'),
        ('super_structure', 'Super Structure'),
        ('finishing', 'Finishing'),
    ]

    project = models.ForeignKey(
        'ProjectFirstLevelName',
        on_delete=models.CASCADE,
        related_name='schedule_items'
    )

    subject_name = models.CharField(max_length=255)

    start_date = models.DateField()

    end_date = models.DateField()

    # Actual dates
    actual_start_date = models.DateField(
        null=True,
        blank=True
    )

    actual_end_date = models.DateField(
        null=True,
        blank=True
    )

    schedule_type = models.CharField(
        max_length=50,
        choices=SCHEDULE_TYPE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_first_name} - {self.subject_name}"
     
        
# class BOQ(models.Model):
#     project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
#     category_type = models.CharField(
#         max_length=100,
#         choices=[('Material Purchase Cost', 'Material Purchase Cost'), ('Labor Cost', 'Labor Cost')],
#         default='Material Purchase Cost'
#     )
#     category_name = models.CharField(max_length=255)
#     supplier_name = models.ForeignKey('Suppliers', on_delete=models.SET_NULL, null=True, blank=True)
#     item_name = models.CharField(max_length=255)
#     unit = models.CharField(max_length=50)
#     qty = models.DecimalField(max_digits=20, decimal_places=2)  # Change to DecimalField
#     rate = models.DecimalField(max_digits=20, decimal_places=2)
#     amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    

#     def __str__(self):
#         return self.project_name.project_first_name


class BOQ(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    category_type = models.CharField(
        max_length=100,
        choices=[('Materials Purchase Cost', 'Materials Purchase Cost'), ('Labour Cost', 'Labour Cost')],
        default='Materials Purchase Cost'
    )
    type_name = models.CharField(max_length=100, default='')
    category_name = models.CharField(max_length=255)
    supplier_name = models.ForeignKey('Suppliers', on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.ForeignKey('purchase.HeadOfRequisition', on_delete=models.CASCADE)
    unit = models.CharField(max_length=50)
    qty = models.DecimalField(max_digits=20, decimal_places=2)  
    rate = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    status_item = models.CharField(max_length=50, default='') 
    update_item = models.CharField(max_length=100, default='')
    boq_date = models.DateField(null=True, blank=True)

    # def __str__(self):
    #     return self.project_name.project_first_name
    
    def __str__(self):
        return f"{self.project_name.project_first_name} - {self.category_type}"
        


class BoRevisedItem(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    original_boq = models.ForeignKey('BOQ', on_delete=models.SET_NULL, null=True, blank=True)
    linked_boq = models.ForeignKey('BOQ', on_delete=models.SET_NULL, null=True, blank=True, related_name='revised_entries')  # <-- NEW FIELD

    category_type = models.CharField(max_length=100)
    category_name = models.CharField(max_length=255)
    supplier_name = models.ForeignKey('Suppliers', on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.ForeignKey('purchase.HeadOfRequisition', on_delete=models.CASCADE)
    unit = models.CharField(max_length=50)
    qty = models.DecimalField(max_digits=20, decimal_places=2)
    rate = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_new_entry = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} (Revised)"
        
        

class EmployeeCost(models.Model):
    project_name = models.CharField(max_length=200, default='Default Project')
    employee_name = models.CharField(max_length=100)
    first_month_salary = models.DecimalField(max_digits=10, decimal_places=2)
    project_duration_months = models.IntegerField()
    total_salary = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    yearly_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.project_name} - {self.employee_name}"


class SafetyEquipment(models.Model):
    project_name = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.item_cost and self.quantity:
            self.total_cost = self.item_cost * self.quantity
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.project_name} - {self.item_name}"


class BoQType(models.Model):    
    boq_type_name = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.boq_type_name
        
        

class BoQCategory(models.Model):    
    boq_cat_type = models.CharField(max_length=100, default='')
    boq_cat_name = models.CharField(max_length=255, blank=True, null=True)  

    def __str__(self):
        return f"{self.boq_cat_type} - {self.boq_cat_name or 'N/A'}"
    
    


# class BoQCategory(models.Model):
#     TYPE_CHOICES = [
#         ('Material Purchase Cost', 'Material Purchase Cost'),
#         ('Labor Cost', 'Labor Cost'),
#     ]
#     boq_cat_type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='General')
#     boq_cat_name = models.CharField(max_length=255, unique=True)


class ExpenseCost(models.Model):
    project_name = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.item_cost and self.quantity:
            self.total_cost = self.item_cost * self.quantity
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.project_name} - {self.item_name}"
    

class SiteSupervisor(models.Model):
    supervisor_name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    pay_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.supervisor_name
    
class Suppliers(models.Model):
    supplier_name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    pay_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.supplier_name
        
        
        
class ContractorActivity(models.Model):
    contractor = models.ForeignKey(SiteSupervisor, on_delete=models.CASCADE) 
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE) 
    working_head = models.CharField(max_length=100, help_text="E.g., Basement, Piling, First Floor")
    create_date = models.DateField(auto_now_add=True)
    work_start_date = models.DateField()
    work_end_date = models.DateField()
    work_description = models.TextField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=[
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('paused', 'Paused')
    ], default='ongoing')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.contractor} - {self.working_head} ({self.work_start_date} to {self.work_end_date})"
        
        
        
        
class MaterialEntry(models.Model):
    PARTY_CHOICES = (
        ('BTP Office', 'BTP Office'),
        ('Client', 'Client'),
    )

    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    client_name = models.CharField(max_length=100)
    date = models.DateField()

    party = models.CharField(max_length=20, choices=PARTY_CHOICES)
    sl = models.IntegerField()
    description = models.CharField(max_length=100)
    band = models.CharField(max_length=100)
    quantity = models.FloatField()
    rate = models.FloatField()
    amount = models.FloatField(blank=True)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_name} - {self.party} - {self.description}"
        
        
        
# class Donation(models.Model):
#     donation_type = models.CharField(max_length=255, null=True, blank=True)
#     donation_name = models.CharField(max_length=255, null=True, blank=True)
#     address = models.CharField(max_length=255, null=True, blank=True)
#     phone = models.CharField(max_length=20, null=True, blank=True)
#     description = models.TextField(blank=True)
#     active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.donation_name





class Donation(models.Model):
    donation_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Combine donation_type and donation_name before saving
        if self.donation_name:
            self.donation_name = f"{self.donation_name}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.donation_name
