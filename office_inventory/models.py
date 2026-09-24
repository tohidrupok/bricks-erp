import uuid
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Safe import to prevent ModuleNotFoundError if the app name is different
try:
    from project.models import ProjectFirstLevelName
except ImportError:
    try:
        from projects.models import ProjectFirstLevelName
    except ImportError:
        ProjectFirstLevelName = None

RDA_EMPLOYEE_MODEL = 'hrm.RdaEmployee'
RESTAURANT_EMPLOYEE_MODEL = 'restahrm.RestaurantEmployee'


def _generate_no(prefix):
    return f"{prefix}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"


# ---------------------------------------------------------------------------
# Master data
# ---------------------------------------------------------------------------

class Department(models.Model):
    DEPT_TYPES = (
        ('btp', 'BTP Office'),
        ('restaurant', 'Restaurant'),
    )

    dept_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    dept_type = models.CharField(max_length=20, choices=DEPT_TYPES, default='btp')

    # Generic Foreign Key to support both hrm.RdaEmployee and restahrm.RestaurantEmployee
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    manager = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['dept_id']

    def save(self, *args, **kwargs):
        if not self.dept_id:
            last = Department.objects.order_by('-id').first()
            next_id = last.id + 1 if last else 1
            self.dept_id = f"BTP-DEPT-{next_id:05d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dept_id} - {self.name}"


# import uuid
# from django.db import models
# from django.utils import timezone
# RDA_EMPLOYEE_MODEL = 'hrm.RdaEmployee'
# RESTAURANT_EMPLOYEE_MODEL = 'restahrm.RestaurantEmployee'


# def _generate_no(prefix):
#     return f"{prefix}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"


# # ---------------------------------------------------------------------------
# # Master data
# # ---------------------------------------------------------------------------

# class Department(models.Model):
#     dept_id = models.CharField(
#         max_length=20,
#         unique=True,
#         blank=True
#     )
#     name = models.CharField(max_length=100)

#     manager = models.ForeignKey(
#         RDA_EMPLOYEE_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='managed_departments'
#     )

#     class Meta:
#         ordering = ['dept_id']

#     def save(self, *args, **kwargs):
#         if not self.dept_id:
#             last = Department.objects.order_by('-id').first()
#             next_id = last.id + 1 if last else 1
#             self.dept_id = f"BTP-DEPT-{next_id:05d}"

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.dept_id} - {self.name}"
        
        

class Location(models.Model):
    """Physical store / warehouse / branch office for location-wise inventory.

    Locations can now be nested (`parent`) so you can model things like
    "Kitchen" as a sub-location under either "Head Office" or a specific
    "Restaurant" branch, and tagged with `location_type` so
    stock/requisitions/assignments/ledger entries can all be sliced
    place-wise (e.g. one restaurant branch vs another vs Head Office).
    """
    TYPE_HEAD_OFFICE = 'HEAD_OFFICE'
    TYPE_RESTAURANT = 'RESTAURANT'
    TYPE_KITCHEN = 'KITCHEN'
    TYPE_WAREHOUSE = 'WAREHOUSE'
    TYPE_OTHER = 'OTHER'
    LOCATION_TYPE_CHOICES = [
        (TYPE_HEAD_OFFICE, 'Head Office'),
        (TYPE_RESTAURANT, 'Restaurant'),
        (TYPE_KITCHEN, 'Kitchen'),
        (TYPE_WAREHOUSE, 'Warehouse'),
        (TYPE_OTHER, 'Other'),
    ]

    code = models.CharField(max_length=20, unique=True)              # e.g. LOC-001
    name = models.CharField(max_length=100)                          # e.g. Head Office Store
    address = models.TextField(blank=True)

    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPE_CHOICES, default=TYPE_OTHER,
        help_text="Head Office, Restaurant, Kitchen (under either), Warehouse, or Other."
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sub_locations',
        help_text="e.g. set this to 'Head Office' or a specific Restaurant to model "
                   "its Kitchen as a sub-location."
    )

    class Meta:
        ordering = ['code']

    @property
    def full_path(self):
        """e.g. 'Gulshan Restaurant > Kitchen' for breadcrumb-style display."""
        return f"{self.parent.name} > {self.name}" if self.parent_id else self.name

    def __str__(self):
        return self.full_path


class Category(models.Model):
    """Item category, e.g. Kitchen Equipment, Furniture, Stationery, IT Asset."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Inventory item - category-wise AND location-wise
# ---------------------------------------------------------------------------

class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'Pcs'),
        ('REAM', 'Ream'),
        ('BOX', 'Box'),
        ('SET', 'Set'),
        ('KG', 'Kg'),
        ('LTR', 'Litre'),
        ('UNIT', 'Unit'),
        ('GRAM', 'Gram'),
    ]

    # Leave blank to auto-generate
    item_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    name = models.CharField(max_length=150)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='items',
        null=True,
        blank=True
    )

    # Remove this field if you no longer use Location
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name='items',
        null=True,
        blank=True
    )

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='PCS'
    )

    min_stock = models.PositiveIntegerField(default=0)
    current_stock = models.PositiveIntegerField(default=0)

    purchase_date = models.DateField(null=True, blank=True)
    purchase_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_asset = models.BooleanField(
        default=False,
        help_text="Tick for returnable assets (furniture, laptop, etc.) that get assigned to an employee instead of being consumed."
    )

    class Meta:
        ordering = ['category', 'item_code']

    @property
    def status(self):
        return "LOW STOCK" if self.current_stock <= self.min_stock else "OK"

    def save(self, *args, **kwargs):
        if not self.item_code:
            last = InventoryItem.objects.order_by('-id').first()
            next_id = last.id + 1 if last else 1
            self.item_code = f"BTP-INV-{next_id:05d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_code} - {self.name}"
        
        
# ---------------------------------------------------------------------------
# Requisition workflow
# ---------------------------------------------------------------------------

class Requisition(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_DEPT_APPROVED = 'DEPT_APPROVED'
    STATUS_DEPT_REJECTED = 'DEPT_REJECTED'
    STATUS_ADMIN_APPROVED = 'ADMIN_APPROVED'
    STATUS_ADMIN_REJECTED = 'ADMIN_REJECTED'
    STATUS_ISSUED = 'ISSUED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_DEPT_APPROVED, 'Department Approved'),
        (STATUS_DEPT_REJECTED, 'Department Rejected'),
        (STATUS_ADMIN_APPROVED, 'Admin Approved'),
        (STATUS_ADMIN_REJECTED, 'Admin Rejected'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    req_no = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='requisitions')
    employee = models.ForeignKey(RDA_EMPLOYEE_MODEL, on_delete=models.PROTECT, related_name='requisitions')
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='requisitions')

    # Which place (Head Office / a Restaurant branch / a Kitchen under
    # either) this requisition is for - drives project-wise reporting and
    # is copied onto the StockLedger entry when the requisition is issued.
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitions'
    )

    # Snapshot of the item's unit at the time of request, so historical
    # requisitions still show the correct unit even if the item master's
    # unit is changed later. Auto-filled from `item.unit` in save() if blank.
    unit = models.CharField(max_length=10, choices=InventoryItem.UNIT_CHOICES, blank=True)

    requested_qty = models.PositiveIntegerField()
    approved_qty = models.PositiveIntegerField(null=True, blank=True)
    issued_qty = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    dept_approver = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='dept_approvals'
    )
    dept_approved_at = models.DateTimeField(null=True, blank=True)

    admin_approver = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='admin_approvals'
    )
    admin_approved_at = models.DateTimeField(null=True, blank=True)

    store_officer = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='store_issues'
    )
    issued_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.req_no:
            self.req_no = _generate_no("REQ")
        if not self.unit and self.item_id:
            self.unit = self.item.unit
        super().save(*args, **kwargs)

    def __str__(self):
        return self.req_no


# ---------------------------------------------------------------------------
# Stock ledger - every stock movement (IN / OUT) is recorded here
# ---------------------------------------------------------------------------

class StockLedger(models.Model):
    TYPE_IN = 'IN'
    TYPE_OUT = 'OUT'
    TYPE_CHOICES = [(TYPE_IN, 'IN'), (TYPE_OUT, 'OUT')]

    date = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=50, blank=True)   # requisition req_no / PO / assignment id
    type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='ledger_entries')
    qty_in = models.PositiveIntegerField(default=0)
    qty_out = models.PositiveIntegerField(default=0)
    balance = models.IntegerField()
    user = models.ForeignKey(RDA_EMPLOYEE_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Place/department-wise traceability for this specific movement (e.g.
    # "OUT to Gulshan Restaurant Kitchen" vs "OUT to Head Office"), so the
    # ledger stays specific to user/department/place, not just item-wise.
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries'
    )
    unit = models.CharField(max_length=10, choices=InventoryItem.UNIT_CHOICES, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date:%Y-%m-%d %H:%M} | {self.item.item_code} | {self.type} | Bal:{self.balance}"


# ---------------------------------------------------------------------------
# Purchase - brings new stock into a location; feeds the stock ledger (IN)
# ---------------------------------------------------------------------------

class Purchase(models.Model):
    STATUS_ORDERED = 'ORDERED'
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_ORDERED, 'Ordered'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    purchase_no = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='purchases')
    # Set automatically when this purchase is generated from an admin-approved
    # requisition via the Purchase Department panel. When present, the
    # purchase officer only APPROVES it - item & qty are locked from the
    # requisition and cannot be edited.
    requisition = models.ForeignKey(
        'Requisition', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases'
    )
    supplier = models.CharField(max_length=150, blank=True)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ORDERED)
    received_by = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases_received'
    )
    received_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.purchase_no:
            self.purchase_no = _generate_no("PUR")
        if not self.total_amount:
            self.total_amount = (self.unit_price or 0) * (self.qty or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.purchase_no


# ---------------------------------------------------------------------------
# Assignment type - dynamic, admin-defined "who/what can an item be assigned
# to". Not hard-coded to Employee only: an org can add "Restaurant",
# "Department Pool", "Warehouse", "Vendor Loan", etc. from the UI.
#
# `requires_employee` controls which field the Assignment form needs:
#   - True  -> the `employee` FK must be filled (e.g. type "Employee")
#   - False -> the free-text `assignee_name` field is used instead
#              (e.g. type "Restaurant" -> assignee_name = "Gulshan Branch")
# ---------------------------------------------------------------------------

class AssignmentType(models.Model):
    # Which employee table (if any) this assign type pulls its dropdown from.
    SOURCE_NONE = 'NONE'
    SOURCE_HR = 'HR'
    SOURCE_RESTAURANT = 'RESTAURANT'
    EMPLOYEE_SOURCE_CHOICES = [
        (SOURCE_NONE, 'No specific employee (free-text name)'),
        (SOURCE_HR, 'HR / Office Employee (hrm.RdaEmployee)'),
        (SOURCE_RESTAURANT, 'Restaurant Employee (RestaurantEmployee)'),
    ]

    name = models.CharField(max_length=100, unique=True)   # e.g. Employee, Restaurant, Department Pool
    requires_employee = models.BooleanField(
        default=True,
        help_text="Tick if this assign type hands the item to a specific employee. "
                   "Untick for non-employee targets (department pool, warehouse, etc.) "
                   "where a free-text name is used instead. Kept for backward "
                   "compatibility - `employee_source` below is the more precise control."
    )
    employee_source = models.CharField(
        max_length=20, choices=EMPLOYEE_SOURCE_CHOICES, default=SOURCE_HR,
        help_text="Controls which dropdown the Assign form shows: HR Employee, "
                   "Restaurant Employee, or plain free-text (e.g. 'Head Office Pool')."
    )
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Asset assignment (direct hand-over of an item to an employee OR any other
# dynamic assign-type target, e.g. a restaurant branch, a department pool).
# Location-wise: tracks which location the asset currently sits at/deployed to.
# ---------------------------------------------------------------------------

class EmployeeAssignment(models.Model):
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_RETURNED = 'RETURNED'
    STATUS_CHOICES = [(STATUS_ASSIGNED, 'Assigned'), (STATUS_RETURNED, 'Returned')]

    assignment_type = models.ForeignKey(
        AssignmentType, on_delete=models.PROTECT, related_name='assignments',
        null=True, blank=True,
        help_text="Who/what this item is assigned to (Employee, Restaurant, Department, etc.)"
    )
    # Required only when assignment_type.employee_source == 'HR'
    # (requires_employee True, for backward compatibility).
    employee = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, on_delete=models.CASCADE, related_name='assigned_items',
        null=True, blank=True,
    )
    # Required only when assignment_type.employee_source == 'RESTAURANT'.
    # Kept as a separate FK (rather than reusing `employee`) since restaurant
    # staff live in a different table with a different shape.
    restaurant_employee = models.ForeignKey(
        RESTAURANT_EMPLOYEE_MODEL, on_delete=models.CASCADE, related_name='assigned_items',
        null=True, blank=True,
    )
    # Used instead of employee/restaurant_employee when
    # assignment_type.employee_source == 'NONE', e.g. "IT Department Pool".
    assignee_name = models.CharField(max_length=150, blank=True)
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, related_name='assignments', null=True, blank=True,
        help_text="Where the asset is physically deployed/held (Head Office, a "
                   "Restaurant branch, a Kitchen under either, etc.)."
    )
    # Optional department tag, independent of `location`, so a report can be
    # sliced by department as well as by physical place.
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, related_name='assignments', null=True, blank=True
    )
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='assignments')
    qty = models.PositiveIntegerField(default=1)
    # Snapshot of the item's unit at assignment time - lets the same
    # AssignmentForm be genuinely "unit-wise specific" (Pcs vs Set vs Box)
    # even if the item master's default unit changes later.
    unit = models.CharField(max_length=10, choices=InventoryItem.UNIT_CHOICES, blank=True)
    assigned_date = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ASSIGNED)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-assigned_date']

    def save(self, *args, **kwargs):
        if not self.unit and self.item_id:
            self.unit = self.item.unit
        super().save(*args, **kwargs)

    @property
    def assignee_label(self):
        """Human-readable label for whoever/whatever holds this item."""
        if self.employee_id:
            return str(self.employee)
        if self.restaurant_employee_id:
            return f"{self.restaurant_employee} (Restaurant)"
        return self.assignee_name or "-"

    def __str__(self):
        return f"{self.assignee_label} <- {self.item.item_code} x{self.qty} ({self.status})"


# ---------------------------------------------------------------------------
# Damage tracking - dynamic "who/what is responsible" (Employee, Office /
# Location, Stock / Inventory, Vendor, Other) and dynamic damage reasons.
# A damage record can optionally reference the EmployeeAssignment it happened
# under (damage after assignment) or stand alone (damage found in store stock).
# ---------------------------------------------------------------------------

class DamageResponsibleType(models.Model):
    """Dynamic list of 'who/what caused the damage' categories, e.g.
    Employee, Office/Location, Stock/Inventory, Vendor, Other."""
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Damage Responsible Type"
        verbose_name_plural = "Damage Responsible Types"

    def __str__(self):
        return self.name


class DamageReason(models.Model):
    """Dynamic list of damage causes, e.g. Mishandling, Wear & Tear, Accident."""
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DamageRecord(models.Model):
    SEVERITY_MINOR = 'MINOR'
    SEVERITY_MAJOR = 'MAJOR'
    SEVERITY_TOTAL_LOSS = 'TOTAL_LOSS'
    SEVERITY_CHOICES = [
        (SEVERITY_MINOR, 'Minor (repairable)'),
        (SEVERITY_MAJOR, 'Major (partially usable)'),
        (SEVERITY_TOTAL_LOSS, 'Total Loss'),
    ]

    STATUS_REPORTED = 'REPORTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_WRITTEN_OFF = 'WRITTEN_OFF'
    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reported'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_WRITTEN_OFF, 'Written Off'),
    ]

    damage_no = models.CharField(max_length=30, unique=True, blank=True)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='damage_records')
    # Optional link back to the specific hand-over this damage happened under
    # (i.e. "damage after assign"). Left blank for damage found directly in
    # store stock (i.e. "damage by stock/inventory").
    assignment = models.ForeignKey(
        EmployeeAssignment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='damage_records'
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_records'
    )
    qty = models.PositiveIntegerField(default=1)
    date_reported = models.DateField(default=timezone.now)

    responsible_type = models.ForeignKey(
        DamageResponsibleType, on_delete=models.PROTECT, related_name='damage_records'
    )
    # Filled only when responsible_type points to an employee-based category.
    responsible_employee = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='damages_caused'
    )
    # Free-text for non-employee responsibility (office/branch name, vendor
    # name, "found during stock count", etc.)
    responsible_note = models.CharField(max_length=255, blank=True)

    reason = models.ForeignKey(DamageReason, on_delete=models.PROTECT, related_name='damage_records')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MINOR)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REPORTED)

    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # If True, `qty` is written off from InventoryItem.current_stock via the
    # stock ledger (OUT) at the moment the record is created.
    deduct_from_stock = models.BooleanField(
        default=True,
        help_text="Tick to remove the damaged quantity from current stock immediately."
    )
    action_taken = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    reported_by = models.ForeignKey(
        RDA_EMPLOYEE_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='damage_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.damage_no:
            self.damage_no = _generate_no("DMG")
        super().save(*args, **kwargs)

    @property
    def responsible_label(self):
        if self.responsible_employee_id:
            return str(self.responsible_employee)
        return self.responsible_note or self.responsible_type.name

    def __str__(self):
        return f"{self.damage_no} | {self.item.item_code} x{self.qty} ({self.get_status_display()})"
