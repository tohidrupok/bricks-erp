from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages

from .models import EmployeeTask
from .forms import EmployeeTaskForm
from hrm.models import RdaEmployee

# Helper validation rule: Checks if the user is an administrator or manager
def is_admin_user(user):
    return user.is_staff or user.is_superuser


# ==========================================
# 1. ADMIN ACTION: ASSIGN BTP EMPLOYEE TASK
# ==========================================
@login_required
@user_passes_test(is_admin_user)
def task_assign_btp_employeex(request):
    if request.method == 'POST':
        form = EmployeeTaskForm(request.POST, request.FILES)
        if 'project' in request.POST:
            try:
                p_id = int(request.POST.get('project'))
                form.fields['employee'].queryset = RdaEmployee.objects.filter(project_name_id=p_id, rda_active_status=True)
            except (ValueError, TypeError):
                pass

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, "Task successfully assigned to Employee!")
            return redirect('task_assign_btp_employee')
    else:
        form = EmployeeTaskForm()
        
    # --- DYNAMIC MATRIX FOR EMPLOYEE CARDS GENERATION ---
    active_employees = RdaEmployee.objects.filter(rda_active_status=True).select_related('project_name')
    employee_cards = []
    
    for emp in active_employees:
        emp_tasks = emp.assigned_tasks.all() 
        pending_count = emp_tasks.filter(status='Pending').count()
        completed_count = emp_tasks.filter(status='Completed').count()
        total_count = emp_tasks.count()
        
        employee_cards.append({
            'emp': emp,
            'pending': pending_count,
            'done': completed_count,
            'total': total_count
        })
        
    context = {
        'form': form, 
        'title': 'Tasks Management Assign',
        'employee_cards': employee_cards
    }
    return render(request, 'tasks/assign_task.html', context)


# ==========================================
# 2. ADMIN VIEW: INDIVIDUAL EMPLOYEE PROFILE AUDIT
# ==========================================
# @login_required
# def admin_employee_task_details(request, employee_id):
#     # SECURITY GATE: If not an admin, verify if they are trying to peek at another profile ID
#     if not is_admin_user(request.user):
#         own_profile = RdaEmployee.objects.filter(rda_email=request.user.email, rda_active_status=True).first()
#         if not own_profile or own_profile.id != employee_id:
#             messages.error(request, "Unauthorized Access Protection: You can only audit your own task history.")
#             return redirect('employee_task_dashboard')

#     employee = get_object_or_404(RdaEmployee, id=employee_id)
#     all_tasks = EmployeeTask.objects.filter(employee=employee)
    
#     context = {
#         'employee': employee,
#         'pending_tasks': all_tasks.filter(status='Pending'),
#         'completed_tasks': all_tasks.filter(status='Completed')
#     }
#     return render(request, 'tasks/employee_audit_history.html', context)


@login_required
def admin_employee_task_details(request, employee_id):
    # If the user is a standard employee, verify they are only trying to access their own ID
    if not is_admin_user(request.user):
        login_username = request.user.username
        login_full_name = request.user.get_full_name()
        
        own_profile = RdaEmployee.objects.filter(
            rda_emp_name__icontains=login_full_name if login_full_name else login_username, 
            rda_active_status=True
        ).first()
        
        if not own_profile:
            own_profile = RdaEmployee.objects.filter(rda_email=request.user.email, rda_active_status=True).first()

        if not own_profile or own_profile.id != employee_id:
            messages.error(request, "Unauthorized Access Protection: You can only audit your own task records.")
            return redirect('employee_task_dashboard')

    employee = get_object_or_404(RdaEmployee, id=employee_id)
    all_tasks = EmployeeTask.objects.filter(employee=employee)
    
    context = {
        'employee': employee,
        'pending_tasks': all_tasks.filter(status='Pending'),
        'completed_tasks': all_tasks.filter(status='Completed')
    }
    return render(request, 'tasks/employee_audit_history.html', context)
    
    

# ==========================================
# 3. AJAX UTILITY: ASYNC PROJECT EMPS LOADER
# ==========================================
@login_required
def load_employees(request):
    project_id = request.GET.get('project')
    if not project_id:
        return JsonResponse([], safe=False)
        
    employees = RdaEmployee.objects.filter(project_name_id=project_id, rda_active_status=True)
    data = [{'id': emp.id, 'name': emp.rda_emp_name} for emp in employees]
    return JsonResponse(data, safe=False)


# # ==========================================
# # 4. USER PORTAL: SELF-SERVICE PORTAL MATRIX
# # ==========================================
# @login_required
# def employee_task_dashboard(request):
#     # Step 1: Locate the active employee record whose primary key matches the logged-in User ID
#     employee = RdaEmployee.objects.filter(
#         id=request.user.id, 
#         rda_active_status=True
#     ).first()
    
#     if not employee:
#         messages.error(
#             request, 
#             "Access Denied: No active employee profile matches your account authentication key."
#         )
#         return render(request, 'tasks/dashboard.html', {'tasks': [], 'employee': None})

#     # Step 2: Extract tasks where the 'employee' foreign key matches our confirmed employee instance
#     tasks = EmployeeTask.objects.filter(employee=employee)
    
#     context = {
#         'employee': employee,
#         'tasks': tasks
#     }
#     return render(request, 'tasks/dashboard.html', context)


# # ==========================================
# # 5. USER ACTION: SUBMIT ACTION PERFORMANCE REPORT
# # ==========================================
# @login_required
# def complete_task_submit(request, task_id):
#     if request.method == 'POST':
#         # Safely fetch the employee context signature matching the user session
#         employee = RdaEmployee.objects.filter(
#             id=request.user.id, 
#             rda_active_status=True
#         ).first()
        
#         if not employee:
#             messages.error(request, "Execution Blocked: Employee record context tracking error.")
#             return redirect('employee_task_dashboard')
            
#         # Secure isolation: Ensure the task belongs explicitly to the matching employee instance
#         task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)
        
#         # Save submission report data logs
#         task.completion_note = request.POST.get('completion_note', '').strip()
#         task.status = 'Completed'
#         task.completed_at = timezone.now()
#         task.save()
        
#         messages.success(request, "Task deployment status verified and closed successfully.")
        
#     return redirect('employee_task_dashboard')


# ==========================================
# 4. USER PORTAL: SELF-SERVICE PORTAL MATRIX
# ==========================================
@login_required
def employee_task_dashboard(request):
    # 1. Extract the name or username details from the Django auth User table
    login_username = request.user.username
    login_full_name = request.user.get_full_name()

    # 2. Find the corresponding single instance inside the RdaEmployee table
    # We look for a match against username first, then fallback to full name
    employee = RdaEmployee.objects.filter(
        rda_emp_name__icontains=login_full_name if login_full_name else login_username, 
        rda_active_status=True
    ).first()

    # Fallback lookup: if your users use their email across both tables
    if not employee:
        employee = RdaEmployee.objects.filter(
            rda_email=request.user.email,
            rda_active_status=True
        ).first()

    # 3. Security Check: Block execution if no profile is found
    if not employee:
        messages.error(
            request, 
            f"Access Denied: No active RdaEmployee profile matches the authenticated user account '{login_username}'."
        )
        return render(request, 'tasks/dashboard.html', {'tasks': [], 'employee': None})

    # 4. Safe Query: Pass the found RdaEmployee instance to the filter
    tasks = EmployeeTask.objects.filter(employee=employee).order_by('-id')
    
    context = {
        'employee': employee,
        'tasks': tasks
    }
    return render(request, 'tasks/dashboard.html', context)


# ==========================================
# 5. USER ACTION: SUBMIT ACTION PERFORMANCE REPORT
# ==========================================
# @login_required
# def complete_task_submit(request, task_id):
#     if request.method == 'POST':
#         login_username = request.user.username
#         login_full_name = request.user.get_full_name()
        
#         # Pull the RdaEmployee instance to authenticate the post request boundary
#         employee = RdaEmployee.objects.filter(
#             rda_emp_name__icontains=login_full_name if login_full_name else login_username, 
#             rda_active_status=True
#         ).first()
        
#         if not employee:
#             employee = RdaEmployee.objects.filter(rda_email=request.user.email, rda_active_status=True).first()

#         if not employee:
#             messages.error(request, "Execution Blocked: Employee record matching layout processing error.")
#             return redirect('employee_task_dashboard')
            
#         # Verify the task belongs explicitly to this RdaEmployee instance
#         task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)
        
#         task.completion_note = request.POST.get('completion_note', '').strip()
#         task.status = 'Completed'
#         task.completed_at = timezone.now()
#         task.save()
        
#         messages.success(request, "Task deployment status verified and closed successfully.")
        
#     return redirect('employee_task_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import EmployeeTask
from hrm.models import RdaEmployee

@login_required
def complete_task_submit(request, task_id):
    if request.method == 'POST':
        login_username = request.user.username
        login_full_name = request.user.get_full_name()
        
        # Authenticate the employee profile boundary
        employee = RdaEmployee.objects.filter(
            rda_emp_name__icontains=login_full_name if login_full_name else login_username, 
            rda_active_status=True
        ).first()
        
        if not employee:
            employee = RdaEmployee.objects.filter(rda_email=request.user.email, rda_active_status=True).first()

        if not employee:
            messages.error(request, "Execution Blocked: Employee record matching layout processing error.")
            return redirect('employee_task_dashboard')
            
        # Verify the task belongs explicitly to this RdaEmployee instance
        task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)
        
        # 1. Update text metadata boundaries
        task.completion_note = request.POST.get('completion_note', '').strip()
        task.status = 'Completed'
        task.completed_at = timezone.now()
        
        # 2. Extract and link the submitted file artifact from request.FILES
        if 'completion_file' in request.FILES:
            task.emp_attachment = request.FILES['completion_file']
            
        task.save()
        
        messages.success(request, "Task deployment status verified and closed successfully.")
        
    return redirect('employee_task_dashboard')
    
    
@login_required
@user_passes_test(is_admin_user)
@login_required
@user_passes_test(is_admin_user)
def task_assign_btp_employee(request):

    if request.method == 'POST':
        form = EmployeeTaskForm(request.POST, request.FILES)

        # ALL employees
        form.fields['employee'].queryset = RdaEmployee.objects.all()

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            messages.success(
                request,
                "Task successfully assigned to Employee!"
            )

            return redirect('task_assign_btp_employee')

    else:
        form = EmployeeTaskForm()

        # ALL employees
        form.fields['employee'].queryset = RdaEmployee.objects.all()

    active_employees = (
        RdaEmployee.objects
        .filter(rda_active_status=True)
        .select_related('project_name')
    )

    employee_cards = []

    for emp in active_employees:
        emp_tasks = emp.assigned_tasks.all()

        employee_cards.append({
            'emp': emp,
            'pending': emp_tasks.filter(status='Pending').count(),
            'done': emp_tasks.filter(status='Completed').count(),
            'total': emp_tasks.count()
        })

    context = {
        'form': form,
        'title': 'Tasks Management Assign',
        'employee_cards': employee_cards
    }

    return render(
        request,
        'tasks/assign_task.html',
        context
    )
