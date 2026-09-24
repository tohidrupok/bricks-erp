from django.db import models
from projects.models import ProjectFirstLevelName


class Customer(models.Model):
    customer_name = models.CharField(max_length=200)
    profession = models.CharField(max_length=200, null=True, blank=True)
    lead_status = models.CharField(max_length=200, default='New') 
    lead_source = models.CharField(max_length=200, null=True, blank=True)
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, related_name='leads', null=True, blank=True)
    contact_no = models.CharField(max_length=15)
    address = models.TextField()
    description = models.TextField(null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    assign_to_user = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='customers/', null=True, blank=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.customer_name
        
 
 
 
class CustInfoBank(models.Model):   
    customer_name = models.CharField(max_length=200)
    profession = models.CharField(max_length=200, null=True, blank=True)
    contact_no = models.CharField(max_length=15)
    address = models.TextField()
    description = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    nid = models.CharField(max_length=15)
    dateofbrith = models.DateField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='customers/', null=True, blank=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.customer_name
        
        


class CustomerLead(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_leads')
    lead_name = models.CharField(max_length=255)
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True)
    first_contact_date = models.DateField(null=True, blank=True)
    first_contact_note = models.TextField(blank=True)

    followup_date = models.DateField(null=True, blank=True)
    followup_note = models.TextField(blank=True)

    create_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('close', 'Close'),
    ]
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='open')

    def __str__(self):
        return f"{self.customer.customer_name} - {self.lead_name}"
    



class CustomerFollowup(models.Model):
    lead_id = models.CharField(max_length=255)
    followup_date = models.DateField(null=True, blank=True)
    followup_note = models.TextField(blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Follow-up on {self.followup_date} (Lead: {self.lead_id})"
        
        
        
class Sale(models.Model):
    SALE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    sales_agent = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='')
    
    sale_date = models.DateField()
    booking_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    sales_discount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Discount amount applied on the sale"
    )
    
    payment_mode = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('other', 'Other')
    ])
    
    sale_status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='pending')
    
    payment_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        discounted_price = self.total_amount - self.sales_discount
        self.balance_due = discounted_price - self.payment_received
        
        # Optional: prevent negative balance_due
        if self.balance_due < 0:
            self.balance_due = 0
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Sale of {self.project_name} to {self.customer} on {self.sale_date}"
        
        
        

class BulkSMS(models.Model):
    """
    Represents a bulk SMS message sent to multiple customers.
    Recipients are tracked via BulkSMSRecipient.
    """
    message = models.TextField()

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Sent', 'Sent'),
        ('Failed', 'Failed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SMS #{self.id} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class BulkSMSRecipient(models.Model):
    """
    Tracks SMS status per customer.
    """
    bulk_sms = models.ForeignKey(BulkSMS, on_delete=models.CASCADE, related_name='recipients')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=(('Sent', 'Sent'), ('Failed', 'Failed')),
        default='Pending'
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer.customer_name} - {self.status}"
