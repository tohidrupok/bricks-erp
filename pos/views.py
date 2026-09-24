import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import (
    WorkPeriod, RestaurantCustomer, RestaurantSupplier, RestaurantTable, RawMaterial,
    MenuItemCategory, MenuItem, BillOfQuantities, BOQItem, Requisition, RequisitionItem,
    PurchaseOrder, PurchaseOrderItem, RestaurantOrder, RestaurantOrderItem, TakaReturn,
    AccountingTransaction
)

# Admin verification helper
def is_admin(user):
    return user.is_staff or user.is_superuser


# ------------------------------------------------------------------
# 1. POS Terminal Order Execution
# ------------------------------------------------------------------
@login_required
def pos_terminal(request):
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
                return JsonResponse({'status': 'error', 'message': 'Cart is empty!'}, status=400)

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
                    status='COMPLETED',
                    server_name=request.user.username
                )

                subtotal = Decimal('0.00')

                for itm in items:
                    menu_obj = MenuItem.objects.get(id=itm['id'])
                    qty = int(itm['qty'])
                    line_amt = menu_obj.selling_price * qty
                    subtotal += line_amt

                    RestaurantOrderItem.objects.create(
                        order=order, menu_item=menu_obj, qty=qty,
                        price=menu_obj.selling_price, amount=line_amt
                    )

                    # Deduct ingredients based on approved BOQ
                    if hasattr(menu_obj, 'boq') and menu_obj.boq.status == 'APPROVED':
                        for ingredient in menu_obj.boq.ingredients.all():
                            req_qty = ingredient.quantity_required * qty
                            raw = ingredient.raw_material
                            if raw.current_stock < req_qty:
                                raise ValueError(f"Insufficient stock for raw material: {raw.name}")
                            raw.current_stock -= req_qty
                            raw.save()

                order.subtotal = subtotal
                order.net_total = max(Decimal('0.00'), subtotal - discount)
                order.save()

                # Record Accounting Ledger Entry
                AccountingTransaction.objects.create(
                    txn_type='RECEIPT',
                    amount=order.paid_amount,
                    customer=customer,
                    order=order,
                    note=f"POS Payment received for Order #{order.order_no}"
                )

                if table_obj:
                    table_obj.is_occupied = False
                    table_obj.save()

            return JsonResponse({'status': 'success', 'order_no': order.order_no})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    tables = RestaurantTable.objects.all().order_by('id')
    categories = MenuItemCategory.objects.prefetch_related('items').all()
    menu_items = MenuItem.objects.filter(is_active=True)
    customers = RestaurantCustomer.objects.all()

    return render(request, 'pos/terminal.html', {
        'active_period': active_period,
        'tables': tables,
        'categories': categories,
        'menu_items': menu_items,
        'customers': customers,
        'active_tab': 'pos'
    })


# ------------------------------------------------------------------
# 2. Executive Dashboard
# ------------------------------------------------------------------
@login_required
def dashboard(request):
    active_period = WorkPeriod.objects.filter(is_active=True).first()
    orders = RestaurantOrder.objects.filter(work_period=active_period, status='COMPLETED') if active_period else []

    total_sales = sum(o.net_total for o in orders)
    total_orders = len(orders)
    subtotal = sum(o.subtotal for o in orders)
    discount = sum(o.discount for o in orders)

    channel_data = []
    for ch_code, ch_label in RestaurantOrder.CHANNEL_CHOICES:
        ch_orders = [o for o in orders if o.channel == ch_code]
        channel_data.append({
            'name': ch_label,
            'count': len(ch_orders),
            'amount': sum(o.net_total for o in ch_orders)
        })

    payment_data = []
    for pm_code, pm_label in RestaurantOrder.PAYMENT_CHOICES:
        pm_orders = [o for o in orders if o.payment_method == pm_code]
        payment_data.append({
            'method': pm_label,
            'count': len(pm_orders),
            'amount': sum(o.net_total for o in pm_orders)
        })

    return render(request, 'pos/dashboard.html', {
        'active_period': active_period,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'subtotal': subtotal,
        'discount': discount,
        'channel_data': channel_data,
        'payment_data': payment_data,
        'active_tab': 'dashboard'
    })


# ------------------------------------------------------------------
# 3. Stock, BOQ, Purchase Orders & Requisitions
# ------------------------------------------------------------------
@login_required
def stock_boq_view(request):
    active_period = WorkPeriod.objects.filter(is_active=True).first()
    raw_materials = RawMaterial.objects.all()
    boqs = BillOfQuantities.objects.all()
    requisitions = Requisition.objects.all().order_by('-id')
    purchase_orders = PurchaseOrder.objects.all().order_by('-id')
    suppliers = RestaurantSupplier.objects.all()

    return render(request, 'pos/stock_boq.html', {
        'active_period': active_period,
        'raw_materials': raw_materials,
        'boqs': boqs,
        'requisitions': requisitions,
        'purchase_orders': purchase_orders,
        'suppliers': suppliers,
        'active_tab': 'stock'
    })


@login_required
@user_passes_test(is_admin)
def approve_boq(request, boq_id):
    boq = get_object_or_404(BillOfQuantities, id=boq_id)
    boq.status = 'APPROVED'
    boq.approved_by = request.user
    boq.save()
    messages.success(request, f"BOQ for '{boq.menu_item.name}' successfully approved!")
    return redirect('stock_boq')


@login_required
def create_requisition(request):
    if request.method == 'POST':
        material_id = request.POST.get('raw_material_id')
        qty = Decimal(request.POST.get('qty', '0'))
        cost = Decimal(request.POST.get('estimated_cost', '0'))

        with transaction.atomic():
            req = Requisition.objects.create(requested_by=request.user)
            raw = RawMaterial.objects.get(id=material_id)
            RequisitionItem.objects.create(
                requisition=req, raw_material=raw, qty=qty, estimated_cost=cost
            )
        messages.success(request, f"Requisition {req.req_no} submitted!")
    return redirect('stock_boq')


@login_required
@user_passes_test(is_admin)
def approve_requisition(request, req_id):
    req = get_object_or_404(Requisition, id=req_id)
    req.status = 'APPROVED'
    req.approved_by = request.user
    req.save()
    messages.success(request, f"Requisition {req.req_no} marked as Approved.")
    return redirect('stock_boq')


@login_required
def create_purchase_order(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        material_id = request.POST.get('raw_material_id')
        qty = Decimal(request.POST.get('qty', '0'))
        unit_price = Decimal(request.POST.get('unit_price', '0'))
        total_amount = qty * unit_price

        with transaction.atomic():
            supplier = RestaurantSupplier.objects.get(id=supplier_id)
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                total_amount=total_amount,
                paid_amount=total_amount,
                status='PENDING'
            )
            raw = RawMaterial.objects.get(id=material_id)
            PurchaseOrderItem.objects.create(
                purchase_order=po, raw_material=raw, qty=qty,
                unit_price=unit_price, amount=total_amount
            )
        messages.success(request, f"Purchase Order {po.po_no} created and waiting for Admin approval.")
    return redirect('stock_boq')


@login_required
@user_passes_test(is_admin)
def approve_purchase_order(request, po_id):
    po = get_object_or_404(PurchaseOrder, id=po_id)
    if po.status == 'PENDING':
        po.approve_and_receive_stock(admin_user=request.user)

        # Log accounting payment entry for purchase
        AccountingTransaction.objects.create(
            txn_type='PAYMENT',
            amount=po.paid_amount,
            supplier=po.supplier,
            note=f"Payment disbursed for PO #{po.po_no}"
        )
        messages.success(request, f"Purchase Order {po.po_no} Approved! Raw Material stock updated.")
    return redirect('stock_boq')


# ------------------------------------------------------------------
# 4. Work Period Control, Orders, Customers, Refunds
# ------------------------------------------------------------------
@login_required
def order_history(request):
    active_period = WorkPeriod.objects.filter(is_active=True).first()
    orders = RestaurantOrder.objects.all().order_by('-order_date')
    return render(request, 'pos/order_history.html', {
        'orders': orders,
        'active_period': active_period,
        'active_tab': 'orders'
    })


@login_required
def toggle_work_period(request):
    active_period = WorkPeriod.objects.filter(is_active=True).first()
    if active_period:
        active_period.is_active = False
        active_period.end_time = timezone.now()
        active_period.ended_by = request.user
        active_period.save()
        messages.info(request, f"Work Period #{active_period.id} closed.")
    else:
        new_period = WorkPeriod.objects.create(started_by=request.user, is_active=True)
        messages.success(request, f"Work Period #{new_period.id} opened.")
    return redirect(request.META.get('HTTP_REFERER', 'pos_terminal'))


@login_required
def process_taka_return(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        refund_amt = Decimal(request.POST.get('refund_amount', '0'))
        reason = request.POST.get('reason')

        with transaction.atomic():
            order = RestaurantOrder.objects.get(id=order_id)
            order.status = 'REFUNDED'
            order.save()

            TakaReturn.objects.create(
                order=order, refund_amount=refund_amt, reason=reason, processed_by=request.user
            )

            # Log accounting disbursement entry
            AccountingTransaction.objects.create(
                txn_type='PAYMENT',
                amount=refund_amt,
                customer=order.customer,
                order=order,
                note=f"Taka Return refund for Order #{order.order_no}"
            )

        messages.success(request, f"Refund of BDT {refund_amt} recorded for Order #{order.order_no}")
    return redirect('order_history')