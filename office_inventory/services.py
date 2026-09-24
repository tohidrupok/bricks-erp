"""
Business logic for every stock-affecting operation.

All functions run inside select_for_update() transactions so concurrent
requisitions/issues can never double-deduct the same item - the same
locking pattern used in the BM ERP RestaurantKitchenLedger module.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    InventoryItem, StockLedger, Requisition, EmployeeAssignment, Purchase,
    DamageRecord, AssignmentType,
)


def _default_employee_assignment_type():
    """Auto-created assignments (from an issued requisition or a purchase
    that fulfils one) are always employee-based - fetch or create the
    'Employee' AssignmentType so these rows stay consistent with manually
    created ones."""
    obj, _ = AssignmentType.objects.get_or_create(
        name='Employee', defaults={'requires_employee': True, 'description': 'Assigned directly to an employee.'}
    )
    return obj


def _write_ledger(item, movement_type, qty, reference, user=None,
                   location_id=None, department_id=None, unit=None):
    """Applies the stock change to `item` and writes one ledger row.

    `location_id` / `department_id` make the ledger entry traceable to a
    specific place (Head Office / a Restaurant branch / a Kitchen under
    either) and department, on top of the existing item/user tracking.
    `unit` snapshots the item's unit at the time of the movement.
    """
    if movement_type == StockLedger.TYPE_IN:
        item.current_stock = item.current_stock + qty
        qty_in, qty_out = qty, 0
    else:
        if item.current_stock < qty:
            raise ValidationError(
                f"Insufficient stock for {item.item_code}. "
                f"Available: {item.current_stock}, requested: {qty}"
            )
        item.current_stock = item.current_stock - qty
        qty_in, qty_out = 0, qty

    item.save(update_fields=['current_stock'])

    StockLedger.objects.create(
        date=timezone.now(),
        reference=reference,
        type=movement_type,
        item=item,
        qty_in=qty_in,
        qty_out=qty_out,
        balance=item.current_stock,
        user=user,
        location_id=location_id,
        department_id=department_id,
        unit=unit or item.unit,
    )
    return item.current_stock


@transaction.atomic
def receive_stock(item_id, qty, reference, user=None, location_id=None):
    """Stock IN - opening stock / manual adjustment entry."""
    item = InventoryItem.objects.select_for_update().get(pk=item_id)
    return _write_ledger(item, StockLedger.TYPE_IN, qty, reference, user, location_id=location_id)


# ---------------------------------------------------------------------------
# Purchase - order stock, then receive it into the location (stock auto adds)
# ---------------------------------------------------------------------------

@transaction.atomic
def receive_purchase(purchase_id, received_by):
    """Marks a Purchase as received and adds its qty to the item's stock."""
    purchase = Purchase.objects.select_for_update().get(pk=purchase_id)
    if purchase.status != Purchase.STATUS_ORDERED:
        raise ValidationError("Only an 'Ordered' purchase can be received.")
    item = InventoryItem.objects.select_for_update().get(pk=purchase.item_id)
    _write_ledger(item, StockLedger.TYPE_IN, purchase.qty, reference=purchase.purchase_no, user=received_by)
    purchase.status = Purchase.STATUS_RECEIVED
    purchase.received_by = received_by
    purchase.received_at = timezone.now()
    purchase.save()
    return purchase


@transaction.atomic
def cancel_purchase(purchase_id):
    purchase = Purchase.objects.select_for_update().get(pk=purchase_id)
    if purchase.status != Purchase.STATUS_ORDERED:
        raise ValidationError("Only an 'Ordered' purchase can be cancelled.")
    purchase.status = Purchase.STATUS_CANCELLED
    purchase.save()
    return purchase


# ---------------------------------------------------------------------------
# Purchase Department: turn an ADMIN-APPROVED requisition into a purchase.
# The purchase officer cannot change the item or quantity - both are locked
# to whatever department + admin already approved. Approving here creates
# the Purchase record, marks it Received immediately, adds the qty to store
# stock, marks the requisition Issued, and (for returnable assets) creates
# the employee's asset assignment - all in one atomic step.
# ---------------------------------------------------------------------------

@transaction.atomic
def process_requisition_purchase(requisition_id, purchase_officer, supplier='', unit_price=0):
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    if req.status != Requisition.STATUS_ADMIN_APPROVED:
        raise ValidationError("Only admin-approved requisitions are ready for purchase.")

    qty = req.approved_qty or req.requested_qty
    item = InventoryItem.objects.select_for_update().get(pk=req.item_id)

    purchase = Purchase.objects.create(
        requisition=req,
        item=item,
        supplier=supplier or '',
        qty=qty,
        unit_price=unit_price or 0,
        status=Purchase.STATUS_ORDERED,
    )

    # Store / inventory update - stock in against this purchase.
    _write_ledger(
        item, StockLedger.TYPE_IN, qty, reference=purchase.purchase_no, user=purchase_officer,
        location_id=req.location_id, department_id=req.department_id, unit=req.unit,
    )

    purchase.status = Purchase.STATUS_RECEIVED
    purchase.received_by = purchase_officer
    purchase.received_at = timezone.now()
    purchase.save()

    req.status = Requisition.STATUS_ISSUED
    req.issued_qty = qty
    req.store_officer = purchase_officer
    req.issued_at = timezone.now()
    req.save()

    # Returnable assets (furniture, laptops, etc.) automatically create an
    # employee-wise assignment record with a proper asset profile.
    if item.is_asset:
        EmployeeAssignment.objects.create(
            assignment_type=_default_employee_assignment_type(),
            employee=req.employee, item=item, qty=qty, unit=req.unit,
            location_id=req.location_id, department_id=req.department_id,
            assigned_date=timezone.now().date(),
            remarks=f"Auto-assigned via purchase {purchase.purchase_no} for requisition {req.req_no}",
        )
    return purchase


# ---------------------------------------------------------------------------
# Requisition workflow: Employee -> Dept Approval -> Admin Approval -> Issue
# ---------------------------------------------------------------------------

@transaction.atomic
def dept_approve_requisition(requisition_id, approver, approved_qty=None):
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    if req.status != Requisition.STATUS_PENDING:
        raise ValidationError("Only pending requisitions can be department-approved.")
    req.approved_qty = int(approved_qty) if approved_qty else req.requested_qty
    req.status = Requisition.STATUS_DEPT_APPROVED
    req.dept_approver = approver
    req.dept_approved_at = timezone.now()
    req.save()
    return req


@transaction.atomic
def dept_reject_requisition(requisition_id, approver, remarks=''):
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    req.status = Requisition.STATUS_DEPT_REJECTED
    req.dept_approver = approver
    req.dept_approved_at = timezone.now()
    req.remarks = remarks
    req.save()
    return req


@transaction.atomic
def admin_approve_requisition(requisition_id, approver, approved_qty=None):
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    if req.status != Requisition.STATUS_DEPT_APPROVED:
        raise ValidationError("Only department-approved requisitions can be admin-approved.")
    if approved_qty:
        req.approved_qty = int(approved_qty)
    req.status = Requisition.STATUS_ADMIN_APPROVED
    req.admin_approver = approver
    req.admin_approved_at = timezone.now()
    req.save()
    return req


@transaction.atomic
def admin_reject_requisition(requisition_id, approver, remarks=''):
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    req.status = Requisition.STATUS_ADMIN_REJECTED
    req.admin_approver = approver
    req.admin_approved_at = timezone.now()
    req.remarks = remarks
    req.save()
    return req


@transaction.atomic
def issue_requisition(requisition_id, store_officer, issued_qty=None):
    """Store Issue step -> Stock Auto Deduct -> Dashboard Update."""
    req = Requisition.objects.select_for_update().get(pk=requisition_id)
    if req.status != Requisition.STATUS_ADMIN_APPROVED:
        raise ValidationError("Only admin-approved requisitions can be issued.")

    qty = int(issued_qty) if issued_qty else (req.approved_qty or req.requested_qty)
    item = InventoryItem.objects.select_for_update().get(pk=req.item_id)

    _write_ledger(
        item, StockLedger.TYPE_OUT, qty, reference=req.req_no, user=store_officer,
        location_id=req.location_id, department_id=req.department_id, unit=req.unit,
    )

    req.issued_qty = qty
    req.status = Requisition.STATUS_ISSUED
    req.store_officer = store_officer
    req.issued_at = timezone.now()
    req.save()

    # Returnable assets (furniture, laptops, etc.) automatically create an
    # employee-wise assignment record so they can later be returned.
    if item.is_asset:
        EmployeeAssignment.objects.create(
            assignment_type=_default_employee_assignment_type(),
            employee=req.employee, item=item, qty=qty, unit=req.unit,
            location_id=req.location_id, department_id=req.department_id,
            assigned_date=timezone.now().date(),
            remarks=f"Auto-created from requisition {req.req_no}",
        )
    return req


# ---------------------------------------------------------------------------
# Direct employee-wise assignment (no requisition needed)
# ---------------------------------------------------------------------------

@transaction.atomic
def assign_item_to_employee(item_id, qty, assignment_type, user=None, remarks='',
                             employee=None, restaurant_employee=None, assignee_name='',
                             location_id=None, department_id=None, unit=None):
    """Main stock decreases immediately when an item is assigned out.

    `assignment_type.employee_source` decides which target field is used:
      - HR         -> pass `employee` (hrm.RdaEmployee)
      - RESTAURANT -> pass `restaurant_employee` (RestaurantEmployee)
      - NONE       -> pass `assignee_name` (e.g. a department pool name)
    `location_id` / `department_id` record where the asset is physically
    deployed (Head Office / a Restaurant branch / a Kitchen under either,
    and which department). `unit` is a snapshot of the item's unit, so the
    same assign flow stays unit-wise specific (Pcs, Set, Box, ...).
    """
    item = InventoryItem.objects.select_for_update().get(pk=item_id)
    source = assignment_type.employee_source or (
        AssignmentType.SOURCE_HR if assignment_type.requires_employee else AssignmentType.SOURCE_NONE
    )
    if source == AssignmentType.SOURCE_HR:
        target = str(employee) if employee else assignment_type.name
    elif source == AssignmentType.SOURCE_RESTAURANT:
        target = str(restaurant_employee) if restaurant_employee else assignment_type.name
    else:
        target = assignee_name or assignment_type.name

    _write_ledger(
        item, StockLedger.TYPE_OUT, qty, reference=f"ASSIGN-{target}", user=user,
        location_id=location_id, department_id=department_id, unit=unit,
    )
    return EmployeeAssignment.objects.create(
        assignment_type=assignment_type,
        employee=employee if source == AssignmentType.SOURCE_HR else None,
        restaurant_employee=restaurant_employee if source == AssignmentType.SOURCE_RESTAURANT else None,
        assignee_name=assignee_name if source == AssignmentType.SOURCE_NONE else '',
        location_id=location_id,
        department_id=department_id,
        item=item, qty=qty, unit=unit or item.unit,
        assigned_date=timezone.now().date(), remarks=remarks,
    )


@transaction.atomic
def update_assignment(assignment_id, *, item_id, qty, assignment_type, employee=None,
                       restaurant_employee=None, assignee_name='', location_id=None,
                       department_id=None, unit=None, remarks='', status=None, user=None):
    """Edit an existing assignment. Reconciles `current_stock` through the
    proper ledger (_write_ledger) instead of poking the field directly, so
    every adjustment stays fully audited - whether the item was swapped, the
    quantity changed, or both.
    """
    assignment = EmployeeAssignment.objects.select_for_update().get(pk=assignment_id)
    original_item_id = assignment.item_id
    original_qty = assignment.qty
    new_qty = int(qty)

    if original_item_id == item_id:
        item = InventoryItem.objects.select_for_update().get(pk=item_id)
        diff = new_qty - original_qty
        if diff > 0:
            _write_ledger(item, StockLedger.TYPE_OUT, diff, reference=f"ASSIGN-EDIT-{assignment.pk}",
                          user=user, location_id=location_id, department_id=department_id, unit=unit)
        elif diff < 0:
            _write_ledger(item, StockLedger.TYPE_IN, -diff, reference=f"ASSIGN-EDIT-{assignment.pk}",
                          user=user, location_id=location_id, department_id=department_id, unit=unit)
    else:
        old_item = InventoryItem.objects.select_for_update().get(pk=original_item_id)
        _write_ledger(old_item, StockLedger.TYPE_IN, original_qty, reference=f"ASSIGN-EDIT-{assignment.pk}",
                      user=user, location_id=location_id, department_id=department_id)
        new_item = InventoryItem.objects.select_for_update().get(pk=item_id)
        _write_ledger(new_item, StockLedger.TYPE_OUT, new_qty, reference=f"ASSIGN-EDIT-{assignment.pk}",
                      user=user, location_id=location_id, department_id=department_id, unit=unit)
        item = new_item

    if assignment_type is not None:
        source = assignment_type.employee_source or (
            AssignmentType.SOURCE_HR if assignment_type.requires_employee else AssignmentType.SOURCE_NONE
        )
    else:
        # No type given - matches the previous behavior of defaulting to an
        # employee-based target.
        source = AssignmentType.SOURCE_HR

    assignment.item = item
    assignment.qty = new_qty
    assignment.unit = unit or item.unit
    assignment.assignment_type = assignment_type
    assignment.employee = employee if source == AssignmentType.SOURCE_HR else None
    assignment.restaurant_employee = restaurant_employee if source == AssignmentType.SOURCE_RESTAURANT else None
    assignment.assignee_name = assignee_name if source == AssignmentType.SOURCE_NONE else ''
    assignment.location_id = location_id
    assignment.department_id = department_id
    assignment.remarks = remarks
    if status:
        assignment.status = status
        if status == EmployeeAssignment.STATUS_ASSIGNED:
            assignment.return_date = None
        elif status == EmployeeAssignment.STATUS_RETURNED and not assignment.return_date:
            assignment.return_date = timezone.now().date()
    assignment.save()
    return assignment


@transaction.atomic
def return_assignment(assignment_id, user=None):
    """Employee returns an asset - stock is added back to main stock."""
    assignment = EmployeeAssignment.objects.select_for_update().get(pk=assignment_id)
    if assignment.status == EmployeeAssignment.STATUS_RETURNED:
        raise ValidationError("This item has already been returned.")
    item = InventoryItem.objects.select_for_update().get(pk=assignment.item_id)
    _write_ledger(item, StockLedger.TYPE_IN, assignment.qty,
                  reference=f"RETURN-{assignment.pk}", user=user,
                  location_id=assignment.location_id, department_id=assignment.department_id,
                  unit=assignment.unit)
    assignment.status = EmployeeAssignment.STATUS_RETURNED
    assignment.return_date = timezone.now().date()
    assignment.save()
    return assignment


# ---------------------------------------------------------------------------
# Damage tracking
# ---------------------------------------------------------------------------

@transaction.atomic
def report_damage(*, item_id, qty, responsible_type, reason, reported_by=None,
                   assignment_id=None, location_id=None, responsible_employee=None,
                   responsible_note='', severity=DamageRecord.SEVERITY_MINOR,
                   estimated_cost=0, deduct_from_stock=True, date_reported=None,
                   action_taken='', remarks=''):
    """Creates a DamageRecord. If `deduct_from_stock` is True, the damaged
    qty is immediately written off the item's current stock through the
    normal stock ledger (OUT), so dashboards / low-stock alerts stay
    accurate - exactly like an issue or a purchase, just with a DMG-xxxxx
    reference instead of a REQ/PUR one.
    """
    item = InventoryItem.objects.select_for_update().get(pk=item_id)
    qty = int(qty)
    if qty < 1:
        raise ValidationError("Damaged quantity must be at least 1.")
    if deduct_from_stock and item.current_stock < qty:
        raise ValidationError(
            f"Cannot write off {qty} - only {item.current_stock} currently in stock for {item.item_code}."
        )

    record = DamageRecord.objects.create(
        item=item,
        assignment_id=assignment_id,
        location_id=location_id,
        qty=qty,
        date_reported=date_reported or timezone.now().date(),
        responsible_type=responsible_type,
        responsible_employee=responsible_employee,
        responsible_note=responsible_note,
        reason=reason,
        severity=severity,
        estimated_cost=estimated_cost or 0,
        deduct_from_stock=deduct_from_stock,
        action_taken=action_taken,
        remarks=remarks,
        reported_by=reported_by,
    )

    if deduct_from_stock:
        _write_ledger(item, StockLedger.TYPE_OUT, qty, reference=record.damage_no, user=reported_by)

    return record


@transaction.atomic
def set_damage_status(damage_id, status, action_taken=None):
    """Move a damage record through Reported -> Under Review -> Resolved /
    Written Off. Does not touch stock - stock was already adjusted (if at
    all) at report time."""
    valid_statuses = dict(DamageRecord.STATUS_CHOICES)
    if status not in valid_statuses:
        raise ValidationError("Invalid damage status.")
    record = DamageRecord.objects.select_for_update().get(pk=damage_id)
    record.status = status
    if action_taken is not None:
        record.action_taken = action_taken
    record.save()
    return record
