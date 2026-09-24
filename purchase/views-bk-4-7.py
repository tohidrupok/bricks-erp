from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse
from .models import Notification,Requisition,HeadOfRequisition,Notification,RequisitionComparative,HeadOfExpense,ExpenseVoucher,PettyCash
from .forms import RequisitionForm,HeadOfRequisitionForm,RequisitionCategory,RequisitionCategoryForm,RequisitionComparativeForm,HeadOfExpenseForm,ExpenseVoucherForm,PettyCashForm
from django.db.models import Sum
from projects.models import ProjectFirstLevelName,Suppliers,SiteSupervisor,BOQ
from projects.forms import ProjectFirstLevelName
from inventories.models import Inventories
from inventories.forms import InventoriesForm
from hrm.models import Employee
from django.contrib import messages
import logging,traceback, json
from .models import Notification
from django.contrib.auth.models import User
from accounting.models import DebitVoucher,CashType, TransactionHistory,CreditVoucher
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
from inventories.utils import log_deleted_data


logger = logging.getLogger(__name__)
# @login_required
# def requisition_list(request):
#     projects_first = ProjectFirstLevelName.objects.all()
#     suppliers = Suppliers.objects.all()
#     conductors = SiteSupervisor.objects.all()
#     username = request.user.username
#     requisitions = Requisition.objects.filter(
#         return_requisition__isnull=True
#     ).select_related('project_name').order_by('-id')

#     # Group by project
#     project_map = defaultdict(list)
#     for req in requisitions:
#         project_map[req.project_name].append(req)
    
#     if username == 'admin':
#         employees = Employee.objects.exclude(emp_type__iexact='admin')
#     else:
#         employees = Employee.objects.filter(emp_name=username)

#     # Build grouped data for the table
#     grouped_data = []
#     for project, items in project_map.items():
#         total_amount = sum(item.amount for item in items if item.amount)
#         latest_req = items[0]  # You can use latest if needed

#         grouped_data.append({
#             'project_name': project,
#             'requisition_date': latest_req.requisition_date,
#             'total_amount': total_amount,
#             'project_id': project.id  # for linking to detail page if needed
#         })
    
#     context = {
#         'grouped_data': grouped_data,
#         'projects_firts': projects_first,
#         'employees': employees,
#         'suppliers': suppliers,
#         'conductors': conductors,
#     }
#     return render(request, 'requisitions/requisition_list.html', context)



@login_required
def requisition_list(request):
    username = request.user.username

    projects_first = ProjectFirstLevelName.objects.all()
    suppliers = Suppliers.objects.all()
    conductors = SiteSupervisor.objects.all()

    requisitions = (
        Requisition.objects
        .filter(return_requisition__isnull=True)
        .select_related('project_name')
        .order_by('-id')
    )

    # Grouped data to return
    grouped_data = []

    # --- Handle requisitions with requi_uniq_id ---
    uniq_id_map = defaultdict(list)
    project_map = defaultdict(list)

    for req in requisitions:
        if req.project_name:  # Ensure project exists
            if req.requi_uniq_id:
                uniq_id_map[req.requi_uniq_id].append(req)
            else:
                project_map[req.project_name].append(req)

    # Process requi_uniq_id based groupings
    for uniq_id, items in uniq_id_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]  # Assuming the first is the latest due to ordering
        grouped_data.append({
            'group_type': 'uniq_id',
            'requi_uniq_id': uniq_id,
            'requisition_date': latest_req.requisition_date,
            'project_name': latest_req.project_name,
            'total_amount': total_amount,
            'project_id': latest_req.project_name.id
        })

    # Process null requi_uniq_id groupings, fallback to project_name based
    for project, items in project_map.items():
        total_amount = sum(item.amount for item in items if item.amount)
        latest_req = items[0]
        grouped_data.append({
            'group_type': 'project',
            'requi_uniq_id': None,
            'requisition_date': latest_req.requisition_date,
            'project_name': project,
            'total_amount': total_amount,
            'project_id': project.id,
            'employee_names': list(set(req.employee_name.employee_name for req in items)),
        })

    # Filter employee list based on login
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

@login_required
def requisition_by_project(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    requisitions = Requisition.objects.filter(project_name=project)

    context = {
        'project': project,
        'requisitions': requisitions,
    }
    return render(request, 'requisitions/requisition_by_project.html', context)



@login_required
def pettycash_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            remark_text = data.get('remark') or request.GET.get('remark')

            # ✅ Validation check (no 'type' used anymore)
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

            # ✅ Notification (optional)
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
def petty_cash_list(request):
    projects_first = ProjectFirstLevelName.objects.all()
    username = request.user.username

    try:
        current_employee = Employee.objects.get(emp_name=username)
        emp_type = current_employee.emp_type.strip().lower()
    except Employee.DoesNotExist:
        current_employee = None
        emp_type = ''

    # ✅ Removed invalid filter
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

    # ✅ Filter by status (if given)
    if status and status.lower() in ['pending', 'approved', 'rejected']:
        requisition_filter &= Q(approv_status__iexact=status)

    # ✅ Filter by date (if given)
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
            requisition_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

    # ✅ Query PettyCash model instead of Requisition
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

    # ✅ Get distinct employee IDs for this project and optional date
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
        log_deleted_data(requisition, request.user)
        requisition.delete()
        return redirect('petty_cash_list')
    return render(request, 'pettycash/pettycash_delete.html', {'requisition': requisition})






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
def purchase_list(request):
    purch_ids = (
        Requisition.objects
        .filter(approv_acct_status='approved')
        .order_by('-requi_uniq_id')
        .values_list('requi_uniq_id', flat=True)
        .distinct()
    )

    grouped_data = []

    for pid in purch_ids:
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
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'vendor_name': first_item.vendor_name, 
            'total_amount': total_amount,
            'items': items,
        })

    context = {
        'grouped_data': grouped_data,
        'projects_firts': ProjectFirstLevelName.objects.all(),
    }

    return render(request, 'requisitions/purchase_head_cash.html', context)
    
    
@login_required
def purchase_cash_details(request, pk):
    requisitions = Requisition.objects.filter(requi_uniq_id=pk)
    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
    amount_in_words = num2words(total_amount, lang='en').title()
    
    first_item = requisitions.first()
    cash_rec_name = ""

    if first_item and first_item.cash_empl:
        try:
            emp = Employee.objects.get(id=first_item.cash_empl)
            cash_rec_name = emp.employee_name
        except Employee.DoesNotExist:
            cash_rec_name = f"[Unknown ID: {first_item.cash_empl}]"
            
    # first_item = requisitions.first()
    # cash_rec_name = first_item.cash_empl.employee_name if first_item and first_item.cash_empl else ''
    # print(cash_rec_name)
    context = {
        'requi_uniq_id': pk,
        'requisitions': requisitions,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words,
        'received_person': cash_rec_name,
        'print_time': now(), 
        'voucher': requisitions.first(),
    }

    return render(request, 'requisitions/purchase_cash_details.html', context)
    

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


@login_required
def purchase_invoice_list(request):
    purch_ids = Inventories.objects.order_by('-purch_id').values_list('purch_id', flat=True).distinct()

    grouped_data = []
    for pid in purch_ids:
        items = Inventories.objects.filter(purch_id=pid).select_related('project_name').order_by('id')
        if not items.exists():
            continue

        total_amount = sum(item.amount for item in items if item.amount)
        first_item = items.first()  # first row in that group, earliest by id
       
        print(first_item.purch_file.url if first_item.purch_file else 'No file')
        grouped_data.append({
            'purch_id': pid,
            'project_name': first_item.project_name,
            'requisition_date': first_item.requisition_date,
            'vendor_name': first_item.vendor_name,
            'total_amount': total_amount,
            'purch_file': first_item.purch_file,  # file from first row
        })

    return render(request, 'requisitions/purchase_invoice_list.html', {'grouped_data': grouped_data})



from django.http import HttpResponseNotAllowed


#@require_POST
@login_required
def update_purch_file(request, purch_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'], 'Only POST method allowed.')

    uploaded_file = request.FILES.get('purch_file')
    if uploaded_file:
        objs = Inventories.objects.filter(purch_id=purch_id)
        for obj in objs:
            obj.purch_file = uploaded_file
            obj.save()  # triggers proper file saving

    return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def purchase_invoice_details(request, pk):
    requisitions = Inventories.objects.filter(purch_id=pk)
    total_amount = requisitions.aggregate(total=Sum('amount'))['total'] or 0
    amount_in_words = num2words(total_amount, lang='en').title()

    first_entry = requisitions.first()
    vendor_name = first_entry.vendor_name.supplier_name if first_entry and first_entry.vendor_name else ""

    context = {
        'purch_id': pk,
        'requisitions': requisitions,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words,
        'print_time': now(),
        'voucher': first_entry,
        'vendor_name': vendor_name,
    }

    return render(request, 'requisitions/purchase_invoice_details.html', context)



# @login_required
# def requisitions_create(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             reqsi_data = data.get('data', [])
#             employee_id = data.get('employee_id') or request.GET.get('employee')
#             project_id = data.get('project_id') or request.GET.get('project_id')
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not reqsi_data or not employee_id or not project_id:
#                 raise ValueError("Missing required fields (data, employee_id, or project_id).")

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             employee = get_object_or_404(Employee, pk=employee_id)

#             # Track if all forms are valid
#             all_saved = True
#             requisition_date = timezone.now()
#             for item in reqsi_data:
#                 amount = float(item['qty']) * float(item['rate'])                
#                 form = RequisitionForm({
#                     'project_name': project.pk,  
#                     'employee_name': employee.pk,
#                     'item_name': item.get('item_name'),
#                     'vendor_name': item.get('vendor_name'),
#                     'unit': item.get('unit'),
#                     'qty': item.get('qty'),
#                     'rate': item.get('rate'),
#                     'amount': amount,
#                     'remark': remark_text,
#                     'requisition_date': requisition_date,

#                 })

#                 if form.is_valid():
#                     form.save()
#                 else:
#                     all_saved = False
#                     return JsonResponse({'status': 'error', 'message': f'Form data invalid: {form.errors}'})

#             if all_saved:
#                 roles_to_notify = ['admin']
#                 is_admin = request.user.groups.filter(name__iexact='admin').exists()

#                 for role in roles_to_notify:
#                     recipients = User.objects.filter(groups__name__iexact=role)
                    
#                     if is_admin:
#                         try:
#                             sender_user = User.objects.get(username=employee.emp_name)
#                         except User.DoesNotExist:
#                             return JsonResponse({
#                                 'status': 'error',
#                                 'message': f"User with username '{employee.emp_name}' not found."
#                             })
#                     else:
#                         sender_user = request.user

#                     for user in recipients:
#                         Notification.objects.create(
#                             sender=sender_user,
#                             recipient=user,
#                             project_name=project,
#                             message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
#                             is_read=False,
#                             link='',
#                             pass_url='requisition_admin_confirm',
#                             role=role
#                         )

#                 return JsonResponse({'status': 'success', 'message': 'Data saved and notifications sent.'})

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})

#     else:
#         form = RequisitionForm()
#         project_id = request.GET.get('project_id')
#         employee_id = request.GET.get('employee')
#         sppliers = Suppliers.objects.all()
#         headRequists = HeadOfRequisition.objects.all()
#         project_first_name = ''
#         employee_name = ''

#         try:
#             if project_id:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 project_first_name = project.project_first_name

#             if employee_id:
#                 employee = Employee.objects.get(pk=employee_id)
#                 employee_name = employee.employee_name
#         except (ProjectFirstLevelName.DoesNotExist, Employee.DoesNotExist):
#             pass

#         return render(request, 'requisitions/requisition_add.html', {
#             'form': form,
#             'project_id': project_id,
#             'employee': employee_id,
#             'project_first_name': project_first_name,
#             'employee_name': employee_name,
#             'headRequists': headRequists,
#             'sppliers': sppliers,
#         })


# @login_required
# def requisitions_create(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             reqsi_data = data.get('data', [])
#             employee_id = data.get('employee_id') or request.GET.get('employee')
#             project_id = data.get('project_id') or request.GET.get('project_id')
#             req_type = data.get('type') or request.GET.get('type')  # renamed 'type' to 'req_type' to avoid Python keyword
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not reqsi_data or not employee_id or not project_id or not req_type:
#                 return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             employee = get_object_or_404(Employee, pk=employee_id)
#             requisition_date = timezone.now()

#             for item in reqsi_data:
#                 try:
#                     qty = Decimal(str(item['qty'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                     rate = Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                     amount = (qty * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                 except Exception as e:
#                     return JsonResponse({'status': 'error', 'message': f'Invalid qty or rate: {e}'})

#                 # Important: req_type from global POST (not from each item)
#                 form_data = {
#                     'project_name': project.pk,
#                     'employee_name': employee.pk,
#                     'item_name': item.get('item_name'),
#                     'type': req_type,  # use the type from POST
#                     'vendor_name': item.get('vendor_name'),  # Must be a valid choice
#                     'unit': item.get('unit'),
#                     'qty': str(qty),
#                     'rate': str(rate),
#                     'amount': str(amount),
#                     'remark': remark_text,
#                     'requisition_date': requisition_date,
#                 }

#                 form = RequisitionForm(form_data)

#                 if form.is_valid():
#                     form.save()
#                 else:
#                     return JsonResponse({
#                         'status': 'error',
#                         'message': f'Form data invalid: {form.errors}'
#                     })

#             # Create Notifications
#             roles_to_notify = ['admin']
#             is_admin = request.user.groups.filter(name__iexact='admin').exists()

#             for role in roles_to_notify:
#                 recipients = User.objects.filter(groups__name__iexact=role)
#                 sender_user = request.user
#                 if is_admin:
#                     try:
#                         sender_user = User.objects.get(username=employee.emp_name)
#                     except User.DoesNotExist:
#                         return JsonResponse({
#                             'status': 'error',
#                             'message': f"User with username '{employee.emp_name}' not found."
#                         })

#                 for user in recipients:
#                     Notification.objects.create(
#                         sender=sender_user,
#                         recipient=user,
#                         project_name=project,
#                         message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
#                         is_read=False,
#                         link='',
#                         pass_url='requisition_admin_confirm',
#                         role=role
#                     )

#             return JsonResponse({'status': 'success', 'message': 'Data saved and notifications sent.'})

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})

#     else:
#         form = RequisitionForm()
#         project_id = request.GET.get('project_id')
#         employee_id = request.GET.get('employee')
#         type = request.GET.get('type')
#         sppliers = Suppliers.objects.all()
#         conductors = SiteSupervisor.objects.all()
#         headRequists = HeadOfRequisition.objects.all()
#         project_first_name = ''
#         employee_name = ''
        
#         try:
#             if project_id:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 project_first_name = project.project_first_name

#             if employee_id:
#                 employee = Employee.objects.get(pk=employee_id)
#                 employee_name = employee.employee_name
#         except (ProjectFirstLevelName.DoesNotExist, Employee.DoesNotExist):
#             pass
        
#         return render(request, 'requisitions/requisition_add.html', {
#             'form': form,
#             'project_id': project_id,
#             'employee': employee_id,
#             'type': type,
#             'project_first_name': project_first_name,
#             'employee_name': employee_name,
#             'headRequists': headRequists,
#             'sppliers': sppliers,
#             'conductors': conductors,
#         })



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

            if not reqsi_data or not employee_id or not project_id or not req_type:
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
                    'type': req_type,
                    'vendor_name': item.get('vendor_name'),
                    'unit': item.get('unit'),
                    'qty': str(qty),
                    'rate': str(rate),
                    'amount': str(amount),
                    'remark': remark_text,
                    'requisition_date': requisition_date,
                }

                form = RequisitionForm(form_data)

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
                        pass_url='requisition_admin_confirm',
                        role=role
                    )

            return JsonResponse({'status': 'success', 'message': 'Requisition saved and notifications sent.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # Render form
        form = RequisitionForm()
        project_id = request.GET.get('project_id')
        employee_id = request.GET.get('employee')
        type = request.GET.get('type')
        sppliers = Suppliers.objects.all()
        conductors = SiteSupervisor.objects.all()
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

        return render(request, 'requisitions/requisition_add.html', {
            'form': form,
            'project_id': project_id,
            'employee': employee_id,
            'type': type,
            'project_first_name': project_first_name,
            'employee_name': employee_name,
            'headRequists': headRequists,
            'sppliers': sppliers,
            'conductors': conductors,
        })
    



# @login_required
# def requisition_edit(request, pk):
#     requisition = get_object_or_404(Requisition, pk=pk)

#     if request.method == 'POST':
#         form = RequisitionForm(request.POST, instance=requisition)
#         if form.is_valid():
#             form.save()

#             # Manually update approv_status and approv_note
#             requisition.approv_status = request.POST.get('approv_status')
#             requisition.approv_note = request.POST.get('approv_note')
#             requisition.save()

#             messages.success(request, 'Requisition updated successfully.')
#             return redirect('requisition_detail', pk=requisition.pk)
#     else:
#         form = RequisitionForm(instance=requisition)
#         project_name = ProjectFirstLevelName.objects.all()
#         employee_names = Employee.objects.all()
#         requisition_list = HeadOfRequisition.objects.all()
#         supplier_list = Suppliers.objects.all()

#     context = {
#         'form': form,
#         'project_list': project_name,
#         'employee_names': employee_names,
#         'requisition_list': requisition_list,
#         'supplier_list': supplier_list,
#     }
#     return render(request, 'requisitions/requisition_edit.html', context)


@login_required
def requisition_edit(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, instance=requisition)
        if form.is_valid():
            updated = form.save(commit=False)

            # Only allow changing status if not already approved
            if requisition.approv_status != 'approved':
                updated.approv_status = request.POST.get('approv_status')
                updated.approv_note = request.POST.get('approv_note')

            updated.save()
            messages.success(request, 'Requisition updated successfully.')
            return redirect('requisition_detail', pk=requisition.pk)
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


# @login_required
# def project_boq_requisition_summary(request):
#     # Step 1: Get BOQ grouped by project + item_name
#     boq_raw = BOQ.objects.filter(
#         category_type='Material Purchase Cost'
#     ).select_related('project_name')

#     boq_map = {}
#     for boq in boq_raw:
#         key = (boq.project_name.project_first_name, boq.item_name)
#         if key not in boq_map:
#             boq_map[key] = {'qty': 0, 'amount': 0}
#         boq_map[key]['qty'] += boq.qty
#         boq_map[key]['amount'] += boq.amount or 0

#     # Step 2: Get Requisition data grouped the same way
#     requisitions = Requisition.objects.filter(
#         type='Supplier'
#     ).select_related('item_name', 'project_name')

#     req_map = {}
#     for req in requisitions:
#         item_name = req.item_name.head_requi_name
#         project = req.project_name.project_first_name
#         key = (project, item_name)
#         if key not in req_map:
#             req_map[key] = {'qty': 0, 'amount': 0}
#         req_map[key]['qty'] += req.qty
#         req_map[key]['amount'] += req.amount or 0

#     # Step 3: Merge both into combined data
#     all_keys = set(boq_map.keys()) | set(req_map.keys())
#     combined_data = []
#     for project_name, item_name in sorted(all_keys):
#         boq = boq_map.get((project_name, item_name), {'qty': 0, 'amount': 0})
#         req = req_map.get((project_name, item_name), {'qty': 0, 'amount': 0})
#         combined_data.append({
#             'project_name': project_name,
#             'item_name': item_name,
#             'boq_qty': boq['qty'],
#             'boq_amount': boq['amount'],
#             'req_qty': req['qty'],
#             'req_amount': req['amount'],
#             'diff_qty': boq['qty'] - req['qty'],
#             'diff_amount': boq['amount'] - req['amount'],
#         })

#     return render(request, 'requisitions/boq_requisition_summary.html', {
#         'combined_data': combined_data,
#         'is_global': True,
#     })



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
        log_deleted_data(requisition, request.user)
        requisition.delete()
        return redirect('requisition_list')
    return render(request, 'requisitions/requisition_delete.html', {'requisition': requisition})




@login_required
def requisition_confirmation(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

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

        all_saved = True
        notified_users = set()

        try:
            for item_id in selected_ids:
                try:
                    item = Requisition.objects.get(id=item_id)
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.save()

                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:                        
                        pass

                except Requisition.DoesNotExist:
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
            return redirect("requisition_detail", pk=selected_ids[0])  

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")



    # Group requisitions by employee
    employee_ids = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    ).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}
    for emp_id in employee_ids:
        requisitions = Requisition.objects.filter(
            project_name=project,
            employee_name=emp_id,
            approv_status='pending'
        )
        employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        employee_obj = requisitions.first().employee_name if requisitions.exists() else None
        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'requisitions/requisition_confirmation.html', {
        'project': project,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })



# @login_required
# def requisition_acct_confirmation(request):
#     project_id = request.GET.get('project_id')
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     reference_requisition = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).first()

#     if request.method == "POST":
#         selected_ids = request.POST.getlist("selected_items")
#         approv_acct_status = request.POST.get("approv_acct_status")
#         approv_acct_note = request.POST.get("approv_acct_note")

#         if not selected_ids:
#             messages.error(request, "No items selected.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         if not approv_acct_status:
#             messages.error(request, "Please select an approval status.")
#             return redirect(f"{request.path}?project_id={project.id}")

#         try:
#             # If grouping items together, use one unique ID for all
#             unique_purch_id = int(time.time())

#             updated_items = Requisition.objects.filter(id__in=selected_ids)
#             for item in updated_items:
#                 item.approv_acct_status = approv_acct_status
#                 item.approv_acct_note = approv_acct_note
#                 item.requi_uniq_id = unique_purch_id
#                 item.save()

#             messages.success(request, "Selected items updated successfully.")
#             return redirect("requisition_detail", pk=updated_items.first().id)

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(f"{request.path}?project_id={project.id}")

#     # Group requisitions by employee
#     employee_ids = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).values_list('employee_name', flat=True).distinct()

#     requisitions_by_employee = {}
#     for emp_id in employee_ids:
#         requisitions = Requisition.objects.filter(
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

#     final_total = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'requisitions/requisition_acct_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
#     })



# @login_required
# def requisition_acct_confirmation(request):
#     project_id = request.GET.get('project_id')
#     employee_list = Employee.objects.exclude(employee_name='Admin')
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     reference_requisition = Requisition.objects.filter(
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

#             updated_items = Requisition.objects.filter(id__in=selected_ids)
#             for item in updated_items:
#                 item.approv_acct_status = approv_acct_status
#                 item.approv_acct_note = approv_acct_note
#                 item.requi_uniq_id = unique_purch_id
#                 item.cash_empl = cash_empl
#                 item.save()

#             messages.success(request, "Selected items updated successfully.")
#             return redirect("requisition_list")
#             #return redirect("requisition_list", pk=updated_items.first().requi_uniq_id)
            

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect(f"{request.path}?project_id={project.id}")

#     # Group requisitions by employee
#     employee_ids = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).values_list('employee_name', flat=True).distinct()

#     requisitions_by_employee = {}
#     for emp_id in employee_ids:
#         requisitions = Requisition.objects.filter(
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

#     final_total = Requisition.objects.filter(
#         project_name=project,
#         approv_status='approved',
#         approv_acct_status='pending'
#     ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'requisitions/requisition_acct_confirmation.html', {
#         'project': project,
#         'employee_list': employee_list,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_acct_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_acct_note if reference_requisition else '',
#     })



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

        all_saved = True
        notified_users = set()

        try:
            for item_id in selected_ids:
                try:
                    item = Requisition.objects.get(id=item_id)
                    item.approv_status = approval_status
                    item.approv_note = note
                    item.save()
                    
                    try:
                        user = User.objects.get(username=item.employee_name.emp_name)
                        notified_users.add(user)
                    except User.DoesNotExist:

                        pass

                except Requisition.DoesNotExist:
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
            return redirect("requisition_detail", pk=selected_ids[0])  # first selected ID

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path + f"?project_id={project.id}")

    # Group requisitions by employee
    employee_name = request.GET.get('employeeName') 
    queryset = Requisition.objects.filter(
        project_name=project,
        approv_status='pending'
    )

    if employee_name:       
        queryset = queryset.filter(employee_name__emp_name=employee_name)    
    employee_total = queryset.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'requisitions/requisition_admin_confirmation.html', {
        'project': project,
        'requisitions_by_employee': {employee_name: {'items': queryset, 'total': employee_total}},
        'final_total': queryset.aggregate(total=Sum('amount'))['total'] or 0,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })



@login_required
def requisition_detail(request, pk):  
    requisition = get_object_or_404(Requisition, pk=pk)
    project = requisition.project_name
    
    return render(request, 'requisitions/requisition_details.html', {
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
        log_deleted_data(requis_categorys, request.user)
        requis_categorys.delete()
        return redirect('requisition_category')
    return render(request, 'headrequisition/requisition_category_delete.html', {
        'requis_categorys': requis_categorys  
    })


## headrequisition --
@login_required
def head_of_requisition_list(request):
    headrequi = HeadOfRequisition.objects.all()
    return render(request, 'headrequisition/head_of_requisition_list.html', {'headrequi': headrequi})


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
        log_deleted_data(head_requisition, request.user)
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

@login_required
def return_purchase_list(request):
    # GET filters
    project_id = request.GET.get('project_id')
    supplier_param = request.GET.get('supplier_id')
    conductor_id = request.GET.get('conductor')
    reqiDate = request.GET.get('reqiDate')

    # Dropdowns (always needed)
    projects_first = ProjectFirstLevelName.objects.all()
    all_suppliers = Suppliers.objects.all()

    # Get current employee role
    try:
        current_employee = Employee.objects.get(emp_name=request.user.username)
        emp_type = current_employee.emp_type.lower()
    except Employee.DoesNotExist:
        current_employee = None
        emp_type = 'employee'

    # Base filter (return not done, and purchase approved)
    if request.user.is_superuser:
        base_queryset = Requisition.objects.filter(
            Q(return_requisition__isnull=True) | ~Q(return_requisition='Yes'),
            purch_appov='Yes'
        )
    else:
        try:
            employee = Employee.objects.get(emp_name=request.user)
            base_queryset = Requisition.objects.filter(
                Q(return_requisition__isnull=True) | ~Q(return_requisition='Yes'),
                purch_appov='Yes',
                employee_name=employee
            )
        except Employee.DoesNotExist:
            base_queryset = Requisition.objects.none()

    # If filters are provided, apply additional filtering
    if project_id:
        try:
            project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
        except ValueError:
            return HttpResponse("Invalid project ID.", status=400)

        requisition_filter = Q(project_name=project)
        supplier = None
        filtered_suppliers = None

        # Handle supplier filter (by ID or name, but vendor_name is CharField)
        if supplier_param:
            supplier_param = supplier_param.strip()
            try:
                # Try treating as supplier ID
                supplier_obj = Suppliers.objects.get(id=int(supplier_param))
                requisition_filter &= Q(vendor_name__iexact=supplier_obj.supplier_name)
                filtered_suppliers = [supplier_obj]
                supplier = supplier_obj
            except (ValueError, Suppliers.DoesNotExist):
                # Try by name (case-insensitive)
                try:
                    supplier_obj = Suppliers.objects.get(supplier_name__iexact=supplier_param)
                    requisition_filter &= Q(vendor_name__iexact=supplier_obj.supplier_name)
                    filtered_suppliers = [supplier_obj]
                    supplier = supplier_obj
                except Suppliers.DoesNotExist:
                    return HttpResponse("Supplier not found.", status=404)

        # Handle conductor filter
        elif conductor_id and conductor_id.isdigit():
            try:
                conductor = Suppliers.objects.get(id=int(conductor_id))
                requisition_filter &= Q(vendor_name__iexact=conductor.supplier_name)
                filtered_suppliers = [conductor]
                supplier = conductor
            except Suppliers.DoesNotExist:
                return HttpResponse("Conductor not found.", status=404)

        # Handle purchase date filter
        if reqiDate:
            try:
                parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
                requisition_filter &= Q(purch_date=parsed_date)
            except ValueError:
                return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

        # Final filtered result
        requisition_items = base_queryset.filter(requisition_filter)

        # Collect all suppliers used if not already filtered
        if not filtered_suppliers:
            supplier_names = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
            filtered_suppliers = Suppliers.objects.filter(supplier_name__in=supplier_names)

        # Summation & date
        total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
        requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

        # Helper: amount in words
        def amount_to_words(amount):
            amount = round(float(amount), 2)
            taka = int(amount)
            poisha = int(round((amount - taka) * 100))
            taka_words = num2words(taka, lang='en').capitalize() + " Taka"
            return f"{taka_words} and {num2words(poisha, lang='en')} Poisha" if poisha > 0 else taka_words

        context = {
            'project': project,
            'supplier': supplier,
            'suppliers': filtered_suppliers,
            'Requisitions': requisition_items,
            'total_amount': total_amount,
            'amount_in_words': amount_to_words(total_amount),
            'print_time': now(),
            'requisition_date': requisition_date,
            'projects_firts': projects_first,
        }
        return render(request, 'requisitions/return_purchase_list.html', context)
    

    if emp_type == 'admin':
        employees = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        employees = Employee.objects.filter(emp_name=request.user.username).exclude(emp_type__iexact='admin')

    requisitions = base_queryset  
   
    for requisition in requisitions:
        if requisition.return_qty is not None:
            requisition.qty_after_return = requisition.qty - requisition.return_qty
        else:
            requisition.qty_after_return = requisition.qty
        
        if hasattr(requisition, 'rate') and requisition.rate is not None:
            requisition.amount_after_return = requisition.qty_after_return * requisition.rate
        else:
            requisition.amount_after_return = requisition.amount  # fallback

    context = {
        'projects_firts': projects_first,
        'employees': employees,
        'suppliers': all_suppliers,
        'requisitions': requisitions,
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
    requisitions = Requisition.objects.filter(return_qty__gt=0).order_by('-id')

    # Add calculated fields for template use
    for r in requisitions:
        r.payment_amount = r.qty * r.rate  # Full payment (Qty × Rate)
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

#             approved_items = [
#                 item for item in updated_items
#                 if item.approv_status == 'approved' and
#                    item.approv_acct_status == 'approved' and
#                    item.approv_purch_status == 'approved'
#             ]

#             if approved_items:
#                 unique_purch_id = int(time.time())
#                 for item in approved_items:
#                     Inventories.objects.create(
#                         project_name=item.project_name,
#                         employee_name=item.employee_name,
#                         vendor_name=item.vendor_name,
#                         item_name=item.item_name,
#                         unit=item.unit,
#                         qty=item.qty,
#                         rate=item.rate,
#                         amount=item.amount,
#                         remark=item.remark,
#                         approv_note=item.approv_note,
#                         approv_acct_note=item.approv_acct_note,
#                         approv_purch_note=item.approv_purch_note,
#                         requisition_date=item.requisition_date,
#                         requi_id=item.id,
#                         qtysub=item.qty,
#                         purch_id =unique_purch_id
#                     )
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


@login_required
def requisition_approv_list(request):
    project_id = request.GET.get('project_id')
    supplier_id = request.GET.get('supplier_id')
    conductor_id = request.GET.get('conductor')

    # Validate project ID
    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid project ID.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
    supplier = None
    suppliers = None

    # Build the Q filter for vendor_name (supplier OR conductor)
    vendor_filter = Q()
    if supplier_id and supplier_id.isdigit():
        supplier = get_object_or_404(Suppliers, id=int(supplier_id))
        vendor_filter = Q(vendor_name=supplier)
        suppliers = [supplier]
    elif conductor_id and conductor_id.isdigit():
        supplier = get_object_or_404(Suppliers, id=int(conductor_id))
        vendor_filter = Q(vendor_name=supplier)
        suppliers = [supplier]

    # Fetch all filtered requisitions
    requisition_queryset = Requisition.objects.filter(
        Q(project_name=project) &
        Q(approv_status='approved') &
        Q(approv_acct_status='approved') &
        Q(approv_purch_status='pending') &
        vendor_filter
    )

    # If no specific supplier/conductor was selected, get all relevant suppliers
    if not suppliers:
        supplier_ids = requisition_queryset.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
        suppliers = Suppliers.objects.filter(id__in=supplier_ids)

    # Get a reference requisition for current status/note
    reference_requisition = requisition_queryset.first()

    # === POST Logic ===
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

                # Fetch vendor name from the dynamically named field
                vendor_field_name = f"vendor_{item_id}"
                vendor_name = request.POST.get(vendor_field_name, '').strip()

                # Assign fields
                item.vendor_name = vendor_name  # Store vendor name (not ID)
                item.approv_purch_status = approv_purch_status
                item.approv_purch_note = approv_purch_note
                item.purch_appov = 'Yes'
                item.purch_date = timezone.now().date()
                item.save()

                updated_items.append(item)

            # Only fully approved items go to inventory
            approved_items = [
                item for item in updated_items
                if item.approv_status == 'approved' and
                   item.approv_acct_status == 'approved' and
                   item.approv_purch_status == 'approved'
            ]

            if approved_items:
                vendor_group = defaultdict(list)
                for item in approved_items:
                    vendor_group[item.vendor_name].append(item)  # vendor_name is string here

                for vendor_name_str, items in vendor_group.items():
                    # Try to find the Supplier object for this vendor name string
                    try:
                        vendor_obj = Suppliers.objects.get(supplier_name=vendor_name_str)
                    except Suppliers.DoesNotExist:
                        vendor_obj = None  # Or handle the missing supplier as needed

                    unique_purch_id = int(time.time())
                    time.sleep(1)  # avoid duplicate timestamp

                    for item in items:
                        Inventories.objects.create(
                            project_name=item.project_name,
                            employee_name=item.employee_name,
                            vendor_name=vendor_obj,  
                            item_name=item.item_name,
                            unit=item.unit,
                            qty=item.qty,
                            rate=item.rate,
                            amount=item.amount,
                            remark=item.remark,
                            approv_note=item.approv_note,
                            approv_acct_note=item.approv_acct_note,
                            approv_purch_note=item.approv_purch_note,
                            requisition_date=item.requisition_date,
                            requi_id=item.id,
                            qtysub=item.qty,
                            purch_id=unique_purch_id,
                            purch_date = timezone.now().date()
                        )

                messages.success(request, "Selected items updated and inventory records inserted.")
                return redirect("purchase_list")
            else:
                messages.warning(request, "No approved requisition items to create inventory records.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.get_full_path())

    # Group requisitions by vendor
    vendor_ids = requisition_queryset.values_list('vendor_name', flat=True).distinct()
    requisitions_by_vendor = {}
    for ven_id in vendor_ids:
        requisitions = requisition_queryset.filter(vendor_name=ven_id)
        vendor_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        vendor_obj = requisitions.first().vendor_name if requisitions.exists() else None
        requisitions_by_vendor[vendor_obj] = {
            'items': requisitions,
            'total': vendor_total
        }

    final_total = requisition_queryset.aggregate(total=Sum('amount'))['total'] or 0

    supplier_list= Suppliers.objects.all()
    contructors_list= SiteSupervisor.objects.all()

    return render(request, 'requisitions/requisition_approv_list.html', {
        'project': project,
        'requisitions_by_vendor': requisitions_by_vendor,
        'final_total': final_total,
        'current_status': reference_requisition.approv_purch_status if reference_requisition else '',
        'current_note': reference_requisition.approv_purch_note if reference_requisition else '',
        'suppliers': suppliers,
        'supplier_list': supplier_list,
        'contructors_list': contructors_list,
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

# def amount_to_words(amount):
#     return f"{amount} Taka"

# @login_required
# def requisition_item_summary(request):
#     project_id = request.GET.get('project_id')
#     supplier_id = request.GET.get('supplier_id')
#     supplier_id = request.GET.get('conductor')

#     status = request.GET.get('status')  

#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

#     requisition_filter = Q(project_name=project)

#     if supplier_id and supplier_id.isdigit():
#         supplier = get_object_or_404(Suppliers, id=int(supplier_id))
#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]
#     else:
#         supplier = None
#         suppliers = None  # we'll set it later after filtering requisitions

#     if status in ['Pending', 'Approved', 'Rejected']:
#         requisition_filter &= Q(approv_status=status)

#     # Apply all filters
#     requisition_items = Requisition.objects.filter(requisition_filter)

#     if not supplier:
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
#             return f"{taka_words} and {poisha_words} only"
#         else:
#             return f"{taka_words} only"
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



# @login_required
# def requisition_item_summary(request):
#     project_id = request.GET.get('project_id')
#     supplier_id = request.GET.get('supplier_id')
#     conductor_id = request.GET.get('conductor')
#     status = request.GET.get('status')  
#     reqiDate = request.GET.get('reqiDate') 

#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))
#     requisition_filter = Q(project_name=project)

#     supplier = None
#     suppliers = None

#     # Filter either by supplier or conductor
#     if supplier_id and supplier_id.isdigit():
#         supplier = get_object_or_404(Suppliers, id=int(supplier_id))
#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]

#     elif conductor_id and conductor_id.isdigit():
#         supplier = get_object_or_404(Suppliers, id=int(conductor_id))
#         requisition_filter &= Q(vendor_name=supplier)
#         suppliers = [supplier]

#     if status in ['Pending', 'Approved', 'Rejected']:
#         requisition_filter &= Q(approv_status=status)

#     # Apply filters
#     requisition_items = Requisition.objects.filter(requisition_filter)

#     # If no specific supplier or conductor selected, fetch all relevant suppliers
#     if not suppliers:
#         supplier_ids = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
#         suppliers = Suppliers.objects.filter(id__in=supplier_ids)

#     total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
#     requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None

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

    # andle supplier name or ID
    if supplier_param:
        try:
            # Try treating as ID
            supplier = Suppliers.objects.get(id=int(supplier_param))
        except (ValueError, Suppliers.DoesNotExist):
            # Try treating as name (case-insensitive)
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

    # Status filter (case-insensitive)
    if status and status.lower() in ['pending', 'approved', 'rejected']:
        requisition_filter &= Q(approv_status__iexact=status)

    # Date filter
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, "%Y-%m-%d").date()
            requisition_filter &= Q(requisition_date=parsed_date)
        except ValueError:
            return HttpResponse("Invalid requisition_date format. Use YYYY-MM-DD.", status=400)

    # inal filtered query
    requisition_items = Requisition.objects.filter(requisition_filter)

    if not suppliers:
        supplier_ids = requisition_items.exclude(vendor_name__isnull=True).values_list('vendor_name', flat=True).distinct()
        suppliers = Suppliers.objects.filter(id__in=supplier_ids)

    total_amount = requisition_items.aggregate(total=Sum('amount'))['total'] or 0
    requisition_date = requisition_items.first().requisition_date if requisition_items.exists() else None
    
    employee_ids = requisition_items.values_list('employee_name', flat=True).distinct()
    employees = Employee.objects.filter(id__in=employee_ids)

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
        'supplier': supplier,
        'suppliers': suppliers,
        'requisition_items': requisition_items,
        'total_amount': total_amount,
        'amount_in_words': amount_to_words(total_amount),
        'print_time': now(),
        'requisition_date': requisition_date,
        'employees': employees
    }
    return render(request, 'requisitions/requisition_item_summary.html', context)



## requisition comparative --
@login_required
def requisition_comparative_list(request):
    requisitions_category = RequisitionComparative.objects.all().order_by('-id')
    projects_first = ProjectFirstLevelName.objects.all()
    context = {
        'requisitions_categorys': requisitions_category, 
        'projects_firts': projects_first,
    }
    return render(request, 'headrequisition/requisition_comparative_list.html', context)


  

# @login_required
# def add_requisition_comparative(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             reqsi_data = data.get('data', [])
#             employee_id = data.get('employee_id') or request.GET.get('employee')
#             project_id = data.get('project_id') or request.GET.get('project_id')
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not reqsi_data or not employee_id or not project_id:
#                 return JsonResponse({'status': 'error', 'message': "Missing required fields (data, employee_id, or project_id)."})

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             employee = get_object_or_404(Employee, pk=employee_id)

#             all_saved = True
#             requisition_date = timezone.now()

#             for item in reqsi_data:
#                 form = RequisitionComparativeForm({
#                     'project_name': project.pk,
#                     'employee_name': employee.pk,
#                     'item_name': item.get('item_name'),
#                     'vendor_name': item.get('vendor_name'),
#                     'unit': item.get('unit'),
#                     'qty': item.get('qty'),
#                     'rate': item.get('rate'),
#                     'remark': remark_text,
#                     'requisition_date': requisition_date                   
#                 })

#                 if form.is_valid():
#                     form.save()
#                 else:
#                     all_saved = False
#                     return JsonResponse({'status': 'error', 'message': f'Form data invalid: {form.errors}'})

#             if all_saved:
#                 roles_to_notify = ['admin']
#                 is_admin = request.user.groups.filter(name__iexact='admin').exists()

#                 for role in roles_to_notify:
#                     recipients = User.objects.filter(groups__name__iexact=role)

#                     if is_admin:
#                         try:
#                             sender_user = User.objects.get(username=employee.emp_name)
#                         except User.DoesNotExist:
#                             return JsonResponse({
#                                 'status': 'error',
#                                 'message': f"User with username '{employee.emp_name}' not found."
#                             })
#                     else:
#                         sender_user = request.user

#                     for user in recipients:
#                         Notification.objects.create(
#                             sender=sender_user,
#                             recipient=user,
#                             project_name=project,
#                             message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
#                             is_read=False,
#                             link='',
#                             pass_url='requisition_comparative_admin_confirm',
#                             role=role
#                         )

#                 return JsonResponse({'status': 'success', 'message': 'Data saved and notifications sent.'})

#         except Exception as e:
#             traceback.print_exc()
#             return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})

#     else:
#         form = RequisitionForm()
#         sppliers = Suppliers.objects.all()
#         headRequists = HeadOfRequisition.objects.all()
#         project = ProjectFirstLevelName.objects.all()

#         return render(request, 'headrequisition/add_requisition_comparative.html', {
#             'form': form,
#             'project_lists': project,
#             'headRequists': headRequists,
#             'sppliers': sppliers,
#         })



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


# @login_required
# def requisition_comparative_print(request):
#     project_id = request.GET.get('project_id')
#     if not project_id:
#         return render(request, 'error.html', {'message': 'Project ID is required to print comparative.'})

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    
#     # Fetch related comparative data for the project
#     comparisons = RequisitionComparative.objects.filter(project_name=project)

#     context = {
#         'project': project,
#         'comparisons': comparisons,
#     }

#     return render(request, 'headrequisition/print_comparative.html', context)
    


from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import RequisitionComparative, ProjectFirstLevelName  # and others as needed

@login_required
def requisition_comparative_print(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return render(request, 'error.html', {'message': 'Project ID is missing.'})

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    comparisons = RequisitionComparative.objects.filter(project_name=project)

    # ✅ Use correct path to vendor name field from ForeignKey: vendor_name__supplier_name
    vendor_names = comparisons.values_list('vendor_name__supplier_name', flat=True).distinct()

    item_names = comparisons.values_list('item_name__head_name', flat=True).distinct()

    items = []
    for item_name in item_names:
        item_group = comparisons.filter(item_name__head_name=item_name)
        if not item_group.exists():
            continue

        base = item_group.first()
        vendor_data = []

        # group by vendor
        vendor_rates = {}
        for vendor in vendor_names:
            entry = item_group.filter(vendor_name__supplier_name=vendor).first()
            if entry:
                vendor_rates[vendor] = entry.rate or 0

        rates_only = [rate for rate in vendor_rates.values() if rate > 0]
        lowest = min(rates_only) if rates_only else None
        highest = max(rates_only) if rates_only else None

        for vendor in vendor_names:
            entry = item_group.filter(vendor_name__supplier_name=vendor).first()
            if entry:
                rate = entry.rate or 0
                amount = rate * float(entry.qty)
                vendor_data.append({
                    'id': entry.id,
                    'rate': rate,
                    'amount': amount,
                    'is_lowest': rate == lowest,
                    'is_highest': rate == highest,
                    'selected': False  # Optional: add if selection logic is present
                })
            else:
                vendor_data.append({
                    'rate': None,
                    'amount': None,
                    'is_lowest': False,
                    'is_highest': False,
                    'selected': False
                })

        items.append({
            'item_name': item_name,
            'unit': base.unit,
            'qty': base.qty,
            'vendor_data': vendor_data
        })

    # ✅ Aggregate total by vendor (using correct field path)
    vendor_totals = []
    final_total = 0
    for vendor in vendor_names:
        total = comparisons.filter(vendor_name__supplier_name=vendor).aggregate(
            total=Sum('rate')
        )['total'] or 0
        vendor_totals.append(total)
        final_total += total

    return render(request, 'headrequisition/print_comparative.html', {
        'project': project,
        'vendor_names': vendor_names,
        'items': items,
        'vendor_totals': vendor_totals,
        'final_total': final_total,
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
        log_deleted_data(requisition, request.user)
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
        log_deleted_data(head_requisition, request.user)
        head_requisition.delete()
        return redirect('expense_head_list')
    return render(request, 'expense/delete_head_of_expense.html', {
        'head_requisition': head_requisition  
    })


###  expense list ----
@login_required
def expense_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()    
    expenses = HeadOfExpense.objects.all()   
    expenslisrs = ExpenseVoucher.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes"))
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
                expense = form.save()
                roles_to_notify = ['admin']
                is_admin = request.user.groups.filter(name__iexact='admin').exists()

                for role in roles_to_notify:
                    recipients = User.objects.filter(groups__name__iexact=role)

                    # Get sender
                    sender_user = request.user

                    for user in recipients:
                        Notification.objects.create(
                            sender=sender_user,
                            recipient=user,
                            project_name=expense.project_name,
                            message=f"New expense voucher submitted by {sender_user} for project {expense.project_name}.",
                            is_read=False,
                            link='',
                            pass_url='expense_admin_confirm',
                            role=role
                        )

                JsonResponse({'status': 'success', 'message': 'Expense voucher saved and notifications sent.'})
                return redirect(reverse("expense_list"))
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Form is invalid.', 'errors': form.errors})

    else:
        form = ExpenseVoucherForm()
    return render(request, "expense/expense_add.html", {"form": form})





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
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('expense_list')
    return render(request, 'expense/expense_delete.html', {'voucher': voucher})


@login_required
def expense_voucher_pdf(request, pk):
    voucher = get_object_or_404(ExpenseVoucher, pk=pk)
    def amount_to_words(amount):
        return f"{amount} Taka"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'expense/print_expensevoucher.html', context)


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
                item.save()
                updated_items.append(item)
           
            approved_items = [item for item in updated_items if item.approv_status == 'approved']

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
                        mr_or_bill_no=requisition_obj.mr_or_bill_no or "-",
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
                        mr_or_bill_no=requisition_obj.mr_or_bill_no or "-",
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


