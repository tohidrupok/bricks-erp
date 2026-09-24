from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, F, Sum
from django.utils import timezone

from .models import (
    Department, Location, Category, InventoryItem, Requisition,
    EmployeeAssignment, Purchase, AssignmentType, DamageResponsibleType,
    DamageReason, DamageRecord,
)
from .forms import (
    RequisitionForm, InventoryItemForm, AssignmentForm, PurchaseForm, PurchaseApprovalForm,
    AssignmentTypeForm, DamageResponsibleTypeForm, DamageReasonForm, DamageRecordForm,
)
from . import services
from . import reports

# Your existing employee model lives in the hrm app.
# If your app label is different, change this one import line.
from hrm.models import RdaEmployee

# Restaurant-side staff live in a separate app/table.
# If your app label is different, change this one import line.
from restahrm.models import RestaurantEmployee


# ---------------------------------------------------------------------------
# Role checks - swap these for your real permission/group model.
# Simplest option: create Django Groups named 'DeptHead', 'Admin', 'StoreOfficer'
# and add users to them (or make them superusers).
# ---------------------------------------------------------------------------

def is_dept_head(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='DeptHead').exists())


def is_admin_approver(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Admin').exists())


def is_store_officer(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='StoreOfficer').exists())


def is_purchase_officer(user):
    """Purchase Department: approves admin-approved requisitions into purchases."""
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='PurchaseOfficer').exists())


def _current_employee(request):
    """Maps the logged-in Django user to an RdaEmployee row. Adjust the
    lookup (e.g. a OneToOne field) to match how your project links them."""
    return RdaEmployee.objects.filter(rda_email=request.user.email).first()


def _employee_source_map():
    """{'<AssignmentType id>': 'HR' | 'RESTAURANT' | 'NONE'} - drives which
    target field (employee / restaurant_employee / assignee_name) the
    Assign form's JS shows for the selected type."""
    return {
        str(t.pk): (t.employee_source or (AssignmentType.SOURCE_HR if t.requires_employee else AssignmentType.SOURCE_NONE))
        for t in AssignmentType.objects.filter(is_active=True)
    }


def _item_unit_map():
    """{'<InventoryItem id>': 'PCS' | 'SET' | ...} - lets the Assign/Requisition
    form's JS suggest the item's unit automatically (unit-wise specific
    assignment) without an extra AJAX round-trip."""
    return {str(i.pk): i.unit for i in InventoryItem.objects.all()}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    total_requisitions = Requisition.objects.count()
    pending = Requisition.objects.filter(
        status__in=[Requisition.STATUS_PENDING, Requisition.STATUS_DEPT_APPROVED,
                    Requisition.STATUS_ADMIN_APPROVED]
    ).count()
    completed = Requisition.objects.filter(status=Requisition.STATUS_ISSUED).count()
    low_stock_items = InventoryItem.objects.filter(current_stock__lte=F('min_stock')).count()

    category_summary = (InventoryItem.objects.values('category__name')
                         .annotate(items=Count('id'), stock=Sum('current_stock'))
                         .order_by('category__name'))
    location_summary = (InventoryItem.objects.values('location__name')
                         .annotate(items=Count('id'), stock=Sum('current_stock'))
                         .order_by('location__name'))

    pending_purchases = Purchase.objects.filter(status=Purchase.STATUS_ORDERED).count()
    assigned_assets = EmployeeAssignment.objects.filter(status=EmployeeAssignment.STATUS_ASSIGNED).count()

    damage_open = DamageRecord.objects.filter(
        status__in=[DamageRecord.STATUS_REPORTED, DamageRecord.STATUS_UNDER_REVIEW]
    ).count()
    damage_total_cost = DamageRecord.objects.aggregate(total=Sum('estimated_cost'))['total'] or 0

    context = {
        'total_requisitions': total_requisitions,
        'pending': pending,
        'completed': completed,
        'low_stock_items': low_stock_items,
        'pending_purchases': pending_purchases,
        'assigned_assets': assigned_assets,
        'damage_open': damage_open,
        'damage_total_cost': damage_total_cost,
        'category_summary': category_summary,
        'location_summary': location_summary,
        'recent_requisitions': Requisition.objects.select_related('department', 'employee', 'item')[:10],
        'low_stock_list': InventoryItem.objects.filter(
            current_stock__lte=F('min_stock')).select_related('category', 'location'),
    }
    return render(request, 'office_inventory/dashboard.html', context)


# ---------------------------------------------------------------------------
# Inventory items (category-wise + location-wise stock)
# ---------------------------------------------------------------------------

@login_required
def item_list(request):
    items = InventoryItem.objects.select_related('category', 'location')
    category_id = request.GET.get('category')
    location_id = request.GET.get('location')
    q = request.GET.get('q')
    if category_id:
        items = items.filter(category_id=category_id)
    if location_id:
        items = items.filter(location_id=location_id)
    if q:
        items = items.filter(Q(item_code__icontains=q) | Q(name__icontains=q))

    return render(request, 'office_inventory/item_list.html', {
        'items': items,
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
        'selected_category': category_id or '',
        'selected_location': location_id or '',
        'q': q or '',
    })


@login_required
def item_create(request):
    """Item Master - Add Item. Code + Name are required; Category/Location/
    Unit are optional classification; `min_stock` sets the low-stock alert
    threshold, and an optional opening quantity can be typed in right here -
    it's applied through the stock ledger (services.receive_stock) so it's
    fully audited like every other stock movement."""
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            opening_qty = form.cleaned_data.get('opening_stock') or 0
            if opening_qty > 0:
                services.receive_stock(
                    item.id, opening_qty, reference=f"OPENING-{item.item_code}",
                    user=_current_employee(request),
                )
            messages.success(
                request,
                f"Item {item.item_code} created" + (f" with opening stock {opening_qty}." if opening_qty else "."),
            )
            return redirect('office_inventory:item_list')
    else:
        form = InventoryItemForm()
    return render(request, 'office_inventory/item_form.html', {'form': form, 'title': 'Add Item'})


@login_required
def item_update(request, pk):
    """Edit item master data (code/name/category/location/unit/min stock/
    is_asset). Current stock is never edited here - only through Purchase /
    Requisition / Assignment / Damage so the stock ledger stays authoritative."""
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item {item.item_code} updated.")
            return redirect('office_inventory:item_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'office_inventory/item_form.html', {
        'form': form, 'title': f'Edit Item - {item.item_code}', 'item': item,
    })


# # ---------------------------------------------------------------------------
# # Master data list pages
# # ---------------------------------------------------------------------------


# from .forms import DepartmentForm

# @login_required
# def department_list(request):
#     departments = Department.objects.all()
#     return render(request, 'office_inventory/department_list.html', {'departments': departments})


# @login_required
# def department_detail(request, pk):
#     department = get_object_or_404(Department, pk=pk)
#     return render(request, 'office_inventory/department_detail.html', {'department': department})


# @login_required
# def department_create(request):
#     if request.method == 'POST':
#         form = DepartmentForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Department created successfully!")
#             return redirect('office_inventory:department_list')
#     else:
#         form = DepartmentForm()
#     return render(request, 'office_inventory/department_form.html', {'form': form, 'title': 'Add Department'})


# @login_required
# def department_update(request, pk):
#     department = get_object_or_404(Department, pk=pk)
#     if request.method == 'POST':
#         form = DepartmentForm(request.POST, instance=department)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Department updated successfully!")
#             return redirect('office_inventory:department_list')
#     else:
#         form = DepartmentForm(instance=department)
#     return render(request, 'office_inventory/department_form.html', {'form': form, 'title': 'Edit Department', 'department': department})


# @login_required
# def department_delete(request, pk):
#     department = get_object_or_404(Department, pk=pk)
#     if request.method == 'POST':
#         department.delete()
#         messages.success(request, "Department deleted successfully!")
#         return redirect('office_inventory:department_list')
#     return render(request, 'office_inventory/department_confirm_delete.html', {'department': department})




from .forms import DepartmentForm

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'office_inventory/department_list.html', {'departments': departments})


@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'office_inventory/department_detail.html', {'department': department})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from hrm.models import RdaEmployee
from restahrm.models import RestaurantEmployee

@login_required
def load_employees(request):
    dept_type = request.GET.get('dept_type')
    employees = []
    
    if dept_type == 'btp':
        # Filter only active BTP employees
        qs = RdaEmployee.objects.filter(rda_active_status=True)
        employees = [{'id': emp.id, 'name': str(emp)} for emp in qs]
        
    elif dept_type == 'restaurant':
        # Filter active restaurant employees belonging to the specified Galleria projects
        qs = RestaurantEmployee.objects.filter(
            rda_active_status=True,
            project_name__project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        )
        employees = [{'id': emp.id, 'name': str(emp)} for emp in qs]
        
    return JsonResponse({'employees': employees})
    
    


@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect('office_inventory:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'office_inventory/department_form.html', {'form': form, 'title': 'Add Department'})


@login_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully!")
            return redirect('office_inventory:department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'office_inventory/department_form.html', {'form': form, 'title': 'Edit Department', 'department': department})


@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, "Department deleted successfully!")
        return redirect('office_inventory:department_list')
    return render(request, 'office_inventory/department_confirm_delete.html', {'department': department})
    


from django.http import JsonResponse
from hrm.models import RdaEmployee
from restahrm.models import RestaurantEmployee

@login_required
def load_employees(request):
    dept_type = request.GET.get('dept_type')
    employees = []
    
    if dept_type == 'btp':
        employees = [{'id': emp.id, 'name': str(emp)} for emp in RdaEmployee.objects.all()]
    elif dept_type == 'restaurant':
        employees = [{'id': emp.id, 'name': str(emp)} for emp in RestaurantEmployee.objects.all()]
        
    return JsonResponse({'employees': employees})
    

from .forms import LocationForm
@login_required
def location_list(request):
    locations = Location.objects.all()
    return render(request, 'office_inventory/location_list.html', {'locations': locations})


@login_required
def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, 'office_inventory/location_detail.html', {'location': location})


@login_required
def location_create(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location created successfully!")
            return redirect('office_inventory:location_list')
    else:
        form = LocationForm()
    return render(request, 'office_inventory/location_form.html', {'form': form, 'title': 'Add Location'})


@login_required
def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Location updated successfully!")
            return redirect('office_inventory:location_list')
    else:
        form = LocationForm(instance=location)
    return render(request, 'office_inventory/location_form.html', {'form': form, 'title': 'Edit Location', 'location': location})


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        location.delete()
        messages.success(request, "Location deleted successfully!")
        return redirect('office_inventory:location_list')
    return render(request, 'office_inventory/location_confirm_delete.html', {'location': location})
    
    

# ---------------------------------------------------------------------------
# Requisition workflow
# ---------------------------------------------------------------------------

@login_required
def requisition_list(request):
    requisitions = Requisition.objects.select_related('department', 'employee', 'item')
    status = request.GET.get('status')
    if status:
        requisitions = requisitions.filter(status=status)
    return render(request, 'office_inventory/requisition_list.html', {
        'requisitions': requisitions,
        'status_choices': Requisition.STATUS_CHOICES,
        'selected_status': status or '',
    })



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Requisition
from .forms import RequisitionForm

# Define which statuses lock the record from ANY edit or delete action
LOCKED_STATUSES = [
    Requisition.STATUS_ADMIN_APPROVED,
    Requisition.STATUS_ISSUED,
    Requisition.STATUS_ADMIN_REJECTED,
    Requisition.STATUS_CANCELLED,
]

@login_required
def requisition_edit(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Lock for everyone (including admin) if admin approved, issued, etc.
    if requisition.status in LOCKED_STATUSES:
        messages.error(
            request, 
            f"Requisition {requisition.req_no} is already {requisition.get_status_display().lower()} and is locked from editing."
        )
        return redirect('office_inventory:requisition_list')

    is_admin_user = (request.session.get('department') == 'admin') or request.user.is_staff or request.user.is_superuser
    auto_employee = None if is_admin_user else getattr(request.user, 'employee', None)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, instance=requisition, is_admin=is_admin_user)
        if form.is_valid():
            req = form.save(commit=False)
            if not is_admin_user and auto_employee:
                req.employee = auto_employee
            req.save()
            messages.success(request, f"Requisition {requisition.req_no} updated successfully.")
            return redirect('office_inventory:requisition_list')
    else:
        form = RequisitionForm(instance=requisition, is_admin=is_admin_user)

    return render(request, 'office_inventory/requisition_form.html', {
        'form': form,
        'title': f"Edit Requisition ({requisition.req_no})",
        'requisition': requisition,
        'auto_employee': auto_employee,
        'is_edit': True,
    })


@login_required
def requisition_delete(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Lock for everyone (including admin) if admin approved, issued, etc.
    if requisition.status in LOCKED_STATUSES:
        messages.error(
            request, 
            f"Requisition {requisition.req_no} is already {requisition.get_status_display().lower()} and cannot be deleted."
        )
        return redirect('office_inventory:requisition_list')

    if request.method == 'POST':
        req_no = requisition.req_no
        requisition.delete()
        messages.success(request, f"Requisition {req_no} deleted successfully.")
        return redirect('office_inventory:requisition_list')

    return render(request, 'office_inventory/requisition_confirm_delete.html', {
        'requisition': requisition
    })
    
    
@login_required
def requisition_create(request):
    """New Requisition. Non-admin users never see an Employee dropdown - the
    requisition is always raised in their own name. Only Admin (or
    superuser) users get the Employee field, so they can raise a requisition
    on behalf of someone else."""
    admin_user = is_admin_approver(request.user)
    current_employee = _current_employee(request)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, is_admin=admin_user)
        if form.is_valid():
            req = form.save(commit=False)
            if not admin_user:
                if not current_employee:
                    messages.error(
                        request,
                        "Your login isn't linked to an employee record yet - contact Admin."
                    )
                    return render(request, 'office_inventory/requisition_form.html',
                                  {'form': form, 'title': 'New Requisition'})
                req.employee = current_employee
            req.save()
            messages.success(request, f"Requisition {req.req_no} submitted - pending department approval.")
            return redirect('office_inventory:requisition_detail', pk=req.pk)
    else:
        initial = {} if admin_user else {}
        form = RequisitionForm(is_admin=admin_user, initial=initial)
    return render(request, 'office_inventory/requisition_form.html', {
        'form': form, 'title': 'New Requisition',
        'auto_employee': None if admin_user else current_employee,
        'item_unit_map': _item_unit_map(),
    })


@login_required
def requisition_detail(request, pk):
    req = get_object_or_404(
        Requisition.objects.select_related(
            'department', 'employee', 'item', 'dept_approver', 'admin_approver', 'store_officer'),
        pk=pk,
    )
    return render(request, 'office_inventory/requisition_detail.html', {
        'req': req,
        'can_dept_approve': is_dept_head(request.user) and req.status == Requisition.STATUS_PENDING,
        'can_admin_approve': is_admin_approver(request.user) and req.status == Requisition.STATUS_DEPT_APPROVED,
        'can_issue': is_store_officer(request.user) and req.status == Requisition.STATUS_ADMIN_APPROVED,
    })


@login_required
@user_passes_test(is_dept_head)
def requisition_dept_approve(request, pk):
    approver = _current_employee(request)
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'approve':
                services.dept_approve_requisition(pk, approver, request.POST.get('approved_qty') or None)
                messages.success(request, "Approved by department. Sent for admin approval.")
            else:
                services.dept_reject_requisition(pk, approver, request.POST.get('remarks', ''))
                messages.warning(request, "Requisition rejected by department.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:requisition_detail', pk=pk)


@login_required
@user_passes_test(is_admin_approver)
def requisition_admin_approve(request, pk):
    approver = _current_employee(request)
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'approve':
                services.admin_approve_requisition(pk, approver, request.POST.get('approved_qty') or None)
                messages.success(request, "Approved by admin. Ready for store issue.")
            else:
                services.admin_reject_requisition(pk, approver, request.POST.get('remarks', ''))
                messages.warning(request, "Requisition rejected by admin.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:requisition_detail', pk=pk)


@login_required
@user_passes_test(is_store_officer)
def requisition_issue(request, pk):
    officer = _current_employee(request)
    if request.method == 'POST':
        try:
            services.issue_requisition(pk, officer, request.POST.get('issued_qty') or None)
            messages.success(request, "Item issued. Stock deducted and dashboard updated.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:requisition_detail', pk=pk)


# ---------------------------------------------------------------------------
# Purchase Department panel - admin-approved requisitions waiting to be
# turned into a purchase. The purchase officer can ONLY approve; item and
# quantity are locked to what department + admin already approved.
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_purchase_officer)
def purchase_queue(request):
    ready = Requisition.objects.select_related('department', 'employee', 'item').filter(
        status=Requisition.STATUS_ADMIN_APPROVED
    )
    return render(request, 'office_inventory/purchase_queue.html', {
        'requisitions': ready,
        'form': PurchaseApprovalForm(),
    })


@login_required
@user_passes_test(is_purchase_officer)
def purchase_approve_requisition(request, pk):
    officer = _current_employee(request)
    if request.method == 'POST':
        form = PurchaseApprovalForm(request.POST)
        if form.is_valid():
            try:
                services.process_requisition_purchase(
                    pk, officer,
                    supplier=form.cleaned_data.get('supplier') or '',
                    unit_price=form.cleaned_data.get('unit_price') or 0,
                )
                messages.success(request, "Purchase approved. Store stock updated.")
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors and try again.")
    return redirect('office_inventory:purchase_queue')


# ---------------------------------------------------------------------------
# Purchase - order stock, receive it (stock auto-adds)
# ---------------------------------------------------------------------------

@login_required
def purchase_list(request):
    purchases = Purchase.objects.select_related('item', 'received_by')
    status = request.GET.get('status')
    if status:
        purchases = purchases.filter(status=status)
    return render(request, 'office_inventory/purchase_list.html', {
        'purchases': purchases,
        'status_choices': Purchase.STATUS_CHOICES,
        'selected_status': status or '',
        'can_receive': is_store_officer(request.user),
    })


@login_required
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            messages.success(request, f"Purchase {purchase.purchase_no} recorded as Ordered.")
            return redirect('office_inventory:purchase_list')
    else:
        form = PurchaseForm()
    return render(request, 'office_inventory/purchase_form.html', {'form': form, 'title': 'New Purchase'})


@login_required
@user_passes_test(is_store_officer)
def purchase_receive(request, pk):
    if request.method == 'POST':
        try:
            services.receive_purchase(pk, received_by=_current_employee(request))
            messages.success(request, "Purchase received. Stock added and dashboard updated.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:purchase_list')


@login_required
@user_passes_test(is_store_officer)
def purchase_cancel(request, pk):
    if request.method == 'POST':
        try:
            services.cancel_purchase(pk)
            messages.warning(request, "Purchase cancelled.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:purchase_list')


# ---------------------------------------------------------------------------
# Employee-wise direct asset assignment
# ---------------------------------------------------------------------------

@login_required
def assignment_list(request):
    assignments = EmployeeAssignment.objects.select_related(
        'employee', 'item', 'assignment_type', 'location'
    )
    type_id = request.GET.get('type')
    location_id = request.GET.get('location')
    status = request.GET.get('status')
    if type_id:
        assignments = assignments.filter(assignment_type_id=type_id)
    if location_id:
        assignments = assignments.filter(location_id=location_id)
    if status:
        assignments = assignments.filter(status=status)
    return render(request, 'office_inventory/assignment_list.html', {
        'assignments': assignments,
        'assignment_types': AssignmentType.objects.filter(is_active=True),
        'locations': Location.objects.all(),
        'status_choices': EmployeeAssignment.STATUS_CHOICES,
        'selected_type': type_id or '',
        'selected_location': location_id or '',
        'selected_status': status or '',
        # The "Mark Returned" action is admin-only from this general list -
        # individual users return their own items from "My Assignments"
        # (employee_asset_profile) instead. See assignment_list.html.
        'is_admin': is_admin_approver(request.user),
    })


@login_required
def assignment_create(request):
    """Assign an item to any dynamic target - an employee, or a non-employee
    target (Restaurant, Department Pool, Warehouse, etc. - configured under
    Assignment Types), optionally tagged with a location."""
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            try:
                services.assign_item_to_employee(
                    item_id=form.cleaned_data['item'].id,
                    qty=form.cleaned_data['qty'],
                    assignment_type=form.cleaned_data['assignment_type'],
                    employee=form.cleaned_data.get('employee'),
                    restaurant_employee=form.cleaned_data.get('restaurant_employee'),
                    assignee_name=form.cleaned_data.get('assignee_name', ''),
                    location_id=form.cleaned_data['location'].id if form.cleaned_data.get('location') else None,
                    department_id=form.cleaned_data['department'].id if form.cleaned_data.get('department') else None,
                    unit=form.cleaned_data.get('unit'),
                    user=_current_employee(request),
                    remarks=form.cleaned_data['remarks'],
                )
                messages.success(request, "Item assigned. Main stock decreased.")
                return redirect('office_inventory:assignment_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = AssignmentForm()
    return render(request, 'office_inventory/assignment_form.html', {
        'form': form, 'title': 'Assign Item',
        # Drives the 3-way JS toggle in assignment_form.html: which of
        # employee / restaurant_employee / assignee_name to show.
        'employee_source_map': _employee_source_map(),
        'item_unit_map': _item_unit_map(),
    })



# @login_required
# def assignment_update(request, pk):
#     assignment = get_object_or_404(EmployeeAssignment, pk=pk)
#     if request.method == 'POST':
#         form = AssignmentForm(request.POST, instance=assignment)
#         if form.is_valid():
#             form.save()
#             messages.success(request, f"Assignment for {assignment.employee} successfully updated.")
#             return redirect('office_inventory:assignment_list')
#     else:
#         form = AssignmentForm(instance=assignment)
#     return render(request, 'office_inventory/assignment_form.html', {'form': form, 'title': 'Edit Assignment'})



@login_required
def assignment_update(request, pk):
    """Edit an assignment. Any change to item/qty is reconciled through the
    stock ledger via services.update_assignment() - never by poking a stock
    field directly - so the change stays fully audited."""
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            try:
                services.update_assignment(
                    assignment.pk,
                    item_id=form.cleaned_data['item'].id,
                    qty=form.cleaned_data['qty'],
                    assignment_type=form.cleaned_data['assignment_type'],
                    employee=form.cleaned_data.get('employee'),
                    restaurant_employee=form.cleaned_data.get('restaurant_employee'),
                    assignee_name=form.cleaned_data.get('assignee_name', ''),
                    location_id=form.cleaned_data['location'].id if form.cleaned_data.get('location') else None,
                    department_id=form.cleaned_data['department'].id if form.cleaned_data.get('department') else None,
                    unit=form.cleaned_data.get('unit'),
                    remarks=form.cleaned_data['remarks'],
                    user=_current_employee(request),
                )
                messages.success(request, "Assignment updated and stock adjusted successfully.")
                return redirect('office_inventory:assignment_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'office_inventory/assignment_form.html', {
        'form': form, 'title': 'Edit Assignment', 'assignment': assignment,
        'employee_source_map': _employee_source_map(),
        'item_unit_map': _item_unit_map(),
    })

@login_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)
    if request.method == 'POST':
        assignee_name = assignment.assignee_label
        assignment.delete()
        messages.success(request, f"Assignment record for {assignee_name} was deleted successfully.")
        return redirect('office_inventory:assignment_list')
    return render(request, 'office_inventory/assignment_confirm_delete.html', {'assignment': assignment})
    
    

@login_required
def assignment_return(request, pk):
    if request.method == 'POST':
        try:
            services.return_assignment(pk, user=_current_employee(request))
            messages.success(request, "Item returned. Stock restored.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:assignment_list')
    


# ---------------------------------------------------------------------------
# Employee-wise asset profile - every employee who has (or ever had) an
# assigned item gets a clean profile page listing everything issued to them.
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_admin_approver)
def employee_profile_list(request):
    """Employees who currently have (or previously had) at least one assigned
    item. Admin-only: individual employees use "My Assignments" instead to
    see just their own assigned items (see my_assignments below)."""
    employees = (
        RdaEmployee.objects.filter(assigned_items__isnull=False)
        .distinct()
        .annotate(
            active_count=Count('assigned_items', filter=Q(assigned_items__status=EmployeeAssignment.STATUS_ASSIGNED)),
            total_count=Count('assigned_items'),
        )
    )
    return render(request, 'office_inventory/employee_profile_list.html', {'employees': employees})


@login_required
def employee_asset_profile(request, pk):
    """Employee-wise asset profile: employee details + full assignment
    history. Only Admin can open *another* employee's profile; anyone can
    open their own (e.g. via the "My Assignments" link), and only there -
    or if they're Admin - do they see the Mark Returned button."""
    employee = get_object_or_404(RdaEmployee, pk=pk)
    current_employee = _current_employee(request)
    is_admin = is_admin_approver(request.user)
    is_self = bool(current_employee and current_employee.pk == employee.pk)

    if not (is_admin or is_self):
        messages.error(request, "You can only view your own assignment profile.")
        return redirect('office_inventory:dashboard')

    assignments = EmployeeAssignment.objects.select_related('item', 'item__category').filter(
        employee=employee
    )
    active_assignments = assignments.filter(status=EmployeeAssignment.STATUS_ASSIGNED)
    returned_assignments = assignments.filter(status=EmployeeAssignment.STATUS_RETURNED)
    return render(request, 'office_inventory/employee_profile.html', {
        'employee': employee,
        'assignments': assignments,
        'active_assignments': active_assignments,
        'returned_assignments': returned_assignments,
        'active_count': active_assignments.count(),
        'total_count': assignments.count(),
        # Only Admin, or the employee viewing their own profile, can return
        # an item from here - see employee_profile.html.
        'can_return': is_admin or is_self,
    })


@login_required
def my_assignments(request):
    """Self-service shortcut: takes the logged-in user straight to their own
    assignment profile (with the Return button), without needing Admin
    access to the full employee_profile_list."""
    current_employee = _current_employee(request)
    if not current_employee:
        messages.error(request, "Your login isn't linked to an employee record yet - contact Admin.")
        return redirect('office_inventory:dashboard')
    return redirect('office_inventory:employee_asset_profile', pk=current_employee.pk)


from .models import Category
from .forms import CategoryForm

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'office_inventory/category_list.html', {'categories': categories})


@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, 'office_inventory/category_detail.html', {'category': category})


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return redirect('office_inventory:category_list')
    else:
        form = CategoryForm()
    return render(request, 'office_inventory/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect('office_inventory:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'office_inventory/category_form.html', {'form': form, 'title': 'Edit Category', 'category': category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect('office_inventory:category_list')
    return render(request, 'office_inventory/category_confirm_delete.html', {'category': category})


# ---------------------------------------------------------------------------
# Assignment Types - dynamic list of "who/what an item can be assigned to"
# (Employee, Restaurant, Department Pool, Warehouse, ...). Admin-managed.
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_admin_approver)
def assignment_type_list(request):
    types = AssignmentType.objects.annotate(assignment_count=Count('assignments'))
    return render(request, 'office_inventory/assignment_type_list.html', {'types': types})


@login_required
@user_passes_test(is_admin_approver)
def assignment_type_create(request):
    if request.method == 'POST':
        form = AssignmentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment type created successfully!")
            return redirect('office_inventory:assignment_type_list')
    else:
        form = AssignmentTypeForm()
    return render(request, 'office_inventory/assignment_type_form.html', {'form': form, 'title': 'Add Assignment Type'})


@login_required
@user_passes_test(is_admin_approver)
def assignment_type_update(request, pk):
    a_type = get_object_or_404(AssignmentType, pk=pk)
    if request.method == 'POST':
        form = AssignmentTypeForm(request.POST, instance=a_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment type updated successfully!")
            return redirect('office_inventory:assignment_type_list')
    else:
        form = AssignmentTypeForm(instance=a_type)
    return render(request, 'office_inventory/assignment_type_form.html', {
        'form': form, 'title': 'Edit Assignment Type', 'a_type': a_type,
    })


@login_required
@user_passes_test(is_admin_approver)
def assignment_type_delete(request, pk):
    a_type = get_object_or_404(AssignmentType, pk=pk)
    if request.method == 'POST':
        if a_type.assignments.exists():
            messages.error(request, "Can't delete a type that already has assignments. Mark it inactive instead.")
        else:
            a_type.delete()
            messages.success(request, "Assignment type deleted successfully!")
        return redirect('office_inventory:assignment_type_list')
    return render(request, 'office_inventory/assignment_type_confirm_delete.html', {'a_type': a_type})


@login_required
def assignment_type_profile(request, pk):
    """Type-wise profile: every assignment under one AssignmentType (e.g. all
    'Restaurant' hand-overs), split into currently-held vs returned, same
    shape as the per-employee profile page."""
    a_type = get_object_or_404(AssignmentType, pk=pk)
    assignments = EmployeeAssignment.objects.select_related('item', 'item__category', 'employee', 'location').filter(
        assignment_type=a_type
    )
    active_assignments = assignments.filter(status=EmployeeAssignment.STATUS_ASSIGNED)
    returned_assignments = assignments.filter(status=EmployeeAssignment.STATUS_RETURNED)
    return render(request, 'office_inventory/assignment_type_profile.html', {
        'a_type': a_type,
        'assignments': assignments,
        'active_assignments': active_assignments,
        'returned_assignments': returned_assignments,
        'active_count': active_assignments.count(),
        'total_count': assignments.count(),
    })


# ---------------------------------------------------------------------------
# Damage tracking - dynamic responsible-type / reason master data, plus the
# damage records themselves (create, list/filter, status transitions).
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_admin_approver)
def damage_type_list(request):
    types = DamageResponsibleType.objects.annotate(record_count=Count('damage_records'))
    return render(request, 'office_inventory/damage_type_list.html', {'types': types})


@login_required
@user_passes_test(is_admin_approver)
def damage_type_create(request):
    if request.method == 'POST':
        form = DamageResponsibleTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Damage responsible type created successfully!")
            return redirect('office_inventory:damage_type_list')
    else:
        form = DamageResponsibleTypeForm()
    return render(request, 'office_inventory/damage_type_form.html', {'form': form, 'title': 'Add Responsible Type'})


@login_required
@user_passes_test(is_admin_approver)
def damage_type_update(request, pk):
    d_type = get_object_or_404(DamageResponsibleType, pk=pk)
    if request.method == 'POST':
        form = DamageResponsibleTypeForm(request.POST, instance=d_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Damage responsible type updated successfully!")
            return redirect('office_inventory:damage_type_list')
    else:
        form = DamageResponsibleTypeForm(instance=d_type)
    return render(request, 'office_inventory/damage_type_form.html', {
        'form': form, 'title': 'Edit Responsible Type', 'd_type': d_type,
    })


@login_required
@user_passes_test(is_admin_approver)
def damage_type_delete(request, pk):
    d_type = get_object_or_404(DamageResponsibleType, pk=pk)
    if request.method == 'POST':
        if d_type.damage_records.exists():
            messages.error(request, "Can't delete a type already used on damage records. Mark it inactive instead.")
        else:
            d_type.delete()
            messages.success(request, "Damage responsible type deleted successfully!")
        return redirect('office_inventory:damage_type_list')
    return render(request, 'office_inventory/damage_type_confirm_delete.html', {'d_type': d_type})


@login_required
@user_passes_test(is_admin_approver)
def damage_reason_list(request):
    reasons = DamageReason.objects.annotate(record_count=Count('damage_records'))
    return render(request, 'office_inventory/damage_reason_list.html', {'reasons': reasons})


@login_required
@user_passes_test(is_admin_approver)
def damage_reason_create(request):
    if request.method == 'POST':
        form = DamageReasonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Damage reason created successfully!")
            return redirect('office_inventory:damage_reason_list')
    else:
        form = DamageReasonForm()
    return render(request, 'office_inventory/damage_reason_form.html', {'form': form, 'title': 'Add Damage Reason'})


@login_required
@user_passes_test(is_admin_approver)
def damage_reason_update(request, pk):
    reason = get_object_or_404(DamageReason, pk=pk)
    if request.method == 'POST':
        form = DamageReasonForm(request.POST, instance=reason)
        if form.is_valid():
            form.save()
            messages.success(request, "Damage reason updated successfully!")
            return redirect('office_inventory:damage_reason_list')
    else:
        form = DamageReasonForm(instance=reason)
    return render(request, 'office_inventory/damage_reason_form.html', {
        'form': form, 'title': 'Edit Damage Reason', 'reason': reason,
    })


@login_required
@user_passes_test(is_admin_approver)
def damage_reason_delete(request, pk):
    reason = get_object_or_404(DamageReason, pk=pk)
    if request.method == 'POST':
        if reason.damage_records.exists():
            messages.error(request, "Can't delete a reason already used on damage records. Mark it inactive instead.")
        else:
            reason.delete()
            messages.success(request, "Damage reason deleted successfully!")
        return redirect('office_inventory:damage_reason_list')
    return render(request, 'office_inventory/damage_reason_confirm_delete.html', {'reason': reason})


@login_required
def damage_list(request):
    records = DamageRecord.objects.select_related(
        'item', 'responsible_type', 'responsible_employee', 'reason', 'assignment', 'location'
    )
    item_id = request.GET.get('item')
    status = request.GET.get('status')
    responsible_type_id = request.GET.get('responsible_type')
    severity = request.GET.get('severity')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if item_id:
        records = records.filter(item_id=item_id)
    if status:
        records = records.filter(status=status)
    if responsible_type_id:
        records = records.filter(responsible_type_id=responsible_type_id)
    if severity:
        records = records.filter(severity=severity)
    if date_from:
        records = records.filter(date_reported__gte=date_from)
    if date_to:
        records = records.filter(date_reported__lte=date_to)

    total_estimated_cost = records.aggregate(total=Sum('estimated_cost'))['total'] or 0

    return render(request, 'office_inventory/damage_list.html', {
        'records': records,
        'items': InventoryItem.objects.all(),
        'status_choices': DamageRecord.STATUS_CHOICES,
        'severity_choices': DamageRecord.SEVERITY_CHOICES,
        'responsible_types': DamageResponsibleType.objects.filter(is_active=True),
        'selected_item': item_id or '',
        'selected_status': status or '',
        'selected_responsible_type': responsible_type_id or '',
        'selected_severity': severity or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'total_estimated_cost': total_estimated_cost,
    })


@login_required
def damage_create(request):
    if request.method == 'POST':
        form = DamageRecordForm(request.POST)
        if form.is_valid():
            try:
                services.report_damage(
                    item_id=form.cleaned_data['item'].id,
                    qty=form.cleaned_data['qty'],
                    responsible_type=form.cleaned_data['responsible_type'],
                    reason=form.cleaned_data['reason'],
                    reported_by=_current_employee(request),
                    assignment_id=form.cleaned_data['assignment'].id if form.cleaned_data.get('assignment') else None,
                    location_id=form.cleaned_data['location'].id if form.cleaned_data.get('location') else None,
                    responsible_employee=form.cleaned_data.get('responsible_employee'),
                    responsible_note=form.cleaned_data.get('responsible_note', ''),
                    severity=form.cleaned_data['severity'],
                    estimated_cost=form.cleaned_data.get('estimated_cost') or 0,
                    deduct_from_stock=form.cleaned_data['deduct_from_stock'],
                    date_reported=form.cleaned_data.get('date_reported'),
                    action_taken=form.cleaned_data.get('action_taken', ''),
                    remarks=form.cleaned_data.get('remarks', ''),
                )
                messages.success(request, "Damage reported successfully.")
                return redirect('office_inventory:damage_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = DamageRecordForm()
    responsible_employee_map = {
        str(t.pk): (t.name.strip().lower() == 'employee') for t in DamageResponsibleType.objects.filter(is_active=True)
    }
    return render(request, 'office_inventory/damage_form.html', {
        'form': form, 'title': 'Report Damage',
        'responsible_employee_map': responsible_employee_map,
    })


@login_required
@user_passes_test(is_admin_approver)
def damage_set_status(request, pk):
    if request.method == 'POST':
        try:
            services.set_damage_status(
                pk, request.POST.get('status'), action_taken=request.POST.get('action_taken')
            )
            messages.success(request, "Damage record status updated.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('office_inventory:damage_list')


@login_required
@user_passes_test(is_admin_approver)
def damage_delete(request, pk):
    record = get_object_or_404(DamageRecord, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, "Damage record deleted successfully!")
        return redirect('office_inventory:damage_list')
    return render(request, 'office_inventory/damage_confirm_delete.html', {'record': record})


# ---------------------------------------------------------------------------
# Reports - Excel / PDF export for every major section. Each export view
# reuses the exact same filters as its list page so "what you filtered is
# what you export".
# ---------------------------------------------------------------------------

@login_required
def reports_home(request):
    return render(request, 'office_inventory/reports.html', {
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
        'assignment_types': AssignmentType.objects.filter(is_active=True),
        'status_choices': Requisition.STATUS_CHOICES,
        'purchase_status_choices': Purchase.STATUS_CHOICES,
        'damage_status_choices': DamageRecord.STATUS_CHOICES,
    })


def _filtered_items(request):
    items = InventoryItem.objects.select_related('category', 'location')
    if request.GET.get('category'):
        items = items.filter(category_id=request.GET['category'])
    if request.GET.get('location'):
        items = items.filter(location_id=request.GET['location'])
    if request.GET.get('low_stock_only') == '1':
        items = items.filter(current_stock__lte=F('min_stock'))
    return items


@login_required
def items_report_excel(request):
    headers, rows = reports.items_report_rows(_filtered_items(request))
    return reports.build_excel("Inventory Stock Report", headers, rows, filename="inventory_stock_report.xlsx")


@login_required
def items_report_pdf(request):
    headers, rows = reports.items_report_rows(_filtered_items(request))
    return reports.build_pdf("Inventory Stock Report", headers, rows, filename="inventory_stock_report.pdf")


def _filtered_requisitions(request):
    qs = Requisition.objects.select_related('department', 'employee', 'item')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    if request.GET.get('date_from'):
        qs = qs.filter(date__gte=request.GET['date_from'])
    if request.GET.get('date_to'):
        qs = qs.filter(date__lte=request.GET['date_to'])
    return qs


@login_required
def requisitions_report_excel(request):
    headers, rows = reports.requisitions_report_rows(_filtered_requisitions(request))
    return reports.build_excel("Requisitions Report", headers, rows, filename="requisitions_report.xlsx")


@login_required
def requisitions_report_pdf(request):
    headers, rows = reports.requisitions_report_rows(_filtered_requisitions(request))
    return reports.build_pdf("Requisitions Report", headers, rows, filename="requisitions_report.pdf")


def _filtered_purchases(request):
    qs = Purchase.objects.select_related('item', 'received_by')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    if request.GET.get('date_from'):
        qs = qs.filter(date__gte=request.GET['date_from'])
    if request.GET.get('date_to'):
        qs = qs.filter(date__lte=request.GET['date_to'])
    return qs


@login_required
def purchases_report_excel(request):
    headers, rows = reports.purchases_report_rows(_filtered_purchases(request))
    return reports.build_excel("Purchases Report", headers, rows, filename="purchases_report.xlsx")


@login_required
def purchases_report_pdf(request):
    headers, rows = reports.purchases_report_rows(_filtered_purchases(request))
    return reports.build_pdf("Purchases Report", headers, rows, filename="purchases_report.pdf")


def _filtered_assignments(request):
    qs = EmployeeAssignment.objects.select_related('employee', 'item', 'assignment_type', 'location')
    if request.GET.get('type'):
        qs = qs.filter(assignment_type_id=request.GET['type'])
    if request.GET.get('location'):
        qs = qs.filter(location_id=request.GET['location'])
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    return qs


@login_required
def assignments_report_excel(request):
    headers, rows = reports.assignments_report_rows(_filtered_assignments(request))
    return reports.build_excel("Assignments Report", headers, rows, filename="assignments_report.xlsx")


@login_required
def assignments_report_pdf(request):
    headers, rows = reports.assignments_report_rows(_filtered_assignments(request))
    return reports.build_pdf("Assignments Report", headers, rows, filename="assignments_report.pdf")


def _filtered_damage(request):
    qs = DamageRecord.objects.select_related('item', 'responsible_type', 'responsible_employee', 'reason')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    if request.GET.get('responsible_type'):
        qs = qs.filter(responsible_type_id=request.GET['responsible_type'])
    if request.GET.get('date_from'):
        qs = qs.filter(date_reported__gte=request.GET['date_from'])
    if request.GET.get('date_to'):
        qs = qs.filter(date_reported__lte=request.GET['date_to'])
    return qs


@login_required
def damage_report_excel(request):
    headers, rows = reports.damage_report_rows(_filtered_damage(request))
    return reports.build_excel("Damage Report", headers, rows, filename="damage_report.xlsx")


@login_required
def damage_report_pdf(request):
    headers, rows = reports.damage_report_rows(_filtered_damage(request))
    return reports.build_pdf("Damage Report", headers, rows, filename="damage_report.pdf")
