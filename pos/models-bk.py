from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class WorkPeriod(models.Model):
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='started_periods')
    ended_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ended_periods')
    is_active = models.BooleanField(default=True)

    def total_sales(self):
        orders = RestaurantOrder.objects.filter(work_period=self, status='COMPLETED')
        return sum(o.net_total for o in orders) or Decimal('0.00')

    def __str__(self):
        return f"Work Period #{self.id} ({'Active' if self.is_active else 'Closed'})"


class RestaurantCustomer(models.Model):
    CUSTOMER_TYPES = [
        ('WALK_IN', 'Walk-in'),
        ('REGULAR', 'Regular'),
        ('VIP', 'VIP'),
        ('ONLINE', 'Online Platform'),
    ]
    customer_code = models.CharField(max_length=50, unique=True, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='WALK_IN')
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            last = RestaurantCustomer.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.customer_code = f"CUS-{nxt:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_code} - {self.name}"


class RestaurantSupplier(models.Model):
    supplier_code = models.CharField(max_length=50, unique=True, editable=False)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.supplier_code:
            last = RestaurantSupplier.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.supplier_code = f"SUP-{nxt:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"


class RawMaterial(models.Model):
    UNIT_CHOICES = [('KG', 'KG'), ('GM', 'Gram'), ('LTR', 'Litre'), ('PCS', 'Pieces'), ('PKT', 'Packet')]
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=5.000)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.unit})"


class MenuItemCategory(models.Model):
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=20, default='#1e293b')

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(MenuItemCategory, on_delete=models.CASCADE, related_name='items')
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class BillOfQuantities(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('PENDING', 'Pending Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')]
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='boq')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='boq_approvals')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BOQ for {self.menu_item.name} [{self.status}]"


class BOQItem(models.Model):
    boq = models.ForeignKey(BillOfQuantities, on_delete=models.CASCADE, related_name='ingredients')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)


class RestaurantTable(models.Model):
    table_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(default=4)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Table {self.table_number}"


class Requisition(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('COMPLETED', 'Completed')]
    req_no = models.CharField(max_length=50, unique=True, editable=False)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.req_no:
            last = Requisition.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.req_no = f"REQ-{nxt:05d}"
        super().save(*args, **kwargs)


class RequisitionItem(models.Model):
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=3)


class PurchaseOrder(models.Model):
    po_no = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(RestaurantSupplier, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.po_no:
            last = PurchaseOrder.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.po_no = f"PO-{nxt:05d}"
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class RestaurantOrder(models.Model):
    CHANNEL_CHOICES = [
        ('DINE_IN', 'Dine In'),
        ('FOODPANDA', 'Foodpanda'),
        ('FOODI', 'Foodi'),
        ('PATHAO', 'Pathao'),
        ('DELIVERY', 'Delivery'),
        ('TAKEAWAY', 'Takeaway'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('VISA', 'Visa'),
        ('AMEX', 'Amex'),
        ('MASTERCARD', 'Mastercard'),
        ('BKASH', 'bKash'),
        ('NAGAD', 'Nagad'),
    ]
    order_no = models.CharField(max_length=50, unique=True, editable=False)
    work_period = models.ForeignKey(WorkPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(RestaurantCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='DINE_IN')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.order_no:
            last = RestaurantOrder.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.order_no = f"ORD-{nxt:05d}"
        super().save(*args, **kwargs)


class RestaurantOrderItem(models.Model):
    order = models.ForeignKey(RestaurantOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class OrderReturn(models.Model):
    return_no = models.CharField(max_length=50, unique=True, editable=False)
    order = models.ForeignKey(RestaurantOrder, on_delete=models.CASCADE, related_name='returns')
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    returned_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.return_no:
            last = OrderReturn.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.return_no = f"RET-{nxt:05d}"
        super().save(*args, **kwargs)


class AccountingTransaction(models.Model):
    TXN_TYPES = [('RECEIPT', 'Payment Received'), ('PAYMENT', 'Payment Disbursed')]
    txn_no = models.CharField(max_length=50, unique=True, editable=False)
    txn_type = models.CharField(max_length=10, choices=TXN_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    customer = models.ForeignKey(RestaurantCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(RestaurantSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(RestaurantOrder, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.txn_no:
            last = AccountingTransaction.objects.order_by('-id').first()
            nxt = (last.id + 1) if last else 1
            self.txn_no = f"TXN-{nxt:05d}"
        super().save(*args, **kwargs)