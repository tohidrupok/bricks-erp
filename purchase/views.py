from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.shortcuts import render
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse
from .models import Notification,Requisition,HeadOfRequisition,Notification,RequisitionComparative,HeadOfExpense,ExpenseVoucher,PettyCash,ExpenseRequisition,BillRequisition,RequisitionApprovalPayment,RequisitionApprovalPayment
from .forms import RequisitionForm,HeadOfRequisitionForm,RequisitionCategory,RequisitionCategoryForm,RequisitionComparativeForm,HeadOfExpenseForm,ExpenseVoucherForm,PettyCashForm,ExpenseRequisitionForm,BillRequisitionForm,RequisitionApprovalPaymentForm
from django.db.models import Sum
from projects.models import ProjectFirstLevelName,Suppliers,SiteSupervisor,BOQ,BoQCategory
from projects.forms import ProjectFirstLevelName
from inventories.models import Inventories
from inventories.forms import InventoriesForm
from hrm.models import Employee
from django.contrib import messages
import logging,traceback, json
from .models import Notification
from django.contrib.auth.models import User
from accounting.models import DebitVoucher,CashType, TransactionHistory,CreditVoucher,MainChequeBook,MainCheque,HeadOfAccount,LedgerEntry
from django.utils import timezone
from django.db.models import Q
from collections import defaultdict
from django.utils.timezone import now
from django.db import transaction
import time
from django.db.models import Sum
from num2words import num2words
from datetime import datetime 
from django.utils import timezone
from decimal import Decimal
from django.db.models import Min, Max
from django.utils.dateparse import parse_date
import json
from django.utils.dateformat import DateFormat
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet



## firebase code----

from .models import FCMDevice

@csrf_exempt
def save_fcm_token(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")
        if request.user.is_authenticated and token:
            FCMDevice.objects.update_or_create(
                user=request.user, defaults={"token": token}
            )
            return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid request"}, status=400)
    
    

import logging
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)

@login_required 
def requisition_list(request):
    username = request.user.username

    projects_first = ProjectFirstLevelName.objects.all()
    conductors = SiteSupervisor.objects.all()
    suppliers = Suppliers.objects.all()

    requisitions = (
        Requisition.objects
        .filter(return_requisition__isnull=True)
        .select_related('project_name', 'employee_name')
        .order_by('-id')
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

    for uniq_id, items in uniq_id_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]
        vendor_names = list(set(item.vendor_name for item in items if item.vendor_name))

        status = "Approved" if all(item.approv_status == 'approved' for item in items) else "Pending"

        grouped_data.append({
            'group_type': 'uniq_id',
            'requi_uniq_id': uniq_id,
            'requisition_date': latest_req.requisition_date,
            'project_name': latest_req.project_name,
            'total_amount': total_amount,
            'project_id': latest_req.project_name.id,
            'vendor_names': vendor_names,
            'status': status,
        })

    for project, items in project_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]
        vendor_names = list(set(item.vendor_name for item in items if item.vendor_name))

        status = "Approved" if all(item.approv_status == 'approved' for item in items) else "Pending"

        grouped_data.append({
            'group_type': 'project',
            'requi_uniq_id': None,
            'requisition_date': latest_req.requisition_date,
            'project_name': project,
            'total_amount': total_amount,
            'project_id': project.id,
            'vendor_names': vendor_names,
            'status': status,
            'employee_names': list(set(req.employee_name.employee_name for req in items)),
        })

    # ------------------------------------------------
    # 🔥 SORT so PENDING rows come first in the table
    # ------------------------------------------------
    grouped_data = sorted(grouped_data, key=lambda x: 0 if x['status']=="Pending" else 1)

    if username == 'admin':
        employees = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employees = Employee.objects.filter(emp_name=username)

    context = {
        'grouped_data': grouped_data,
        'projects_firts': projects_first,
        'employees': employees,
        'suppliers': suppliers,
        'conductors': conductors,
    }

    return render(request, 'requisitions/requisition_list.html', context)

    
    
# @login_required
# def bill_requisition_list(request):
#     username = request.user.username

#     projects_first = ProjectFirstLevelName.objects.all()
#     conductors = SiteSupervisor.objects.all()
#     suppliers = Suppliers.objects.all()

#     requisitions = (
#         BillRequisition.objects
#         .filter(return_requisition__isnull=True)
#         .select_related('project_name', 'employee_name')
#         .order_by('-id')
#     )

#     # Group by vendor name
#     vendor_map = defaultdict(list)
#     for req in requisitions:
#         if req.vendor_name:
#             vendor_map[req.vendor_name].append(req)

#     grouped_data = []

#     for vendor, items in vendor_map.items():
#         total_amount = sum(item.amount for item in items if item.amount)
#         latest_req = items[0]

#         # Status logic: if all items are approved, status is "Approved", else "Pending"
#         if all(item.approv_status == 'approved' for item in items):
#             status = "Approved"
#         else:
#             status = "Pending"
        
#         grouped_data.append({
#             'vendor_name': vendor,
#             'total_amount': total_amount,
#             'latest_requisition_date': latest_req.requisition_date,
#             'project_names': list(set(req.project_name for req in items if req.project_name)),
#             'employee_names': list(set(req.employee_name.employee_name for req in items if req.employee_name)),
#             'status': status,
#             'requi_uniq_id': latest_req.requi_uniq_id,   # ✅ add this
#         })

#     # Employee filtering
#     if username == 'admin':
#         employees = Employee.objects.exclude(emp_type__iexact='admin')
#     else:
#         employees = Employee.objects.filter(emp_name=username)

#     context = {
#         'grouped_data': grouped_data,
#         'projects_firts': projects_first,
#         'employees': employees,
#         'suppliers': suppliers,
#         'conductors': conductors,
#     }

#     return render(request, 'billrequisitions/bill_requisition_list.html', context)
    


@login_required
def bill_requisition_list(request):
    username = request.user.username

    projects_first = ProjectFirstLevelName.objects.all()
    conductors = SiteSupervisor.objects.all()
    suppliers = Suppliers.objects.all()

    requisitions = (
        BillRequisition.objects
        .filter(return_requisition__isnull=True)
        .select_related('project_name', 'employee_name')
        .order_by('-id')
    )

    # Group by a composite key of (requi_uniq_id, vendor_name, project_name) 
    # or keep unique approval IDs separate from vendor-only fallbacks
    grouped_map = defaultdict(list)
    for req in requisitions:
        # Use requi_uniq_id if present, otherwise group by project and vendor name
        group_key = (req.requi_uniq_id, req.vendor_name, req.project_name_id if req.project_name else None)
        grouped_map[group_key].append(req)

    grouped_data = []

    for key, items in grouped_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]

        # Status logic: if all items are approved, status is "Approved", else "Pending"
        if all(item.approv_status == 'approved' for item in items):
            status = "Approved"
        else:
            status = "Pending"
         
        grouped_data.append({
            'vendor_name': latest_req.vendor_name,
            'total_amount': total_amount,
            'latest_requisition_date': latest_req.requisition_date,
            'project_names': [latest_req.project_name] if latest_req.project_name else [],
            'employee_names': list(set(req.employee_name.employee_name for req in items if req.employee_name)),
            'status': status,
            'requi_uniq_id': latest_req.requi_uniq_id,
            'project_id': latest_req.project_name.id if latest_req.project_name else None,
        })

    # Employee filtering
    if username == 'admin':
        employees = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employees = Employee.objects.filter(emp_name=username)

    context = {
        'grouped_data': grouped_data,
        'projects_firts': projects_first,
        'employees': employees,
        'suppliers': suppliers,
        'conductors': conductors,
    }

    return render(request, 'billrequisitions/bill_requisition_list.html', context)


@login_required
def requisition_by_project(request, requi_id):
    requisitions = Requisition.objects.filter(requi_uniq_id=requi_id)
    
    project = None
    if requisitions.exists():
        project = requisitions.first().project_name  # Assuming project_name is a FK

    context = {
        'requisitions': requisitions,
        'project': project,
    }
    return render(request, 'requisitions/requisition_by_rqui.html', context)



@login_required
def requisition_by_fallback(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Get filters from GET parameters
    requisition_date_str = request.GET.get('requisition_date')
    vendor_names_str = request.GET.get('vendor_name', '')  # comma separated vendors

    # Base queryset: requi_uniq_id null and approv_status NOT approved
    requisitions = Requisition.objects.filter(
        project_name=project,
        requi_uniq_id__isnull=True,
    ).exclude(approv_status='approved')

    # Filter by requisition_date if provided and valid
    if requisition_date_str:
        try:
            requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date=requisition_date)
        except ValueError:
            # Invalid date format, ignore filter
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
    return render(request, 'requisitions/requisition_by_project.html', context)

    
    

@login_required
def petty_cash_list(request):
    projects_first = ProjectFirstLevelName.objects.all()
    username = request.user.username

    try:
        current_employee = Employee.objects.get(emp_name=username)
        emp_type = current_employee.emp_type.strip().lower()
    except Employee.DoesNotExist:
        current_employee = None
        emp_type = ''

    # âœ… Removed invalid filter
    pettycashs = PettyCash.objects.all().order_by('-id')

    if username == 'admin':
        employees = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employees = Employee.objects.filter(emp_name=username)
    
    context = {
        'pettycashs': pettycashs,
        'projects_firts': projects_first,
        'employees': employees,
    }
    return render(request, 'pettycash/petty_cash_list.html', context)



@login_required
def pettycash_item_summary(request):
    project_id = request.GET.get('project_id')
    status = request.GET.get('status')
    reqiDate = request.GET.get('reqiDate')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
    requisition_filter = Q(project_name=project)

    # âœ… Filter by status (if given)
    if status and status.lower() in ['pending', 'approved', 'rejected']:
        requisition_filter &= Q(approv_status__iexact=status)

    # âœ… Filter by date (if given)
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
            requisition_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

    # âœ… Query PettyCash model instead of Requisition
    requisition_items = PettyCash.objects.filter(requisition_filter).order_by('id')

    total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
    requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None
    employee_name = None
    if requisition_items.exists():
        employee_name = requisition_items.first().employee_name.employee_name
        
    def amount_to_words(amount):
        amount = round(float(amount), 2)
        taka = int(amount)
        poisha = int(round((amount - taka) * 100))

        taka_words = num2words(taka, lang='en').capitalize() + " Taka"

        if poisha > 0:
            poisha_words = num2words(poisha, lang='en') + " Poisha"
            return f"{taka_words} and {poisha_words}"
        else:
            return f"{taka_words}"

    context = {
        'project': project,
        'requisition_items': requisition_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
        'requisition_date': requisition_date,
        'employee_name': employee_name,
    }

    return render(request, 'pettycash/pettycash_item_summary.html', context)



@login_required
def pettycash_acct_confirmation(request):
    project_id = request.GET.get('project_id')
    pettyDate = request.GET.get('pettyDate', '').strip()

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Base filter
    base_filter = Q(project_name=project, approv_status='pending', approv_acct_status='pending')
    
    if pettyDate:
        try:
            parsed_date = datetime.strptime(pettyDate, "%Y-%m-%d").date()
            base_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return redirect(f"{request.path}?project_id={project.id}")

    reference_requisition = PettyCash.objects.filter(base_filter).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approv_acct_status = request.POST.get("approv_acct_status")
        approv_acct_note = request.POST.get("approv_acct_note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(f"{request.path}?project_id={project.id}")

        if not approv_acct_status:
            messages.error(request, "Please select an approval status.")
            return redirect(f"{request.path}?project_id={project.id}")

        try:
            unique_purch_id = int(time.time())
            updated_items = PettyCash.objects.filter(id__in=selected_ids)
            for item in updated_items:
                item.approv_acct_status = approv_acct_status
                item.approv_acct_note = approv_acct_note
                item.requi_uniq_id = unique_purch_id
                item.save()

            messages.success(request, "Selected items updated successfully.")
            return redirect("petty_cash_list")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(f"{request.path}?project_id={project.id}")

    # âœ… Get distinct employee IDs for this project and optional date
    employee_ids = PettyCash.objects.filter(base_filter).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}
    for emp_id in employee_ids:
        requisitions = PettyCash.objects.filter(base_filter & Q(employee_name=emp_id))
        employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        employee_obj = requisitions.first().employee_name if requisitions.exists() else None
        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = PettyCash.objects.filter(base_filter).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'pettycash/pettycash_acct_confirmation.html', {
        'project': project,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
        'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
    })




@login_required
def admin_confirmation(request):
    project_id = request.GET.get('project_id')
    pettyDate = request.GET.get('pettyDate', '').strip()

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Base filters
    base_filter = Q(project_name=project, approv_acct_status='approved', approv_status='pending')

    if pettyDate:
        try:
            parsed_date = datetime.strptime(pettyDate, "%Y-%m-%d").date()
            base_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return redirect(request.path + f"?project_id={project.id}")

    reference_requisition = PettyCash.objects.filter(base_filter).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status")
        note = request.POST.get("note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        notified_users = set()

        try:
            for item_id in selected_ids:
                try:
                    item = PettyCash.objects.get(id=item_id)
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.save()

                    # Notify employee
                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:
                        pass

                except PettyCash.DoesNotExist:
                    continue

            # Notify employees
            for user in notified_users:
                Notification.objects.create(
                    sender=request.user,
                    recipient=user,
                    project_name=project,
                    message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
                    is_read=False,
                    link='',
                    pass_url='requisition_admin_confirm',
                    role='admin'
                )

            messages.success(request, "Selected items updated and notifications sent successfully.")
            return redirect("petty_cash_list")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # Group requisitions by employee
    employee_ids = PettyCash.objects.filter(base_filter).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}
    for emp_id in employee_ids:
        requisitions = PettyCash.objects.filter(base_filter & Q(employee_name=emp_id))
        employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        employee_obj = requisitions.first().employee_name if requisitions.exists() else None
        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = PettyCash.objects.filter(base_filter).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'pettycash/pettycash_confirmation.html', {
        'project': project,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })


@login_required
def pettycash_edit(request, pk):
    requisition = get_object_or_404(PettyCash, pk=pk)

    if request.method == 'POST':
        form = PettyCashForm(request.POST, instance=requisition)
        if form.is_valid():
            updated = form.save(commit=False)

            # Only allow changing status if not already approved
            if requisition.approv_status != 'approved':
                updated.approv_status = request.POST.get('approv_status')
                updated.approv_note = request.POST.get('approv_note')

            updated.save()
            messages.success(request, 'Requisition updated successfully.')
            return redirect('petty_cash_list')
    else:
        form = PettyCashForm(instance=requisition)

    context = {
        'form': form,
        'project_list': ProjectFirstLevelName.objects.all(),
        'employee_names': Employee.objects.all(),
        'requisition_list': HeadOfRequisition.objects.all(),
        'supplier_list': Suppliers.objects.all(),
        'contructor_list': SiteSupervisor.objects.all(),
    }
    return render(request, 'pettycash/pettycash_edit.html', context)



@login_required
def pettycash_detail(request, pk):  
    requisition = get_object_or_404(PettyCash, pk=pk)
    project = requisition.project_name
    
    return render(request, 'pettycash/pettycash_details.html', {
        'project': project,
        'requisition': requisition,
    })


@login_required
def pettycash_delete(request, pk):
    requisition = get_object_or_404(PettyCash, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('petty_cash_list')
    return render(request, 'pettycash/pettycash_delete.html', {'requisition': requisition})



@login_required
def purchase_list(request):
    requi_ids = (
        Requisition.objects
        .filter(approv_acct_status='approved')
        .order_by('-requi_uniq_id')
        .values_list('requi_uniq_id', flat=True)
        .distinct()
    )

    grouped_data = []

    for pid in requi_ids:
        items = (
            Requisition.objects
            .filter(requi_uniq_id=pid, approv_acct_status='approved')
            .select_related('project_name', 'employee_name')
            .order_by('-id')
        )

        if not items.exists():
            continue

        first_item = items.first()
        total_amount = sum(item.amount for item in items if item.amount)

        grouped_data.append({
            'requi_uniq_id': first_item.requi_uniq_id,
            'requi_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'employee_name': first_item.employee_name,
            'vendor_name': first_item.vendor_name,
            'total_amount': total_amount,
            'items': items,
            'purch_appov': first_item.purch_appov,
            'purch_id': first_item.purch_id,
        })

    context = {
        'grouped_data': grouped_data,
        'projects_firts': ProjectFirstLevelName.objects.all(),
    }

    return render(request, 'requisitions/purchase_head_cash.html', context)


# @login_required
# def purchase_check_details(request, requi_id, purch_id):
#     requisitions = Requisition.objects.filter(requi_uniq_id=requi_id)
#     inventories = Inventories.objects.filter(purch_id=purch_id)
    
#     if not requisitions.exists():
#         raise Http404("No requisition found.")
   
#     first_req = requisitions.first()

#     return render(request, 'requisitions/purchase_check_details.html', {
#         'requisitions': requisitions,
#         'requisition': first_req,  # for single display
#         'inventories': inventories,
#         'purch_id': purch_id,
#         'requi_uniq_id': requi_id,
#     })





@login_required
def purchase_check_details(request, requi_id, purch_id):
    requisitions = Requisition.objects.filter(requi_uniq_id=requi_id)
    inventories = Inventories.objects.filter(purch_id=purch_id)

    if not requisitions.exists():
        raise Http404("No requisition found.")

    first_req = requisitions.first()

    # Calculate totals
    req_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
    inv_total = inventories.aggregate(total=Sum('amount'))['total'] or 0
    difference = req_total - inv_total

    return render(request, 'requisitions/purchase_check_details.html', {
        'requisitions': requisitions,
        'requisition': first_req,
        'inventories': inventories,
        'purch_id': purch_id,
        'requi_uniq_id': requi_id,
        'req_total': req_total,
        'inv_total': inv_total,
        'difference': difference,
    })





@login_required
def purchase_repurchase(request, requi_id, purch_id):
    suppliers = Suppliers.objects.all()
    requisitions = Requisition.objects.filter(
        requi_uniq_id=requi_id
    ).filter(
        purch_appov__isnull=True
    ) | Requisition.objects.filter(
        requi_uniq_id=requi_id,
        purch_appov__iexact='No Purchase'
    )

    requisitions = requisitions.order_by('id')

    context = {
        'requisitions': requisitions,
        'requi_uniq_id': requi_id,
        'purch_id': purch_id,
        'suppliers': suppliers
    }
    return render(request, 'requisitions/repurchase.html', context)


@login_required
def purchase_repurchase_save(request, requi_id):
    if request.method == "POST":
        counter = 1
        updated_items = []

        while True:
            row_id = request.POST.get(f"id_{counter}")
            if not row_id:
                break  # No more rows

            try:
                item = Requisition.objects.get(id=row_id)
            except Requisition.DoesNotExist:
                counter += 1
                continue

            purch_id_raw = request.POST.get(f"purch_id_{counter}", "").strip()
            vendor_name = request.POST.get(f"vendor_name_{counter}", "").strip()
            qty_raw = request.POST.get(f"qty_{counter}")
            rate_raw = request.POST.get(f"rate_{counter}")

            try:
                qty = float(qty_raw) if qty_raw else item.qty
            except ValueError:
                qty = item.qty

            try:
                rate = float(rate_raw) if rate_raw else item.rate
            except ValueError:
                rate = item.rate

            try:
                purch_id = int(purch_id_raw) if purch_id_raw else 0
            except ValueError:
                purch_id = 0
            
            item.purch_id = purch_id
            item.purch_appov = "Wait"
            item.purch_date = timezone.now().date()
            item.save()
            updated_items.append(item)

            # Insert into inventories table
            try:
                vendor_obj = Suppliers.objects.get(supplier_name=vendor_name)
            except Suppliers.DoesNotExist:
                vendor_obj = None

            Inventories.objects.create(
                project_name=item.project_name,
                employee_name=item.employee_name,
                vendor_name=vendor_obj,
                item_name=item.item_name,
                unit=item.unit,
                qty=qty,
                rate=rate,
                amount=qty * rate,
                remark=item.remark,
                approv_note=item.approv_note,
                approv_acct_note=item.approv_acct_note,
                approv_purch_note=item.approv_purch_note,
                requisition_date=item.requisition_date,
                requi_id=item.id,
                qtysub=qty,
                purch_id=purch_id,
                purch_date=timezone.now().date()
            )

            counter += 1

        messages.success(request, f"{len(updated_items)} items updated successfully.")
        return redirect("purchase_list")
    else:
        messages.error(request, "Invalid request method.")
        return redirect("purchase_list")



@login_required
def purchase_approval_action(request, requi_id, purch_id):
    if request.method == 'POST':
        requisitions = Requisition.objects.filter(requi_uniq_id=requi_id, purch_id=purch_id)

        if not requisitions.exists():
            messages.error(request, "No requisition items found to approve.")
            return redirect('purchase_list')

        requisitions.update(purch_appov='Yes')
        messages.success(request, f"All requisition rows approved for Requisition ID {requi_id}.")

        return redirect('purchase_check_details', requi_id=requi_id, purch_id=purch_id)
    else:
        messages.error(request, "Invalid request method.")
        return redirect('purchase_list')
    



# @login_required
# def purchase_check_details(request, requi_id, purch_id):
#     requisition = get_object_or_404(Requisition, requi_uniq_id=requi_id)
#     inventories = Inventories.objects.filter(purch_id=purch_id)

#     return render(request, 'requisitions/purchase_check_details.html', {
#         'requisition': requisition,
#         'inventories': inventories,
#         'purch_id': purch_id,
#     })



## ok code is ----
# @login_required
# def purchase_list(request):
#     purch_ids = (
#         Requisition.objects
#         .filter(approv_acct_status='approved')
#         .order_by('-requi_uniq_id')
#         .values_list('requi_uniq_id', flat=True)
#         .distinct()
#     )

#     grouped_data = []

#     for pid in purch_ids:
#         items = (
#             Requisition.objects
#             .filter(requi_uniq_id=pid, approv_acct_status='approved')
#             .select_related('project_name', 'employee_name') 
#             .order_by('-id')
#         )

#         if not items.exists():
#             continue

#         first_item = items.first()
#         total_amount = sum(item.amount for item in items if item.amount)

#         grouped_data.append({
#             'requi_uniq_id': first_item.requi_uniq_id,
#             'purch_id': pid,
#             'project_name': first_item.project_name,
#             'requisition_date': first_item.requisition_date,
#             'employee_name': first_item.employee_name,
#             'vendor_name': first_item.vendor_name,  
#             'total_amount': total_amount,
#             'items': items,
#         })

#     context = {
#         'grouped_data': grouped_data,
#         'projects_firts': ProjectFirstLevelName.objects.all(),
#     }

#     return render(request, 'requisitions/purchase_head_cash.html', context)





# @login_required
# def purchase_cash_details(request, pk):
#     requisitions = Requisition.objects.filter(requi_uniq_id=pk)
#     total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#     amount_in_words = num2words(total_amount, lang='en').title()

#     first_item = requisitions.first()
#     cash_rec_name = ""

#     if first_item and first_item.cash_empl:
#         try:
#             emp = Employee.objects.get(id=first_item.cash_empl)
#             cash_rec_name = emp.employee_name
#         except Employee.DoesNotExist:
#             cash_rec_name = f"[Unknown ID: {first_item.cash_empl}]"

#     # first_item = requisitions.first()
#     # cash_rec_name = first_item.cash_empl.employee_name if first_item and first_item.cash_empl else ''
#     # print(cash_rec_name)
#     context = {
#         'requi_uniq_id': pk,
#         'requisitions': requisitions,
#         'total_amount': total_amount,
#         'amount_in_words': amount_in_words,
#         'print_time': now(), 
#         'voucher': requisitions.first(),
#         'received_person': cash_rec_name,
#     }

#     return render(request, 'requisitions/purchase_cash_details.html', context)



@login_required
def purchase_cash_details(request, pk):
    requisitions = Requisition.objects.filter(requi_uniq_id=pk)
    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
    amount_in_words = num2words(total_amount, lang='en').title()

    first_item = requisitions.first()
    cash_rec_name = ""

    if first_item and first_item.cash_empl:
        try:
            emp = Employee.objects.get(employee_name=first_item.cash_empl)
            cash_rec_name = emp.employee_name
        except Employee.DoesNotExist:
            cash_rec_name = f"[Unknown Name: {first_item.cash_empl}]"

    context = {
        'requi_uniq_id': pk,
        'requisitions': requisitions,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words,
        'print_time': now(),
        'voucher': first_item,
        'received_person': cash_rec_name,
    }

    return render(request, 'requisitions/purchase_cash_details.html', context)




# @login_required
# def purchase_list(request):
#     projects_first = ProjectFirstLevelName.objects.all()
#     suppliers = Suppliers.objects.all()
#     conductors = SiteSupervisor.objects.all()
#     try:
#         current_employee = Employee.objects.get(emp_name=request.user.username)
#         emp_type = current_employee.emp_type.strip().lower()  
#     except Employee.DoesNotExist:
#         current_employee = None
#         emp_type = ''
#     if request.user.username == 'admin':
#         requisitions = Requisition.objects.filter(
#             Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")
#         ).order_by('-id')
#     else:
#         requisitions = Requisition.objects.filter(
#             Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")
#         ).order_by('-id')       

#     if request.user.username == 'admin':
#         employees = Employee.objects.exclude(emp_type__iexact='admin')  
#     else:
#         employees = Employee.objects.filter(emp_name=request.user.username)  

#     context = {
#         'Requisitions': requisitions,
#         'projects_firts': projects_first,
#         'employees': employees,
#         'suppliers': suppliers,
#         'conductors': conductors,
#     }
#     return render(request, 'requisitions/purchase_list.html', context)



@login_required
def purchase_order_list(request):
    purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

    grouped_data = []
    for pid in purch_ids:
        items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('-id')
        if not items.exists():
            continue

        total_amount = sum(item.amount for item in items if item.amount)
        first_item = items.first()

        grouped_data.append({
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'items': items,
            'total_amount': total_amount
        })

    context = {
        'grouped_data': grouped_data
    }
    return render(request, 'requisitions/purchase_order_list.html', context)





@login_required
def purchase_order_details(request, pk):
    requisitions = Inventories.objects.filter(purch_id=pk)
    context = {
        'purch_id': pk,
        'requisitions': requisitions
    }
    return render(request, 'requisitions/purchase_order_details.html', context)



@login_required
def requisition_invoice_list(request):
    purch_ids = Requisition.objects.order_by('-requi_uniq_id').values_list('requi_uniq_id', flat=True).distinct()

    grouped_data = []
    for pid in purch_ids:
        items = Requisition.objects.filter(requi_uniq_id=pid).select_related('project_name').order_by('-id')
        if not items.exists():
            continue

        total_amount = sum(item.amount for item in items if item.amount)
        first_item = items.first()

        grouped_data.append({
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'items': items,
            'employee_name': first_item.employee_name,
            'vendor_name': first_item.vendor_name,
            'total_amount': total_amount
        })

    context = {
        'grouped_data': grouped_data
    }
    return render(request, 'requisitions/requisition_invoice_list.html', context)


@login_required
def requisition_invoice_details(request, pk):
    requisitions = Requisition.objects.filter(requi_uniq_id=pk)
    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
    amount_in_words = num2words(total_amount, lang='en').title()

    context = {
        'requi_uniq_id': pk,
        'requisitions': requisitions,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words,
        'print_time': now(), 
        'voucher': requisitions.first(),  
    }

    return render(request, 'requisitions/requisition_invoice_details.html', context)



# @login_required
# def purchase_invoice_list(request):
#     purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

#     grouped_data = []
#     for pid in purch_ids:
#         items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('-id')
#         if not items.exists():
#             continue

#         total_amount = sum(item.amount for item in items if item.amount)
#         first_item = items.first()

#         grouped_data.append({
#             'purch_id': pid,
#             'project_name': first_item.project_name,
#             'requisition_date': first_item.requisition_date,
#             #'items': items,
#             'vendor_name': first_item.vendor_name,
#             'total_amount': total_amount
#         })

#     context = {
#         'grouped_data': grouped_data
#     }
#     return render(request, 'requisitions/purchase_invoice_list.html', context)


# @login_required
# def purchase_invoice_list(request):
#     purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

#     grouped_data = []
#     for pid in purch_ids:
#         items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('id')
#         if not items.exists():
#             continue

#         total_amount = sum(item.amount for item in items if item.amount)
#         first_item = items.first()  # first row in that group, earliest by id
       
#         print(first_item.purch_file.url if first_item.purch_file else 'No file')
#         grouped_data.append({
#             'purch_id': pid,
#             'project_name': first_item.project_name,
#             'requisition_date': first_item.requisition_date,
#             'vendor_name': first_item.vendor_name,
#             'total_amount': total_amount,
#             'purch_file': first_item.purch_file,  # file from first row
#         })

#     return render(request, 'requisitions/purchase_invoice_list.html', {'grouped_data': grouped_data})



# from django.http import HttpResponseNotAllowed


# #@require_POST
# @login_required
# def update_purch_file(request, purch_id):
#     if request.method != "POST":
#         return HttpResponseNotAllowed(['POST'], 'Only POST method allowed.')

#     uploaded_file = request.FILES.get('purch_file')
#     if uploaded_file:
#         objs = Inventories.objects.filter(purch_id=purch_id)
#         for obj in objs:
#             obj.purch_file = uploaded_file
#             obj.save()  # triggers proper file saving

#     return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def purchase_invoice_list(request):
    purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

    grouped_data = []
    for pid in purch_ids:
        items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('id')
        if not items.exists():
            continue

        total_amount = sum(item.amount for item in items if item.amount)
        first_item = items.first()

        grouped_data.append({
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'vendor_name': first_item.vendor_name,
            'total_amount': total_amount,
            'purch_files': [
                first_item.purch_file_1,
                first_item.purch_file_2,
                first_item.purch_file_3,
            ],
        })

    return render(request, 'requisitions/purchase_invoice_list.html', {'grouped_data': grouped_data})
    


@login_required
def purchase_invoice_filter(request):
    purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

    grouped_data = []
    for pid in purch_ids:
        items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('id')
        if not items.exists():
            continue

        total_amount = sum(item.amount for item in items if item.amount)
        first_item = items.first()

        grouped_data.append({
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'vendor_name': first_item.vendor_name,
            'total_amount': total_amount,
            'purch_files': [
                first_item.purch_file_1,
                first_item.purch_file_2,
                first_item.purch_file_3,
            ],
        })

    return render(request, 'requisitions/purchase_invoice_filter.html', {'grouped_data': grouped_data})
    
    
    
from django.http import HttpResponseNotAllowed

def update_purch_file(request, purch_id, file_index):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])

    uploaded_file = request.FILES.get('purch_file')
    if not uploaded_file:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Ensure file_index is int
    try:
        file_index = int(file_index)
    except ValueError:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if file_index not in [1, 2, 3]:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    objs = Inventories.objects.filter(purch_id=purch_id)
    for obj in objs:
        if file_index == 1:
            obj.purch_file_1 = uploaded_file
        elif file_index == 2:
            obj.purch_file_2 = uploaded_file
        elif file_index == 3:
            obj.purch_file_3 = uploaded_file
        obj.save()  # important!

    return redirect(request.META.get('HTTP_REFERER', '/'))
    
    

@login_required
def purchase_invoice_details(request, pk):
    # Queryset with related fields to optimize DB queries
    requisitions_qs = Inventories.objects.filter(purch_id=pk).select_related('vendor_name', 'item_name')

    # Calculate requisition date range
    date_range = requisitions_qs.aggregate(
        start_date=Min('requisition_date'),
        end_date=Max('requisition_date'),
    )

    # If no requisitions found, show error page or empty message
    if not requisitions_qs.exists():
        return render(request, 'requisitions/purchase_invoice_details.html', {
            'error_message': 'No data found for this purchase ID.'
        })

    # Calculate total amount and amount in words
    total_amount = requisitions_qs.aggregate(total=Sum('amount'))['total'] or 0
    total_amount_int = int(total_amount)  # removes decimal part by converting to int
    amount_in_words = num2words(total_amount_int, lang='en').title()

    # Prepare a custom list with split item_code and item_title
    requisition_list = []
    for item in requisitions_qs:
        item_name_str = str(item.item_name)  # Convert foreign key object to string
        parts = item_name_str.split(' - ', 1)
        item_code = parts[0].strip() if len(parts) > 1 else ''
        item_title = parts[1].strip() if len(parts) > 1 else item_name_str.strip()

        requisition_list.append({
            'item': item,
            'item_code': item_code,
            'item_title': item_title,
            'vendor_name': item.vendor_name or "",
        })

    first_entry = requisitions_qs.first()
    vendor_name = first_entry.vendor_name.supplier_name if first_entry and first_entry.vendor_name else ""

    context = {
        'purch_id': pk,
        'requisitions': requisition_list,
        'total_amount_int': total_amount_int,
        'amount_in_words': amount_in_words,
        'print_time': now(),
        'voucher': first_entry,
        'vendor_name': vendor_name,
        'start_date': date_range['start_date'],
        'end_date': date_range['end_date'],
    }

    return render(request, 'requisitions/purchase_invoice_details.html', context)





@login_required
def update_amount(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        amount = request.POST.get('amount')
        
        try:
            inventory_item = Inventories.objects.get(id=item_id)
            inventory_item.amount = amount
            inventory_item.save()
            return JsonResponse({'status': 'success'})
        except Inventories.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# @login_required
# def purchase_invoice_filter_details(request, pk):
#     requisitions = Inventories.objects.filter(purch_id=pk)
#     total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#     total_amount_int = int(total_amount)
#     amount_in_words = num2words(total_amount_int, lang='en').title()

#     first_entry = requisitions.first()
#     vendor_name = first_entry.vendor_name.supplier_name if first_entry and first_entry.vendor_name else ""

#     context = {
#         'purch_id': pk,
#         'requisitions': requisitions,
#         'total_amount': total_amount,
#         'amount_in_words': amount_in_words,
#         'print_time': now(),
#         'voucher': first_entry,
#         'vendor_name': vendor_name,
#     }

#     return render(request, 'requisitions/purchase_invoice_filter_details.html', context)


@login_required
def purchase_invoice_filter_details(request, pk):
    requisitions_qs = Inventories.objects.filter(purch_id=pk).select_related('vendor_name', 'item_name')
    date_range = requisitions_qs.aggregate(
        start_date=Min('requisition_date'),
        end_date=Max('requisition_date')
    )

    if not requisitions_qs.exists():
        return render(request, 'requisitions/purchase_invoice_filter_details.html', {
            'error_message': 'No data found for this purchase ID.'
        })

    total_amount = requisitions_qs.aggregate(total=Sum('amount'))['total'] or 0
    total_amount_int = int(total_amount)  # removes decimal part by converting to int
    amount_in_words = num2words(total_amount_int, lang='en').title()

    requisition_list = []
    for item in requisitions_qs:
        item_name_str = str(item.item_name)  # Convert foreign key object to string
        parts = item_name_str.split(' - ', 1)
        item_code = parts[0].strip() if len(parts) > 1 else ''
        item_title = parts[1].strip() if len(parts) > 1 else item_name_str.strip()

        requisition_list.append({
            'item': item,
            'item_code': item_code,
            'item_title': item_title,
        })

    first_entry = requisitions_qs.first()
    vendor_name = first_entry.vendor_name.supplier_name if first_entry and first_entry.vendor_name else ""

    context = {
        'purch_id': pk,
        'requisitions': requisition_list,
        'total_amount': total_amount,
        'total_amount_int': total_amount_int,
        'amount_in_words': amount_in_words,
        'print_time': now(),
        'voucher': first_entry,
        'vendor_name': vendor_name,
        'start_date': date_range['start_date'],
        'end_date': date_range['end_date'],
    }

    return render(request, 'requisitions/purchase_invoice_filter_details.html', context)
    
    


# @login_required
# def requisitions_create(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             reqsi_data = data.get('data', [])
#             employee_id = data.get('employee_id') or request.GET.get('employee')
#             project_id = data.get('project_id') or request.GET.get('project_id')
#             req_type = data.get('type') or request.GET.get('type')
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not reqsi_data or not employee_id or not project_id or not req_type:
#                 return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             employee = get_object_or_404(Employee, pk=employee_id)
#             requisition_date = timezone.now()

#             for item in reqsi_data:
#                 qty = Decimal(str(item['qty'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                 rate = Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                 discount = Decimal(str(item['discount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                 amount = (qty * rate - discount).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

#                 form_data = {
#                     'project_name': project.pk,
#                     'employee_name': employee.pk,
#                     'item_name': item.get('item_name'),
#                     'type': req_type,
#                     'vendor_name': item.get('vendor_name'),
#                     'unit': item.get('unit'),
#                     'qty': str(qty),
#                     'rate': str(rate),
#                     'discount': str(discount),
#                     'amount': str(amount),
#                     'remark': remark_text,
#                     'requisition_date': requisition_date,
#                 }

#                 form = RequisitionForm(form_data)
#                 if form.is_valid():
#                     form.save()
#                 else:
#                     return JsonResponse({'status': 'error', 'message': f'Form data invalid: {form.errors}'})

#             # Optional Notifications
#             roles_to_notify = ['admin']
#             sender_user = request.user
#             for role in roles_to_notify:
#                 recipients = User.objects.filter(groups__name__iexact=role)
#                 for user in recipients:
#                     Notification.objects.create(
#                         sender=sender_user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='requisition_admin_confirm',
#                         role=role,
#                         created_at=timezone.now()
#                     )

#             return JsonResponse({'status': 'success', 'message': 'Requisition saved and notifications sent.'})

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return JsonResponse({'status': 'error', 'message': str(e)})
    
#     # GET request (render form)
#     form = RequisitionForm()
#     project_id = request.GET.get('project_id')
#     employee_id = request.GET.get('employee')
#     type = request.GET.get('type')
#     sppliers = Suppliers.objects.all()
#     conductors = SiteSupervisor.objects.all()
#     headRequists = HeadOfRequisition.objects.all()
#     headExpenses = HeadOfExpense.objects.all()

#     project_first_name = ''
#     employee_name = ''
#     try:
#         if project_id:
#             project = ProjectFirstLevelName.objects.get(pk=project_id)
#             project_first_name = project.project_first_name
#         if employee_id:
#             employee = Employee.objects.get(pk=employee_id)
#             employee_name = employee.employee_name
#     except:
#         pass

#     return render(request, 'requisitions/requisition_add.html', {
#         'form': form,
#         'project_id': project_id,
#         'employee': employee_id,
#         'type': type,
#         'project_first_name': project_first_name,
#         'employee_name': employee_name,
#         'headRequists': headRequists,
#         'headExpenses': headExpenses,
#         'sppliers': sppliers,
#         'conductors': conductors,
#     })




@login_required
def requisitions_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            req_type = data.get('type') or request.GET.get('type')
            remark_text = data.get('remark') or request.GET.get('remark')

            # ✅ Validate
            if not reqsi_data or not employee_id or not project_id or not req_type:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_id)
            requisition_date = timezone.now()

            saved_requisitions = []

            # ✅ Save requisition items
            for item in reqsi_data:
                qty = Decimal(str(item['qty'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                rate = Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                discount = Decimal(str(item['discount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                amount = (qty * rate - discount).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

                form_data = {
                    'project_name': project.pk,
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name'),
                    'type': req_type,
                    'vendor_name': item.get('vendor_name'),
                    'unit': item.get('unit'),
                    'qty': str(qty),
                    'rate': str(rate),
                    'discount': str(discount),
                    'description': item.get("description", ""),
                    'amount': str(amount),
                    'remark': remark_text,
                    'requisition_date': requisition_date,
                }

                form = RequisitionForm(form_data)
                if form.is_valid():
                    requisition = form.save()
                    saved_requisitions.append(requisition)
                else:
                    return JsonResponse({'status': 'error', 'message': f'Invalid form data: {form.errors}'})

            # ✅ Create in-app notification for Admin users
            sender_user = request.user
            roles_to_notify = ['admin']

            for role in roles_to_notify:
                recipients = User.objects.filter(groups__name__iexact=role)
                for user in recipients:
                    Notification.objects.create(
                        sender=sender_user,
                        recipient=user,
                        project_name=project,
                        message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='requisition_admin_confirm',
                        role=role,
                        created_at=timezone.now()
                    )

            # ✅ Push notification via Firebase Cloud Messaging
            admin_tokens = list(FCMDevice.objects.filter(user__groups__name__iexact='admin').values_list('token', flat=True))

            if admin_tokens:
                try:
                    push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
                    push_service.notify_multiple_devices(
                        registration_ids=admin_tokens,
                        message_title="New Requisition Submitted",
                        message_body=f"{employee.employee_name} submitted a requisition for project {project.project_first_name}.",
                    )
                except Exception as e:
                    print("⚠️ FCM Push Error:", e)

            return JsonResponse({'status': 'success', 'message': 'Requisition saved, notifications sent, and push delivered.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    # ✅ GET request (render form)
    form = RequisitionForm()
    project_id = request.GET.get('project_id')
    employee_id = request.GET.get('employee')
    type = request.GET.get('type')
    sppliers = Suppliers.objects.all()
    conductors = SiteSupervisor.objects.all()
    headRequists = HeadOfRequisition.objects.all()
    headExpenses = HeadOfExpense.objects.all()

    project_first_name = ''
    employee_name = ''
    try:
        if project_id:
            project = ProjectFirstLevelName.objects.get(pk=project_id)
            project_first_name = project.project_first_name
        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            employee_name = employee.employee_name
    except:
        pass

    return render(request, 'requisitions/requisition_add.html', {
        'form': form,
        'project_id': project_id,
        'employee': employee_id,
        'type': type,
        'project_first_name': project_first_name,
        'employee_name': employee_name,
        'headRequists': headRequists,
        'headExpenses': headExpenses,
        'sppliers': sppliers,
        'conductors': conductors,
    })
    
    

@login_required
def bill_requisitions_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            req_type = data.get('type') or request.GET.get('type')
            remark_text = data.get('remark') or request.GET.get('remark')
            vendor_name = data.get('vendor_name') or request.GET.get('vendor_name')
            paymentType = data.get('payment_type') or request.GET.get('payment_type')
            
            if not reqsi_data or not employee_id or not project_id or not req_type:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_id)
            requisition_date = timezone.now()

            for item in reqsi_data:
                qty = Decimal(str(item['qty'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                rate = Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                amount = (qty * rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                
                if req_type == 'Supplier':
                    headofaccount = HeadOfAccount.objects.get(head_name="Supplier Account")
                else:
                    headofaccount = HeadOfAccount.objects.get(head_name="Contractor Account")
                    
                
                form_data = {
                    'project_name': project.pk,
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name'),
                    'type': req_type,
                    'vendor_name': vendor_name,
                    'unit': item.get('unit'),
                    'qty': str(qty),
                    'rate': str(rate),
                    'amount': str(amount),
                    'remark': remark_text,
                    'requisition_date': requisition_date,
                    'note': item.get('note'),
                    'head_of_account': headofaccount.pk,
                    'approv_purch_note': paymentType
                }

                form = BillRequisitionForm(form_data)

                if form.is_valid():
                    form.save()
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Form data invalid: {form.errors}'
                    })

            # Notification (optional)
            roles_to_notify = ['admin']
            is_admin = request.user.groups.filter(name__iexact='admin').exists()

            sender_user = request.user
            if is_admin:
                try:
                    sender_user = User.objects.get(username=employee.emp_name)
                except User.DoesNotExist:
                    pass

            for role in roles_to_notify:
                recipients = User.objects.filter(groups__name__iexact=role)
                for user in recipients:
                    Notification.objects.create(
                        sender=sender_user,
                        recipient=user,
                        project_name=project,
                        message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='bill_requisition_admin_confirm',
                        role=role,
                        created_at=timezone.now() 
                    )

            return JsonResponse({'status': 'success', 'message': 'Requisition saved and notifications sent.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # Render form
        form = BillRequisitionForm()
        project_id = request.GET.get('project_id')
        employee_id = request.GET.get('employee')
        type = request.GET.get('type')
        sppliers = Suppliers.objects.all()
        conductors = SiteSupervisor.objects.all()
        headRequists = HeadOfRequisition.objects.all()
        headExpenses = HeadOfExpense.objects.all()

        project_first_name = ''
        employee_name = ''
        try:
            if project_id:
                project = ProjectFirstLevelName.objects.get(pk=project_id)
                project_first_name = project.project_first_name
            if employee_id:
                employee = Employee.objects.get(pk=employee_id)
                employee_name = employee.employee_name
        except:
            pass

        return render(request, 'billrequisitions/bill_requisition_add.html', {
            'form': form,
            'project_id': project_id,
            'employee': employee_id,
            'type': type,
            'project_first_name': project_first_name,
            'employee_name': employee_name,
            'headRequists': headRequists,
            'headExpenses': headExpenses,
            'sppliers': sppliers,
            'conductors': conductors,
        })
        

@login_required
def bill_requisition_by_project(request, requi_id):
    requisitions = BillRequisition.objects.filter(requi_uniq_id=requi_id)
    
    project = None
    if requisitions.exists():
        project = requisitions.first().project_name  # Assuming project_name is a FK

    context = {
        'requisitions': requisitions,
        'project': project,
    }
    return render(request, 'billrequisitions/bill_requisition_by_project.html', context)



@login_required
def bill_requisition_by_fallback(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Get filters from GET parameters
    requisition_date_str = request.GET.get('requisition_date')
    vendor_names_str = request.GET.get('vendor_name', '')  # comma separated vendors

    # Base queryset: requi_uniq_id null and approv_status NOT approved
    requisitions = BillRequisition.objects.filter(
        project_name=project,
        requi_uniq_id__isnull=True,
    ).exclude(approv_status='approved')

    # Filter by requisition_date if provided and valid
    if requisition_date_str:
        try:
            requisition_date = datetime.strptime(requisition_date_str, '%Y-%m-%d').date()
            requisitions = requisitions.filter(requisition_date=requisition_date)
        except ValueError:
            # Invalid date format, ignore filter
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
    return render(request, 'billrequisitions/bill_requisition_by_fallback.html', context)




# @login_required
# def bill_requisition_item_summary(request):
#     project_id = request.GET.get('project_id')
#     type_name = request.GET.get('type') 
#     supplier_param = request.GET.get('supplier_id')  # Can be name or ID
#     conductor_id = request.GET.get('conductor')
#     status = request.GET.get('status')
#     reqiDate = request.GET.get('reqiDate')
    
#     # Validate project
#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
#     requisition_filter = Q(project_name=project)

#     supplier = None
#     suppliers = None

#     # andle supplier name or ID
#     if supplier_param:
#         try:
#             # Try treating as ID
#             supplier = Suppliers.objects.get(id=int(supplier_param))
#         except (ValueError, Suppliers.DoesNotExist):
#             # Try treating as name (case-insensitive)
#             try:
#                 supplier = Suppliers.objects.get(supplier_name__iexact=supplier_param)
#             except Suppliers.DoesNotExist:
#                 return HttpResponse("Supplier not found.", status=404)

#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]

#     # Conductor filter by ID
#     elif conductor_id and conductor_id.isdigit():
#         supplier = get_object_or_404(SiteSupervisor, id=int(conductor_id))
#         requisition_filter &= Q(supervisor_name=supplier)
#         suppliers = [supplier]

#     # Status filter (case-insensitive)
#     if status and status.lower() in ['pending', 'approved', 'rejected']:
#         requisition_filter &= Q(approv_status__iexact=status)

#     # Date filter
#     if reqiDate:
#         try:
#             parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
#             requisition_filter &= Q(requisition_date=parsed_date)
#         except ValueError:
#             return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

#     # inal filtered query
#     requisition_items = BillRequisition.objects.filter(requisition_filter)

#     if not suppliers:
#         supplier_ids = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
#         suppliers = Suppliers.objects.filter(id__in=supplier_ids)

#     total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
#     requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

#     def amount_to_words(amount):
#         amount = round(float(amount), 2)
#         taka = int(amount)
#         poisha = int(round((amount - taka) * 100))

#         taka_words = num2words(taka, lang='en').capitalize() + " Taka"

#         if poisha > 0:
#             poisha_words = num2words(poisha, lang='en') + " Poisha"
#             return f"{taka_words} and {poisha_words}"
#         else:
#             return f"{taka_words}"
    
#     context = {
#         'project': project,
#         'supplier': supplier,
#         'suppliers': suppliers,
#         'requisition_items': requisition_items,
#         'total_amount': total_amount,
#         'amount_in_words': amount_to_words(total_amount),
#         'print_time': now(),
#         'requisition_date': requisition_date,
#     }
#     return render(request, 'billrequisitions/bill_requisition_item_summary.html', context)



@login_required
def bill_requisition_item_summary(request):
    project_id = request.GET.get('project_id')
    supplier_name = request.GET.get('supplier_id') 
    contractor_name = request.GET.get('contractor')  
    req_type = request.GET.get('type')               
    status = request.GET.get('status')
    reqiDate = request.GET.get('reqiDate')

    # --- Validate project ---
    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
    requisition_filter = Q(project_name=project)

    supplier = None
    contractor = None

    # --- Supplier filter ---
    if req_type and req_type.lower() == "supplier" and supplier_name:
        requisition_filter &= (
            Q(type="Supplier") & Q(vendor_name__iexact=supplier_name)
        )

    # --- Contractor filter ---
    elif req_type and req_type.lower() in "contractor" and contractor_name:
        requisition_filter &= (
            Q(type="Contractor") & Q(vendor_name__iexact=contractor_name)
        )
    # --- Status filter ---
    if status and status.lower() in ['pending', 'approved', 'rejected']:
        requisition_filter &= Q(approv_status__iexact=status)

    # --- Date filter ---
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
            requisition_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            return HttpResponse(
                "Invalid requisition_date format. Use YYYY-MM-DD.", status=400
            )

    # --- Fetch filtered items ---
    requisition_items = BillRequisition.objects.filter(requisition_filter)

    # --- Total amount ---
    total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
    requisition_date = (
        requisition_items.first().requisition_date if requisition_items.exists() else None
    )

    # --- Amount in words ---
    def amount_to_words(amount):
        amount = round(float(amount), 2)
        taka = int(amount)
        poisha = int(round((amount - taka) * 100))
        taka_words = num2words(taka, lang='en').capitalize() + " Taka"
        if poisha > 0:
            poisha_words = num2words(poisha, lang='en') + " Poisha"
            return f"{taka_words} and {poisha_words}"
        return taka_words

    context = {
        'project': project,
        'supplier': supplier,
        'conductor': contractor_name,
        'requisition_items': requisition_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'requisition_date': requisition_date,
    }

    return render(request, 'billrequisitions/bill_requisition_item_summary.html', context)

    
    

# @login_required
# def bill_requisition_item_summary(request):
#     project_id = request.GET.get("project_id")
#     type_name = request.GET.get("type")  # "Supplier" or "Conductor"
#     supplier_param = request.GET.get("supplier_id")
#     conductor_id = request.GET.get("conductor")
#     status = request.GET.get("status")
#     reqiDate = request.GET.get("reqiDate")

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
#     requisition_filter = Q(project_name=project)

#     supplier = None
#     conductor = None
#     debug_info = []

#     # --- Supplier filter ---
#     if type_name == "Supplier" and supplier_param:
#         try:
#             supplier = Suppliers.objects.get(id=int(supplier_param))
#             requisition_filter &= Q(vendor_name__iexact=supplier.supplier_name)
#             debug_info.append(f"Supplier filter applied: {supplier.supplier_name}")
#         except (ValueError, Suppliers.DoesNotExist):
#             supplier = Suppliers.objects.filter(supplier_name__iexact=supplier_param).first()
#             if supplier:
#                 requisition_filter &= Q(vendor_name__iexact=supplier.supplier_name)
#                 debug_info.append(f"Supplier filter applied: {supplier.supplier_name}")

#     # --- Conductor filter ---
#     elif type_name == "Conductor" and conductor_id:
#         if conductor_id.isdigit():
#             try:
#                 conductor = SiteSupervisor.objects.get(id=int(conductor_id))
#                 requisition_filter &= Q(vendor_name__iexact=conductor.site_supervisor_name)
#                 debug_info.append(f"Conductor filter applied: {conductor.site_supervisor_name}")
#             except SiteSupervisor.DoesNotExist:
#                 debug_info.append(f"Conductor not found: {conductor_id}")

#     # --- Status filter ---
#     if status and status.lower() in ["pending", "approved", "rejected"]:
#         requisition_filter &= Q(approv_status__iexact=status)
#         debug_info.append(f"Status filter: {status}")

#     # --- Date filter ---
#     if reqiDate:
#         try:
#             parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
#             requisition_filter &= Q(requisition_date=parsed_date)
#             debug_info.append(f"Date filter: {reqiDate}")
#         except ValueError:
#             return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

#     # --- Fetch filtered items ---
#     requisition_items = BillRequisition.objects.filter(requisition_filter)
#     debug_info.append(f"Total items found: {requisition_items.count()}")

#     # --- Amount calculation ---
#     total_amount = requisition_items.aggregate(total=Sum("amount"))["total"] or 0

#     def amount_to_words(amount):
#         amount = round(float(amount), 2)
#         taka = int(amount)
#         poisha = int(round((amount - taka) * 100))
#         taka_words = num2words(taka, lang="en").capitalize() + " Taka"
#         if poisha > 0:
#             poisha_words = num2words(poisha, lang="en") + " Poisha"
#             return f"{taka_words} and {poisha_words}"
#         return f"{taka_words}"

#     context = {
#         "project": project,
#         "supplier": supplier,
#         "conductor": conductor,
#         "requisition_items": requisition_items,
#         "total_amount": total_amount,
#         "amount_in_words": amount_to_words(total_amount),
#         "debug_info": debug_info,
#     }

#     return render(request, "billrequisitions/bill_requisition_item_summary.html", context)





@login_required
def pettycash_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            remark_text = data.get('remark') or request.GET.get('remark')

            # âœ… Validation check (no 'type' used anymore)
            if not reqsi_data or not employee_id or not project_id:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_id)
            requisition_date = timezone.now()

            for item in reqsi_data:
                qty = Decimal(str(item['qty'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                rate = Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                amount = (qty * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                form_data = {
                    'project_name': project.pk,
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name'),
                    'unit': item.get('unit'),
                    'qty': str(qty),
                    'rate': str(rate),
                    'amount': str(amount),
                    'remark': remark_text,
                    'requisition_date': requisition_date,
                }

                form = PettyCashForm(form_data)

                if form.is_valid():
                    form.save()
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Form data invalid: {form.errors}'
                    })

            # âœ… Notification (optional)
            roles_to_notify = ['admin']
            is_admin = request.user.groups.filter(name__iexact='admin').exists()
            sender_user = request.user
            if is_admin:
                try:
                    sender_user = User.objects.get(username=employee.emp_name)
                except User.DoesNotExist:
                    pass

            for role in roles_to_notify:
                recipients = User.objects.filter(groups__name__iexact=role)
                for user in recipients:
                    Notification.objects.create(
                        sender=sender_user,
                        recipient=user,
                        project_name=project,
                        message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='requisition_account_confirm',
                        role=role
                    )

            return JsonResponse({'status': 'success', 'message': 'Requisition saved and notifications sent.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # GET request: Render the pettycash form
        form = PettyCashForm()
        project_id = request.GET.get('project_id')
        employee_id = request.GET.get('employee')
        headRequists = HeadOfRequisition.objects.all()

        project_first_name = ''
        employee_name = ''
        try:
            if project_id:
                project = ProjectFirstLevelName.objects.get(pk=project_id)
                project_first_name = project.project_first_name
            if employee_id:
                employee = Employee.objects.get(pk=employee_id)
                employee_name = employee.employee_name
        except:
            pass

        return render(request, 'pettycash/pettycash_add.html', {
            'form': form,
            'project_id': project_id,
            'employee': employee_id,
            'project_first_name': project_first_name,
            'employee_name': employee_name,
            'headRequists': headRequists,
        })

    
    



@login_required 
def requisition_edit(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, instance=requisition)
        if form.is_valid():
            updated = form.save(commit=False)

            # if requisition.approv_status != 'approved':
            #     updated.approv_status = request.POST.get('approv_status')
            #     updated.approv_note = request.POST.get('approv_note')

            updated.save()
            messages.success(request, 'Requisition updated successfully.')

            if updated.requi_uniq_id:
                return redirect('requisition_by_project', requi_id=updated.requi_uniq_id)
            else:
                project_id = updated.project_name.id  # use correct field name
                requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
                vendor_name = updated.vendor_name  # ✅ correct usage
            
                fallback_url = reverse('requisition_by_fallback', args=[project_id])
                return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_name}')


    else:
        form = RequisitionForm(instance=requisition)

    context = {
        'form': form,
        'project_list': ProjectFirstLevelName.objects.all(),
        'employee_names': Employee.objects.all(),
        'requisition_list': HeadOfRequisition.objects.all(),
        'supplier_list': Suppliers.objects.all(),
        'contructor_list': SiteSupervisor.objects.all(),
    }
    return render(request, 'requisitions/requisition_edit.html', context)


 



@login_required
def project_boq_requisition_summary(request):
    # Step 1: Get BOQ grouped by project + item_name
    boq_raw = BOQ.objects.filter(
        category_type='Material Purchase Cost'
    ).select_related('project_name')

    boq_map = {}
    for boq in boq_raw:
        key = (boq.project_name.project_first_name, boq.item_name)
        if key not in boq_map:
            boq_map[key] = {'qty': 0, 'amount': 0}
        boq_map[key]['qty'] += boq.qty
        boq_map[key]['amount'] += boq.amount or 0
    
    requisitions = Requisition.objects.filter(
        type='Supplier',
        purch_appov='Yes' 
    ).select_related('item_name', 'project_name')

    req_map = {}
    for req in requisitions:
        item_name = req.item_name.head_requi_name
        project = req.project_name.project_first_name
        key = (project, item_name)
        if key not in req_map:
            req_map[key] = {'qty': 0, 'amount': 0}
        req_map[key]['qty'] += req.qty
        req_map[key]['amount'] += req.amount or 0

    # Step 3: Merge both into combined data
    all_keys = set(boq_map.keys()) | set(req_map.keys())
    combined_data = []
    for project_name, item_name in sorted(all_keys):
        boq = boq_map.get((project_name, item_name), {'qty': 0, 'amount': 0})
        req = req_map.get((project_name, item_name), {'qty': 0, 'amount': 0})
        combined_data.append({
            'project_name': project_name,
            'item_name': item_name,
            'boq_qty': boq['qty'],
            'boq_amount': boq['amount'],
            'req_qty': req['qty'],
            'req_amount': req['amount'],
            'diff_qty': boq['qty'] - req['qty'],
            'diff_amount': boq['amount'] - req['amount'],
        })

    return render(request, 'requisitions/boq_requisition_summary.html', {
        'combined_data': combined_data,
        'is_global': True,
    })



@login_required
def requisition_delete(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('requisition_list')
    return render(request, 'requisitions/requisition_delete.html', {'requisition': requisition})


@login_required
def get_stock_qty(request):
    item_id = request.GET.get('item_id')
    project_id = request.GET.get('project_id')

    try:
        total_qty = Inventories.objects.filter(
            item_name_id=item_id
        ).aggregate(total=Sum('qtysub'))['total'] or 0

        return JsonResponse({'qtysub': total_qty})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
        
## this code is..ok----

from django.db.models import Sum
#import time
#from collections import defaultdict

# @login_required
# def requisition_confirmation(request):
#     project_id = request.GET.get('project_id')
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

#         all_saved = True
#         notified_users = set()

#         try:
#             for item_id in selected_ids:
#                 requiUniq_id = int(time.time())
#                 try:
#                     item = Requisition.objects.get(id=item_id)
#                     item.approv_status = approval_status
#                     item.approv_note = note
#                     item.requi_uniq_id = requiUniq_id
#                     item.save()

#                     # 🔹 Update Supplier or SiteSupervisor total_amount based on type
#                     if approval_status == "approved":
#                         if item.type in ["Vendor", "Supplier"] and item.vendor_name:
#                             supplier, created = Suppliers.objects.get_or_create(
#                                 supplier_name=item.vendor_name
#                             )
#                             supplier.total_amount = (supplier.total_amount or 0) + (item.amount or 0)
#                             supplier.save()

#                         elif item.type == "Contructor" and hasattr(item, "contructor") and item.contructor:
#                             supervisor = item.contructor
#                             supervisor.total_amount = (supervisor.total_amount or 0) + (item.amount or 0)
#                             supervisor.save()

#                     # 🔹 Notification logic
#                     try:
#                         user = User.objects.get(username=item.employee_name.emp_name)
#                         notified_users.add(user)
#                     except User.DoesNotExist:
#                         pass

#                 except Requisition.DoesNotExist:
#                     continue

#             if all_saved:
#                 for user in notified_users:
#                     Notification.objects.create(
#                         sender=request.user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='requisition_accounts_confirm',
#                         role='accounts'
#                     )

#             messages.success(request, "Selected items updated and notifications sent successfully.")
#             return redirect("requisition_detail", pk=selected_ids[0])  

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # Group requisitions by employee
#     all_requisitions = Requisition.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).order_by('employee_name', 'requisition_date')

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

#     return render(request, 'requisitions/requisition_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': grouped_data,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })



# @login_required
# def requisition_confirmation(request):
#     project_id = request.GET.get('project_id')
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

#         all_saved = True
#         notified_users = set()

#         try:
#             # 🔹 Create a unique approval batch ID
#             requiUniq_id = str(int(time.time()))

#             for item_id in selected_ids:
#                 try:
#                     item = Requisition.objects.get(id=item_id)
#                     item.approv_status = approval_status
#                     item.approv_note = note
#                     item.requi_uniq_id = requiUniq_id
#                     item.save()

#                     # 🔹 When approved, handle Supplier & Payment Table
#                     if approval_status == "approved":
#                         supplier_obj = None

#                         # Determine supplier from requisition type
#                         if item.type in ["Vendor", "Supplier"] and item.vendor_name:
#                             supplier_obj, created = Suppliers.objects.get_or_create(
#                                 supplier_name=item.vendor_name
#                             )
#                             supplier_obj.total_amount = (supplier_obj.total_amount or 0) + (item.amount or 0)
#                             supplier_obj.save()

#                         elif item.type == "Contructor" and hasattr(item, "contructor") and item.contructor:
#                             supplier_obj = item.contructor
#                             supplier_obj.total_amount = (supplier_obj.total_amount or 0) + (item.amount or 0)
#                             supplier_obj.save()

#                         # ✅ Insert into RequisitionApprovalPayment
#                         if supplier_obj:
#                             total_amount = (
#                                 Requisition.objects.filter(
#                                     vendor_name=supplier_obj.supplier_name,
#                                     requi_uniq_id=requiUniq_id
#                                 ).aggregate(total=Sum('amount'))['total'] or 0
#                             )

#                             RequisitionApprovalPayment.objects.update_or_create(
#                                 requisition=item,
#                                 requi_uniq_id=requiUniq_id,
#                                 supplier=supplier_obj,
#                                 defaults={
#                                     'payment_type': 'requisition_pay',
#                                     'requi_item_name': item.item_name,
#                                     'requi_amount': total_amount,
#                                     'requisition_date': item.requisition_date or timezone.now().date()
#                                 }
#                             )

#                     # 🔹 Notification logic
#                     try:
#                         user = User.objects.get(username=item.employee_name.emp_name)
#                         notified_users.add(user)
#                     except User.DoesNotExist:
#                         pass

#                 except Requisition.DoesNotExist:
#                     continue

#             if all_saved:
#                 for user in notified_users:
#                     Notification.objects.create(
#                         sender=request.user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='requisition_accounts_confirm',
#                         role='accounts'
#                     )

#             messages.success(request, "Selected items updated, payments recorded, and notifications sent successfully.")
#             return redirect("requisition_detail", pk=selected_ids[0])

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # 🔹 Group requisitions by employee
#     all_requisitions = Requisition.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).order_by('employee_name', 'requisition_date')

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

#     return render(request, 'requisitions/requisition_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': grouped_data,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })
    
    
@login_required
def requisition_confirmation(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status")
        note = request.POST.get("note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        all_saved = True
        notified_users = set()

        try:
            # 🔹 Unique approval batch ID
            requiUniq_id = str(int(time.time()))

            for item_id in selected_ids:
                try:
                    item = Requisition.objects.get(id=item_id)
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.requi_uniq_id = requiUniq_id
                    item.save()

                    # 🔹 When approved, handle Supplier & Payment Table
                    if approval_status == "approved":
                        supplier_obj = None

                        # Determine supplier from requisition type
                        if item.type in ["Vendor", "Supplier"] and item.vendor_name:
                            supplier_obj, created = Suppliers.objects.get_or_create(
                                supplier_name=item.vendor_name
                            )
                            supplier_obj.total_amount = (supplier_obj.total_amount or 0) + (item.amount or 0)
                            supplier_obj.save()

                        elif item.type == "Contructor" and hasattr(item, "contructor") and item.contructor:
                            supplier_obj = item.contructor
                            supplier_obj.total_amount = (supplier_obj.total_amount or 0) + (item.amount or 0)
                            supplier_obj.save()

                        # ✅ Insert into RequisitionApprovalPayment (row-wise amount only)
                        if supplier_obj:
                            RequisitionApprovalPayment.objects.update_or_create(
                                requisition=item,
                                requi_uniq_id=requiUniq_id,
                                supplier=supplier_obj,
                                defaults={
                                    'payment_type': 'requisition_pay',
                                    'requi_item_name': item.item_name,
                                    'requi_amount': item.amount or 0,  # ← fixed (per-row amount)
                                    'requisition_date': item.requisition_date or timezone.now().date()
                                }
                            )

                    # 🔹 Notification logic
                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:
                        pass

                except Requisition.DoesNotExist:
                    continue

            # 🔹 Create notifications for all relevant users
            if all_saved:
                for user in notified_users:
                    Notification.objects.create(
                        sender=request.user,
                        recipient=user,
                        project_name=project,
                        message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='requisition_accounts_confirm',
                        role='accounts'
                    )

            messages.success(request, "Selected items updated, payments recorded, and notifications sent successfully.")
            return redirect("requisition_detail", pk=selected_ids[0])

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # 🔹 Group requisitions by employee
    all_requisitions = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    ).order_by('employee_name', 'requisition_date')

    requisitions_by_employee = defaultdict(lambda: defaultdict(list))
    for req in all_requisitions:
        employee = req.employee_name
        date = req.requisition_date
        requisitions_by_employee[employee][date].append(req)

    grouped_data = {}
    for employee, date_group in requisitions_by_employee.items():
        items_by_date = dict(date_group)
        totals_by_date = {
            date: sum(item.amount or 0 for item in items)
            for date, items in items_by_date.items()
        }
        employee_total = sum(totals_by_date.values())
        grouped_data[employee] = {
            'items_by_date': items_by_date,
            'totals_by_date': totals_by_date,
            'total': employee_total,
        }

    final_total = all_requisitions.aggregate(total=Sum('amount'))['total'] or 0
    reference_requisition = all_requisitions.first()

    return render(request, 'requisitions/requisition_confirmation.html', {
        'project': project,
        'requisitions_by_employee': grouped_data,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })






@login_required
def requisition_payment_list(request):
    # Fetch all payments with supplier
    payments = RequisitionApprovalPayment.objects.select_related('supplier').order_by('supplier__supplier_name')

    # Build supplier-wise summary dictionary
    summary_dict = {}
    for p in payments:
        supplier_name = p.supplier.supplier_name if p.supplier else "N/A"
        supplier_id = p.supplier.id if p.supplier else None

        if supplier_name not in summary_dict:
            summary_dict[supplier_name] = {
                'supplier': supplier_name,
                'supplier_id': supplier_id,
                'requisition_pay': 0,
                'purchase_pay': 0,
                'approval_pay': 0,
                'advance_pay': 0,
                'id': p.id,
            }

        # Sum amounts based on payment type
        if p.payment_type == 'requisition_pay':
            summary_dict[supplier_name]['requisition_pay'] += float(p.requi_amount or 0)
        elif p.payment_type == 'purchase_pay':
            summary_dict[supplier_name]['purchase_pay'] += float(p.requi_amount or 0)
        elif p.payment_type == 'approval_pay':
            summary_dict[supplier_name]['approval_pay'] += float(p.requi_amount or 0)
        elif p.payment_type == 'advance_pay':
            summary_dict[supplier_name]['advance_pay'] += float(p.requi_amount or 0)

    # Calculate final balance and status
    summary = []
    for data in summary_dict.values():
        # Safely get numeric values (default to 0 if missing or None)
        requisition_pay = float(data.get('requisition_pay', 0) or 0)
        approval_pay = float(data.get('approval_pay', 0) or 0)
        advance_pay = float(data.get('advance_pay', 0) or 0)
        purchase_pay = float(data.get('purchase_pay', 0) or 0)
    
        payments = approval_pay + advance_pay
    
        # Special case: no purchase, no payments
        if purchase_pay == 0 and approval_pay == 0 and advance_pay == 0:
            balance = abs(requisition_pay)
            status = "Payable" if requisition_pay > 0 else ("Receivable" if requisition_pay < 0 else "Balanced")
        else:
            # Normal case
            balance = purchase_pay - payments
            if purchase_pay > payments:
                status = "Payable"
            elif purchase_pay < payments:
                status = "Receivable"
            else:
                status = "Balanced"
            balance = abs(balance)  # display as positive
    
        data['balance'] = balance
        data['status'] = status
        summary.append(data)
    
    return render(request, 'requisitions/requisition_payment_list.html', {
        'summary': summary,
    })




@login_required
def requi_app_pay_pdf(request, supplier_id):
    supplier = get_object_or_404(Suppliers, id=supplier_id)

    payments = (
        RequisitionApprovalPayment.objects
        .filter(supplier_id=supplier_id)
        .order_by('requisition_date')
    )

    # Initialize totals
    total = {
        'requisition_pay': Decimal('0.00'),
        'purchase_pay': Decimal('0.00'),
        'approval_pay': Decimal('0.00'),
        'advance_pay': Decimal('0.00'),
    }

    for p in payments:
        amount = p.requi_amount or Decimal('0.00')
        if p.payment_type == 'requisition_pay':
            total['requisition_pay'] += amount
        elif p.payment_type == 'purchase_pay':
            total['purchase_pay'] += amount
        elif p.payment_type == 'approval_pay':
            total['approval_pay'] += amount
        elif p.payment_type == 'advance_pay':
            total['advance_pay'] += amount

    requisition_pay = float(total['requisition_pay'])
    purchase_pay = float(total['purchase_pay'])
    approval_pay = float(total['approval_pay'])
    advance_pay = float(total['advance_pay'])
    payments_total = approval_pay + advance_pay

    # Special case: no purchase and no payments
    if purchase_pay == 0 and approval_pay == 0 and advance_pay == 0:
        balance = abs(requisition_pay)
        status = "Payable" if requisition_pay > 0 else ("Receivable" if requisition_pay < 0 else "Balanced")
    else:
        # Normal case
        balance = purchase_pay - payments_total
        if purchase_pay > payments_total:
            status = "Payable"
        elif purchase_pay < payments_total:
            status = "Receivable"
        else:
            status = "Balanced"
        balance = abs(balance)

    # Convert balance to words
    def amount_to_words(amount):
        try:
            amount_int = int(abs(amount))
            words = num2words(amount_int).replace(',', '').lower()
            return f"{words} taka only"
        except:
            return f"{amount} taka only"

    context = {
        'supplier': supplier,
        'payments': payments,
        'total': total,
        'balance': balance,
        'status': status,
        'balance_in_words': amount_to_words(balance),
        'print_time': now(),
    }

    return render(request, 'requisitions/requi_app_pay_pdf.html', context)



@login_required
def approval_payment_edit(request, pk):
    payment = get_object_or_404(RequisitionApprovalPayment, pk=pk)

    if request.method == 'POST':
        form = RequisitionApprovalPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully')
            return redirect('requisition_payment_list')
    else:
        form = RequisitionApprovalPaymentForm(instance=payment)

    return render(request, 'requisitions/approval_payment_edit.html', {
        'form': form,
        'payment': payment
    })



@login_required
def approval_payment_delete(request, pk):
    payment = get_object_or_404(RequisitionApprovalPayment, pk=pk)

    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully')
        return redirect('requisition_payment_list')

    return render(request, 'requisitions/approval_payment_delete.html', {
        'payment': payment
    })
    
    


@login_required
def bill_reqs_payment_list(request):
    # Fetch all payments with contractors
    payments = BillRequisitionApprovalPayment.objects.select_related('contractors').order_by('contractors__supervisor_name')

    # Build contractor-wise summary dictionary
    summary_dict = {}
    for p in payments:
        contractor_name = p.contractors.supervisor_name if p.contractors else "N/A"
        contractor_id = p.contractors.id if p.contractors else None

        if contractor_name not in summary_dict:
            summary_dict[contractor_name] = {
                'contractor': contractor_name,
                'contractor_id': contractor_id,
                'requisition_pay': 0,
                'approval_pay': 0,
                'advance_pay': 0,
                'id': p.id,
            }

        # Sum amounts based on payment type (excluding purchase_pay)
        amount = float(p.requi_amount or 0)
        if p.payment_type == 'requisition_pay':
            summary_dict[contractor_name]['requisition_pay'] += amount
        elif p.payment_type == 'approval_pay':
            summary_dict[contractor_name]['approval_pay'] += amount
        elif p.payment_type == 'advance_pay':
            summary_dict[contractor_name]['advance_pay'] += amount

    # Calculate final balance and status (Balance = Requisition - (Approval + Advance))
    summary = []
    for data in summary_dict.values():
        requisition_pay = float(data.get('requisition_pay', 0) or 0)
        approval_pay = float(data.get('approval_pay', 0) or 0)
        advance_pay = float(data.get('advance_pay', 0) or 0)
    
        total_payments = approval_pay + advance_pay
        balance = requisition_pay - total_payments
        
        if balance > 0:
            status = "Payable"
        elif balance < 0:
            status = "Receivable"
        else:
            status = "Balanced"
            
        data['balance'] = abs(balance)
        data['status'] = status
        summary.append(data)
    
    return render(request, 'requisitions/bill_reqs_payment_list.html', {
        'summary': summary,
    })



from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from num2words import num2words

@login_required
def bill_requi_app_pay_pdf(request, contractor_id):
    sitesupervisor = get_object_or_404(SiteSupervisor, id=contractor_id)

    payments = (
        BillRequisitionApprovalPayment.objects
        .filter(contractors_id=contractor_id)  # <-- Changed from contractor_id to contractors_id
        .order_by('requisition_date')
    )

    # Initialize totals
    total = {
        'requisition_pay': Decimal('0.00'),
        'purchase_pay': Decimal('0.00'),
        'approval_pay': Decimal('0.00'),
        'advance_pay': Decimal('0.00'),
    }

    for p in payments:
        if p.payment_type == 'requisition_pay':
            total['requisition_pay'] += p.requi_amount or Decimal('0.00')
        elif p.payment_type == 'purchase_pay':
            total['purchase_pay'] += p.requi_amount or Decimal('0.00')
        elif p.payment_type == 'approval_pay':
            total['approval_pay'] += p.requi_amount or Decimal('0.00')
        elif p.payment_type == 'advance_pay':
            total['advance_pay'] += p.requi_amount or Decimal('0.00')

    # Calculations
    diff = total['requisition_pay'] - total['purchase_pay']
    paid_total = total['approval_pay'] + total['advance_pay']
    calculate_balance = paid_total + (diff if diff > 0 else 0)
    balance = calculate_balance - total['purchase_pay']

    if balance > 0:
        status = "Receivable"
    elif balance < 0:
        status = "Payable"
    else:
        status = "Balanced"

    # Convert balance to words
    def amount_to_words(amount):
        try:
            amount_int = int(abs(amount))
            words = num2words(amount_int).replace(',', '').lower()
            return f"{words} taka only"
        except Exception:
            return f"{amount} taka only"

    context = {
        'sitesupervisor': sitesupervisor,
        'payments': payments,
        'total': total,
        'balance': abs(balance),
        'status': status,
        'balance_in_words': amount_to_words(balance),
        'print_time': now(),
    }

    return render(request, 'requisitions/bill_requi_app_pay_pdf.html', context)
    
    
    
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import BillRequisitionApprovalPaymentForm

@login_required
def bill_approval_payment_edit(request, pk):
    payment = get_object_or_404(BillRequisitionApprovalPayment, pk=pk)

    if request.method == 'POST':
        form = BillRequisitionApprovalPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            # Save payment first
            payment = form.save(commit=False)
            payment.save()

            # Only proceed if debit_voucher exists
            debit_voucher = payment.debit_voucher
            if debit_voucher:
                tbl_id = str(debit_voucher.id).strip() 
                tbl_name = 'Payment'

                # --------------------
                # Update existing LedgerEntry if it exists
                # --------------------
                try:
                    ledger_entry = LedgerEntry.objects.get(tbl_id=tbl_id, tbl_name=tbl_name)
                    ledger_entry.debit = payment.requi_amount
                    ledger_entry.date = payment.requisition_date or ledger_entry.date
                    ledger_entry.save()
                except LedgerEntry.DoesNotExist:
                    pass  # Skip if ledger entry doesn't exist

                # --------------------
                # Update existing TransactionHistory if it exists
                # --------------------
                try:
                    trans_history = TransactionHistory.objects.get(tbl_id=tbl_id, tbl_name=tbl_name)
                    trans_history.amount = payment.requi_amount
                    trans_history.date = payment.requisition_date or trans_history.date
                    trans_history.save()
                except TransactionHistory.DoesNotExist:
                    pass  # Skip if transaction history doesn't exist

            messages.success(request, 'Payment updated successfully')
            return redirect('bill_reqs_payment_list')

    else:
        form = BillRequisitionApprovalPaymentForm(instance=payment)

    return render(request, 'requisitions/bill_approval_payment_edit.html', {
        'form': form,
        'payment': payment
    })




@login_required
def bill_approval_payment_delete(request, pk):
    payment = get_object_or_404(BillRequisitionApprovalPayment, pk=pk)

    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully')
        return redirect('bill_reqs_payment_list')

    return render(request, 'requisitions/bill_approval_payment_delete.html', {
        'payment': payment
    })
    
        
@csrf_exempt
def requisition_update_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            req_id = data.get("id")
            qty = float(data.get("qty", 0))
            rate = float(data.get("rate", 0))
            discount = float(data.get("discount", 0))

            requisition = Requisition.objects.get(id=req_id)

            # ✅ Recalculate amount with discount
            amount = (qty * rate) - discount
            if amount < 0:
                amount = 0

            requisition.qty = qty
            requisition.rate = rate
            requisition.discount = discount
            requisition.amount = amount
            requisition.save(update_fields=["qty", "rate", "discount", "amount"])

            return JsonResponse({
                "success": True,
                "id": requisition.id,
                "qty": qty,
                "rate": rate,
                "discount": discount,
                "amount": round(amount, 2)
            })

        except Requisition.DoesNotExist:
            return JsonResponse({"success": False, "error": "Item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
        


# @login_required
# def bill_requisition_confirmation(request):
#     project_id = request.GET.get('project_id')
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
#             for item_id in selected_ids:
#                 requiUniq_id = int(time.time())
#                 try:
#                     item = BillRequisition.objects.get(id=item_id)
#                     item.approv_status = approval_status
#                     item.approv_note = note
#                     item.requi_uniq_id = requiUniq_id
#                     item.save()
                  
#                     try:
#                         user = User.objects.get(username=item.employee_name.emp_name)
#                         notified_users.add(user)
#                     except User.DoesNotExist:
#                         pass
#                     if item.type.lower() == "supplier":
#                         supplier_obj = Suppliers.objects.filter(supplier_name=item.vendor_name).first()
#                         typeName = supplier_obj  
#                         contructor_obj = None
#                     else:
#                         contructor_obj = SiteSupervisor.objects.filter(supervisor_name=item.vendor_name).first()
#                         typeName = None
#                         supplier_obj = None
                    
#                     payAmountDR = 0
#                     payAmountCR = 0
                    
#                     if item.approv_purch_note == "Payment":
#                         payAmountDR = item.amount or 0
#                     else:
#                         payAmountCR = item.amount or 0
                        
                    
#                     cashtype_obj = CashType.objects.filter(cash_type_name='Cash').first()
                   
#                     if item.approv_status == "approved":
#                         LedgerEntry.objects.create(
#                             project_name=item.project_name,
#                             type=item.type,   
#                             contructor=contructor_obj,      
#                             vendor=supplier_obj,           
#                             customer_name=None,
#                             bankName=None,
#                             capi_name=None,
#                             exp_name=None,   
#                             empl_name=None,
#                             invest_name=None,
#                             balance_trf=None,
#                             cash_type=cashtype_obj,
#                             cheque_number=None,
#                             head=item.head_of_account,      
#                             mr_or_bill_no=item.mr_or_bill_no,
#                             date=item.requisition_date or timezone.now().date(),
#                             description=f"Bill requisition approved for {item.vendor_name or 'N/A'}",
#                             debit=payAmountDR,
#                             credit=payAmountCR,
#                             carrier=None,
#                             loan_status=None,
#                             type_name=item.vendor_name     
#                         )
        
#                 except BillRequisition.DoesNotExist:
#                     continue

#             # 🔹 Notify users
#             for user in notified_users:
#                 Notification.objects.create(
#                     sender=request.user,
#                     recipient=user,
#                     project_name=project,
#                     message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
#                     is_read=False,
#                     link='',
#                     pass_url='Bill_requisition_accounts_confirm',
#                     role='accounts'
#                 )

#             messages.success(request, "Selected items updated and notifications sent successfully.")
#             return redirect("bill_requisition_list")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # Group requisitions by employee
#     all_requisitions = BillRequisition.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).order_by('employee_name', 'requisition_date')

#     # Group by employee → requisition_date → list of requisitions
#     requisitions_by_employee = defaultdict(lambda: defaultdict(list))
#     for req in all_requisitions:
#         requisitions_by_employee[req.employee_name][req.requisition_date].append(req)

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

#     return render(request, 'billrequisitions/bill_requisition_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': grouped_data,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })


import time
from decimal import Decimal
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.db import transaction

# Ensure models are imported
from .models import (
    BillRequisition,
    BillRequisitionApprovalPayment
)


@login_required
def bill_requisition_confirmation(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status", "").strip()
        note = request.POST.get("note", "")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(f"{request.path}?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(f"{request.path}?project_id={project.id}")

        notified_users = set()

        try:
            with transaction.atomic():
                for item_id in selected_ids:
                    # Generate unique ID timestamp per iteration
                    current_uniq_id = int(time.time())
                    
                    try:
                        item = BillRequisition.objects.get(id=item_id)
                    except BillRequisition.DoesNotExist:
                        continue

                    # Update BillRequisition fields
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.requi_uniq_id = current_uniq_id
                    item.save()

                    # Collect user to notify safely
                    try:
                        if item.employee_name and hasattr(item.employee_name, 'emp_name'):
                            user = User.objects.get(username=item.employee_name.emp_name)
                            notified_users.add(user)
                    except User.DoesNotExist:
                        pass

                    # Resolve Supplier vs Contractor
                    item_type = (item.type or "").strip().lower()
                    if item_type == "supplier":
                        supplier_obj = Suppliers.objects.filter(supplier_name=item.vendor_name).first()
                        contructor_obj = None
                    else:
                        contructor_obj = SiteSupervisor.objects.filter(supervisor_name=item.vendor_name).first()
                        supplier_obj = None

                    # Amounts
                    payAmountDR = Decimal('0.00')
                    payAmountCR = Decimal('0.00')

                    if item.approv_purch_note == "Payment":
                        payAmountDR = item.amount or Decimal('0.00')
                    else:
                        payAmountCR = item.amount or Decimal('0.00')

                    cashtype_obj = CashType.objects.filter(cash_type_name='Cash').first()

                    # Check approval status case-insensitively
                    if approval_status.lower() == "approved":

                        # 2. Insert into BillRequisitionApprovalPayment
                        BillRequisitionApprovalPayment.objects.create(
                            requisition=item,
                            requi_item_name=item.item_name,
                            requi_uniq_id=str(current_uniq_id),
                            contractors=contructor_obj,
                            payment_type='requisition_pay',
                            requi_amount=item.amount or Decimal('0.00'),
                            requi_id=str(item.id),
                            requisition_date=item.requisition_date or timezone.now().date(),
                            debit_voucher=None
                        )

                # Send notifications
                for user in notified_users:
                    Notification.objects.create(
                        sender=request.user,
                        recipient=user,
                        project_name=project,
                        message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='Bill_requisition_accounts_confirm',
                        role='accounts'
                    )

            messages.success(request, "Selected items updated and payment records created successfully.")
            return redirect("bill_requisition_list")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(f"{request.path}?project_id={project.id}")

    # GET Request Processing
    all_requisitions = BillRequisition.objects.filter(
        project_name=project,
        approv_status='pending'
    ).order_by('employee_name', 'requisition_date')

    requisitions_by_employee = defaultdict(lambda: defaultdict(list))
    for req in all_requisitions:
        requisitions_by_employee[req.employee_name][req.requisition_date].append(req)

    grouped_data = {}
    for employee, date_group in requisitions_by_employee.items():
        items_by_date = dict(date_group)
        totals_by_date = {
            date: sum(item.amount or Decimal('0.00') for item in items)
            for date, items in items_by_date.items()
        }
        employee_total = sum(totals_by_date.values())
        grouped_data[employee] = {
            'items_by_date': items_by_date,
            'totals_by_date': totals_by_date,
            'total': employee_total,
        }

    final_total = all_requisitions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    reference_requisition = all_requisitions.first()

    return render(request, 'billrequisitions/bill_requisition_confirmation.html', {
        'project': project,
        'requisitions_by_employee': grouped_data,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })



import traceback
@csrf_exempt 
def bill_requisition_update_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Support single update
            req_id = data.get("id")
            qty = data.get("qty")
            rate = data.get("rate")

            requisition = BillRequisition.objects.get(id=req_id)
            requisition.qty = qty
            requisition.rate = rate
            requisition.amount = float(qty) * float(rate)
            requisition.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method"})




@login_required 
def bill_requisition_edit(request, pk):
    requisition = get_object_or_404(BillRequisition, pk=pk)

    if request.method == 'POST':
        form = BillRequisitionForm(request.POST, instance=requisition)
        if form.is_valid():
            updated = form.save(commit=False)
            # auto calculate amount
            updated.amount = updated.qty * updated.rate
            updated.save()
            messages.success(request, 'Requisition updated successfully.')

            if updated.requi_uniq_id:
                return redirect('bill_requisition_by_project', requi_id=updated.requi_uniq_id)
            else:
                project_id = updated.project_name.id
                requisition_date = updated.requisition_date.strftime('%Y-%m-%d') if updated.requisition_date else ''
                vendor_name = updated.vendor_name or ''
                fallback_url = reverse('bill_requisition_by_fallback', args=[project_id])
                return redirect(f'{fallback_url}?requisition_date={requisition_date}&vendor_name={vendor_name}')
    else:
        form = BillRequisitionForm(instance=requisition)

    context = {
        'form': form,
        'project_list': ProjectFirstLevelName.objects.all(),
        'employee_names': Employee.objects.all(),
        'requisition_list': HeadOfRequisition.objects.all(),
        'supplier_list': Suppliers.objects.all(),
        'contructor_list': SiteSupervisor.objects.all(),
    }
    return render(request, 'billrequisitions/bill_requisition_edit.html', context)




@login_required
def bill_requisition_delete(request, pk):
    requisition = get_object_or_404(BillRequisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('bill_requisition_list')
    return render(request, 'billrequisitions/bill_requisition_delete.html', {'requisition': requisition})
    



@login_required
def requisition_acct_confirmation(request):
    project_id = request.GET.get('project_id')
    employee_list = Employee.objects.exclude(employee_name='Admin')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    reference_requisition = Requisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approv_acct_status = request.POST.get("approv_acct_status")
        approv_acct_note = request.POST.get("approv_acct_note")
        cash_empl = request.POST.get("cash_empl")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(f"{request.path}?project_id={project.id}")

        if not approv_acct_status:
            messages.error(request, "Please select an approval status.")
            return redirect(f"{request.path}?project_id={project.id}")

        try:
            # If grouping items together, use one unique ID for all
            unique_purch_id = int(time.time())

            updated_items = Requisition.objects.filter(id__in=selected_ids)
            for item in updated_items:
                item.approv_acct_status = approv_acct_status
                item.approv_acct_note = approv_acct_note
                item.requi_uniq_id = unique_purch_id
                item.cash_empl = cash_empl
                item.save()

            messages.success(request, "Selected items updated successfully.")
            return redirect("requisition_list")
            #return redirect("requisition_list", pk=updated_items.first().requi_uniq_id)
            

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(f"{request.path}?project_id={project.id}")

    # Group requisitions by employee
    employee_ids = Requisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}
    for emp_id in employee_ids:
        requisitions = Requisition.objects.filter(
            project_name=project,
            employee_name=emp_id,
            approv_status='approved',
            approv_acct_status='pending'
        )
        employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        employee_obj = requisitions.first().employee_name if requisitions.exists() else None
        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = Requisition.objects.filter(
        project_name=project,
        approv_status='approved',
        approv_acct_status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'requisitions/requisition_acct_confirmation.html', {
        'project': project,
        'employee_list': employee_list,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
        'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
        'print_time': datetime.now(),
    })





# @login_required
# def requisition_admin_confirm(request, pk):
#     project = get_object_or_404(ProjectFirstLevelName, id=pk)

#     reference_requisition = Requisition.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).first()

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

#         all_saved = True
#         notified_users = set()

#         try:
#             for item_id in selected_ids:
#                 requiUniq_id = int(time.time())
#                 try:
#                     item = Requisition.objects.get(id=item_id)
#                     item.approv_status = approval_status
#                     item.approv_note = note
#                     item.requi_uniq_id = requiUniq_id
#                     item.save()
                    
#                     try:
#                         user = User.objects.get(username=item.employee_name.emp_name)
#                         notified_users.add(user)
#                     except User.DoesNotExist:

#                         pass

#                 except Requisition.DoesNotExist:
#                     continue

#             if all_saved:
#                 for user in notified_users:
#                     Notification.objects.create(
#                         sender=request.user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='requisition_accounts_confirm',
#                         role='accounts'
#                     )

#             messages.success(request, "Selected items updated and notifications sent successfully.")
#             return redirect("requisition_detail", pk=selected_ids[0])  # first selected ID

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # Group requisitions by employee
#     employee_name = request.GET.get('employeeName') 
#     queryset = Requisition.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     )

#     if employee_name:       
#         queryset = queryset.filter(employee_name__emp_name=employee_name)    
#     employee_total = queryset.aggregate(total=Sum('amount'))['total'] or 0
#     return render(request, 'requisitions/requisition_admin_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': {employee_name: {'items': queryset, 'total': employee_total}},
#         'final_total': queryset.aggregate(total=Sum('amount'))['total'] or 0,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })


@login_required
def requisition_admin_confirm(request, pk):
    project = get_object_or_404(ProjectFirstLevelName, id=pk)

    reference_requisition = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    ).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status")
        note = request.POST.get("note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        notified_users = set()

        try:
            for item_id in selected_ids:
                requiUniq_id = int(time.time())

                try:
                    item = Requisition.objects.get(id=item_id)

                    # ✅ Update requisition approval
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.requi_uniq_id = requiUniq_id
                    item.save()

                    # ✅ Detect supplier from vendor_name (string field)
                    supplier_obj = None
                    if item.vendor_name:
                        supplier_obj = Suppliers.objects.filter(supplier_name=item.vendor_name).first()

                    # ✅ Create new payment record for approved requisition
                    RequisitionApprovalPayment.objects.create(
                        requisition=item,
                        requi_item_name=item.item_name,  # HeadOfRequisition FK
                        requi_uniq_id=str(requiUniq_id),
                        supplier=supplier_obj,
                        payment_type='requisition_pay',
                        requi_amount=item.amount or Decimal("0.00"),
                        requisition_date=item.requisition_date or timezone.now().date()
                    )

                    # ✅ Notify the employee
                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:
                        pass

                except Requisition.DoesNotExist:
                    continue

            # ✅ Create notifications for all relevant users
            for user in notified_users:
                Notification.objects.create(
                    sender=request.user,
                    recipient=user,
                    project_name=project,
                    message=f"Your requisition has been approved for project {project.project_first_name}.",
                    is_read=False,
                    link='',
                    pass_url='requisition_accounts_confirm',
                    role='accounts'
                )

            messages.success(request, "Selected items approved and payment records created successfully.")
            return redirect("requisition_detail", pk=selected_ids[0])

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # ✅ GET request — show pending requisitions
    employee_name = request.GET.get("employeeName")
    queryset = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    )

    if employee_name:
        queryset = queryset.filter(employee_name__emp_name=employee_name)

    employee_total = queryset.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "requisitions/requisition_admin_confirmation.html", {
        "project": project,
        "requisitions_by_employee": {employee_name: {"items": queryset, "total": employee_total}},
        "final_total": queryset.aggregate(total=Sum("amount"))["total"] or 0,
        "current_status": reference_requisition.approv_status if reference_requisition else "",
        "current_note": reference_requisition.approv_note if reference_requisition else "",
    })



@login_required
def requisition_detail(request, pk):  
    requisition = get_object_or_404(Requisition, pk=pk)
    project = requisition.project_name
    
    return render(request, 'requisitions/requisition_details.html', {
        'project': project,
        'requisition': requisition,
    })


@login_required
def requisition_item_detail(request, pk):  
    requisition = get_object_or_404(RequisitionComparative, pk=pk)
    project = requisition.project_name
    
    return render(request, 'requisitions/requisition_item_detail.html', {
        'project': project,
        'requisition': requisition,
    })
    
## requisition category--
@login_required
def requisition_category(request):
    requisitions_category = RequisitionCategory.objects.all()
    return render(request, 'headrequisition/requisition_category.html', {'requisitions_categorys': requisitions_category})

@login_required
def add_requisition_category(request):
    if request.method == 'POST':
        form = RequisitionCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('requisition_category')  
    else:
        form = RequisitionCategoryForm()
    return render(request, 'headrequisition/add_requisition_category.html', {'form': form})


@login_required
def requisition_category_edit(request, pk):
    requis_category = get_object_or_404(RequisitionCategory, pk=pk)    
    if request.method == 'POST':
        form = RequisitionCategoryForm(request.POST, instance=requis_category)
        if form.is_valid():
            form.save()
            return redirect('requisition_category')  
    else:
        form = RequisitionCategoryForm(instance=requis_category)
    
    return render(request, 'headrequisition/requisition_category_edit.html', {
        'form': form
    })


@login_required
def requisition_category_delete(request, pk):
    requis_categorys = get_object_or_404(RequisitionCategory, pk=pk)
    if request.method == 'POST':
        requis_categorys.delete()
        return redirect('requisition_category')
    return render(request, 'headrequisition/requisition_category_delete.html', {
        'requis_categorys': requis_categorys  
    })


## headrequisition --
# @login_required
# def head_of_requisition_list(request):
#     headrequi = HeadOfRequisition.objects.all()
#     return render(request, 'headrequisition/head_of_requisition_list.html', {'headrequi': headrequi})



@login_required
def head_of_requisition_list(request):
    requisitions_category = RequisitionCategory.objects.all()
    headrequi = HeadOfRequisition.objects.all()
    return render(request, 'headrequisition/head_of_requisition_list.html', {'headrequi': headrequi, 'requisitions_categories': requisitions_category})
    


@login_required
def head_of_requisition_pdf(request):
    category_id = request.GET.get("category")  # optional filter
    queryset = HeadOfRequisition.objects.select_related("requi_category").all()

    if category_id:
        queryset = queryset.filter(requi_category_id=category_id)

    # Create response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="head_of_requisition.pdf"'

    # PDF doc
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Head of Requisition Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table Data
    data = [["Category", "Head Name", "Code"]]
    for obj in queryset:
        data.append([
            obj.requi_category.requi_category_name if obj.requi_category else "",
            obj.head_requi_name,
            obj.head_requi_code,
        ])

    # Table styling
    table = Table(data, colWidths=[150, 200, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    return response
    
    
    
@login_required
def add_head_of_requisition(request):   
    requisitions_category = RequisitionCategory.objects.all()

    if request.method == 'POST':
        form = HeadOfRequisitionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('head_of_requisition_list')
    else:
        form = HeadOfRequisitionForm()
    context = {
        'form': form,
        'requisitions_category': requisitions_category,
    }

    return render(request, 'headrequisition/add_head_of_requisition.html', context)





@login_required
def edit_head_of_requisition(request, pk):
    head_requisition = get_object_or_404(HeadOfRequisition, pk=pk)   
    
    if request.method == 'POST':
        form = HeadOfRequisitionForm(request.POST, instance=head_requisition)
        if form.is_valid():
            form.save()
            return redirect('head_of_requisition_list')  
    else:
        form = HeadOfRequisitionForm(instance=head_requisition)
        requisitions_category = RequisitionCategory.objects.all()
    
    return render(request, 'headrequisition/edit_head_of_requisition.html', {
        'form': form,
        'head_account': head_requisition,
        'requisitions_category' : requisitions_category
    })


@login_required
def delete_head_of_requisition(request, pk):
    head_requisition = get_object_or_404(HeadOfRequisition, pk=pk)
    if request.method == 'POST':
        head_requisition.delete()
        return redirect('head_of_requisition_list')
    return render(request, 'headrequisition/delete_head_of_requisition.html', {
        'head_requisition': head_requisition  
    })



## Notification ---
@login_required
def send_notification_to_role(role, message, link=''):
    users = User.objects.filter(groups__name__iexact=role)
    for user in users:
        Notification.objects.create(
            recipient=user,
            role=role,
            message=message,
            link=link
        )

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return HttpResponseRedirect(notification.link or '/')


@login_required
def read_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    if notification.project_name and notification.sender:
        url = reverse(notification.pass_url, args=[notification.project_name.id])
        url += f'?employeeName={notification.sender.username}'
        return HttpResponseRedirect(url)
    if notification.pass_url:
        return redirect(notification.pass_url)
    #return redirect(notification.link or 'dashboard')
    return redirect('dashboard')



# @login_required
# def return_purchase_list(request):
#     projects_first = ProjectFirstLevelName.objects.all()
#     if request.user.is_superuser:
#         Requsit = Requisition.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes"))
#     else:
#         try:
#             employee = Employee.objects.get(emp_name=request.user)
#             Requsit = Requisition.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes"),employee_name=employee)
#         except Employee.DoesNotExist:
#             Requsit = Requisition.objects.none()

#     try:
#         current_employee = Employee.objects.get(emp_name=request.user.username)
#         emp_type = current_employee.emp_type.lower()
#     except Employee.DoesNotExist:
#         emp_type = 'employee'
#         current_employee = None

#     if emp_type == 'admin':
#         employee = Employee.objects.exclude(emp_type__iexact='admin')
#     else:
#         employee = Employee.objects.filter(emp_name=request.user.username).exclude(emp_type__iexact='admin')

#     context = {
#         'Requisitions': Requsit, 
#         'projects_firts': projects_first,
#         'employees': employee
#     }
#     return render(request, 'requisitions/return_purchase_list.html', context)

#.......................

# @login_required
# def return_purchase_list(request):
#     # GET filters
#     project_id = request.GET.get('project_id')
#     supplier_param = request.GET.get('supplier_id')
#     conductor_id = request.GET.get('conductor')
#     reqiDate = request.GET.get('reqiDate')

#     # Dropdowns (always needed)
#     projects_first = ProjectFirstLevelName.objects.all()
#     all_suppliers = Suppliers.objects.all()

#     # Get current employee role
#     try:
#         current_employee = Employee.objects.get(emp_name=request.user.username)
#         emp_type = current_employee.emp_type.lower()
#     except Employee.DoesNotExist:
#         current_employee = None
#         emp_type = 'employee'

#     # Base filter (return not done, and purchase approved)
#     if request.user.is_superuser:
#         base_queryset = Requisition.objects.filter(
#             Q(return_requisition__isnull=True) | ~Q(return_requisition='Yes'),
#             purch_appov='Yes'
#         )
#     else:
#         try:
#             employee = Employee.objects.get(emp_name=request.user)
#             base_queryset = Requisition.objects.filter(
#                 Q(return_requisition__isnull=True) | ~Q(return_requisition='Yes'),
#                 purch_appov='Yes',
#                 employee_name=employee
#             )
#         except Employee.DoesNotExist:
#             base_queryset = Requisition.objects.none()

#     # If filters are provided, apply additional filtering
#     if project_id:
#         try:
#             project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
#         except ValueError:
#             return HttpResponse("Invalid project ID.", status=400)

#         requisition_filter = Q(project_name=project)
#         supplier = None
#         filtered_suppliers = None

#         # Handle supplier filter (by ID or name, but vendor_name is CharField)
#         if supplier_param:
#             supplier_param = supplier_param.strip()
#             try:
#                 # Try treating as supplier ID
#                 supplier_obj = Suppliers.objects.get(id=int(supplier_param))
#                 requisition_filter &= Q(vendor_name__iexact=supplier_obj.supplier_name)
#                 filtered_suppliers = [supplier_obj]
#                 supplier = supplier_obj
#             except (ValueError, Suppliers.DoesNotExist):
#                 # Try by name (case-insensitive)
#                 try:
#                     supplier_obj = Suppliers.objects.get(supplier_name__iexact=supplier_param)
#                     requisition_filter &= Q(vendor_name__iexact=supplier_obj.supplier_name)
#                     filtered_suppliers = [supplier_obj]
#                     supplier = supplier_obj
#                 except Suppliers.DoesNotExist:
#                     return HttpResponse("Supplier not found.", status=404)

#         # Handle conductor filter
#         elif conductor_id and conductor_id.isdigit():
#             try:
#                 conductor = Suppliers.objects.get(id=int(conductor_id))
#                 requisition_filter &= Q(vendor_name__iexact=conductor.supplier_name)
#                 filtered_suppliers = [conductor]
#                 supplier = conductor
#             except Suppliers.DoesNotExist:
#                 return HttpResponse("Conductor not found.", status=404)

#         # Handle purchase date filter
#         if reqiDate:
#             try:
#                 parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
#                 requisition_filter &= Q(purch_date=parsed_date)
#             except ValueError:
#                 return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

#         # Final filtered result
#         requisition_items = base_queryset.filter(requisition_filter)

#         # Collect all suppliers used if not already filtered
#         if not filtered_suppliers:
#             supplier_names = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
#             filtered_suppliers = Suppliers.objects.filter(supplier_name__in=supplier_names)

#         # Summation & date
#         total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
#         requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

#         # Helper: amount in words
#         def amount_to_words(amount):
#             amount = round(float(amount), 2)
#             taka = int(amount)
#             poisha = int(round((amount - taka) * 100))
#             taka_words = num2words(taka, lang='en').capitalize() + " Taka"
#             return f"{taka_words} and {num2words(poisha, lang='en')} Poisha" if poisha > 0 else taka_words

#         context = {
#             'project': project,
#             'supplier': supplier,
#             'suppliers': filtered_suppliers,
#             'Requisitions': requisition_items,
#             'total_amount': total_amount,
#             'amount_in_words': amount_to_words(total_amount),
#             'print_time': now(),
#             'requisition_date': requisition_date,
#             'projects_firts': projects_first,
#         }
#         return render(request, 'requisitions/return_purchase_list.html', context)
    

#     if emp_type == 'admin':
#         employees = Employee.objects.exclude(emp_type__iexact='admin')
#     else:
#         employees = Employee.objects.filter(emp_name=request.user.username).exclude(emp_type__iexact='admin')

#     requisitions = base_queryset  
   
#     for requisition in requisitions:
#         if requisition.return_qty is not None:
#             requisition.qty_after_return = requisition.qty - requisition.return_qty
#         else:
#             requisition.qty_after_return = requisition.qty
        
#         if hasattr(requisition, 'rate') and requisition.rate is not None:
#             requisition.amount_after_return = requisition.qty_after_return * requisition.rate
#         else:
#             requisition.amount_after_return = requisition.amount  # fallback

#     context = {
#         'projects_firts': projects_first,
#         'employees': employees,
#         'suppliers': all_suppliers,
#         'requisitions': requisitions,
#     }
#     return render(request, 'requisitions/return_purchase_list.html', context)


from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import datetime
from num2words import num2words


@login_required
def return_purchase_list(request):

    # ================= GET FILTERS =================
    project_id = request.GET.get('project_id')
    supplier_id = request.GET.get('supplier_id')
    conductor_id = request.GET.get('conductor')
    reqiDate = request.GET.get('reqiDate')

    # ================= DROPDOWNS =================
    projects_first = ProjectFirstLevelName.objects.all()
    all_suppliers = Suppliers.objects.all()

    # ================= CURRENT EMPLOYEE =================
    try:
        current_employee = Employee.objects.get(emp_name=request.user.username)
        emp_type = current_employee.emp_type.lower()
    except Employee.DoesNotExist:
        current_employee = None
        emp_type = 'employee'

    # ================= BASE QUERYSET =================
    if request.user.is_superuser:
        base_queryset = Inventories.objects.all()
    else:
        if current_employee:
            base_queryset = Inventories.objects.filter(employee_name=current_employee)
        else:
            base_queryset = Inventories.objects.none()

    # ================= FILTER SECTION =================
    if project_id:
        try:
            project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
        except ValueError:
            return HttpResponse("Invalid project ID", status=400)

        inventory_filter = Q(project_name=project)
        supplier = None
        filtered_suppliers = None

        # Supplier filter
        if supplier_id:
            try:
                supplier = Suppliers.objects.get(id=int(supplier_id))
                inventory_filter &= Q(vendor_name=supplier)
                filtered_suppliers = [supplier]
            except (ValueError, Suppliers.DoesNotExist):
                return HttpResponse("Supplier not found", status=404)

        # Conductor filter
        elif conductor_id and conductor_id.isdigit():
            try:
                supplier = Suppliers.objects.get(id=int(conductor_id))
                inventory_filter &= Q(vendor_name=supplier)
                filtered_suppliers = [supplier]
            except Suppliers.DoesNotExist:
                return HttpResponse("Conductor not found", status=404)

        # Purchase date filter
        if reqiDate:
            try:
                parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
                inventory_filter &= Q(purch_date=parsed_date)
            except ValueError:
                return HttpResponse("Invalid date format (YYYY-MM-DD)", status=400)

        inventories = base_queryset.filter(inventory_filter)

        # Supplier list (auto)
        if not filtered_suppliers:
            filtered_suppliers = Suppliers.objects.filter(
                id__in=inventories.values_list('vendor_name', flat=True)
            )

        # ================= CALCULATION (CORRECT) =================
        for inv in inventories:
            remaining_qty = inv.qty - inv.qtysub
            inv.qty_after_return = max(remaining_qty, 0)

            if inv.amount and inv.amount > 0 and inv.qty > 0:
                inv.amount_after_return = (inv.amount / inv.qty) * inv.qty_after_return
            else:
                inv.amount_after_return = inv.qty_after_return * inv.rate

        total_amount = sum(inv.amount_after_return for inv in inventories)

        requisition_date = inventories.first().requisition_date if inventories.exists() else None

        def amount_to_words(amount):
            amount = round(float(amount), 2)
            taka = int(amount)
            poisha = int(round((amount - taka) * 100))
            taka_words = num2words(taka, lang='en').capitalize() + " Taka"
            return (
                f"{taka_words} and {num2words(poisha, lang='en')} Poisha"
                if poisha > 0 else taka_words
            )

        context = {
            'project': project,
            'supplier': supplier,
            'suppliers': filtered_suppliers,
            'inventories': inventories,
            'total_amount': total_amount,
            'amount_in_words': amount_to_words(total_amount),
            'print_time': now(),
            'requisition_date': requisition_date,
            'projects_firts': projects_first,
        }

        return render(request, 'requisitions/return_purchase_list.html', context)

    # ================= DEFAULT LIST =================
    if emp_type == 'admin':
        employees = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employees = Employee.objects.filter(
            emp_name=request.user.username
        ).exclude(emp_type__iexact='admin')

    inventories = base_queryset

    # ================= CALCULATION (CORRECT) =================
    for inv in inventories:
        remaining_qty = inv.qty - inv.qtysub
        inv.qty_after_return = max(remaining_qty, 0)

        if inv.amount and inv.amount > 0 and inv.qty > 0:
            inv.amount_after_return = (inv.amount / inv.qty) * inv.qty_after_return
        else:
            inv.amount_after_return = inv.qty_after_return * inv.rate

    context = {
        'projects_firts': projects_first,
        'employees': employees,
        'suppliers': all_suppliers,
        'inventories': inventories,
    }

    return render(request, 'requisitions/return_purchase_list.html', context)




# @login_required
# def approve_return_voucher(request, pk):
#     voucher = DebitVoucher.objects.filter(requi_id=pk).first()
#     if not voucher:
#         messages.error(request, "Voucher not found.")
#         return redirect('return_purchase_list')
#     if voucher.approval_dr_status:
#         voucher.approval_dr_status = True
#         voucher.return_requisition = "Yes"
#         voucher.save()

#         try:
#             requisition = Requisition.objects.get(pk=pk)
#             requisition.return_requisition = "Yes"
#             requisition.save()
#         except Requisition.DoesNotExist:
#             pass
#         try:
#             cash_type = CashType.objects.get(type_name=voucher.cash_type)
#             current_balance = cash_type.type_amount or 0
#             cash_type.type_amount = current_balance + voucher.amount
#             cash_type.type_note = f"Debited on approval of voucher ID {voucher.id}"
#             cash_type.save()
#         except CashType.DoesNotExist:
#             cash_type = None

#         # Log the transaction if cash_type exists
#         if cash_type:
#             TransactionHistory.objects.create(
#                 project=voucher.project_name,
#                 transaction_type=voucher.type,
#                 head_of_account=voucher.head_of_account,
#                 cash_type=cash_type,
#                 amount=voucher.amount,
#                 date=voucher.date,
#                 reference=voucher.mr_or_bill_no,
#             )
#     else:
#         messages.warning(request, "This voucher has no approved Yeat.") 
#     return redirect('return_purchase_list')



# @login_required
# def approve_return_voucher(request, pk):
#     if request.method == 'POST':
#         return_qty = request.POST.get('return_qty')
#         return_status = request.POST.get('return_status')
        
#         try:
#             return_qty = int(return_qty)
#         except (TypeError, ValueError):
#             messages.error(request, "Invalid return quantity.")
#             return redirect('return_purchase_list')

#         requisition = get_object_or_404(Requisition, pk=pk)
        
#         if not requisition.qty or return_qty > requisition.qty:
#             messages.error(request, f"Return quantity cannot exceed original quantity ({requisition.qty}).")
#             return redirect('return_purchase_list')

#         # Get the CreditVoucher linked to this requisition
#         credit_voucher = CreditVoucher.objects.filter(requi_id=pk).first()

#         if not credit_voucher:
#             messages.error(request, "Related Credit Voucher not found.")
#             return redirect('return_purchase_list')

#         # Get cash_type from the voucher
#         cash_type = credit_voucher.cash_type

#         if not cash_type:
#             messages.error(request, "Cash Type not found for this voucher.")
#             return redirect('return_purchase_list')

#         # Calculate credit amount
#         credit_amount = requisition.rate * return_qty

#         from datetime import date
#         today = date.today()

#         # Create a new return CreditVoucher (optional or overwrite existing)
#         return_voucher = CreditVoucher.objects.create(
#             project=requisition.project_name,
#             type="Return",
#             cash_type=cash_type,
#             head_of_account=requisition.item_name,
#             mr_or_bill_no=f"Return-{requisition.id}",
#             date=today,
#             amount=credit_amount,
#             particulars=f"Return of items for requisition {requisition.id}",
#             confirmation="Yes",
#             requi_id=requisition.id
#         )

#         # Update requisition
#         requisition.return_qty = return_qty
#         requisition.return_status = return_status
#         requisition.save()

#         # Update or create inventory
#         inventory, created = Inventories.objects.get_or_create(requi_id=requisition.id, defaults={
#             'project_name': requisition.project_name,
#             'employee_name': requisition.employee_name,
#             'item_name': requisition.item_name,
#             'vendor_name': None,
#             'unit': '',
#             'qty': 0,
#             'rate': 0,
#             'amount': 0,
#             'remark': '',
#             'requisition_date': requisition.requisition_date,
#             'purch_date': today
#         })

#         inventory.qtysub = return_qty
#         inventory.remark = f"Returned ({return_status})"
#         inventory.purch_date = today
#         inventory.save()

#         # Update cash type balance
#         cash_type.type_amount += credit_amount
#         cash_type.type_note = f"Credited on return for requisition ID {requisition.id}"
#         cash_type.save()

#         # Transaction log
#         TransactionHistory.objects.create(
#             project=requisition.project_name,
#             transaction_type="Return",
#             head_of_account=requisition.item_name,
#             cash_type=cash_type,
#             amount=credit_amount,
#             date=today,
#             reference=f"Return-{requisition.id}",
#         )

#         messages.success(request, "Return processed successfully.")

#     return redirect('return_purchase_list')



# @login_required
# def approve_return_voucher(request, pk):
#     if request.method == 'POST':
#         return_qty = request.POST.get('return_qty')
#         return_status = request.POST.get('return_status')

#         # Validate return_qty is a decimal number
#         try:
#             return_qty = float(return_qty)
#         except (TypeError, ValueError):
#             messages.error(request, "Invalid return quantity.")
#             return redirect('return_purchase_list')

#         requisition = get_object_or_404(Requisition, pk=pk)

#         # Update fields
#         requisition.return_qty = return_qty
#         requisition.return_status = return_status
#         requisition.return_requisition = "Yes"
#         requisition.save()

#         messages.success(request, "Requisition updated successfully.")

#     return redirect('return_purchase_list')


# from django.db.models import F

# @login_required
# def approve_return_voucher(request, pk):
#     if request.method == 'POST':
#         return_qty = request.POST.get('return_qty')
#         return_status = request.POST.get('return_status')

#         # Validate return_qty is a decimal number
#         try:
#             return_qty = float(return_qty)
#         except (TypeError, ValueError):
#             messages.error(request, "Invalid return quantity.")
#             return redirect('return_purchase_list')

#         requisition = get_object_or_404(Requisition, pk=pk)

#         # If previous return_qty exists, add new value to it
#         if requisition.return_qty is not None:
#             return_qty += requisition.return_qty

#         # Update and save
#         requisition.return_qty = return_qty
#         requisition.return_status = return_status
#         requisition.save()

#         try:
#             inventory = Inventories.objects.get(requi_id=pk)

#             new_qty = max(inventory.qty - int(return_qty), 0)
#             new_qtysub = max(inventory.qtysub - int(return_qty), 0)

#             inventory.qty = new_qty
#             inventory.qtysub = new_qtysub

#             # Update amount = new_qty * requisition.rate
#             inventory.amount = new_qty * float(requisition.rate)

#             inventory.save()

#         except Inventories.DoesNotExist:
#             messages.warning(request, "Inventory record not found for this requisition.")

#         messages.success(request, "Requisition and Inventory updated successfully.")

#     return redirect('return_purchase_list')


from decimal import Decimal, InvalidOperation

@login_required
def approve_return_voucher(request, pk):
    if request.method == 'POST':
        return_qty_input = request.POST.get('return_qty')
        return_status = request.POST.get('return_status')

        # Validate return_qty as Decimal
        try:
            return_qty = Decimal(return_qty_input)
        except (TypeError, ValueError, InvalidOperation):
            messages.error(request, "Invalid return quantity.")
            return redirect('return_purchase_list')

        requisition = get_object_or_404(Requisition, pk=pk)

        # Add to existing return_qty if it exists
        if requisition.return_qty:
            return_qty += requisition.return_qty

        # Save updated return values
        requisition.return_qty = return_qty
        requisition.return_status = return_status
        #requisition.return_date = return_status
        requisition.save()

        # Update related inventory
        try:
            inventory = Inventories.objects.get(requi_id=pk)

            new_qty = max(inventory.qty - return_qty, 0)
            new_qtysub = max(inventory.qtysub - return_qty, 0)

            inventory.qty = new_qty
            inventory.qtysub = new_qtysub

            # Calculate updated amount using Decimal
            inventory.amount = new_qty * requisition.rate

            inventory.save()

        except Inventories.DoesNotExist:
            messages.warning(request, "Inventory record not found for this requisition.")

        messages.success(request, "Requisition and Inventory updated successfully.")

    return redirect('return_purchase_list')


# @login_required
# def return_item_list(request):
#     # Only requisitions with return_qty not null
#     requisitions = Requisition.objects.filter(return_qty__isnull=False)
#     return render(request, 'requisitions/return_item_list.html', {'requisitions': requisitions})


@login_required
def return_item_list(request):
    # Only requisitions with return_qty > 0
    requisitions = Requisition.objects.filter(return_qty__gt=0)

    # Add calculated fields for template use
    for r in requisitions:
        r.payment_amount = r.qty * r.rate  # Full payment (Qty Ã— Rate)
        r.received_qty = r.qty - r.return_qty  # Qty after return
        r.received_amount = r.received_qty * r.rate  # Received value
        r.returned_amount = r.payment_amount - r.received_amount 

    return render(request, 'requisitions/return_item_list.html', {
        'requisitions': requisitions
    })

@login_required
def return_purchase_item(request):
    projects_first = ProjectFirstLevelName.objects.all()
    if request.user.is_superuser:
        Requsit = Requisition.objects.filter(return_requisition="Yes")
    else:
        try:
            employee = Employee.objects.get(emp_name=request.user)
            Requsit = Requisition.objects.filter(employee_name=employee, return_requisition="Yes")
        except Employee.DoesNotExist:
            Requsit = Requisition.objects.none()

    try:
        current_employee = Employee.objects.get(emp_name=request.user.username)
        emp_type = current_employee.emp_type.lower()
    except Employee.DoesNotExist:
        emp_type = 'employee'
        current_employee = None

    if emp_type == 'admin':
        employee = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employee = Employee.objects.filter(emp_name=request.user.username).exclude(emp_type__iexact='admin')

    context = {
        'Requisitions': Requsit, 
        'projects_firts': projects_first,
        'employees': employee
    }
    return render(request, 'requisitions/return_purchase_item.html', context)





@login_required
def requisition_approv_list(request):
    project_id = request.GET.get('project_id')
    requi_uniq_id = request.GET.get('requi_uniq_id')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid project ID", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

    # Base filter
    
    base_filter = Q(
        project_name=project,
        approv_status='approved',
        approv_acct_status='approved',
        approv_purch_status='pending'
    )

    if requi_uniq_id:
        base_filter &= Q(requi_uniq_id=requi_uniq_id)

    requisition_queryset = Requisition.objects.filter(base_filter)

    # Suppliers based on vendor_name
    supplier_ids = requisition_queryset.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
    suppliers = Suppliers.objects.filter(id__in=supplier_ids)

    reference_requisition = requisition_queryset.first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approv_purch_status = request.POST.get("approv_purch_status")
        approv_purch_note = request.POST.get("approv_purch_note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.get_full_path())

        if not approv_purch_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.get_full_path())

        try:
            updated_items = []

            for item_id in selected_ids:
                item = Requisition.objects.get(id=item_id)

                vendor_field_name = f"vendor_{item_id}"
                vendor_name = request.POST.get(vendor_field_name, '').strip()

                qty_field_name = f"qty_{item_id}"
                rate_field_name = f"rate_{item_id}"

                qty_raw = request.POST.get(qty_field_name)
                rate_raw = request.POST.get(rate_field_name)

                try:
                    qty = float(qty_raw) if qty_raw else item.qty
                except ValueError:
                    qty = item.qty

                try:
                    rate = float(rate_raw) if rate_raw else item.rate
                except ValueError:
                    rate = item.rate

                #item.vendor_name = vendor_name
                item.approv_purch_status = approv_purch_status
                item.approv_purch_note = approv_purch_note
                item.purch_appov = 'Wait'
                item.save()
                updated_items.append(item)

            # Filter for fully approved items
            approved_items = [
                item for item in updated_items
                if item.approv_status == 'approved' and
                   item.approv_acct_status == 'approved' and
                   item.approv_purch_status == 'approved'
            ]

            if approved_items:
                vendor_group = defaultdict(list)
                for item in approved_items:
                    vendor_group[item.vendor_name].append(item)

                for vendor_name_str, items in vendor_group.items():
                    try:
                        vendor_obj = Suppliers.objects.get(supplier_name=vendor_name_str)
                    except Suppliers.DoesNotExist:
                        vendor_obj = None

                    unique_purch_id = int(time.time())

                    # for item in items:
                    #     # Extract qty and rate again
                    #     qty_field_name = f"qty_{item.id}"
                    #     rate_field_name = f"rate_{item.id}"

                    #     qty_raw = request.POST.get(qty_field_name)
                    #     rate_raw = request.POST.get(rate_field_name)

                    #     try:
                    #         qty = float(qty_raw) if qty_raw else item.qty
                    #     except ValueError:
                    #         qty = item.qty

                    #     try:
                    #         rate = float(rate_raw) if rate_raw else item.rate
                    #     except ValueError:
                    #         rate = item.rate

                    #     amount = qty * rate
                    
                    for item in items:
                        # Extract qty and rate again
                        qty_field_name = f"qty_{item.id}"
                        rate_field_name = f"rate_{item.id}"
                        amount_field_name = f"amount_{item.id}"

                        qty_raw = request.POST.get(qty_field_name)
                        rate_raw = request.POST.get(rate_field_name)
                        amount_raw = request.POST.get(amount_field_name)

                        try:
                            qty = float(qty_raw) if qty_raw else item.qty
                        except ValueError:
                            qty = item.qty

                        try:
                            rate = float(rate_raw) if rate_raw else item.rate
                        except ValueError:
                            rate = item.rate
                        
                        try:
                            amount = float(amount_raw) if amount_raw else item.amount
                        except ValueError:
                            amount = item.amount

                        #amount = qty * rate
                        

                        Inventories.objects.create(
                            project_name=item.project_name,
                            employee_name=item.employee_name,
                            vendor_name=vendor_obj,
                            item_name=item.item_name,
                            unit=item.unit,
                            qty=qty,
                            rate=rate,
                            amount=amount,
                            remark=item.remark,
                            approv_note=item.approv_note,
                            approv_acct_note=item.approv_acct_note,
                            approv_purch_note=item.approv_purch_note,
                            requisition_date=item.requisition_date,
                            requi_id=item.id,
                            qtysub=qty,
                            purch_id=unique_purch_id,
                            purch_date=timezone.now().date()
                        )                        
                        item.purch_id = unique_purch_id
                        item.purch_date = timezone.now().date()
                        item.save()
                        
                        # ✅ Insert or update RequisitionApprovalPayment
                        if vendor_obj:
                            RequisitionApprovalPayment.objects.update_or_create(
                                requisition=item,
                                requi_uniq_id=item.requi_uniq_id,
                                supplier=vendor_obj,
                                defaults={
                                    'payment_type': 'purchase_pay',
                                    'requi_item_name': item.item_name or "N/A",
                                    'requi_amount': amount,
                                    'requisition_date': item.requisition_date or timezone.now().date()
                                }
                            )

                messages.success(request, "Selected items updated and inventory records inserted.")
                return redirect("purchase_list")  # âœ… Ensure this matches your urls.py
            else:
                messages.warning(request, "No fully approved items found.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.get_full_path())

    # Grouping requisitions for UI
    vendor_ids = requisition_queryset.values_list('vendor_name', flat=True).distinct()
    requisitions_by_vendor = {}
    for ven_id in vendor_ids:
        vendor_items = requisition_queryset.filter(vendor_name=ven_id)
        vendor_total = vendor_items.aggregate(total=Sum('amount'))['total'] or 0
        vendor_obj = vendor_items.first().vendor_name if vendor_items.exists() else None
        requisitions_by_vendor[vendor_obj] = {
            'items': vendor_items,
            'total': vendor_total
        }

    final_total = requisition_queryset.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'requisitions/requisition_approv_list.html', {
        'project': project,
        'requisitions_by_vendor': requisitions_by_vendor,
        'final_total': final_total,
        'current_status': reference_requisition.approv_purch_status if reference_requisition else '',
        'current_note': reference_requisition.approv_purch_note if reference_requisition else '',
        'suppliers': suppliers,
        'supplier_list': Suppliers.objects.all(),
        'contructors_list': SiteSupervisor.objects.all(),
        'headOfexpense_list': HeadOfExpense.objects.all(),
    })
    
    
    
    


# @login_required
# def requisition_approv_list(request):
#     project_id = request.GET.get('project_id')
#     supplier_id = request.GET.get('supplier_id')
    

#     # Validate project ID
#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid project ID.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

#     supplier = None
#     if supplier_id and supplier_id.isdigit():
#         supplier = get_object_or_404(Suppliers, id=int(supplier_id))

#     # Get a reference requisition (any one for note/status display)
#     reference_requisition = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='approved',
#         approv_purch_status='pending',
#         vendor_name=supplier if supplier else None
#     ).first()

#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_items")
#         approv_purch_status = request.POST.get("approv_purch_status")
#         approv_purch_note = request.POST.get("approv_purch_note")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(request.path + f"?project_id={project.id}&supplier_id={supplier.id if supplier else ''}")

#         if not approv_purch_status:
#             messages.error(request, "Please select an approval status.")
#             return redirect(request.path + f"?project_id={project.id}&supplier_id={supplier.id if supplier else ''}")

#         try:
#             updated_items = []

#             for item_id in selected_ids:
#                 item = Requisition.objects.get(id=item_id)
#                 item.approv_purch_status = approv_purch_status
#                 item.approv_purch_note = approv_purch_note
#                 item.save()
#                 updated_items.append(item)

#             # Filter approved requisition items
#             approved_items = [
#                 item for item in updated_items
#                 if item.approv_status == 'approved' and
#                    item.approv_acct_status == 'approved' and
#                    item.approv_purch_status == 'approved'
#             ]

#             if approved_items:
#                 # Group items by vendor
#                 vendor_group = defaultdict(list)
#                 for item in approved_items:
#                     vendor_group[item.vendor_name].append(item)

#                 for vendor, items in vendor_group.items():
#                     unique_purch_id = int(time.time())  # per vendor
#                     time.sleep(1)  # prevent same timestamp for next vendor

#                     for item in items:
#                         Inventories.objects.create(
#                             project_name=item.project_name,
#                             employee_name=item.employee_name,
#                             vendor_name=item.vendor_name,
#                             item_name=item.item_name,
#                             unit=item.unit,
#                             qty=item.qty,
#                             rate=item.rate,
#                             amount=item.amount,
#                             remark=item.remark,
#                             approv_note=item.approv_note,
#                             approv_acct_note=item.approv_acct_note,
#                             approv_purch_note=item.approv_purch_note,
#                             requisition_date=item.requisition_date,
#                             requi_id=item.id,
#                             qtysub=item.qty,
#                             purch_id=unique_purch_id
#                         )

#                 messages.success(request, "Selected items updated and inventory records inserted.")
#                 return redirect("purchase_list")
#             else:
#                 messages.warning(request, "No approved requisition items to create inventory records.")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}&supplier_id={supplier.id if supplier else ''}")

#     # Requisition Queryset for filter
#     requisition_filter = {
#         'project_name': project,
#         'approv_status': 'approved',
#         'approv_acct_status': 'approved',
#         'approv_purch_status': 'pending'
#     }
#     if supplier:
#         requisition_filter['vendor_name'] = supplier

#     requisition_queryset = Requisition.objects.filter(**requisition_filter)

#     # Group requisitions by vendor
#     vendor_ids = requisition_queryset.values_list('vendor_name', flat=True).distinct()

#     requisitions_by_vendor = {}
#     for ven_id in vendor_ids:
#         requisitions = requisition_queryset.filter(vendor_name=ven_id)
#         vendor_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#         vendor_obj = requisitions.first().vendor_name if requisitions.exists() else None
#         requisitions_by_vendor[vendor_obj] = {
#             'items': requisitions,
#             'total': vendor_total
#         }

#     final_total = requisition_queryset.aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'requisitions/requisition_approv_list.html', {
#         'project': project,
#         'requisitions_by_vendor': requisitions_by_vendor,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_purch_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_purch_note if reference_requisition else '',
#     })



## Requision Summary - Vendor wise ---




# @login_required
# def requisition_item_summary(request):
#     project_id = request.GET.get('project_id')
#     supplier_param = request.GET.get('supplier_id')  # Can be name or ID
#     conductor_id = request.GET.get('conductor')
#     status = request.GET.get('status')
#     reqiDate = request.GET.get('reqiDate')

#     # Validate project
#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
#     requisition_filter = Q(project_name=project)

#     supplier = None
#     suppliers = None

#     # andle supplier name or ID
#     if supplier_param:
#         try:
#             # Try treating as ID
#             supplier = Suppliers.objects.get(id=int(supplier_param))
#         except (ValueError, Suppliers.DoesNotExist):
#             # Try treating as name (case-insensitive)
#             try:
#                 supplier = Suppliers.objects.get(supplier_name__iexact=supplier_param)
#             except Suppliers.DoesNotExist:
#                 return HttpResponse("Supplier not found.", status=404)

#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]

#     # Conductor filter by ID
#     elif conductor_id and conductor_id.isdigit():
#         supplier = get_object_or_404(Suppliers, id=int(conductor_id))
#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]

#     # Status filter (case-insensitive)
#     if status and status.lower() in ['pending', 'approved', 'rejected']:
#         requisition_filter &= Q(approv_status__iexact=status)

#     # Date filter
#     if reqiDate:
#         try:
#             parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
#             requisition_filter &= Q(requisition_date=parsed_date)
#         except ValueError:
#             return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

#     # inal filtered query
#     requisition_items = Requisition.objects.filter(requisition_filter)

#     if not suppliers:
#         supplier_ids = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
#         suppliers = Suppliers.objects.filter(id__in=supplier_ids)

#     total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
#     requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

#     def amount_to_words(amount):
#         amount = round(float(amount), 2)
#         taka = int(amount)
#         poisha = int(round((amount - taka) * 100))

#         taka_words = num2words(taka, lang='en').capitalize() + " Taka"

#         if poisha > 0:
#             poisha_words = num2words(poisha, lang='en') + " Poisha"
#             return f"{taka_words} and {poisha_words}"
#         else:
#             return f"{taka_words}"
    
#     context = {
#         'project': project,
#         'supplier': supplier,
#         'suppliers': suppliers,
#         'requisition_items': requisition_items,
#         'total_amount': total_amount,
#         'amount_in_words': amount_to_words(total_amount),
#         'print_time': now(),
#         'requisition_date': requisition_date,
#     }
#     return render(request, 'requisitions/requisition_item_summary.html', context)

from django.db.models import Sum, Q
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import datetime
from num2words import num2words

# Import your models (Requisition, Inventories, etc.)

@login_required
def requisition_item_summary(request):
    project_id = request.GET.get('project_id')
    supplier_param = request.GET.get('supplier_id')  # Can be name or ID
    conductor_id = request.GET.get('conductor')
    status = request.GET.get('status')
    reqiDate = request.GET.get('reqiDate')

    # Validate project
    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
    requisition_filter = Q(project_name=project)

    supplier = None
    suppliers = None

    # Handle supplier name or ID
    if supplier_param:
        try:
            supplier = Suppliers.objects.get(id=int(supplier_param))
        except (ValueError, Suppliers.DoesNotExist):
            try:
                supplier = Suppliers.objects.get(supplier_name__iexact=supplier_param)
            except Suppliers.DoesNotExist:
                return HttpResponse("Supplier not found.", status=404)

        requisition_filter &= Q(vendor_name=supplier)
        suppliers = [supplier]

    # Conductor filter by ID
    elif conductor_id and conductor_id.isdigit():
        supplier = get_object_or_404(Suppliers, id=int(conductor_id))
        requisition_filter &= Q(vendor_name=supplier)
        suppliers = [supplier]

    # Status filter
    if status and status.lower() in ['pending', 'approved', 'rejected']:
        requisition_filter &= Q(approv_status__iexact=status)

    # Date filter
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
            requisition_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

    # Final filtered query
    requisition_items = Requisition.objects.filter(requisition_filter)

    # --- INVENTORY AVAILABLE QTY CALCULATION ---
    for item in requisition_items:
        # Calculate total issued/subtracted stock (qtysub) for this project and item
        total_qtysub = Inventories.objects.filter(
            project_name=project,
            item_name=item.item_name
        ).aggregate(total_sub=Sum('qtysub'))['total_sub'] or 0

        # Calculate total added stock (qty) for this project and item
        total_qty_added = Inventories.objects.filter(
            project_name=project,
            item_name=item.item_name
        ).aggregate(total_add=Sum('qty'))['total_add'] or 0

        # Available Stock = Total Added - Total Subtracted
        item.available_qty = total_qty_added - total_qtysub
    # -------------------------------------------

    if not suppliers:
        supplier_ids = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
        suppliers = Suppliers.objects.filter(id__in=supplier_ids)

    total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
    requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

    def amount_to_words(amount):
        try:
            amount = round(float(amount), 2)
            taka = int(amount)
            poisha = int(round((amount - taka) * 100))

            # Change lang to 'en_IN' to format in Lakh/Crore
            taka_words = num2words(taka, lang='en_IN').title() + " Taka"

            if poisha > 0:
                poisha_words = num2words(poisha, lang='en_IN').title() + " Poisha"
                return f"{taka_words} and {poisha_words}"
            else:
                return f"{taka_words}"
        except Exception:
            return "Zero Taka"

    context = {
        'project': project,
        'supplier': supplier,
        'suppliers': suppliers,
        'requisition_items': requisition_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
        'requisition_date': requisition_date,
    }
    return render(request, 'requisitions/requisition_item_summary.html', context)

## requisition comparative --
@login_required
def requisition_comparative_list(request):
    requisitions_category = RequisitionComparative.objects.all()
    projects_first = ProjectFirstLevelName.objects.all()
    context = {
        'requisitions_categorys': requisitions_category, 
        'projects_firts': projects_first,
    }
    return render(request, 'headrequisition/requisition_comparative_list.html', context)



@login_required
def add_requisition_comparative(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            items = data.get('data', [])
            employee_id = data.get('employee_id')
            project_id = data.get('project_id')
            remark = data.get('remark', '')

            if not items or not employee_id or not project_id:
                return JsonResponse({'status': 'error', 'message': "Missing data, employee_id, or project_id."})

            try:
                employee = Employee.objects.get(pk=int(employee_id))
            except (Employee.DoesNotExist, ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': f"Invalid employee_id: {employee_id}"})

            try:
                project = ProjectFirstLevelName.objects.get(pk=int(project_id))
            except (ProjectFirstLevelName.DoesNotExist, ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': f"Invalid project_id: {project_id}"})

            for item in items:
                form = RequisitionComparativeForm({
                    'project_name': project.pk,
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name'),
                    'vendor_name': item.get('vendor_name'),
                    'unit': item.get('unit'),
                    'qty': item.get('qty'),
                    'rate': item.get('rate'),
                    'remark': remark,
                    'requisition_date': timezone.now()
                })
                if not form.is_valid():
                    return JsonResponse({'status': 'error', 'message': f"Form errors: {form.errors}"})
                form.save()

            is_admin = request.user.groups.filter(name__iexact='admin').exists()
            sender_user = request.user
            if is_admin:
                try:
                    sender_user = User.objects.get(username=employee.emp_name)
                except User.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f"User '{employee.emp_name}' not found."})

            recipients = User.objects.filter(groups__name__iexact='admin')
            for rd in recipients:
                Notification.objects.create(
                    sender=sender_user,
                    recipient=rd,
                    project_name=project,
                    message=f"New requisition submitted by {employee.emp_name} for project {project.project_first_name}.",
                    is_read=False,
                    link='',
                    pass_url='requisition_comparative_admin_confirm',
                    role='admin'
                )

            return JsonResponse({'status': 'success', 'message': 'Saved & notifications sent.'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    # GET request:
    form = RequisitionComparativeForm()
    suppliers = Suppliers.objects.all()
    heads = HeadOfRequisition.objects.all()
    projects = ProjectFirstLevelName.objects.all()
    username = request.user.username

    try:
        current_emp = Employee.objects.get(emp_name=username)
        emp_type = current_emp.emp_type.strip().lower()
    except Employee.DoesNotExist:
        current_emp = None
        emp_type = ''

    if emp_type == 'admin' or username == 'admin':
        employee_qs = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employee_qs = Employee.objects.filter(emp_name=username)

    return render(request, 'headrequisition/add_requisition_comparative.html', {
        'form': form,
        'sppliers': suppliers,
        'headRequists': heads,
        'project_lists': projects,
        'employee_list': employee_qs,
        'current_employee': current_emp,
    })



@login_required
def requis_comparative_approval(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    if request.method == "POST":
        try:
            approved_ids = request.POST.getlist("approved_rates")  
            note = request.POST.get("note", "").strip()
            with transaction.atomic():
                all_items = RequisitionComparative.objects.filter(project_name=project, approv_status='pending')

                notified_users = set()
                updated_items = []

                for item in all_items:
                    if str(item.id) in approved_ids:
                        item.approv_status = 'approved'
                    else:
                        item.approv_status = 'rejected'
                    item.approv_note = note
                    item.save()
                    updated_items.append(item)

                    if item.employee_name and hasattr(item.employee_name, 'emp_name'):
                        try:
                            user = User.objects.get(username=item.employee_name.emp_name)
                            notified_users.add(user)
                        except User.DoesNotExist:
                            pass
                for item in updated_items:
                    if item.approv_status == 'approved':
                        Requisition.objects.create(
                            project_name=item.project_name,
                            employee_name=item.employee_name,
                            vendor_name=item.vendor_name,
                            item_name=item.item_name,
                            unit=item.unit,
                            qty=item.qty,
                            rate=item.rate,
                            amount=item.amount,
                            remark=item.remark,
                            approv_status=item.approv_status,
                            approv_note=item.approv_note,
                            requisition_date=item.requisition_date,
                        )
               
                for user in notified_users:
                    Notification.objects.create(
                        sender=request.user,
                        recipient=user,
                        project_name=project,
                        message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='requisition_accounts_confirm',
                        role='accounts'
                    )

            messages.success(request, "Vendor rates updated (approved/rejected) and notifications sent successfully.")
            return redirect(reverse("requisition_comparative_list"))

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")



    all_requisitions = RequisitionComparative.objects.filter(
        project_name=project,
        approv_status='pending'
    )

    vendor_ids = list(all_requisitions.values_list('vendor_name', flat=True).distinct())
    vendor_objs = Suppliers.objects.filter(id__in=vendor_ids)
    vendor_map = {vendor.id: vendor.supplier_name for vendor in vendor_objs}

    unique_items = all_requisitions.values_list('item_name', 'unit', 'qty').distinct()
    items = []

    for item_id, unit, qty in unique_items:
        try:
            item_obj = HeadOfRequisition.objects.get(id=item_id)
            item_name_display = item_obj.head_requi_name
        except HeadOfRequisition.DoesNotExist:
            item_name_display = "Unknown"

        vendor_data_list = []
        rates = []

        # Gather all rates for this item/unit/qty across vendors
        vendor_rate_map = {}

        for vendor_id in vendor_ids:
            entry = all_requisitions.filter(
                item_name=item_id,
                unit=unit,
                qty=qty,
                vendor_name=vendor_id
            ).first()

            if entry:
                rate = entry.rate
                amount = entry.amount
                if rate is not None:
                    rates.append(rate)
                    vendor_rate_map[vendor_id] = rate

                vendor_data_list.append({
                    'id': entry.id,
                    'rate': rate,
                    'amount': amount,
                    'vendor_id': vendor_id
                })
            else:
                vendor_data_list.append({
                    'id': None,
                    'rate': None,
                    'amount': None,
                    'vendor_id': vendor_id
                })

        # Determine min and max rates
        min_rate = min(rates) if rates else None
        max_rate = max(rates) if rates else None

        # Annotate with is_lowest and is_highest flags
        for data in vendor_data_list:
            rate = data.get('rate')
            data['is_lowest'] = rate == min_rate if rate is not None else False
            data['is_highest'] = rate == max_rate if rate is not None else False

        items.append({
            'item_name': item_name_display,
            'unit': unit,
            'qty': qty,
            'vendor_data': vendor_data_list
        })

    vendor_totals = []
    for vendor_id in vendor_ids:
        total = all_requisitions.filter(vendor_name=vendor_id).aggregate(total=Sum('amount'))['total'] or 0
        vendor_totals.append(total)

    final_total = all_requisitions.aggregate(total=Sum('amount'))['total'] or 0
    column_span = 4 + len(vendor_ids) * 3

    return render(request, 'headrequisition/requis_comparative_approval.html', {
        'project': project,
        'vendor_names': [vendor_map[vid] for vid in vendor_ids],
        'items': items,
        'vendor_totals': vendor_totals,
        'final_total': final_total,
        'column_span': column_span
    })




@login_required
def requis_comparative_check(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    all_requisitions = RequisitionComparative.objects.filter(
        project_name=project,
        approv_status='pending'
    )

    vendor_ids = list(all_requisitions.values_list('vendor_name', flat=True).distinct())
    vendor_objs = Suppliers.objects.filter(id__in=vendor_ids)
    vendor_map = {vendor.id: vendor.supplier_name for vendor in vendor_objs}
    vendor_names = [vendor_map[vid] for vid in vendor_ids]

    # Group items by item_name (to align same items across vendors)
    item_vendor_map = defaultdict(dict)
    item_names = {}

    for entry in all_requisitions:
        item_id = entry.item_name.id
        item_name = HeadOfRequisition.objects.get(id=item_id).head_requi_name
        item_names[item_id] = item_name

        vendor_name = vendor_map[entry.vendor_name.id]
        item_vendor_map[item_id][vendor_name] = {
            'qty': entry.qty,
            'unit': entry.unit,
            'rate': entry.rate,
            'amount': entry.amount
        }

    # Prepare rows by item (row = dict with 'description' and ordered 'vendors' list)
    rows = []
    for item_id, item_name in item_names.items():
        # Calculate min/max rates
        rate_map = {}
        for vendor in vendor_names:
            item = item_vendor_map[item_id].get(vendor)
            if item:
                try:
                    rate = float(item['rate']) if item['rate'] is not None else None
                except (ValueError, TypeError):
                    rate = None
                rate_map[vendor] = rate

        valid_rates = [r for r in rate_map.values() if r is not None]
        min_rate = min(valid_rates) if valid_rates else None
        max_rate = max(valid_rates) if valid_rates else None

        # Create ordered list of vendor items for this row
        vendors_list = []
        for vendor in vendor_names:
            item = item_vendor_map[item_id].get(vendor, {'qty': '', 'unit': '', 'rate': None, 'amount': ''})
            rate = item.get('rate')
            is_min = (rate == min_rate) if rate is not None else False
            is_max = (rate == max_rate) if rate is not None else False

            vendors_list.append({
                'qty': item['qty'],
                'unit': item['unit'],
                'rate': item['rate'],
                'amount': item['amount'],
                'is_min': is_min,
                'is_max': is_max,
            })

        rows.append({
            'description': item_name,
            'vendors': vendors_list,
        })

    # Calculate vendor totals
    vendor_totals = {}
    for vendor_id in vendor_ids:
        total = all_requisitions.filter(vendor_name=vendor_id).aggregate(total=Sum('amount'))['total'] or 0
        vendor_totals[vendor_map[vendor_id]] = total

    vendor_totals_list = [vendor_totals.get(vendor, 0) for vendor in vendor_names]

    # Calculate colspan for table cells: 4 columns per vendor (unit, qty, rate, amount)
    colspan = len(vendor_names) * 4

    return render(request, 'headrequisition/requis_comparative_check.html', {
        'project': project,
        'vendor_names': vendor_names,
        'rows': rows,
        'vendor_totals_list': vendor_totals_list,
        'colspan': colspan,
    })





@login_required
def requisition_comparative_edit(request, pk):
    requisition = get_object_or_404(RequisitionComparative, pk=pk)

    if request.method == 'POST':
        form = RequisitionComparativeForm(request.POST, instance=requisition)
        if form.is_valid():
            form.save()

            # Manually update approv_status and approv_note
            requisition.approv_status = request.POST.get('approv_status')
            requisition.approv_note = request.POST.get('approv_note')
            requisition.save()

            messages.success(request, 'Requisition Comparative updated successfully.')
            return redirect('requisition_detail', pk=requisition.pk)
    else:
        form = RequisitionComparativeForm(instance=requisition)
        project_name = ProjectFirstLevelName.objects.all()
        employee_names = Employee.objects.all()
        requisition_list = HeadOfRequisition.objects.all()

    context = {
        'form': form,
        'project_list': project_name,
        'employee_names': employee_names,
        'requisition_list': requisition_list,
    }
    return render(request, 'headrequisition/requisition_comparative_edit.html', context)

    

@login_required
def requisition_comparative_delete(request, pk):
    requisition = get_object_or_404(RequisitionComparative, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('requisition_comparative_list')
    return render(request, 'headrequisition/requisition_comparative_delete.html', {'requisition': requisition})



@login_required
def requisition_comparative_admin_confirm(request, pk):
    project = get_object_or_404(ProjectFirstLevelName, id=pk)

    reference_requisition = RequisitionCategory.objects.filter(
        project_name=project,
        approv_status='pending'
    ).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approval_status = request.POST.get("approval_status")
        note = request.POST.get("note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approval_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        all_saved = True
        notified_users = set()

        try:
            for item_id in selected_ids:
                try:
                    item = RequisitionCategory.objects.get(id=item_id)
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.save()
                    
                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:

                        pass

                except RequisitionCategory.DoesNotExist:
                    continue

            if all_saved:
                for user in notified_users:
                    Notification.objects.create(
                        sender=request.user,
                        recipient=user,
                        project_name=project,
                        message=f"Your requisition has been updated by admin for project {project.project_first_name}.",
                        is_read=False,
                        link='',
                        pass_url='requisition_accounts_confirm',
                        role='accounts'
                    )

            messages.success(request, "Selected items updated and notifications sent successfully.")
            return redirect("requisition_comparative_list", pk=selected_ids[0])  # first selected ID

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # Group requisitions by employee
    employee_name = request.GET.get('employeeName') 
    queryset = RequisitionCategory.objects.filter(
        project_name=project,
        approv_status='pending'
    )

    if employee_name:       
        queryset = queryset.filter(employee_name__emp_name=employee_name)    
    employee_total = queryset.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'headrequisition/requisition_comparative_admin_confirm.html', {
        'project': project,
        'requisitions_by_employee': {employee_name: {'items': queryset, 'total': employee_total}},
        'final_total': queryset.aggregate(total=Sum('amount'))['total'] or 0,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })



## head of expense --
@login_required
def expense_head_list(request):
    headexpense = HeadOfExpense.objects.all()
    return render(request, 'expense/head_of_expense_list.html', {'headexpense': headexpense})


@login_required
def add_head_of_expense(request):
    if request.method == 'POST':
        form = HeadOfExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_head_list')
    else:
        form = HeadOfExpenseForm()
    context = {
        'form': form,
    }

    return render(request, 'expense/add_head_of_expense.html', context)



@login_required
def edit_head_of_expense(request, pk):
    head_requisition = get_object_or_404(HeadOfExpense, pk=pk) 
    if request.method == 'POST':
        form = HeadOfExpenseForm(request.POST, instance=head_requisition)
        if form.is_valid():
            form.save()
            return redirect('expense_head_list')  
    else:
        form = HeadOfExpenseForm(instance=head_requisition)
    
    return render(request, 'expense/edit_head_of_expense.html', {
        'form': form,
        'head_expense': head_requisition,
    })


@login_required
def delete_head_of_expense(request, pk):
    head_requisition = get_object_or_404(HeadOfExpense, pk=pk)
    if request.method == 'POST':
        head_requisition.delete()
        return redirect('expense_head_list')
    return render(request, 'expense/delete_head_of_expense.html', {
        'head_requisition': head_requisition  
    })



###  expense requisition list ----
# @login_required
# def expense_requisition_list(request):
#     projects_firt = ProjectFirstLevelName.objects.all()    
#     expenses = HeadOfExpense.objects.all()   
#     expenslisrs = ExpenseRequisition.objects.all()
#     context = {
#         'projects_firts': projects_firt,
#         'expenses': expenses,
#         'expenslisrs': expenslisrs,
#     }
#     return render(request, 'expense/expense_requisition_list.html', context)
    



@login_required
def expense_requisition_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()
    expenses = HeadOfExpense.objects.all()
    
    #expenslisrs = ExpenseRequisition.objects.filter(~Q(approv_status='approved'))
    expenslisrs = ExpenseRequisition.objects.all()
    pending_dates = expenslisrs.exclude(requisition_date__isnull=True) \
        .order_by('-requisition_date') \
        .values_list('requisition_date', flat=True).distinct()

    context = {
        'projects_firts': projects_firt,
        'expenses': expenses,
        'expenslisrs': expenslisrs,
        'pending_dates': pending_dates,
    }
    return render(request, 'expense/expense_requisition_list.html', context)

##########################new code rupok########################

# @login_required
# def grouped_requisitions_view(request):
#     all_requisitions = ExpenseRequisition.objects.all().order_by('-requisition_date', 'project_name__project_first_name')
#     pending_dates = all_requisitions.exclude(requisition_date__isnull=True) \
#         .order_by('-requisition_date') \
#         .values_list('requisition_date', flat=True).distinct()

#     grouped_data = defaultdict(lambda: defaultdict(list))

#     for req in all_requisitions:
#         date_str = req.requisition_date.strftime('%Y-%m-%d') if req.requisition_date else 'Unknown'
#         project_title = req.project_name.project_first_name
#         project_id = req.project_name.id  # Get the project_id
        
#         # Get existing data if present
#         existing_data = grouped_data[date_str].get(project_title, {'id': project_id, 'requisitions': [], 'total_amount': 0})

#         existing_data['requisitions'].append(req)
#         existing_data['total_amount'] += req.amount or 0

#         grouped_data[date_str][project_title] = existing_data
    


#     grouped_data = {
#         date: dict(projects)
#         for date, projects in sorted(grouped_data.items(), reverse=True)
#     }

#     return render(request, 'expense/grouped_requisitions.html', {
#         'grouped_data': grouped_data, 'pending_dates': pending_dates
#     }) 
    


from collections import defaultdict

@login_required
def grouped_requisitions_view(request):

    all_requisitions = ExpenseRequisition.objects.all().order_by(
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

    return render(request, 'expense/grouped_requisitions.html', {
        'grouped_data': grouped_data
    })




@login_required
def requisition_details_view(request, date_str, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    requisitions = ExpenseRequisition.objects.filter(
        requisition_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        project_name=project
    )

    return render(request, 'expense/requisition_details.html', {
        'requisitions': requisitions,
        'date_str': date_str,             
        'project_id': project.id,          
        'project': project
    })





@login_required
def update_expense_requisition(request, pk):
    expense_req = get_object_or_404(ExpenseRequisition, pk=pk)

    if request.method == "POST":
        form = ExpenseVoucherForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save form without committing
                    item = form.save(commit=False)

                    # Auto-generate mr_or_bill_no if missing
                    if not item.mr_or_bill_no:
                        base_code = "MEX-"
                        last = ExpenseVoucher.objects.filter(
                            mr_or_bill_no__startswith=base_code
                        ).order_by('-id').first()
                        next_id = (last.id + 1) if last else 1
                        generated_code = f"{base_code}{next_id:05d}"
                        while ExpenseVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                            next_id += 1
                            generated_code = f"{base_code}{next_id:05d}"
                        item.mr_or_bill_no = generated_code
                    else:
                        generated_code = item.mr_or_bill_no

                    # Link data from ExpenseRequisition if not in form
                    if not item.project_name:
                        item.project_name = expense_req.project_name
                    if not item.expense_name:
                        item.expense_name = expense_req.item_name
                    if not item.amount:
                        item.amount = expense_req.amount
                    if not item.particulars:
                        item.particulars = expense_req.descript

                    # Set approval defaults
                    item.approv_status = 'approved'
                    item.approval_cr_status = True

                    # Save ExpenseVoucher
                    item.save()

                    # Create linked DebitVoucher
                    debit_voucher = DebitVoucher.objects.create(
                        type='Expense',
                        expense=item.expense_name,
                        bill_date=item.date,
                        project_name=item.project_name,
                        amount=item.amount,
                        particulars=item.particulars,
                        date=item.date,
                        mr_or_bill_no=item.mr_or_bill_no,
                        head_of_account=item.head_of_account,
                        cash_type=item.cash_type,
                        cheque_number=item.cheque_number,
                        requi_id=expense_req.id,
                        return_requisition='No',
                        approval_dr_status=True,
                        carrier=''
                    )

                    # Update CashType
                    try:
                        cash_type_obj = item.cash_type
                        if cash_type_obj:
                            cash_type_obj.type_amount -= item.amount
                            cash_type_obj.type_note = f"Payment for Expense Voucher ID {item.id}"
                            cash_type_obj.save()
                    except CashType.DoesNotExist:
                        cash_type_obj = None

                    # ✅ Update MainCheque if cheque_number provided
                    cheque_id = request.POST.get('cheque_number')
                    if cheque_id and debit_voucher.cash_type:
                        try:
                            cheque = MainCheque.objects.get(id=cheque_id)
                            cheque.status = 'used'
                            cheque.remarks = debit_voucher.particulars or ''
                            cheque.issue_date = debit_voucher.date
                            cheque.payee_name = debit_voucher.cash_type.cash_type_name
                            cheque.amount = debit_voucher.amount
                            cheque.save()
                        except MainCheque.DoesNotExist:
                            print("⚠️ Cheque not found, skipping update.")

                    # --- Create TransactionHistory ---
                    TransactionHistory.objects.create(
                        project=item.project_name,
                        transaction_type=item.type,
                        head_of_account=item.head_of_account,
                        cash_type=cash_type_obj,
                        amount=item.amount,
                        cheque_number=item.cheque_number,
                        date=item.date,
                        type_name=f"{item.type}_Payment",
                        reference=item.mr_or_bill_no,
                    )

                    # --- Create LedgerEntry ---
                    LedgerEntry.objects.create(
                        project_name=item.project_name,
                        type='Expense',
                        exp_name=item.expense_name,
                        type_name=item.expense_name,
                        cash_type=item.cash_type,
                        cheque_number=item.cheque_number,
                        head=item.head_of_account,
                        mr_or_bill_no=item.mr_or_bill_no,
                        date=item.date,
                        description=item.particulars or '',
                        debit=item.amount,
                        credit=0,
                        carrier=item.carrier,
                        loan_status='payment'
                    )

                    expense_req.ledger_add = True
                    expense_req.save(update_fields=['ledger_add'])

                    return redirect(reverse("grouped_requisitions"))

            except Exception as e:
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'An error occurred: {str(e)}'
                })

        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Form is invalid.',
                'errors': form.errors
            })

    else:
        # Pre-fill form with requisition data
        initial_data = {
            'project_name': expense_req.project_name,
            'expense_name': expense_req.item_name,
            'amount': expense_req.amount,
            'particulars': expense_req.descript,
            'date': expense_req.requisition_date or now().date()
        }
        form = ExpenseVoucherForm(initial=initial_data)

    head_of_account = get_object_or_404(HeadOfAccount, head_name='Expense Account')
    return render(
        request,
        "expense/expense_requisition_update.html",
        {
            "form": form,
            "today": now().date(),
            "expense_req": expense_req,
            'head_of_accounts': [head_of_account],
        }
    )





##########################new code rupok########################
# @login_required
# def approve_selected_requisitions(request):
#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_reqs")
#         if selected_ids:
#             ExpenseRequisition.objects.filter(id__in=selected_ids).update(approv_status="approved")
#             messages.success(request, "Selected requisitions approved.")
#         else:
#             messages.warning(request, "No items selected.")
#     return redirect(request.META.get("HTTP_REFERER", "/"))




# @login_required
# def approve_selected_requisitions(request):
#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_reqs")

#         if not selected_ids:
#             messages.warning(request, "No items selected.")
#             return redirect(request.META.get("HTTP_REFERER", "/"))

#         try:
#             with transaction.atomic():
#                 selected_reqs = ExpenseRequisition.objects.filter(id__in=selected_ids)

#                 for expense_req in selected_reqs:
#                     # Skip already processed
#                     if getattr(expense_req, "ledger_add", False):
#                         continue

#                     # --- Mark requisition approved ---
#                     expense_req.approv_status = "approved"
#                     expense_req.save(update_fields=["approv_status"])

#                     # --- Auto-generate mr_or_bill_no ---
#                     base_code = "MEX-"
#                     last = DebitVoucher.objects.filter(
#                         mr_or_bill_no__startswith=base_code
#                     ).order_by("-id").first()
#                     next_id = (last.id + 1) if last else 1
#                     generated_code = f"{base_code}{next_id:05d}"
#                     while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                         next_id += 1
#                         generated_code = f"{base_code}{next_id:05d}"

#                     # --- Create DebitVoucher ---
#                     debit_voucher = DebitVoucher.objects.create(
#                         type="Expense",
#                         expense=str(expense_req.item_name),
#                         bill_date=expense_req.requisition_date,
#                         project_name=expense_req.project_name,
#                         amount=expense_req.amount,
#                         particulars=expense_req.descript or "",
#                         date=expense_req.requisition_date,
#                         mr_or_bill_no=generated_code,
#                         head_of_account=expense_req.head_of_account,
#                         cash_type=expense_req.cash_type,
#                         cheque_number=expense_req.cheque_number or "",
#                         requi_id=expense_req.id,
#                         return_requisition="No",
#                         approval_dr_status=True,
#                         carrier="",
#                         create_dr=request.user.username,
#                         is_confirmed=True,
#                     )

#                     # --- Update CashType ---
#                     cash_type_obj = expense_req.cash_type
#                     if cash_type_obj:
#                         cash_type_obj.type_amount -= expense_req.amount
#                         cash_type_obj.type_note = f"Expense Requisition ID {expense_req.id} Approved"
#                         cash_type_obj.save()

#                     # --- Update Cheque (if exists) ---
#                     cheque_id = expense_req.cheque_number
#                     if cheque_id and cash_type_obj:
#                         try:
#                             cheque = MainCheque.objects.get(id=cheque_id)
#                             cheque.status = "used"
#                             cheque.remarks = expense_req.descript or ""
#                             cheque.issue_date = expense_req.requisition_date
#                             cheque.payee_name = cash_type_obj.cash_type_name
#                             cheque.amount = expense_req.amount
#                             cheque.save()
#                         except MainCheque.DoesNotExist:
#                             print("⚠️ Cheque not found, skipping update.")

#                     # --- Create TransactionHistory ---
#                     TransactionHistory.objects.create(
#                         project=expense_req.project_name,
#                         transaction_type="Expense",
#                         head_of_account=expense_req.head_of_account,
#                         cash_type=cash_type_obj,
#                         cheque_number=expense_req.cheque_number,
#                         amount=expense_req.amount,
#                         date=expense_req.requisition_date,
#                         type_name="Expense_Payment",
#                         reference=generated_code,
#                         create_by=request.user.username,
#                         particulars=expense_req.descript or "",
#                     )

#                     # --- Create LedgerEntry ---
#                     LedgerEntry.objects.create(
#                         project_name=expense_req.project_name,
#                         type="Expense",
#                         exp_name=expense_req.item_name,
#                         type_name=str(expense_req.item_name),
#                         cash_type=cash_type_obj,
#                         cheque_number=expense_req.cheque_number,
#                         head=expense_req.head_of_account,
#                         mr_or_bill_no=generated_code,
#                         date=expense_req.requisition_date,
#                         description=expense_req.descript or "",
#                         debit=expense_req.amount,
#                         credit=0,
#                         carrier="",
#                         loan_status="payment",
#                         tbl_id=str(debit_voucher.id),
#                         tbl_name="DebitVoucher",
#                     )

#                     # --- Mark as added to ledger ---
#                     expense_req.ledger_add = True
#                     expense_req.save(update_fields=["ledger_add"])

#                 messages.success(request, "Selected requisitions approved and processed successfully.")

#         except Exception as e:
#             traceback.print_exc()
#             messages.error(request, f"Error occurred during approval: {str(e)}")
#             return JsonResponse({
#                 "status": "error",
#                 "message": f"Error occurred: {str(e)}"
#             })

#     return redirect(request.META.get("HTTP_REFERER", "/"))





# from django.db import transaction
# from django.http import JsonResponse
# import traceback

# @login_required
# def approve_selected_requisitions(request):
#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_reqs")

#         if not selected_ids:
#             messages.warning(request, "No items selected.")
#             return redirect(request.META.get("HTTP_REFERER", "/"))

#         try:
#             with transaction.atomic():
#                 selected_reqs = ExpenseRequisition.objects.filter(id__in=selected_ids)

#                 for expense_req in selected_reqs:
#                     if getattr(expense_req, "ledger_add", False):
#                         continue

#                     # --- Approve requisition ---
#                     expense_req.approv_status = "approved"
#                     expense_req.save(update_fields=["approv_status"])

#                     # --- Auto-generate mr_or_bill_no ---
#                     base_code = "MEX-"
#                     last = DebitVoucher.objects.filter(
#                         mr_or_bill_no__startswith=base_code
#                     ).order_by("-id").first()
#                     next_id = (last.id + 1) if last else 1
#                     generated_code = f"{base_code}{next_id:05d}"
#                     while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                         next_id += 1
#                         generated_code = f"{base_code}{next_id:05d}"

#                     # --- Create DebitVoucher ---
#                     debit_voucher = DebitVoucher.objects.create(
#                         type="Expense",
#                         expense=str(expense_req.item_name),
#                         bill_date=expense_req.requisition_date,
#                         project_name=expense_req.project_name,
#                         amount=expense_req.amount,
#                         particulars=expense_req.descript or "",
#                         date=expense_req.requisition_date,
#                         mr_or_bill_no=generated_code,
#                         head_of_account=expense_req.head_of_account,
#                         cash_type=expense_req.cash_type,
#                         cheque_number=expense_req.cheque_number or "",
#                         requi_id=expense_req.id,
#                         return_requisition="No",
#                         approval_dr_status=True,
#                         carrier="",
#                         create_dr=request.user.username,
#                         is_confirmed=True,
#                     )

#                     # --- Update CashType ---
#                     cash_type_obj = expense_req.cash_type
#                     if cash_type_obj:
#                         cash_type_obj.type_amount -= expense_req.amount
#                         cash_type_obj.type_note = f"Expense Requisition ID {expense_req.id} Approved"
#                         cash_type_obj.save()

#                     # --- Update Cheque (if exists) ---
#                     cheque_id = expense_req.cheque_number
#                     if cheque_id and cash_type_obj:
#                         try:
#                             cheque = MainCheque.objects.get(id=cheque_id)
#                             cheque.status = "used"
#                             cheque.remarks = expense_req.descript or ""
#                             cheque.issue_date = expense_req.requisition_date
#                             cheque.payee_name = cash_type_obj.cash_type_name
#                             cheque.amount = expense_req.amount
#                             cheque.save()
#                         except MainCheque.DoesNotExist:
#                             # Safe log message (avoid printing Unicode directly)
#                             print("Cheque not found, skipping update.".encode("utf-8", "ignore").decode("utf-8"))

#                     # --- Create TransactionHistory ---
#                     TransactionHistory.objects.create(
#                         project=expense_req.project_name,
#                         transaction_type="Expense",
#                         head_of_account=expense_req.head_of_account,
#                         cash_type=cash_type_obj,
#                         cheque_number=expense_req.cheque_number,
#                         amount=expense_req.amount,
#                         date=expense_req.requisition_date,
#                         type_name="Expense_Payment",
#                         reference=generated_code,
#                         create_by=request.user.username,
#                         particulars=expense_req.descript or "",
#                         tbl_id=expense_req.id,
#                         tbl_name="Payment",
#                     )

#                     # --- Create LedgerEntry ---
#                     LedgerEntry.objects.create(
#                         project_name=expense_req.project_name,
#                         type="Expense",
#                         exp_name=expense_req.item_name,
#                         type_name=str(expense_req.item_name),
#                         cash_type=cash_type_obj,
#                         cheque_number=expense_req.cheque_number,
#                         head=expense_req.head_of_account,
#                         mr_or_bill_no=generated_code,
#                         date=expense_req.requisition_date,
#                         description=expense_req.descript or "",
#                         debit=expense_req.amount,
#                         credit=0,
#                         carrier="",
#                         loan_status="payment",
#                         tbl_id=str(debit_voucher.id),
#                         tbl_name="Payment",
#                     )

#                     expense_req.ledger_add = True
#                     expense_req.save(update_fields=["ledger_add"])

#                 messages.success(request, "Selected requisitions approved and processed successfully.")

#         except Exception as e:
#             error_msg = str(e).encode("utf-8", "ignore").decode("utf-8")
#             traceback.print_exc()
#             messages.error(request, f"Error occurred during approval: {error_msg}")
#             return JsonResponse({
#                 "status": "error",
#                 "message": f"Error occurred: {error_msg}"
#             })

#     return redirect(request.META.get("HTTP_REFERER", "/"))






@login_required
def approve_selected_requisitions(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_reqs")

        if not selected_ids:
            messages.warning(request, "No items selected.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        try:
            with transaction.atomic():
                selected_reqs = ExpenseRequisition.objects.filter(id__in=selected_ids)

                for expense_req in selected_reqs:
                    if expense_req.approv_status == "approved":
                        continue  # skip already approved

                    # --- Approve requisition ---
                    expense_req.approv_status = "approved"
                    expense_req.save(update_fields=["approv_status"])

                    # --- Generate unique MR/Bill No ---
                    base_code = "MEX-"
                    last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by("-id").first()
                    next_id = (last.id + 1) if last else 1
                    generated_code = f"{base_code}{next_id:05d}"
                    while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                        next_id += 1
                        generated_code = f"{base_code}{next_id:05d}"

                    # --- Create DebitVoucher ---
                    debit_voucher = DebitVoucher.objects.create(
                        type="Expense",
                        expense=str(expense_req.item_name),
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

                    # --- Update CashType ---
                    if expense_req.cash_type:
                        expense_req.cash_type.type_amount -= expense_req.amount
                        expense_req.cash_type.type_note = f"Expense Requisition ID {expense_req.id} Approved"
                        expense_req.cash_type.save()

                    # --- Update Cheque if exists ---
                    if expense_req.cheque_number:
                        try:
                            cheque = MainCheque.objects.get(id=expense_req.cheque_number)
                            cheque.status = "used"
                            cheque.remarks = expense_req.descript or ""
                            cheque.issue_date = expense_req.requisition_date
                            cheque.payee_name = expense_req.cash_type.cash_type_name if expense_req.cash_type else ""
                            cheque.amount = expense_req.amount
                            cheque.save()
                        except MainCheque.DoesNotExist:
                            print(f"Cheque {expense_req.cheque_number} not found, skipping update.")

                    # --- Create TransactionHistory ---
                    TransactionHistory.objects.create(
                        project=expense_req.project_name,
                        transaction_type="Expense",
                        head_of_account=expense_req.head_of_account,
                        cash_type=expense_req.cash_type,
                        cheque_number=expense_req.cheque_number,
                        amount=expense_req.amount,
                        date=expense_req.requisition_date,
                        type_name="Expense_Payment",
                        reference=generated_code,
                        create_by=request.user.username,
                        particulars=expense_req.descript or "",
                        tbl_id=expense_req.id,
                        tbl_name="Payment",
                    )

                    # --- Create LedgerEntry ---
                    LedgerEntry.objects.create(
                        project_name=expense_req.project_name,
                        type="Expense",
                        exp_name=expense_req.item_name,
                        type_name=str(expense_req.item_name),
                        cash_type=expense_req.cash_type,
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

                    # --- Mark ledger added ---
                    expense_req.ledger_add = True
                    expense_req.save(update_fields=["ledger_add"])

                messages.success(request, "Selected requisitions approved and processed successfully.")

        except Exception as e:
            error_msg = str(e)
            traceback.print_exc()
            messages.error(request, f"Error occurred during approval: {error_msg}")

    return redirect(request.META.get("HTTP_REFERER", "/"))





@login_required
def print_exp_requisition_data(request, date_str, project_id):
    requisitions = ExpenseRequisition.objects.filter(
        requisition_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        project_name_id=project_id  
    )

    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expense/print_exp_requisition_data.html', {
        'requisitions': requisitions,
        'date_str': date_str,
        'project_id': project_id,
        'total_amount': total_amount,
    })
   
    


@login_required
def edit_expense_requisition(request, pk):
    expense = get_object_or_404(ExpenseRequisition, pk=pk)

    if request.method == 'POST':
        form = ExpenseRequisitionForm(request.POST, instance=expense)
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
            return redirect('requisition_details', date_str=date_str, project_id=project_id)
        else:
            return render(request, 'expense/expense_requisition_edit.html', {
                'form': form,
                'expense': expense,
                'errors': form.errors,
            })
    else:
        form = ExpenseRequisitionForm(instance=expense)

    return render(request, 'expense/expense_requisition_edit.html', {
        'form': form,
        'expense': expense,
    })
    
    
    

@login_required
def delete_expense_requisition(request, pk):
    voucher = get_object_or_404(ExpenseRequisition, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        return redirect('grouped_requisitions')
    return render(request, 'expense/delete_expense_requisition.html', {'voucher': voucher})
    
    

    
    
# @login_required
# def expense_requisition_add(request):
#     if request.method == "POST" and request.content_type == "application/json":
#         try:
#             data = json.loads(request.body)
#             items = data.get('data', [])
#             employee_id = data.get('employee_id')
#             type_value = data.get('type')
#             remark = data.get('remark', '')
#             head_of_account_id = data.get('head_of_account')
#             cash_type_id = data.get('cash_type')
#             cheque_number = data.get('cheque_number','')

#             employee = Employee.objects.get(id=employee_id)

#             # Validate and create each item
#             for item in items:
#                 project_id = item.get('project')
#                 item_id = item.get('item')
#                 qty = item.get('qty')
#                 rate = item.get('rate')
#                 descript = item.get('description', '')

#                 # Basic validation
#                 if not all([project_id, item_id, qty, rate]):
#                     return JsonResponse({'status': 'error', 'message': 'Missing required fields in one or more items.'})

#                 project = ProjectFirstLevelName.objects.get(id=project_id)
#                 head_name = HeadOfAccount.objects.get(id=head_of_account_id)
#                 cashtype_name = CashType.objects.get(id=cash_type_id)
#                 head_item = HeadOfExpense.objects.get(id=item_id)
#                 amount = float(qty) * float(rate)

#                 ExpenseRequisition.objects.create(
#                     project_name=project,
#                     cash_type=cashtype_name,
#                     cheque_number=cheque_number,
#                     head_of_account=head_name,
#                     employee_name=employee,
#                     item_name=head_item,
#                     qty=qty,
#                     rate=rate,
#                     amount=amount,
#                     descript=descript,
#                     remark=remark,
#                     approv_status='pending',  # default
#                     approv_note='',
#                     requisition_date=timezone.now().date() 
#                 )
#             return JsonResponse({'status': 'success', 'message': 'Expense requisitions saved successfully.'})

#         except Employee.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Employee not found.'})
#         except ProjectFirstLevelName.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Project not found.'})
#         except HeadOfRequisition.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Item not found.'})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'})

#     else:
#         # GET request - render form page
#         employee = Employee.objects.get(user=request.user)
#         headExpenses = HeadOfExpense.objects.all()
#         cashTypes = CashType.objects.all()
#         project_lists = ProjectFirstLevelName.objects.all()
#         headOfAccounts = HeadOfAccount.objects.all()

#         return render(request, 'expense/expense_requisition_add.html', {
#             'employee_id': employee.id,
#             'employee_name': employee.employee_name,
#             'headExpenses': headExpenses,
#             'project_lists': project_lists,
#             'type': 'Expense',  
#             'cashTypes' : cashTypes,
#             'headOfAccounts': headOfAccounts,
#         })





@login_required
def expense_requisition_add(request):
    # JSON-based POST (AJAX submission)
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

            employee = Employee.objects.get(id=employee_id)

            # Validate and create each item
            for item in items:
                project_id = item.get('project')
                item_id = item.get('item')
                qty = item.get('qty')
                rate = item.get('rate')
                descript = item.get('description', '')

                if not all([project_id, item_id, qty, rate]):
                    return JsonResponse({'status': 'error', 'message': 'Missing required fields in one or more items.'})

                project = ProjectFirstLevelName.objects.get(id=project_id)
                head_name = HeadOfAccount.objects.get(id=head_of_account_id)
                cashtype_name = CashType.objects.get(id=cash_type_id)
                head_item = HeadOfExpense.objects.get(id=item_id)
                amount = float(qty) * float(rate)

                # Create the expense requisition entry
                requisition = ExpenseRequisition.objects.create(
                    type=type_value,
                    project_name=project,
                    cash_type=cashtype_name,
                    head_of_account=head_name,
                    employee_name=employee,
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
                        cheque = MainCheque.objects.get(id=cheque_id)
                        requisition.cheque_number = cheque.cheque_number
                        requisition.save()

                        # Update cheque details
                        cheque.status = 'used'
                        cheque.remarks = f"Used in Expense Requisition ID {requisition.id}"
                        cheque.issue_date = timezone.now().date()
                        cheque.amount = amount
                        cheque.save()
                    except MainCheque.DoesNotExist:
                        return JsonResponse({'status': 'error', 'message': 'Cheque not found.'})

            return JsonResponse({'status': 'success', 'message': 'Expense requisitions saved successfully.'})

        except Employee.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Employee not found.'})
        except ProjectFirstLevelName.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Project not found.'})
        except HeadOfExpense.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'})

    # Standard Django form submission (non-AJAX)
    else:
        form = ExpenseRequisitionForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            requisition = form.save(commit=False)
            cheque_id = request.POST.get('cheque_number')

            if cheque_id:
                try:
                    cheque = MainCheque.objects.get(id=cheque_id)
                    requisition.cheque_number = cheque.cheque_number
                    requisition.save()

                    # Update cheque info
                    cheque.status = 'used'
                    cheque.remarks = requisition.remark or ''
                    cheque.issue_date = requisition.requisition_date
                    cheque.amount = requisition.amount
                    cheque.save()

                except MainCheque.DoesNotExist:
                    print("Cheque not found")
            else:
                requisition.save()

            return redirect('grouped_requisitions')

        # GET request — render form
        employee = Employee.objects.get(user=request.user)
        headExpenses = HeadOfExpense.objects.all()
        cashTypes = CashType.objects.all()
        project_lists = ProjectFirstLevelName.objects.all()
        headOfAccounts = HeadOfAccount.objects.all()

        return render(request, 'expense/expense_requisition_add.html', {
            'form': form,
            'employee_id': employee.id,
            'employee_name': employee.employee_name,
            'headExpenses': headExpenses,
            'project_lists': project_lists,
            'type': 'Expense',
            'cashTypes': cashTypes,
            'headOfAccounts': headOfAccounts,
        })



# @login_required
# def expense_requisition_confirmation(request):
#     requisition_date = request.GET.get('requisition_date')
#     vouchers = ExpenseRequisition.objects.none()
#     selected_project = None

#     if requisition_date:
#         parsed_date = parse_date(requisition_date)
#         if parsed_date:
#             vouchers = ExpenseRequisition.objects.filter(
#                 requisition_date=parsed_date
#             ).select_related('item_name', 'employee_name', 'project_name').order_by('id')

#             if vouchers.exists():
#                 selected_project = vouchers[0].project_name

#     total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or 0

#     # ✅ Auto confirm and insert related data when confirmation requirement triggered
#     try:
#         with transaction.atomic():
#             for expense_req in vouchers:
#                 # Skip if already added to ledger
#                 if getattr(expense_req, "ledger_add", False):
#                     continue

#                 # --- Auto-generate mr_or_bill_no ---
#                 base_code = "MEX-"
#                 last = DebitVoucher.objects.filter(
#                     mr_or_bill_no__startswith=base_code
#                 ).order_by('-id').first()
#                 next_id = (last.id + 1) if last else 1
#                 generated_code = f"{base_code}{next_id:05d}"
#                 while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 # --- Create DebitVoucher ---
#                 debit_voucher = DebitVoucher.objects.create(
#                     type='Expense',
#                     expense=str(expense_req.item_name),
#                     bill_date=expense_req.requisition_date,
#                     project_name=expense_req.project_name,
#                     amount=expense_req.amount,
#                     particulars=expense_req.descript or '',
#                     date=expense_req.requisition_date,
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

#                 # --- Update CashType ---
#                 cash_type_obj = expense_req.cash_type
#                 if cash_type_obj:
#                     cash_type_obj.type_amount -= expense_req.amount
#                     cash_type_obj.type_note = f"Expense Requisition ID {expense_req.id} Confirmed"
#                     cash_type_obj.save()

#                 # --- Update Cheque (if exists) ---
#                 cheque_id = expense_req.cheque_number
#                 if cheque_id and cash_type_obj:
#                     try:
#                         cheque = MainCheque.objects.get(id=cheque_id)
#                         cheque.status = 'used'
#                         cheque.remarks = expense_req.descript or ''
#                         cheque.issue_date = expense_req.requisition_date
#                         cheque.payee_name = cash_type_obj.cash_type_name
#                         cheque.amount = expense_req.amount
#                         cheque.save()
#                     except MainCheque.DoesNotExist:
#                         print("⚠️ Cheque not found, skipping update.")

#                 # --- Create TransactionHistory ---
#                 TransactionHistory.objects.create(
#                     project=expense_req.project_name,
#                     transaction_type='Expense',
#                     head_of_account=expense_req.head_of_account,
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     amount=expense_req.amount,
#                     date=expense_req.requisition_date,
#                     type_name='Expense_Payment',
#                     reference=generated_code,
#                     create_by=request.user.username,
#                     particulars=expense_req.descript or ''
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # --- Create LedgerEntry (include debit_voucher.id in tbl_id) ---
#                 LedgerEntry.objects.create(
#                     project_name=expense_req.project_name,
#                     type='Expense',
#                     exp_name=expense_req.item_name,
#                     type_name=str(expense_req.item_name),
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     head=expense_req.head_of_account,
#                     mr_or_bill_no=generated_code,
#                     date=expense_req.requisition_date,
#                     description=expense_req.descript or '',
#                     debit=expense_req.amount,
#                     credit=0,
#                     carrier='',
#                     loan_status='payment',
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # --- Mark requisition as added to ledger ---
#                 expense_req.ledger_add = True
#                 expense_req.save(update_fields=['ledger_add'])

#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse({
#             'status': 'error',
#             'message': f'Error occurred: {str(e)}'
#         })

#     context = {
#         'selected_project': selected_project,
#         'vouchers': vouchers,
#         'print_time': now(),
#         'requisition_date': requisition_date,
#         'total_amount': total_amount,
#     }
#     return render(request, 'expense/expense_requisition_confirmation.html', context)
    
    
    
# from django.db import transaction
# from django.db.models import Sum
# from django.http import JsonResponse
# from django.utils.timezone import now
# from django.utils.dateparse import parse_date
# import traceback

# @login_required
# def expense_requisition_confirmation(request):
#     requisition_date = request.GET.get('requisition_date')
#     vouchers = ExpenseRequisition.objects.none()
#     selected_project = None

#     if requisition_date:
#         parsed_date = parse_date(requisition_date)
#         if parsed_date:
#             vouchers = (
#                 ExpenseRequisition.objects
#                 .filter(requisition_date=parsed_date)
#                 .select_related('item_name', 'employee_name', 'project_name')
#                 .order_by('id')
#             )
#             if vouchers.exists():
#                 selected_project = vouchers[0].project_name

#     total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or 0

#     try:
#         with transaction.atomic():
#             for expense_req in vouchers:

#                 # Skip already confirmed
#                 if getattr(expense_req, "ledger_add", False):
#                     continue

#                 # -------- Generate MR / Bill No --------
#                 base_code = "MEX-"
#                 last = DebitVoucher.objects.filter(
#                     mr_or_bill_no__startswith=base_code
#                 ).order_by('-id').first()

#                 next_id = (last.id + 1) if last else 1
#                 generated_code = f"{base_code}{next_id:05d}"

#                 while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 # -------- Create Debit Voucher --------
#                 debit_voucher = DebitVoucher.objects.create(
#                     type='Expense',
#                     expense=str(expense_req.item_name),
#                     bill_date=expense_req.requisition_date,
#                     project_name=expense_req.project_name,
#                     amount=expense_req.amount,
#                     particulars=expense_req.descript or '',
#                     date=expense_req.requisition_date,
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

#                 # -------- Update Cash Type --------
#                 cash_type_obj = expense_req.cash_type
#                 if cash_type_obj:
#                     cash_type_obj.type_amount -= expense_req.amount
#                     cash_type_obj.type_note = f"Expense Requisition ID {expense_req.id} Confirmed"
#                     cash_type_obj.save()

#                 # -------- Update Cheque --------
#                 cheque_id = expense_req.cheque_number
#                 if cheque_id and cash_type_obj:
#                     try:
#                         cheque = MainCheque.objects.get(id=cheque_id)
#                         cheque.status = 'used'
#                         cheque.remarks = expense_req.descript or ''
#                         cheque.issue_date = expense_req.requisition_date
#                         cheque.payee_name = str(cash_type_obj.cash_type_name)
#                         cheque.amount = expense_req.amount
#                         cheque.save()
#                     except MainCheque.DoesNotExist:
#                         pass  # silently ignore

#                 # -------- Transaction History --------
#                 TransactionHistory.objects.create(
#                     project=expense_req.project_name,
#                     transaction_type='Expense',
#                     head_of_account=expense_req.head_of_account,
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     amount=expense_req.amount,
#                     date=expense_req.requisition_date,
#                     type_name='Expense_Payment',
#                     reference=generated_code,
#                     create_by=request.user.username,
#                     particulars=expense_req.descript or '',
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # -------- Ledger Entry --------
#                 LedgerEntry.objects.create(
#                     project_name=expense_req.project_name,
#                     type='Expense',
#                     exp_name=expense_req.item_name,          # ✅ FIXED
#                     type_name=str(expense_req.item_name),    # string is OK here
#                     cash_type=cash_type_obj,
#                     cheque_number=expense_req.cheque_number,
#                     head=expense_req.head_of_account,
#                     mr_or_bill_no=generated_code,
#                     date=expense_req.requisition_date,
#                     description=expense_req.descript or '',
#                     debit=expense_req.amount,
#                     credit=0,
#                     carrier='',
#                     loan_status='payment',
#                     tbl_id=str(debit_voucher.id),
#                     tbl_name='Payment'
#                 )

#                 # -------- Mark as processed --------
#                 expense_req.ledger_add = True
#                 expense_req.save(update_fields=['ledger_add'])

#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse(
#             {
#                 'status': 'error',
#                 'message': f'Error occurred: {str(e)}'
#             },
#             json_dumps_params={'ensure_ascii': False}
#         )

#     context = {
#         'selected_project': selected_project,
#         'vouchers': vouchers,
#         'print_time': now(),
#         'requisition_date': requisition_date,
#         'total_amount': total_amount,
#     }

#     return render(request, 'expense/expense_requisition_confirmation.html', context)




from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.utils.timezone import now
from django.utils.dateparse import parse_date
import traceback


@login_required
def expense_requisition_confirmation(request):
    requisition_date = request.GET.get('requisition_date')
    vouchers = ExpenseRequisition.objects.none()
    selected_project = None

    # -------- Filter vouchers by requisition date --------
    if requisition_date:
        parsed_date = parse_date(requisition_date)
        if parsed_date:
            vouchers = (
                ExpenseRequisition.objects
                .filter(requisition_date=parsed_date)
                .select_related('item_name', 'employee_name', 'project_name')
                .order_by('id')
            )

            if vouchers.exists():
                selected_project = vouchers[0].project_name

    total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or 0

    try:
        with transaction.atomic():

            # Approval date = current date
            approval_date = now().date()

            for expense_req in vouchers:

                # Skip already processed
                if expense_req.ledger_add:
                    continue

                # -------- Generate MR/Bill No --------
                base_code = "MEX-"

                last = DebitVoucher.objects.filter(
                    mr_or_bill_no__startswith=base_code
                ).order_by('-id').first()

                next_id = (last.id + 1) if last else 1
                generated_code = f"{base_code}{next_id:05d}"

                while DebitVoucher.objects.filter(
                    mr_or_bill_no=generated_code
                ).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"

                # -------- Create Debit Voucher --------
                debit_voucher = DebitVoucher.objects.create(
                    type='Expense',
                    expense=str(expense_req.item_name),
                    bill_date=approval_date,
                    project_name=expense_req.project_name,
                    amount=expense_req.amount,
                    particulars=expense_req.descript or '',
                    date=approval_date,
                    mr_or_bill_no=generated_code,
                    head_of_account=expense_req.head_of_account,
                    cash_type=expense_req.cash_type,
                    cheque_number=expense_req.cheque_number or '',
                    requi_id=expense_req.id,
                    return_requisition='No',
                    approval_dr_status=True,
                    carrier='',
                    create_dr=request.user.username,
                    is_confirmed=True,
                )

                # -------- Update Cash Balance --------
                cash_type_obj = expense_req.cash_type
                if cash_type_obj:
                    cash_type_obj.type_amount -= expense_req.amount
                    cash_type_obj.type_note = (
                        f"Expense Requisition ID {expense_req.id} Confirmed"
                    )
                    cash_type_obj.save()

                # -------- Update Cheque Safely --------
                cheque_id = expense_req.cheque_number

                if cheque_id and str(cheque_id).isdigit() and cash_type_obj:
                    try:
                        cheque = MainCheque.objects.get(id=int(cheque_id))
                        cheque.status = 'used'
                        cheque.remarks = expense_req.descript or ''
                        cheque.issue_date = approval_date
                        cheque.payee_name = str(
                            cash_type_obj.cash_type_name
                        )
                        cheque.amount = expense_req.amount
                        cheque.save()
                    except MainCheque.DoesNotExist:
                        pass

                # -------- Transaction History --------
                TransactionHistory.objects.create(
                    project=expense_req.project_name,
                    transaction_type='Expense',
                    head_of_account=expense_req.head_of_account,
                    cash_type=cash_type_obj,
                    cheque_number=expense_req.cheque_number,
                    amount=expense_req.amount,
                    date=approval_date,
                    type_name='Expense_Payment',
                    reference=generated_code,
                    create_by=request.user.username,
                    particulars=expense_req.descript or '',
                    tbl_id=str(debit_voucher.id),
                    tbl_name='Payment'
                )

                # -------- Ledger Entry --------
                LedgerEntry.objects.create(
                    project_name=expense_req.project_name,
                    type='Expense',
                    exp_name=expense_req.item_name,
                    type_name=str(expense_req.item_name),
                    cash_type=cash_type_obj,
                    cheque_number=expense_req.cheque_number,
                    head=expense_req.head_of_account,
                    mr_or_bill_no=generated_code,
                    date=approval_date,
                    description=expense_req.descript or '',
                    debit=expense_req.amount,
                    credit=0,
                    carrier='',
                    loan_status='payment',
                    tbl_id=str(debit_voucher.id),
                    tbl_name='Payment'
                )

                # -------- Mark requisition approved --------
                expense_req.ledger_add = True
                expense_req.approv_status = 'approved'
                expense_req.approval_date = approval_date

                expense_req.save(update_fields=[
                    'ledger_add',
                    'approv_status',
                    'approval_date'
                ])

    except Exception as e:
        traceback.print_exc()
        return JsonResponse(
            {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            },
            json_dumps_params={'ensure_ascii': False}
        )

    context = {
        'selected_project': selected_project,
        'vouchers': vouchers,
        'print_time': now(),
        'requisition_date': requisition_date,
        'total_amount': total_amount,
    }

    return render(
        request,
        'expense/expense_requisition_confirmation.html',
        context
    )




@login_required
def approve_expense_voucher(request, pk):
    requisition_date = request.GET.get('requisition_date')

    # First, get the current approved requisition (single record)
    requisition = get_object_or_404(ExpenseRequisition, pk=pk)
    
    requi_expenseid = int(time.time())
    # Approve the current requisition
    requisition.approv_status = 'approved'
    requisition.approv_note = 'Approved by admin'
    requisition.requi_expense_id = requi_expenseid  # Save own pk here
    requisition.save()

    # Now update all rows with the same requisition_date and not approved yet
    if requisition_date:
        ExpenseRequisition.objects.filter(
            requisition_date=requisition_date,
            approv_status__in=['pending', 'rejected']
        ).update(
            approv_status='approved',
            requi_expense_id=requi_expenseid,
            approv_note='Approved by admin'
        )

    # Redirect back to confirmation page with requisition_date param to maintain context
    redirect_url = f'{reverse("expense_requisition_confirmation")}?requisition_date={requisition_date}'
    return redirect(redirect_url)

    
    


###  expense list ----
@login_required
def expense_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()    
    expenses = HeadOfExpense.objects.all()   
    expenslisrs = ExpenseVoucher.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")).order_by('-id')
    context = {
        'projects_firts': projects_firt,
        'expenses': expenses,
        'expenslisrs': expenslisrs,
    }
    return render(request, 'expense/expense_list.html', context)



@login_required
def expense_add(request):
    if request.method == "POST":
        form = ExpenseVoucherForm(request.POST)
        if form.is_valid():
            try:
                # Save the form without committing to manipulate before save
                item = form.save(commit=False)

                # Generate mr_or_bill_no if not provided
                if not item.mr_or_bill_no:
                    base_code = "MEX-"
                    last = ExpenseVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
                    next_id = (last.id + 1) if last else 1
                    generated_code = f"{base_code}{next_id:05d}"
                    while ExpenseVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                        next_id += 1
                        generated_code = f"{base_code}{next_id:05d}"
                    item.mr_or_bill_no = generated_code
                else:
                    generated_code = item.mr_or_bill_no

                # Set required fields
                item.approv_status = 'approved'
                item.approval_cr_status = True

                # Save the ExpenseVoucher
                item.save()

                # Create DebitVoucher linked to Expense
                DebitVoucher.objects.create(
                    type='Expense',
                    expense=item.expense_name,
                    bill_date=item.date,  # assuming 'date' in ExpenseVoucher is bill_date
                    project_name=item.project_name,
                    amount=item.amount,
                    particulars=item.particulars,
                    date=item.date,
                    mr_or_bill_no=item.mr_or_bill_no,
                    head_of_account=item.head_of_account,
                    cash_type=item.cash_type,
                    cheque_number=item.cheque_number,
                    requi_id=None,  # replace if needed
                    return_requisition='No',
                    carrier=''  # replace with actual value if available
                )

                return redirect(reverse("expense_list"))

            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Form is invalid.', 'errors': form.errors})

    else:
        form = ExpenseVoucherForm()
    return render(request, "expense/expense_add.html", {"form": form, 'today': now().date()})



@login_required
def expense_edit(request, pk):
    voucher = get_object_or_404(ExpenseVoucher, pk=pk)
    form = ExpenseVoucherForm(request.POST or None, instance=voucher)
    if form.is_valid():
        form.save()
        return redirect('expense_list')
    return render(request, 'expense/expense_edit.html', {'form': form, 'voucher': voucher})


@login_required
def expense_delete(request, pk):
    voucher = get_object_or_404(ExpenseVoucher, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        return redirect('expense_list')
    return render(request, 'expense/expense_delete.html', {'voucher': voucher})


from num2words import num2words
@login_required
def expense_voucher_pdf(request, pk):
    voucher = get_object_or_404(ExpenseVoucher, pk=pk)
    
    def amount_to_words(amount):
        whole_number = int(amount)
        words = num2words(whole_number).replace(',', '').lower()
        return f"{words} taka only"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'expense/print_expensevoucher.html', context)


# @login_required
# def expense_confirmation(request):
#     project_id = request.GET.get('project_id')
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     reference_requisition = ExpenseVoucher.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).first()

#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_items")
#         approv_status = request.POST.get("approv_status")
#         approv_note = request.POST.get("approv_note")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(request.path + f"?project_id={project.id}")

#         if not approv_status:
#             messages.error(request, "Please select an approval status.")
#             return redirect(request.path + f"?project_id={project.id}")

#         try:
#             updated_items = []           
#             for item_id in selected_ids:
#                 item = ExpenseVoucher.objects.get(id=item_id)
#                 item.approv_status = approv_status
#                 item.approv_note = approv_note
#                 item.save()
#                 updated_items.append(item)
           
#             approved_items = [item for item in updated_items if item.approv_status == 'approved']

#             if approved_items:
#                 grouped = defaultdict(list)
#                 for item in approved_items:
#                     key = (item.project_name.id, item.date, item.expense_name.id)
#                     grouped[key].append(item)

#                 for (project_id, bill_date, expense_id), items in grouped.items():
#                     project = ProjectFirstLevelName.objects.get(id=project_id)
#                     expense = ExpenseVoucher.objects.get(id=expense_id)
#                     total_amount = sum(item.amount for item in items)
#                     particulars = " | ".join(str(item.particulars) for item in items)

#                     requisition_obj = items[0]

#                     # Find the first non-empty carrier from grouped items
#                     carrier_name = next((item.carrier for item in items if item.carrier), None)
            
#                     DebitVoucher.objects.create(
#                         type='Expense',
#                         expense=expense.expense_name,
#                         bill_date=bill_date,
#                         project_name=project,
#                         amount=total_amount,
#                         particulars=particulars,
#                         date=requisition_obj.date,
#                         mr_or_bill_no='',
#                         head_of_account=requisition_obj.head_of_account,
#                         cash_type=requisition_obj.cash_type,
#                         requi_id=requisition_obj.id,
#                         return_requisition='No',
#                         carrier=carrier_name  
#                     )

#                 messages.success(request, "Selected items updated and DebitVoucher(s) inserted.")
#                 return redirect("expense_list")

#             else:
#                 messages.warning(request, "No approved Expense items.")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(request.path + f"?project_id={project.id}")

#     # Group requisitions by Expense
#     expense_ids = ExpenseVoucher.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).values_list('expense_name', flat=True).distinct()

#     requisitions_by_expense = {}
#     for exp_id in expense_ids:
#         requisitions = ExpenseVoucher.objects.filter(
#             project_name=project,
#             expense_name=exp_id,
#             approv_status='pending'
#         )
#         expense_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#         expense_obj = requisitions.first().expense_name if requisitions.exists() else None
#         requisitions_by_expense[expense_obj] = {
#             'items': requisitions,
#             'total': expense_total
#         }

#     final_total = ExpenseVoucher.objects.filter(
#         project_name=project,
#         approv_status='pending'
#     ).aggregate(total=Sum('amount'))['total'] or 0
    
#     return render(request, 'expense/expense_confirmation.html', {
#         'project': project,
#         'requisitions_by_expense': requisitions_by_expense,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })





@login_required
def expense_confirmation(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    reference_requisition = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approv_status = request.POST.get("approv_status")
        approv_note = request.POST.get("approv_note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approv_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        try:
            updated_items = []
            for item_id in selected_ids:
                item = ExpenseVoucher.objects.get(id=item_id)
                item.approv_status = approv_status
                item.approv_note = approv_note

                # Generate MR/Bill No if not set
                if not item.mr_or_bill_no:
                    base_code = "MEX-"
                    last = (
                        ExpenseVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                        .order_by('-id')
                        .first()
                    )
                    next_id = (last.id + 1) if last else 1
                    generated_code = f"{base_code}{next_id:05d}"

                    while ExpenseVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                        next_id += 1
                        generated_code = f"{base_code}{next_id:05d}"

                    item.mr_or_bill_no = generated_code

                item.approval_cr_status = True
                item.save()
                updated_items.append(item)

            approved_items = [item for item in updated_items if item.approv_status == 'approved']

            if approved_items:
                grouped = defaultdict(list)
                for item in approved_items:
                    key = (item.project_name.id, item.date, item.expense_name.id)
                    grouped[key].append(item)

                for (project_id, bill_date, expense_id), items in grouped.items():
                    project_obj = ProjectFirstLevelName.objects.get(id=project_id)
                    # For expense, get the related expense_name from first item (avoid wrong query)
                    expense_obj = items[0].expense_name
                    total_amount = sum(item.amount for item in items)
                    particulars = " | ".join(str(item.particulars) for item in items)

                    requisition_obj = items[0]

                    carrier_name = next((item.carrier for item in items if item.carrier), None)

                    DebitVoucher.objects.create(
                        type='Expense',
                        expense=expense_obj,
                        bill_date=bill_date,
                        project_name=project_obj,
                        amount=total_amount,
                        particulars=particulars,
                        date=requisition_obj.date,
                        mr_or_bill_no=generated_code,
                        head_of_account=requisition_obj.head_of_account,
                        cash_type=requisition_obj.cash_type,
                        requi_id=requisition_obj.id,
                        return_requisition='No',
                        carrier=carrier_name
                    )

                messages.success(request, "Selected items updated and DebitVoucher(s) inserted.")
                return redirect("expense_list")
            else:
                messages.warning(request, "No approved Expense items.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # Group requisitions by Expense for GET request
    expense_ids = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).values_list('expense_name', flat=True).distinct()

    requisitions_by_expense = {}
    for exp_id in expense_ids:
        requisitions = ExpenseVoucher.objects.filter(
            project_name=project,
            expense_name=exp_id,
            approv_status='pending'
        )
        expense_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        expense_obj = requisitions.first().expense_name if requisitions.exists() else None
        requisitions_by_expense[expense_obj] = {
            'items': requisitions,
            'total': expense_total
        }

    final_total = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expense/expense_confirmation.html', {
        'project': project,
        'requisitions_by_expense': requisitions_by_expense,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })






def amount_to_words(amount):
    return f"{amount} Taka"

@login_required
def expense_item_summary(request):
    project_id = request.GET.get('project_id')
    expense_id = request.GET.get('expense_id')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

    if expense_id and expense_id.isdigit():
        hexpense = get_object_or_404(HeadOfExpense, id=int(expense_id))
        expense_items = ExpenseVoucher.objects.filter(project_name=project, expense_name=hexpense)
        single_expense = hexpense
        multiple_expenses = None
    else:
        expense_items = ExpenseVoucher.objects.filter(project_name=project)
        expense_ids = expense_items.exclude(expense_name__isnull=True).values_list('expense_name', flat=True).distinct()
        multiple_expenses = HeadOfExpense.objects.filter(id__in=expense_ids)
        single_expense = None

    total_amount = expense_items.aggregate(total=Sum('amount'))['total'] or 0
    expense_date = expense_items.first().date if expense_items.exists() else None

    context = {
        'project': project,
        'single_expense': single_expense,
        'multiple_expenses': multiple_expenses,
        'requisition_items': expense_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
        'requisition_date': expense_date,
    }
    return render(request, 'expense/expense_item_summary.html', context)





@login_required
def expense_admin_confirm(request, pk):
    project = get_object_or_404(ProjectFirstLevelName, id=pk)

    reference_requisition = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).first()

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        approv_status = request.POST.get("approv_status")
        approv_note = request.POST.get("approv_note")

        if not selected_ids:
            messages.error(request, "No items selected.")
            return redirect(request.path + f"?project_id={project.id}")

        if not approv_status:
            messages.error(request, "Please select an approval status.")
            return redirect(request.path + f"?project_id={project.id}")

        try:
            updated_items = []            
            for item_id in selected_ids:
                item = ExpenseVoucher.objects.get(id=item_id)
                item.approv_status = approv_status
                item.approv_note = approv_note
                
                if not item.mr_or_bill_no:
                    base_code = "MEX-"
                    last = (
                        ExpenseVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                        .order_by('-id')
                        .first()
                    )
                    next_id = (last.id + 1) if last else 1
                    generated_code = f"{base_code}{next_id:05d}"

                    while ExpenseVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                        next_id += 1
                        generated_code = f"{base_code}{next_id:05d}"

                    item.mr_or_bill_no = generated_code

                item.approval_cr_status = True
                item.save()
                updated_items.append(item)
            
            approved_items = [item for item in updated_items if item.approv_status == 'approved']

            from collections import defaultdict

            if approved_items:
                grouped = defaultdict(list)
                for item in approved_items:
                    key = (item.project_name.id, item.date, item.expense_name.id)
                    grouped[key].append(item)

                for (project_id, bill_date, expense_id), items in grouped.items():
                    project = ProjectFirstLevelName.objects.get(id=project_id)
                    expense = ExpenseVoucher.objects.get(id=expense_id)
                    total_amount = sum(item.amount for item in items)
                    particulars = " | ".join(str(item.particulars) for item in items)

                    requisition_obj = items[0]

                    # Find the first non-empty carrier from grouped items
                    carrier_name = next((item.carrier for item in items if item.carrier), None)
            
                    DebitVoucher.objects.create(
                        type='Expense',
                        expense=expense.expense_name,
                        bill_date=bill_date,
                        project_name=project,
                        amount=total_amount,
                        particulars=particulars,
                        date=requisition_obj.date,
                        mr_or_bill_no=generated_code,
                        head_of_account=requisition_obj.head_of_account,
                        cash_type=requisition_obj.cash_type,
                        requi_id=requisition_obj.id,
                        return_requisition='No',
                        carrier=carrier_name  # Corrected to use extracted carrier
                    )


                messages.success(request, "Selected items updated and DebitVoucher(s) inserted.")
                return redirect("expense_list")

            else:
                messages.warning(request, "No approved Expense items.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # Group requisitions by Expense
    expense_ids = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).values_list('expense_name', flat=True).distinct()

    requisitions_by_expense = {}
    for exp_id in expense_ids:
        requisitions = ExpenseVoucher.objects.filter(
            project_name=project,
            expense_name=exp_id,
            approv_status='pending'
        )
        expense_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        expense_obj = requisitions.first().expense_name if requisitions.exists() else None
        requisitions_by_expense[expense_obj] = {
            'items': requisitions,
            'total': expense_total
        }

    final_total = ExpenseVoucher.objects.filter(
        project_name=project,
        approv_status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'expense/expense_confirmation.html', {
        'project': project,
        'requisitions_by_expense': requisitions_by_expense,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })





