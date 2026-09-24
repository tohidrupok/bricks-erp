from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse
from .models import RestaurantCategory,RestaurantExpenseCategory,RestRequisition,RestaurantItem,RestaurantCustomer,RestaurantItemAmount,RestaurantSaleItem,RestInventories,RestInventoryUse,RestaurantSale,RestHeadofAcct,RestaurantAccount,RestaurantSupplier,RestExpense,RestPurchaseCost,RestaurantJewelSupplier,RestExpenseRequisition
from .forms import RestaurantCategoryForm,RestaurantExpenseCategoryForm,RestaurantItemForm,RestRequisitionForm,RestaurantCustomerForm,RestaurantItemAmountForm,RestaurantSaleForm,RestHeadofAcctForm,RestaurantAccountForm,RestaurantSupplierForm,RestExpenseForm,RestPurchaseCostForm,RestExpenseRequisitionForm,RestaurantJewelSupplierForm
import json
from hrm.models import Employee
from restahrm.models import RestaurantEmployee,RestaurantAttendance
from restaccounting.models import CashRestType,RestHeadOfAccount,DebitRestVoucher,RestTransactionHistory,LedgerRestEntry,RestMainCheque,DailyPayment
from restaccounting.forms import DailyPaymentForm
from projects.models import ProjectFirstLevelName
from django.utils.timezone import now
from django.utils import timezone
from datetime import datetime
import calendar
from django.db.models import Sum




# Create your views here.
from calendar import monthcalendar, FRIDAY

@login_required
def rest_attendance_add_holiday(request):
    fridays = []
    selected_month = None

    if request.method == 'POST':
        month_input = request.POST.get('month')  # YYYY-MM
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")

        year = selected_month_dt.year
        month = selected_month_dt.month

        # 🔹 Get all Fridays of selected month
        for week in monthcalendar(year, month):
            if week[FRIDAY] != 0:
                fridays.append(datetime(year, month, week[FRIDAY]).date())

        # 🔹 Active employees (excluding two projects)
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True
        )

        for emp in employees:
            for friday in fridays:
                qs = RestaurantAttendance.objects.filter(
                    employee=emp,
                    date=friday
                ).order_by('id')

                if qs.exists():
                    main = qs.first()

                    # 🧹 Remove duplicate rows
                    if qs.count() > 1:
                        qs.exclude(id=main.id).delete()

                    # ❌ Do NOT touch Present
                    if main.att_status == 'Present':
                        continue

                    # 🔁 Update existing (non-present) row
                    main.att_status = 'Off Day'
                    main.check_in = None
                    main.check_out = None
                    main.save()

                else:
                    # ➕ Insert new Off Day
                    RestaurantAttendance.objects.create(
                        employee=emp,
                        date=friday,
                        att_status='Off Day',
                        check_in=None,
                        check_out=None
                    )

        return redirect('restaurant_attendance_list')

    # 🔹 GET → Preview Fridays
    if request.GET.get('month'):
        month_input = request.GET.get('month')
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")
        selected_month = selected_month_dt.strftime('%B %Y')

        for week in monthcalendar(selected_month_dt.year, selected_month_dt.month):
            if week[FRIDAY] != 0:
                fridays.append(datetime(
                    selected_month_dt.year,
                    selected_month_dt.month,
                    week[FRIDAY]
                ).date())

    return render(request, 'restaurant/attendance/add_holiday.html', {
        'fridays': fridays,
        'selected_month': selected_month
    })



   
## requisition category--
@login_required
def restaurant_category(request):
    restaurants_category = RestaurantCategory.objects.all()
    return render(request, 'restaurant/restaurant_category.html', {'restaurants_categorys': restaurants_category})
    
    
@login_required
def add_restaurant_category(request):
    if request.method == 'POST':
        form = RestaurantCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_requisition_category')  
    else:
        form = RestaurantCategoryForm()
    return render(request, 'restaurant/add_restaurant_category.html', {'form': form})
    
    
    
@login_required
def restaurant_category_edit(request, pk):
    requis_category = get_object_or_404(RestaurantCategory, pk=pk)    
    if request.method == 'POST':
        form = RestaurantCategoryForm(request.POST, instance=requis_category)
        if form.is_valid():
            form.save()
            return redirect('restaurant_requisition_category')  
    else:
        form = RestaurantCategoryForm(instance=requis_category)
    
    return render(request, 'restaurant/restaurant_category_edit.html', {
        'form': form
    })
    
    

@login_required
def restaurant_category_delete(request, pk):
    restu_category = get_object_or_404(RestaurantCategory, pk=pk)
    if request.method == 'POST':
        restu_category.delete()
        return redirect('restaurant_requisition_category')
    return render(request, 'restaurant/restaurant_category_delete.html', {
        'restu_categorys': restu_category  
    })
    
    
    
@login_required
def restaurant_item_name(request):
    restItem = RestaurantItem.objects.all()
    return render(request, 'restaurant/restaurant_item_name.html', {'restItems': restItem})
    
    
    
@login_required
def add_restaurant_item_name(request):
    restaurant_category = RestaurantCategory.objects.all()

    if request.method == 'POST':
        form = RestaurantItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_item_name')
    else:
        form = RestaurantItemForm()
    context = {
        'form': form,
        'restaurant_categorys': restaurant_category,
    }

    return render(request, 'restaurant/add_restaurant_item_name.html', context)
    
    
    
@login_required
def edit_restaurant_item(request, pk):
    head_restaurant = get_object_or_404(RestaurantItem, pk=pk)   
    
    if request.method == 'POST':
        form = RestaurantItemForm(request.POST, instance=head_restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_item_name')  
    else:
        form = RestaurantItemForm(instance=head_restaurant)
        restaurant_category = RestaurantCategory.objects.all()
    
    return render(request, 'restaurant/edit_restaurant_item.html', {
        'form': form,
        'head_restaurants': head_restaurant,
        'restaurant_category' : restaurant_category
    })


@login_required
def delete_restaurant_item(request, pk):
    head_restaurant = get_object_or_404(RestaurantItem, pk=pk)
    if request.method == 'POST':
        head_restaurant.delete()
        return redirect('restaurant_item_name')
    return render(request, 'restaurant/delete_restaurant_item.html', {
        'head_restaurant': head_restaurant  
    })



    
@login_required
def restaurant_customer_name(request):
    restCustomer = RestaurantCustomer.objects.all()
    return render(request, 'restaurant/restaurant_customer_name.html', {'restCustomers': restCustomer})
    
    
    
@login_required
def add_restaurant_customer(request):
    if request.method == 'POST':
        form = RestaurantCustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_customer_name')
    else:
        form = RestaurantCustomerForm()

    return render(request, 'restaurant/add_restaurant_customer.html', {'form': form})
    
    
    
@login_required
def edit_restaurant_customer(request, pk):
    head_restaurant = get_object_or_404(RestaurantCustomer, pk=pk)   
    
    if request.method == 'POST':
        form = RestaurantCustomerForm(request.POST, instance=head_restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_customer_name')  
    else:
        form = RestaurantCustomerForm(instance=head_restaurant)    
    return render(request, 'restaurant/edit_restaurant_customer.html', {
        'form': form,
        'head_restaurants': head_restaurant,
    })


@login_required
def delete_restaurant_customer(request, pk):
    customer_restaurant = get_object_or_404(RestaurantCustomer, pk=pk)
    if request.method == 'POST':
        customer_restaurant.delete()
        return redirect('restaurant_customer_name')
    return render(request, 'restaurant/delete_restaurant_customer.html', {
        'customer_restaurants': customer_restaurant  
    })





@login_required
def restaurant_item_amount_list(request):
    categories = RestaurantCategory.objects.all()
    selected_category = request.GET.get("category") or request.POST.get("category")
    items = RestaurantItemAmount.objects.all()

    # Filter by category
    try:
        category_id = int(selected_category)
        items = items.filter(category_id=category_id)
    except (TypeError, ValueError):
        category_id = None

    # Save / Update item
    if request.method == "POST" and request.POST.get("item_name"):
        category_id_post = request.POST.get("category")
        item_name_id = request.POST.get("item_name")

        if category_id_post and item_name_id:
            RestaurantItemAmount.objects.update_or_create(
                category_id=category_id_post,
                item_name_id=item_name_id,
                defaults={
                    "item_code": request.POST.get("item_code", "").strip(),
                    "opening_stock": request.POST.get("opening_stock") or 0,
                    "purchase_price": request.POST.get("purchase_price") or 0,
                    "selling_price": request.POST.get("selling_price") or 0,
                    "reorder_warning": request.POST.get("reorder_warning") or 0,
                    "reorder_size": request.POST.get("reorder_size") or 0,
                    "unit": request.POST.get("unit", "PRCE").strip(),
                },
            )
            return redirect(f"{request.path}?category={category_id_post}")

    context = {
        "categories": categories,
        "items": items,
        "selected_category": category_id,
    }
    return render(request, "restaurant/restaurant_item_amount_list.html", context)






@login_required
def get_item_amount_data(request):
    item_id = request.GET.get("item_id")
    if item_id:
        try:
            item_amount = RestaurantItemAmount.objects.get(item_name_id=item_id)
            data = {
                "item_code": item_amount.item_code,
                "opening_stock": item_amount.opening_stock,
                "purchase_price": str(item_amount.purchase_price or ""),
                "selling_price": str(item_amount.selling_price or ""),
                "reorder_warning": item_amount.reorder_warning,
                "reorder_size": item_amount.reorder_size,
                "unit": item_amount.unit,
            }
            return JsonResponse({"status": "ok", "data": data})
        except RestaurantItemAmount.DoesNotExist:
            return JsonResponse({"status": "empty", "data": {}})
    return JsonResponse({"status": "error"})

@login_required
def delete_items(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ids = data.get("ids", [])
        RestaurantItemAmount.objects.filter(id__in=ids).delete()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"})


@login_required
def restaurant_item_amount_add(request):
    if request.method == "POST":
        form = RestaurantItemAmountForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            item_name = form.cleaned_data['item_name']

            if RestaurantItemAmount.objects.filter(category=category, item_name=item_name).exists():
                messages.warning(request, f"The item '{item_name}' already exists in this category.")
            else:
                form.save()
                messages.success(request, f"Item '{item_name}' added successfully.")
                return redirect(f"/dashboard/restaurant-item-amount/list?category={category.id}")
        else:
            messages.error(request, "Form is not valid. Please check the inputs.")
    else:
        form = RestaurantItemAmountForm()

    return render(request, "restaurant/restaurant_item_amount_add.html", {"form": form})

@login_required
def load_items(request):
    category_id = request.GET.get('category')
    items = RestaurantItem.objects.filter(rest_category_id=category_id).order_by('rest_item_name')
    data = [{"id": item.id, "name": item.rest_item_name} for item in items]
    return JsonResponse(data, safe=False)




# from decimal import Decimal
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone

# from .forms import RestaurantSaleForm

# from .models import (
#     RestaurantItemAmount,
#     RestaurantCustomer,
#     RestaurantSale,
#     RestaurantSaleItem,
# )
# from restahrm.models import ShiftSession


# @login_required
# def restaurant_sales_list(request, sale_id=None):
#     restSalItems = RestaurantItemAmount.objects.all()
#     restCustomers = RestaurantCustomer.objects.all()

#     # stock report links).
#     active_shift = ShiftSession.objects.filter(
#         user=request.user, is_active=True
#     ).first()

#     sale_instance = get_object_or_404(RestaurantSale, id=sale_id) if sale_id else None

#     # Invoice ID generation
#     if sale_instance:
#         next_invoice = sale_instance.invoice_no
#     else:
#         last_sale = RestaurantSale.objects.all().order_by('-id').first()
#         if last_sale and last_sale.invoice_no:
#             try:
#                 last_no = int(last_sale.invoice_no.replace("INV-", ""))
#             except Exception:
#                 last_no = 0
#             next_invoice = f"INV-{last_no+1:05d}"
#         else:
#             next_invoice = "INV-00001"

#     if request.method == "POST":
#         form = RestaurantSaleForm(request.POST, instance=sale_instance)
#         if form.is_valid():
#             sale = form.save(commit=False)

#             # Parse discount safely
#             try:
#                 discount_value = Decimal(request.POST.get("discount", "0") or "0")
#             except Exception:
#                 discount_value = Decimal("0.00")

#             sale.discount = str(discount_value)
            
#             # Set created_by if creating new sale
#             if not sale_instance and hasattr(sale, 'created_by'):
#                 sale.created_by = request.user.username or str(request.user)

#             sale.save()  # Save first to get/maintain ID for foreign key linking

#             # If editing an existing sale, clear previous sale item entries
#             if sale_instance:
#                 sale_instance.items.all().delete()

#             total_amount = Decimal("0.00")

#             # First Pass: Calculate subtotal across selected items
#             items_to_create = []
#             for item in restSalItems:
#                 qty_val = request.POST.get(f"qty_{item.id}")
#                 if qty_val and int(qty_val) > 0:
#                     qty = int(qty_val)
#                     price = Decimal(item.selling_price or 0)
#                     amount = qty * price
#                     total_amount += amount
#                     items_to_create.append({
#                         'item': item,
#                         'qty': qty,
#                         'price': price,
#                         'amount': amount
#                     })

#             # Second Pass: Create line sale items
#             for item_data in items_to_create:
#                 item = item_data['item']
#                 qty = item_data['qty']
#                 price = item_data['price']
#                 amount = item_data['amount']

#                 # Proportional discount allocation per line item
#                 if total_amount > 0:
#                     item_discount = (amount / total_amount) * discount_value
#                 else:
#                     item_discount = Decimal("0.00")

#                 final_amount = max(Decimal("0.00"), amount - item_discount)

#                 RestaurantSaleItem.objects.create(
#                     sale=sale,
#                     item=item,
#                     quantity=qty,
#                     price=price,
#                     amount=amount,
#                     discount=str(item_discount),
#                     final_amount=final_amount
#                 )

#             # Calculate and save final bill amounts & paid/return amounts
#             sale.total_amount = total_amount
#             calculated_final_amount = max(Decimal("0.00"), total_amount - discount_value)
#             sale.final_amount = calculated_final_amount

#             # Parse paid amount & calculate return amount safely
#             try:
#                 paid_value = Decimal(request.POST.get("paid_amount", "0") or "0")
#             except Exception:
#                 paid_value = Decimal("0.00")
                
#             sale.paid_amount = paid_value
#             sale.return_amount = max(Decimal("0.00"), paid_value - calculated_final_amount)
            
#             sale.save()

#             messages.success(request, f"Sale {sale.invoice_no} saved successfully!")

#             # Check if Auto Print checkbox was checked
#             auto_print = request.POST.get("auto_print") == "on"
#             if auto_print:
#                 # Redirect directly to invoice view with auto_print=true flag
#                 redirect_url = f"{reverse('restaurant_sales_view', kwargs={'sale_id': sale.id})}?auto_print=true"
#                 return redirect(redirect_url)

#             return redirect("restaurant_sales_list")

#     else:
#         form = RestaurantSaleForm(instance=sale_instance)

#     # Fetch Latest 5 Invoices
#     invoice_list = RestaurantSale.objects.all().order_by('-id')[:5]

#     return render(request, "restaurant/restaurant_sales_list.html", {
#         "form": form,
#         "restSalItems": restSalItems,
#         "restCustomers": restCustomers,
#         "next_invoice": next_invoice,
#         "invoice_list": invoice_list,
#         "sale_instance": sale_instance,
#         "active_shift": active_shift,  # NEW
#     })



from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import RestaurantSaleForm

from .models import (
    RestaurantItemAmount,
    RestaurantCustomer,
    RestaurantSale,
    RestaurantSaleItem,
)
from restahrm.models import ShiftSession


@login_required
def restaurant_sales_list(request, sale_id=None):
    restSalItems = RestaurantItemAmount.objects.all()
    restCustomers = RestaurantCustomer.objects.all()

    active_shift = ShiftSession.objects.filter(
        user=request.user, is_active=True
    ).first()

    sale_instance = get_object_or_404(RestaurantSale, id=sale_id) if sale_id else None

    # Invoice ID generation
    if sale_instance:
        next_invoice = sale_instance.invoice_no
    else:
        last_sale = RestaurantSale.objects.all().order_by('-id').first()
        if last_sale and last_sale.invoice_no:
            try:
                last_no = int(last_sale.invoice_no.replace("INV-", ""))
            except Exception:
                last_no = 0
            next_invoice = f"INV-{last_no+1:05d}"
        else:
            next_invoice = "INV-00001"

    if request.method == "POST":
        form = RestaurantSaleForm(request.POST, instance=sale_instance)
        if form.is_valid():
            sale = form.save(commit=False)

            # Parse discount safely
            try:
                discount_value = Decimal(request.POST.get("discount", "0") or "0")
            except Exception:
                discount_value = Decimal("0.00")

            # FIX: keep this as Decimal, not str - storing it as text is what
            # causes "unsupported operand type(s) for -: 'decimal.Decimal' and 'str'"
            # anywhere downstream that does math with sale.discount (e.g. reports,
            # the item-sales list page).
            sale.discount = discount_value

            # Set created_by if creating new sale
            if not sale_instance and hasattr(sale, 'created_by'):
                sale.created_by = request.user.username or str(request.user)

            sale.save()  # Save first to get/maintain ID for foreign key linking

            # If editing an existing sale, clear previous sale item entries
            if sale_instance:
                sale_instance.items.all().delete()

            total_amount = Decimal("0.00")

            # First Pass: Calculate subtotal across selected items
            items_to_create = []
            for item in restSalItems:
                qty_val = request.POST.get(f"qty_{item.id}")
                if qty_val and int(qty_val) > 0:
                    qty = int(qty_val)
                    price = Decimal(item.selling_price or 0)
                    amount = qty * price
                    total_amount += amount
                    items_to_create.append({
                        'item': item,
                        'qty': qty,
                        'price': price,
                        'amount': amount
                    })

            # Second Pass: Create line sale items
            for item_data in items_to_create:
                item = item_data['item']
                qty = item_data['qty']
                price = item_data['price']
                amount = item_data['amount']

                # Proportional discount allocation per line item
                if total_amount > 0:
                    item_discount = (amount / total_amount) * discount_value
                else:
                    item_discount = Decimal("0.00")

                final_amount = max(Decimal("0.00"), amount - item_discount)

                RestaurantSaleItem.objects.create(
                    sale=sale,
                    item=item,
                    quantity=qty,
                    price=price,
                    amount=amount,
                    # FIX: same as above - keep as Decimal, not str
                    discount=item_discount,
                    final_amount=final_amount
                )

            # Calculate and save final bill amounts & paid/return amounts
            sale.total_amount = total_amount
            calculated_final_amount = max(Decimal("0.00"), total_amount - discount_value)
            sale.final_amount = calculated_final_amount

            # Parse paid amount & calculate return amount safely
            try:
                paid_value = Decimal(request.POST.get("paid_amount", "0") or "0")
            except Exception:
                paid_value = Decimal("0.00")

            sale.paid_amount = paid_value
            sale.return_amount = max(Decimal("0.00"), paid_value - calculated_final_amount)

            sale.save()

            messages.success(request, f"Sale {sale.invoice_no} saved successfully!")

            # Check if Auto Print checkbox was checked
            auto_print = request.POST.get("auto_print") == "on"
            if auto_print:
                redirect_url = f"{reverse('restaurant_sales_view', kwargs={'sale_id': sale.id})}?auto_print=true"
                return redirect(redirect_url)

            return redirect("restaurant_sales_list")

    else:
        form = RestaurantSaleForm(instance=sale_instance)

    # Fetch Latest 5 Invoices
    invoice_list = RestaurantSale.objects.all().order_by('-id')[:5]

    return render(request, "restaurant/restaurant_sales_list.html", {
        "form": form,
        "restSalItems": restSalItems,
        "restCustomers": restCustomers,
        "next_invoice": next_invoice,
        "invoice_list": invoice_list,
        "sale_instance": sale_instance,
        "active_shift": active_shift,
    })
    
    
    

from .models import (
    RestaurantItemAmount,
    RestaurantCustomer,
    RestaurantSale,
    RestaurantSaleItem,
    RestaurantDamageFood,   # <-- was missing
)

@login_required
def record_damage_food(request):
    """
    Record Damaged / Wasted Food Items.
    Sourced from RestaurantItemAmount (not RestaurantItem) so the saved
    item_id matches what RestaurantItemAmount.available_qty filters
    RestaurantDamageFood against.
    """
    items = (
        RestaurantItemAmount.objects
        .select_related('item_name')
        .order_by('item_name__rest_item_name')
    )

    if request.method == "POST":
        item_id = request.POST.get('item_id')
        qty = int(request.POST.get('quantity', 0) or 0)
        reason = request.POST.get('reason', '')

        if item_id and qty > 0:
            target_item = get_object_or_404(RestaurantItemAmount, id=item_id)
            RestaurantDamageFood.objects.create(
                item=target_item,
                quantity=qty,
                reason=reason,
                reported_by=request.user.username or str(request.user)
            )
            item_display = (
                target_item.item_name.rest_item_name
                if target_item.item_name else target_item.item_code
            )
            messages.success(request, f"Recorded {qty} damaged unit(s) for {item_display}.")
            return redirect("restaurant_sales_list")
        else:
            messages.error(request, "Please select an item and enter a valid quantity.")

    return render(request, "restaurant/record_damage.html", {"items": items})
    

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from restaurant.models import RestaurantDamageFood, RestaurantItemAmount

from .forms import RestaurantDamageFoodForm
from .models import (
    RestaurantEmployee,
    ShiftItemSnapshot,
    ShiftSession,
    StockRequisition,
)


def _build_items_data():
    """Shared helper: current stock + status badges for every item."""
    items_data = []
    items = RestaurantItemAmount.objects.select_related('item_name').all()

    for item in items:
        qty = item.available_qty
        if qty == 0:
            badge_color = 'bg-danger text-white'
            label = '0 (Out of Stock)'
        elif 1 <= qty <= 10:
            badge_color = 'bg-warning text-dark'
            label = f'{qty} (Low Stock)'
        elif 11 <= qty <= 20:
            badge_color = 'bg-info text-white'
            label = f'{qty} (10-20 Qty)'
        elif 21 <= qty <= 30:
            badge_color = 'bg-primary text-white'
            label = f'{qty} (20-30 Qty)'
        elif 31 <= qty <= 40:
            badge_color = 'bg-secondary text-white'
            label = f'{qty} (30-40 Qty)'
        else:
            badge_color = 'bg-success text-white'
            label = f'{qty} (50+ Optimal)'

        items_data.append(
            {
                'item': item,
                'available_qty': qty,
                'badge_color': badge_color,
                'label': label,
            }
        )
    return items_data


@login_required
def shift_dashboard(request):
    user = request.user
    emp_profile = RestaurantEmployee.objects.filter(user=user).first()
    project = emp_profile.project_name if emp_profile else None

    active_shift = ShiftSession.objects.filter(
        user=user, is_active=True
    ).first()

    my_pending_requests = StockRequisition.objects.filter(
        requested_by=user, status='pending'
    ).select_related('item_amount', 'item_amount__item_name')

    context = {
        'active_shift': active_shift,
        'items_data': _build_items_data(),
        'emp_profile': emp_profile,
        'project': project,
        'my_pending_requests': my_pending_requests,
    }
    return render(request, 'restaurant/shift_dashboard.html', context)


@login_required
def start_work(request):
    user = request.user
    emp_profile = RestaurantEmployee.objects.filter(user=user).first()
    project = emp_profile.project_name if emp_profile else None

    active_shift = ShiftSession.objects.filter(
        user=user, is_active=True
    ).first()

    if not active_shift:
        shift = ShiftSession.objects.create(
            user=user,
            employee=emp_profile,
            project_name=project,
            is_active=True,
        )

        for item in RestaurantItemAmount.objects.all():
            ShiftItemSnapshot.objects.create(
                shift=shift,
                item_amount=item,
                opening_stock=item.available_qty,
            )

        messages.success(
            request, 'Work shift started! Opening stock report generated below.'
        )
        return redirect('opening_stock_report', shift_id=shift.id)

    # Already has an active shift - just show them today's opening report again
    return redirect('opening_stock_report', shift_id=active_shift.id)


@login_required
def opening_stock_report(request, shift_id):
    """Printable 'Day Opening Stock Report' - named to the user who started the shift."""
    shift = get_object_or_404(ShiftSession, pk=shift_id, user=request.user)
    snapshots = shift.snapshots.select_related(
        'item_amount', 'item_amount__item_name'
    ).all()
    return render(
        request,
        'restaurant/opening_stock_report.html',
        {'shift': shift, 'snapshots': snapshots},
    )


@login_required
def stop_work(request):
    active_shift = ShiftSession.objects.filter(
        user=request.user, is_active=True
    ).first()

    if active_shift:
        active_shift.end_time = timezone.now()
        active_shift.is_active = False
        active_shift.save()

        for snapshot in active_shift.snapshots.all():
            snapshot.closing_stock = snapshot.item_amount.available_qty
            snapshot.save()

        messages.success(request, 'Work shift ended! Closing stock report generated.')
        return redirect('shift_report', shift_id=active_shift.id)

    return redirect('shift_dashboard')


@login_required
def request_stock_increase(request):
    """
    Adds stock immediately - no approval step. Only ever increases
    opening_stock (never decreases), and is logged via StockRequisition
    purely as an audit trail (auto-approved), not a pending gate.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        qty = int(request.POST.get('quantity', 0) or 0)

        if qty <= 0:
            messages.error(request, 'Please enter a quantity greater than 0.')
            return redirect('shift_dashboard')

        item_amount = get_object_or_404(RestaurantItemAmount, pk=item_id)
        emp_profile = RestaurantEmployee.objects.filter(user=request.user).first()
        project = emp_profile.project_name if emp_profile else None

        # Audit trail only - status is set to 'approved' immediately, there is
        # no pending state and nobody else needs to sign off on this anymore.
        StockRequisition.objects.create(
            requested_by=request.user,
            employee=emp_profile,
            project_name=project,
            item_amount=item_amount,
            requested_qty=qty,
            status='approved',
            approved_by=request.user,
        )

        item_amount.opening_stock += qty
        item_amount.save()

        messages.success(
            request,
            f'Added +{qty} stock for {item_amount.item_name}. '
            f'New available stock: {item_amount.available_qty}.',
        )

    return redirect('shift_dashboard')
    
    

@login_required
def approve_requisition(request, req_id):
    if request.user.is_staff or request.user.is_superuser:
        requisition = get_object_or_404(StockRequisition, pk=req_id)
        if requisition.status == 'pending':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.save()

            item_amount = requisition.item_amount
            item_amount.opening_stock += requisition.requested_qty
            item_amount.save()

            messages.success(
                request,
                f'Approved +{requisition.requested_qty} for {item_amount.item_name}. '
                f'New available stock: {item_amount.available_qty}.',
            )
        else:
            messages.info(request, 'This request has already been processed.')
    else:
        messages.error(request, 'You do not have permission to approve stock requests.')

    return redirect('shift_dashboard')


@login_required
def add_damage_food(request):
    if request.method == 'POST':
        form = RestaurantDamageFoodForm(request.POST)
        if form.is_valid():
            damage_entry = form.save(commit=False)
            damage_entry.reported_by = request.user
            damage_entry.save()
            messages.success(request, 'Damaged food item recorded.')
            return redirect('shift_dashboard')
    else:
        form = RestaurantDamageFoodForm()

    return render(request, 'restaurant/damage_food_form.html', {'form': form})


@login_required
def shift_report(request, shift_id):
    """Printable 'Day Closing Stock Report' - named to the user who closed the shift."""
    shift = get_object_or_404(ShiftSession, pk=shift_id)
    snapshots = shift.snapshots.select_related(
        'item_amount', 'item_amount__item_name'
    ).all()

    snapshot_rows = []
    total_variance = 0
    for snap in snapshots:
        closing = snap.closing_stock if snap.closing_stock is not None else 0
        variance = closing - snap.opening_stock
        total_variance += variance
        snapshot_rows.append({
            'item_name': (
                snap.item_amount.item_name.rest_item_name
                if snap.item_amount.item_name else f'Item #{snap.item_amount.id}'
            ),
            'opening_stock': snap.opening_stock,
            'closing_stock': snap.closing_stock,
            'variance': variance,
        })

    return render(
        request,
        'restaurant/shift_report.html',
        {'shift': shift, 'snapshot_rows': snapshot_rows, 'total_variance': total_variance},
    )



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import RestaurantSale, RestaurantSaleItem

@login_required
def restaurant_sales_challan(request, sale_id):
    sale = get_object_or_404(RestaurantSale, id=sale_id)
    sale_items = RestaurantSaleItem.objects.filter(sale=sale).select_related('item')

    return render(request, "restaurant/restaurant_sales_challan.html", {
        "sale": sale,
        "sale_items": sale_items,
        "print_time": timezone.now()
    })


    
@login_required
def restaurant_invoice_view(request, sale_id):
    sale = get_object_or_404(RestaurantSale, id=sale_id)
    sale_items = RestaurantSaleItem.objects.filter(sale=sale)

    return render(request, "restaurant/restaurant_invoice_view.html", {
        "sale": sale,
        "sale_items": sale_items,
        "print_time": timezone.now()  # for printing date
    })
    
    
    


@login_required
def restaurant_sales_report(request):
    restaurantsale = RestaurantSale.objects.all().order_by('-id')
    return render(request, 'restaurant/restaurant_sales_report.html', {'restaurantsales': restaurantsale})



    
@login_required
def edit_restaurant_sales(request, pk):
    sales_restaurant = get_object_or_404(RestaurantSale, pk=pk)

    if request.method == 'POST':
        form = RestaurantSaleForm(request.POST, instance=sales_restaurant)
        if form.is_valid():
            sale = form.save(commit=False)

            # Parse total_amount safely from POST
            try:
                sale.total_amount = Decimal(request.POST.get('total_amount', '0') or '0')
            except:
                sale.total_amount = Decimal("0.00")

            # Parse discount safely from POST
            try:
                discount_value = Decimal(request.POST.get('discount', '0') or '0')
            except:
                discount_value = Decimal("0.00")

            sale.discount = str(discount_value)

            # Calculate final_amount
            sale.final_amount = sale.total_amount - discount_value
            if sale.final_amount < 0:
                sale.final_amount = Decimal("0.00")

            sale.save()
            return redirect('restaurant_sales_report')
    else:
        form = RestaurantSaleForm(instance=sales_restaurant)

    return render(request, 'restaurant/edit_restaurant_sales.html', {
        'form': form,
        'sales_restaurants': sales_restaurant,
    })

@login_required
def delete_restaurant_sales(request, pk):
    sales_restaurant = get_object_or_404(RestaurantSale, pk=pk)
    if request.method == 'POST':
        sales_restaurant.delete()
        return redirect('restaurant_sales_report')
    return render(request, 'restaurant/delete_restaurant_sales.html', {
        'salesRestaurants': sales_restaurant  
    })



@login_required
def restaurant_sales_view(request, sale_id):
    sale = get_object_or_404(RestaurantSale, id=sale_id)
    sale_items = RestaurantSaleItem.objects.filter(sale=sale)

    return render(request, "restaurant/restaurant_sales_view.html", {
        "sale": sale,
        "sale_items": sale_items,
        "print_time": timezone.now()  # for printing date
    })
    
    
    
    
    
@login_required
def daily_salary_history(request):
    month_param = request.GET.get('month')
    date_param = request.GET.get('date')

    sales = RestaurantSale.objects.all().order_by('sale_date')

    # Filter by month name if provided
    if month_param:
        try:
            month_number = list(calendar.month_name).index(month_param.capitalize())
            if month_number != 0:
                sales = sales.filter(sale_date__month=month_number)
        except ValueError:
            pass  # ignore invalid month

    # Filter by exact date if provided
    if date_param:
        try:
            date_dt = datetime.strptime(date_param, "%Y-%m-%d").date()
            sales = sales.filter(sale_date=date_dt)
        except ValueError:
            pass  # ignore invalid date

    # Calculate grand total of final_amount for all items
    grand_total = sum(
        item.final_amount for sale in sales for item in sale.items.all()
    )

    context = {
        "sales": sales,
        "grand_total": grand_total,
        "print_time": timezone.now(),
    }
    return render(request, "restaurant/daily_salary_history.html", context)
    





## Head of account --
@login_required
def head_account_name(request):
    restaurants_headAccount = RestHeadofAcct.objects.all()
    return render(request, 'restaurant/headofaccount/restaurant_head_account.html', {'restaurants_headAccounts': restaurants_headAccount})
    
    
@login_required
def add_head_account_name(request):
    if request.method == 'POST':
        form = RestHeadofAcctForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('head_account_name')  
    else:
        form = RestHeadofAcctForm()
    return render(request, 'restaurant/headofaccount/add_restaurant_head_account.html', {'form': form})
    
    
    
@login_required
def restaurant_headofacct_edit(request, pk):
    requis_category = get_object_or_404(RestHeadofAcct, pk=pk)    
    if request.method == 'POST':
        form = RestHeadofAcctForm(request.POST, instance=requis_category)
        if form.is_valid():
            form.save()
            return redirect('head_account_name')  
    else:
        form = RestHeadofAcctForm(instance=requis_category)
    
    return render(request, 'restaurant/headofaccount/restaurant_headofacct_edit.html', {
        'form': form
    })
    
    

@login_required
def restaurant_headofacct_delete(request, pk):
    restu_headname = get_object_or_404(RestHeadofAcct, pk=pk)
    if request.method == 'POST':
        restu_headname.delete()
        return redirect('head_account_name')
    return render(request, 'restaurant/headofaccount/restaurant_headofacct_delete.html', {
        'restu_headnames': restu_headname  
    })





## Account Name List -----
@login_required
def account_name_list(request):
    restaccut = RestaurantAccount.objects.all()
    return render(request, 'restaurant/accountlist/restaurant_account_list.html', {'restaccuts': restaccut})
    
    
    
@login_required
def add_account_name(request):
    restaurant_head = RestHeadofAcct.objects.all()

    if request.method == 'POST':
        form = RestaurantAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_name_list')
    else:
        form = RestaurantAccountForm()
    context = {
        'form': form,
        'restaurant_heads': restaurant_head,
    }

    return render(request, 'restaurant/accountlist/add_account_name.html', context)
    
    
    
@login_required
def edit_restaurant_account(request, pk):
    head_restaurant = get_object_or_404(RestHeadofAcct, pk=pk)   
    
    if request.method == 'POST':
        form = RestaurantAccountForm(request.POST, instance=head_restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_item_name')  
    else:
        form = RestaurantAccountForm(instance=head_restaurant)
        restaurant_headnames = RestHeadofAcct.objects.all()
    
    return render(request, 'restaurant/accountlist/edit_restaurant_account.html', {
        'form': form,
        'head_restaurants': head_restaurant,
        'restaurant_headnames' : restaurant_headnames
    })


@login_required
def delete_restaurant_account(request, pk):
    head_restaurant = get_object_or_404(RestaurantAccount, pk=pk)
    if request.method == 'POST':
        head_restaurant.delete()
        return redirect('account_name_list')
    return render(request, 'restaurant/accountlist/delete_restaurant_account.html', {
        'head_restaurant': head_restaurant  
    })




    
    
### Supplier - ----
    
@login_required
def restaurant_supplier_name(request):
    restSupplier = RestaurantSupplier.objects.all()
    return render(request, 'restaurant/supplier/restaurant_supplier_name.html', {'restSuppliers': restSupplier})
    
    
    
@login_required
def add_restaurant_supplier(request):
    if request.method == 'POST':
        form = RestaurantSupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_supplier_name')
    else:
        form = RestaurantSupplierForm()

    return render(request, 'restaurant/supplier/add_restaurant_supplier.html', {'form': form})
    
    



@login_required
def edit_restaurant_supplier(request, pk):
    supplier = RestaurantSupplier.objects.get(pk=pk)

    if request.method == 'POST':
        form = RestaurantSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('restaurant_supplier_name')
    else:
        form = RestaurantSupplierForm(instance=supplier)

    return render(request,
        'restaurant/supplier/edit_restaurant_supplier.html',
        {'form': form}
    )
    
    

@login_required
def delete_restaurant_supplier(request, pk):
    supplier_restaurant = get_object_or_404(RestaurantSupplier, pk=pk)
    if request.method == 'POST':
        supplier_restaurant.delete()
        return redirect('restaurant_supplier_name')
    return render(request, 'restaurant/supplier/delete_restaurant_supplier.html', {
        'supplier_restaurants': supplier_restaurant  
    })
    


### Jewel Supplier - ----
    
@login_required
def restaurant_jewel_supplier_name(request):
    restSupplier = RestaurantJewelSupplier.objects.all()
    return render(request, 'restaurant/supplier/restaurant_jewel_supplier_name.html', {'restSuppliers': restSupplier})
    
    
    
@login_required
def add_restaurant_jewel_supplier(request):
    if request.method == 'POST':
        form = RestaurantJewelSupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_jewel_supplier_name')
    else:
        form = RestaurantJewelSupplierForm()

    return render(request, 'restaurant/supplier/add_restaurant_jewel_supplier.html', {'form': form})
    
    

@login_required
def edit_restaurant_jewel_supplier(request, pk):
    supplier = RestaurantJewelSupplier.objects.get(pk=pk)

    if request.method == 'POST':
        form = RestaurantJewelSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('restaurant_jewel_supplier_name')
    else:
        form = RestaurantJewelSupplierForm(instance=supplier)

    return render(request,
        'restaurant/supplier/edit_restaurant_jewel_supplier.html',
        {'form': form}
    )
    
    

@login_required
def delete_restaurant_jewel_supplier(request, pk):
    supplier_restaurant = get_object_or_404(RestaurantJewelSupplier, pk=pk)
    if request.method == 'POST':
        supplier_restaurant.delete()
        return redirect('restaurant_jewel_supplier_name')
    return render(request, 'restaurant/supplier/delete_restaurant_jewel_supplier.html', {
        'supplier_restaurants': supplier_restaurant  
    })
    
    
    
    
# ================= Home =================
def public_restaurant_home(request):
    projects = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    return render(
        request,
        'restaurant/public/public_restaurant_requisitions_home.html',
        {
            'projects': projects,
        }
    )


# ================= LIST =================
def public_restaurant_supplier_list(request):
    suppliers = RestaurantJewelSupplier.objects.all().order_by('-id')

    # simple search (optional)
    search = request.GET.get('search')
    if search:
        suppliers = suppliers.filter(rest_supplier_name__icontains=search)

    return render(request, 'restaurant/supplier/public_restaurant_supplier_list.html', {
        'restSuppliers': suppliers
    })


# ================= ADD =================
def public_add_restaurant_supplier(request):
    if request.method == 'POST':
        form = RestaurantJewelSupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_supplier_list')
    else:
        form = RestaurantJewelSupplierForm()

    return render(request, 'restaurant/supplier/public_add_restaurant_supplier.html', {
        'form': form
    })


# ================= EDIT =================
def public_edit_restaurant_supplier(request, pk):
    supplier = get_object_or_404(RestaurantJewelSupplier, pk=pk)

    if request.method == 'POST':
        form = RestaurantJewelSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_supplier_list')
    else:
        form = RestaurantJewelSupplierForm(instance=supplier)

    return render(request, 'restaurant/supplier/public_edit_restaurant_supplier.html', {
        'form': form
    })


# ================= DELETE =================
def public_delete_restaurant_supplier(request, pk):
    supplier = get_object_or_404(RestaurantJewelSupplier, pk=pk)

    if request.method == 'POST':
        supplier.delete()
        return redirect('public_restaurant_supplier_list')

    return render(request, 'restaurant/supplier/public_delete_restaurant_supplier.html', {
        'supplier': supplier
    })
    
    
   
# ================= LIST =================
def public_restaurant_category(request):
    categories = RestaurantCategory.objects.all().order_by('-id')

    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            restu_category_name__icontains=search
        )

    return render(request, 'restaurant/public/restaurant_category.html', {
        'categories': categories
    })



def public_restaurant_requisition_exp_category(request):
    categories = RestaurantExpenseCategory.objects.all().order_by('-id')

    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            restu_Exp_category_name__icontains=search
        )

    return render(request, 'restaurant/public/restaurant_exp_category.html', {
        'categories': categories
    })

# ================= ADD =================
def public_add_restaurant_category(request):
    if request.method == 'POST':
        form = RestaurantCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_requisition_category')
    else:
        form = RestaurantCategoryForm()

    return render(request, 'restaurant/public/add_restaurant_category.html', {
        'form': form
    })


def public_add_restaurant_exp_category(request):
    if request.method == 'POST':
        form = RestaurantExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_requisition_exp_category')
    else:
        form = RestaurantExpenseCategoryForm()

    return render(request, 'restaurant/public/add_restaurant_exp_category.html', {
        'form': form
    })
    
    
# ================= EDIT =================
def public_restaurant_category_edit(request, pk):
    category = get_object_or_404(RestaurantCategory, pk=pk)

    if request.method == 'POST':
        form = RestaurantCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_requisition_category')
    else:
        form = RestaurantCategoryForm(instance=category)

    return render(request, 'restaurant/public/edit_restaurant_category.html', {
        'form': form
    })


def public_restaurant_exp_category_edit(request, pk):
    category = get_object_or_404(RestaurantExpenseCategory, pk=pk)

    if request.method == 'POST':
        form = RestaurantExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_requisition_exp_category')
    else:
        form = RestaurantExpenseCategoryForm(instance=category)

    return render(request, 'restaurant/public/edit_restaurant_exp_category.html', {
        'form': form
    })

# ================= DELETE =================
def public_restaurant_category_delete(request, pk):
    category = get_object_or_404(RestaurantCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        return redirect('public_restaurant_requisition_category')

    return render(request, 'restaurant/public/delete_restaurant_category.html', {
        'category': category
    }) 



# ================= DELETE =================
def public_restaurant_exp_category_delete(request, pk):
    category = get_object_or_404(RestaurantExpenseCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        return redirect('public_restaurant_requisition_exp_category')

    return render(request, 'restaurant/public/delete_restaurant_exp_category.html', {
        'category': category
    }) 




# ================= LIST =================
def public_restaurant_item_list(request):
    items = RestaurantItem.objects.select_related('rest_category').all().order_by('-id')

    search = request.GET.get('search')
    if search:
        items = items.filter(rest_item_name__icontains=search)

    return render(request, 'restaurant/public/restaurant_item_list.html', {
        'restItems': items
    })


# ================= ADD =================
def public_add_restaurant_item(request):
    categories = RestaurantCategory.objects.all()

    if request.method == 'POST':
        form = RestaurantItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_item_name')
    else:
        form = RestaurantItemForm()

    return render(request, 'restaurant/public/add_restaurant_item.html', {
        'form': form,
        'categories': categories
    })


# ================= EDIT =================
def public_edit_restaurant_item(request, pk):
    item = get_object_or_404(RestaurantItem, pk=pk)
    categories = RestaurantCategory.objects.all()

    if request.method == 'POST':
        form = RestaurantItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('public_restaurant_item_name')
    else:
        form = RestaurantItemForm(instance=item)

    return render(request, 'restaurant/public/edit_restaurant_item.html', {
        'form': form,
        'categories': categories,
        'item': item
    })


# ================= DELETE =================
def public_delete_restaurant_item(request, pk):
    item = get_object_or_404(RestaurantItem, pk=pk)

    if request.method == 'POST':
        item.delete()
        return redirect('public_restaurant_item_name')

    return render(request, 'restaurant/public/delete_restaurant_item.html', {
        'item': item
    })
    




import json
import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages

logger = logging.getLogger(__name__)

def restaurant_expense_purchase_history(request):
    # Fetch suppliers safely
    try:
        suppliers = RestaurantJewelSupplier.objects.all()
    except NameError:
        suppliers = []

    # --- 1. HANDLE AJAX POST REQUESTS (POS & INLINE UPDATES) ---
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)

            # --- CASE A: Handle POS Basket Submission ---
            if "items" in data:
                items = data.get("items", [])
                supplier_name = data.get("supplier_name")
                project_id = data.get("project_id")
                purchase_date = data.get("date")

                # Map employee_id based on project_id requirement
                employee_id = None
                if str(project_id) == "36":
                    employee_id = 24
                elif str(project_id) == "60":
                    employee_id = 54
                else:
                    employee_id = data.get("employee_id")

                # Get model instances
                supplier_instance = None
                if supplier_name and 'RestaurantSupplier' in globals():
                    supplier_instance = RestaurantSupplier.objects.filter(
                        rest_supplier_name__iexact=supplier_name.strip()
                    ).first()

                employee_instance = None
                if employee_id and 'RestaurantEmployee' in globals():
                    employee_instance = RestaurantEmployee.objects.filter(id=employee_id).first()

                for item in items:
                    item_id = item.get("item_id")
                    qty = Decimal(str(item.get("qty", 0)))
                    rate = Decimal(str(item.get("rate", 0)))
                    amount = qty * rate

                    item_obj = None
                    if 'RestaurantItem' in globals():
                        item_obj = RestaurantItem.objects.filter(id=item_id).first()

                    # Save to Inventory Table with mapped employee
                    if 'RestInventories' in globals():
                        RestInventories.objects.create(
                            project_name_id=project_id if project_id else None,
                            employee_name=employee_instance,
                            item_name=item_obj,
                            vendor_name=supplier_instance,
                            qty=int(qty),
                            rate=rate,
                            amount=amount,
                            purch_date=purchase_date,
                        )

                return JsonResponse({
                    "status": "success",
                    "message": "POS Purchase saved and synced successfully!"
                })

            # --- CASE B: Handle Single Dynamic Row Updates ---
            row_id = data.get("id")
            field = data.get("field")
            value = data.get("value")
            calc_mode = data.get("calc_mode", "unit")

            if not row_id:
                return JsonResponse({"status": "error", "message": "Missing Record ID."}, status=400)

            # Fetch target record
            req_item = RestRequisition.objects.get(id=row_id)

            # Map dynamic input variables
            qty = Decimal(str(value or 0)) if field == "qty" else (req_item.qty or Decimal('0'))
            rate = Decimal(str(value or 0)) if field == "rate" else (req_item.rate or Decimal('0'))
            discount = Decimal(str(req_item.discount or 0))
            vendor_name = value if field == "vendor_name" else req_item.vendor_name
            approv_purch_status = value if field == "approv_purch_status" else req_item.approv_purch_status
            target_calc_mode = value if field == "calc_mode" else calc_mode
                
            # Dynamic amount calculation
            if target_calc_mode == "whole":
                final_amount = (rate - discount).quantize(Decimal('0.01'))
            else:
                final_amount = (qty * rate - discount).quantize(Decimal('0.01'))
            
            final_amount = max(final_amount, Decimal("0.00"))

            # Update Requisition
            req_item.qty = qty
            req_item.rate = rate
            req_item.amount = final_amount
            req_item.vendor_name = vendor_name
            req_item.approv_purch_status = approv_purch_status
            req_item.calc_mode = target_calc_mode
            req_item.save()

            # Sync Inventory table
            supplier_instance = None
            if req_item.vendor_name and 'RestaurantSupplier' in globals():
                supplier_instance = RestaurantSupplier.objects.filter(
                    rest_supplier_name__iexact=req_item.vendor_name.strip()
                ).first()

            if 'RestInventories' in globals():
                RestInventories.objects.update_or_create(
                    requi_id=req_item.id,
                    defaults={
                        'project_name': req_item.project_name,
                        'employee_name': req_item.employee_name,
                        'item_name': req_item.item_name,
                        'vendor_name': supplier_instance,
                        'unit': req_item.unit or '',
                        'qty': int(qty),
                        'rate': rate,
                        'amount': final_amount,
                        'remark': req_item.remark or '',
                        'approv_note': req_item.approv_note,
                        'approv_acct_note': req_item.approv_acct_note,
                        'approv_purch_note': req_item.approv_purch_note,
                        'requisition_date': req_item.requisition_date,
                        'purch_id': req_item.purch_id,
                        'purch_date': req_item.purch_date,
                    }
                )

            return JsonResponse({
                "status": "success", 
                "message": "Saved and synced successfully.",
                "total_amount": float(final_amount)
            })

        except Exception as e:
            logger.error(f"AJAX Requisition Update Error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # --- 2. CAPTURE WORKSPACE FILTERS ---
    project_id_filter = request.GET.get('project')
    employee_id_filter = request.GET.get('employee')

    filters = Q(
        return_requisition__isnull=True,
        approv_store='approved',  
        requi_uniq_id__isnull=True,
    )

    if project_id_filter:
        filters &= Q(project_name_id=project_id_filter)
    if employee_id_filter:
        filters &= Q(employee_name_id=employee_id_filter)

    requisitions = (
        RestRequisition.objects
        .filter(filters)
        .select_related('project_name', 'employee_name', 'item_name')
        .order_by('-id')
    )

    # --- 3. HANDLE STANDARD FORM SUBMISSION ---
    if request.method == "POST":
        running_grand_total = Decimal('0.00')

        for item in requisitions:
            qty_input = request.POST.get(f'qty_{item.id}', str(item.qty or 0))
            rate_input = request.POST.get(f'rate_{item.id}', str(item.rate or 0))
            discount_input = request.POST.get(f'discount_{item.id}', str(item.discount or 0))
            remark_input = request.POST.get(f'remark_{item.id}', item.remark or '')
            calc_mode = request.POST.get(f'calc_mode_{item.id}', item.calc_mode or 'unit')

            try:
                qty = Decimal(qty_input)
                rate = Decimal(rate_input)
                discount = Decimal(discount_input)
            except (ValueError, TypeError):
                qty = Decimal('0.00')
                rate = Decimal('0.00')
                discount = Decimal('0.00')

            if calc_mode == "whole":
                calculated_amount = rate - discount
            else:
                calculated_amount = (qty * rate) - discount

            calculated_amount = max(calculated_amount, Decimal('0.00'))

            item.qty = qty
            item.rate = rate
            item.discount = discount
            item.amount = calculated_amount
            item.calc_mode = calc_mode
            item.remark = remark_input
            item.save()

            running_grand_total += calculated_amount

            supplier_instance = None
            if item.vendor_name and 'RestaurantSupplier' in globals():
                supplier_instance = RestaurantSupplier.objects.filter(
                    rest_supplier_name__iexact=item.vendor_name.strip()
                ).first()

            if 'RestInventories' in globals():
                RestInventories.objects.update_or_create(
                    requi_id=item.id,
                    defaults={
                        'project_name': item.project_name,
                        'employee_name': item.employee_name,
                        'item_name': item.item_name,
                        'vendor_name': supplier_instance,
                        'unit': item.unit or '',
                        'qty': int(qty),
                        'rate': rate,
                        'amount': calculated_amount,
                        'remark': remark_input,
                        'approv_note': item.approv_note,
                        'approv_acct_note': item.approv_acct_note,
                        'approv_purch_note': item.approv_purch_note,
                        'requisition_date': item.requisition_date,
                        'purch_id': item.purch_id,
                        'purch_date': item.purch_date,
                    }
                )

        first_item = requisitions.first()
        if first_item and first_item.project_name and first_item.employee_name and 'RestaurantKitchenLedger' in globals():
            RestaurantKitchenLedger.objects.update_or_create(
                type='Purchase',
                requisition=first_item,
                project=first_item.project_name,
                employee=first_item.employee_name,
                item_name=first_item.item_name,
                defaults={
                    'debit': Decimal('0.00'),
                    'credit': running_grand_total,
                }
            )

        messages.success(request, "Requisition items, Inventory records, and Kitchen Ledger updated successfully.")
        return redirect(request.get_full_path())

    # --- 4. PROCESS ROWS FOR TEMPLATE RENDER ---
    flat_data = []
    for req in requisitions:
        if req.project_name:
            project_name_str = getattr(req.project_name, 'project_first_name', str(req.project_name))
            project_id = req.project_name.id
        else:
            project_name_str = "No Project Assigned"
            project_id = None

        if req.employee_name:
            employee_name_str = getattr(req.employee_name, 'rda_emp_name', str(req.employee_name))
        else:
            employee_name_str = "No Employee Assigned"

        if req.item_name:
            item_name_str = getattr(req.item_name, 'item_name', getattr(req.item_name, 'name', str(req.item_name)))
        else:
            item_name_str = "No Item Specified"

        current_qty = float(req.qty) if req.qty else 0.0
        current_rate = float(req.rate) if req.rate else 0.0
        current_amount = float(req.amount) if req.amount else 0.0

        detected_mode = req.calc_mode
        if not detected_mode:
            detected_mode = "unit"
            if current_rate > 0 and current_amount == current_rate and current_qty != 1.0:
                detected_mode = "whole"

        flat_data.append({
            'id': req.id,
            'requisition_date': req.requisition_date,
            'project_name': project_name_str,
            'project_id': project_id,
            'employee_name': employee_name_str,
            'item_name': item_name_str,
            'unit': req.unit or '',
            'vendor_name': req.vendor_name if req.vendor_name else "",
            'total_qty': current_qty,
            'rate': current_rate,
            'total_amount': current_amount,
            'store_status': str(req.approv_store).lower().strip() if req.approv_store else 'pending',
            'purch_status': str(req.approv_purch_status or 'pending').lower().strip(),
            'calc_mode': detected_mode,
        })

    query_string = request.META.get('QUERY_STRING', '')
    url_suffix = f"?{query_string}" if query_string else ""

    context = {
        'grouped_data': flat_data, 
        'projects_firts': ProjectFirstLevelName.objects.filter(
            project_first_name__in=["The Galleria Restauent Cafe", "The Galleria Live Kitchen"]
        ) if 'ProjectFirstLevelName' in globals() else [],
        'employees': RestaurantEmployee.objects.exclude(rda_emp_type__iexact='admin') if 'RestaurantEmployee' in globals() else [],
        'items': RestaurantItem.objects.all() if 'RestaurantItem' in globals() else [],
        'suppliers': suppliers,
        'url_suffix': url_suffix,
        'current_project': project_id_filter or '',
        'current_employee': employee_id_filter or '',
    }

    return render(request, 'restaurant/requisitions/restaurant_expense_purchase_history.html', context)
    
    




import json
import logging
import traceback
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)


def _resolve_req_date(date_str):
    """Helper to safely parse requisition date string into a date object."""
    if not date_str:
        return date.today()
    try:
        if isinstance(date_str, date):
            return date_str
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date.today()


def _map_employee_by_project(project_id, employee_id=None):
    """Rule Mapping: Project 36 -> Employee 24 | Project 60 -> Employee 54"""
    p_id = str(project_id) if project_id else ""
    if p_id == "36":
        return 24
    elif p_id == "60":
        return 54
    return employee_id


def _get_jewel_vendor_instance(vendor_str):
    """Returns FK instance for RestRequisition (RestaurantJewelSupplier)."""
    if not vendor_str or "RestaurantJewelSupplier" not in globals():
        return None
    return RestaurantJewelSupplier.objects.filter(
        rest_supplier_name__iexact=str(vendor_str).strip()
    ).first()


def _get_inventory_vendor_instance(vendor_str):
    """Returns FK instance for RestInventories (RestaurantSupplier)."""
    if not vendor_str or "RestaurantSupplier" not in globals():
        return None
    return RestaurantSupplier.objects.filter(
        rest_supplier_name__iexact=str(vendor_str).strip()
    ).first()


def restau_requisition_list_public(request):
    # Fetch suppliers safely for template dropdowns
    suppliers = (
        RestaurantJewelSupplier.objects.all()
        if "RestaurantJewelSupplier" in globals()
        else []
    )

    # ------------------------------------------------------------------
    # 1. AJAX GET: Load Category Items, Stock, and Saved Requisitions
    # ------------------------------------------------------------------
    if request.method == "GET" and "category_id" in request.GET:
        try:
            cat_id = request.GET.get("category_id")
            project_id = request.GET.get("project_id") or None
            employee_id = _map_employee_by_project(
                project_id, request.GET.get("employee_id") or None
            )
            req_date = _resolve_req_date(request.GET.get("req_date"))

            items = RestaurantItem.objects.filter(
                rest_category_id=cat_id
            ).order_by("rest_item_name")
            item_ids = list(items.values_list("id", flat=True))

            # -- Current stock per item: IN (qty) minus OUT (qtysub) --------
            stock_map = {}
            if "RestInventories" in globals():
                stock_rows = (
                    RestInventories.objects.filter(item_name_id__in=item_ids)
                    .values("item_name_id")
                    .annotate(in_qty=Sum("qty"), out_qty=Sum("qtysub"))
                )
                stock_map = {
                    r["item_name_id"]: (r["in_qty"] or 0) - (r["out_qty"] or 0)
                    for r in stock_rows
                }

            # -- Already-saved requisition per item on that date ------------
            saved_map = {}
            if project_id and employee_id:
                saved = RestRequisition.objects.filter(
                    requisition_date=req_date,
                    project_name_id=project_id,
                    employee_name_id=employee_id,
                    item_name_id__in=item_ids,
                )
                saved_map = {
                    r.item_name_id: {
                        "qty": float(r.qty or 0),
                        "unit": r.unit or "",
                        "vendor": (
                            r.vendor_name.rest_supplier_name
                            if getattr(r, "vendor_name", None)
                            else ""
                        ),
                        "rate": float(r.rate or 0),
                        "amount": float(r.amount or 0),
                        "calc_mode": r.calc_mode or "normal",
                        "approv_store": r.approv_store or "pending",
                        "approv_purch": r.approv_purch_status or "pending",
                        "req_id": r.id,
                    }
                    for r in saved
                }

            payload = []
            for it in items:
                s = saved_map.get(it.id, {})
                payload.append(
                    {
                        "id": it.id,
                        "name": getattr(it, "rest_item_name", str(it)),
                        "code": getattr(it, "rest_item_code", "") or "",
                        "stock": stock_map.get(it.id, 0),
                        "saved_qty": s.get("qty", ""),
                        "saved_unit": s.get("unit", ""),
                        "saved_vendor": s.get("vendor", ""),
                        "saved_rate": s.get("rate", ""),
                        "saved_amount": s.get("amount", 0),
                        "saved_calc_mode": s.get("calc_mode", "normal"),
                        "approv_store": s.get("approv_store", "pending"),
                        "approv_purch": s.get("approv_purch", "pending"),
                        "req_id": s.get("req_id", None),
                    }
                )
            return JsonResponse({"status": "success", "items": payload})
        except Exception as err:
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": str(err)}, status=500
            )

    # ------------------------------------------------------------------
    # 2. AJAX POST: Auto-save one item / POS Basket / Approvals
    # ------------------------------------------------------------------
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        try:
            data = json.loads(request.body)
            action = data.get("action")
            req_date = _resolve_req_date(
                data.get("req_date") or data.get("date")
            )

            # ---------- 2a. Auto-save a single item row into RestRequisition -----------
            if action == "save_item":
                project_id = data.get("project_id")
                raw_employee_id = data.get("employee_id")
                employee_id = _map_employee_by_project(
                    project_id, raw_employee_id
                )
                item_id = data.get("item_id")
                unit = (data.get("unit") or "").strip()
                vendor_str = (data.get("vendor") or "").strip()[:100]
                jewel_vendor = _get_jewel_vendor_instance(vendor_str)
                calc_mode = data.get("calc_mode") or "normal"

                if calc_mode not in ("normal", "unit", "whole"):
                    calc_mode = "normal"

                try:
                    qty = Decimal(str(data.get("qty") or 0))
                    rate = Decimal(str(data.get("rate") or 0))
                except InvalidOperation:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Invalid quantity or rate value.",
                        }
                    )

                if rate <= 0:
                    rate = Decimal("1.00")

                if calc_mode == "unit":
                    amount = (qty * rate).quantize(Decimal("0.01"))
                else:
                    amount = rate.quantize(Decimal("0.01"))

                if not (project_id and employee_id and item_id):
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Project, Employee, and Item are required.",
                        }
                    )

                if qty <= 0:
                    RestRequisition.objects.filter(
                        requisition_date=req_date,
                        project_name_id=project_id,
                        employee_name_id=employee_id,
                        item_name_id=item_id,
                        approv_store="pending",
                    ).delete()
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "Row removed.",
                            "saved": False,
                        }
                    )

                if not unit:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Please select a unit first.",
                        }
                    )

                lookup = dict(
                    requisition_date=req_date,
                    project_name_id=project_id,
                    employee_name_id=employee_id,
                    item_name_id=item_id,
                )
                existing = RestRequisition.objects.filter(**lookup).order_by(
                    "id"
                )

                if existing.exists():
                    obj = existing.first()
                    existing.exclude(id=obj.id).delete()
                    obj.type = "Restaurant"
                    obj.unit = unit
                    obj.qty = qty
                    obj.vendor_name = jewel_vendor
                    obj.rate = rate
                    obj.amount = amount
                    obj.calc_mode = calc_mode
                    obj.discount = Decimal("0.00")
                    obj.save()
                    created = False
                else:
                    obj = RestRequisition.objects.create(
                        **lookup,
                        type="Restaurant",
                        unit=unit,
                        qty=qty,
                        vendor_name=jewel_vendor,
                        rate=rate,
                        amount=amount,
                        calc_mode=calc_mode,
                        discount=Decimal("0.00"),
                        description=data.get("description", "") or "",
                        remark=data.get("remark", "") or "",
                        approv_store="pending",
                        approv_purch_status="pending",
                        requi_uniq_id=None,
                    )
                    created = True

                return JsonResponse(
                    {
                        "status": "success",
                        "message": (
                            "Requisition saved."
                            if created
                            else "Requisition updated."
                        ),
                        "saved": True,
                        "req_id": obj.id,
                        "amount": float(amount),
                    }
                )

            # ---------- 2b. Store Approval Action -------------------------
            if action == "store_approve":
                project_id = data.get("project_id")
                employee_id = _map_employee_by_project(
                    project_id, data.get("employee_id")
                )

                qs = RestRequisition.objects.filter(
                    requisition_date=req_date,
                    approv_store="pending",
                )
                if project_id:
                    qs = qs.filter(project_name_id=project_id)
                if employee_id:
                    qs = qs.filter(employee_name_id=employee_id)

                updated = qs.update(approv_store="approved")
                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"{updated} item(s) store-approved.",
                        "updated": updated,
                    }
                )

            # ---------- 2c. Purchase Approval Action + Inventory Sync ------
            if action == "purchase_approve":
                project_id = data.get("project_id")
                employee_id = _map_employee_by_project(
                    project_id, data.get("employee_id")
                )

                qs = RestRequisition.objects.filter(
                    requisition_date=req_date,
                    approv_purch_status="pending",
                )
                if project_id:
                    qs = qs.filter(project_name_id=project_id)
                if employee_id:
                    qs = qs.filter(employee_name_id=employee_id)

                with transaction.atomic():
                    approved_items = list(qs)
                    updated = qs.update(
                        approv_purch_status="approved",
                        purch_date=req_date,
                    )

                    # Sync to RestInventories using RestaurantSupplier FK lookup
                    if "RestInventories" in globals():
                        for req_item in approved_items:
                            inv_vendor = None
                            if (
                                req_item.vendor_name
                                and "RestaurantSupplier" in globals()
                            ):
                                inv_vendor = RestaurantSupplier.objects.filter(
                                    rest_supplier_name__iexact=req_item.vendor_name.rest_supplier_name
                                ).first()

                            RestInventories.objects.update_or_create(
                                requi_id=req_item.id,
                                defaults={
                                    "project_name": req_item.project_name,
                                    "employee_name": req_item.employee_name,
                                    "item_name": req_item.item_name,
                                    "vendor_name": inv_vendor,
                                    "unit": req_item.unit or "",
                                    "qty": int(req_item.qty or 0),
                                    "rate": req_item.rate or Decimal("0.00"),
                                    "amount": req_item.amount
                                    or Decimal("0.00"),
                                    "remark": req_item.remark or "",
                                    "requisition_date": req_item.requisition_date,
                                    "purch_date": req_date,
                                },
                            )

                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"{updated} item(s) purchase-approved & synced to inventory.",
                        "updated": updated,
                    }
                )

            # ---------- 2d. POS Items Direct Purchase Save ----------------
            if "items" in data:
                items = data.get("items", [])
                supplier_name = data.get("supplier_name")
                project_id = data.get("project_id")
                employee_id = _map_employee_by_project(
                    project_id, data.get("employee_id")
                )
                purchase_date = req_date

                # Separate instances for different vendor tables
                jewel_vendor = _get_jewel_vendor_instance(supplier_name)
                inv_vendor = _get_inventory_vendor_instance(supplier_name)

                employee_instance = None
                if employee_id and "RestaurantEmployee" in globals():
                    employee_instance = RestaurantEmployee.objects.filter(
                        id=employee_id
                    ).first()

                project_instance = None
                if project_id and "ProjectFirstLevelName" in globals():
                    project_instance = ProjectFirstLevelName.objects.filter(
                        id=project_id
                    ).first()

                with transaction.atomic():
                    for item in items:
                        item_id = item.get("item_id")
                        qty = Decimal(str(item.get("qty", 0)))
                        rate = Decimal(str(item.get("rate", 0)))
                        amount = qty * rate

                        item_obj = (
                            RestaurantItem.objects.filter(id=item_id).first()
                            if "RestaurantItem" in globals()
                            else None
                        )

                        # 1. Insert into RestRequisition (using RestaurantJewelSupplier)
                        req_obj = RestRequisition.objects.create(
                            requisition_date=purchase_date,
                            project_name_id=project_id if project_id else None,
                            employee_name_id=(
                                employee_id if employee_id else None
                            ),
                            item_name=item_obj,
                            vendor_name=jewel_vendor,
                            qty=qty,
                            rate=rate,
                            amount=amount,
                            approv_store="approved",
                            approv_purch_status="approved",
                            purch_date=purchase_date,
                            calc_mode="unit",
                        )

                        # 2. Sync to RestInventories (using RestaurantSupplier)
                        if "RestInventories" in globals():
                            RestInventories.objects.create(
                                requi_id=req_obj.id,
                                project_name_id=(
                                    project_id if project_id else None
                                ),
                                employee_name=employee_instance,
                                item_name=item_obj,
                                vendor_name=inv_vendor,
                                qty=int(qty),
                                rate=rate,
                                amount=amount,
                                purch_date=purchase_date,
                            )

                return JsonResponse(
                    {"status": "success", "message": "Saved successfully!"}
                )

            return JsonResponse(
                {"status": "error", "message": "Unknown action."}, status=400
            )

        except Exception as e:
            logger.error(f"Error in requisition view: {str(e)}")
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )

    # ------------------------------------------------------------------
    # 3. STANDARD PAGE RENDER (GET)
    # ------------------------------------------------------------------
    project_id_filter = request.GET.get("project")
    employee_id_filter = _map_employee_by_project(
        project_id_filter, request.GET.get("employee")
    )

    filters = Q(
        return_requisition__isnull=True,
        requi_uniq_id__isnull=True,
    )

    if project_id_filter:
        filters &= Q(project_name_id=project_id_filter)
    if employee_id_filter:
        filters &= Q(employee_name_id=employee_id_filter)

    requisitions = (
        RestRequisition.objects.filter(filters)
        .select_related(
            "project_name", "employee_name", "item_name", "vendor_name"
        )
        .order_by("-id")
    )

    flat_data = []
    for req in requisitions:
        flat_data.append(
            {
                "id": req.id,
                "requisition_date": req.requisition_date,
                "project_name": getattr(
                    req.project_name,
                    "project_first_name",
                    str(req.project_name or "N/A"),
                ),
                "project_id": req.project_name_id,
                "employee_name": getattr(
                    req.employee_name,
                    "rda_emp_name",
                    str(req.employee_name or "N/A"),
                ),
                "item_name": getattr(
                    req.item_name,
                    "rest_item_name",
                    str(req.item_name or "N/A"),
                ),
                "unit": req.unit or "",
                "vendor_name": (
                    req.vendor_name.rest_supplier_name
                    if getattr(req, "vendor_name", None)
                    else ""
                ),
                "total_qty": float(req.qty or 0),
                "rate": float(req.rate or 0),
                "total_amount": float(req.amount or 0),
                "store_status": str(req.approv_store or "pending")
                .lower()
                .strip(),
                "purch_status": str(req.approv_purch_status or "pending")
                .lower()
                .strip(),
                "calc_mode": req.calc_mode or "normal",
            }
        )

    projects_qs = (
        ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen",
            ]
        )
        if "ProjectFirstLevelName" in globals()
        else []
    )
    items_qs = (
        RestaurantItem.objects.all().order_by("rest_item_name")
        if "RestaurantItem" in globals()
        else []
    )

    context = {
        "grouped_data": flat_data,
        "projects_firts": projects_qs,
        "projects_first": projects_qs,
        "employees": (
            RestaurantEmployee.objects.all()
            if "RestaurantEmployee" in globals()
            else []
        ),
        "items": items_qs,
        "suppliers": suppliers,
        "today_date": date.today().strftime("%Y-%m-%d"),
    }

    return render(
        request, "restaurant/requisitions/requisition_list_public.html", context
    )
    
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import RestRequisition

@csrf_protect
@require_POST
def update_inline_requisition(request):
    try:
        data = json.loads(request.body)
        record_id = data.get('id')
        field_name = data.get('field')
        value = data.get('value')

        # Find the specific record row id wise
        requisition = RestRequisition.objects.get(id=record_id)

        # Map frontend changes to model attributes
        if field_name == 'vendor_name':
            requisition.vendor_name = value
        elif field_name == 'qty':
            requisition.qty = float(value) if value else 0.0
        elif field_name == 'rate':
            requisition.rate = float(value) if value else 0.0
        elif field_name == 'approv_purch_status':
            requisition.approv_purch_status = value
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid field targeted'}, status=400)

        # Triggers your custom model save logic (amount = qty * rate - discount)
        requisition.save()
        
        return JsonResponse({'status': 'success', 'message': 'Row updated successfully!'})

    except RestRequisition.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        
    
# ok code bello ----


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import RestaurantPublicExpense
from .forms import RestaurantPublicExpenseForm

@login_required
def restaurant_expense_account_list(request):
    expenses = RestaurantPublicExpense.objects.all().order_by('-id')

    return render(request,
                  'restaurant/requisitions/restaurant_expense_account_list.html',
                  {'expenses': expenses})
                  
                  
                  
# List
def restaurant_expense_public_list(request):
    expenses = RestaurantPublicExpense.objects.all().order_by('-id')

    return render(request,
                  'restaurant/requisitions/restaurant_expense_public_list.html',
                  {'expenses': expenses})



from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import RestaurantPublicExpenseForm
from .models import RestaurantKitchenLedger


@login_required
@transaction.atomic
def add_restaurant_expense_public(request):
    if request.method == 'POST':
        form = RestaurantPublicExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save()

            # Project -> Employee Mapping
            employee_map = {
                36: 24,   # Project ID 36 -> Employee ID 24
                60: 54,   # Project ID 60 -> Employee ID 54
            }

            employee_id = employee_map.get(expense.project_name_id)

            if employee_id is None:
                messages.error(
                    request,
                    "No employee has been mapped for this project."
                )
                transaction.set_rollback(True)
                return render(
                    request,
                    'restaurant/requisitions/add_restaurant_expense_public.html',
                    {'form': form}
                )

            RestaurantKitchenLedger.objects.create(
                type='Expense',
                project=expense.project_name,
                employee_id=employee_id,
                item_name_id=190,          # Default Item ID
                debit=Decimal('0.00'),
                credit=expense.restu_expense_amount,
                tbl_id=str(expense.id),
            )

            messages.success(request, "Expense added successfully.")
            return redirect('restaurant_expense_public_list')

    else:
        form = RestaurantPublicExpenseForm()

    return render(
        request,
        'restaurant/requisitions/add_restaurant_expense_public.html',
        {'form': form}
    )
    
# Edit
def edit_restaurant_expense_public(request, pk):
    expense = get_object_or_404(RestaurantPublicExpense, pk=pk)

    if request.method == 'POST':
        form = RestaurantPublicExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated successfully.")
            return redirect('restaurant_expense_public_list')
    else:
        form = RestaurantPublicExpenseForm(instance=expense)

    return render(request,
                  'restaurant/requisitions/edit_restaurant_expense_public.html',
                  {'form': form})


# Delete
def delete_restaurant_expense_public(request, pk):
    expense = get_object_or_404(RestaurantPublicExpense, pk=pk)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect('restaurant_expense_public_list')

    return render(request,
                  'restaurant/requisitions/delete_restaurant_expense_public.html',
                  {'expense': expense})
                  
                  
                  


def restu_requisition_by_fallback_public(request, project_id):
    # Public access: Displays the list table filtered by project_id
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Get filters from GET parameters
    requisition_date_str = request.GET.get('requisition_date')
    vendor_names_str = request.GET.get('vendor_name', '')  # comma separated vendors

    # Base queryset: requi_uniq_id null and approv_status NOT approved
    requisitions = RestRequisition.objects.filter(
        project_name=project,
        requi_uniq_id__isnull=True,
    ).exclude(approv_status='approved')

    # Filter by requisition_date if provided and valid
    if requisition_date_str:
        try:
            requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date=requisition_date)
        except ValueError:
            pass

    # Filter by vendor_name(s) if provided
    if vendor_names_str:
        vendor_names = [v.strip() for v in vendor_names_str.split(',') if v.strip()]
        if vendor_names:
            requisitions = requisitions.filter(vendor_name__in=vendor_names)

    # Extract unique vendor names for display/filter UI
    vendors = list(set(r.vendor_name for r in requisitions if r.vendor_name))

    context = {
        'project': project,
        'requisitions': requisitions,
        'vendors': vendors,
        'approv_note': 'Not Approved',
        'requisition_date': requisition_date_str or '',
        'vendor_name': vendor_names_str or '',
    }
    return render(request, 'restaurant/requisitions/requisition_by_project_public.html', context)


def restau_requisition_edit_public(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)

    if request.method == 'POST':
        # Create a mutable copy of the POST data so we can fix missing fields
        post_data = request.POST.copy()
        
        # 🛠️ FIX: If 'type' is missing or empty in the HTML submission, 
        # look at the existing database value. If that is empty too, fallback to 'Supplier'
        if not post_data.get('type'):
            post_data['type'] = requisition.type if requisition.type else 'Supplier'

        # Pass the patched data into your form
        form = RestRequisitionForm(post_data, instance=requisition)
        
        if form.is_valid():
            updated = form.save(commit=False)
            updated.save()
            messages.success(request, 'Requisition updated successfully.')

            if updated.requi_uniq_id:
                return redirect('restau_requisition_list_public', requi_id=updated.requi_uniq_id)
            else:
                project_id = updated.project_name.id  
                requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
                vendor_name = updated.vendor_name or ''  
            
                fallback_url = reverse('restu_requisition_by_fallback_public', args=[project_id])
                return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_name}')
        else:
            # Trap and display any remaining validation errors to your user interface
            print("Form errors occurred:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in field '{field}': {error}")
    else:
        form = RestRequisitionForm(instance=requisition)

    context = {
        'form': form,
        'requisition': requisition,
        'projects_firts': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'employee_names': RestaurantEmployee.objects.all(), 
        'requisition_list': RestaurantItem.objects.all(),
        'supplier_list': RestaurantSupplier.objects.all(),
    }
    return render(request, 'restaurant/requisitions/requisition_public_edit.html', context)
    
    



def restau_requisition_delete_public(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('restau_requisition_list_public')
    return render(request, 'restaurant/requisitions/requisition_delete_public.html', {'requisition': requisition})
 


## store ##

# import logging
# from django.shortcuts import render, redirect
# from django.views.decorators.http import require_POST
# from django.contrib import messages
# from django.utils.http import urlencode
# from .models import RestRequisition, RestaurantSupplier, ProjectFirstLevelName, RestaurantEmployee

# logger = logging.getLogger(__name__)

# def restau_requisition_list_public_store(request):
#     suppliers = RestaurantSupplier.objects.all()

#     # Base Public Filter Matrix: target row-by-row item entries pending store verification
#     queryset = RestRequisition.objects.filter(
#         return_requisition__isnull=True,
#         approv_store='pending',            # Displays only rows where store status is pending
#         requi_uniq_id__isnull=True,
#     ).select_related('project_name', 'employee_name', 'item_name').order_by('-id')

#     # Read active GET parameter values directly from the browser incoming URL path
#     project_id = request.GET.get('project')
#     employee_id = request.GET.get('employee')

#     # Apply row-by-row database filters if keys are found in parameters
#     if project_id:
#         queryset = queryset.filter(project_name_id=project_id)
#     if employee_id:
#         queryset = queryset.filter(employee_name_id=employee_id)

#     context = {
#         'requisitions': queryset,          # Flattened individual database rows passed directly
#         'projects_firts': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         ),
#         'employees': RestaurantEmployee.objects.exclude(rda_emp_type__iexact='admin'),
#         'suppliers': suppliers,
#         'current_project': project_id or '',
#         'current_employee': employee_id or '',
#     }

#     return render(request, 'restaurant/requisitions/requisition_list_public_store.html', context)


# @require_POST
# def restau_requisition_bulk_approve(request):
#     # Extracts the array of individual checked Requisition item IDs from the form checkboxes
#     requisition_ids = request.POST.getlist('requisition_ids')
    
#     # Track parameter filter states to redirect cleanly back to user's precise workspace layout view
#     project_id = request.POST.get('current_project', '')
#     employee_id = request.POST.get('current_employee', '')

#     if requisition_ids:
#         # TARGETED DATABASE UPDATE: Update approv_store directly on individual records
#         updated_count = RestRequisition.objects.filter(
#             id__in=requisition_ids,
#             approv_store='pending'
#         ).update(approv_store='approved')  # Updates matching records to choices-defined lowercased state
        
#         messages.success(request, f"Successfully approved {updated_count} selected requisition items in store configuration.")
#     else:
#         messages.warning(request, "No individual row entries were selected.")

#     # Reconstruct exact active parameters query string matching initial entry layout
#     redirect_url = redirect('restau_requisition_list_public_store')
#     query_params = {}
#     if project_id:
#         query_params['project'] = project_id
#     if employee_id:
#         query_params['employee'] = employee_id
        
#     if query_params:
#         redirect_url['Location'] += '?' + urlencode(query_params)
        
#     return redirect_url
    



## ---------------

import json
from decimal import Decimal
import logging
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.http import urlencode
from django.http import JsonResponse
from .models import RestRequisition, RestaurantSupplier, ProjectFirstLevelName

logger = logging.getLogger(__name__)

def restau_requisition_list_public_store(request):
    suppliers = RestaurantSupplier.objects.all()

    # --- 1. HANDLE INLINE CELL & STATUS UPDATES (AJAX POST) ---
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            action = data.get("action")
            
            if action == "update_field":
                row_id = data.get("id")
                field = data.get("field")
                value = data.get("value")
                
                req_item = RestRequisition.objects.get(id=row_id)
                
                if field == "qty":
                    req_item.qty = Decimal(str(value or 0))
                elif field == "rate":
                    req_item.rate = Decimal(str(value or 0))
                elif field == "vendor_name":
                    req_item.vendor_name = value
                elif field == "approv_store":
                    req_item.approv_store = value  # Updates status directly when pending clicked
                
                req_item.save()
                return JsonResponse({"status": "success", "message": f"Row #{row_id} updated successfully."})
                
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # --- 2. STANDARD FILTERED QUERY RENDER ---
    queryset = RestRequisition.objects.filter(
        return_requisition__isnull=True,
        approv_store='pending',
        requi_uniq_id__isnull=True,
    ).select_related('project_name', 'employee_name', 'item_name').order_by('-id')

    project_id = request.GET.get('project')
    employee_id = request.GET.get('employee')

    if project_id:
        queryset = queryset.filter(project_name_id=project_id)
    if employee_id:
        queryset = queryset.filter(employee_name_id=employee_id)

    projects_firts = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    context = {
        'requisitions': queryset,
        'projects_firts': projects_firts,
        'suppliers': suppliers,
        'current_project': project_id or '',
        'current_employee': employee_id or '',
    }
    return render(request, 'restaurant/requisitions/requisition_list_public_store.html', context)


@require_POST
def restau_requisition_bulk_approve(request):
    requisition_ids = request.POST.getlist('requisition_ids')
    project_id = request.POST.get('current_project', '')
    employee_id = request.POST.get('current_employee', '')

    if requisition_ids:
        updated_count = RestRequisition.objects.filter(
            id__in=requisition_ids,
            approv_store='pending'
        ).update(approv_store='approved')
        
        messages.success(request, f"Successfully approved {updated_count} selected requisition items.")
    else:
        messages.warning(request, "No items were selected.")

    redirect_url = redirect('restau_requisition_list_public_store')
    query_params = {}
    if project_id: query_params['project'] = project_id
    if employee_id: query_params['employee'] = employee_id
        
    if query_params:
        redirect_url['Location'] += '?' + urlencode(query_params)
        
    return redirect_url
    
    



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import json

# Keep your original view as is, just ensure it handles the template rendering
def restu_requisition_by_fallback_public_store(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    requisition_date_str = request.GET.get('requisition_date')
    vendor_names_str = request.GET.get('vendor_name', '')

    requisitions = RestRequisition.objects.filter(
        project_name=project,
        requi_uniq_id__isnull=True,
    ).exclude(approv_status='approved')

    if requisition_date_str:
        try:
            requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date=requisition_date)
        except ValueError:
            pass

    if vendor_names_str:
        vendor_names = [v.strip() for v in vendor_names_str.split(',') if v.strip()]
        if vendor_names:
            requisitions = requisitions.filter(vendor_name__in=vendor_names)

    vendors = list(set(r.vendor_name for r in requisitions if r.vendor_name))

    context = {
        'project': project,
        'requisitions': requisitions,
        'vendors': vendors,
        'approv_note': 'Not Approved',
        'requisition_date': requisition_date_str or '',
        'vendor_name': vendor_names_str or '',
    }
    return render(request, 'restaurant/requisitions/requisition_by_project_public_store.html', context)


# NEW ENDPOINT: Add this view to handle the async status update safely
@require_POST
def update_purch_status_ajax(request):
    try:
        data = json.loads(request.body)
        requisition_id = data.get('id')
        new_status = data.get('status')
        
        # Validation checks
        if new_status not in ['pending', 'approved', 'rejected']:
            return JsonResponse({'success': False, 'error': 'Invalid status choice.'}, status=400)
            
        requisition = get_object_or_404(RestRequisition, pk=requisition_id)
        requisition.approv_purch_status = new_status
        requisition.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
        

def restau_requisition_edit_public_store(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)

    if request.method == 'POST':
        # Create a mutable copy of the POST data so we can fix missing fields
        post_data = request.POST.copy()
        
        # 🛠️ FIX: If 'type' is missing or empty in the HTML submission, 
        # look at the existing database value. If that is empty too, fallback to 'Supplier'
        if not post_data.get('type'):
            post_data['type'] = requisition.type if requisition.type else 'Supplier'

        # Pass the patched data into your form
        form = RestRequisitionForm(post_data, instance=requisition)
        
        if form.is_valid():
            updated = form.save(commit=False)
            updated.save()
            messages.success(request, 'Requisition updated successfully.')

            if updated.requi_uniq_id:
                return redirect('restau_requisition_list_public_store', requi_id=updated.requi_uniq_id)
            else:
                project_id = updated.project_name.id  
                requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
                vendor_name = updated.vendor_name or ''  
            
                fallback_url = reverse('restu_requisition_by_fallback_public_store', args=[project_id])
                return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_name}')
        else:
            # Trap and display any remaining validation errors to your user interface
            print("Form errors occurred:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in field '{field}': {error}")
    else:
        form = RestRequisitionForm(instance=requisition)

    context = {
        'form': form,
        'requisition': requisition,
        'projects_firts': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'employee_names': RestaurantEmployee.objects.all(), 
        'requisition_list': RestaurantItem.objects.all(),
        'supplier_list': RestaurantSupplier.objects.all(),
    }
    return render(request, 'restaurant/requisitions/requisition_public_edit_store.html', context)
    
    



def restau_requisition_delete_public_store(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('restau_requisition_list_public')
    return render(request, 'restaurant/requisitions/requisition_delete_public_store.html', {'requisition': requisition})
    
    
    
### LEAVE ###

@login_required
def rest_expense_list(request):
    expenses = RestExpense.objects.all()
    return render(request, 'restaurant/expenses/expense_list.html', {'expenses': expenses})



@login_required
def rest_expense_add(request):
    if request.method == 'POST':
        form = RestExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_expense_list')
    else:
        form = RestExpenseForm()

    return render(request, 'restaurant/expenses/expense_add.html', {'form': form})


@login_required
def rest_expense_edit(request, pk):
    expense = get_object_or_404(RestExpense, pk=pk)

    if request.method == 'POST':
        form = RestExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('rest_expense_list')
    else:
        form = RestExpenseForm(instance=expense)

    return render(request, 'restaurant/expenses/expense_edit.html', {'form': form})



@login_required
def rest_expense_delete(request, pk):
    expense = get_object_or_404(RestExpense, pk=pk)

    if request.method == 'POST':
        expense.delete()
        return redirect('rest_expense_list')

    return render(request, 'restaurant/expenses/expense_delete.html', {'expense': expense})
    
    
    

@login_required
def rest_purchase_cost_list(request):
    purchases = RestPurchaseCost.objects.all()
    return render(request, 'restaurant/expenses/purchase_cost_list.html', {'purchases': purchases})



@login_required
def rest_purchase_cost_add(request):
    if request.method == 'POST':
        form = RestPurchaseCostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_purchase_cost_list')
    else:
        form = RestPurchaseCostForm()

    return render(request, 'restaurant/expenses/purchase_cost_add.html', {'form': form})


@login_required
def rest_purchase_cost_edit(request, pk):
    purchases = get_object_or_404(RestPurchaseCost, pk=pk)

    if request.method == 'POST':
        form = RestPurchaseCostForm(request.POST, instance=purchases)
        if form.is_valid():
            form.save()
            return redirect('rest_purchase_cost_list')
    else:
        form = RestPurchaseCostForm(instance=purchases)

    return render(request, 'restaurant/expenses/purchase_cost_edit.html', {'form': form})



@login_required
def rest_purchase_cost_delete(request, pk):
    purchases = get_object_or_404(RestPurchaseCost, pk=pk)

    if request.method == 'POST':
        purchases.delete()
        return redirect('rest_purchase_cost_list')

    return render(request, 'restaurant/expenses/purchase_cost_delete.html', {'purchases': purchases})
    
    
    
from collections import defaultdict

@login_required
def restaurant_grouped_requisitions(request):

    all_requisitions = RestExpenseRequisition.objects.all().order_by(
        '-requisition_date',
        'project_name__project_first_name'
    )

    grouped_data = defaultdict(lambda: defaultdict(dict))

    for req in all_requisitions:

        date_str = req.requisition_date.strftime('%Y-%m-%d') if req.requisition_date else 'Unknown'
        project_title = req.project_name.project_first_name
        project_id = req.project_name.id

        if 'id' not in grouped_data[date_str][project_title]:
            grouped_data[date_str][project_title] = {
                'id': project_id,
                'requisitions': [],
                'total_amount': 0,
                'status_list': []
            }

        grouped_data[date_str][project_title]['requisitions'].append(req)
        grouped_data[date_str][project_title]['total_amount'] += req.amount or 0
        grouped_data[date_str][project_title]['status_list'].append(req.approv_status)

    # 🔥 Calculate final status per group
    for date in grouped_data:
        for project in grouped_data[date]:
            statuses = grouped_data[date][project]['status_list']

            if all(status == 'approved' for status in statuses):
                final_status = 'approved'
            elif any(status == 'rejected' for status in statuses):
                final_status = 'rejected'
            else:
                final_status = 'pending'

            grouped_data[date][project]['final_status'] = final_status

    grouped_data = {
        date: dict(projects)
        for date, projects in sorted(grouped_data.items(), reverse=True)
    }

    return render(request, 'restaurant/expenses/grouped_requisitions.html', {
        'grouped_data': grouped_data
    })
    
    


# @login_required
# def restaurant_expense_requisition_add(request):
#     """
#     Handles both AJAX JSON submissions and standard form submissions
#     for adding restaurant expense requisitions.
#     """
    
#     # -----------------------------
#     # AJAX JSON POST submission
#     # -----------------------------
#     if request.method == "POST" and request.content_type == "application/json":
#         try:
#             data = json.loads(request.body)
#             items = data.get('data', [])
#             employee_id = data.get('employee_id')
#             type_value = data.get('type')
#             remark = data.get('remark', '')
#             head_of_account_id = data.get('head_of_account')
#             cash_type_id = data.get('cash_type')
#             cheque_id = data.get('cheque_number', '')
#             expense_date = data.get('expense_date')

#             employee = RestaurantEmployee.objects.get(id=employee_id)

#             # Create each expense item
#             for item in items:
#                 project_id = item.get('project')
#                 item_id = item.get('item')
#                 qty = item.get('qty')
#                 rate = item.get('rate')
#                 descript = item.get('description', '')

#                 if not all([project_id, item_id, qty, rate]):
#                     return JsonResponse({
#                         'status': 'error',
#                         'message': 'Missing required fields in one or more items.'
#                     })

#                 project = ProjectFirstLevelName.objects.get(id=project_id)
#                 head_name = RestHeadOfAccount.objects.get(id=head_of_account_id)
#                 cashtype_name = CashRestType.objects.get(id=cash_type_id)
#                 head_item = RestExpense.objects.get(id=item_id)
#                 amount = float(qty) * float(rate)

#                 # Create the expense requisition
#                 requisition = RestExpenseRequisition.objects.create(
#                     type=type_value,
#                     project_name=project,
#                     cash_type=cashtype_name,
#                     head_of_account=head_name,
#                     employee_name=employee,
#                     item_name=head_item,
#                     qty=qty,
#                     rate=rate,
#                     amount=amount,
#                     descript=descript,
#                     remark=remark,
#                     approv_status='pending',
#                     approv_note='',
#                     requisition_date=expense_date
#                 )

#                 # Handle cheque if selected
#                 if cheque_id:
#                     try:
#                         cheque = RestMainCheque.objects.get(id=cheque_id)
#                         requisition.cheque_number = cheque.cheque_number
#                         requisition.save()

#                         # Update cheque info
#                         cheque.status = 'used'
#                         cheque.remarks = f"Used in Restaurant Expense Requisition ID {requisition.id}"
#                         cheque.issue_date = timezone.now().date()
#                         cheque.amount = amount
#                         cheque.save()
#                     except RestMainCheque.DoesNotExist:
#                         return JsonResponse({'status': 'error', 'message': 'Cheque not found.'})

#             return JsonResponse({'status': 'success', 'message': 'Expense requisitions saved successfully.'})

#         except RestaurantEmployee.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Employee not found.'})
#         except ProjectFirstLevelName.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Project not found.'})
#         except RestHeadOfAccount.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Head of Account not found.'})
#         except RestExpense.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Expense item not found.'})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'})

#     # -----------------------------
#     # Standard form POST or GET
#     # -----------------------------
#     else:
#         form = RestExpenseRequisitionForm(request.POST or None)

#         if request.method == "POST" and form.is_valid():
#             requisition = form.save(commit=False)
#             cheque_id = request.POST.get('cheque_number')

#             if cheque_id:
#                 try:
#                     cheque = RestMainCheque.objects.get(id=cheque_id)
#                     requisition.cheque_number = cheque.cheque_number
#                     requisition.save()

#                     # Update cheque info
#                     cheque.status = 'used'
#                     cheque.remarks = requisition.remark or ''
#                     cheque.issue_date = requisition.requisition_date
#                     cheque.amount = requisition.amount
#                     cheque.save()

#                 except RestMainCheque.DoesNotExist:
#                     print("Cheque not found")
#             else:
#                 requisition.save()

#             return redirect('restaurant_grouped_requisitions')

#         # GET request — render form
#         try:
#             employee = Employee.objects.get(email=request.user.email)
#         except RestaurantEmployee.DoesNotExist:
#             employee = None  # handle gracefully in template if needed

#         headExpenses = RestExpense.objects.all()
#         cashTypes = CashRestType.objects.all()
#         project_lists = ProjectFirstLevelName.objects.all()
#         headOfAccounts = RestHeadOfAccount.objects.all()
#         restEmps = RestaurantEmployee.objects.all()

#         return render(request, 'restaurant/expenses/expense_requisition_add.html', {
#             'form': form,
#             'employee_id': employee.id if employee else None,
#             'employee_name': employee.employee_name if employee else '',
#             'headExpenses': headExpenses,
#             'project_lists': project_lists,
#             'type': 'Expense',
#             'cashTypes': cashTypes,
#             'restEmps': restEmps,
#             'headOfAccounts': headOfAccounts,
#         })
        


@login_required
def restaurant_expense_requisition_add(request):
    """
    Handles both AJAX JSON submissions and standard form submissions
    for adding restaurant expense requisitions.
    """
    
    # -----------------------------
    # AJAX JSON POST submission
    # -----------------------------
    if request.method == "POST" and request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            items = data.get('data', [])
            employee_id = data.get('employee_id')
            type_value = data.get('type')
            remark = data.get('remark', '')
            head_of_account_id = data.get('head_of_account')
            cash_type_id = data.get('cash_type')
            cheque_id = data.get('cheque_number', '')
            expense_date = data.get('expense_date')

            # ✅ FIXED: use Employee instead of RestaurantEmployee
            employee = Employee.objects.get(id=employee_id)

            # Create each expense item
            for item in items:
                project_id = item.get('project')
                item_id = item.get('item')
                qty = item.get('qty')
                rate = item.get('rate')
                descript = item.get('description', '')

                if not all([project_id, item_id, qty, rate]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required fields in one or more items.'
                    })

                project = ProjectFirstLevelName.objects.get(id=project_id)
                head_name = RestHeadOfAccount.objects.get(id=head_of_account_id)
                cashtype_name = CashRestType.objects.get(id=cash_type_id)
                head_item = RestExpense.objects.get(id=item_id)
                amount = float(qty) * float(rate)

                requisition = RestExpenseRequisition.objects.create(
                    type=type_value,
                    project_name=project,
                    cash_type=cashtype_name,
                    head_of_account=head_name,
                    employee_name=employee,   # ✅ now Employee
                    item_name=head_item,
                    qty=qty,
                    rate=rate,
                    amount=amount,
                    descript=descript,
                    remark=remark,
                    approv_status='pending',
                    approv_note='',
                    requisition_date=expense_date
                )

                # Handle cheque if selected
                if cheque_id:
                    try:
                        cheque = RestMainCheque.objects.get(id=cheque_id)
                        requisition.cheque_number = cheque.cheque_number
                        requisition.save()

                        cheque.status = 'used'
                        cheque.remarks = f"Used in Restaurant Expense Requisition ID {requisition.id}"
                        cheque.issue_date = timezone.now().date()
                        cheque.amount = amount
                        cheque.save()

                    except RestMainCheque.DoesNotExist:
                        return JsonResponse({'status': 'error', 'message': 'Cheque not found.'})

            return JsonResponse({'status': 'success', 'message': 'Expense requisitions saved successfully.'})

        # ✅ FIXED exception
        except Employee.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Employee not found.'})

        except ProjectFirstLevelName.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Project not found.'})
        except RestHeadOfAccount.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Head of Account not found.'})
        except RestExpense.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Expense item not found.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'})

    # -----------------------------
    # Standard form POST or GET
    # -----------------------------
    else:
        form = RestExpenseRequisitionForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            requisition = form.save(commit=False)
            cheque_id = request.POST.get('cheque_number')

            # ✅ AUTO SET logged-in employee
            try:
                requisition.employee_name = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                requisition.employee_name = None

            if cheque_id:
                try:
                    cheque = RestMainCheque.objects.get(id=cheque_id)
                    requisition.cheque_number = cheque.cheque_number
                    requisition.save()

                    cheque.status = 'used'
                    cheque.remarks = requisition.remark or ''
                    cheque.issue_date = requisition.requisition_date
                    cheque.amount = requisition.amount
                    cheque.save()

                except RestMainCheque.DoesNotExist:
                    print("Cheque not found")
            else:
                requisition.save()

            return redirect('restaurant_grouped_requisitions')

        # GET request — render form
        try:
            # ✅ FIXED: use user relation (BEST)
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            employee = None

        headExpenses = RestExpense.objects.all()
        cashTypes = CashRestType.objects.all()
        project_lists = ProjectFirstLevelName.objects.all()
        headOfAccounts = RestHeadOfAccount.objects.all()

        # ❌ OLD: RestaurantEmployee
        # restEmps = RestaurantEmployee.objects.all()

        # ✅ NEW:
        employees = Employee.objects.filter(active_status=True)

        return render(request, 'restaurant/expenses/expense_requisition_add.html', {
            'form': form,
            'employee_id': employee.id if employee else None,
            'employee_name': employee.employee_name if employee else '',
            'headExpenses': headExpenses,
            #'project_lists': project_lists,
            'project_lists': ProjectFirstLevelName.objects.filter(
                project_first_name__in=[
                    "The Galleria Restauent Cafe",
                    "The Galleria Live Kitchen"
                ]
            ),
            'type': 'Expense',
            'cashTypes': cashTypes,
            'employees': employees,   # ✅ updated
            'headOfAccounts': headOfAccounts,
        })



@login_required
def restaurant_requisition_details(request, date_str, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    requisitions = RestExpenseRequisition.objects.filter(
        requisition_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        project_name=project
    )

    return render(request, 'restaurant/expenses/requisition_details.html', {
        'requisitions': requisitions,
        'date_str': date_str,             
        'project_id': project.id,          
        'project': project
    })


from django.utils.dateformat import DateFormat

@login_required
def rest_edit_expense_requisition(request, pk):
    expense = get_object_or_404(RestExpenseRequisition, pk=pk)

    if request.method == 'POST':
        form = RestExpenseRequisitionForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save(commit=False)

            # Convert string to date
            requisition_date_str = request.POST.get('requisition_date', '')
            if requisition_date_str:
                expense.requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()

            # Manually update descript and remark
            expense.descript = request.POST.get('descript', '')
            expense.remark = request.POST.get('remark', '')

            expense.save()

            date_str = DateFormat(expense.requisition_date).format('Y-m-d')
            project_id = expense.project_name.id
            return redirect('restaurant_requisition_details', date_str=date_str, project_id=project_id)
        else:
            return render(request, 'restaurant/expenses/expense_requisition_edit.html', {
                'form': form,
                'expense': expense,
                'errors': form.errors,
            })
    else:
        form = RestExpenseRequisitionForm(instance=expense)

    return render(request, 'restaurant/expenses/expense_requisition_edit.html', {
        'form': form,
        'expense': expense,
    })
    




# from django.db import transaction
# from django.db.models import Sum
# from django.http import JsonResponse
# from django.utils.timezone import now
# from django.utils.dateparse import parse_date
# import traceback



# @login_required
# def expense_requisition_confirmation(request):
#     requisition_date = request.GET.get('requisition_date')

#     vouchers = RestExpenseRequisition.objects.none()
#     selected_project = None

#     # ---------------- FILTER ----------------
#     if requisition_date:
#         parsed_date = parse_date(requisition_date)

#         if parsed_date:
#             vouchers = (
#                 RestExpenseRequisition.objects
#                 .filter(requisition_date=parsed_date)
#                 .select_related('item_name', 'employee_name', 'project_name')
#                 .order_by('id')
#             )

#             if vouchers.exists():
#                 selected_project = vouchers.first().project_name

#     total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or 0

#     # ---------------- PROCESS ----------------
#     try:
#         with transaction.atomic():

#             approval_date = now().date()

#             for expense_req in vouchers:

#                 # Skip already processed
#                 if expense_req.ledger_add:
#                     continue

#                 # -------- VALIDATION --------
#                 if not expense_req.project_name:
#                     raise Exception(f"Missing project in Req ID {expense_req.id}")

#                 if not expense_req.head_of_account:
#                     raise Exception(f"Missing head_of_account in Req ID {expense_req.id}")

#                 if not expense_req.cash_type:
#                     raise Exception(f"Missing cash_type in Req ID {expense_req.id}")

#                 if not expense_req.item_name:
#                     raise Exception(f"Missing expense item in Req ID {expense_req.id}")

#                 # -------- GENERATE MR NO --------
#                 base_code = "MEX-"

#                 last = DebitRestVoucher.objects.filter(
#                     mr_or_bill_no__startswith=base_code
#                 ).order_by('-id').first()

#                 if last and last.mr_or_bill_no:
#                     try:
#                         last_number = int(last.mr_or_bill_no.split('-')[1])
#                         next_number = last_number + 1
#                     except:
#                         next_number = last.id + 1
#                 else:
#                     next_number = 1

#                 generated_code = f"{base_code}{next_number:05d}"

#                 while DebitRestVoucher.objects.filter(
#                     mr_or_bill_no=generated_code
#                 ).exists():
#                     next_number += 1
#                     generated_code = f"{base_code}{next_number:05d}"

#                 # -------- CREATE DEBIT VOUCHER --------
#                 debit_voucher = DebitRestVoucher.objects.create(
#                     type='Expense',
#                     expense=expense_req.item_name,
#                     bill_date=approval_date,
#                     project_name=expense_req.project_name,
#                     amount=expense_req.amount,
#                     particulars=expense_req.descript or '',
#                     date=approval_date,
#                     mr_or_bill_no=generated_code,
#                     head_of_account=expense_req.head_of_account,
#                     cash_type=expense_req.cash_type,
#                     cheque_number=expense_req.cheque_number or '',
#                     requi_id=expense_req.id,
#                     return_requisition='No',
#                     approval_dr_status=True,
#                     carrier='',
#                     create_dr=request.user.username,
#                     is_confirmed=True,
#                 )

#                 # -------- UPDATE CASH --------
#                 cash_type_obj = expense_req.cash_type

#                 if cash_type_obj:
#                     current_amount = cash_type_obj.type_amount or 0
#                     cash_type_obj.type_amount = current_amount - expense_req.amount
#                     cash_type_obj.type_note = f"Expense Req ID {expense_req.id} Confirmed"
#                     cash_type_obj.save()

#                 # -------- UPDATE CHEQUE --------
#                 cheque_number = expense_req.cheque_number

#                 if cheque_number:
#                     try:
#                         cheque = RestMainCheque.objects.get(
#                             cheque_number=cheque_number
#                         )
#                         cheque.status = 'used'
#                         cheque.remarks = expense_req.descript or ''
#                         cheque.issue_date = approval_date
#                         cheque.payee_name = (
#                             cash_type_obj.cash_type_name if cash_type_obj else ''
#                         )
#                         cheque.amount = expense_req.amount
#                         cheque.save()
#                     except RestMainCheque.DoesNotExist:
#                         pass  # ignore if cheque not found

#                 # -------- TRANSACTION HISTORY --------
#                 RestTransactionHistory.objects.create(
#                     project=expense_req.project_name,
#                     transaction_type='Expense',
#                     head_of_account=expense_req.head_of_account,
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     amount=expense_req.amount,
#                     date=approval_date,
#                     type_name='Expense_Payment',
#                     reference=generated_code,
#                     create_by=request.user.username,
#                     particulars=expense_req.descript or '',
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # -------- LEDGER ENTRY --------
#                 LedgerRestEntry.objects.create(
#                     project_name=expense_req.project_name,
#                     type='Expense',
#                     exp_name=expense_req.item_name,
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     head=expense_req.head_of_account,
#                     mr_or_bill_no=generated_code,
#                     date=approval_date,
#                     description=expense_req.descript or '',
#                     debit=expense_req.amount,
#                     credit=0,
#                     carrier='',
#                     loan_status='payment',
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # -------- UPDATE REQUISITION --------
#                 expense_req.ledger_add = True
#                 expense_req.approv_status = 'approved'
#                 expense_req.approval_date = approval_date

#                 expense_req.save(update_fields=[
#                     'ledger_add',
#                     'approv_status',
#                     'approval_date'
#                 ])

#     except Exception as e:
#         traceback.print_exc()

#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         })

#     # ---------------- RESPONSE ----------------
#     context = {
#         'selected_project': selected_project,
#         'vouchers': vouchers,
#         'print_time': now(),
#         'requisition_date': requisition_date,
#         'total_amount': total_amount,
#     }

#     return render(
#         request,
#         'restaurant/expenses/expense_requisition_confirmation.html',
#         context
#     )





# @login_required
# def rest_approve_expense_voucher(request, pk):
#     requisition_date = request.GET.get('requisition_date')

#     # First, get the current approved requisition (single record)
#     requisition = get_object_or_404(RestExpenseRequisition, pk=pk)
    
#     requi_expenseid = int(time.time())
#     # Approve the current requisition
#     requisition.approv_status = 'approved'
#     requisition.approv_note = 'Approved by admin'
#     requisition.requi_expense_id = requi_expenseid  # Save own pk here
#     requisition.save()

#     # Now update all rows with the same requisition_date and not approved yet
#     if requisition_date:
#         ExpenseRequisition.objects.filter(
#             requisition_date=requisition_date,
#             approv_status__in=['pending', 'rejected']
#         ).update(
#             approv_status='approved',
#             requi_expense_id=requi_expenseid,
#             approv_note='Approved by admin'
#         )

#     # Redirect back to confirmation page with requisition_date param to maintain context
#     redirect_url = f'{reverse("rest_expense_requisition_confirmation")}?requisition_date={requisition_date}'
#     return redirect(redirect_url)



@login_required
def rest_delete_expense_requisition(request, pk):
    voucher = get_object_or_404(RestExpenseRequisition, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        return redirect('restaurant_grouped_requisitions')
    return render(request, 'restaurant/expenses/delete_expense_requisition.html', {'voucher': voucher})
    
    
    

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
import traceback

@login_required
def rest_approve_selected_requisitions(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_reqs")

        if not selected_ids:
            messages.warning(request, "No items selected.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        try:
            with transaction.atomic():

                selected_reqs = RestExpenseRequisition.objects.filter(id__in=selected_ids)

                for expense_req in selected_reqs:

                    # ✅ Skip already processed
                    if expense_req.approv_status == "approved":
                        continue

                    # -------- VALIDATION --------
                    if not expense_req.project_name:
                        raise Exception(f"Missing project (Req ID {expense_req.id})")

                    if not expense_req.head_of_account:
                        raise Exception(f"Missing head_of_account (Req ID {expense_req.id})")

                    if not expense_req.cash_type:
                        raise Exception(f"Missing cash_type (Req ID {expense_req.id})")

                    if not expense_req.item_name:
                        raise Exception(f"Missing expense item (Req ID {expense_req.id})")

                    # -------- GENERATE MR NO --------
                    base_code = "MEX-"

                    last = DebitRestVoucher.objects.filter(
                        mr_or_bill_no__startswith=base_code
                    ).order_by("-id").first()

                    if last and last.mr_or_bill_no:
                        try:
                            last_num = int(last.mr_or_bill_no.split("-")[1])
                            next_id = last_num + 1
                        except:
                            next_id = last.id + 1
                    else:
                        next_id = 1

                    generated_code = f"{base_code}{next_id:05d}"

                    while DebitRestVoucher.objects.filter(
                        mr_or_bill_no=generated_code
                    ).exists():
                        next_id += 1
                        generated_code = f"{base_code}{next_id:05d}"

                    # -------- CREATE DEBIT VOUCHER --------
                    debit_voucher = DebitRestVoucher.objects.create(
                        type="Expense",
                        expense=expense_req.item_name,  # ✅ FK (correct)
                        empl_name=expense_req.employee_name.employee_name if expense_req.employee_name else "",
                        bill_date=expense_req.requisition_date,
                        project_name=expense_req.project_name,
                        amount=expense_req.amount,
                        particulars=expense_req.descript or "",
                        date=expense_req.requisition_date,
                        mr_or_bill_no=generated_code,
                        head_of_account=expense_req.head_of_account,
                        cash_type=expense_req.cash_type,
                        cheque_number=expense_req.cheque_number or "",
                        requi_id=expense_req.id,
                        return_requisition="No",
                        approval_dr_status=True,
                        carrier="",
                        create_dr=request.user.username,
                        is_confirmed=True,
                    )

                    # -------- UPDATE CASH --------
                    cash_type_obj = expense_req.cash_type

                    if cash_type_obj:
                        current_amount = cash_type_obj.type_amount or 0
                        cash_type_obj.type_amount = current_amount - expense_req.amount
                        cash_type_obj.type_note = f"Expense Req ID {expense_req.id} Approved"
                        cash_type_obj.save()

                    # -------- UPDATE CHEQUE --------
                    if expense_req.cheque_number:
                        try:
                            cheque = RestMainCheque.objects.get(
                                cheque_number=expense_req.cheque_number
                            )
                            cheque.status = "used"
                            cheque.remarks = expense_req.descript or ""
                            cheque.issue_date = expense_req.requisition_date
                            cheque.payee_name = (
                                cash_type_obj.cash_type_name if cash_type_obj else ""
                            )
                            cheque.amount = expense_req.amount
                            cheque.save()
                        except RestMainCheque.DoesNotExist:
                            print(f"Cheque {expense_req.cheque_number} not found")

                    # -------- TRANSACTION HISTORY --------
                    RestTransactionHistory.objects.create(
                        project=expense_req.project_name,
                        transaction_type="Expense",
                        head_of_account=expense_req.head_of_account,
                        cash_type=cash_type_obj,
                        cheque_number=expense_req.cheque_number,
                        amount=expense_req.amount,
                        date=expense_req.requisition_date,
                        type_name="Expense",
                        reference=generated_code,
                        create_by=request.user.username,
                        particulars=expense_req.descript or "",
                        tbl_id=str(debit_voucher.id),
                        tbl_name="Payment",
                    )

                    # -------- LEDGER ENTRY --------
                    LedgerRestEntry.objects.create(
                        project_name=expense_req.project_name,
                        type="Expense",
                        exp_name=expense_req.item_name,  # ✅ FK
                        empl_name=expense_req.employee_name.employee_name if expense_req.employee_name else "",
                        cash_type=cash_type_obj,
                        cheque_number=expense_req.cheque_number,
                        head=expense_req.head_of_account,
                        mr_or_bill_no=generated_code,
                        date=expense_req.requisition_date,
                        description=expense_req.descript or "",
                        debit=expense_req.amount,
                        credit=0,
                        carrier="",
                        loan_status="payment",
                        tbl_id=str(debit_voucher.id),
                        tbl_name="Payment",
                    )

                    # -------- UPDATE REQUISITION --------
                    expense_req.approv_status = "approved"
                    expense_req.ledger_add = True

                    expense_req.save(update_fields=[
                        "approv_status",
                        "ledger_add"
                    ])

                messages.success(request, "Approved & Posted Successfully ✅")

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Error: {str(e)}")

    return redirect(request.META.get("HTTP_REFERER", "/"))
    


@login_required
def rest_print_exp_requisition_data(request, date_str, project_id):
    requisitions = RestExpenseRequisition.objects.filter(
        requisition_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        project_name_id=project_id  
    )

    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'restaurant/expenses/print_exp_requisition_data.html', {
        'requisitions': requisitions,
        'date_str': date_str,
        'project_id': project_id,
        'total_amount': total_amount,
    })
    
    



# import logging
# from collections import defaultdict
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from django.db.models import Q

# logger = logging.getLogger(__name__)

# @login_required 
# def restau_requisition_list(request):
#     username = request.user.username

#     # Fetching necessary QuerySets
#     projects_first = ProjectFirstLevelName.objects.all()
#     suppliers = RestaurantJewelSupplier.objects.all()

#     requisitions = (
#         RestRequisition.objects
#         .filter(
#             return_requisition__isnull=True,
#             approv_store='approved',
#             approv_purch_status='approved',
#             #approv_status ='pending',
#             approv_status__in=['pending', 'approved'],
#         )
#         .exclude(Q(vendor_name__isnull=True) | Q(vendor_name=''))
#         .select_related('project_name', 'employee_name', 'item_name')
#         .order_by('-id')
#     )

#     grouped_data = []
#     uniq_id_map = defaultdict(list)
#     project_map = defaultdict(list)

#     for req in requisitions:
#         if req.project_name:
#             if req.requi_uniq_id:
#                 uniq_id_map[req.requi_uniq_id].append(req)
#             else:
#                 project_map[req.project_name].append(req)

#     for uniq_id, items in uniq_id_map.items():
#         total_amount = sum(item.amount for item in items if item.amount)
#         latest_req = items[0]
#         vendor_names = list(set(item.vendor_name for item in items if item.vendor_name))

#         status = "Approved" if all(item.approv_status == 'approved' for item in items) else "Pending"

#         grouped_data.append({
#             'group_type': 'uniq_id',
#             'requi_uniq_id': uniq_id,
#             'requisition_date': latest_req.requisition_date,
#             'project_name': latest_req.project_name,
#             'total_amount': total_amount,
#             'project_id': latest_req.project_name.id,
#             'vendor_names': vendor_names,
#             'status': status,
#         })

#     for project, items in project_map.items():
#         total_amount = sum(item.amount for item in items if item.amount)
#         latest_req = items[0]
#         vendor_names = list(set(item.vendor_name for item in items if item.vendor_name))

#         status = "Approved" if all(item.approv_status == 'approved' for item in items) else "Pending"

#         # 🔥 FIXED: Changed 'req.employee_name.employee_name' to 'req.employee_name.rda_emp_name'
#         employee_names = []
#         for req in items:
#             if req.employee_name and hasattr(req.employee_name, 'rda_emp_name'):
#                 employee_names.append(req.employee_name.rda_emp_name)
#             elif req.employee_name:
#                 employee_names.append(str(req.employee_name))
        
#         projects_first = ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         )

#         grouped_data.append({
#             'group_type': 'project',
#             'requi_uniq_id': None,
#             'requisition_date': latest_req.requisition_date,
#             'project_name': project,
#             'total_amount': total_amount,
#             'project_id': project.id,
#             'vendor_names': vendor_names,
#             'status': status,
#             'employee_names': list(set(employee_names)),
#         })

#     # Sort so PENDING rows come first in the table
#     grouped_data = sorted(grouped_data, key=lambda x: 0 if x['status'] == "Pending" else 1)

#     # Note: Ensure the model loaded into 'Employee' here matches your structural expectations.
#     # If the database model is named RestaurantEmployee, swap it out here as well.
#     if username == 'admin':
#         employees = RestaurantEmployee.objects.exclude(rda_emp_type__iexact='admin')
#     else:
#         employees = RestaurantEmployee.objects.filter(rda_emp_name=username)

#     context = {
#         'grouped_data': grouped_data,
#         'projects_firts': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         ),
#         'employees': employees,
#         'suppliers': suppliers,
#     }

#     return render(request, 'restaurant/requisitions/requisition_list.html', context)
    


from collections import defaultdict
import logging
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def restau_requisition_list(request):
    username = request.user.username

    # Fetching initial QuerySets
    suppliers = RestaurantJewelSupplier.objects.all()

    # Base target projects filter
    target_projects = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    # FIXED: Use vendor_name__isnull=False instead of comparing a ForeignKey to an empty string ''
    requisitions = (
        RestRequisition.objects.filter(
            return_requisition__isnull=True,
            approv_store="approved",
            approv_purch_status="approved",
            approv_status__in=["pending", "approved"],
            vendor_name__isnull=False,  # Exclude null vendor references safely
        )
        .select_related("project_name", "employee_name", "item_name")
        .order_by("-id")
    )

    grouped_data = []
    uniq_id_map = defaultdict(list)
    project_map = defaultdict(list)

    for req in requisitions:
        if req.project_name:
            if req.requi_uniq_id:
                uniq_id_map[req.requi_uniq_id].append(req)
            else:
                project_map[req.project_name].append(req)

    # 1. Group by Unique Requisition ID
    for uniq_id, items in uniq_id_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]
        vendor_names = list(
            set(item.vendor_name for item in items if item.vendor_name)
        )

        status = (
            "Approved"
            if all(item.approv_status == "approved" for item in items)
            else "Pending"
        )

        grouped_data.append(
            {
                "group_type": "uniq_id",
                "requi_uniq_id": uniq_id,
                "requisition_date": latest_req.requisition_date,
                "project_name": latest_req.project_name,
                "total_amount": total_amount,
                "project_id": latest_req.project_name.id,
                "vendor_names": vendor_names,
                "status": status,
            }
        )

    # 2. Group by Project Name
    for project, items in project_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]
        vendor_names = list(
            set(item.vendor_name for item in items if item.vendor_name)
        )

        status = (
            "Approved"
            if all(item.approv_status == "approved" for item in items)
            else "Pending"
        )

        employee_names = []
        for req in items:
            if req.employee_name and hasattr(req.employee_name, "rda_emp_name"):
                employee_names.append(req.employee_name.rda_emp_name)
            elif req.employee_name:
                employee_names.append(str(req.employee_name))

        grouped_data.append(
            {
                "group_type": "project",
                "requi_uniq_id": None,
                "requisition_date": latest_req.requisition_date,
                "project_name": project,
                "total_amount": total_amount,
                "project_id": project.id,
                "vendor_names": vendor_names,
                "status": status,
                "employee_names": list(set(employee_names)),
            }
        )

    # Sort so PENDING rows come first in the table
    grouped_data = sorted(
        grouped_data, key=lambda x: 0 if x["status"] == "Pending" else 1
    )

    # Employee filtering based on active user
    if username == "admin":
        employees = RestaurantEmployee.objects.exclude(
            rda_emp_type__iexact="admin"
        )
    else:
        employees = RestaurantEmployee.objects.filter(rda_emp_name=username)

    context = {
        "grouped_data": grouped_data,
        "projects_firts": target_projects,
        "projects_first": target_projects,
        "employees": employees,
        "suppliers": suppliers,
    }

    return render(
        request, "restaurant/requisitions/requisition_list.html", context
    )
    
    
    
from django.contrib.auth.models import User
from purchase.models import Notification

@login_required
def rest_requisitions_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            req_type = data.get('type') or request.GET.get('type')
            remark_text = data.get('remark') or request.GET.get('remark')

            if not reqsi_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No requisition items found.'
                })

            if not employee_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Employee is required.'
                })

            if not project_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Project is required.'
                })

            if not req_type:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Type is required.'
                })

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_id)

            requisition_date = timezone.now()

            saved_requisitions = []

            for item in reqsi_data:

                try:
                    qty = Decimal(
                        str(item.get('qty', 0) or 0)
                    ).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP
                    )

                    rate = Decimal(
                        str(item.get('rate', 0) or 0)
                    ).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP
                    )

                    discount = Decimal(
                        str(item.get('discount', 0) or 0)
                    ).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP
                    )

                except (InvalidOperation, TypeError, ValueError):
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Invalid numeric value for item: {item.get('item_name', '')}"
                    })

                amount = (
                    (qty * rate) - discount
                ).quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP
                )

                form_data = {
                    'project_name': project.pk,
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name', ''),
                    'type': req_type,
                    'vendor_name': item.get('vendor_name', ''),
                    'unit': item.get('unit', ''),
                    'qty': str(qty),
                    'rate': str(rate),
                    'discount': str(discount),
                    'description': item.get('description', ''),
                    'amount': str(amount),
                    'remark': remark_text or '',
                }

                form = RestRequisitionForm(form_data)

                if form.is_valid():
                    requisition = form.save()
                    saved_requisitions.append(requisition)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': form.errors.as_json()
                    })

            # Notification
            sender_user = request.user

            for user in User.objects.filter(groups__name__iexact='admin'):

                Notification.objects.create(
                    sender=sender_user,
                    recipient=user,
                    project_name=project,
                    message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
                    is_read=False,
                    link='',
                    pass_url='',
                    role='admin',
                    created_at=timezone.now()
                )

            # Firebase Push
            try:
                admin_tokens = list(
                    FCMDevice.objects.filter(
                        user__groups__name__iexact='admin'
                    ).values_list('token', flat=True)
                )

                if admin_tokens:
                    push_service = FCMNotification(
                        api_key=settings.FCM_SERVER_KEY
                    )

                    push_service.notify_multiple_devices(
                        registration_ids=admin_tokens,
                        message_title="New Requisition Submitted",
                        message_body=f"{employee.employee_name} submitted a requisition for project {project.project_first_name}.",
                    )

            except Exception as e:
                print("FCM Error:", str(e))

            return JsonResponse({
                'status': 'success',
                'message': 'Requisition saved successfully.'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    # GET Request
    form = RestRequisitionForm()

    project_id = request.GET.get('project_id')
    employee_id = request.GET.get('employee')
    req_type = request.GET.get('type')

    sppliers = RestaurantSupplier.objects.all()
    headRequists = RestaurantItem.objects.all()

    project_first_name = ''
    employee_name = ''

    try:
        if project_id:
            project = ProjectFirstLevelName.objects.get(pk=project_id)
            project_first_name = project.project_first_name

        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            employee_name = employee.employee_name

    except Exception:
        pass

    return render(
        request,
        'restaurant/requisitions/requisition_add.html',
        {
            'form': form,
            'project_id': project_id,
            'employee': employee_id,
            'type': req_type,
            'project_first_name': project_first_name,
            'employee_name': employee_name,
            'headRequists': headRequists,
            'sppliers': sppliers,
        }
    )
    
    

@login_required
def restu_requisition_by_project(request, requi_id):
    requisitions = RestRequisition.objects.filter(requi_uniq_id=requi_id)
    
    project = None
    if requisitions.exists():
        project = requisitions.first().project_name  # Assuming project_name is a FK

    context = {
        'requisitions': requisitions,
        'project': project,
    }
    return render(request, 'restaurant/requisitions/requisition_by_rqui.html', context)
    
    
    

# @login_required
# def restu_requisition_by_fallback(request, project_id):
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     # Get filters from GET parameters
#     requisition_date_str = request.GET.get('requisition_date')
#     vendor_names_str = request.GET.get('vendor_name', '')  # comma separated vendors

#     # Base queryset: requi_uniq_id null and approv_status NOT approved
#     requisitions = RestRequisition.objects.filter(
#         project_name=project,
#         requi_uniq_id__isnull=True,
#     ).exclude(approv_status='approved')

#     # Filter by requisition_date if provided and valid
#     if requisition_date_str:
#         try:
#             requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()
#             requisitions = requisitions.filter(requisition_date=requisition_date)
#         except ValueError:
#             # Invalid date format, ignore filter
#             pass

#     # Filter by vendor_name(s) if provided
#     if vendor_names_str:
#         vendor_names = [v.strip() for v in vendor_names_str.split(',') if v.strip()]
#         if vendor_names:
#             requisitions = requisitions.filter(vendor_name__in=vendor_names)

#     # Extract unique vendor names for display/filter UI
#     vendors = list(set(r.vendor_name for r in requisitions if r.vendor_name))

#     context = {
#         'project': project,
#         'requisitions': requisitions,
#         'vendors': vendors,
#         'approv_note': 'Not Approved',
#         'requisition_date': requisition_date_str or '',
#         'vendor_name': vendor_names_str or '',
#     }
#     return render(request, 'restaurant/requisitions/requisition_by_project.html', context)
    

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render


@login_required
def restu_requisition_by_fallback(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Get filters from GET parameters
    requisition_date_str = request.GET.get("requisition_date")
    vendor_names_str = request.GET.get(
        "vendor_name", ""
    )  # e.g. 'RCS-00009 - didar fish'

    # Base queryset: requi_uniq_id null and approv_status NOT approved
    requisitions = (
        RestRequisition.objects.filter(
            project_name=project,
            requi_uniq_id__isnull=True,
        )
        .exclude(approv_status="approved")
        .select_related("vendor_name", "item_name", "employee_name")
    )

    # 1. Flexible Requisition Date Filter
    if requisition_date_str:
        try:
            req_date = datetime.strptime(
                requisition_date_str, "%Y-%m-%d"
            ).date()
            requisitions = requisitions.filter(requisition_date=req_date)
        except ValueError:
            pass

    # 2. Flexible Vendor Name Filter (Handles code, name, or full string)
    if vendor_names_str:
        vendor_list = [
            v.strip() for v in vendor_names_str.split(",") if v.strip()
        ]

        vendor_query = Q()
        for vendor_val in vendor_list:
            if vendor_val.isdigit():
                vendor_query |= Q(vendor_name_id=int(vendor_val))
            else:
                # If "RCS-00009 - didar fish" is passed, split code and name if applicable
                parts = [p.strip() for p in vendor_val.split("-") if p.strip()]

                for part in parts:
                    vendor_query |= Q(
                        vendor_name__rest_supplier_name__icontains=part
                    )
                    # If your supplier model has a supplier_code field, uncomment below:
                    # vendor_query |= Q(vendor_name__rest_supplier_code__icontains=part)

        requisitions = requisitions.filter(vendor_query)

    # Extract unique vendor instances safely for display
    vendors = list(set(r.vendor_name for r in requisitions if r.vendor_name))

    context = {
        "project": project,
        "requisitions": requisitions,
        "vendors": vendors,
        "approv_note": "Not Approved",
        "requisition_date": requisition_date_str or "",
        "vendor_name": vendor_names_str or "",
    }
    return render(
        request,
        "restaurant/requisitions/requisition_by_project.html",
        context,
    )
    

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import (
    RestRequisition, 
    ProjectFirstLevelName, 
    RestaurantEmployee, 
    RestaurantItem, 
    RestaurantJewelSupplier
)
from .forms import RestRequisitionForm

@login_required 
def restau_requisition_edit(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)

    if request.method == 'POST':
        form = RestRequisitionForm(request.POST, instance=requisition)
        if form.is_valid():
            updated = form.save()
            messages.success(request, 'Requisition updated successfully.')

            if updated.requi_uniq_id:
                return redirect('requisition_by_project', requi_id=updated.requi_uniq_id)
            else:
                project_id = updated.project_name.id if updated.project_name else ''
                requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
                vendor_id = updated.vendor_name.id if updated.vendor_name else ''
            
                fallback_url = reverse('restu_requisition_by_fallback', args=[project_id])
                return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_id}')
    else:
        form = RestRequisitionForm(instance=requisition)

    context = {
        'form': form,
        'requisition': requisition,
        'project_list': ProjectFirstLevelName.objects.all(),
        # Filter active employees directly
        'employee_names': RestaurantEmployee.objects.filter(rda_active_status=True).select_related('project_name'),
        'requisition_list': RestaurantItem.objects.all(),
        'supplier_list': RestaurantJewelSupplier.objects.all(),
        'contructor_list': RestaurantJewelSupplier.objects.all(), 
    }
    return render(request, 'restaurant/requisitions/requisition_edit.html', context)

# @login_required 
# def restau_requisition_edit(request, pk):
#     requisition = get_object_or_404(RestRequisition, pk=pk)

#     if request.method == 'POST':
#         form = RestRequisitionForm(request.POST, instance=requisition)
#         if form.is_valid():
#             updated = form.save(commit=False)

#             # if requisition.approv_status != 'approved':
#             #     updated.approv_status = request.POST.get('approv_status')
#             #     updated.approv_note = request.POST.get('approv_note')

#             updated.save()
#             messages.success(request, 'Requisition updated successfully.')

#             if updated.requi_uniq_id:
#                 return redirect('requisition_by_project', requi_id=updated.requi_uniq_id)
#             else:
#                 project_id = updated.project_name.id  # use correct field name
#                 requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
#                 vendor_name = updated.vendor_name  # ✅ correct usage
            
#                 fallback_url = reverse('restu_requisition_by_fallback', args=[project_id])
#                 return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_name}')


#     else:
#         form = RestRequisitionForm(instance=requisition)

#     context = {
#         'form': form,
#         'project_list': ProjectFirstLevelName.objects.all(),
#         'employee_names': Employee.objects.all(),
#         'requisition_list': RestaurantItem.objects.all(),
#         'supplier_list': RestaurantJewelSupplier.objects.all(),
#     }
#     return render(request, 'restaurant/requisitions/requisition_edit.html', context)



@login_required
def restau_requisition_delete(request, pk):
    requisition = get_object_or_404(RestRequisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('restau_requisition_list')
    return render(request, 'restaurant/requisitions/requisition_delete.html', {'requisition': requisition})
    
    


@login_required
def requisition_details_view(request, pk):

    requisition = get_object_or_404(
        RestRequisition.objects.select_related(
            'project_name',
            'employee_name',
            'item_name'
        ),
        pk=pk
    )

    return render(
        request,
        'restaurant/requisitions/requisition_details.html',
        {
            'project': requisition.project_name,
            'requisition': requisition,
            'print_time': timezone.now(),
        }
    )
 



# @login_required
# def restu_requisition_confirmation(request):
#     project_id = request.GET.get('project_id')

#     if not project_id:
#         messages.error(request, "Project ID is missing.")
#         return redirect('dashboard')

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_items")
#         approval_status = request.POST.get("approval_status")
#         note = request.POST.get("note")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(request.path + f"?project_id={project.id}")

#         if not approval_status:
#             messages.error(request, "Please select an approval status.")
#             return redirect(request.path + f"?project_id={project.id}")

#         notified_users = set()

#         try:
#             from decimal import Decimal
#             import time
#             requiUniq_id = int(time.time())

#             for item_id in selected_ids:
#                 try:
#                     item = RestRequisition.objects.get(id=item_id)
                    
#                     # 1. Capture potentially modified input data from the posted form
#                     qty_val = request.POST.get(f"qty_{item_id}")
#                     rate_val = request.POST.get(f"rate_{item_id}")
#                     disc_val = request.POST.get(f"discount_{item_id}")
                    
#                     qty = Decimal(str(qty_val)) if qty_val is not None else (item.qty or Decimal('0'))
#                     rate = Decimal(str(rate_val)) if rate_val is not None else (item.rate or Decimal('0'))
#                     discount = Decimal(str(disc_val)) if disc_val is not None else (item.discount or Decimal('0'))
                    
#                     # 2. Check calculation mode condition explicitly inside loop
#                     if item.calc_mode == "unit":
#                         # ✅ Unit Mode: No auto-calculation with qty multiplier
#                         final_amount = (rate - discount).quantize(Decimal('0.01'))
#                     else:
#                         # ✅ Normal Mode: qty * rate
#                         final_amount = (qty * rate - discount).quantize(Decimal('0.01'))
                        
#                     final_amount = max(final_amount, Decimal("0.00"))

#                     # 3. Direct database update write operation
#                     RestRequisition.objects.filter(id=item_id).update(
#                         qty=qty,
#                         rate=rate,
#                         discount=discount,
#                         amount=final_amount,
#                         approv_status=approval_status,
#                         approv_note=note,
#                         requi_uniq_id=requiUniq_id
#                     )
                    
#                     # Refresh local instance safely for context downstream updates
#                     item.refresh_from_db()

#                     # Supplier Handling
#                     if approval_status == "approved":
#                         if item.type in ["Vendor", "Supplier"] and item.vendor_name:
#                             supplier_obj, created = RestaurantJewelSupplier.objects.get_or_create(
#                                 supplier_name=item.vendor_name
#                             )

#                             if hasattr(supplier_obj, "total_amount"):
#                                 current_amount = supplier_obj.total_amount if supplier_obj.total_amount else 0
#                                 supplier_obj.total_amount = current_amount + (item.amount or 0)
#                                 supplier_obj.save()

#                     # Notification User compilation
#                     try:
#                         emp_name = ""
#                         if item.employee_name:
#                             emp_name = item.employee_name.emp_name

#                         user = User.objects.filter(username=emp_name).first()
#                         if user:
#                             notified_users.add(user)
#                     except Exception:
#                         pass

#                 except RestRequisition.DoesNotExist:
#                     continue

#             # Create Notifications
#             for user in notified_users:
#                 try:
#                     Notification.objects.create(
#                         sender=request.user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"Your requisition has been updated for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='',
#                         role='accounts'
#                     )
#                 except Exception:
#                     pass
            
#             messages.success(request, "Selected requisitions updated successfully.")
#             return redirect(request.path + f"?project_id={project.id}")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # ====================================
#     # GET REQUEST 
#     # ====================================
#     # all_requisitions = RestRequisition.objects.filter(
#     #     project_name=project,
#     #     approv_status='pending'
#     # ).order_by('employee_name', 'requisition_date')
#     all_requisitions = (
#         RestRequisition.objects.filter(
#             project_name=project,
#             return_requisition__isnull=True,
#             approv_store='approved',
#             approv_purch_status='approved',
#             approv_status='pending',
#             vendor_name__isnull=False,
#         )
#         .exclude(vendor_name='')
#         .order_by('employee_name', 'requisition_date')
#     )

#     requisitions_by_employee = defaultdict(lambda: defaultdict(list))
#     for req in all_requisitions:
#         employee = req.employee_name
#         date = req.requisition_date
#         requisitions_by_employee[employee][date].append(req)

#     grouped_data = {}
#     for employee, date_group in requisitions_by_employee.items():
#         items_by_date = dict(date_group)
#         totals_by_date = {
#             date: sum(item.amount or 0 for item in items)
#             for date, items in items_by_date.items()
#         }
#         employee_total = sum(totals_by_date.values())
#         grouped_data[employee] = {
#             'items_by_date': items_by_date,
#             'totals_by_date': totals_by_date,
#             'total': employee_total,
#         }

#     final_total = all_requisitions.aggregate(total=Sum('amount'))['total'] or 0
#     reference_requisition = all_requisitions.first()

#     return render(
#         request,
#         'restaurant/requisitions/requisition_confirmation.html',
#         {
#             'project': project,
#             'requisitions_by_employee': grouped_data,
#             'final_total': final_total,
#             'current_status': reference_requisition.approv_status if reference_requisition else '',
#             'current_note': reference_requisition.approv_note if reference_requisition else '',
#         }
#     )
    
from collections import defaultdict
from decimal import Decimal
import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

logger = logging.getLogger(__name__)


@login_required
def restu_requisition_confirmation(request):
    project_id = request.GET.get("project_id")

    if not project_id:
        messages.error(request, "Project ID is missing.")
        return redirect("dashboard")

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # ====================================
    # POST REQUEST HANDLER
    # ====================================
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status")
        note = request.POST.get("note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(f"{request.path}?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(f"{request.path}?project_id={project.id}")

        notified_users = set()

        try:
            requiUniq_id = int(time.time())

            with transaction.atomic():
                for item_id in selected_ids:
                    try:
                        item = RestRequisition.objects.get(id=item_id)

                        # 1. Capture potentially modified input data from form
                        qty_val = request.POST.get(f"qty_{item_id}")
                        rate_val = request.POST.get(f"rate_{item_id}")
                        disc_val = request.POST.get(f"discount_{item_id}")

                        qty = (
                            Decimal(str(qty_val))
                            if qty_val is not None
                            else (item.qty or Decimal("0"))
                        )
                        rate = (
                            Decimal(str(rate_val))
                            if rate_val is not None
                            else (item.rate or Decimal("0"))
                        )
                        discount = (
                            Decimal(str(disc_val))
                            if disc_val is not None
                            else (item.discount or Decimal("0"))
                        )

                        # 2. Check calculation mode condition
                        if item.calc_mode == "unit":
                            final_amount = (rate - discount).quantize(
                                Decimal("0.01")
                            )
                        else:
                            final_amount = (qty * rate - discount).quantize(
                                Decimal("0.01")
                            )

                        final_amount = max(final_amount, Decimal("0.00"))

                        # 3. Direct database update operation
                        RestRequisition.objects.filter(id=item_id).update(
                            qty=qty,
                            rate=rate,
                            discount=discount,
                            amount=final_amount,
                            approv_status=approval_status,
                            approv_note=note,
                            requi_uniq_id=requiUniq_id,
                        )

                        item.refresh_from_db()

                        # 4. Supplier Balance Handling (Only if Approved)
                        if approval_status == "approved" and item.vendor_name:
                            supplier_obj = item.vendor_name
                            if hasattr(supplier_obj, "total_amount"):
                                current_amount = (
                                    supplier_obj.total_amount
                                    or Decimal("0.00")
                                )
                                supplier_obj.total_amount = current_amount + (
                                    item.amount or Decimal("0.00")
                                )
                                supplier_obj.save()

                        # 5. Kitchen Ledger Entry Creation
                        try:
                            project_instance = item.project_name
                            employee_instance = item.employee_name
                            vendor_name_instance = item.vendor_name
                            item_obj = getattr(item, "item_name", None)

                            if (
                                project_instance
                                and employee_instance
                                and item_obj
                            ):
                                RestaurantKitchenLedger.objects.create(
                                    type="Purchase",
                                    requisition=item,
                                    project=project_instance,
                                    employee=employee_instance,
                                    vendor_name=vendor_name_instance,
                                    item_name=item_obj,
                                    debit=Decimal("0.00"),
                                    credit=final_amount,
                                    tbl_id=requiUniq_id,
                                )
                        except NameError:
                            # Skips safely if RestaurantKitchenLedger model is not defined/imported
                            pass

                        # 6. Notification Target User compilation
                        try:
                            emp_name = (
                                item.employee_name.rda_emp_name
                                if item.employee_name
                                else ""
                            )
                            user = User.objects.filter(
                                username=emp_name
                            ).first()
                            if user:
                                notified_users.add(user)
                        except Exception:
                            pass

                    except RestRequisition.DoesNotExist:
                        continue

                # 7. Create System Notifications after batch completes
                for user in notified_users:
                    try:
                        Notification.objects.create(
                            sender=request.user,
                            recipient=user,
                            project_name=project,
                            message=f"Your requisition has been updated for project {project.project_first_name}.",
                            is_read=False,
                            link="",
                            pass_url="",
                            role="accounts",
                        )
                    except Exception:
                        pass

            messages.success(
                request, "Selected requisitions updated successfully."
            )
            return redirect(f"{request.path}?project_id={project.id}")

        except Exception as e:
            import traceback

            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(f"{request.path}?project_id={project.id}")

    # ====================================
    # GET REQUEST HANDLER
    # ====================================
    # FIXED: Replaced invalid `.exclude(vendor_name='')` with `vendor_name__isnull=False`
    all_requisitions = (
        RestRequisition.objects.filter(
            project_name=project,
            return_requisition__isnull=True,
            approv_store="approved",
            approv_purch_status="approved",
            approv_status="pending",
            vendor_name__isnull=False,
        )
        .select_related("project_name", "employee_name", "item_name", "vendor_name")
        .order_by("employee_name", "requisition_date")
    )

    # Group requisitions by employee and then date
    requisitions_by_employee = defaultdict(lambda: defaultdict(list))
    for req in all_requisitions:
        employee = req.employee_name
        date = req.requisition_date
        requisitions_by_employee[employee][date].append(req)

    grouped_data = {}
    for employee, date_group in requisitions_by_employee.items():
        items_by_date = dict(date_group)
        totals_by_date = {
            date: sum(item.amount or Decimal("0.00") for item in items)
            for date, items in items_by_date.items()
        }
        employee_total = sum(totals_by_date.values())
        grouped_data[employee] = {
            "items_by_date": items_by_date,
            "totals_by_date": totals_by_date,
            "total": employee_total,
        }

    final_total = (
        all_requisitions.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    reference_requisition = all_requisitions.first()

    return render(
        request,
        "restaurant/requisitions/requisition_confirmation.html",
        {
            "project": project,
            "requisitions_by_employee": grouped_data,
            "final_total": final_total,
            "current_status": (
                reference_requisition.approv_status
                if reference_requisition
                else ""
            ),
            "current_note": (
                reference_requisition.approv_note
                if reference_requisition
                else ""
            ),
        },
    )





        
# @csrf_exempt
# def restu_requisition_update_ajax(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)

#             req_id = data.get("id")
#             qty = float(data.get("qty", 0))
#             rate = float(data.get("rate", 0))
#             discount = float(data.get("discount", 0))

#             requisition = RestRequisition.objects.get(id=req_id)

#             # ✅ Recalculate amount with discount
#             amount = (qty * rate) - discount
#             if amount < 0:
#                 amount = 0

#             requisition.qty = qty
#             requisition.rate = rate
#             requisition.discount = discount
#             requisition.amount = amount
#             requisition.save(update_fields=["qty", "rate", "discount", "amount"])

#             return JsonResponse({
#                 "success": True,
#                 "id": requisition.id,
#                 "qty": qty,
#                 "rate": rate,
#                 "discount": discount,
#                 "amount": round(amount, 2)
#             })

#         except Requisition.DoesNotExist:
#             return JsonResponse({"success": False, "error": "Item not found"}, status=404)
#         except Exception as e:
#             return JsonResponse({"success": False, "error": str(e)}, status=400)

#     return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
        
        
    
# @login_required
# def restuarant_get_stock_qty(request):
#     item_id = request.GET.get('item_id')
#     project_id = request.GET.get('project_id')

#     try:
#         total_qty = RestInventories.objects.filter(
#             item_name_id=item_id
#         ).aggregate(total=Sum('qtysub'))['total'] or 0

#         return JsonResponse({'qtysub': total_qty})

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)
    




# from datetime import datetime

# from django.contrib.auth.decorators import login_required
# from django.db.models import Q, Sum
# from django.http import HttpResponse
# from django.shortcuts import get_object_or_404, render
# from django.utils.timezone import now

# from num2words import num2words


# @login_required
# def rest_requisition_item_summary(request):

#     project_id = request.GET.get('project_id')
#     supplier_id = request.GET.get('supplier_id')
#     status = request.GET.get('status')
#     reqiDate = request.GET.get('reqiDate')

#     if not project_id:
#         return HttpResponse(
#             "Project ID is required.",
#             status=400
#         )

#     try:
#         project = ProjectFirstLevelName.objects.get(
#             id=project_id
#         )
#     except ProjectFirstLevelName.DoesNotExist:
#         return HttpResponse(
#             "Project not found.",
#             status=404
#         )

#     requisition_filter = Q(
#         project_name=project
#     )

#     supplier = None

#     # Supplier Filter
#     if supplier_id:
#         try:
#             supplier = RestaurantSupplier.objects.get(
#                 id=supplier_id
#             )

#             requisition_filter &= Q(
#                 vendor_name=supplier.rest_supplier_name
#             )

#         except RestaurantSupplier.DoesNotExist:
#             return HttpResponse(
#                 "Supplier not found.",
#                 status=404
#             )

#     # Status Filter
#     if status:
#         requisition_filter &= Q(
#             approv_status=status.lower()
#         )

#     # Date Filter
#     if reqiDate:
#         try:
#             req_date = datetime.strptime(
#                 reqiDate,
#                 "%Y-%m-%d"
#             ).date()

#             requisition_filter &= Q(
#                 requisition_date=req_date
#             )

#         except ValueError:
#             return HttpResponse(
#                 "Invalid date format. Use YYYY-MM-DD.",
#                 status=400
#             )

#     requisition_items = (
#         RestRequisition.objects
#         .select_related(
#             'project_name',
#             'employee_name',
#             'item_name'
#         )
#         .filter(requisition_filter)
#         .order_by('item_name')
#     )

#     total_qty = (
#         requisition_items.aggregate(
#             total=Sum('qty')
#         )['total']
#         or 0
#     )

#     total_amount = (
#         requisition_items.aggregate(
#             total=Sum('amount')
#         )['total']
#         or 0
#     )

#     requisition_date = (
#         requisition_items.first().requisition_date
#         if requisition_items.exists()
#         else None
#     )

#     def amount_to_words(amount):

#         amount = round(float(amount), 2)

#         taka = int(amount)

#         poisha = int(
#             round((amount - taka) * 100)
#         )

#         taka_words = (
#             num2words(
#                 taka,
#                 lang='en'
#             ).capitalize()
#             + " Taka"
#         )

#         if poisha > 0:
#             return (
#                 f"{taka_words} and "
#                 f"{num2words(poisha, lang='en')} Poisha"
#             )

#         return taka_words

#     context = {
#         'project': project,
#         'supplier': supplier,
#         'requisition_items': requisition_items,
#         'total_qty': total_qty,
#         'total_amount': total_amount,
#         'amount_in_words': amount_to_words(total_amount),
#         'print_time': now(),
#         'requisition_date': requisition_date,
#     }

#     return render(
#         request,
#         'restaurant/requisitions/requisition_item_summary.html',
#         context
#     )




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.timezone import now
from num2words import num2words

@login_required
def rest_requisition_item_summary(request):

    project_id = request.GET.get('project_id')
    supplier_name = request.GET.get('supplier_id')
    status = request.GET.get('status')
    reqiDate = request.GET.get('reqiDate')

    project = get_object_or_404(
        ProjectFirstLevelName,
        id=project_id
    )

    requisition_items = RestRequisition.objects.filter(
        project_name=project
    )

    # Supplier Filter
    if supplier_name:
        requisition_items = requisition_items.filter(
            vendor_name__iexact=supplier_name
        )

    # Status Filter
    if status:
        requisition_items = requisition_items.filter(
            approv_status__iexact=status
        )

    # Date Filter
    if reqiDate:
        requisition_items = requisition_items.filter(
            requisition_date=reqiDate
        )

    requisition_items = requisition_items.order_by(
        'item_name'
    )

    total_amount = requisition_items.aggregate(
        total=Sum('amount')
    )['total'] or 0

    requisition_date = None

    if requisition_items.exists():
        requisition_date = requisition_items.first().requisition_date

    suppliers = (
        requisition_items
        .exclude(vendor_name__isnull=True)
        .exclude(vendor_name='')
        .values_list('vendor_name', flat=True)
        .distinct()
    )

    employees = (
        requisition_items
        .values_list(
            'employee_name__emp_name',
            flat=True
        )
        .distinct()
    )

    def amount_to_words(amount):

        taka = int(amount)

        poisha = int(
            round(
                (float(amount) - taka) * 100
            )
        )

        taka_words = (
            num2words(
                taka,
                lang='en'
            ).capitalize()
            + ' Taka'
        )

        if poisha:
            return (
                f"{taka_words} and "
                f"{num2words(poisha)} Poisha"
            )

        return taka_words

    context = {
        'project': project,
        'supplier': supplier_name,
        'suppliers': suppliers,
        'employees': employees,
        'requisition_items': requisition_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
        'requisition_date': requisition_date,
    }

    return render(
        request,
        'restaurant/requisitions/requisition_item_summary.html',
        context
    )
    
    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.timezone import now
from num2words import num2words

@login_required
def restu_requisition_approved(request, requi_uniq_id):

    requisition_items = RestRequisition.objects.filter(
        requi_uniq_id=requi_uniq_id
    ).select_related(
        'project_name',
        'employee_name',
        'item_name'
    )

    if not requisition_items.exists():
        return render(
            request,
            'restaurant/requisitions/restu_requisition_approved.html',
            {'error': 'No requisition found.'}
        )

    first_item = requisition_items.first()

    project = first_item.project_name
    requisition_date = first_item.requisition_date
    supplier = first_item.vendor_name

    total_amount = requisition_items.aggregate(
        total=Sum('amount')
    )['total'] or 0

    employees = requisition_items.values_list(
        'employee_name__rda_emp_name',
        flat=True
    ).distinct()

    def amount_to_words(amount):
        taka = int(amount)
        poisha = int(round((float(amount) - taka) * 100))

        taka_words = (
            num2words(taka, lang='en').capitalize()
            + ' Taka'
        )

        if poisha:
            return (
                f"{taka_words} and "
                f"{num2words(poisha)} Poisha"
            )

        return taka_words

    context = {
        'requi_uniq_id': requi_uniq_id,
        'project': project,
        'supplier': supplier,
        'employees': employees,
        'requisition_items': requisition_items,
        'requisition_date': requisition_date,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
    }

    return render(
        request,
        'restaurant/requisitions/restu_requisition_approved.html',
        context
    )
    
    
    
  


# import json
# import traceback
# from decimal import Decimal, InvalidOperation

# from django.db.models import Sum
# from django.http import JsonResponse
# from django.shortcuts import render
# from django.utils import timezone

# from .models import (
#     ProjectFirstLevelName,
#     RestaurantCategory,
#     RestaurantEmployee,
#     RestaurantItem,
#     RestaurantJewelSupplier,
#     RestInventories,
#     RestRequisition,
# )

# GALLERIA_PROJECTS = [
#     "The Galleria Restauent Cafe",
#     "The Galleria Live Kitchen",
# ]


# def _employee_qs(project_id=None):
#     """Same employee filtering rules as public_rest_requisition_create."""
#     qs = RestaurantEmployee.objects.filter(
#         rda_active_status=True,
#         project_name__project_first_name__in=GALLERIA_PROJECTS,
#     ).exclude(rda_emp_type__iexact="admin")

#     if project_id == "36":
#         qs = qs.filter(id__in=[88, 36, 2])
#     elif project_id == "60":
#         qs = qs.filter(id__in=[59, 3])
#     elif project_id:
#         qs = qs.filter(project_name_id=project_id)
#     return qs


# def public_rest_requisition_create(request):
#     today = timezone.now().date()

#     # ------------------------------------------------------------------
#     # 1. AJAX GET: employees for a project (reused dropdown filter)
#     #    Keyed on query params only — normal page load uses ?project=,
#     #    AJAX uses ?project_id=, so there is no clash.
#     # ------------------------------------------------------------------
#     if request.method == "GET" and "project_id" in request.GET and "category_id" not in request.GET:
#         try:
#             emps = _employee_qs(request.GET.get("project_id"))
#             return JsonResponse({
#                 "employees": [{"id": e.id, "name": e.rda_emp_name} for e in emps]
#             })
#         except Exception as err:
#             traceback.print_exc()
#             return JsonResponse({"status": "error", "message": str(err)}, status=500)

#     # ------------------------------------------------------------------
#     # 2. AJAX GET: items of one category + current stock + today's saved qty
#     # ------------------------------------------------------------------
#     if request.method == "GET" and "category_id" in request.GET:
#         try:
#             cat_id = request.GET.get("category_id")
#             project_id = request.GET.get("project_id") or None
#             employee_id = request.GET.get("employee_id") or None

#             items = RestaurantItem.objects.filter(rest_category_id=cat_id).order_by("rest_item_name")
#             item_ids = list(items.values_list("id", flat=True))

#             # -- Current stock per item: IN (qty) minus OUT (qtysub) --------
#             stock_rows = (
#                 RestInventories.objects
#                 .filter(item_name_id__in=item_ids)
#                 .values("item_name_id")
#                 .annotate(in_qty=Sum("qty"), out_qty=Sum("qtysub"))
#             )
#             stock_map = {
#                 r["item_name_id"]: (r["in_qty"] or 0) - (r["out_qty"] or 0)
#                 for r in stock_rows
#             }

#             # -- Today's already-saved requisition per item (prefill) -------
#             saved_map = {}
#             if project_id and employee_id:
#                 saved = RestRequisition.objects.filter(
#                     requisition_date=today,
#                     project_name_id=project_id,
#                     employee_name_id=employee_id,
#                     item_name_id__in=item_ids,
#                 )
#                 saved_map = {
#                     r.item_name_id: {
#                         "qty": float(r.qty),
#                         "unit": r.unit,
#                         "vendor": r.vendor_name or "",
#                         "rate": float(r.rate),
#                         "amount": float(r.amount or 0),
#                         "calc_mode": r.calc_mode or "normal",
#                         "approv_store": r.approv_store,
#                         "approv_purch": r.approv_purch_status,
#                         "req_id": r.id,
#                     }
#                     for r in saved
#                 }

#             payload = []
#             for it in items:
#                 s = saved_map.get(it.id, {})
#                 payload.append({
#                     "id": it.id,
#                     "name": it.rest_item_name,
#                     "code": it.rest_item_code or "",
#                     "stock": stock_map.get(it.id, 0),
#                     "saved_qty": s.get("qty", ""),
#                     "saved_unit": s.get("unit", ""),
#                     "saved_vendor": s.get("vendor", ""),
#                     "saved_rate": s.get("rate", ""),
#                     "saved_amount": s.get("amount", 0),
#                     "saved_calc_mode": s.get("calc_mode", "normal"),
#                     "approv_store": s.get("approv_store", ""),
#                     "approv_purch": s.get("approv_purch", ""),
#                 })
#             return JsonResponse({"status": "success", "items": payload})
#         except Exception as err:
#             traceback.print_exc()
#             return JsonResponse({"status": "error", "message": str(err)}, status=500)

#     # ------------------------------------------------------------------
#     # 3. AJAX POST: auto-save one item / store approval
#     # ------------------------------------------------------------------
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             action = data.get("action")

#             # ---------- 3a. Auto-save a single item row -------------------
#             if action == "save_item":
#                 project_id = data.get("project_id")
#                 employee_id = data.get("employee_id")
#                 item_id = data.get("item_id")
#                 unit = (data.get("unit") or "").strip()
#                 vendor_name_str = (data.get("vendor") or "").strip()[:100]
#                 calc_mode = data.get("calc_mode") or "normal"
#                 if calc_mode not in ("normal", "unit"):
#                     calc_mode = "normal"
                    
#                 try:
#                     qty = Decimal(str(data.get("qty") or 0))
#                     rate = Decimal(str(data.get("rate") or 0))
#                 except InvalidOperation:
#                     return JsonResponse({"status": "error", "message": "Invalid quantity or rate value."})
            
#                 if rate <= 0:
#                     rate = Decimal("1.00")
            
#                 if calc_mode == "unit":
#                     amount = (qty * rate).quantize(Decimal("0.01"))
#                 else:
#                     amount = rate.quantize(Decimal("0.01"))
            
#                 if not (project_id and employee_id and item_id):
#                     return JsonResponse({"status": "error", "message": "Project, Employee and Item are required."})
            
#                 if qty <= 0:
#                     RestRequisition.objects.filter(
#                         requisition_date=today,
#                         project_name_id=project_id,
#                         employee_name_id=employee_id,
#                         item_name_id=item_id,
#                         approv_store="pending",
#                     ).delete()
#                     return JsonResponse({"status": "success", "message": "Row removed.", "saved": False})
            
#                 if not unit:
#                     return JsonResponse({"status": "error", "message": "Please select a unit first."})
            
#                 # Resolve vendor string to a RestaurantJewelSupplier instance (if provided)
#                 vendor_obj = None
#                 if vendor_name_str:
#                     vendor_obj, _ = RestaurantJewelSupplier.objects.get_or_create(
#                         rest_supplier_name=vendor_name_str
#                     )
            
#                 lookup = dict(
#                     requisition_date=today,
#                     project_name_id=project_id,
#                     employee_name_id=employee_id,
#                     item_name_id=item_id,
#                 )
#                 existing = RestRequisition.objects.filter(**lookup).order_by("id")
            
#                 if existing.exists():
#                     obj = existing.first()
#                     existing.exclude(id=obj.id).delete()
#                     obj.type = "Restaurant"
#                     obj.unit = unit
#                     obj.qty = qty
#                     obj.vendor_name = vendor_obj  # Assign the instance here
#                     obj.rate = rate
#                     obj.amount = amount
#                     obj.calc_mode = calc_mode
#                     obj.discount = Decimal("0.00")
#                     obj.save()
#                     created = False
#                 else:
#                     obj = RestRequisition.objects.create(
#                         **lookup,
#                         type="Restaurant",
#                         unit=unit,
#                         qty=qty,
#                         vendor_name=vendor_obj,  # Assign the instance here
#                         rate=rate,
#                         amount=amount,
#                         calc_mode=calc_mode,
#                         discount=Decimal("0.00"),
#                         description=data.get("description", "") or "",
#                         remark=data.get("remark", "") or "",
#                         requi_uniq_id=None,
#                     )
#                     created = True
                    
#                 return JsonResponse({
#                     "status": "success",
#                     "message": "Saved." if created else "Updated.",
#                     "saved": True,
#                     "req_id": obj.id,
#                     "amount": float(amount),
#                 })

#             # ---------- 3b. Store approval button -------------------------
#             if action == "store_approve":
#                 project_id = data.get("project_id")
#                 employee_id = data.get("employee_id")

#                 qs = RestRequisition.objects.filter(
#                     requisition_date=today,
#                     approv_store="pending",
#                 )
#                 if project_id:
#                     qs = qs.filter(project_name_id=project_id)
#                 if employee_id:
#                     qs = qs.filter(employee_name_id=employee_id)

#                 updated = qs.update(approv_store="approved")
#                 return JsonResponse({
#                     "status": "success",
#                     "message": f"{updated} item(s) store-approved.",
#                     "updated": updated,
#                 })

#             # ---------- 3c. Purchase approval button ----------------------
#             if action == "purchase_approve":
#                 project_id = data.get("project_id")
#                 employee_id = data.get("employee_id")

#                 qs = RestRequisition.objects.filter(
#                     requisition_date=today,
#                     approv_purch_status="pending",
#                 )
#                 if project_id:
#                     qs = qs.filter(project_name_id=project_id)
#                 if employee_id:
#                     qs = qs.filter(employee_name_id=employee_id)

#                 updated = qs.update(
#                     approv_purch_status="approved",
#                     purch_date=today,
#                 )
#                 return JsonResponse({
#                     "status": "success",
#                     "message": f"{updated} item(s) purchase-approved.",
#                     "updated": updated,
#                 })

#             return JsonResponse({"status": "error", "message": "Unknown action."}, status=400)

#         except Exception as err:
#             traceback.print_exc()
#             return JsonResponse({"status": "error", "message": str(err)}, status=500)

#     # ------------------------------------------------------------------
#     # 4. NORMAL GET: initial page render
#     # ------------------------------------------------------------------
#     selected_project_id = request.GET.get("project")
#     selected_employee_id = request.GET.get("employee")

#     categories = RestaurantCategory.objects.all().order_by("restu_category_name")

#     projects_firts = ProjectFirstLevelName.objects.filter(
#         project_first_name__in=GALLERIA_PROJECTS
#     )

#     initial_employees = _employee_qs(selected_project_id)

#     # Store-approval button state for today's rows
#     base_today = RestRequisition.objects.filter(requisition_date=today)
#     if selected_project_id:
#         base_today = base_today.filter(project_name_id=selected_project_id)
#     if selected_employee_id:
#         base_today = base_today.filter(employee_name_id=selected_employee_id)

#     pending_count = base_today.filter(approv_store="pending").count()
#     approved_count = base_today.filter(approv_store="approved").count()
#     purch_pending_count = base_today.filter(approv_purch_status="pending").count()
#     purch_approved_count = base_today.filter(approv_purch_status="approved").count()

#     suppliers = RestaurantJewelSupplier.objects.all().order_by("rest_supplier_name")

#     return render(
#         request,
#         "restaurant/requisitions/public_requisition_add.html",
#         {
#             "categories": categories,
#             "projects_firts": projects_firts,
#             "employees": initial_employees,
#             "suppliers": suppliers,
#             "selected_project_id": selected_project_id,
#             "selected_employee_id": selected_employee_id,
#             "pending_count": pending_count,
#             "approved_count": approved_count,
#             "purch_pending_count": purch_pending_count,
#             "purch_approved_count": purch_approved_count,
#         },
#     )



import json
import traceback
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import (
    ProjectFirstLevelName,
    RestaurantCategory,
    RestaurantEmployee,
    RestaurantItem,
    RestInventories,
    RestRequisition,
)

GALLERIA_PROJECTS = [
    "The Galleria Restauent Cafe",
    "The Galleria Live Kitchen",
]

# Fixed values now that Unit / Rate / Vendor / Whole-Unit mode are no
# longer collected from the UI. Amount = qty * FIXED_RATE (see model.save()).
FIXED_RATE = Decimal("1.00")
FIXED_CALC_MODE = "unit"
FIXED_UNIT = ""  # no unit selection anymore


def _resolve_date(raw_value):
    """Parse a 'YYYY-MM-DD' string into a date, falling back to today
    when it's missing or invalid."""
    if raw_value:
        try:
            return datetime.strptime(raw_value, "%Y-%m-%d").date()
        except ValueError:
            pass
    return timezone.now().date()


def _employee_qs(project_id=None):
    """Same employee filtering rules as public_rest_requisition_create."""
    qs = RestaurantEmployee.objects.filter(
        rda_active_status=True,
        project_name__project_first_name__in=GALLERIA_PROJECTS,
    ).exclude(rda_emp_type__iexact="admin")

    if project_id == "36":
        qs = qs.filter(id__in=[88, 36, 2])
    elif project_id == "60":
        qs = qs.filter(id__in=[59, 3])
    elif project_id:
        qs = qs.filter(project_name_id=project_id)
    return qs


def public_rest_requisition_create(request):
    # ------------------------------------------------------------------
    # 1. AJAX GET: employees for a project (reused dropdown filter)
    #    Keyed on query params only — normal page load uses ?project=,
    #    AJAX uses ?project_id=, so there is no clash.
    # ------------------------------------------------------------------
    if request.method == "GET" and "project_id" in request.GET and "category_id" not in request.GET:
        try:
            emps = _employee_qs(request.GET.get("project_id"))
            return JsonResponse({
                "employees": [{"id": e.id, "name": e.rda_emp_name} for e in emps]
            })
        except Exception as err:
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(err)}, status=500)

    # ------------------------------------------------------------------
    # 2. AJAX GET: items of one category (or ALL categories) + current
    #    stock + this date's saved qty
    # ------------------------------------------------------------------
    if request.method == "GET" and "category_id" in request.GET:
        try:
            cat_id = request.GET.get("category_id")
            project_id = request.GET.get("project_id") or None
            employee_id = request.GET.get("employee_id") or None
            req_date = _resolve_date(request.GET.get("req_date"))

            items = RestaurantItem.objects.select_related("rest_category").order_by(
                "rest_category__restu_category_name", "rest_item_name"
            )
            if cat_id and cat_id != "all":
                items = items.filter(rest_category_id=cat_id)

            item_ids = list(items.values_list("id", flat=True))

            # -- Current stock per item: IN (qty) minus OUT (qtysub) --------
            stock_rows = (
                RestInventories.objects
                .filter(item_name_id__in=item_ids)
                .values("item_name_id")
                .annotate(in_qty=Sum("qty"), out_qty=Sum("qtysub"))
            )
            stock_map = {
                r["item_name_id"]: (r["in_qty"] or 0) - (r["out_qty"] or 0)
                for r in stock_rows
            }

            # -- Already-saved requisition per item for this date (prefill) -
            saved_map = {}
            if project_id and employee_id:
                saved = RestRequisition.objects.filter(
                    requisition_date=req_date,
                    project_name_id=project_id,
                    employee_name_id=employee_id,
                    item_name_id__in=item_ids,
                )
                saved_map = {
                    r.item_name_id: {
                        "qty": float(r.qty),
                        "amount": float(r.amount or 0),
                        "approv_store": r.approv_store,
                        "approv_purch": r.approv_purch_status,
                        "req_id": r.id,
                    }
                    for r in saved
                }

            payload = []
            for it in items:
                s = saved_map.get(it.id, {})
                payload.append({
                    "id": it.id,
                    "name": it.rest_item_name,
                    "code": it.rest_item_code or "",
                    "category_name": getattr(it.rest_category, "restu_category_name", ""),
                    "stock": stock_map.get(it.id, 0),
                    "saved_qty": s.get("qty", ""),
                    "saved_amount": s.get("amount", 0),
                    "approv_store": s.get("approv_store", ""),
                    "approv_purch": s.get("approv_purch", ""),
                })
            return JsonResponse({"status": "success", "items": payload})
        except Exception as err:
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(err)}, status=500)

    # ------------------------------------------------------------------
    # 3. AJAX POST: auto-save one item / store approval
    # ------------------------------------------------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")

            # ---------- 3a. Auto-save a single item row -------------------
            if action == "save_item":
                project_id = data.get("project_id")
                employee_id = data.get("employee_id")
                item_id = data.get("item_id")
                req_date = _resolve_date(data.get("req_date"))

                try:
                    qty = Decimal(str(data.get("qty") or 0))
                except InvalidOperation:
                    return JsonResponse({"status": "error", "message": "Invalid quantity value."})

                if not (project_id and employee_id and item_id):
                    return JsonResponse({"status": "error", "message": "Project, Employee and Item are required."})

                if qty <= 0:
                    RestRequisition.objects.filter(
                        requisition_date=req_date,
                        project_name_id=project_id,
                        employee_name_id=employee_id,
                        item_name_id=item_id,
                        approv_store="pending",
                    ).delete()
                    return JsonResponse({"status": "success", "message": "Row removed.", "saved": False})

                rate = FIXED_RATE
                amount = (qty * rate).quantize(Decimal("0.01"))

                lookup = dict(
                    requisition_date=req_date,
                    project_name_id=project_id,
                    employee_name_id=employee_id,
                    item_name_id=item_id,
                )
                existing = RestRequisition.objects.filter(**lookup).order_by("id")

                if existing.exists():
                    obj = existing.first()
                    existing.exclude(id=obj.id).delete()
                    obj.type = "Restaurant"
                    obj.unit = FIXED_UNIT
                    obj.qty = qty
                    obj.vendor_name = None
                    obj.rate = rate
                    obj.amount = amount
                    obj.calc_mode = FIXED_CALC_MODE
                    obj.discount = Decimal("0.00")
                    obj.save()
                    created = False
                else:
                    obj = RestRequisition.objects.create(
                        **lookup,
                        type="Restaurant",
                        unit=FIXED_UNIT,
                        qty=qty,
                        vendor_name=None,
                        rate=rate,
                        amount=amount,
                        calc_mode=FIXED_CALC_MODE,
                        discount=Decimal("0.00"),
                        description=data.get("description", "") or "",
                        remark=data.get("remark", "") or "",
                        requi_uniq_id=None,
                    )
                    created = True

                return JsonResponse({
                    "status": "success",
                    "message": "Saved." if created else "Updated.",
                    "saved": True,
                    "req_id": obj.id,
                    "amount": float(amount),
                })

            # ---------- 3b. Store approval button -------------------------
            if action == "store_approve":
                project_id = data.get("project_id")
                employee_id = data.get("employee_id")
                req_date = _resolve_date(data.get("req_date"))

                qs = RestRequisition.objects.filter(
                    requisition_date=req_date,
                    approv_store="pending",
                )
                if project_id:
                    qs = qs.filter(project_name_id=project_id)
                if employee_id:
                    qs = qs.filter(employee_name_id=employee_id)

                updated = qs.update(approv_store="approved")
                return JsonResponse({
                    "status": "success",
                    "message": f"{updated} item(s) store-approved.",
                    "updated": updated,
                })

            return JsonResponse({"status": "error", "message": "Unknown action."}, status=400)

        except Exception as err:
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(err)}, status=500)

    # ------------------------------------------------------------------
    # 4. NORMAL GET: initial page render
    # ------------------------------------------------------------------
    selected_project_id = request.GET.get("project")
    selected_employee_id = request.GET.get("employee")
    selected_date = _resolve_date(request.GET.get("req_date"))

    categories = RestaurantCategory.objects.all().order_by("restu_category_name")

    projects_firts = ProjectFirstLevelName.objects.filter(
        project_first_name__in=GALLERIA_PROJECTS
    )

    initial_employees = _employee_qs(selected_project_id)

    # Store-approval button state for the selected date's rows
    base_selected_date = RestRequisition.objects.filter(requisition_date=selected_date)
    if selected_project_id:
        base_selected_date = base_selected_date.filter(project_name_id=selected_project_id)
    if selected_employee_id:
        base_selected_date = base_selected_date.filter(employee_name_id=selected_employee_id)

    pending_count = base_selected_date.filter(approv_store="pending").count()
    approved_count = base_selected_date.filter(approv_store="approved").count()

    return render(
        request,
        "restaurant/requisitions/public_requisition_add.html",
        {
            "categories": categories,
            "projects_firts": projects_firts,
            "employees": initial_employees,
            "selected_project_id": selected_project_id,
            "selected_employee_id": selected_employee_id,
            "selected_date": selected_date,
            "pending_count": pending_count,
            "approved_count": approved_count,
        },
    )




from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from .models import RestRequisition 

def print_day_wise_requisitions(request):
    # Initialize base queryset with optimized relations
    requisitions = RestRequisition.objects.select_related("project_name", "employee_name", "item_name")

    # 1. Gather filters from the GET parameters
    project_id = request.GET.get('project')
    employee_id = request.GET.get('employee')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # 2. Apply Project filter if selected
    if project_id:
        requisitions = requisitions.filter(project_name_id=project_id)

    # 3. Apply Employee filter if selected
    if employee_id:
        requisitions = requisitions.filter(employee_name_id=employee_id)

    # 4. Apply Date Range filters
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date__gte=from_date)
        except ValueError:
            pass
            
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date__lte=to_date)
        except ValueError:
            pass

    # Default fallback: If no dates are passed at all, fall back to showing today's entries
    if not from_date_str and not not to_date_str:
        today = timezone.now().date()
        requisitions = requisitions.filter(requisition_date=today)
        display_date_range = f"Today ({today})"
    else:
        display_date_range = f"{from_date_str or 'Beginning'} to {to_date_str or 'End'}"

    # Sort results structurally by project first, then entry ID
    requisitions = requisitions.order_by("project_name", "id")

    context = {
        "requisitions": requisitions,
        "display_date_range": display_date_range,
        "project_id": project_id,
        "employee_id": employee_id,
    }
    
    return render(request, "restaurant/requisitions/print_requisitions.html", context)
    
  
    

from django.db.models import Sum
from django.shortcuts import render

from .models import (
    ProjectFirstLevelName,
    RestaurantEmployee,
    RestRequisition,
)

GALLERIA_PROJECTS = [
    "The Galleria Restauent Cafe",   # NOTE: spelling matches existing DB rows
    "The Galleria Live Kitchen",
]


def public_rest_requisition_list(request):
    projects = ProjectFirstLevelName.objects.filter(
        project_first_name__in=GALLERIA_PROJECTS
    )
    employees = RestaurantEmployee.objects.filter(
        rda_active_status=True
    ).exclude(rda_emp_type__iexact="admin")

    project_id = request.GET.get("project") or ""
    employee_id = request.GET.get("employee") or ""
    from_date = request.GET.get("from_date") or ""
    to_date = request.GET.get("to_date") or ""
    status = request.GET.get("status") or ""   # store_pending / store_approved / purch_pending / purch_approved

    base = RestRequisition.objects.select_related(
        "project_name", "employee_name", "item_name"
    )

    # ---- Project / Employee / Date filters (shared by table AND counts) ----
    if project_id:
        base = base.filter(project_name_id=project_id)
    if employee_id:
        base = base.filter(employee_name_id=employee_id)
    if from_date:
        base = base.filter(requisition_date__gte=from_date)
    if to_date:
        base = base.filter(requisition_date__lte=to_date)

    # ---- Status button counts (on the date/project-filtered set) -----------
    counts = {
        "all": base.count(),
        "store_pending": base.filter(approv_store="pending").count(),
        "store_approved": base.filter(approv_store="approved").count(),
        "purch_pending": base.filter(approv_purch_status="pending").count(),
        "purch_approved": base.filter(approv_purch_status="approved").count(),
    }

    # ---- Apply the active status filter to the table -----------------------
    requisitions = base
    if status == "store_pending":
        requisitions = requisitions.filter(approv_store="pending")
    elif status == "store_approved":
        requisitions = requisitions.filter(approv_store="approved")
    elif status == "purch_pending":
        requisitions = requisitions.filter(approv_purch_status="pending")
    elif status == "purch_approved":
        requisitions = requisitions.filter(approv_purch_status="approved")

    requisitions = requisitions.order_by("-requisition_date", "-id")

    total_amount = requisitions.aggregate(t=Sum("amount"))["t"] or 0
    total_qty = requisitions.aggregate(t=Sum("qty"))["t"] or 0

    return render(request, "restaurant/requisitions/public_requisition_list.html", {
        "projects": projects,
        "employees": employees,
        "requisitions": requisitions,
        "project_id": project_id,
        "employee_id": employee_id,
        "from_date": from_date,
        "to_date": to_date,
        "status": status,
        "counts": counts,
        "total_amount": total_amount,
        "total_qty": total_qty,
    })

    
    
    
    
# def public_rest_requisition_list(request):

#     projects = ProjectFirstLevelName.objects.all()
#     employees = Employee.objects.all()

#     project_id = request.GET.get('project')
#     employee_id = request.GET.get('employee')

#     # ✅ default = today
#     date_filter = request.GET.get('date') or str(date.today())
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     requisitions = RestRequisition.objects.all().select_related(
#         'project_name', 'employee_name', 'item_name'
#     )

#     # ✅ default today filter
#     if not request.GET.get('from_date') and not request.GET.get('to_date') and not request.GET.get('date'):
#         requisitions = requisitions.filter(requisition_date=date.today())

#     # filters
#     if project_id:
#         requisitions = requisitions.filter(project_name_id=project_id)

#     if employee_id:
#         requisitions = requisitions.filter(employee_name_id=employee_id)

#     if date_filter and not from_date and not to_date:
#         requisitions = requisitions.filter(requisition_date=date_filter)

#     if from_date and to_date:
#         requisitions = requisitions.filter(requisition_date__range=[from_date, to_date])

#     requisitions = requisitions.order_by('-requisition_date')

#     return render(request, 'restaurant/requisitions/public_requisition_list.html', {
#         'projects': projects,
#         'employees': employees,
#         'requisitions': requisitions,
#         'project_id': project_id,
#         'employee_id': employee_id,
#         'date': date_filter,
#         'from_date': from_date,
#         'to_date': to_date,
#     })




# @login_required
# def rest_requisition_acct_confirmation(request):
#     project_id = request.GET.get('project_id')
#     employee_list = RestaurantEmployee.objects.filter(
#         project_name_id=project_id,
#         rda_active_status=True
#     ).exclude(
#         rda_emp_name='Admin'
#     )
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     reference_requisition = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).first()

#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_items")
#         approv_acct_status = request.POST.get("approv_acct_status")
#         approv_acct_note = request.POST.get("approv_acct_note")
#         cash_empl = request.POST.get("cash_empl")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         if not approv_acct_status:
#             messages.error(request, "Please select an approval status.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         try:
#             # If grouping items together, use one unique ID for all
#             unique_purch_id = int(time.time())

#             updated_items = RestRequisition.objects.filter(id__in=selected_ids)
#             for item in updated_items:
#                 item.approv_acct_status = approv_acct_status
#                 item.approv_acct_note = approv_acct_note
#                 item.requi_uniq_id = unique_purch_id
#                 item.cash_empl = cash_empl
#                 item.save()

#             messages.success(request, "Selected items updated successfully.")
#             return redirect("restau_requisition_list")
#             #return redirect("requisition_list", pk=updated_items.first().requi_uniq_id)
            

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(f"{request.path}?project_id={project.id}")

#     # Group requisitions by employee
#     employee_ids = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).values_list('employee_name', flat=True).distinct()

#     requisitions_by_employee = {}
#     for emp_id in employee_ids:
#         requisitions = RestRequisition.objects.filter(
#             project_name=project,
#             employee_name=emp_id,
#             approv_status='approved',
#             approv_acct_status='pending'
#         )
#         employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#         employee_obj = requisitions.first().employee_name if requisitions.exists() else None
#         requisitions_by_employee[employee_obj] = {
#             'items': requisitions,
#             'total': employee_total
#         }

#     final_total = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'restaurant/requisitions/requisition_acct_confirmation.html', {
#         'project': project,
#         'employee_list': employee_list,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
#         'print_time': datetime.now(),
#     })


# from django.db.models import Sum
# import time

# @login_required
# def rest_requisition_acct_confirmation(request):

#     project_id = request.GET.get('project_id')

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     employee_list = RestaurantEmployee.objects.filter(
#         project_name_id=project_id,
#         rda_active_status=True
#     ).exclude(
#         rda_emp_name='Admin'
#     )

#     reference_requisition = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).first()

#     # ================= POST =================
#     if request.method == "POST":

#         selected_ids = request.POST.getlist("selected_items")
#         approv_acct_status = request.POST.get("approv_acct_status")
#         approv_acct_note = request.POST.get("approv_acct_note")
#         cash_empl = request.POST.get("cash_empl")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         if not approv_acct_status:
#             messages.error(request, "Approval status required.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         try:

#             # ================= ITEMS =================
#             updated_items = RestRequisition.objects.filter(
#                 id__in=selected_ids
#             )

#             first_item = updated_items.first()

#             if not first_item:
#                 messages.error(request, "No requisition found.")
#                 return redirect(f"{request.path}?project_id={project.id}")

#             # ================= GROUP IDS =================
#             requi_uniq_id = first_item.requi_uniq_id
#             purch_appov = f"PA{int(time.time())}"

#             # ================= TOTAL =================
#             total_amount = updated_items.aggregate(
#                 total=Sum('amount')
#             )['total'] or 0

#             # ================= UPDATE REQUISITIONS =================
#             for item in updated_items:
#                 item.approv_acct_status = approv_acct_status
#                 item.approv_acct_note = approv_acct_note
#                 item.cash_empl = cash_empl
#                 item.purch_appov = purch_appov
#                 item.save()

#             # ================= HRM EMPLOYEE MAP =================
#             approved_employee = Employee.objects.filter(
#                 email=getattr(request.user, "email", None)
#             ).first()

#             if not approved_employee:
#                 approved_employee = Employee.objects.filter(
#                     username=getattr(request.user, "username", None)
#                 ).first()

#             # ================= HISTORY INSERT =================
#             RestRequisitionApprovalHistory.objects.create(

#                 requi_uniq_id=requi_uniq_id,
#                 purch_appov=purch_appov,
#                 project_name=project,
#                 employee_name=first_item.employee_name,
#                 cash_empl=cash_empl,
#                 total_amount=total_amount,
#                 approv_acct_status=approv_acct_status,
#                 approv_acct_note=approv_acct_note,
#                 approved_by=approved_employee   # ✅ HRM Employee
#             )

#             messages.success(
#                 request,
#                 f"Approved Successfully. Ref: {purch_appov}"
#             )

#             return redirect("restau_requisition_list")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, str(e))
#             return redirect(f"{request.path}?project_id={project.id}")

#     # ================= GET =================
#     employee_ids = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).values_list('employee_name', flat=True).distinct()

#     requisitions_by_employee = {}

#     for emp_id in employee_ids:

#         requisitions = RestRequisition.objects.filter(
#             project_name=project,
#             employee_name=emp_id,
#             approv_status='approved',
#             approv_acct_status='pending'
#         )

#         employee_total = requisitions.aggregate(
#             total=Sum('amount')
#         )['total'] or 0

#         employee_obj = requisitions.first().employee_name if requisitions.exists() else None

#         requisitions_by_employee[employee_obj] = {
#             'items': requisitions,
#             'total': employee_total
#         }

#     final_total = RestRequisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'restaurant/requisitions/requisition_acct_confirmation.html', {

#         'project': project,
#         'employee_list': employee_list,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
#         'print_time': datetime.now(),
#     })
    
    



from django.db.models import Sum
from datetime import datetime  
import time
from django.db.models import Q
# Import your models here
# from .models import ProjectFirstLevelName, RestaurantEmployee, RestRequisition, Employee, RestRequisitionApprovalHistory

@login_required
def rest_requisition_acct_confirmation(request):

    project_id = request.GET.get('project_id')

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    employee_query = RestaurantEmployee.objects.filter(
        project_name_id=project_id,
        rda_active_status=True
    ).exclude(
        rda_emp_name='Admin'
    )
    if str(project_id) == '36':
        employee_list = employee_query.filter(id=24)
    elif str(project_id) == '60':
        employee_list = employee_query.filter(id=54)
    else:
        # Fallback to default behavior if it's any other project ID
        employee_list = employee_query

    reference_requisition = RestRequisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).first()

    # ================= POST =================
    if request.method == "POST":

        selected_ids = request.POST.getlist("selected_items")
        approv_acct_status = request.POST.get("approv_acct_status")
        approv_acct_note = request.POST.get("approv_acct_note")
        cash_empl_id = request.POST.get("cash_empl")  # Value coming from HTML <select> ID

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(f"{request.path}?project_id={project.id}")

        if not approv_acct_status:
            messages.error(request, "Approval status required.")
            return redirect(f"{request.path}?project_id={project.id}")

        try:
            # ================= MATCH & EXTRACT EMPLOYEE NAME =================
            cash_empl_name = ""
            if cash_empl_id:
                try:
                    emp_record = RestaurantEmployee.objects.get(id=cash_empl_id)
                    cash_empl_name = emp_record.rda_emp_name  # Extracting actual string name
                except (RestaurantEmployee.DoesNotExist, ValueError):
                    cash_empl_name = "Unknown Employee"

            # ================= ITEMS =================
            updated_items = RestRequisition.objects.filter(
                id__in=selected_ids
            )

            first_item = updated_items.first()

            if not first_item:
                messages.error(request, "No requisition found.")
                return redirect(f"{request.path}?project_id={project.id}")

            # ================= GROUP IDS =================
            requi_uniq_id = first_item.requi_uniq_id
            purch_appov = f"PA{int(time.time())}"

            # ================= TOTAL =================
            total_amount = updated_items.aggregate(
                total=Sum('amount')
            )['total'] or 0

            # ================= UPDATE REQUISITIONS =================
            for item in updated_items:
                item.approv_acct_status = approv_acct_status
                item.approv_acct_note = approv_acct_note
                item.cash_empl = cash_empl_name  # ✅ Saved matching text string name here
                item.purch_appov = purch_appov
                item.save()

            # ================= HRM EMPLOYEE MAP =================
            approved_employee = Employee.objects.filter(
                email=getattr(request.user, "email", None)
            ).first()

            if not approved_employee:
                approved_employee = Employee.objects.filter(
                    username=getattr(request.user, "username", None)
                ).first()

            # ================= HISTORY INSERT =================
            RestRequisitionApprovalHistory.objects.create(
                requi_uniq_id=requi_uniq_id,
                purch_appov=purch_appov,
                project_name=project,
                employee_name=first_item.employee_name,
                cash_empl=cash_empl_name,  # ✅ Saved matching text string name here
                total_amount=total_amount,
                approv_acct_status=approv_acct_status,
                approv_acct_note=approv_acct_note,
                approved_by=approved_employee   # ✅ HRM Employee
            )

            messages.success(
                request,
                f"Approved Successfully. Ref: {purch_appov}"
            )

            return redirect("restau_requisition_list")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, str(e))
            return redirect(f"{request.path}?project_id={project.id}")

    # ================= GET =================
    employee_ids = RestRequisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}

    for emp_id in employee_ids:

        requisitions = RestRequisition.objects.filter(
            project_name=project,
            employee_name=emp_id,
            approv_status='approved',
            approv_acct_status='pending'
        )

        employee_total = requisitions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        employee_obj = requisitions.first().employee_name if requisitions.exists() else None

        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = RestRequisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'restaurant/requisitions/requisition_acct_confirmation.html', {
        'project': project,
        'employee_list': employee_list,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
        'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
        'print_time': datetime.now(),
    })
    
    

from .models import RestRequisitionApprovalHistory


@login_required
def requisition_approval_history_list(request):

    histories = RestRequisitionApprovalHistory.objects.all().order_by('-id')

    return render(
        request,
        'restaurant/requisitions/requisition_history_list.html',
        {
            'histories': histories
        }
    )


@login_required
def requisition_jewel_ledger_list(request):

    histories = RestRequisitionApprovalHistory.objects.all().order_by('-id')

    return render(
        request,
        'restaurant/requisitions/requisition_jewel_ledger_list.html',
        {
            'histories': histories
        }
    )
    



@login_required
def rest_jewel_ledger_manage(request):
    projects_firts = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )
    context = {
        'projectNames': projects_firts,
        'today': date.today(),
    }
    return render(request, 'restaurant/requisitions/jewel_ledger_manage.html', context)
    

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import RestaurantEmployee

@login_required
def get_restaurant_employees_by_project(request):
    project_id = request.GET.get('project_id')
    if project_id:
        # Fetch matching active employees from the database
        employees_queryset = RestaurantEmployee.objects.filter(
            project_name_id=project_id, 
            rda_active_status=True
        ).values('id', 'rda_emp_name')
        
        # Convert to list
        employees_list = list(employees_queryset)
        
        # Prepend an "All Employees" option so the user can select everything combined
        response_data = [{'id': 'all', 'rda_emp_name': '— All Employees —'}] + employees_list
        
        return JsonResponse(response_data, safe=False)
        
    return JsonResponse([], safe=False)
    
    
    
# from decimal import Decimal
# from datetime import datetime
# from django.db.models import Sum
# from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.utils.timezone import make_naive, is_aware

# # Ensure your models are accurately imported here
# # from .models import ProjectFirstLevelName, RestRequisitionApprovalHistory, DailyPayment

# @login_required
# def rest_jewel_ledger_report(request):
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except Exception:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Initialize Base QuerySets
#     approvals = RestRequisitionApprovalHistory.objects.all()
#     payments = DailyPayment.objects.all()

#     # Apply Project Filters
#     if is_valid(project_id):
#         approvals = approvals.filter(project_name_id=project_id)
#         payments = payments.filter(project_id=project_id)

#     # Apply Date Filters
#     if transaction_option == 'datewise':
#         if fd:
#             approvals = approvals.filter(approved_date__date__gte=fd)
#             payments = payments.filter(date__gte=fd)
#         if td:
#             approvals = approvals.filter(approved_date__date__lte=td)
#             payments = payments.filter(date__lte=td)

#     # Gather all unique active project IDs
#     approval_project_ids = list(approvals.values_list('project_name_id', flat=True).distinct())
#     payment_project_ids = list(payments.values_list('project_id', flat=True).distinct())
#     all_project_ids = list(set(filter(None, approval_project_ids + payment_project_ids)))

#     report_data = []

#     for pid in all_project_ids:
#         project = get_object_or_404(ProjectFirstLevelName, id=pid)
        
#         proj_approvals = approvals.filter(project_name_id=pid).order_by('approved_date')
#         proj_payments = payments.filter(project_id=pid).order_by('date')

#         # Calculate Totals
#         credit_total = proj_approvals.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
#         debit_total = proj_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         balance = debit_total - credit_total

#         # Build combined ledger list
#         ledger_entries = []

#         # Map Credit Rows (Approvals)
#         for app in proj_approvals:
#             # Safe conversion of aware datetime to naive datetime for sorting stability
#             app_date = app.approved_date
#             if app_date and is_aware(app_date):
#                 app_date = make_naive(app_date)

#             ledger_entries.append({
#                 'date': app_date,
#                 'description': f"Requisition Approved (ID: {app.requi_uniq_id or 'N/A'}) - Appr. By: {app.approved_by if app.approved_by else 'N/A'}",
#                 'debit': Decimal('0.00'),
#                 'credit': app.total_amount or Decimal('0.00'),
#             })

#         # Map Debit Rows (Payments)
#         for pay in proj_payments:
#             # Combine Date into naive Datetime to match the layout above
#             pay_datetime = datetime.combine(pay.date, datetime.min.time())

#             ledger_entries.append({
#                 'date': pay_datetime,
#                 'description': f"Daily Payment ({pay.type or 'Expense'}) - Ref: {pay.pay_id or 'N/A'}",
#                 'debit': pay.amount or Decimal('0.00'),
#                 'credit': Decimal('0.00'),
#             })

#         # Sort combined records chronologically without mixing timezone statuses
#         ledger_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)

#         report_data.append({
#             'project': project,
#             'ledger_entries': ledger_entries,
#             'debit_total': debit_total,
#             'credit_total': credit_total,
#             'balance': balance,
#         })

#     return render(
#         request,
#         'restaurant/requisitions/jewel_ledger_report.html',
#         {
#             'report_data': report_data,
#             'selected_filters': {
#                 'project': project_id,
#                 'from_date': from_date,
#                 'to_date': to_date,
#                 'transaction': transaction_option,
#             },
#             'print_time': datetime.now(),
#         }
#     )



from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_naive, is_aware

# Ensure all your required models are imported here
# from .models import ProjectFirstLevelName, RestRequisitionApprovalHistory, DailyPayment, RestaurantPublicExpense

@login_required
def rest_jewel_ledger_report(request):
    project_id = request.GET.get('project')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')
    ledger_type = request.GET.get('ledger_type')  # Can be 'Purchase', 'Expense', or None/empty

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # 1. Establish project lists based on requirements mapping
    if is_valid(project_id):
        project_ids = [int(project_id)]
    else:
        project_ids = [36, 60]

    report_data = []

    for pid in project_ids:
        project = get_object_or_404(ProjectFirstLevelName, id=pid)
        
        # Enforce employee mapping constraint matching user specification
        target_employee_id = 24 if pid == 36 else (54 if pid == 60 else None)

        # Initialize storage containers for combined rows
        ledger_entries = []
        debit_total = Decimal('0.00')
        credit_total = Decimal('0.00')

        # ----------------------------------------------------
        # PROCESS ROUTE A: PURCHASE LEDGER DATA
        # ----------------------------------------------------
        if not ledger_type or ledger_type == 'Purchase':
            # Credits: Requisition Approvals
            approvals_qs = RestRequisitionApprovalHistory.objects.filter(project_name_id=pid)
            # if target_employee_id:
            #     approvals_qs = approvals_qs.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: approvals_qs = approvals_qs.filter(approved_date__date__gte=fd)
                if td: approvals_qs = approvals_qs.filter(approved_date__date__lte=td)

            for app in approvals_qs:
                app_date = app.approved_date
                if app_date and is_aware(app_date):
                    app_date = make_naive(app_date)

                credit_amt = app.total_amount or Decimal('0.00')
                credit_total += credit_amt
                ledger_entries.append({
                    'date': app_date,
                    'type': 'Purchase (Credit)',
                    'description': f"Req Approved ID: {app.requi_uniq_id or 'N/A'} | Status: {app.approv_acct_status or 'N/A'}",
                    'debit': Decimal('0.00'),
                    'credit': credit_amt,
                })

            # Debits: Daily Payments for Purchases
            payments_purchase = DailyPayment.objects.filter(project_id=pid, type='Purchase')
            if target_employee_id and hasattr(DailyPayment, 'employee_name'):
                payments_purchase = payments_purchase.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: payments_purchase = payments_purchase.filter(date__gte=fd)
                if td: payments_purchase = payments_purchase.filter(date__lte=td)

            for pay in payments_purchase:
                pay_datetime = datetime.combine(pay.date, datetime.min.time())
                debit_amt = pay.amount or Decimal('0.00')
                debit_total += debit_amt
                ledger_entries.append({
                    'date': pay_datetime,
                    'type': 'Purchase (Debit)',
                    'description': f"Daily Payment Ref: {pay.pay_id or 'N/A'} [Cash Type: {pay.cash_type or '-'}]",
                    'debit': debit_amt,
                    'credit': Decimal('0.00'),
                })

        # ----------------------------------------------------
        # PROCESS ROUTE B: EXPENSE LEDGER DATA
        # ----------------------------------------------------
        if not ledger_type or ledger_type == 'Expense':
            # Credits: Public Expenses
            expenses_qs = RestaurantPublicExpense.objects.filter(project_name_id=pid)
            # Note: If RestaurantPublicExpense has date/employee fields, filter them here. 
            # Given model outline, we track directly via model amount fields.

            for exp in expenses_qs:
                # Fallback to current time if expense lacks internal timestamp
                exp_datetime = datetime.combine(fd, datetime.min.time()) if fd else datetime.now()
                credit_amt = exp.restu_expense_amount or Decimal('0.00')
                credit_total += credit_amt
                ledger_entries.append({
                    'date': exp_datetime,
                    'type': 'Expense (Credit)',
                    'description': f"Public Expense: {exp.restu_expense_name} | Cat: {exp.restu_cate_name}",
                    'debit': Decimal('0.00'),
                    'credit': credit_amt,
                })

            # Debits: Daily Payments for Expenses
            payments_expense = DailyPayment.objects.filter(project_id=pid, type='Expense')
            if target_employee_id and hasattr(DailyPayment, 'employee_name'):
                payments_expense = payments_expense.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: payments_expense = payments_expense.filter(date__gte=fd)
                if td: payments_expense = payments_expense.filter(date__lte=td)

            for pay in payments_expense:
                pay_datetime = datetime.combine(pay.date, datetime.min.time())
                debit_amt = pay.amount or Decimal('0.00')
                debit_total += debit_amt
                ledger_entries.append({
                    'date': pay_datetime,
                    'type': 'Expense (Debit)',
                    'description': f"Daily Payment Ref: {pay.pay_id or 'N/A'} [Cash Type: {pay.cash_type or '-'}]",
                    'debit': debit_amt,
                    'credit': Decimal('0.00'),
                })

        # Sort the rows chronologically
        ledger_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)

        # Calculate chronological running balance structure matching your context style
        running_balance = Decimal('0.00')
        for entry in ledger_entries:
            running_balance += entry['credit'] - entry['debit']
            entry['running_balance'] = running_balance

        report_data.append({
            'project': project,
            'ledger_entries': ledger_entries,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'balance': credit_total - debit_total,
        })

    return render(
        request,
        'restaurant/requisitions/jewel_ledger_report.html',
        {
            'report_data': report_data,
            'selected_filters': {
                'project': project_id,
                'from_date': from_date,
                'to_date': to_date,
                'transaction': transaction_option,
                'ledger_type': ledger_type,
            },
            'print_time': datetime.now(),
        }
    )
    
    

# from decimal import Decimal
# from datetime import datetime
# from django.db.models import Sum
# from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.utils.timezone import make_naive, is_aware
# from num2words import num2words

# # Ensure your updated models are imported accurately
# # from .models import ProjectFirstLevelName, RestRequisitionApprovalHistory, DailyPayment

# @login_required
# def rest_jewel_ledger_manage_pdf(request):
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Base Filtering Projects
#     if is_valid(project_id):
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#     else:
#         # Gather projects with actual ledger logs across both tables if no specific filter is provided
#         approval_pids = list(RestRequisitionApprovalHistory.objects.values_list('project_name_id', flat=True).distinct())
#         payment_pids = list(DailyPayment.objects.values_list('project_id', flat=True).distinct())
#         all_pids = list(set(filter(None, approval_pids + payment_pids)))
#         projects = ProjectFirstLevelName.objects.filter(id__in=all_pids)

#     report_data = []
#     grand_debit_total = Decimal('0.00')
#     grand_credit_total = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'ledger_list': [],
#         }

#         # Query and isolate items matching current project scope
#         approvals = RestRequisitionApprovalHistory.objects.filter(project_name=project)
#         payments = DailyPayment.objects.filter(project=project)

#         if transaction_option == 'datewise':
#             if fd:
#                 approvals = approvals.filter(approved_date__date__gte=fd)
#                 payments = payments.filter(date__gte=fd)
#             if td:
#                 approvals = approvals.filter(approved_date__date__lte=td)
#                 payments = payments.filter(date__lte=td)

#         # Merge transactions chronologically into a single ledger list
#         ledger_entries = []

#         # Map Credit Rows (Approvals)
#         for app in approvals:
#             app_date = app.approved_date
#             if app_date and is_aware(app_date):
#                 app_date = make_naive(app_date)

#             ledger_entries.append({
#                 'date': app_date,
#                 'head': 'Requisition Approval',
#                 'account': 'Store/Purchase',
#                 'type_name': app.employee_name if app.employee_name else 'N/A',
#                 'description': f"Approved ID: {app.requi_uniq_id or 'N/A'} | Status: {app.approv_acct_status or 'N/A'}",
#                 'debit': Decimal('0.00'),
#                 'credit': app.total_amount or Decimal('0.00'),
#             })

#         # Map Debit Rows (Payments)
#         for pay in payments:
#             pay_datetime = datetime.combine(pay.date, datetime.min.time())
            
#             # Form account context mapping dynamically 
#             account_context = "-"
#             if pay.cash_type:
#                 account_context = str(pay.cash_type)
#             elif pay.sales_type:
#                 account_context = str(pay.sales_type)

#             ledger_entries.append({
#                 'date': pay_datetime,
#                 'head': pay.type or 'Payment Log',
#                 'account': account_context,
#                 'type_name': pay.rest_exp if pay.rest_exp else (pay.pur_cost if pay.pur_cost else 'General Entry'),
#                 'description': f"Pay ID: {pay.pay_id or 'N/A'}",
#                 'debit': pay.amount or Decimal('0.00'),
#                 'credit': Decimal('0.00'),
#             })

#         # Sort the compiled elements cleanly by Date
#         ledger_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)

#         # Calculate Running Balance metrics across structural rows
#         running_balance = Decimal('0.00')
#         for entry in ledger_entries:
#             # Formula setup: Credit (Received) - Debit (Payment) matches original balance calculations
#             running_balance += entry['credit'] - entry['debit']
#             entry['running_balance'] = running_balance

#         project_block['ledger_list'] = ledger_entries

#         # Aggregate total details per project item block
#         debit_total = sum(entry['debit'] for entry in ledger_entries)
#         credit_total = sum(entry['credit'] for entry in ledger_entries)
        
#         project_block['debit_total'] = debit_total
#         project_block['credit_total'] = credit_total
#         project_block['balance'] = credit_total - debit_total

#         grand_debit_total += debit_total
#         grand_credit_total += credit_total

#         report_data.append(project_block)

#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
#             words += " only"
#             if is_negative:
#                 words = "Minus " + words
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'grand_debit_total': grand_debit_total,
#         'grand_credit_total': grand_credit_total,
#         'grand_total_balance': grand_credit_total - grand_debit_total,
#         'grand_total_in_words': amount_to_words(grand_credit_total - grand_debit_total),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'restaurant/requisitions/rest_jewel_ledger_manage_pdf.html', context)


    
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_naive, is_aware
from num2words import num2words

# Ensure your models are accurately imported here
# from .models import ProjectFirstLevelName, RestRequisitionApprovalHistory, DailyPayment, RestaurantPublicExpense

@login_required
def rest_jewel_ledger_manage_pdf(request):
    project_id = request.GET.get('project')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')
    ledger_type = request.GET.get('ledger_type')  # 'Purchase', 'Expense', or None

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Base Filtering Projects
    if is_valid(project_id):
        projects = ProjectFirstLevelName.objects.filter(id=project_id)
    else:
        project_ids = [36, 60]
        projects = ProjectFirstLevelName.objects.filter(id__in=project_ids)

    report_data = []
    grand_debit_total = Decimal('0.00')
    grand_credit_total = Decimal('0.00')

    for project in projects:
        project_block = {
            'project': project,
            'ledger_list': [],
        }

        # Enforce static strict project employee ID rules matching specification constraints
        target_employee_id = 24 if project.id == 36 else (54 if project.id == 60 else None)
        ledger_entries = []

        # ----------------------------------------------------
        # ROUTE A: PURCHASE LEDGER QUERYING
        # ----------------------------------------------------
        if not ledger_type or ledger_type == 'Purchase':
            # Credits: Requisition Approvals
            approvals = RestRequisitionApprovalHistory.objects.filter(project_name=project)
            # if target_employee_id:
            #     approvals = approvals.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: approvals = approvals.filter(approved_date__date__gte=fd)
                if td: approvals = approvals.filter(approved_date__date__lte=td)

            for app in approvals:
                app_date = app.approved_date
                if app_date and is_aware(app_date):
                    app_date = make_naive(app_date)

                ledger_entries.append({
                    'date': app_date,
                    'head': 'Purchase (Credit)',
                    'account': 'Store/Purchase',
                    'type_name': app.employee_name.rda_emp_name if app.employee_name else 'N/A',
                    'description': f"Approved ID: {app.requi_uniq_id or 'N/A'} | Status: {app.approv_acct_status or 'N/A'}",
                    'debit': Decimal('0.00'),
                    'credit': app.total_amount or Decimal('0.00'),
                })

            # Debits: Daily Payments for Purchase
            payments_p = DailyPayment.objects.filter(project=project, type='Purchase')
            if target_employee_id and hasattr(DailyPayment, 'employee_name'):
                payments_p = payments_p.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: payments_p = payments_p.filter(date__gte=fd)
                if td: payments_p = payments_p.filter(date__lte=td)

            for pay in payments_p:
                pay_datetime = datetime.combine(pay.date, datetime.min.time())
                account_context = str(pay.cash_type) if pay.cash_type else (str(pay.sales_type) if pay.sales_type else "-")
                
                ledger_entries.append({
                    'date': pay_datetime,
                    'head': 'Purchase (Debit)',
                    'account': account_context,
                    'type_name': pay.pur_cost if getattr(pay, 'pur_cost', None) else 'General Entry',
                    'description': f"Pay ID: {pay.pay_id or 'N/A'}",
                    'debit': pay.amount or Decimal('0.00'),
                    'credit': Decimal('0.00'),
                })

        # ----------------------------------------------------
        # ROUTE B: EXPENSE LEDGER QUERYING
        # ----------------------------------------------------
        if not ledger_type or ledger_type == 'Expense':
            # Credits: Public Expense Table
            expenses = RestaurantPublicExpense.objects.filter(project_name=project)
            for exp in expenses:
                exp_datetime = datetime.combine(fd, datetime.min.time()) if fd else datetime.now()
                
                ledger_entries.append({
                    'date': exp_datetime,
                    'head': 'Expense (Credit)',
                    'account': 'Public/Expense',
                    'type_name': exp.restu_cate_name.name if hasattr(exp.restu_cate_name, 'name') else str(exp.restu_cate_name),
                    'description': f"Expense Item: {exp.restu_expense_name} | Type: {exp.restu_expense_type}",
                    'debit': Decimal('0.00'),
                    'credit': exp.restu_expense_amount or Decimal('0.00'),
                })

            # Debits: Daily Payments for Expense
            payments_e = DailyPayment.objects.filter(project=project, type='Expense')
            if target_employee_id and hasattr(DailyPayment, 'employee_name'):
                payments_e = payments_e.filter(employee_name_id=target_employee_id)
            if transaction_option == 'datewise':
                if fd: payments_e = payments_e.filter(date__gte=fd)
                if td: payments_e = payments_e.filter(date__lte=td)

            for pay in payments_e:
                pay_datetime = datetime.combine(pay.date, datetime.min.time())
                account_context = str(pay.cash_type) if pay.cash_type else (str(pay.sales_type) if pay.sales_type else "-")
                
                ledger_entries.append({
                    'date': pay_datetime,
                    'head': 'Expense (Debit)',
                    'account': account_context,
                    'type_name': pay.rest_exp if getattr(pay, 'rest_exp', None) else 'General Entry',
                    'description': f"Pay ID: {pay.pay_id or 'N/A'}",
                    'debit': pay.amount or Decimal('0.00'),
                    'credit': Decimal('0.00'),
                })

        # Sort all compiled ledger lines chronologically
        ledger_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)

        # Calculate chronological progressive running balances
        running_balance = Decimal('0.00')
        for entry in ledger_entries:
            running_balance += entry['credit'] - entry['debit']
            entry['running_balance'] = running_balance

        project_block['ledger_list'] = ledger_entries

        # Set up summaries per block
        debit_total = sum(entry['debit'] for entry in ledger_entries)
        credit_total = sum(entry['credit'] for entry in ledger_entries)
        
        project_block['debit_total'] = debit_total
        project_block['credit_total'] = credit_total
        project_block['balance'] = credit_total - debit_total

        grand_debit_total += debit_total
        grand_credit_total += credit_total

        report_data.append(project_block)

    def amount_to_words(amount):
        try:
            amount = float(amount)
            is_negative = amount < 0
            amount = abs(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en_IN').title().replace(",", "")
            words += " Taka"
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
            words += " only"
            if is_negative:
                words = "Minus " + words
            return words
        except:
            return f"{amount} Taka only"

    context = {
        'report_data': report_data,
        'grand_debit_total': grand_debit_total,
        'grand_credit_total': grand_credit_total,
        'grand_total_balance': grand_credit_total - grand_debit_total,
        'grand_total_in_words': amount_to_words(grand_credit_total - grand_debit_total),
        'selected_filters': {
            'project': project_id,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
            'ledger_type': ledger_type,
        },
        'print_time': datetime.now(),
    }

    return render(request, 'restaurant/requisitions/rest_jewel_ledger_manage_pdf.html', context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
# From .models import RestRequisitionApprovalHistory, RestRequisition

@login_required
def requisition_approval_history_details(request, history_id):
    # 1. Fetch the main history block via ID
    history = get_object_or_404(
        RestRequisitionApprovalHistory,
        id=history_id
    )

    # 2. Extract purchase reference string from that history token block to find related individual items
    requisitions = RestRequisition.objects.filter(
        purch_appov=history.purch_appov
    )

    return render(
        request,
        'restaurant/requisitions/requisition_history_details.html',
        {
            'history': history,
            'requisitions': requisitions
        }
    )
    
    

def requisition_jewel_purchase_list(request):

    histories = RestRequisitionApprovalHistory.objects.all().order_by('-id')

    return render(
        request,
        'restaurant/requisitions/requisition_jewel_purchase_list.html',
        {
            'histories': histories
        }
    )
    



from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import (
    RestRequisition,
    RestRequisitionApprovalHistory,
    RestInventories,
    RestaurantSupplier,
    RestaurantKitchenLedger,
)


# @login_required
# @transaction.atomic
# def edit_purch_requisition_jewel(request, purch_appov):
#     history_record = get_object_or_404(RestRequisitionApprovalHistory, purch_appov=purch_appov)
#     requisitions = RestRequisition.objects.filter(purch_appov=purch_appov)

#     if request.method == "POST":
#         running_grand_total = Decimal('0.00')

#         for item in requisitions:
#             qty_input = request.POST.get(f'qty_{item.id}', '0')
#             rate_input = request.POST.get(f'rate_{item.id}', '0')
#             discount_input = request.POST.get(f'discount_{item.id}', '0')
#             remark_input = request.POST.get(f'remark_{item.id}', '')
#             calc_mode = request.POST.get(f'calc_mode_{item.id}', 'normal')

#             try:
#                 qty = Decimal(qty_input)
#                 rate = Decimal(rate_input)
#                 discount = Decimal(discount_input)
#             except (ValueError, TypeError):
#                 qty = Decimal('0.00')
#                 rate = Decimal('0.00')
#                 discount = Decimal('0.00')

#             if calc_mode == "whole":
#                 calculated_amount = rate - discount
#             else:
#                 calculated_amount = (qty * rate) - discount

#             if calculated_amount < 0:
#                 calculated_amount = Decimal('0.00')

#             item.qty = qty
#             item.rate = rate
#             item.discount = discount
#             item.amount = calculated_amount
#             item.calc_mode = calc_mode
#             item.remark = remark_input
#             item.save()

#             running_grand_total += calculated_amount

#             supplier_instance = None
#             if item.vendor_name:
#                 supplier_instance = RestaurantSupplier.objects.filter(
#                     rest_supplier_name__iexact=item.vendor_name.strip()
#                 ).first()

#             RestInventories.objects.update_or_create(
#                 requi_id=item.id,
#                 defaults={
#                     'project_name': item.project_name,
#                     'employee_name': item.employee_name,
#                     'item_name': item.item_name,
#                     'vendor_name': supplier_instance,
#                     'unit': item.unit or '',
#                     'qty': int(qty),
#                     'rate': rate,
#                     'amount': calculated_amount,
#                     'remark': remark_input,
#                     'approv_note': item.approv_note,
#                     'approv_acct_note': item.approv_acct_note,
#                     'approv_purch_note': item.approv_purch_note,
#                     'requisition_date': item.requisition_date,
#                     'purch_id': item.purch_id,
#                     'purch_date': item.purch_date,
#                 }
#             )

#         history_record.total_amount = running_grand_total
#         history_record.save()

#         # ── Restaurant Kitchen Ledger sync (project-wise, single row, no duplicates) ──
#         first_item = requisitions.first()
#         if first_item and first_item.project_name and first_item.employee_name:
#             ledger_entry, created = RestaurantKitchenLedger.objects.update_or_create(
#                 type='Purchase',
#                 requisition=first_item,
#                 project=first_item.project_name,
#                 employee=first_item.employee_name,
#                 item_name=first_item.item_name,
#                 defaults={
#                     'debit': Decimal('0.00'),
#                     'credit': running_grand_total,
#                 }
#             )

#         messages.success(request, f"Requisition items and Inventory records for Reference {purch_appov} updated successfully.")
#         return redirect('requisition_jewel_purchase_list')

#     context = {
#         'history_record': history_record,
#         'requisitions': requisitions,
#         'purch_appov': purch_appov
#     }
#     return render(request, 'restaurant/requisitions/edit_purch_requisition_jewel.html', context)
    


from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

@login_required
@transaction.atomic
def edit_purch_requisition_jewel(request, purch_appov):
    history_record = get_object_or_404(RestRequisitionApprovalHistory, purch_appov=purch_appov)
    requisitions = RestRequisition.objects.filter(purch_appov=purch_appov)

    if request.method == "POST":
        running_grand_total = Decimal('0.00')

        for item in requisitions:
            qty_input = request.POST.get(f'qty_{item.id}', '0')
            rate_input = request.POST.get(f'rate_{item.id}', '0')
            discount_input = request.POST.get(f'discount_{item.id}', '0')
            remark_input = request.POST.get(f'remark_{item.id}', '')
            calc_mode = request.POST.get(f'calc_mode_{item.id}', 'unit')

            try:
                qty = Decimal(qty_input)
                rate = Decimal(rate_input)
                discount = Decimal(discount_input)
            except (ValueError, TypeError):
                qty = Decimal('0.00')
                rate = Decimal('0.00')
                discount = Decimal('0.00')

            if calc_mode == "whole":
                calculated_amount = rate - discount
            else:
                calculated_amount = (qty * rate) - discount

            if calculated_amount < 0:
                calculated_amount = Decimal('0.00')

            item.qty = qty
            item.rate = rate
            item.discount = discount
            item.amount = calculated_amount
            item.calc_mode = calc_mode
            item.remark = remark_input
            item.save()

            running_grand_total += calculated_amount

            supplier_instance = None
            if item.vendor_name:
                supplier_instance = RestaurantSupplier.objects.filter(
                    rest_supplier_name__iexact=item.vendor_name.strip()
                ).first()

            RestInventories.objects.update_or_create(
                requi_id=item.id,
                defaults={
                    'project_name': item.project_name,
                    'employee_name': item.employee_name,
                    'item_name': item.item_name,
                    'vendor_name': supplier_instance,
                    'unit': item.unit or '',
                    'qty': int(qty),
                    'rate': rate,
                    'amount': calculated_amount,
                    'remark': remark_input,
                    'approv_note': item.approv_note,
                    'approv_acct_note': item.approv_acct_note,
                    'approv_purch_note': item.approv_purch_note,
                    'requisition_date': item.requisition_date,
                    'purch_id': item.purch_id,
                    'purch_date': item.purch_date,
                }
            )

        history_record.total_amount = running_grand_total
        history_record.pur_verify='Yes'
        history_record.save()

        # Kitchen Ledger sync
        first_item = requisitions.first()
        if first_item and first_item.project_name and first_item.employee_name:
            RestaurantKitchenLedger.objects.update_or_create(
                type='Purchase',
                requisition=first_item,
                project=first_item.project_name,
                employee=first_item.employee_name,
                item_name=first_item.item_name,
                defaults={
                    'debit': Decimal('0.00'),
                    'credit': running_grand_total,
                }
            )

        messages.success(request, f"Requisition items and Inventory records for Reference {purch_appov} updated successfully.")
        return redirect('requisition_jewel_purchase_list')

    context = {
        'history_record': history_record,
        'requisitions': requisitions,
        'purch_appov': purch_appov
    }
    return render(request, 'restaurant/requisitions/edit_purch_requisition_jewel.html', context)
    
    

from decimal import Decimal
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def restaurant_kitchen_ledger_list(request):
    ledgers = (
        RestaurantKitchenLedger.objects.values(
            "type",
            "employee",
            "employee__rda_emp_name",
            "project",
            "project__project_first_name",
            "vendor_name",  # Added vendor foreign key
            "vendor_name__rest_supplier_name",  # Added supplier name
        )
        .annotate(
            total_credit=Coalesce(
                Sum("credit"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            total_debit=Coalesce(
                Sum("debit"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .annotate(
            balance=ExpressionWrapper(
                F("total_credit") - F("total_debit"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .order_by(
            "employee__rda_emp_name",
            "project__project_first_name",
            "vendor_name__rest_supplier_name",  # Optional: added to ordering
        )
    )

    return render(
        request,
        "restaurant/requisitions/restaurant_kitchen_ledger_list.html",
        {"ledgers": ledgers},
    )
    


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import RestaurantKitchenLedger


@login_required
def restaurant_kitchen_ledger_view(request, project_id):

    ledger_entries = (
        RestaurantKitchenLedger.objects
        .filter(project_id=project_id)
        .select_related(
            'project',
            'employee',
            'item_name',
            'requisition'
        )
        .order_by('-created_at')
    )

    return render(
        request,
        'restaurant/requisitions/kitchen_ledger_view.html',
        {
            'ledger_entries': ledger_entries,
        }
    )
    

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import RestInventories, ProjectFirstLevelName

@login_required
def rest_inventory_project_wise(request, project_id=None):
    # 1. Fetch only projects that actually exist in the inventory table to keep the filter menu clean
    active_project_ids = RestInventories.objects.values_list('project_name_id', flat=True).distinct()
    projects = ProjectFirstLevelName.objects.filter(id__in=active_project_ids)
    
    # Alternatively, if you want your specific restaurant filters like your list view:
    # projects = ProjectFirstLevelName.objects.filter(project_first_name__in=["The Galleria Restauent Cafe", "The Galleria Live Kitchen"])

    selected_project = None
    inventories = RestInventories.objects.none()
    grand_total_amount = 0
    total_items_count = 0

    if projects.exists():
        # If no project_id is provided in URL, fallback automatically to the first available project
        if not project_id:
            selected_project = projects.first()
        else:
            selected_project = projects.filter(id=project_id).first()

        if selected_project:
            # 2. Extract performance-optimized tracking datasets using select_related
            inventories = RestInventories.objects.filter(
                project_name=selected_project
            ).select_related('project_name', 'employee_name', 'item_name', 'vendor_name').order_by('-requisition_date', '-id')
            
            # Aggregate total metrics context
            grand_total_amount = inventories.aggregate(total=Sum('amount'))['total'] or 0
            total_items_count = inventories.aggregate(total_qty=Sum('qty'))['total_qty'] or 0

    context = {
        'projects': projects,
        'selected_project': selected_project,
        'inventories': inventories,
        'grand_total_amount': grand_total_amount,
        'total_items_count': total_items_count,
    }
    return render(request, 'restaurant/requisitions/project_wise_inventory.html', context)
    



    
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction

from .models import RestInventories, RestInventoryUse


@login_required
def requisition_deduct_inventory_stock(request, inventory_id):
    source_inventory = get_object_or_404(RestInventories, id=inventory_id)

    # Global total stock for this item at this branch/project
    total_stock_query = RestInventories.objects.filter(
        project_name=source_inventory.project_name,
        item_name=source_inventory.item_name
    ).aggregate(total=Sum('qty'))
    
    total_available_stock = total_stock_query['total'] or 0

    if request.method == "POST":
        deduct_qty_input = request.POST.get("deduct_qty", "0")
        details_input = request.POST.get("details", "")
        remark_input = request.POST.get("remark", "")

        try:
            deduct_qty = int(deduct_qty_input)

            if deduct_qty <= 0:
                raise ValidationError("Deduction quantity must be greater than zero.")

            if deduct_qty > total_available_stock:
                raise ValidationError(
                    f"Requested {deduct_qty} units, but only {total_available_stock} units are available in total branch stock."
                )

            with transaction.atomic():
                # Just create the log entry. The model's custom save() method 
                # will automatically handle the FIFO batch deductions!
                RestInventoryUse.objects.create(
                    project_name=source_inventory.project_name,
                    item_name=source_inventory.item_name,
                    qty=deduct_qty,
                    details=details_input,
                    remark=remark_input,
                )

            messages.success(
                request,
                f"{deduct_qty} {source_inventory.unit} deducted successfully via FIFO."
            )

            return redirect(
                "rest_inventory_project_wise_filtered",
                project_id=source_inventory.project_name.id,
            )

        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, 'message') else str(e))
        except ValueError:
            messages.error(request, "Please enter a valid numeric quantity.")
        except Exception as e:
            messages.error(request, f"System Error: {str(e)}")

    context = {
        "source_inventory": source_inventory,
        "available_qty": source_inventory.qty,
        "total_available_stock": total_available_stock,
    }

    return render(
        request,
        "restaurant/requisitions/requisition_deduct_inventory_stock.html",
        context,
    )
 




# from django.shortcuts import render, get_object_dict_or_404, redirect
# from django.contrib import messages
# from .models import ApprovalRange, RestaurantBudget
# from .forms import ApprovalRangeForm, RestaurantBudgetForm

# # ==========================================
# # APPROVAL RANGE CRUD
# # ==========================================
# @login_required
# def approval_range_list(request):
#     ranges = ApprovalRange.objects.select_related('user').all()
#     return render(request, 'restaurant/approval_range_list.html', {'ranges': ranges})

# @login_required
# def approval_range_create(request):
#     if request.method == "POST":
#         form = ApprovalRangeForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Approval Range created successfully!")
#             return redirect('approval_range_list')
#     else:
#         form = ApprovalRangeForm()
#     return render(request, 'restaurant/approval_range_form.html', {'form': form, 'title': 'Create Approval Range'})

# @login_required
# def approval_range_edit(request, pk):
#     instance = get_object_or_404(ApprovalRange, pk=pk)
#     if request.method == "POST":
#         form = ApprovalRangeForm(request.POST, instance=instance)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Approval Range updated successfully!")
#             return redirect('approval_range_list')
#     else:
#         form = ApprovalRangeForm(instance=instance)
#     return render(request, 'restaurant/approval_range_form.html', {'form': form, 'title': 'Edit Approval Range'})


# @login_required
# def approval_range_delete(request, pk):
#     instance = get_object_or_404(ApprovalRange, pk=pk)
#     if request.method == "POST":
#         instance.delete()
#         messages.success(request, "Approval Range deleted successfully!")
#         return redirect('approval_range_list')
#     return render(request, 'restaurant/confirm_delete.html', {'object': instance, 'cancel_url': 'approval_range_list'})


# # ==========================================
# # RESTAURANT BUDGET CRUD
# # ==========================================
# @login_required
# def budget_list(request):
#     budgets = RestaurantBudget.objects.select_related('category').all()
#     return render(request, 'restaurant/budget_list.html', {'budgets': budgets})

# @login_required
# def budget_create(request):
#     if request.method == "POST":
#         form = RestaurantBudgetForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Budget target created successfully!")
#             return redirect('budget_list')
#     else:
#         form = RestaurantBudgetForm()
#     return render(request, 'restaurant/budget_form.html', {'form': form, 'title': 'Create Restaurant Budget'})

# @login_required
# def budget_edit(request, pk):
#     instance = get_object_or_404(RestaurantBudget, pk=pk)
#     if request.method == "POST":
#         form = RestaurantBudgetForm(request.POST, instance=instance)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Budget target updated successfully!")
#             return redirect('budget_list')
#     else:
#         form = RestaurantBudgetForm(instance=instance)
#     return render(request, 'restaurant/budget_form.html', {'form': form, 'title': 'Edit Restaurant Budget'})


# @login_required
# def budget_delete(request, pk):
#     instance = get_object_or_404(RestaurantBudget, pk=pk)
#     if request.method == "POST":
#         instance.delete()
#         messages.success(request, "Budget allocated record deleted successfully!")
#         return redirect('budget_list')
#     return render(request, 'restaurant/confirm_delete.html', {'object': instance, 'cancel_url': 'budget_list'})