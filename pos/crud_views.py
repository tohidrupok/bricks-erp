from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import (
    MenuItem, BillOfQuantities, BOQItem, RawMaterial, Requisition,
    PurchaseOrder, RestaurantCustomer, RestaurantTable, RestaurantOrder
)

def is_admin(user):
    return user.is_staff or user.is_superuser


# ------------------------------------------------------------------
# BOQ CRUD OPERATIONS
# ------------------------------------------------------------------
@login_required
def create_boq(request):
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        raw_material_ids = request.POST.getlist('raw_material_id[]')
        quantities = request.POST.getlist('quantity_required[]')

        if not menu_item_id or not raw_material_ids:
            messages.error(request, "Please select a menu item and at least one raw material.")
            return redirect('stock_boq')

        try:
            with transaction.atomic():
                menu_item = MenuItem.objects.get(id=menu_item_id)
                
                # Check if BOQ already exists for this menu item
                boq, created = BillOfQuantities.objects.get_or_create(
                    menu_item=menu_item,
                    defaults={'created_by': request.user, 'status': 'PENDING'}
                )
                
                # Clear existing items if re-creating/updating via create endpoint
                if not created:
                    boq.ingredients.all().delete()
                    boq.status = 'PENDING'
                    boq.save()

                for mat_id, qty_str in zip(raw_material_ids, quantities):
                    if mat_id and qty_str:
                        raw = RawMaterial.objects.get(id=mat_id)
                        qty = Decimal(str(qty_str))
                        BOQItem.objects.create(
                            boq=boq,
                            raw_material=raw,
                            quantity_required=qty
                        )

            messages.success(request, f"BOQ for '{menu_item.name}' created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating BOQ: {str(e)}")

    return redirect('stock_boq')


@login_required
@user_passes_test(is_admin)
def edit_boq(request, pk):
    boq = get_object_or_404(BillOfQuantities, pk=pk)
    
    if request.method == 'POST':
        raw_material_ids = request.POST.getlist('raw_material_id[]')
        quantities = request.POST.getlist('quantity_required[]')

        try:
            with transaction.atomic():
                boq.ingredients.all().delete()
                for mat_id, qty_str in zip(raw_material_ids, quantities):
                    if mat_id and qty_str:
                        raw = RawMaterial.objects.get(id=mat_id)
                        qty = Decimal(str(qty_str))
                        BOQItem.objects.create(
                            boq=boq,
                            raw_material=raw,
                            quantity_required=qty
                        )
                boq.status = 'PENDING'  # Require re-approval after edits
                boq.save()
            messages.success(request, f"BOQ for '{boq.menu_item.name}' updated successfully.")
            return redirect('stock_boq')
        except Exception as e:
            messages.error(request, f"Error updating BOQ: {str(e)}")

    raw_materials = RawMaterial.objects.all()
    return render(request, 'pos/boq_edit.html', {'boq': boq, 'raw_materials': raw_materials})


@login_required
@user_passes_test(is_admin)
def delete_boq(request, pk):
    boq = get_object_or_404(BillOfQuantities, pk=pk)
    menu_item_name = boq.menu_item.name
    boq.delete()
    messages.success(request, f"BOQ for '{menu_item_name}' deleted.")
    return redirect('stock_boq')


# ------------------------------------------------------------------
# REQUISITION & PURCHASE ORDER DELETIONS
# ------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def delete_requisition(request, pk):
    req = get_object_or_404(Requisition, pk=pk)
    req.delete()
    messages.success(request, f"Requisition #{pk} deleted.")
    return redirect('stock_boq')


@login_required
@user_passes_test(is_admin)
def delete_purchase_order(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    po.delete()
    messages.success(request, f"Purchase Order #{pk} deleted.")
    return redirect('stock_boq')


# ------------------------------------------------------------------
# CUSTOMER & TABLE CRUD OPERATIONS
# ------------------------------------------------------------------
@login_required
def create_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        
        if name and phone:
            RestaurantCustomer.objects.create(name=name, phone=phone, email=email)
            messages.success(request, f"Customer '{name}' added successfully.")
        else:
            messages.error(request, "Name and Phone number are required.")
            
    return redirect(request.META.get('HTTP_REFERER', 'pos_terminal'))


@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(RestaurantCustomer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name', customer.name)
        customer.phone = request.POST.get('phone', customer.phone)
        customer.email = request.POST.get('email', customer.email)
        customer.save()
        messages.success(request, f"Customer '{customer.name}' updated.")
        return redirect('pos_terminal')
    return render(request, 'pos/customer_edit.html', {'customer': customer})


@login_required
@user_passes_test(is_admin)
def delete_customer(request, pk):
    customer = get_object_or_404(RestaurantCustomer, pk=pk)
    name = customer.name
    customer.delete()
    messages.success(request, f"Customer '{name}' removed.")
    return redirect(request.META.get('HTTP_REFERER', 'pos_terminal'))


@login_required
def create_table(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        capacity = request.POST.get('capacity', 4)
        
        if table_number:
            RestaurantTable.objects.get_or_create(
                table_number=table_number,
                defaults={'capacity': capacity}
            )
            messages.success(request, f"Table '{table_number}' created successfully.")
        else:
            messages.error(request, "Table number is required.")
            
    return redirect('pos_terminal')


@login_required
@user_passes_test(is_admin)
def delete_table(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    table_number = table.table_number
    table.delete()
    messages.success(request, f"Table '{table_number}' removed.")
    return redirect('pos_terminal')


# ------------------------------------------------------------------
# ORDER MANAGEMENT
# ------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def delete_order(request, pk):
    order = get_object_or_404(RestaurantOrder, pk=pk)
    order_no = order.order_no
    order.delete()
    messages.success(request, f"Order #{order_no} deleted.")
    return redirect('order_history')