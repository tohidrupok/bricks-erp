from django.contrib import admin
from .models import (
    Department, Location, Category, InventoryItem,
    Requisition, StockLedger, EmployeeAssignment, Purchase,
    AssignmentType, DamageResponsibleType, DamageReason, DamageRecord,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_id', 'name', 'manager')
    search_fields = ('dept_id', 'name')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'location_type', 'parent')
    list_filter = ('location_type',)
    search_fields = ('code', 'name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'name', 'category', 'unit',
                     'min_stock', 'current_stock', 'status', 'is_asset')
    list_filter = ('category', 'is_asset')
    search_fields = ('item_code', 'name')


@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = ('req_no', 'date', 'department', 'employee', 'item', 'location', 'unit',
                     'requested_qty', 'approved_qty', 'issued_qty', 'status')
    list_filter = ('status', 'department', 'location')
    search_fields = ('req_no', 'employee__rda_emp_name')
    readonly_fields = ('req_no', 'created_at')


@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ('date', 'reference', 'type', 'item', 'location', 'department', 'unit',
                     'qty_in', 'qty_out', 'balance', 'user')
    list_filter = ('type', 'item__category', 'location', 'department')
    search_fields = ('reference', 'item__item_code')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchase_no', 'date', 'item', 'requisition', 'supplier', 'qty',
                     'unit_price', 'total_amount', 'status', 'received_by')
    list_filter = ('status', 'item__category')
    search_fields = ('purchase_no', 'supplier', 'item__item_code', 'requisition__req_no')
    readonly_fields = ('purchase_no', 'created_at')


@admin.register(AssignmentType)
class AssignmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_source', 'requires_employee', 'is_active')
    list_filter = ('employee_source', 'requires_employee', 'is_active')
    search_fields = ('name',)


@admin.register(EmployeeAssignment)
class EmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('assignment_type', 'assignee_label', 'location', 'department', 'item', 'unit', 'qty',
                     'assigned_date', 'return_date', 'status')
    list_filter = ('status', 'assignment_type', 'location', 'department')
    search_fields = ('employee__rda_emp_name', 'restaurant_employee__rda_emp_name', 'assignee_name', 'item__item_code')

    @admin.display(description='Assigned To')
    def assignee_label(self, obj):
        return obj.assignee_label


@admin.register(DamageResponsibleType)
class DamageResponsibleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(DamageReason)
class DamageReasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(DamageRecord)
class DamageRecordAdmin(admin.ModelAdmin):
    list_display = ('damage_no', 'date_reported', 'item', 'qty', 'responsible_type',
                     'responsible_label', 'reason', 'severity', 'status', 'estimated_cost')
    list_filter = ('status', 'severity', 'responsible_type', 'reason')
    search_fields = ('damage_no', 'item__item_code', 'responsible_note')
    readonly_fields = ('damage_no', 'created_at', 'updated_at')

    @admin.display(description='Responsible')
    def responsible_label(self, obj):
        return obj.responsible_label
