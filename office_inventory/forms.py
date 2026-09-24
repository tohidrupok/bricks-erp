from django import forms
from django.core.exceptions import ValidationError
from .models import Requisition, InventoryItem, EmployeeAssignment, Purchase, AssignmentType

# Restaurant-side staff live in a separate app/table. Change this import
# (and RESTAURANT_EMPLOYEE_MODEL in models.py) if your app label for
# RestaurantEmployee is not 'restahrm'.
from restahrm.models import RestaurantEmployee


def _bootstrapify(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.setdefault('class', 'form-check-input')
        else:
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class RequisitionForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = ['department', 'employee', 'item', 'unit','location', 'requested_qty', 'remarks']
        widgets = {'remarks': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, is_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_admin:
            self.fields.pop('employee', None)
        self.fields['location'].required = False
        self.fields['location'].empty_label = "-- Not set --"
        _bootstrapify(self)


class InventoryItemForm(forms.ModelForm):
    """Item Master form.

    Item Code and Item Name are required. Category/Location/Unit are
    optional classification fields. `min_stock` sets the low-stock
    threshold, and `opening_stock` (a plain, non-model field) lets you type
    the starting quantity right when the item is created - it is never
    written to `current_stock` directly; the view runs it through
    `services.receive_stock()` so it lands in the stock ledger like every
    other stock movement (full audit trail, no silent stock edits).
    """
    opening_stock = forms.IntegerField(
        required=False, min_value=0, initial=0,
        label="Opening / Current Qty",
        help_text="Starting stock quantity for this item (optional, defaults to 0).",
        widget=forms.NumberInput(attrs={'placeholder': '0'}),
    )

    class Meta:
        model = InventoryItem
        fields = ['item_code', 'name', 'category', 'location', 'unit', 'min_stock','current_stock','is_asset']
        widgets = {
            'min_stock': forms.NumberInput(attrs={'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = "-- Uncategorized --"
        self.fields['location'].required = False
        self.fields['location'].empty_label = "-- Not set --"
        self.fields['min_stock'].required = False
        # When editing an existing item, show its current stock as read-only
        # info instead of an editable "opening stock" field - stock changes
        # only ever go through Purchase / Requisition / Assignment / Damage.
        if self.instance and self.instance.pk:
            self.fields.pop('opening_stock', None)
        _bootstrapify(self)


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['item', 'supplier', 'qty', 'unit_price', 'date', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class PurchaseApprovalForm(forms.Form):
    """Used by the Purchase Department panel when approving a requisition.

    Deliberately has NO item/qty field - those are locked to whatever the
    department + admin already approved. The purchase officer can only add
    the supplier name and unit price for accounting purposes, then approve.
    """
    supplier = forms.CharField(max_length=150, required=False,
                                widget=forms.TextInput(attrs={'placeholder': 'Supplier (optional)'}))
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0,
                                     widget=forms.NumberInput(attrs={'placeholder': 'Unit Price (optional)', 'step': '0.01'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class AssignmentForm(forms.ModelForm):
    """Assign an item to any dynamic target, driven by the selected
    AssignmentType's `employee_source`:
      - HR         -> `employee` (hrm.RdaEmployee, e.g. Head Office staff)
      - RESTAURANT -> `restaurant_employee` (RestaurantEmployee, e.g. Kitchen/
                       restaurant staff), scoped by `location`'s project
      - NONE       -> free-text `assignee_name` (e.g. "Head Office Pool")

    `location` also carries the place this asset is deployed to (Head
    Office / a specific Restaurant branch / a Kitchen under either), and
    `department` optionally tags it by department. `unit` is a snapshot of
    the item's unit so the same form is explicitly unit-wise (Pcs, Set,
    Box, ...). Which target field is required is enforced here in clean()
    AND client-side in assignment_form.html so the right field shows/hides
    as the user picks a type.
    """
    class Meta:
        model = EmployeeAssignment
        fields = ['assignment_type', 'employee', 'restaurant_employee', 'assignee_name',
                   'location', 'department', 'item', 'unit', 'qty', 'remarks']
        widgets = {'remarks': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignment_type'].queryset = AssignmentType.objects.filter(is_active=True)
        self.fields['assignment_type'].required = True
        self.fields['employee'].required = False
        self.fields['restaurant_employee'].queryset = RestaurantEmployee.objects.filter(
            rda_active_status=True
        )
        self.fields['restaurant_employee'].required = False
        self.fields['assignee_name'].required = False
        self.fields['location'].required = False
        self.fields['location'].empty_label = "-- Not set --"
        self.fields['department'].required = False
        self.fields['department'].empty_label = "-- Not set --"
        # Unit is a snapshot, auto-filled from the item's unit on the item_
        # change JS below - leave it optional so the ModelForm doesn't block
        # submission before JS has had a chance to fill it in.
        self.fields['unit'].required = False
        _bootstrapify(self)

    def clean(self):
        cleaned = super().clean()
        a_type = cleaned.get('assignment_type')
        employee = cleaned.get('employee')
        restaurant_employee = cleaned.get('restaurant_employee')
        assignee_name = (cleaned.get('assignee_name') or '').strip()
        item = cleaned.get('item')

        source = None
        if a_type:
            # employee_source is the precise control; fall back to the
            # legacy requires_employee boolean for any older AssignmentType
            # rows that haven't been migrated to a specific source yet.
            source = a_type.employee_source or (
                AssignmentType.SOURCE_HR if a_type.requires_employee else AssignmentType.SOURCE_NONE
            )

        if source == AssignmentType.SOURCE_HR:
            if not employee:
                self.add_error('employee', "Select an HR/office employee for this assign type.")
            cleaned['restaurant_employee'] = None
            cleaned['assignee_name'] = ''
        elif source == AssignmentType.SOURCE_RESTAURANT:
            if not restaurant_employee:
                self.add_error('restaurant_employee', "Select a restaurant employee for this assign type.")
            cleaned['employee'] = None
            cleaned['assignee_name'] = ''
        elif a_type:
            if not assignee_name:
                self.add_error('assignee_name', f"Enter a name for this {a_type.name} assignment.")
            cleaned['employee'] = None
            cleaned['restaurant_employee'] = None

        if not cleaned.get('unit') and item:
            cleaned['unit'] = item.unit
        return cleaned


class AssignmentTypeForm(forms.ModelForm):
    class Meta:
        model = AssignmentType
        fields = ['name', 'employee_source', 'requires_employee', 'description', 'is_active']
        widgets = {'description': forms.TextInput(attrs={'placeholder': 'Optional note'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # requires_employee is kept only for backward compatibility with any
        # code/reports still reading it - keep it in sync with the new,
        # more precise employee_source field so both always agree.
        self.fields['requires_employee'].help_text = (
            "Kept in sync automatically with 'Employee source' below - you "
            "normally don't need to touch this directly."
        )
        _bootstrapify(self)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.requires_employee = instance.employee_source in (
            AssignmentType.SOURCE_HR, AssignmentType.SOURCE_RESTAURANT
        )
        if commit:
            instance.save()
        return instance
        


# from .models import Department
# class DepartmentForm(forms.ModelForm):
#     class Meta:
#         model = Department
#         fields = ['dept_id', 'name', 'manager']
#         widgets = {
#             'dept_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. DPT-001'}),
#             'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Department Name'}),
#             'manager': forms.Select(attrs={'class': 'form-input'}),
#         }


from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import Department
from hrm.models import RdaEmployee
from restahrm.models import RestaurantEmployee

# Safe import to handle different app names without crashing
try:
    from project.models import ProjectFirstLevelName
except ImportError:
    try:
        from projects.models import ProjectFirstLevelName
    except ImportError:
        ProjectFirstLevelName = None


class DepartmentForm(forms.ModelForm):
    DEPT_TYPES = (
        ('', 'Select Department Type'),
        ('btp', 'BTP Office'),
        ('restaurant', 'Restaurant'),
    )
    
    dept_type = forms.ChoiceField(
        choices=DEPT_TYPES,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_dept_type'})
    )
    
    if ProjectFirstLevelName:
        restaurant_project = forms.ModelChoiceField(
            queryset=ProjectFirstLevelName.objects.filter(
                project_first_name__in=[
                    "The Galleria Restauent Cafe",
                    "The Galleria Live Kitchen"
                ]
            ),
            required=False,
            widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_restaurant_project'})
        )
    else:
        restaurant_project = forms.ChoiceField(
            choices=[('', 'Project App Not Found')],
            required=False,
            widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_restaurant_project'})
        )

    manager_select = forms.ChoiceField(
        choices=[('', 'Select Department Type First')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_manager'})
    )

    class Meta:
        model = Department
        fields = ['dept_id', 'name', 'dept_type', 'restaurant_project', 'manager_select']
        widgets = {
            'dept_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. DPT-001', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Department Name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Determine current department type from POST data or existing instance
        dept_type = None
        if self.data and 'dept_type' in self.data:
            dept_type = self.data.get('dept_type')
        elif self.instance and self.instance.pk:
            dept_type = self.instance.dept_type
            self.fields['dept_type'].initial = dept_type
            if self.instance.content_type and self.instance.object_id:
                self.fields['manager_select'].initial = self.instance.object_id

        # Populate active employee choices dynamically based on department type
        if dept_type == 'btp':
            self.fields['manager_select'].choices = [('', 'Select Manager')] + [
                (str(emp.id), str(emp)) for emp in RdaEmployee.objects.filter(rda_active_status=True)
            ]
        elif dept_type == 'restaurant':
            self.fields['manager_select'].choices = [('', 'Select Manager')] + [
                (str(emp.id), str(emp)) for emp in RestaurantEmployee.objects.filter(
                    rda_active_status=True,
                    project_name__project_first_name__in=[
                        "The Galleria Restauent Cafe",
                        "The Galleria Live Kitchen"
                    ]
                )
            ]

    def save(self, commit=True):
        department = super().save(commit=False)
        department.dept_type = self.cleaned_data.get('dept_type')
        manager_id = self.cleaned_data.get('manager_select')

        if department.dept_type == 'btp' and manager_id:
            department.content_type = ContentType.objects.get_for_model(RdaEmployee)
            department.object_id = manager_id
        elif department.dept_type == 'restaurant' and manager_id:
            department.content_type = ContentType.objects.get_for_model(RestaurantEmployee)
            department.object_id = manager_id
        else:
            department.content_type = None
            department.object_id = None

        if commit:
            department.save()
        return department
        
        

from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['code', 'name', 'location_type', 'parent', 'address']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. LOC-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Head Office Store'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Physical Address'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "-- Top level (no parent) --"
        # e.g. set parent to "Head Office" or a Restaurant branch, then
        # location_type = Kitchen, to model "Kitchen under Head Office" /
        # "Kitchen under Restaurant".
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Location.objects.exclude(pk=self.instance.pk)
        

from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. IT Asset, Stationery'}),
        }


# ---------------------------------------------------------------------------
# Damage tracking - dynamic responsible-type / reason master data, plus the
# damage record form itself.
# ---------------------------------------------------------------------------

from .models import DamageResponsibleType, DamageReason, DamageRecord


class DamageResponsibleTypeForm(forms.ModelForm):
    class Meta:
        model = DamageResponsibleType
        fields = ['name', 'description', 'is_active']
        widgets = {'description': forms.TextInput(attrs={'placeholder': 'Optional note'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class DamageReasonForm(forms.ModelForm):
    class Meta:
        model = DamageReason
        fields = ['name', 'description', 'is_active']
        widgets = {'description': forms.TextInput(attrs={'placeholder': 'Optional note'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class DamageRecordForm(forms.ModelForm):
    """Report a damage. `responsible_type` drives whether `responsible_employee`
    (dynamic type flagged as employee-based, e.g. 'Employee') or
    `responsible_note` (Office, Stock/Inventory, Vendor, Other, ...) is used -
    same pattern as AssignmentForm, enforced here and in the template's JS.
    """
    class Meta:
        model = DamageRecord
        fields = [
            'item', 'assignment', 'location', 'qty', 'date_reported',
            'responsible_type', 'responsible_employee', 'responsible_note',
            'reason', 'severity', 'estimated_cost', 'deduct_from_stock',
            'action_taken', 'remarks',
        ]
        widgets = {
            'date_reported': forms.DateInput(attrs={'type': 'date'}),
            'action_taken': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignment'].required = False
        self.fields['assignment'].empty_label = "-- Not linked to an assignment (store stock) --"
        self.fields['location'].required = False
        self.fields['location'].empty_label = "-- Not set --"
        self.fields['responsible_employee'].required = False
        self.fields['responsible_note'].required = False
        self.fields['reason'].queryset = DamageReason.objects.filter(is_active=True)
        self.fields['responsible_type'].queryset = DamageResponsibleType.objects.filter(is_active=True)
        _bootstrapify(self)

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get('qty')
        item = cleaned.get('item')
        deduct = cleaned.get('deduct_from_stock')
        if qty and item and deduct and qty > item.current_stock:
            self.add_error(
                'qty',
                f"Cannot write off {qty} - only {item.current_stock} currently in stock for {item.item_code}."
            )
        r_type = cleaned.get('responsible_type')
        r_employee = cleaned.get('responsible_employee')
        r_note = (cleaned.get('responsible_note') or '').strip()
        if r_type and r_employee is None and not r_note and r_type.name.strip().lower() != 'employee':
            # Non-employee responsible types should have some identifying note.
            self.add_error('responsible_note', f"Add a short note identifying the {r_type.name}.")
        return cleaned
