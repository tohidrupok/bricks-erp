from django.db import models
from django.utils import timezone
from projects.models import ProjectFirstLevelName


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='campaigns/', null=True, blank=True)
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    remark = models.TextField(blank=True, null=True)
    campaign_id = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.campaign_id:
            last_id = Campaign.objects.all().order_by('id').last()
            next_num = last_id.id + 1 if last_id else 1
            self.campaign_id = f"CMP-{next_num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.campaign_id})"


class Customer(models.Model):
    customer_name = models.CharField(max_length=200)
    profession = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=200, null=True, blank=True)
    lead_status = models.CharField(max_length=200, default='New')
    lead_source = models.CharField(max_length=200, null=True, blank=True)
    project = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, related_name='leads_customer', null=True, blank=True)
    contact_no = models.CharField(max_length=15)
    secondary_phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField()
    description = models.TextField(null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    anniversary_date = models.DateField(null=True, blank=True)
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
    STAGE_CHOICES = [
        ('New', 'New'),
        ('Booking', 'Booking'),
        ('Booked', 'Booked'),
        ('Negotiation Meeting', 'Negotiation Meeting'),
        ('Sold', 'Sold'),
        ('Junk', 'Junk'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('close', 'Close'),
        ('junk', 'Junk'),
    ]

    lead_code = models.CharField(max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_leads')
    lead_name = models.CharField(max_length=255)
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.SET_NULL, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_campaigns')

    # Lead Details
    lead_category = models.CharField(max_length=100, null=True, blank=True)
    cr = models.CharField(max_length=200, null=True, blank=True, verbose_name="If CR")

    # Pipeline stage
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default='New')

    first_contact_date = models.DateField(null=True, blank=True)
    first_contact_note = models.TextField(blank=True)

    followup_date = models.DateField(null=True, blank=True)
    followup_note = models.TextField(blank=True)

    create_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    # Customer feedback + sales possibility marking
    customer_feedback_rating = models.IntegerField(default=0, help_text="Customer rating (1-5)")
    salesperson_marking_possibility = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Sales possibility percentage")

    query = models.CharField(max_length=255, blank=True, null=True)

    @classmethod
    def generate_next_code(cls):
        today_str = timezone.now().strftime('%y%m%d')
        prefix = f"L{today_str}"
        last_lead = cls.objects.filter(lead_code__startswith=prefix).order_by('id').last()
        next_num = 1
        if last_lead and last_lead.lead_code:
            try:
                next_num = int(last_lead.lead_code.split('-')[-1]) + 1
            except (ValueError, IndexError):
                next_num = 1
        return f"{prefix}-{next_num:04d}"

    def save(self, *args, **kwargs):
        if not self.lead_code:
            self.lead_code = CustomerLead.generate_next_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.customer_name} - {self.lead_name}"


class CustomerFollowup(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('followup', 'Followup'),
        ('task_visit', 'Task/Visit'),
    ]

    lead = models.ForeignKey(CustomerLead, on_delete=models.CASCADE, related_name='followups', null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='followup')

    followup_date = models.DateField(null=True, blank=True)
    followup_note = models.TextField(blank=True)
    communication_status = models.CharField(max_length=100, blank=True, null=True)

    task_type = models.CharField(max_length=100, blank=True, null=True)
    task_date = models.DateField(null=True, blank=True)
    task_status = models.CharField(max_length=100, blank=True, null=True)
    visit_place = models.CharField(max_length=255, blank=True, null=True)
    task_note = models.CharField(max_length=255, blank=True, null=True)  # NEW
    comment = models.TextField(blank=True, null=True)

    salesperson_marking = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, null=True, blank=True)

    next_activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, null=True, blank=True)
    next_followup_date = models.DateTimeField(null=True, blank=True)
    next_followup_note = models.CharField(max_length=255, blank=True, null=True)

    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.create_date.strftime('%d-%m-%Y')}"

    class Meta:
        ordering = ['-create_date']
        
        

class Sale(models.Model):
    SALE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    
    # Corrected: Changed from invalid choice mapping to a proper text field for the sales agent's name
    sales_agent = models.CharField(max_length=200, blank=True, null=True)

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

        if self.balance_due < 0:
            self.balance_due = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale of {self.project_name} to {self.customer} on {self.sale_date}"


class BulkSMS(models.Model):
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
    bulk_sms = models.ForeignKey(BulkSMS, on_delete=models.CASCADE, related_name='recipients')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    # Corrected: Added 'Pending' to choices since it is set as the default value
    status = models.CharField(
        max_length=20,
        choices=(('Pending', 'Pending'), ('Sent', 'Sent'), ('Failed', 'Failed')),
        default='Pending'
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer.customer_name} - {self.status}"