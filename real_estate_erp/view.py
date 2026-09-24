# from django.shortcuts import render, redirect, get_object_or_404
# from .models import BOQ
# from .forms import BOQForm
# from django.contrib import messages

# # List all BOQ items
# def boq_list(request):
#     boqs = BOQ.objects.all()  # Retrieve all BOQ items from the database
#     return render(request, 'boq_list.html', {'boqs': boqs})

# # Create a new BOQ item
# def boq_create(request):
#     if request.method == 'POST':
#         form = BOQForm(request.POST)
#         if form.is_valid():
#             form.save()  # Save the new BOQ item
#             messages.success(request, 'BOQ item added successfully!')
#             return redirect('boq_list')  # Redirect to the BOQ list page
#     else:
#         form = BOQForm()
    
#     return render(request, 'boq/boq_form.html', {'form': form})

# # Edit an existing BOQ item
# def boq_edit(request, pk):
#     boq = get_object_or_404(BOQ, pk=pk)
#     if request.method == 'POST':
#         form = BOQForm(request.POST, instance=boq)
#         if form.is_valid():
#             form.save()  # Update the BOQ item
#             messages.success(request, 'BOQ item updated successfully!')
#             return redirect('boq_list')  # Redirect to the BOQ list page
#     else:
#         form = BOQForm(instance=boq)
    
#     return render(request, 'boq/boq_form.html', {'form': form, 'boq': boq})

# # Delete a BOQ item
# def boq_delete(request, pk):
#     boq = get_object_or_404(BOQ, pk=pk)
#     if request.method == 'POST':
#         boq.delete()  # Delete the BOQ item
#         messages.success(request, 'BOQ item deleted successfully!')
#         return redirect('boq_list')  # Redirect to the BOQ list page
    
#     return render(request, 'boq/boq_confirm_delete.html', {'boq': boq})



























































































































































from django.shortcuts import render
from django.db.models import Count, Sum, Q
from purchase.models import *
from sales.models import *
from inventories.models import *
from properties.models import *
from hrm.models import *
from accounting.models import *
from restaccounting.models import *

def requisition_dashboard(request):

    # ================= EXISTING =================
    summary = Requisition.objects.aggregate(
        total_req=Count('id'),
        total_pending=Count('id', filter=Q(approv_status='pending')),
        total_approved=Count('id', filter=Q(approv_status='approved')),
        total_amount=Sum('amount'),
    )

    top_projects = Requisition.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    top_suppliers = Requisition.objects.values('vendor_name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    pending_suppliers = Requisition.objects.values('vendor_name').annotate(
        pending=Count('id', filter=Q(approv_status='pending'))
    ).order_by('-pending')[:5]


    # ================= NEW: PURCHASE (Inventories) =================
    purchase_summary = Inventories.objects.aggregate(
        total_purchase=Sum('amount')
    )

    purchase_project = Inventories.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    purchase_supplier = Inventories.objects.values(
        'vendor_name__supplier_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    # ================= NEW: EXPENSE =================
    expense_summary = ExpenseRequisition.objects.aggregate(
        total_expense=Sum('amount')
    )

    expense_project = ExpenseRequisition.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    expense_supplier = ExpenseRequisition.objects.values(
        'employee_name__emp_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]

    # ================= NEW: PROPERTIES =================
    property_summary = PropertyFlatPlot.objects.aggregate(
        total_property=Count('id'),
        total_value=Sum('total_amount')
    )

    property_project = PropertyFlatPlot.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_units=Count('id'),
        total_value=Sum('total_amount')
    ).order_by('-total_value')[:5]







    # ================= NEW: UNIT (AVAILABLE vs SOLD) =================
    unit_summary = PropertySales.objects.aggregate(
        total_sold=Count('id', filter=Q(status='sold')),
        total_available=Count('id', filter=Q(status='available'))
    )

    unit_project = PropertySales.objects.values(
        'project_name__project_first_name'
    ).annotate(
        sold=Count('id', filter=Q(status='sold')),
        available=Count('id', filter=Q(status='available'))
    )


    # ================= NEW: REVENUE =================
    revenue_summary = PropertySales.objects.aggregate(
        total_revenue=Sum('total_amount')
    )

    revenue_project = PropertySales.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_revenue=Sum('total_amount')
    ).order_by('-total_revenue')[:5]


    # ================= NEW: CUSTOMER =================
    customer_summary = Customer.objects.aggregate(
        total_customer=Count('id')
    )

    customer_project = Customer.objects.values(
        'project__project_first_name'
    ).annotate(
        total_customer=Count('id')
    ).order_by('-total_customer')[:5]


    # ================= NEW: RECEIVED (Credit) =================
    received_summary = CreditVoucher.objects.aggregate(
        total_received=Sum('amount')
    )

    received_project = CreditVoucher.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_received=Sum('amount')
    ).order_by('-total_received')[:5]


    # ================= NEW: PAYMENT (Debit) =================
    payment_summary = DebitVoucher.objects.aggregate(
        total_payment=Sum('amount')
    )

    payment_project = DebitVoucher.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_payment=Sum('amount')
    ).order_by('-total_payment')[:5]


    # ================= RESTAURANT =================

    # 1️⃣ Total Daily Collection (Project wise)
    rest_collection_summary = Collection.objects.aggregate(
        total_collection=Sum('amount')
    )

    rest_collection_project = Collection.objects.values(
        'project__project_first_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]


    # 2️⃣ Total Daily Payment (Project wise)
    rest_payment_summary = DailyPayment.objects.aggregate(
        total_payment=Sum('amount')
    )

    rest_payment_project = DailyPayment.objects.values(
        'project__project_first_name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:5]


    # 3️⃣ Total Received (CreditRestVoucher)
    rest_received_summary = CreditRestVoucher.objects.aggregate(
        total_received=Sum('amount')
    )

    rest_received_project = CreditRestVoucher.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_received=Sum('amount')
    ).order_by('-total_received')[:5]


    # 4️⃣ Total Payment (DebitRestVoucher)
    rest_debit_summary = DebitRestVoucher.objects.aggregate(
        total_payment=Sum('amount')
    )

    rest_debit_project = DebitRestVoucher.objects.values(
        'project_name__project_first_name'
    ).annotate(
        total_payment=Sum('amount')
    ).order_by('-total_payment')[:5]


    # ================= FINAL CONTEXT =================
    return render(request, 'x.html', {
        # old
        'summary': summary,
        'top_projects': top_projects,
        'top_suppliers': top_suppliers,
        'pending_suppliers': pending_suppliers,

        # purchase
        'purchase_summary': purchase_summary,
        'purchase_project': purchase_project,
        'purchase_supplier': purchase_supplier,

        # expense
        'expense_summary': expense_summary,
        'expense_project': expense_project,
        'expense_supplier': expense_supplier,

        # property
        'property_summary': property_summary,
        'property_project': property_project,


        # ===== NEW =====
        'unit_summary': unit_summary,
        'unit_project': unit_project,

        'revenue_summary': revenue_summary,
        'revenue_project': revenue_project,

        'customer_summary': customer_summary,
        'customer_project': customer_project,

        'received_summary': received_summary,
        'received_project': received_project,

        'payment_summary': payment_summary,
        'payment_project': payment_project,

        # restaurant
        'rest_collection_summary': rest_collection_summary,
        'rest_collection_project': rest_collection_project,

        'rest_payment_summary': rest_payment_summary,
        'rest_payment_project': rest_payment_project,

        'rest_received_summary': rest_received_summary,
        'rest_received_project': rest_received_project,

        'rest_debit_summary': rest_debit_summary,
        'rest_debit_project': rest_debit_project,

    })