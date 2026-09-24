import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    MenuItem, MenuItemCategory, RawMaterial, BillOfQuantities, BOQItem,
    RestaurantOrder, RestaurantOrderItem, RestaurantCustomer, RestaurantTable,
    RestaurantSupplier, PurchaseOrder, PurchaseOrderItem,
    AccountingTransaction, OrderReturn, WorkPeriod
)


@login_required
def pos_terminal(request):
    categories = MenuItemCategory.objects.prefetch_related('items').all()
    menu_items = MenuItem.objects.filter(is_active=True)
    customers = RestaurantCustomer.objects.all()
    tables = RestaurantTable.objects.all()
    active_period = WorkPeriod.objects.filter(is_active=True).first()

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            channel = payload.get('channel', 'DINE_IN')
            table_id = payload.get('table_id')
            customer_id = payload.get('customer_id')
            items = payload.get('items', [])
            discount = Decimal(str(payload.get('discount', 0)))
            paid_amount = Decimal(str(payload.get('paid_amount', 0)))
            payment_method = payload.get('payment_method', 'CASH')

            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items selected'}, status=400)

            with transaction.atomic():
                customer = RestaurantCustomer.objects.get(id=customer_id) if customer_id else None
                table_obj = RestaurantTable.objects.get(id=table_id) if table_id else None

                order = RestaurantOrder.objects.create(
                    work_period=active_period,
                    table=table_obj,
                    customer=customer,
                    channel=channel,
                    payment_method=payment_method,
                    discount=discount,
                    paid_amount=paid_amount,
                    status='COMPLETED'
                )

                subtotal = Decimal('0.00')

                for itm in items:
                    menu_obj = MenuItem.objects.get(id=itm['id'])
                    qty = int(itm['qty'])
                    line_amt = menu_obj.selling_price * qty
                    subtotal += line_amt

                    RestaurantOrderItem.objects.create(
                        order=order,
                        menu_item=menu_obj,
                        qty=qty,
                        price=menu_obj.selling_price,
                        amount=line_amt
                    )

                    # Deduct Ingredients based on BOQ
                    if hasattr(menu_obj, 'boq') and menu_obj.boq.status == 'APPROVED':
                        for ingredient in menu_obj.boq.ingredients.all():
                            req_qty = ingredient.quantity_required * qty
                            raw = ingredient.raw_material
                            if raw.current_stock < req_qty:
                                raise ValueError(f"Insufficient stock for raw material: {raw.name}")
                            raw.current_stock -= req_qty
                            raw.save()

                net_total = max(Decimal('0.00'), subtotal - discount)
                order.subtotal = subtotal
                order.net_total = net_total
                order.save()

                # Free up table if assigned
                if table_obj:
                    table_obj.is_occupied = False
                    table_obj.save()

                # Accounting Record
                if paid_amount > 0:
                    AccountingTransaction.objects.create(
                        txn_type='RECEIPT',
                        amount=paid_amount,
                        customer=customer,
                        order=order,
                        note=f"Payment for POS Order {order.order_no} via {channel} ({payment_method})"
                    )

            return JsonResponse({'status': 'success', 'order_no': order.order_no})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return render(request, 'pos/terminal.html', {
        'categories': categories,
        'menu_items': menu_items,
        'customers': customers,
        'tables': tables,
        'active_period': active_period
    })


@login_required
def toggle_work_period(request):
    active_period = WorkPeriod.objects.filter(is_active=True).first()
    if active_period:
        active_period.is_active = False
        active_period.end_time = timezone.now()
        active_period.ended_by = request.user
        active_period.save()
        messages.info(request, f"Work Period #{active_period.id} ended.")
    else:
        new_period = WorkPeriod.objects.create(started_by=request.user, is_active=True)
        messages.success(request, f"Work Period #{new_period.id} started successfully.")
    return redirect('pos_terminal')


@login_required
def approve_boq(request, boq_id):
    boq = get_object_or_404(BillOfQuantities, id=boq_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            boq.status = 'APPROVED'
            boq.approved_by = request.user
            messages.success(request, f"BOQ for {boq.menu_item.name} approved successfully.")
        elif action == 'reject':
            boq.status = 'REJECTED'
            messages.warning(request, f"BOQ for {boq.menu_item.name} rejected.")
        boq.save()
    return redirect('pos_terminal')