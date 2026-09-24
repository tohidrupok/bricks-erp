from django.db import models
from projects.models import ProjectFirstLevelName,Donation
from crm.models import Customer
from accounting.models import CashType,HeadOfAccount
from django.utils import timezone
from purchase.models import HeadOfExpense



class Sales(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Completed', 'Completed'),
    ]
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    floor_no = models.CharField(max_length=20)
    unit_no = models.CharField(max_length=20)
    unit_count = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    pay_amount = models.DecimalField(max_digits=15, decimal_places=2)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    head = models.ForeignKey(HeadOfAccount, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    create_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Sale - {self.project_name} - Unit {self.unit_no}"




# class FlatPlot(models.Model):
#     flat_no = models.IntegerField()
#     unit_no = models.IntegerField()
#     project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, null=True, blank=True)

#     def __str__(self):
#         return f"Flat {self.flat_no} - Unit {self.unit_no}"



class FlatPlot(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, null=True, blank=True)
    flat_no = models.IntegerField()
    unit_no = models.IntegerField()
    type = models.CharField(max_length=10, choices=[('flat', 'Flat'), ('plot', 'Plot')], default='flat')
    status = models.CharField(max_length=20, default='Pending')



class PropertyFlatPlot(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE, null=True, blank=True)
    flat_no = models.IntegerField()
    unit_no = models.IntegerField()
    type = models.CharField(max_length=10, choices=[('flat', 'Flat'), ('plot', 'Plot')], default='flat')
    property_name = models.CharField(max_length=255, blank=True, null=True)
    property_code = models.CharField(max_length=100, blank=True, null=True)
    square_fit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    per_square_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"{self.type.capitalize()} {self.flat_no}-{self.unit_no} in {self.project_name}"



class PropertySales(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=[('flat', 'Flat'), ('plot', 'Plot')])
    flat_no = models.IntegerField()
    unit_no = models.IntegerField()
    property_name = models.CharField(max_length=255, blank=True, null=True)
    property_code = models.CharField(max_length=100, blank=True, null=True)
    square_fit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    per_square_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    customer_name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='PropertySales_cus_vr')
    utility = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parking = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    media_persion = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='PropertySales_media_vr')
    commisoin_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    media_commisoin = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    donaton_name = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)
    lilahetalah_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lilahetalah_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_date = models.DateField(default=timezone.now)
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    pay_last_status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"Sale of {self.type.capitalize()} {self.flat_no} Unit {self.unit_no} - {self.project_name}"




class InstallmentPayment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('booking_money', 'Booking Money'),
        ('down_payment', 'Down Payment'),
        ('installment_1', '1st Installment'),
        ('installment_2', '2nd Installment'),
        ('installment_3', '3rd Installment'),
        ('installment_4', '4th Installment'),
        ('installment_5', '5th Installment'),
        ('installment_6', '6th Installment'),
        ('installment_7', '7th Installment'),
        ('installment_8', '8th Installment'),
        ('installment_9', '9th Installment'),
        ('installment_10', '10th Installment'),
        ('installment_11', '11th Installment'),
        ('installment_12', '12th Installment'),
        ('installment_13', '13th Installment'),
        ('installment_14', '14th Installment'),
        ('installment_15', '15th Installment'),
        ('installment_16', '16th Installment'),
        ('installment_17', '17th Installment'),
        ('installment_18', '18th Installment'),
        ('installment_19', '19th Installment'),
        ('installment_20', '20th Installment'),
        
    ]

    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    customer_name = models.ForeignKey(Customer, on_delete=models.CASCADE)
    property_sales = models.ForeignKey(PropertySales, on_delete=models.CASCADE)  # link to sale record
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES)
    month = models.DateField()  # store the first day of the month
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cheque_posted = models.BooleanField(default=False)
    cheque_date = models.DateField(null=True, blank=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    cheque_no = models.CharField(max_length=100, blank=True, null=True)
    mr_or_bill_no = models.CharField(max_length=100, blank=True, null=True)
    pay_status = models.CharField(max_length=20, default='Pending')
    pay_note = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.get_payment_type_display()} - {self.month.strftime('%b %Y')}"
        
        

class SharePlot(models.Model):
    sl = models.AutoField(primary_key=True)
    project_name = models.ForeignKey(
        ProjectFirstLevelName,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    persion_no = persion_no = models.IntegerField(null=True, blank=True)
    decimal = models.DecimalField(max_digits=10, decimal_places=2)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    share_val = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if self.persion_no and self.persion_no > 0:
            self.area = self.decimal / self.persion_no
            self.share_val = self.value / self.persion_no
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"SharePlot {self.sl}"

    @property
    def share_person_count(self):
        return self.persons.count()


class SharePerson(models.Model):
    share_plot = models.ForeignKey(
        SharePlot, on_delete=models.CASCADE, related_name="persons"
    )
    name = models.CharField(max_length=100)
    pay_status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.name


class ShareInstallmentPayment(models.Model):
    sl = models.AutoField(primary_key=True)
    PAYMENT_TYPE_CHOICES = [
        ('booking_money', 'Booking Money'),
        ('down_payment', 'Down Payment'),
        ('installment_1', '1st Installment'),
        ('installment_2', '2nd Installment'),
        ('installment_3', '3rd Installment'),
        ('installment_4', '4th Installment'),
        ('installment_5', '5th Installment'),
    ]
    
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    customer_name = models.ForeignKey(SharePerson, on_delete=models.CASCADE)
    share_sales = models.ForeignKey(SharePlot, on_delete=models.CASCADE, default=1)
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES)
    month = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cheque_posted = models.BooleanField(default=False)
    cheque_date = models.DateField(null=True, blank=True)
    cash_type = models.ForeignKey(CashType, on_delete=models.SET_NULL, null=True)
    cheque_no = models.CharField(max_length=100, blank=True, null=True)
    mr_or_bill_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    pay_status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.get_payment_type_display()} - {self.month.strftime('%b %Y')}"