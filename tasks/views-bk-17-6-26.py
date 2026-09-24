from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.utils import timezone

from hrm.models import RdaEmployee
from resthrm.models import RestaurantEmployee
from projects.models import ProjectFirstLevelName
from .models import EmployeeTask
from .forms import EmployeeTaskForm 

def is_admin(user):
    return user.is_superuser or user.is_staff

# ==========================================
# ADMIN DASHBOARD: BTP OFFICE EMPLOYEES
# ==========================================
@login_required
def task_assign_btp_employee(request):
    if not is_admin(request.user):
        messages.error(request, "Access restricted to administration accounts.")
        return redirect('employee_task_dashboard')
        
    projects = ProjectFirstLevelName.objects.all()
    ct = ContentType.objects.get_for_model(RdaEmployee)
    
    if request.method == "POST":
        form = EmployeeTaskForm(request.POST, request.FILES, employee_type='btp')
        
        if form.is_valid():
            task = form.save(commit=False)
            task.content_type = ct
            task.object_id = form.cleaned_data['employee']  
            task.created_by = request.user
            task.save()
            
            messages.success(request, "Task successfully assigned to BTP Employee.")
            return redirect('task_assign_btp_employee')
        else:
            messages.error(request, "Failed to assign task. Please correct the highlighted errors below.")
    else:
        form = EmployeeTaskForm(employee_type='btp')

    # Re-calculate card statistics safely for the render cycle context
    employees = RdaEmployee.objects.filter(rda_active_status=True)
    employee_cards = []
    for emp in employees:
        tasks = EmployeeTask.objects.filter(content_type=ct, object_id=emp.id)
        pending_count = tasks.filter(status='Pending').count()
        done_count = tasks.filter(status='Completed').count()
        
        employee_cards.append({
            'emp': emp,
            'content_type_id': ct.id,
            'pending': pending_count,
            'done': done_count,
            'total': pending_count + done_count
        })

    return render(request, 'tasks/admin_dashboard.html', {
        'title': 'BTP Office Task Management',
        'projects': projects,
        'employee_cards': employee_cards,
        'employee_type': 'btp',
        'form': form  
    })
    
    
    
# # ==========================================
# # ADMIN DASHBOARD: RESTAURANT EMPLOYEES
# # ==========================================
# @login_required
# def task_assign_resturant_employee(request):
#     if not is_admin(request.user):
#         messages.error(request, "Access restricted to administration accounts.")
#         return redirect('employee_task_dashboard')
        
#     projects = ProjectFirstLevelName.objects.all()
#     ct = ContentType.objects.get_for_model(RestaurantEmployee)
    
#     if request.method == "POST":
#         form = EmployeeTaskForm(request.POST, request.FILES, employee_type='restaurant')
        
#         if form.is_valid():
#             task = form.save(commit=False)
#             task.content_type = ct
#             task.object_id = form.cleaned_data['employee']
#             task.created_by = request.user
#             task.save()
            
#             messages.success(request, "Task successfully assigned to Restaurant Employee.")
#             return redirect('task_assign_resturant_employee')
#         else:
#             messages.error(request, "Failed to assign task. Please correct the form values.")
#     else:
#         form = EmployeeTaskForm(employee_type='restaurant')

#     employees = RestaurantEmployee.objects.filter(rda_active_status=True)
#     employee_cards = []
#     for emp in employees:
#         tasks = EmployeeTask.objects.filter(content_type=ct, object_id=emp.id)
#         pending_count = tasks.filter(status='Pending').count()
#         done_count = tasks.filter(status='Completed').count()
        
#         employee_cards.append({
#             'emp': emp,
#             'content_type_id': ct.id,
#             'pending': pending_count,
#             'done': done_count,
#             'total': pending_count + done_count
#         })

#     return render(request, 'tasks/admin_dashboard.html', {
#         'title': 'Restaurant Task Management',
#         'projects': projects,
#         'employee_cards': employee_cards,
#         'employee_type': 'restaurant',
#         'form': form
#     })


# # ==========================================
# # AJAX DEPENDENT DROPDOWN CONTROLLER
# # ==========================================
# def load_employees(request):
#     project_id = request.GET.get('project_id')
#     emp_type = request.GET.get('type')
#     data = []
    
#     if emp_type == 'btp':
#         employees = RdaEmployee.objects.filter(project_name_id=project_id, rda_active_status=True)
#     else:
#         employees = RestaurantEmployee.objects.filter(project_name_id=project_id, rda_active_status=True)
        
#     for emp in employees:
#         data.append({'id': emp.id, 'name': emp.rda_emp_name})
        
#     return JsonResponse(data, safe=False)


# # ==========================================
# # ADMIN DRILL DOWN VIEW: SEPARATE TABS
# # ==========================================
# @login_required
# def admin_employee_task_details(request, content_type_id, object_id):
#     if not is_admin(request.user):
#         messages.error(request, "Access restricted to administration accounts.")
#         return redirect('employee_task_dashboard')
        
#     ct = get_object_or_404(ContentType, id=content_type_id)
#     employee_model = ct.model_class()
#     employee = get_object_or_404(employee_model, id=object_id)
    
#     all_tasks = EmployeeTask.objects.filter(content_type=ct, object_id=object_id)
#     pending_tasks = all_tasks.filter(status='Pending')
#     completed_tasks = all_tasks.filter(status='Completed')
    
#     return render(request, 'tasks/admin_employee_details.html', {
#         'employee': employee,
#         'pending_tasks': pending_tasks,
#         'completed_tasks': completed_tasks
#     })


# # ==========================================
# # EMPLOYEE SELF DASHBOARD (ISOLATED LOOKUP)
# # ==========================================
# @login_required
# def employee_task_dashboard(request):
#     user_email = getattr(request.user, 'email', None)
    
#     if not user_email:
#         messages.error(request, "Your system user login configuration profile lacks a valid email tracking field.")
#         return render(request, 'tasks/employee_dashboard.html', {'tasks': [], 'employee': None})
        
#     # Scan BTP app space first
#     employee = RdaEmployee.objects.filter(rda_email=user_email, rda_active_status=True).first()
#     if employee:
#         ct = ContentType.objects.get_for_model(RdaEmployee)
#     else:
#         # Scan Restaurant database model space next
#         employee = RestaurantEmployee.objects.filter(rda_email=user_email, rda_active_status=True).first()
#         if employee:
#             ct = ContentType.objects.get_for_model(RestaurantEmployee)
#         else:
#             # Safe Fallback: Handle raw accounts or super admins visiting without breaking template dependencies
#             return render(request, 'tasks/employee_dashboard.html', {
#                 'tasks': [], 
#                 'employee': {'rda_emp_name': request.user.username, 'rda_position': 'Unlinked Admin Profile'}
#             })

#     my_tasks = EmployeeTask.objects.filter(content_type=ct, object_id=employee.id)
#     return render(request, 'tasks/employee_dashboard.html', {
#         'employee': employee,
#         'tasks': my_tasks
#     })


# # ==========================================
# # EMPLOYEE TASK COMPLETION POST SUBMIT
# # ==========================================
# @login_required
# def complete_task_submit(request, task_id):
#     if request.method == "POST":
#         task = get_object_or_404(EmployeeTask, id=task_id)
        
#         # Security Guardrail Check: Enforce user can only complete their own tasks
#         if not is_admin(request.user) and task.employee.rda_email != request.user.email:
#             messages.error(request, "Authorization Denied. Access Violation.")
#             return redirect('employee_task_dashboard')
            
#         task.status = 'Completed'
#         task.completion_note = request.POST.get('completion_note')
#         task.completed_at = timezone.now()
#         task.save()
        
#         messages.success(request, "Task successfully marked complete and sent to admin review.")
#     return redirect('employee_task_dashboard')