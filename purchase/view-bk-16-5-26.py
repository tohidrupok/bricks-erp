from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponseRedirect
from .models import Requisition,HeadOfRequisition,Notification
from .forms import RequisitionForm,HeadOfRequisitionForm,NotificationForm
from django.db.models import Sum
from projects.models import ProjectFirstLevelName
from projects.forms import ProjectFirstLevelName
from hrm.models import Employee
import logging
import json
from .models import Notification
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)
@login_required
def requisition_list(request):
    projects_first = ProjectFirstLevelName.objects.all()
    Requsit = Requisition.objects.all()

    # try:
    #     current_employee = Employee.objects.get(emp_name=request.user.username)
    #     emp_type = current_employee.emp_type.lower()
    # except Employee.DoesNotExist:
    #     emp_type = 'employee'

    # if emp_type == 'admin':
    #     employee = Employee.objects.all()
    # else:
    #     employee = Employee.objects.filter(emp_type=emp_type)

    try:
        current_employee = Employee.objects.get(emp_name=request.user.username)
        emp_type = current_employee.emp_type.lower()
    except Employee.DoesNotExist:
        emp_type = 'employee'
        current_employee = None

    if emp_type == 'admin':
        # Admin: show all employees except admins
        employee = Employee.objects.exclude(emp_type__iexact='admin')
    else:
        # Non-admin: show only the logged-in user
        employee = Employee.objects.filter(emp_name=request.user.username).exclude(emp_type__iexact='admin')

    context = {
        'Requisitions': Requsit, 
        'projects_firts': projects_first,
        'employees': employee
    }

    return render(request, 'requisitions/requisition_list.html', context)




@login_required
def requisitions_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reqsi_data = data.get('data', [])
            employee_id = data.get('employee_id') or request.GET.get('employee')
            project_id = data.get('project_id') or request.GET.get('project_id')
            remark_text = data.get('remark') or request.GET.get('remark')

            if not reqsi_data or not employee_id or not project_id:
                raise ValueError("Missing required fields (data, employee_id, or project_id).")

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_id)

            for item in reqsi_data:
                amount = float(item['qty']) * float(item['rate'])

                form = RequisitionForm({
                    'project_name': project.pk,  # pass PK or instance? Usually PK for forms
                    'employee_name': employee.pk,
                    'item_name': item.get('item_name'),
                    'unit': item.get('unit'),
                    'qty': item.get('qty'),
                    'rate': item.get('rate'),
                    'amount': amount,
                    'remark': remark_text,
                })

                if form.is_valid():
                    form.save()
                    # send_notification_to_role(
                    #     role='admin',
                    #     message='New requisition submitted. Please review.',
                    #     link='/requisition/pending/'  
                    # )
                    # send_notification_to_role(
                    #     role='accounts',
                    #     message='Requisition approved by admin. Awaiting accounts clearance.',
                    #     link='/requisition/accounts-pending/'
                    # )
                    # send_notification_to_role(
                    #     role='purchase',
                    #     message='Requisition cleared by accounts. Proceed to procurement.',
                    #     link='/requisition/purchase-pending/'
                    # )
                else:
                    return JsonResponse({'status': 'error', 'message': f'Form data invalid: {form.errors}'})

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except Exception as e:
            # Log actual error to console
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})

    else:
        form = RequisitionForm()
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
        except (ProjectFirstLevelName.DoesNotExist, Employee.DoesNotExist):
            pass

        return render(request, 'requisitions/requisition_add.html', {
            'form': form,
            'project_id': project_id,
            'employee': employee_id,
            'project_first_name': project_first_name,
            'employee_name': employee_name,
            'headRequists': headRequists,
        })



    

# @login_required
# def requisition_add(request):
#     if request.method == 'POST':
#         form = RequisitionForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('requisition_list')
#     else:
#         form = RequisitionForm()
#     return render(request, 'requisitions/requisition_add.html', {'form': form})



@login_required
def requisition_edit(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if request.method == 'POST':
        form = RequisitionForm(request.POST, instance=requisition)
        if form.is_valid():
            form.save()
            return redirect('requisition_list')
    else:
        form = RequisitionForm(instance=requisition)
        project_name = ProjectFirstLevelName.objects.all()
        employee_names = Employee.objects.all()
        requisition_list = HeadOfRequisition.objects.all()

    context = {
        'form': form,
        'project_list': project_name,
        'employee_names': employee_names,
        'requisition_list': requisition_list,
    }
    return render(request, 'requisitions/requisition_edit.html', context)


@login_required
def requisition_delete(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if request.method == 'POST':
        requisition.delete()
        return redirect('requisition_list')
    return render(request, 'requisitions/requisition_delete.html', {'requisition': requisition})

# @login_required
# def requisition_confirmation(request):
#     project_id = request.GET.get('project_id')
#     project = ProjectFirstLevelName.objects.get(id=project_id)

#     # Get distinct employees who have requisitions under this project
#     employee_ids = Requisition.objects.filter(project_name=project).values_list('employee_name', flat=True).distinct()

#     # Group requisitions by employee and calculate totals
#     requisitions_by_employee = {}
#     for emp_id in employee_ids:
#         requisitions = Requisition.objects.filter(project_name=project, employee_name=emp_id)
#         employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0

#         employee_obj = requisitions.first().employee_name if requisitions.exists() else None
#         requisitions_by_employee[employee_obj] = {
#             'items': requisitions,
#             'total': employee_total
#         }

#     # Calculate the final total
#     final_total = Requisition.objects.filter(project_name=project).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'requisitions/requisition_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total
#     })


### ----------------

# @login_required
# def requisition_confirmation(request):
#     project_id = request.GET.get('project_id')
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     # Get the first requisition as reference
#     reference_requisition = Requisition.objects.filter(project_name=project).first()

#     if request.method == 'POST':
#         approval_status = request.POST.get('approval_status')
#         approv_note = request.POST.get('note')

#         Requisition.objects.filter(project_name=project).update(
#             approv_status=approval_status,
#             approv_note=approv_note
#         )

#         return redirect(f"{request.path}?project_id={project_id}")

#     # Grouped requisitions for display
#     employee_ids = Requisition.objects.filter(project_name=project).values_list('employee_name', flat=True).distinct()
#     requisitions_by_employee = {}
#     for emp_id in employee_ids:
#         requisitions = Requisition.objects.filter(project_name=project, employee_name=emp_id)
#         employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
#         employee_obj = requisitions.first().employee_name if requisitions.exists() else None
#         requisitions_by_employee[employee_obj] = {
#             'items': requisitions,
#             'total': employee_total
#         }

#     final_total = Requisition.objects.filter(project_name=project).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'requisitions/requisition_confirmation.html', {
#         'project': project,
#         'requisitions_by_employee': requisitions_by_employee,
#         'final_total': final_total,
#         'current_status': reference_requisition.approv_status if reference_requisition else '',
#         'current_note': reference_requisition.approv_note if reference_requisition else '',
#     })



@login_required
def requisition_confirmation(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    reference_requisition = Requisition.objects.filter(
        project_name=project,
        approv_status__in=['pending', 'approved']
    ).first()

    if request.method == 'POST':
        approval_status = request.POST.get('approval_status')
        approv_note = request.POST.get('note')
        Requisition.objects.filter(
            project_name=project,
            #approv_status='pending'
            approv_status__in=['pending', 'approved']
        ).update(
            approv_status=approval_status,
            approv_note=approv_note
        )

        return redirect(f"{request.path}?project_id={project_id}")

    employee_ids = Requisition.objects.filter(
        project_name=project,
        approv_status__in=['pending', 'approved']
    ).values_list('employee_name', flat=True).distinct()

    requisitions_by_employee = {}
    for emp_id in employee_ids:
        requisitions = Requisition.objects.filter(
            project_name=project,
            employee_name=emp_id,
            approv_status__in=['pending', 'approved']
        )
        employee_total = requisitions.aggregate(total=Sum('amount'))['total'] or 0
        employee_obj = requisitions.first().employee_name if requisitions.exists() else None
        requisitions_by_employee[employee_obj] = {
            'items': requisitions,
            'total': employee_total
        }

    final_total = Requisition.objects.filter(
        project_name=project,
        approv_status__in=['pending', 'approved']
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'requisitions/requisition_confirmation.html', {
        'project': project,
        'requisitions_by_employee': requisitions_by_employee,
        'final_total': final_total,
        'current_status': reference_requisition.approv_status if reference_requisition else '',
        'current_note': reference_requisition.approv_note if reference_requisition else '',
    })



@login_required
def requisition_detail(request, pk):
    requisition = get_object_or_404(Requisition, id=pk)
    return render(request, 'requisitions/requisition_details.html', {'requisition': requisition})

## headrequisition --
@login_required
def head_of_requisition_list(request):
    head_requisitions = HeadOfRequisition.objects.all()
    return render(request, 'headrequisition/head_of_requisition_list.html', {'head_requisitions': head_requisitions})


@login_required
def add_head_of_requisition(request):
    if request.method == 'POST':
        form = HeadOfRequisitionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('head_of_requisition_list')  
    else:
        form = HeadOfRequisitionForm()
    return render(request, 'headrequisition/add_head_of_requisition.html', {'form': form})



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
    
    return render(request, 'headrequisition/edit_head_of_requisition.html', {
        'form': form,
        'head_account': head_requisition
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