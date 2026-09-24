from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Employee,Attendance,Payroll,Payslip,AdvancePayment,Leave,Iom,Note,Allowances,RdaEmployee,LoanPayment,SalaryVoucher
from .forms import EmployeeForm,AttendanceForm,PayrollForm,PayslipForm,AdvancePaymentForm,LeaveForm,IomForm,NoteForm,AllowancesForm,RdaEmployeeForm,LoanPaymentForm,AttendanceCheckoutForm
from django.contrib.auth.models import User, Group
from datetime import datetime, time
from datetime import datetime
from calendar import monthrange
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.timezone import now
from .forms import EmployeeAllowanceUpdateForm,EmployeePhotoUpdateForm,SalaryPaymentForm
from datetime import date
import csv
import io
from django.contrib import messages
from .models import Attendance, Employee,SalaryPayment,UserBreak
from .forms import AttendanceUploadForm
from inventories.utils import log_deleted_data
from projects.models import ProjectFirstLevelName
from accounting.models import LedgerEntry,HeadOfAccount,CashType,TransactionHistory,DebitVoucher
from datetime import datetime, date, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
from projects.models import ProjectFirstLevelName 
from django.urls import reverse
import calendar
from collections import defaultdict


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def user_profile(request):
  user = request.user

  # Safely get or initialize the associated employee record
  employee, created = Employee.objects.get_or_create(
      user=user, defaults={'email': user.email, 'employee_name': user.username}
  )

  if request.method == 'POST':
    # 1. Update User model basic fields
    user.first_name = request.POST.get('first_name', user.first_name)
    user.last_name = request.POST.get('last_name', user.last_name)
    user.email = request.POST.get('email', user.email)

    # 2. Handle Password Change Logic if provided
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    if current_password or new_password or confirm_password:
      if not current_password or not new_password or not confirm_password:
        messages.error(
            request,
            'Please fill in all password fields to change your password.',
        )
        return redirect('user_profile')

      if not user.check_password(current_password):
        messages.error(request, 'Your current password was entered incorrectly.')
        return redirect('user_profile')

      if new_password != confirm_password:
        messages.error(request, 'The new passwords do not match.')
        return redirect('user_profile')

      user.set_password(new_password)
      messages.success(request, 'Password updated successfully!')

    user.save()

    # Update session name if stored
    request.session['user_name'] = user.get_full_name() or user.username

    # 3. Update Employee model fields & photo safely
    employee.employee_name = request.POST.get(
        'employee_name', employee.employee_name
    )
    employee.phone = request.POST.get('phone', employee.phone)
    employee.email = user.email
    employee.address = request.POST.get('address', employee.address)
    employee.position = request.POST.get('position', employee.position)

    if 'photo' in request.FILES:
      employee.photo = request.FILES['photo']

    employee.save()

    messages.success(request, 'Profile updated successfully!')
    return redirect('user_profile')

  return render(
      request,
      'hrm/user_profile.html',
      {
          'profile_user': user,
          'employee': employee,
      },
  )
    

@login_required
def profile(request):
    user_break, created = UserBreak.objects.get_or_create(user=request.user)
    return render(request, 'profile/profile.html', {'user_break': user_break})

@login_required
def start_break(request):
    if request.method == 'POST':
        user_break, created = UserBreak.objects.get_or_create(user=request.user)
        user_break.break_start = timezone.now()
        user_break.is_on_break = True
        user_break.break_end = None
        user_break.save()
        return JsonResponse({'status': 'success', 'break_start': user_break.break_start.strftime("%Y-%m-%d %H:%M:%S")})
    return JsonResponse({'status': 'failed'}, status=400)


@login_required
def end_break(request):
    if request.method == 'POST':
        user_break, created = UserBreak.objects.get_or_create(user=request.user)
        user_break.break_end = timezone.now()
        user_break.is_on_break = False
        user_break.save()
        return JsonResponse({'status': 'success', 'break_end': user_break.break_end.strftime("%Y-%m-%d %H:%M:%S")})
    return JsonResponse({'status': 'failed'}, status=400)
    
    


@login_required
def break_history(request):
    if request.user.is_staff or request.user.is_superuser:
        user_breaks = UserBreak.objects.select_related("user").order_by("-break_start")
    else:
        user_breaks = UserBreak.objects.filter(user=request.user).order_by("-break_start")

    # Add duration to each break
    break_data = []
    for br in user_breaks:
        if br.break_end:
            duration = br.break_end - br.break_start
        else:
            # if break still ongoing
            duration = timezone.now() - br.break_start

        # Convert duration to hours:minutes format
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        duration_str = f"{hours}h {minutes}m"

        break_data.append({
            'break': br,
            'duration': duration_str
        })

    return render(request, "profile/break_history.html", {
        "break_data": break_data
    })

    
    

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee/employee_list.html', {'employees': employees})



@login_required
def employee_details(request):
    #employees = RdaEmployee.objects.all()
    employees = RdaEmployee.objects.filter(
        rda_active_status=True
    ).order_by('rda_emp_name')
    projects_firts = ProjectFirstLevelName.objects.all()
    return render(request, 'employee/employee_details.html', {'employees': employees, 'projects_firts': projects_firts})


@login_required
def employee_project_detail(request):
    project_id = request.GET.get("project_id")

    if project_id:
        employees = RdaEmployee.objects.filter(project_name_id=project_id)
    else:
        employees = RdaEmployee.objects.all()

    projects_firts = ProjectFirstLevelName.objects.all()

    return render(
        request,
        "employee/employee_details.html",
        {
            "employees": employees,
            "projects_firts": projects_firts,
            "selected_project": project_id,
        },
    )


@login_required
def employee_add(request):
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        employee = form.save(commit=False)
        username = employee.emp_name

        user = User.objects.create_user(
            username=username,
            email=employee.email,
            password='123456',
            first_name=employee.employee_name
        )

        # Assign group based on emp_type
        emp_type = employee.emp_type.lower()
        try:
            group = Group.objects.get(name=emp_type.capitalize())
            user.groups.add(group)
        except Group.DoesNotExist:
            pass

        employee.user = user
        employee.save()       
        return redirect('employee_list')

    return render(request, 'employee/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        log_deleted_data(employee, request.user)
        user = employee.user
        employee.delete()
        
        # Delete the associated User, if it exists
        if user:
            user.delete()
        
        return redirect('employee_list')

    return render(request, 'employee/employee_confirm_delete.html', {'employee': employee})



@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employee/employee_detail.html', {'employee': employee})





@login_required
def monthly_salary_generate(request):
    project_input = request.GET.get("project")
    month_input = request.GET.get("month")
    today = now()
    current_year = today.year

    # --- Month filter ---
    if month_input:
        try:
            # Accept "September" or "September 2025"
            month_parts = month_input.split()
            month_name_only = month_parts[0]  # "September"
            month_datetime = datetime.strptime(month_name_only, "%B")
            selected_month = month_datetime.strftime("%B")
        except ValueError:
            selected_month = today.strftime("%B")
    else:
        selected_month = today.strftime("%B")

    full_month_label = f"{selected_month} {current_year}"

    # --- Project filter ---
    project = None
    project_name = None
    project_id = None
    if project_input:
        project = get_object_or_404(ProjectFirstLevelName, id=project_input)
        project_name = project.project_first_name
        project_id = project.id

    # --- Create or fetch voucher ---
    voucher, created = SalaryVoucher.objects.get_or_create(
        project=project,
        month_name=full_month_label,
        defaults={"approval_salary_status": "Pending"},
    )

    # --- Employees ---
    employees = RdaEmployee.objects.filter(rda_active_status=True)
    if project:
        employees = employees.filter(project_name=project)

    # --- Group employees by type + totals ---
    employee_groups = defaultdict(lambda: {"employees": [], "total_salary": Decimal(0)})
    grand_total_salary = Decimal(0)

    for emp in employees:
        emp_type = emp.rda_emp_type or "Uncategorized"
        employee_groups[emp_type]["employees"].append(emp)
        employee_groups[emp_type]["total_salary"] += emp.rda_salary
        grand_total_salary += emp.rda_salary

    # --- Render template ---
    return render(request, "salary/monthly_salary_report.html", {
        "employee_groups": dict(employee_groups),
        "grand_total_salary": grand_total_salary,
        "print_time": today,
        "month_name": full_month_label,
        "project_name": project_name,
        "voucher": voucher,
        "project_id": project_id,   # always safe
    })



# @login_required
# def monthly_salary_generate(request):
#     project_input = request.GET.get("project")
#     month_input = request.GET.get("month")
#     today = now()
#     current_year = today.year

#     # Month filter
#     if month_input:
#         try:
#             month_datetime = datetime.strptime(month_input, "%B")
#             selected_month = month_datetime.strftime("%B")
#         except ValueError:
#             selected_month = today.strftime("%B")
#     else:
#         selected_month = today.strftime("%B")

#     # Project filter
#     project = None
#     project_name = None
#     if project_input:
#         project = get_object_or_404(ProjectFirstLevelName, id=project_input)
#         project_name = project.project_first_name

#     # Create or fetch voucher
#     voucher, created = SalaryVoucher.objects.get_or_create(
#         project=project,
#         month_name=f"{selected_month} {current_year}",
#         defaults={"approval_salary_status": "Pending"},
#     )

#     # Employees
#     employees = RdaEmployee.objects.filter(rda_active_status=True)
#     if project:
#         employees = employees.filter(project_name=project)

#     # Group employees by type + track totals
#     employee_groups = defaultdict(lambda: {"employees": [], "total_salary": Decimal(0)})
#     grand_total_salary = Decimal(0)

#     for emp in employees:
#         emp_type = emp.rda_emp_type or "Uncategorized"
#         employee_groups[emp_type]["employees"].append(emp)
#         employee_groups[emp_type]["total_salary"] += emp.rda_salary
#         grand_total_salary += emp.rda_salary

#     return render(request, "salary/monthly_salary_report.html", {
#         "employee_groups": dict(employee_groups),
#         "grand_total_salary": grand_total_salary,
#         "print_time": today,
#         "month_name": f"{selected_month} {current_year}",
#         "project_name": project_name,
#         "voucher": voucher,
#         "project_id": project.id if project else None,
#     })


# @login_required
# def approve_salary_generate(request, project_id, month_name):
#     from urllib.parse import unquote
#     month_name = unquote(month_name)

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     # Update or create SalaryVoucher
#     voucher, created = SalaryVoucher.objects.get_or_create(
#         project=project,
#         month_name=month_name,
#         defaults={
#             "approval_salary_status": "Approved",
#             "generate_date": timezone.now(),
#         }
#     )

#     if not created:
#         voucher.approval_salary_status = "Approved"
#         voucher.generate_date = timezone.now()
#         voucher.save()

#     return redirect("monthly_salary_generate") 






from urllib.parse import unquote
@login_required
def approve_salary_generate(request, project_id, month_name):
    # Decode URL-encoded month_name (e.g., "September%202025")
    month_name = unquote(month_name)

    # Get the project
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Update or create SalaryVoucher
    voucher, created = SalaryVoucher.objects.get_or_create(
        project=project,
        month_name=month_name,
        defaults={
            "approval_salary_status": "Approved",
            "generate_date": timezone.now(),
        }
    )

    if not created:
        # Already exists → just update status
        voucher.approval_salary_status = "Approved"
        voucher.generate_date = timezone.now()
        voucher.save()

    # Redirect back to monthly_salary_generate with the same project & month parameters
    return redirect(f"/dashboard/monthly-salary-report/?project={project_id}&month={month_name.split()[0]}")





# @login_required
# def monthly_salary_generate(request):
#     month_input = request.GET.get('month')
#     now = datetime.now()
#     current_year = now.year

#     if month_input:
#         try:
#             month_datetime = datetime.strptime(month_input, "%B")
#             selected_month = month_datetime.strftime("%B")
#         except ValueError:
#             selected_month = now.strftime("%B") 
#     else:
#         selected_month = now.strftime("%B")
#     employees = Employee.objects.filter(active_status=True).exclude(emp_name__iexact='admin')
#     total_salary = sum([emp.salary for emp in employees], Decimal(0))

#     print_time = now

#     return render(request, 'salary/monthly_salary_report.html', {
#         'employees': employees,
#         'total_salary': total_salary,
#         'print_time': print_time,
#         'month_name': f"{selected_month} {current_year}",
#     })



@login_required
def monthly_salary_check(request):
    month_input = request.GET.get('month')
    employee_input = request.GET.get('employee')
    now = datetime.now()
    current_year = now.year

    if month_input:
        try:
            month_datetime = datetime.strptime(month_input, "%B")
            selected_month = month_datetime.strftime("%B")
        except ValueError:
            selected_month = now.strftime("%B") 
    else:
        selected_month = now.strftime("%B")

    employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_name__iexact='admin')
    if employee_input:
        employees = employees.filter(id=employee_input)

    # Get all salary payments for that month
    salary_data = SalaryPayment.objects.filter(monthofsalary=selected_month)

    if employee_input:
        salary_data = salary_data.filter(employee__id=employee_input)

    # Map employee.id -> SalaryPayment object
    salary_map = {sp.employee.id: sp for sp in salary_data if sp.employee}

    # Annotate each employee with paid info and cheque number
    for emp in employees:
        sp = salary_map.get(emp.id)
        emp.salary_paid = sp.amount if sp else Decimal('0.00')
        emp.cheque_number = sp.cheque_number if sp and sp.cheque_number else ''

    total_salary = sum([emp.salary_paid for emp in employees], Decimal('0.00'))

    return render(request, 'salary/monthly_salary_check.html', {
        'employees': employees,
        'total_salary': total_salary,
        'print_time': now,
        'month_name': f"{selected_month} {current_year}",
    })
    
    
    

## new panel- employee adding---
# @login_required
# def add_employee(request):
#     if request.method == 'POST':
#         form = EmployeeForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('employee_list') 
#         else:
#             print(form.errors) 
#     else:
#         form = EmployeeForm()    
#     return render(request, 'employee/employee_form.html', {'form': form})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import EmployeeForm

# @login_required
# def add_employee(request):
#     if request.method == 'POST':
#         form = EmployeeForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('user_group_menu_assign') 
#         else:
#             print(form.errors) 
#     else:
#         form = EmployeeForm()     
#     return render(request, 'employee/employee_form.html', {'form': form})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import EmployeeForm


@login_required
def add_employee(request):

    if request.method == 'POST':

        form = EmployeeForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            try:
                employee = form.save()

                messages.success(
                    request,
                    'Employee created successfully.'
                )

                if form.cleaned_data.get('create_rda_employee'):
                    messages.success(
                        request,
                        'RDA Employee created successfully.'
                    )

                return redirect('user_group_menu_assign')

            except Exception as e:

                print("Employee creation error:", e)

                messages.error(
                    request,
                    'Employee creation failed.'
                )

        else:
            print(form.errors)

    else:
        form = EmployeeForm()

    return render(
        request,
        'employee/employee_form.html',
        {'form': form}
    )
    

# @login_required
# def employee_edit(request, pk):
#     employee = get_object_or_404(Employee, pk=pk)

#     if request.method == 'POST':
#         form = EmployeeAllowanceUpdateForm(request.POST, request.FILES, instance=employee)
#         if form.is_valid():
#             form.save()
#             return redirect('employee_list')
#     else:
#         form = EmployeeAllowanceUpdateForm(instance=employee)

#     return render(request, 'employee/employee_edit.html', {'form': form, 'employee': employee})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeAllowanceUpdateForm(
            request.POST,
            request.FILES,
            instance=employee
        )

        if form.is_valid():
            form.save()
            return redirect('employee_list')

    else:
        form = EmployeeAllowanceUpdateForm(
            instance=employee
        )

    return render(
        request,
        'employee/employee_edit.html',
        {
            'form': form,
            'employee': employee
        }
    )
    

@login_required
def employee_edit_user(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeePhotoUpdateForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()  # only updates the photo field
            return redirect('employee_list')
    else:
        form = EmployeePhotoUpdateForm(instance=employee)

    return render(request, 'employee/employee_edit_user.html', {
        'form': form,
        'employee': employee
    })
    
    
    
# ### ATTENDANCE ###
# @login_required
# def attendance_list(request):
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin').exclude(rda_emp_name__iexact='Admin')
#     today = date.today()
#     records = Attendance.objects.filter(date=today)
#     for r in records:
#         # Check late punch
#         r.is_late = r.check_in and r.check_in > time(10, 10)

#         # Check early leave
#         r.left_early = r.check_out and r.check_out < time(18, 1)

#         # Calculate duration
#         if r.check_in and r.check_out:
#             in_time = datetime.combine(datetime.today(), r.check_in)
#             out_time = datetime.combine(datetime.today(), r.check_out)
#             duration = out_time - in_time
#             hours, remainder = divmod(duration.total_seconds(), 3600)
#             minutes, _ = divmod(remainder, 60)
#             r.duration = f"{int(hours)}h {int(minutes)}m"
#         else:
#             r.duration = "-"
#     projects_firts=ProjectFirstLevelName.objects.all()
#     return render(request, 'attendance/attendance_list.html', {'records': records, 'employees':employees, 'projects_firts': projects_firts})



# @login_required
# def restaurant_attendance_list(request):
#     # employees = (
#     #     RdaEmployee.objects.filter(rda_active_status=True)
#     #     .exclude(rda_emp_type__iexact='admin')
#     #     .exclude(rda_emp_name__iexact='Admin')
#     # )
    
#     employees = (
#         RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name__project_first_name="The Galleria Restauent Cafe"
#         )
#         .exclude(rda_emp_type__iexact='admin')
#         .exclude(rda_emp_name__iexact='Admin')
#     )
    
#     selected_date_str = request.GET.get("date")
#     if selected_date_str:
#         try:
#             selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             selected_date = date.today()
#     else:
#         selected_date = date.today()

#     # Filter attendance records
#     records = Attendance.objects.filter(date=selected_date)
    
#     # records = Attendance.objects.filter(
#     #     date=selected_date,
#     #     employee__project_name__project_first_name="The Galleria Restauent Cafe" 
#     # )
    
#     for r in records:
#         r.is_late = r.check_in and r.check_in > time(10, 10)
        
#         r.left_early = r.check_out and r.check_out < time(18, 1)

#         # Work duration
#         if r.check_in and r.check_out:
#             in_time = datetime.combine(selected_date, r.check_in)
#             out_time = datetime.combine(selected_date, r.check_out)
#             duration = out_time - in_time
#             hours, remainder = divmod(duration.total_seconds(), 3600)
#             minutes, _ = divmod(remainder, 60)
#             r.duration = f"{int(hours)}h {int(minutes)}m"
#         else:
#             r.duration = "-"

#     projects_firts = ProjectFirstLevelName.objects.all()

#     return render(
#         request,
#         "attendance/restaurant_attendance_list.html",
#         {
#             "records": records,
#             "employees": employees,
#             "projects_firts": projects_firts,
#             "selected_date": selected_date.isoformat(),  # pass to template
#         },
#     )
    


# @login_required
# def attendance_create(request):
#     if request.method == "POST":
#         form = AttendanceForm(request.POST)
#         if form.is_valid():
#             form.save()
#     else:
#         form = AttendanceForm()
#         # Filter employee dropdown by project
#         form.fields['employee'].queryset = RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name__project_first_name="The Galleria Restauent Cafe"
#         ).exclude(rda_emp_type__iexact='admin').exclude(rda_emp_name__iexact='Admin')

#     return render(request, 'attendance/restaurant_attendance_create.html', {'form': form})


@login_required
def restaurant_attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'attendance/restaurant_attendance_create.html', {'form': form})
    
    

@login_required
def RestaurentAttendanceCheckoutUpdateView(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        form = AttendanceCheckoutForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('restaurant_attendance_list')  # replace with your attendance list URL name
    else:
        form = AttendanceCheckoutForm(instance=attendance)

    return render(request, 'attendance/restaurant_attendance_checkout_update.html', {'form': form, 'attendance': attendance})
    
    
       



# from datetime import datetime, date, time
# from django.utils import timezone
from hrm.models import RdaEmployee, Attendance as EmployeeAttendance
from tenant.models import Attendance as TenantAttendance

# @login_required
# def attendance_list(request):
#     # ------------------ Setup -------------------
#     # selected_date_str = request.GET.get("date")
#     # if selected_date_str:
#     #     try:
#     #         selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
#     #     except ValueError:
#     #         selected_date = date.today()
#     # else:
#     #     selected_date = date.today()
    
#     selected_date_str = request.GET.get("date")
#     today = date.today()
#     if selected_date_str:
#         try:
#             # user selected specific date
#             selected_date = datetime.strptime(
#                 selected_date_str, "%Y-%m-%d"
#             ).date()
    
#             # process only this date
#             start_date = selected_date
#             end_date = selected_date
    
#         except ValueError:
#             selected_date = today
#             start_date = today.replace(day=1)
#             end_date = today
    
#     else:
#         # no filter → whole month till today
#         selected_date = today
#         start_date = today.replace(day=1)
#         end_date = today


#     # ------------------ Get active employees -------------------
#     employees = (
#         RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name__project_first_name="BTP Office"
#         )
#         .exclude(rda_emp_type__iexact="admin")
#         .exclude(rda_emp_name__iexact="Admin")
#     )

#     # ------------------ Get all punches from tenant -------------------
#     punches = TenantAttendance.objects.filter(
#         punch_time__date=selected_date,
#         device_sn="SMR5253000001"
#     ).order_by("id")  # earliest first

#     # ------------------ Compare IDs -------------------
#     tenant_user_ids = list(punches.values_list("user_id", flat=True).distinct())
#     employee_ids = list(employees.values_list("id", flat=True))

#     matched_user_ids = sorted(set(tenant_user_ids) & set(employee_ids))
#     unmatched_user_ids = sorted(set(tenant_user_ids) - set(employee_ids))

#     # ------------------ Sync HRM attendance -------------------
#     for emp in employees:
#         emp_punches = punches.filter(user_id=emp.id)

#         if emp_punches.exists():
#             first_punch = timezone.localtime(emp_punches.first().punch_time)
#             last_punch = timezone.localtime(emp_punches.last().punch_time)

#             check_in = first_punch.time()
#             check_out = last_punch.time() if emp_punches.count() > 1 else time(0, 0)

#             hr_record, created = EmployeeAttendance.objects.get_or_create(
#                 employee=emp,
#                 date=selected_date,
#                 defaults={
#                     "check_in": check_in,
#                     "check_out": check_out,
#                     "att_status": "Present",
#                 },
#             )

#             if not created:
#                 hr_record.check_in = check_in
#                 hr_record.check_out = check_out
#                 hr_record.att_status = "Present"
#                 hr_record.save()
#         else:
#             # mark absent if not found
#             if not EmployeeAttendance.objects.filter(employee=emp, date=selected_date).exists():
#                 EmployeeAttendance.objects.create(
#                     employee=emp,
#                     date=selected_date,
#                     att_status="Absent",
#                 )

#     # ------------------ Build attendance list -------------------
#     records = EmployeeAttendance.objects.filter(date=selected_date)

#     for r in records:
#         r.is_late = r.check_in and r.check_in > datetime.strptime("10:00", "%H:%M").time()
#         r.left_early = r.check_out and r.check_out < datetime.strptime("19:30", "%H:%M").time()

#         if r.check_in and r.check_out and r.check_out != time(0, 0):
#             in_time = datetime.combine(selected_date, r.check_in)
#             out_time = datetime.combine(selected_date, r.check_out)
#             duration = out_time - in_time
#             hours, remainder = divmod(duration.total_seconds(), 3600)
#             minutes, _ = divmod(remainder, 60)
#             r.duration = f"{int(hours)}h {int(minutes)}m"
#         else:
#             r.duration = "-"

#     projects_first = ProjectFirstLevelName.objects.all()

#     # ------------------ Pass data to template -------------------
#     return render(
#         request,
#         "attendance/attendance_list.html",
#         {
#             "records": records,
#             "employees": employees,
#             "projects_firts": projects_first,
#             "selected_date": selected_date.isoformat(),
#             # 👇 debug info for display
#             "tenant_user_ids": tenant_user_ids,
#             "employee_ids": employee_ids,
#             "matched_user_ids": matched_user_ids,
#             "unmatched_user_ids": unmatched_user_ids,
#         },
#     )



## ok code is
from datetime import datetime, date, time, timedelta
from calendar import monthrange

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone



@login_required
def attendance_list(request):
    # ------------------ Setup -------------------
    selected_date_str = request.GET.get("date")
    filter_type = request.GET.get("filter_type", "single")

    today = date.today()

    if selected_date_str:
        try:
            selected_date = datetime.strptime(
                selected_date_str,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # Single Date Filter
    if filter_type == "single":
        start_date = selected_date
        end_date = selected_date

    # All Filter (Selected Date -> End of Month)
    else:
        start_date = selected_date

        last_day = monthrange(
            selected_date.year,
            selected_date.month
        )[1]

        end_date = selected_date.replace(day=last_day)

    # ------------------ Get active employees -------------------
    employees = (
        RdaEmployee.objects.filter(
            rda_active_status=True,
            project_name__project_first_name="BTP Office"
        )
        .exclude(rda_emp_type__iexact="admin")
        .exclude(rda_emp_name__iexact="Admin")
    )

    # ------------------ Get all punches -------------------
    punches = TenantAttendance.objects.filter(
        punch_time__date__range=[start_date, end_date],
        device_sn="SMR5253000001"
    ).order_by("punch_time")

    # ------------------ Compare IDs -------------------
    tenant_user_ids = list(
        punches.values_list("user_id", flat=True).distinct()
    )

    employee_ids = list(
        employees.values_list("id", flat=True)
    )

    matched_user_ids = sorted(
        set(tenant_user_ids) & set(employee_ids)
    )

    unmatched_user_ids = sorted(
        set(tenant_user_ids) - set(employee_ids)
    )

    # ------------------ Sync Attendance -------------------
    current_date = start_date

    while current_date <= end_date:

        day_punches = punches.filter(
            punch_time__date=current_date
        )

        for emp in employees:

            emp_punches = day_punches.filter(
                user_id=emp.id
            )

            if emp_punches.exists():

                first_punch = timezone.localtime(
                    emp_punches.first().punch_time
                )

                last_punch = timezone.localtime(
                    emp_punches.last().punch_time
                )

                check_in = first_punch.time()

                if emp_punches.count() > 1:
                    check_out = last_punch.time()
                else:
                    check_out = time(0, 0)

                hr_record, created = EmployeeAttendance.objects.get_or_create(
                    employee=emp,
                    date=current_date,
                    defaults={
                        "check_in": check_in,
                        "check_out": check_out,
                        "att_status": "Present",
                    },
                )

                if not created:
                    hr_record.check_in = check_in
                    hr_record.check_out = check_out
                    hr_record.att_status = "Present"
                    hr_record.save()

            else:

                if not EmployeeAttendance.objects.filter(
                    employee=emp,
                    date=current_date
                ).exists():

                    EmployeeAttendance.objects.create(
                        employee=emp,
                        date=current_date,
                        att_status="Absent",
                    )

        current_date += timedelta(days=1)

    # ------------------ Attendance List -------------------
    # records = EmployeeAttendance.objects.filter(
    #     date__range=[start_date, end_date]
    # ).order_by(
    #     "date",
    #     "employee__rda_emp_name"
    # )
    records = (
        EmployeeAttendance.objects.filter(
            date__range=[start_date, end_date],
            employee__in=employees,               # ← restrict to active + BTP Office
            employee__rda_active_status=True,     # ← belt-and-suspenders safety check
        )
        .select_related("employee")
        .order_by("date", "employee__rda_emp_name")
    )

    late_time = datetime.strptime(
        "10:30",
        "%H:%M"
    ).time()

    early_time = datetime.strptime(
        "19:30",
        "%H:%M"
    ).time()

    for r in records:

        r.is_late = (
            r.check_in
            and r.check_in > late_time
        )

        r.left_early = (
            r.check_out
            and r.check_out != time(0, 0)
            and r.check_out < early_time
        )

        if (
            r.check_in
            and r.check_out
            and r.check_out != time(0, 0)
        ):

            in_time = datetime.combine(
                r.date,
                r.check_in
            )

            out_time = datetime.combine(
                r.date,
                r.check_out
            )

            duration = out_time - in_time

            hours, remainder = divmod(
                duration.total_seconds(),
                3600
            )

            minutes, _ = divmod(
                remainder,
                60
            )

            r.duration = f"{int(hours)}h {int(minutes)}m"

        else:
            r.duration = "-"

    projects_first = ProjectFirstLevelName.objects.all()

    # ------------------ Render -------------------
    return render(
        request,
        "attendance/attendance_list.html",
        {
            "records": records,
            "employees": employees,
            "projects_firts": projects_first,
            "selected_date": selected_date.isoformat(),
            "filter_type": filter_type,

            # Debug
            "tenant_user_ids": tenant_user_ids,
            "employee_ids": employee_ids,
            "matched_user_ids": matched_user_ids,
            "unmatched_user_ids": unmatched_user_ids,

            # Optional
            "start_date": start_date,
            "end_date": end_date,
        },
    )







@login_required
def AttendanceCheckoutUpdateView(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        form = AttendanceCheckoutForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')  # replace with your attendance list URL name
    else:
        form = AttendanceCheckoutForm(instance=attendance)

    return render(request, 'attendance/attendance_checkout_update.html', {'form': form, 'attendance': attendance})
    
    
    

@login_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'attendance/attendance_form.html', {'form': form})




from calendar import monthcalendar, FRIDAY

@login_required
def attendance_add_holiday(request):
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
        employees = RdaEmployee.objects.filter(
            rda_active_status=True
        ).exclude(
            project_name__project_first_name__in=[
                'The Galleria Restaurant Cafe',
                'The Galleria Restaurant'
            ]
        )

        for emp in employees:
            for friday in fridays:
                qs = Attendance.objects.filter(
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
                    Attendance.objects.create(
                        employee=emp,
                        date=friday,
                        att_status='Off Day',
                        check_in=None,
                        check_out=None
                    )

        return redirect('attendance_list')

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

    return render(request, 'attendance/add_holiday.html', {
        'fridays': fridays,
        'selected_month': selected_month
    })



@login_required
def attendance_upload_csv(request):
    if request.method == 'POST':
        form = AttendanceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if not file.name.endswith('.csv'):
                messages.error(request, 'Only CSV files are supported.')
                return redirect('attendance_upload_csv')

            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            next(reader)  # Skip header

            for row in reader:
                try:
                    employee_id = int(row[0])  # or use unique field like employee code
                    employee = Employee.objects.get(id=employee_id)
                    date = row[1]
                    check_in = row[2] if row[2] else None
                    check_out = row[3] if row[3] else None

                    Attendance.objects.create(
                        employee=employee,
                        date=date,
                        check_in=check_in,
                        check_out=check_out
                    )
                except Exception as e:
                    messages.warning(request, f'Error on row: {row} - {e}')

            messages.success(request, 'CSV uploaded successfully.')
            return redirect('attendance_list')
    else:
        form = AttendanceUploadForm()

    return render(request, 'attendance/attendance_upload.html', {'form': form})
    

@login_required
def download_sample_attendance_csv(request):
    # Create HTTP response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_sample.csv"'

    writer = csv.writer(response)
    # Header row
    writer.writerow(['id', 'date', 'check_in', 'check_out'])

    # All active employees
    sample_employees = Employee.objects.filter(active_status=True)
    for emp in sample_employees:
        writer.writerow([emp.id, '2025-07-13', '09:00:00', '17:00:00'])

    return response



# @login_required
# def generate_attendance_records(request):
#     month_name = request.GET.get('month')  # e.g., "July"
#     selected_date_str = request.GET.get('date')  # e.g., "2025-07-25"

#     if not month_name:
#         messages.error(request, "Month is required.")
#         return redirect('attendance_list')

#     # Convert month name to month number
#     try:
#         month_number = datetime.strptime(month_name, "%B").month
#     except ValueError:
#         messages.error(request, "Invalid month name.")
#         return redirect('attendance_list')

#     today = timezone.localdate()
#     current_month = today.month
#     current_year = today.year

#     # Determine year
#     year = today.year
#     selected_date = None
#     if selected_date_str:
#         try:
#             selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
#             year = selected_date.year
#         except ValueError:
#             messages.error(request, "Invalid date format.")
#             return redirect('attendance_list')

#     # Case 1: Specific date selected → generate only for that date
#     if selected_date:
#         start_date = end_date = selected_date

#     # Case 2: Only month selected
#     else:
#         start_date = date(year, month_number, 1)

#         # If selected month is current month → end date = today
#         if month_number == current_month and year == current_year:
#             end_date = today
#         else:
#             # Use full month if it's not current
#             last_day = monthrange(year, month_number)[1]
#             end_date = date(year, month_number, last_day)

#     # Get all eligible employees
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_name__iexact='Admin')

#     # Generate attendance entries
#     created_count = 0
#     for emp in employees:
#         for single_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)):
#             if not Attendance.objects.filter(employee=emp, date=single_date).exists():
#                 Attendance.objects.create(
#                     employee=emp,
#                     date=single_date,
#                     check_in=None,
#                     check_out=None,
#                     att_status='Off Day'
#                 )
#                 created_count += 1

#     messages.success(request, f"{created_count} attendance records created for {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}.")
#     return redirect('attendance_list')
    


@login_required
def generate_attendance_records(request):

    month_number = request.GET.get('month')  # 1–12
    selected_date_str = request.GET.get('date')  # YYYY-MM-DD

    if not selected_date_str:
        messages.error(request, "Please select a date for Special Holiday.")
        return redirect('attendance_list')

    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('attendance_list')

    # Fixed special holiday timing
    special_check_in = time(10, 0, 0)   # 10:00:00 AM
    special_check_out = time(19, 30, 0) # 07:30:00 PM

    # Get active employees
    employees = RdaEmployee.objects.filter(
        rda_active_status=True
    ).exclude(
        rda_emp_name__iexact='Admin'
    )

    created_count = 0
    updated_count = 0

    for emp in employees:

        attendance, created = Attendance.objects.get_or_create(
            employee=emp,
            date=selected_date,
            defaults={
                'check_in': special_check_in,
                'check_out': special_check_out,
                'att_status': 'Present'
            }
        )

        if created:
            created_count += 1
        else:
            # If already exists → update it
            attendance.check_in = special_check_in
            attendance.check_out = special_check_out
            attendance.att_status = 'Present'
            attendance.save()
            updated_count += 1

    messages.success(
        request,
        f"Special Holiday attendance generated for {selected_date.strftime('%d %b %Y')}. "
        f"{created_count} created, {updated_count} updated."
    )

    return redirect('attendance_list')
    
    
# @login_required
# def attendance_edit(request, pk):
#     record = get_object_or_404(Attendance, pk=pk)
#     if request.method == 'POST':
#         form = AttendanceForm(request.POST, instance=record)
#         if form.is_valid():
#             form.save()
#             return redirect('attendance_list')
#     else:
#         form = AttendanceForm(instance=record)
#     return render(request, 'attendance/attendance_form.html', {'form': form})



@login_required
def attendance_edit(request, pk):
    record = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save()
            selected_date = updated_record.date.strftime("%Y-%m-%d")
            return redirect(f"/dashboard/attendance/?date={selected_date}")
    else:
        form = AttendanceForm(instance=record)

    return render(request, 'attendance/attendance_edit.html', {'form': form})


    

@login_required
def attendance_delete(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('attendance_list')
    return render(request, 'attendance/attendance_confirm_delete.html', {'record': record})





@login_required
def employee_attendance_summary(request):
    project_id = request.GET.get('project_id')
    employee_id = request.GET.get('employee_id')  # optional
    year_id = request.GET.get('year_id')
    month_id = request.GET.get('month_id')
    date = request.GET.get('date')  # optional YYYY-MM-DD

    # Validate required inputs (employee_id is optional)
    if not (project_id and year_id and month_id):
        return HttpResponse("Missing project_id, year_id or month_id.", status=400)

    try:
        project_id = int(project_id)
        year = int(year_id)
        month = int(month_id)
        employee_id = int(employee_id) if employee_id else None
    except ValueError:
        return HttpResponse("Invalid project_id, year_id or month_id.", status=400)

    # Ensure project exists
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Base query for project and month
    attendance_records = Attendance.objects.filter(
        date__year=year,
        date__month=month,
        employee__project_name=project
    ).order_by('date')

    employee = None
    if employee_id:  # If employee_id is provided
        employee = get_object_or_404(RdaEmployee, id=employee_id, project_name=project)
        attendance_records = attendance_records.filter(employee=employee)

    # If specific date provided, filter
    selected_date = None
    if date:
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            attendance_records = attendance_records.filter(date=selected_date)
        except ValueError:
            return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

    # ---- Add custom fields (late, early, duration) ----
    for r in attendance_records:
        # Late check (after 10:10 AM)
        r.is_late = bool(r.check_in and r.check_in > time(10, 10))

        # Early leave check (before 6:01 PM)
        r.left_early = bool(r.check_out and r.check_out < time(18, 1))

        # Work duration
        if r.check_in and r.check_out:
            work_date = r.date  # actual record date
            in_time = datetime.combine(work_date, r.check_in)
            out_time = datetime.combine(work_date, r.check_out)
            duration = out_time - in_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            r.duration = f"{int(hours)}h {int(minutes)}m"
        else:
            r.duration = "-"

    context = {
        'project': project,
        'employee': employee,   # None if all employees
        'attendance_records': attendance_records,
        'year': year,
        'month': month,
        'specific_date': date if date else None,
        'print_time': now(),
    }
    return render(request, "attendance/attendance_summary.html", context)




@login_required
def payroll_list(request):
    project_id = request.GET.get('project_id')
    today = datetime.today()
    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    # Selected month/year
    month_input = request.GET.get('month', default_month_str)
    year_input = int(request.GET.get('year', default_year))

    # Parse selected month
    selected_month_dt = datetime.strptime(month_input, "%Y-%m")
    selected_month = selected_month_dt.strftime('%B %Y')  # e.g. "September 2025"

    # Month date range
    start_date = selected_month_dt.replace(day=1).date()
    end_day = monthrange(year_input, selected_month_dt.month)[1]
    end_date = selected_month_dt.replace(day=end_day).date()
    days_in_month = end_day

    payroll_data = []

    # Employees
    #employees = RdaEmployee.objects.filter(rda_active_status=True)
    employees = RdaEmployee.objects.filter(
        rda_active_status=True,
        project_name__project_first_name="BTP Office"
    )
    if project_id:
        try:
            employees = employees.filter(project_name_id=int(project_id))
        except ValueError:
            pass

    # Totals
    total_basic_salary = Decimal(0)
    total_allowances = Decimal(0)
    total_deductions = Decimal(0)
    total_loans = Decimal(0)
    total_net_salary = Decimal(0)

    for emp in employees:
        rda_salary = Decimal(emp.rda_salary or 0)

        # Allowances
        allowances = Allowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # Attendance
        present_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Present'
        ).count()

        leave_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Absent'
        ).count()

        absent_days = days_in_month - (present_days + leave_days)

        # Salary calculation
        daily_salary = (rda_salary / Decimal(days_in_month)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        basic_salary = (daily_salary * Decimal(present_days + leave_days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Advance deductions
        deductions = AdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # 🔹 Loan Payments (with start_month, end_month, and month_name validation)
        loans_qs = LoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        loans = Decimal(0)
        for loan in loans_qs:
            if loan.month_name:
                # check if current payroll month (e.g. "September 2025") is in loan.month_name text
                if selected_month in loan.month_name:
                    loans += loan.deduction_amount

        # Net Salary
        net_salary = (basic_salary + allowances - deductions - loans).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Save payroll in DB
        Payroll.objects.update_or_create(
            employee=emp,
            month=selected_month,
            year=year_input,
            defaults={
                'basic_salary': basic_salary,
                'allowances': allowances,
                'deductions': deductions + loans,  # optional: include loans in deductions
                'net_salary': net_salary
            }
        )

        # Payroll row data
        payroll_data.append({
            'employee': emp,
            'days_in_month': days_in_month,
            'working_days': present_days + leave_days,
            'absent_days': absent_days,
            'basic_salary': basic_salary,
            'allowances': allowances,
            'deductions': deductions,
            'loans': loans,
            'net_salary': net_salary,
        })

        # Totals
        total_basic_salary += basic_salary
        total_allowances += allowances
        total_deductions += deductions
        total_loans += loans
        total_net_salary += net_salary

    projects_first = ProjectFirstLevelName.objects.all()
    selected_project_obj = ProjectFirstLevelName.objects.filter(id=project_id).first() if project_id else None

    return render(request, 'payroll/payroll_list.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'default_month': default_month_str,
        'default_year': default_year,
        'employees': employees,
        'projects_first': projects_first,
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_deductions': total_deductions,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
        'selected_project': selected_project_obj,
    })

    
    




# @login_required
# def payroll_print(request):
#     today = datetime.today()
#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     project_id = request.GET.get('project_id')

#     # Parse year
#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     # Parse month
#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     selected_month = selected_month_dt.strftime('%B %Y')  # e.g., "September 2025"
#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()
#     days_in_month = end_day

#     payroll_data = []

#     # Filter employees
#     if project_id and project_id.isdigit():
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name_id=int(project_id)
#         ).exclude(rda_emp_name__iexact='admin')
#     else:
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True
#         ).exclude(rda_emp_name__iexact='admin')

#     for emp in employees:
#         rda_salary = emp.rda_salary or 0

#         # Total allowances
#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         # Attendance breakdown (distinct by date to avoid duplicates)
#         present_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Present'
#         ).values('date').distinct().count()

#         leave_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Leave'
#         ).values('date').distinct().count()

#         off_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Off Day'
#         ).values('date').distinct().count()

#         absent_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Absent'
#         ).values('date').distinct().count()

#         # ✅ Working days = total days - absence (Present + Leave + Off Day all paid)
#         attendance_days = days_in_month - absent_days

#         # Daily & basic salary
        
#         # daily_salary = (Decimal(rda_salary) / Decimal(days_in_month)).quantize(
#         #     Decimal('0.01'), rounding=ROUND_HALF_UP) if rda_salary else 0
#         # basic_salary = round(daily_salary * attendance_days, 2)
        
#         daily_salary = Decimal(rda_salary) / Decimal(days_in_month) if rda_salary else Decimal('0')
#         basic_salary = (daily_salary * attendance_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

#         # Advance deductions
#         total_advance = AdvancePayment.objects.filter(
#             employee=emp, date__range=(start_date, end_date), status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         # LoanPayment deductions for current month
#         loans_qs = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal(0)
#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 loan_amount = loan.deduction_amount or Decimal(0)
#                 total_loan_deduction += loan_amount

#         # Net salary
#         net_salary = round(basic_salary + allowances - total_advance - total_loan_deduction, 2)

#         # Update or create Payroll record
#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances,
#                 'deductions': total_advance + total_loan_deduction,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'days_in_month': days_in_month,
#             'present_days': present_days,
#             'leave_days': leave_days,
#             'off_days': off_days,
#             'absent_days': absent_days,
#             'working_days': attendance_days,
#             'basic_salary': basic_salary,
#             'allowances': allowances,
#             'deductions': total_advance,
#             'loan_amount': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     # Totals
#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['deductions'] for item in payroll_data)
#     total_loans = sum(item['loan_amount'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     selected_project = None
#     if project_id and project_id.isdigit():
#         selected_project = ProjectFirstLevelName.objects.filter(id=int(project_id)).first()

#     return render(request, 'payroll/payroll_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#         'selected_project': selected_project
#     })



## ok code ---- 

# from django.db.models import Sum
# from django.utils import timezone
# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP

# @login_required
# def payroll_print(request):
#     today = datetime.today()
#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     project_id = request.GET.get('project_id')

#     # Parse year
#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     # Parse month
#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     selected_month = selected_month_dt.strftime('%B %Y')
#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()
#     days_in_month = end_day

#     payroll_data = []

#     # Employees
#     if project_id and project_id.isdigit():
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name_id=int(project_id)
#         ).exclude(rda_emp_name__iexact='admin')
#     else:
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True
#         ).exclude(rda_emp_name__iexact='admin')

#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)

#         # Allowances
#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # Attendance counts
#         present_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Present'
#         ).values('date').distinct().count()

#         leave_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Leave'
#         ).values('date').distinct().count()

#         off_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Off Day'
#         ).values('date').distinct().count()

#         absent_days = Attendance.objects.filter(
#             employee=emp, date__range=(start_date, end_date), att_status='Absent'
#         ).values('date').distinct().count()

#         # Default working days
#         working_days = days_in_month - absent_days

#         # Salary calculation
#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')
#         basic_salary = (daily_salary * working_days).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         # ============================
#         # 🔴 MANUAL OVERRIDE (ONLY ID 35, 36)
#         # ============================
#         # if emp.id in [4,6,8,10,13, 17, 34, 35, 36]:
#         #     present_days = 26
#         #     off_days = 4
#         #     absent_days = 0
#         #     leave_days = 0
#         #     working_days = 30
#         #     basic_salary = rda_salary.quantize(
#         #         Decimal('0.01'), rounding=ROUND_HALF_UP
#         #     )
#       # -------------------------------------------------------
#         # manual_ids = [4, 6, 8, 10, 13, 17, 34, 35, 36]
#         # absent_one_day_ids = [4, 34, 36]
        
#         # if emp.id in manual_ids:
#         #     off_days = 4
#         #     leave_days = 0
#         #     working_days = 30
        
#         #     if emp.id in absent_one_day_ids:
#         #         absent_days = 1
#         #         present_days = 25
#         #     else:
#         #         absent_days = 0
#         #         present_days = 26
        
#         #     # Full salary (no deduction)
#         #     basic_salary = Decimal(rda_salary).quantize(
#         #         Decimal('0.01'), rounding=ROUND_HALF_UP
#         #     )
        
        
#         # ---------------------------------
#         # ============================
#         # 🔴 MANUAL OVERRIDE
#         # ============================
#         manual_ids = []
#         absent_one_day_ids = [0]
        
#         if emp.id in manual_ids:
#             off_days = 4
#             leave_days = 0
        
#             if emp.id in absent_one_day_ids:
#                 absent_days = 1
#                 present_days = 25
#                 working_days = 29   # ✅ PAYABLE DAYS
#             else:
#                 absent_days = 0
#                 present_days = 26
#                 working_days = 30   # ✅ PAYABLE DAYS
        
#             # Daily salary
#             daily_salary = Decimal(rda_salary) / Decimal(days_in_month)
        
#             # Payable salary
#             basic_salary = (daily_salary * working_days).quantize(
#                 Decimal('0.01'), rounding=ROUND_HALF_UP
#             )


#         # Advance deduction
#         total_advance = AdvancePayment.objects.filter(
#             employee=emp, date__range=(start_date, end_date), status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # Loan deduction
#         loans_qs = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal('0')
#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal('0')

#         # Net salary
#         net_salary = (basic_salary + allowances - total_advance - total_loan_deduction).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         # Save payroll
#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances,
#                 'deductions': total_advance + total_loan_deduction,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'days_in_month': days_in_month,
#             'present_days': present_days,
#             'leave_days': leave_days,
#             'off_days': off_days,
#             'absent_days': absent_days,
#             'working_days': working_days,
#             'basic_salary': basic_salary,
#             'allowances': allowances,
#             'deductions': total_advance,
#             'loan_amount': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     # Totals
#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['deductions'] for item in payroll_data)
#     total_loans = sum(item['loan_amount'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     selected_project = None
#     if project_id and project_id.isdigit():
#         selected_project = ProjectFirstLevelName.objects.filter(id=int(project_id)).first()
    
    
#     total_rda_salary = sum(item['employee'].rda_salary for item in payroll_data)

#     return render(request, 'payroll/payroll_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#         'selected_project': selected_project,
#         'total_rda_salary': total_rda_salary
#     })




## will be chnage code ---

from datetime import datetime, timedelta
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone


@login_required
def payroll_print(request):

    today = datetime.today()

    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    month_input = request.GET.get('month', default_month_str)
    year_input_str = request.GET.get('year', str(default_year))
    project_id = request.GET.get('project_id')

    # ======================
    # Parse Year
    # ======================
    try:
        year_input = int(year_input_str)
    except ValueError:
        year_input = default_year

    # ======================
    # Parse Month
    # ======================
    try:
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")
    except ValueError:
        selected_month_dt = datetime(today.year, today.month, 1)

    selected_month = selected_month_dt.strftime('%B %Y')

    start_date = selected_month_dt.replace(day=1).date()
    end_day = monthrange(year_input, selected_month_dt.month)[1]
    end_date = selected_month_dt.replace(day=end_day).date()
    days_in_month = end_day

    payroll_data = []

    # ======================
    # EMPLOYEES FILTER
    # ======================
    if project_id and project_id.isdigit():
        employees = RdaEmployee.objects.filter(
            rda_active_status=True,
            project_name_id=int(project_id)
        ).exclude(rda_emp_name__iexact='admin')
    else:
        employees = RdaEmployee.objects.filter(
            rda_active_status=True
        ).exclude(rda_emp_name__iexact='admin')

    # ======================
    # TOTAL VARIABLES (FIXED)
    # ======================
    total_rda_salary = Decimal('0')
    total_basic_salary = Decimal('0')
    total_allowances = Decimal('0')
    total_advance = Decimal('0')
    total_loans = Decimal('0')
    total_net_salary = Decimal('0')

    # ======================
    # MAIN LOOP
    # ======================
    for emp in employees:

        rda_salary = Decimal(emp.rda_salary or 0)

        # ======================
        # MANUAL SALARY OVERRIDE FOR EMPLOYEE ID 44
        # ======================
        if emp.id == 44:
            rda_salary = Decimal('5000.00')

        if emp.id == 42:
            present_days = 21
            leave_days = 0
            off_days = 0
            absent_days = days_in_month - 21
            working_days = 21
        else:
            present_days = Attendance.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                att_status='Present'
            ).values('date').distinct().count()

            leave_days = Attendance.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                att_status='Leave'
            ).values('date').distinct().count()

            off_days = Attendance.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                att_status='Off Day'
            ).values('date').distinct().count()

            absent_days = Attendance.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                att_status='Absent'
            ).values('date').distinct().count()

            working_days = days_in_month - absent_days

        daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')

        basic_salary = (daily_salary * working_days).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # Additional hard override for fixed gross/basic if full month or specific fixed amount is needed
        if emp.id == 44:
            basic_salary = Decimal('5000.00')
        # elif emp.id == 42:
        #     # Force basic salary directly to 5000.00 regardless of attendance calculation
        #     basic_salary = Decimal('5000.00')

        # ======================
        # ALLOWANCES
        # ======================
        allowances = Allowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # ======================
        # ADVANCE
        # ======================
        advance_amount = AdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # ======================
        # LOANS
        # ======================
        loans_qs = LoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        loan_amount = Decimal('0')

        for loan in loans_qs:
            if loan.month_name and selected_month in loan.month_name:
                loan_amount += loan.deduction_amount or Decimal('0')

        # ======================
        # NET SALARY
        # ======================
        net_salary = (
            basic_salary +
            allowances -
            advance_amount -
            loan_amount
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # ======================
        # SAVE PAYROLL
        # ======================
        Payroll.objects.update_or_create(
            employee=emp,
            month=selected_month,
            year=year_input,
            defaults={
                'basic_salary': basic_salary + allowances,
                'allowances': allowances,
                'deductions': advance_amount + loan_amount,
                'net_salary': net_salary
            }
        )

        # ======================
        # APPEND DATA
        # ======================
        payroll_data.append({
            'employee': emp,
            'days_in_month': days_in_month,
            'present_days': present_days,
            'leave_days': leave_days,
            'off_days': off_days,
            'absent_days': absent_days,
            'working_days': working_days,
            'basic_salary': basic_salary + allowances,
            'allowances': allowances,
            'advance_amount': advance_amount,
            'loan_amount': loan_amount,
            'net_salary': net_salary,
        })

        # ======================
        # TOTALS (SAFE ADD)
        # ======================
        total_rda_salary += rda_salary
        total_basic_salary += basic_salary + allowances
        total_allowances += allowances
        total_advance += advance_amount
        total_loans += loan_amount
        total_net_salary += net_salary

    # ======================
    # PROJECT FILTER
    # ======================
    selected_project = None
    if project_id and project_id.isdigit():
        selected_project = ProjectFirstLevelName.objects.filter(
            id=int(project_id)
        ).first()

    # ======================
    # RETURN
    # ======================
    return render(request, 'payroll/payroll_print.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'default_month': default_month_str,
        'default_year': default_year,

        # TOTALS
        'total_rda_salary': total_rda_salary,
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_advance': total_advance,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,

        'print_time': timezone.now(),
        'selected_project': selected_project,
    })


# @login_required
# def payroll_print_manual(request):

#     today = datetime.today()

#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     project_id = request.GET.get('project_id')

#     # -------------------------
#     # Manual overrides (POST)
#     # -------------------------
#     manual_payable_days = {}
#     manual_month_name = request.POST.get("manual_month_name")

#     if request.method == "POST":
#         for key, value in request.POST.items():
#             if key.startswith("payable_days_"):
#                 emp_id = key.replace("payable_days_", "")
#                 try:
#                     manual_payable_days[int(emp_id)] = int(value)
#                 except:
#                     pass

#     # Parse year
#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     # Parse month
#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     # -------------------------
#     # MONTH NAME (MANUAL SUPPORT)
#     # -------------------------
#     if manual_month_name:
#         selected_month = manual_month_name
#     else:
#         selected_month = selected_month_dt.strftime('%B %Y')

#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()
#     days_in_month = end_day

#     payroll_data = []

#     # Employees Filter
#     if project_id and project_id.isdigit():
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True,
#             project_name_id=int(project_id)
#         ).exclude(rda_emp_name__iexact='admin')
#     else:
#         employees = RdaEmployee.objects.filter(
#             rda_active_status=True
#         ).exclude(rda_emp_name__iexact='admin')

#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)

#         present_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Present'
#         ).values('date').distinct().count()

#         leave_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Leave'
#         ).values('date').distinct().count()

#         off_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Off Day'
#         ).values('date').distinct().count()

#         absent_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Absent'
#         ).values('date').distinct().count()

#         # -------------------------
#         # PAYABLE DAYS (MANUAL OVERRIDE)
#         # -------------------------
#         default_working_days = days_in_month - absent_days
#         working_days = manual_payable_days.get(emp.id, default_working_days)

#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')

#         basic_salary = (daily_salary * working_days).quantize(
#             Decimal('0.01'),
#             rounding=ROUND_HALF_UP
#         )

#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         total_advance = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         loans_qs = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal('0')
#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal('0')

#         net_salary = (
#             basic_salary +
#             allowances -
#             total_advance -
#             total_loan_deduction
#         ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary + allowances,
#                 'allowances': allowances,
#                 'deductions': total_advance + total_loan_deduction,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'days_in_month': days_in_month,
#             'present_days': present_days,
#             'leave_days': leave_days,
#             'off_days': off_days,
#             'absent_days': absent_days,
#             'working_days': working_days,
#             'basic_salary': basic_salary + allowances,
#             'allowances': allowances,
#             'advance_amount': total_advance,
#             'loan_amount': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['advance_amount'] for item in payroll_data)
#     total_loans = sum(item['loan_amount'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     total_rda_salary = sum(
#         Decimal(item['employee'].rda_salary or 0)
#         for item in payroll_data
#     )

#     selected_project = None
#     if project_id and project_id.isdigit():
#         selected_project = ProjectFirstLevelName.objects.filter(
#             id=int(project_id)
#         ).first()

#     return render(request, 'payroll/payroll_print_manual.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#         'selected_project': selected_project,
#         'total_rda_salary': total_rda_salary
#     })
    
    
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

@login_required
def payroll_print_manual(request):

    today = datetime.today()

    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    month_input = request.GET.get('month', default_month_str)
    year_input_str = request.GET.get('year', str(default_year))
    project_id = request.GET.get('project_id')

    manual_payable_days = {}
    manual_month_name = request.POST.get("manual_month_name")

    # -------------------------
    # MANUAL INPUTS
    # -------------------------
    manual_loan_status = {}
    manual_advance_status = {}

    if request.method == "POST":

        for key, value in request.POST.items():

            if key.startswith("payable_days_"):
                emp_id = key.replace("payable_days_", "")

                try:
                    manual_payable_days[int(emp_id)] = int(value)
                except:
                    pass

            # Loan status
            if key.startswith("loan_status_"):
                emp_id = key.replace("loan_status_", "")
                manual_loan_status[int(emp_id)] = value

            # Advance status
            if key.startswith("advance_status_"):
                emp_id = key.replace("advance_status_", "")
                manual_advance_status[int(emp_id)] = value

    # -------------------------
    # YEAR
    # -------------------------
    try:
        year_input = int(year_input_str)
    except ValueError:
        year_input = default_year

    # -------------------------
    # MONTH
    # -------------------------
    try:
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")
    except ValueError:
        selected_month_dt = datetime(today.year, today.month, 1)

    if manual_month_name:
        selected_month = manual_month_name
    else:
        selected_month = selected_month_dt.strftime('%B %Y')

    start_date = selected_month_dt.replace(day=1).date()

    end_day = monthrange(year_input, selected_month_dt.month)[1]

    end_date = selected_month_dt.replace(day=end_day).date()

    days_in_month = end_day

    payroll_data = []

    # -------------------------
    # EMPLOYEE FILTER
    # -------------------------
    if project_id and project_id.isdigit():

        employees = RdaEmployee.objects.filter(
            rda_active_status=True,
            project_name_id=int(project_id)
        ).exclude(rda_emp_name__iexact='admin')

    else:

        employees = RdaEmployee.objects.filter(
            rda_active_status=True
        ).exclude(rda_emp_name__iexact='admin')

    # -------------------------
    # LOOP
    # -------------------------
    for emp in employees:

        rda_salary = Decimal(emp.rda_salary or 0)

        present_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Present'
        ).values('date').distinct().count()

        leave_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Leave'
        ).values('date').distinct().count()

        off_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Off Day'
        ).values('date').distinct().count()

        absent_days = Attendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Absent'
        ).values('date').distinct().count()

        # -------------------------
        # PAYABLE DAYS
        # -------------------------
        default_working_days = days_in_month - absent_days

        working_days = manual_payable_days.get(
            emp.id,
            default_working_days
        )

        daily_salary = (
            rda_salary / Decimal(days_in_month)
        ) if rda_salary else Decimal('0')

        # BASIC
        basic_salary = (
            daily_salary * Decimal(working_days)
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # ALLOWANCE
        allowances = Allowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # ADVANCE
        total_advance = AdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # LOAN
        loans_qs = LoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        total_loan_deduction = Decimal('0')

        for loan in loans_qs:

            if loan.month_name and selected_month in loan.month_name:

                total_loan_deduction += (
                    loan.deduction_amount or Decimal('0')
                )

        # -------------------------
        # ACTIVE / INACTIVE
        # -------------------------
        loan_status = manual_loan_status.get(emp.id, "active")

        if loan_status == "inactive":
            total_loan_deduction = Decimal('0')

        advance_status = manual_advance_status.get(emp.id, "active")

        if advance_status == "inactive":
            total_advance = Decimal('0')

        # -------------------------
        # GROSS
        # -------------------------
        gross_salary = (
            basic_salary + allowances
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # -------------------------
        # NET
        # -------------------------
        net_salary = (
            gross_salary -
            total_advance -
            total_loan_deduction
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        payroll_data.append({
            'employee': emp,
            'days_in_month': days_in_month,
            'present_days': present_days,
            'leave_days': leave_days,
            'off_days': off_days,
            'absent_days': absent_days,
            'working_days': working_days,
            'basic_salary': basic_salary,
            'gross_salary': gross_salary,
            'allowances': allowances,
            'advance_amount': total_advance,
            'loan_amount': total_loan_deduction,
            'net_salary': net_salary,
            'loan_status': loan_status,
            'advance_status': advance_status,
        })

    # -------------------------
    # TOTALS
    # -------------------------
    total_basic_salary = sum(
        item['basic_salary']
        for item in payroll_data
    )

    total_allowances = sum(
        item['allowances']
        for item in payroll_data
    )

    total_gross_salary = sum(
        item['gross_salary']
        for item in payroll_data
    )

    total_advance = sum(
        item['advance_amount']
        for item in payroll_data
    )

    total_loans = sum(
        item['loan_amount']
        for item in payroll_data
    )

    total_net_salary = sum(
        item['net_salary']
        for item in payroll_data
    )

    total_rda_salary = sum(
        Decimal(item['employee'].rda_salary or 0)
        for item in payroll_data
    )

    selected_project = None

    if project_id and project_id.isdigit():

        selected_project = ProjectFirstLevelName.objects.filter(
            id=int(project_id)
        ).first()

    projects = ProjectFirstLevelName.objects.all()

    return render(request, 'payroll/payroll_print_manual.html', {

        'payrolls': payroll_data,

        'month': selected_month,
        'year': year_input,

        'projects': projects,
        'selected_project': selected_project,

        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_gross_salary': total_gross_salary,
        'total_advance': total_advance,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
        'total_rda_salary': total_rda_salary,

        'print_time': timezone.now(),
    })
    
    

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum

from hrm.models import (
    RdaEmployee,
    Attendance,
    Allowances,
    RdaPayEmpSalary
)


@login_required
def update_pay_salary(request):

    if request.method == 'POST':

        month_input = request.POST.get('month')
        project_id = request.POST.get('project_id')

        selected_month_dt = datetime.strptime(
            month_input,
            "%B %Y"
        )

        start_date = selected_month_dt.replace(day=1).date()

        end_day = monthrange(
            selected_month_dt.year,
            selected_month_dt.month
        )[1]

        end_date = selected_month_dt.replace(day=end_day).date()

        days_in_month = end_day

        # =========================
        # PROJECT FILTER ADDED
        # =========================

        employees = RdaEmployee.objects.filter(
            rda_active_status=True
        ).exclude(
            rda_emp_name__iexact='admin'
        )

        if project_id and project_id.isdigit():
            employees = employees.filter(project_name_id=int(project_id))

        for emp in employees:

            rda_salary = Decimal(emp.rda_salary or 0)

            # ======================
            # ABSENT DAYS
            # ======================
            absent_days = Attendance.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                att_status='Absent'
            ).values('date').distinct().count()

            # ======================
            # WORKING DAYS
            # ======================
            working_days = days_in_month - absent_days

            # ======================
            # DAILY SALARY
            # ======================
            daily_salary = (
                rda_salary / Decimal(days_in_month)
            ) if rda_salary else Decimal('0')

            # ======================
            # BASIC SALARY
            # ======================
            basic_salary = (
                daily_salary * working_days
            ).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

            # ======================
            # ALLOWANCES
            # ======================
            allowances = Allowances.objects.filter(
                employee=emp,
                date__range=(start_date, end_date),
                status='due'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # ======================
            # FINAL SALARY
            # ======================
            final_salary = (
                basic_salary + allowances
            ).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

            # ======================
            # PROJECT WISE SAVE
            # ======================
            RdaPayEmpSalary.objects.update_or_create(

                rda_emp_name=emp,
                project_name=emp.project_name,   # IMPORTANT PROJECT WISE
                #pay_date=end_date,
                pay_date=date.today(),

                defaults={

                    'rda_salary': rda_salary,
                    'rda_pay_salary': final_salary,
                    'rda_absent_days': absent_days,
                }
            )

        messages.success(
            request,
            "Project-wise Pay Salary Updated Successfully."
        )

    return redirect('payroll_list')
    


# @login_required
# def payslip_print(request):
#     today = datetime.today()
#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     employee_id = request.GET.get('employee_id')  # NEW

#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     selected_month = selected_month_dt.strftime('%B')
#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()

#     payroll_data = []

#     # Filter employees: if employee_id is given, show only that employee
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_name__iexact='admin')
#     if employee_id:
#         employees = employees.filter(id=employee_id)

#     for emp in employees:
#         rda_salary = emp.rda_salary or 0

#         allowances_sum = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0
#         allowances = allowances_sum

#         attendance_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date)
#         ).count()

#         daily_salary = rda_salary / 30 if rda_salary else 0
#         basic_salary = round(daily_salary * attendance_days, 2)

#         total_deductions = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         net_salary = round(basic_salary + allowances - total_deductions, 2)

#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances,
#                 'deductions': total_deductions,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'working_days': attendance_days,
#             'basic_salary': basic_salary,
#             'allowances': allowances,
#             'deductions': total_deductions,
#             'net_salary': net_salary,
#         })

#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_deductions = sum(item['deductions'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     return render(request, 'payroll/payslip_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_deductions': total_deductions,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#     })



# @login_required
# def payslip_print(request):
#     today = datetime.today()
#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     employee_id = request.GET.get('employee_id')  # specific employee

#     # Parse year
#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     # Parse month
#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     selected_month = selected_month_dt.strftime('%B')  # e.g., "September"
#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()

#     payroll_data = []

#     # Filter employees
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_name__iexact='admin')
#     if employee_id:
#         employees = employees.filter(id=employee_id)

#     for emp in employees:
#         rda_salary = emp.rda_salary or 0

#         # Allowances
#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         # Attendance
#         attendance_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date)
#         ).count()

#         daily_salary = rda_salary / 30 if rda_salary else 0
#         basic_salary = round(daily_salary * attendance_days, 2)

#         # Advance deductions
#         total_advance = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         # Loan deductions
#         loans_qs = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal(0)
#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal(0)

#         # Net salary
#         net_salary = round(basic_salary + allowances - total_advance - total_loan_deduction, 2)

#         # Update or create Payroll record
#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances,
#                 'deductions': total_advance + total_loan_deduction,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'working_days': attendance_days,
#             'basic_salary': basic_salary,
#             'allowances': allowances,
#             'advance_deduction': total_advance,
#             'loan_deduction': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['advance_deduction'] for item in payroll_data)
#     total_loans = sum(item['loan_deduction'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     return render(request, 'payroll/payslip_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#     })




# from django.db.models import Sum
# from django.shortcuts import render
# from django.utils import timezone
# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP


# @login_required
# def payslip_print(request):
#     today = datetime.today()
#     default_month_str = today.strftime('%Y-%m')
#     default_year = today.year

#     month_input = request.GET.get('month', default_month_str)
#     year_input_str = request.GET.get('year', str(default_year))
#     employee_id = request.GET.get('employee_id')

#     # Parse year
#     try:
#         year_input = int(year_input_str)
#     except ValueError:
#         year_input = default_year

#     # Parse month
#     try:
#         selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     except ValueError:
#         selected_month_dt = datetime(today.year, today.month, 1)

#     selected_month = selected_month_dt.strftime('%B')
#     start_date = selected_month_dt.replace(day=1).date()
#     end_day = monthrange(year_input, selected_month_dt.month)[1]
#     end_date = selected_month_dt.replace(day=end_day).date()
#     days_in_month = end_day

#     payroll_data = []

#     # Employees filter
#     employees = RdaEmployee.objects.filter(
#         rda_active_status=True
#     ).exclude(rda_emp_name__iexact='admin')

#     if employee_id and employee_id.isdigit():
#         employees = employees.filter(id=int(employee_id))

#     # 🔴 Manual attendance rules
#     MANUAL_IDS = {4, 6, 8, 10, 13, 17, 34, 35, 36}
#     ABSENT_ONE_DAY_IDS = {4, 34, 36}

#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)

#         # -------------------------
#         # Allowances
#         # -------------------------
#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # -------------------------
#         # Attendance (DEFAULT)
#         # -------------------------
#         attendance_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date)
#         ).count()

#         working_days = attendance_days

#         # -------------------------
#         # Salary (DEFAULT)
#         # -------------------------
#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')
#         basic_salary = (daily_salary * Decimal(working_days)).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         # =========================
#         # 🔴 MANUAL ATTENDANCE OVERRIDE
#         # =========================
#         if emp.id in MANUAL_IDS:
#             if emp.id in ABSENT_ONE_DAY_IDS:
#                 working_days = 29
#             else:
#                 working_days = 30

#             daily_salary = rda_salary / Decimal(days_in_month)
#             basic_salary = (daily_salary * Decimal(working_days)).quantize(
#                 Decimal('0.01'), rounding=ROUND_HALF_UP
#             )

#         # -------------------------
#         # Advance deduction
#         # -------------------------
#         total_advance = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # -------------------------
#         # Loan deduction
#         # -------------------------
#         loans_qs = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal('0')
#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal('0')

#         # -------------------------
#         # Net salary
#         # -------------------------
#         net_salary = (basic_salary + allowances - total_advance - total_loan_deduction).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         # -------------------------
#         # Save Payroll
#         # -------------------------
#         Payroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances,
#                 'deductions': total_advance + total_loan_deduction,
#                 'net_salary': net_salary
#             }
#         )

#         payroll_data.append({
#             'employee': emp,
#             'working_days': working_days,
#             'basic_salary': basic_salary,
#             'allowances': allowances,
#             'advance_deduction': total_advance,
#             'loan_deduction': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     # Totals
#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['advance_deduction'] for item in payroll_data)
#     total_loans = sum(item['loan_deduction'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     return render(request, 'payroll/payslip_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'print_time': timezone.now(),
#     })

    

# from django.db.models import Sum
# from django.utils import timezone
# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP


# @login_required
# def payslip_print(request):
#     today = datetime.today()
#     month_input = request.GET.get('month', today.strftime('%Y-%m'))
#     year_input = int(request.GET.get('year', today.year))
#     employee_id = request.GET.get('employee_id')

#     selected_month_dt = datetime.strptime(month_input, "%Y-%m")
#     month_name = selected_month_dt.strftime('%B')
#     days_in_month = monthrange(year_input, selected_month_dt.month)[1]

#     start_date = selected_month_dt.replace(day=1).date()
#     end_date = selected_month_dt.replace(day=days_in_month).date()

#     payroll_data = []

#     # 🔐 Single employee filter
#     employees = RdaEmployee.objects.filter(
#         rda_active_status=True
#     )

#     if employee_id and employee_id.isdigit():
#         employees = employees.filter(id=int(employee_id))

#     # 🔴 Manual rules
#     MANUAL_IDS = {4, 6, 8, 10, 13, 17, 34, 35, 36}
#     ABSENT_ONE_DAY_IDS = {4, 34, 36}

#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)
#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')

#         # -------- DEFAULT attendance
#         absent_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Absent'
#         ).count()

#         payable_days = days_in_month - absent_days

#         # -------- 🔴 MANUAL attendance
#         if emp.id in MANUAL_IDS:
#             if emp.id in ABSENT_ONE_DAY_IDS:
#                 absent_days = 1
#                 payable_days = 29
#             else:
#                 absent_days = 0
#                 payable_days = 30

#         absent_amount = (daily_salary * Decimal(absent_days)).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         payable_salary = (daily_salary * Decimal(payable_days)).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         # -------- Allowances
#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # -------- Advance
#         advance = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # -------- Loan
#         loans = LoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         loan_amount = Decimal('0')
#         for loan in loans:
#             if loan.month_name and month_name in loan.month_name:
#                 loan_amount += loan.deduction_amount or Decimal('0')

#         net_salary = (payable_salary + allowances - advance - loan_amount).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         payroll_data.append({
#             'employee': emp,
#             'working_days': payable_days,
#             'basic_salary': rda_salary,
#             'absent_amount': absent_amount,
#             'allowances': allowances,
#             'advance_deduction': advance,
#             'loan_deduction': loan_amount,
#             'net_salary': net_salary,
#         })

#     return render(request, 'payroll/payslip_print.html', {
#         'payrolls': payroll_data,
#         'month': month_name,
#         'year': year_input,
#         'print_time': timezone.now(),
#     })



# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP
# from django.db.models import Sum

# @login_required
# def payslip_print(request):
#     employee_id = request.GET.get('employee_id')
#     month_input = request.GET.get('month')
#     year = int(request.GET.get('year'))

#     month_dt = datetime.strptime(month_input, "%Y-%m")
#     month_name = month_dt.strftime('%B')
#     total_days = monthrange(year, month_dt.month)[1]

#     start_date = month_dt.replace(day=1).date()
#     end_date = month_dt.replace(day=total_days).date()

#     employees = RdaEmployee.objects.filter(id=employee_id, rda_active_status=True)

#     # 🔴 Manual control
#     MANUAL_IDS = {4, 6, 8, 10, 13, 17, 34, 35, 36}
#     ABSENT_ONE_DAY_IDS = {4, 34, 36}

#     payrolls = []

#     for emp in employees:
#         salary = Decimal(emp.rda_salary or 0)
#         daily_salary = salary / Decimal(total_days) if salary else Decimal('0')

#         # ---------- Attendance counts
#         present_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Present'
#         ).count()

#         leave_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Leave'
#         ).count()

#         off_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Off'
#         ).count()

#         absent_days = Attendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Absent'
#         ).count()

#         # ---------- Manual override
#         if emp.id in MANUAL_IDS:
#             present_days = total_days
#             leave_days = 0
#             off_days = 0
#             absent_days = 0

#             if emp.id in ABSENT_ONE_DAY_IDS:
#                 absent_days = 1
#                 present_days = total_days - 1

#         payable_days = present_days + leave_days + off_days

#         # ---------- Salary calculation
#         absent_amount = (daily_salary * Decimal(absent_days)).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         payable_salary = (daily_salary * Decimal(payable_days)).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         allowances = Allowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         advance = AdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         loan = LoanPayment.objects.filter(
#             employee=emp,
#             status='due'
#         ).aggregate(total=Sum('deduction_amount'))['total'] or Decimal('0')

#         net_salary = (payable_salary + allowances - advance - loan).quantize(
#             Decimal('0.01'), rounding=ROUND_HALF_UP
#         )

#         payrolls.append({
#             'employee': emp,
#             'total_days': total_days,
#             'present_days': present_days,
#             'leave_days': leave_days,
#             'off_days': off_days,
#             'absent_days': absent_days,
#             'payable_days': payable_days,

#             'working_days': payable_days,
#             'basic_salary': salary,
#             'absent_amount': absent_amount,
#             'allowances': allowances,
#             'advance_deduction': advance,
#             'loan_deduction': loan,
#             'net_salary': net_salary,
#         })

#     return render(request, 'payroll/payslip_print.html', {
#         'payrolls': payrolls,
#         'month': month_name,
#         'year': year,
#     })



from datetime import datetime
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum

@login_required
def payslip_print(request):
    employee_id = request.GET.get('employee_id')
    month_input = request.GET.get('month')
    year = int(request.GET.get('year'))

    month_dt = datetime.strptime(month_input, "%Y-%m")
    month_name = month_dt.strftime('%B')
    total_days = monthrange(year, month_dt.month)[1]

    start_date = month_dt.replace(day=1).date()
    end_date = month_dt.replace(day=total_days).date()

    employees = RdaEmployee.objects.filter(id=employee_id, rda_active_status=True)

    # Manual control
    MANUAL_IDS = {0}
    ABSENT_ONE_DAY_IDS = {0}

    payrolls = []

    for emp in employees:
        salary = Decimal(emp.rda_salary or 0)
        daily_salary = salary / Decimal(total_days) if salary else Decimal('0')

        # Attendance counts from DB
        present_days = Attendance.objects.filter(
            employee=emp, date__range=(start_date, end_date), att_status='Present'
        ).count()

        leave_days = Attendance.objects.filter(
            employee=emp, date__range=(start_date, end_date), att_status='Leave'
        ).count()

        off_days = Attendance.objects.filter(
            employee=emp, date__range=(start_date, end_date), att_status='Off Day'  # ✅ exact match
        ).count()

        absent_days = Attendance.objects.filter(
            employee=emp, date__range=(start_date, end_date), att_status='Absent'
        ).count()

        # Manual override for specific employees
        if emp.id in MANUAL_IDS:
            present_days = total_days
            leave_days = 0
            off_days = 0
            absent_days = 0

            if emp.id in ABSENT_ONE_DAY_IDS:
                absent_days = 1
                present_days = total_days - 1

        payable_days = present_days + leave_days + off_days

        # Salary calculations
        absent_amount = (daily_salary * Decimal(absent_days)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        payable_salary = (daily_salary * Decimal(payable_days)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        allowances = Allowances.objects.filter(
            employee=emp, date__range=(start_date, end_date), status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        advance = AdvancePayment.objects.filter(
            employee=emp, date__range=(start_date, end_date), status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        loan = LoanPayment.objects.filter(
            employee=emp, status='due'
        ).aggregate(total=Sum('deduction_amount'))['total'] or Decimal('0')

        net_salary = (payable_salary + allowances - advance - loan).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        payrolls.append({
            'employee': emp,
            'total_days': total_days,
            'present_days': present_days,
            'leave_days': leave_days,
            'off_days': off_days,
            'absent_days': absent_days,
            'payable_days': payable_days,

            'working_days': payable_days,
            'basic_salary': salary,
            'absent_amount': absent_amount,
            'allowances': allowances,
            'advance_deduction': advance,
            'loan_deduction': loan,
            'net_salary': net_salary,
        })

    return render(request, 'payroll/payslip_print.html', {
        'payrolls': payrolls,
        'month': month_name,
        'year': year,
    })



### ADVANCE PAYMENT ###
@login_required
def advance_list(request):
    records = AdvancePayment.objects.all()
    return render(request, 'advancepayment/advance_list.html', {'records': records})


# @login_required
# def advance_create(request):
#     if request.method == 'POST':
#         form = AdvancePaymentForm(request.POST)
#         if form.is_valid():
#             loanvoucher = form.save(commit=False)
#             loanvoucher.save()

#             # Get cash_type instance from loanvoucher (no need to query again)
#             cash_type = loanvoucher.cash_type
#             if cash_type:
#                 current_balance = cash_type.type_amount or 0
#                 cash_type.type_amount = current_balance - (loanvoucher.amount or 0)
#                 cash_type.type_note = f"Update Payment of voucher ID {loanvoucher.id}"
#                 cash_type.save()

#             # Get project
#             try:
#                 project = ProjectFirstLevelName.objects.get(project_first_name='BTP Office')
#             except ProjectFirstLevelName.DoesNotExist:
#                 project = None

#             # Get head of account
#             try:
#                 head_obj = HeadOfAccount.objects.get(head_name='Employee Account')
#             except HeadOfAccount.DoesNotExist:
#                 head_obj = None

#             type_choice = 'Employee' 

#             # Create TransactionHistory record
#             TransactionHistory.objects.create(
#                 project=project,
#                 transaction_type=type_choice,  # fix here, don't use 'type'
#                 head_of_account=head_obj,
#                 cash_type=cash_type,
#                 amount=loanvoucher.amount,
#                 date=loanvoucher.date,
#                 type_name="Employee",
#                 reference='',
#             )

#             # Setup amounts for ledger entry
#             loan_status = 'Payment'
#             amount = loanvoucher.amount or 0
#             debit_amount = amount if loan_status.lower() == 'payment' else 0
#             credit_amount = amount if loan_status.lower() == 'received' else 0

#             # Save LedgerEntry if all required objects exist
#             if project and head_obj and loanvoucher.date:
#                 try:
#                     entry = LedgerEntry.objects.create(
#                         project_name=project,
#                         type=type_choice,
#                         empl_name=str(loanvoucher.employee),
#                         type_name='Employee',
#                         head=head_obj,
#                         date=loanvoucher.date,
#                         description=loanvoucher.reason or 'Advance Payment',
#                         bankName=None,  # if you're using bankName field
#                         cash_type=cash_type,  # or use this if it's a cash transaction
#                         cheque_number=loanvoucher.cheque_number,
#                         debit=debit_amount,
#                         credit=credit_amount,
#                         carrier=str(loanvoucher.employee),
#                         loan_status=loan_status,
#                     )
#                     print('✅ Ledger Entry Created:', entry.pk)
#                 except Exception as e:
#                     print('❌ LedgerEntry creation failed:', str(e))
#             else:
#                 print('❌ Missing required LedgerEntry fields: project, head_obj, or date.')

#             return redirect('advance_list')
#     else:
#         form = AdvancePaymentForm()

#     return render(request, 'advancepayment/advance_form.html', {'form': form})




@login_required
def advance_create(request):
    if request.method == 'POST':
        form = AdvancePaymentForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            # Create DebitVoucher
            debit_voucher = DebitVoucher.objects.create(
                type='Employee', 
                empl_name=str(loanvoucher.employee),
                project_name=loanvoucher.project_name,
                cash_type=loanvoucher.cash_type,
                cheque_number=loanvoucher.cheque_number,
                head_of_account=loanvoucher.head_of_account,  
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                particulars=loanvoucher.reason or "Advance to Employee",
                is_confirmed=True,
                carrier=str(loanvoucher.employee),
                create_dr=str(request.user),
            )
            print('ebitVoucher created:', debit_voucher.id)
            return redirect('advance_list')
    else:
        form = AdvancePaymentForm()

    # CORRECT VARIABLE NAME
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')

    return render(request, 'advancepayment/advance_form.html', {
        'form': form,
        'projects': projects,               
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })


    

    
    
    

@login_required
def advance_edit(request, pk):
    record = get_object_or_404(AdvancePayment, pk=pk)
    if request.method == 'POST':
        form = AdvancePaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('advance_list')
    else:
        form = AdvancePaymentForm(instance=record)
    project = get_object_or_404(ProjectFirstLevelName, project_first_name='BTP Office')
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')
    return render(request, 'advancepayment/advance_form.html', {'form': form, 'projects': [project],'head_of_accounts': [head_of_account]})

@login_required
def advance_delete(request, pk):
    record = get_object_or_404(AdvancePayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('advance_list')
    return render(request, 'advancepayment/advance_confirm_delete.html', {'record': record})

### Allowances PAYMENT ###
@login_required
def allowances_list(request):
    records = Allowances.objects.all().order_by('-id')
    return render(request, 'allowances/allowances_list.html', {'records': records})


@login_required
def allowances_create(request):
    if request.method == 'POST':
        form = AllowancesForm(request.POST)

        if form.is_valid():
            allowance = form.save(commit=False)

            # If project is NOT handled by form properly (optional override)
            project_id = request.POST.get('project_name')
            if project_id:
                allowance.project_name = get_object_or_404(
                    ProjectFirstLevelName,
                    id=project_id
                )

            # Ensure date fallback
            if not allowance.date:
                allowance.date = now().date()

            allowance.save()
            return redirect('allowances_list')

    else:
        form = AllowancesForm()

    projects = ProjectFirstLevelName.objects.all()

    return render(request, 'allowances/allowances_form.html', {
        'form': form,
        'projects': projects,
        'today': now().date(),
    })


@login_required
def allowances_edit(request, pk):
    record = get_object_or_404(Allowances, pk=pk)

    if request.method == 'POST':
        form = AllowancesForm(request.POST, instance=record)

        if form.is_valid():
            allowance = form.save(commit=False)

            # Ensure date fallback (optional safety)
            if not allowance.date:
                allowance.date = now().date()

            allowance.save()
            return redirect('allowances_list')

    else:
        form = AllowancesForm(instance=record)

    return render(request, 'allowances/allowances_form.html', {
        'form': form,
        'today': now().date(),
    })



@login_required
def allowances_delete(request, pk):
    record = get_object_or_404(Allowances, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('allowances_list')
    return render(request, 'allowances/allowances_confirm_delete.html', {'record': record})
    


### SALARY PAYMENT ###
@login_required
def salary_list(request):
    employees = RdaEmployee.objects.all()
    records = SalaryPayment.objects.all()
    return render(request, 'salary/salary_list.html', {'records': records, 'employees': employees})

# @login_required
# def salary_create(request):
#     if request.method == 'POST':
#         form = SalaryPaymentForm(request.POST)
#         if form.is_valid():
#             loanvoucher = form.save(commit=False)
#             loanvoucher.save()

#             # Create DebitVoucher
#             debit_voucher = DebitVoucher.objects.create(
#                 type='Employee', 
#                 empl_name=str(loanvoucher.employee),
#                 project_name=loanvoucher.project_name,
#                 cash_type=loanvoucher.cash_type,
#                 cheque_number=loanvoucher.cheque_number,
#                 head_of_account=loanvoucher.head_of_account,  
#                 amount=loanvoucher.amount,
#                 date=loanvoucher.date or timezone.now().date(),
#                 particulars=loanvoucher.reason or "Allowances to Employee",
#                 is_confirmed=True,
#                 carrier=str(loanvoucher.employee),
#                 create_dr=str(request.user),
#             )
#             print('ebitVoucher created:', debit_voucher.id)
#             return redirect('salary_list')
#     else:
#         form = AdvancePaymentForm()

#     # ORRECT VARIABLE NAME
#     projects = ProjectFirstLevelName.objects.all()
#     head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')

#     return render(request, 'salary/salary_form.html', {
#         'form': form,
#         'projects': projects,               
#         'head_of_accounts': [head_of_account],
#         'today': now().date(),
#     })



@login_required
def get_project_employees(request):
    project_id = request.GET.get('project_id')
    if project_id:
        # Change 'project_name_id' to match your exact foreign key field name if needed (e.g., 'project_id')
        active_employees = RdaEmployee.objects.filter(
            project_name_id=project_id, 
            rda_active_status=True
        ).values('id', 'rda_emp_name')
        return JsonResponse(list(active_employees), safe=False)
    return JsonResponse([], safe=False)
    

@login_required
def salary_create(request):
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        
        project_id = request.POST.get('project_name')
        if project_id:
            form.fields['employee'].queryset = RdaEmployee.objects.filter(
                project_name_id=project_id, 
                rda_active_status=True
            )

        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            DebitVoucher.objects.create(
                type='Employee', 
                empl_name=str(loanvoucher.employee),
                project_name=loanvoucher.project_name,
                cash_type=loanvoucher.cash_type,
                cheque_number=loanvoucher.cheque_number,
                head_of_account=loanvoucher.head_of_account,  
                amount=loanvoucher.amount,
                date=loanvoucher.date or now().date(),
                particulars=loanvoucher.reason or "Allowances to Employee",
                is_confirmed=True,
                carrier=str(loanvoucher.employee),
                create_dr=str(request.user),
            )
            return redirect('salary_list')
    else:
        form = SalaryPaymentForm()

    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')

    return render(request, 'salary/salary_form.html', {
        'form': form,
        'projects': projects,             
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })
    
    
@login_required
def salary_edit(request, pk):
    record = get_object_or_404(SalaryPayment, pk=pk)
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('salary_list')
    else:
        form = SalaryPaymentForm(instance=record)
        
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')
    return render(request, 'salary/salary_form.html', {
        'form': form,
        'projects': projects,               
        'head_of_accounts': [head_of_account],
        'today': date.today(), 
    })



@login_required
def salary_delete(request, pk):
    record = get_object_or_404(SalaryPayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('salary_list')
    return render(request, 'salary/salary_confirm_delete.html', {'record': record})
    
    
    
# ### LEAVE ###
# @login_required
# def leave_list(request):
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin')
#     leaves = Leave.objects.all().order_by('-id')
#     return render(request, 'leave/leave_list.html', {'leaves': leaves, 'employees': employees})


# @login_required
# def leave_apply(request):
#     department = request.session.get('department')

#     if request.method == 'POST':
#         form = LeaveForm(request.POST, department=department)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Leave applied successfully.")
#             return redirect('leave_list')
#     else:
#         form = LeaveForm(department=department)

#     return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Apply for Leave'})



# @login_required
# def leave_edit(request, pk):
#     leave = get_object_or_404(Leave, pk=pk)
#     if request.method == 'POST':
#         form = LeaveForm(request.POST, instance=leave)
#         if form.is_valid():
#             form.save()
#             return redirect('leave_list')
#     else:
#         form = LeaveForm(instance=leave)
#     return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Edit Leave'})


# @login_required
# def leave_delete(request, pk):
#     leave = get_object_or_404(Leave, pk=pk)
#     if request.method == 'POST':
#         log_deleted_data(leave, request.user)
#         leave.delete()
#         return redirect('leave_list')
#     return render(request, 'leave/leave_confirm_delete.html', {'leave': leave})


from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RdaEmployee, Leave, LeaveAllocation, Attendance
from .forms import LeaveForm, LeaveAllocationForm


def sync_leave_and_attendance(leave):
    """
    Loops through every single date between start_date and end_date (inclusive)
    and updates/creates an Attendance record marked as 'Leave'.
    Also updates LeaveAllocation counters upon approval.
    """
    if not leave.approved:
        return

    # 1. Update Allocation Counters
    year = leave.start_date.year
    alloc, _ = LeaveAllocation.objects.get_or_create(employee=leave.employee, year=year)

    days = leave.total_days
    if leave.leave_type == 'CL':
        alloc.casual_leave_used += days
    elif leave.leave_type == 'SL':
        alloc.sick_leave_used += days
    elif leave.leave_type == 'EL':
        alloc.earned_leave_used += days
    alloc.save()

    # 2. Multi-Date Attendance Sync (Iterates day by day from start_date to end_date)
    curr_date = leave.start_date
    while curr_date <= leave.end_date:
        Attendance.objects.update_or_create(
            employee=leave.employee,
            date=curr_date,
            defaults={
                'att_status': 'Leave',
                'check_in': None,
                'check_out': None
            }
        )
        curr_date += timedelta(days=1)


# ==========================================
# LEAVE MANAGEMENT VIEWS
# ==========================================

# @login_required
# def leave_list(request):
#     employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin')
#     leaves = Leave.objects.all().order_by('-id')
#     return render(request, 'leave/leave_list.html', {'leaves': leaves, 'employees': employees})


@login_required
def leave_list(request):
    # Excluded project list
    excluded_projects = [
        "The Galleria Restauent Cafe",
        "The Galleria Live Kitchen"
    ]
    
    # Filter active, non-admin employees AND exclude employees from specified projects
    employees = RdaEmployee.objects.filter(
        rda_active_status=True
    ).exclude(
        rda_emp_type__iexact='admin'
    ).exclude(
        project_name__project_first_name__in=excluded_projects  # Adjust field path if needed (e.g., project_name__in)
    )

    leaves = Leave.objects.all().order_by('-id')
    
    return render(request, 'leave/leave_list.html', {
        'leaves': leaves, 
        'employees': employees
    })
    

@login_required
def leave_apply(request):
    department = request.session.get('department')

    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES, department=department)
        if form.is_valid():
            leave = form.save()
            if leave.approved:
                sync_leave_and_attendance(leave)
            messages.success(request, "Leave applied successfully.")
            return redirect('leave_list')
    else:
        form = LeaveForm(department=department)

    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Apply for Leave'})


@login_required
def leave_edit(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES, instance=leave)
        if form.is_valid():
            leave = form.save()
            if leave.approved:
                sync_leave_and_attendance(leave)
            messages.success(request, "Leave updated successfully.")
            return redirect('leave_list')
    else:
        form = LeaveForm(instance=leave)
    return render(request, 'leave/leave_form.html', {'form': form, 'title': 'Edit Leave'})


@login_required
def leave_delete(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, "Leave deleted successfully.")
        return redirect('leave_list')
    return render(request, 'leave/leave_confirm_delete.html', {'leave': leave})


@login_required
def leave_approval(request, pk):
    """Toggle Approval status for Leave request"""
    leave = get_object_or_404(Leave, pk=pk)
    leave.approved = not leave.approved
    leave.save()

    if leave.approved:
        sync_leave_and_attendance(leave)
        messages.success(request, f"Leave for {leave.employee} has been approved.")
    else:
        messages.warning(request, f"Leave for {leave.employee} approval status removed.")

    return redirect('leave_list')


@login_required
def employee_leave_summary(request):
    """Popup report view for employee leave balance and history"""
    emp_id = request.GET.get('employee_id')
    year_id = request.GET.get('year_id', date.today().year)

    employee = get_object_or_404(RdaEmployee, pk=emp_id)
    alloc, _ = LeaveAllocation.objects.get_or_create(employee=employee, year=int(year_id))

    leave_history = Leave.objects.filter(
        employee=employee,
        approved=True,
        start_date__year=year_id
    ).order_by('-start_date')

    context = {
        'employee': employee,
        'alloc': alloc,
        'year': year_id,
        'leave_history': leave_history
    }
    return render(request, 'leave/leave_summary_popup.html', context)


# ==========================================
# LEAVE ALLOCATION MANAGEMENT VIEWS (CRUD)
# ==========================================

# @login_required
# def allocation_list(request):
#     allocations = LeaveAllocation.objects.all().order_by('-year', 'employee__rda_emp_name')
#     return render(request, 'leave/allocation_list.html', {'allocations': allocations})


@login_required
def allocation_list(request):
    # Excluded project list
    excluded_projects = [
        "The Galleria Restauent Cafe",
        "The Galleria Live Kitchen"
    ]

    # Filter allocations for active, non-admin employees and exclude specified projects
    allocations = LeaveAllocation.objects.filter(
        employee__rda_active_status=True
    ).exclude(
        employee__rda_emp_type__iexact='admin'
    ).exclude(
        employee__project_name__project_first_name__in=excluded_projects  # Adjust field path if needed
    ).order_by('-year', 'employee__rda_emp_name')

    return render(request, 'leave/allocation_list.html', {'allocations': allocations})
    

@login_required
def allocation_create(request):
    if request.method == 'POST':
        form = LeaveAllocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave allocation created successfully.")
            return redirect('allocation_list')
    else:
        form = LeaveAllocationForm()
    return render(request, 'leave/allocation_form.html', {'form': form, 'title': 'Add Leave Allocation'})


@login_required
def allocation_edit(request, pk):
    alloc = get_object_or_404(LeaveAllocation, pk=pk)
    if request.method == 'POST':
        form = LeaveAllocationForm(request.POST, instance=alloc)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave allocation updated successfully.")
            return redirect('allocation_list')
    else:
        form = LeaveAllocationForm(instance=alloc)
    return render(request, 'leave/allocation_form.html', {'form': form, 'title': 'Edit Leave Allocation'})


@login_required
def allocation_delete(request, pk):
    alloc = get_object_or_404(LeaveAllocation, pk=pk)
    if request.method == 'POST':
        alloc.delete()
        messages.success(request, "Leave allocation deleted successfully.")
        return redirect('allocation_list')
    return render(request, 'leave/allocation_confirm_delete.html', {'alloc': alloc})
    


# from datetime import datetime, timedelta, time
# from django.contrib import messages
# from django.utils import timezone
# from tenant.models import Attendance as tenantAttendance


# @login_required
# def leave_approval(request, pk):
#     # Only admin can approve
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve leaves.")
#         return redirect('leave_list')

#     leave = get_object_or_404(Leave, pk=pk)
#     device_sn = "SMR5253000001"

#     # ----------------------------------------------------------------------
#     # Attendance preview
#     # ----------------------------------------------------------------------
#     attendance_preview = tenantAttendance.objects.filter(
#         user_id=leave.employee.id,
#         device_sn=device_sn,
#         created_at__date__range=[leave.start_date, leave.end_date]
#     ).order_by("punch_time")

#     # ----------------------------------------------------------------------
#     # APPROVE / REJECT
#     # ----------------------------------------------------------------------
#     if request.method == 'POST':
#         approved = request.POST.get('approved')

#         if approved == 'True':
#             leave.approved = True
#             leave.save()

#             manual_check_in = time(9, 59)
#             manual_check_out = time(19, 40)

#             start = leave.start_date
#             end = leave.end_date
#             day_count = (end - start).days + 1

#             for i in range(day_count):
#                 day = start + timedelta(days=i)

#                 # ------------------------------
#                 # CHECK-IN
#                 # ------------------------------
#                 punch_in = datetime.combine(day, manual_check_in)
#                 in_qs = tenantAttendance.objects.filter(
#                     user_id=leave.employee.id,
#                     device_sn=device_sn,
#                     created_at__date=day,
#                     check_type=1
#                 ).order_by('id')

#                 if in_qs.exists():
#                     main_in = in_qs.first()
#                     # Remove duplicates
#                     if in_qs.count() > 1:
#                         in_qs.exclude(id=main_in.id).delete()

#                     # Update only if not Present
#                     if main_in.status != 1:
#                         main_in.punch_time = punch_in
#                         main_in.status = 2  # Leave
#                         main_in.created_at = day  # leave date
#                         main_in.save()
#                 else:
#                     tenantAttendance.objects.create(
#                         user_id=leave.employee.id,
#                         device_sn=device_sn,
#                         check_type=1,
#                         punch_time=punch_in,
#                         status=2,  # Leave
#                         field1=0, field2=0, field3=0,
#                         field4=0, field5=0, field6=0,
#                         created_at=day  # leave date
#                     )

#                 # ------------------------------
#                 # CHECK-OUT
#                 # ------------------------------
#                 punch_out = datetime.combine(day, manual_check_out)
#                 out_qs = tenantAttendance.objects.filter(
#                     user_id=leave.employee.id,
#                     device_sn=device_sn,
#                     created_at__date=day,
#                     check_type=0
#                 ).order_by('id')

#                 if out_qs.exists():
#                     main_out = out_qs.first()
#                     if out_qs.count() > 1:
#                         out_qs.exclude(id=main_out.id).delete()

#                     if main_out.status != 1:
#                         main_out.punch_time = punch_out
#                         main_out.status = 2  # Leave
#                         main_out.created_at = day
#                         main_out.save()
#                 else:
#                     tenantAttendance.objects.create(
#                         user_id=leave.employee.id,
#                         device_sn=device_sn,
#                         check_type=0,
#                         punch_time=punch_out,
#                         status=2,
#                         field1=0, field2=0, field3=0,
#                         field4=0, field5=0, field6=0,
#                         created_at=day
#                     )

#             messages.success(
#                 request,
#                 f"Leave approved and attendance inserted/updated successfully for {leave.employee.rda_emp_name}."
#             )

#         else:
#             leave.approved = False
#             leave.save()
#             messages.success(
#                 request,
#                 f"Leave rejected for {leave.employee.rda_emp_name}."
#             )

#         return redirect('leave_list')

#     return render(request, 'leave/leave_approval.html', {
#         "leave": leave,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })



from tenant.models import Attendance as tenantAttendance
from hrm.models import RdaEmployee, Attendance  


@login_required
def leave_approval(request, pk):
    # Only admin can approve
    if request.session.get('department') != 'admin':
        messages.error(request, "You are not authorized to approve leaves.")
        return redirect('leave_list')

    leave = get_object_or_404(Leave, pk=pk)
    device_sn = "SMR5253000001"

    # Attendance preview (tenant)
    attendance_preview = tenantAttendance.objects.filter(
        user_id=leave.employee.id,
        device_sn=device_sn,
        created_at__date__range=[leave.start_date, leave.end_date]
    ).order_by("punch_time")

    # Approve / Reject
    if request.method == 'POST':
        approved = request.POST.get('approved')

        if approved == 'True':
            leave.approved = True
            leave.save()

            manual_check_in = time(9, 59)
            manual_check_out = time(19, 40)

            start = leave.start_date
            end = leave.end_date
            day_count = (end - start).days + 1

            for i in range(day_count):
                day = start + timedelta(days=i)

                # ------------------------------
                # TENANT APP - CHECK-IN
                # ------------------------------
                punch_in = datetime.combine(day, manual_check_in)
                in_qs = tenantAttendance.objects.filter(
                    user_id=leave.employee.id,
                    device_sn=device_sn,
                    created_at__date=day,
                    check_type=1
                ).order_by('id')

                if in_qs.exists():
                    main_in = in_qs.first()
                    if in_qs.count() > 1:
                        in_qs.exclude(id=main_in.id).delete()
                    if main_in.status != 1:
                        main_in.punch_time = punch_in
                        main_in.status = 2  # Leave
                        main_in.created_at = day
                        main_in.save()
                else:
                    tenantAttendance.objects.create(
                        user_id=leave.employee.id,
                        device_sn=device_sn,
                        check_type=1,
                        punch_time=punch_in,
                        status=2,  # Leave
                        field1=0, field2=0, field3=0,
                        field4=0, field5=0, field6=0,
                        created_at=day
                    )

                # ------------------------------
                # TENANT APP - CHECK-OUT
                # ------------------------------
                punch_out = datetime.combine(day, manual_check_out)
                out_qs = tenantAttendance.objects.filter(
                    user_id=leave.employee.id,
                    device_sn=device_sn,
                    created_at__date=day,
                    check_type=0
                ).order_by('id')

                if out_qs.exists():
                    main_out = out_qs.first()
                    if out_qs.count() > 1:
                        out_qs.exclude(id=main_out.id).delete()
                    if main_out.status != 1:
                        main_out.punch_time = punch_out
                        main_out.status = 2  # Leave
                        main_out.created_at = day
                        main_out.save()
                else:
                    tenantAttendance.objects.create(
                        user_id=leave.employee.id,
                        device_sn=device_sn,
                        check_type=0,
                        punch_time=punch_out,
                        status=2,
                        field1=0, field2=0, field3=0,
                        field4=0, field5=0, field6=0,
                        created_at=day
                    )

                # ------------------------------
                # HRM APP - Attendance Table
                # ------------------------------
                Attendance.objects.update_or_create(
                    employee=leave.employee,
                    date=day,
                    defaults={
                        "check_in": manual_check_in,
                        "check_out": manual_check_out,
                        "att_status": "Leave",
                    }
                )

            messages.success(
                request,
                f"Leave approved and attendance updated for {leave.employee.rda_emp_name}."
            )

        else:
            leave.approved = False
            leave.save()
            messages.success(
                request,
                f"Leave rejected for {leave.employee.rda_emp_name}."
            )

        return redirect('leave_list')

    return render(request, 'leave/leave_approval.html', {
        "leave": leave,
        "attendance_preview": attendance_preview,
        "print_time": timezone.now(),
    })





# @login_required
# def employee_leave_summary(request):
#     employee_id = request.GET.get('employee_id')
#     year_id = request.GET.get('year_id')
#     month_id = request.GET.get('month_id')

#     # Validate input
#     if not (employee_id and year_id and month_id):
#         return HttpResponse("Missing employee_id, year_id or month_id.", status=400)

#     try:
#         year = int(year_id)
#         month = int(month_id)
#         employee_id = int(employee_id)
#     except ValueError:
#         return HttpResponse("Invalid year, month or employee_id.", status=400)

#     employee = get_object_or_404(RdaEmployee, id=employee_id)

#     # Get the first and last date of the target month
#     month_start = date(year, month, 1)
#     month_end_day = monthrange(year, month)[1]
#     month_end = date(year, month, month_end_day)

#     # Filter leaves that overlap with the target month
#     leave_records = Leave.objects.filter(
#         employee=employee,
#         start_date__lte=month_end,
#         end_date__gte=month_start
#     ).order_by('start_date')

#     context = {
#         'employee': employee,
#         'attendance_records': leave_records,
#         'year': year,
#         'month': month,
#         'print_time': now(),
#     }
#     return render(request, 'leave/leave_summary.html', context)
    
    
    
    
### IOM ###
@login_required
def iom_list(request):
    employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin')
    iom = Iom.objects.all().order_by('-id')
    return render(request, 'iom/iom_list.html', {'ioms': iom, 'employees': employees})


@login_required
def iom_apply(request):
    department = request.session.get('department')

    if request.method == 'POST':
        form = IomForm(request.POST, department=department)
        if form.is_valid():
            form.save()
            messages.success(request, "IOM applied successfully.")
            return redirect('iom_list')
    else:
        form = IomForm(department=department)

    return render(request, 'iom/iom_form.html', {'form': form, 'title': 'Apply for IOM'})





@login_required
def iom_edit(request, pk):
    iom = get_object_or_404(Iom, pk=pk)
    if request.method == 'POST':
        form = IomForm(request.POST, instance=iom)
        if form.is_valid():
            form.save()
            return redirect('iom_list')
    else:
        form = IomForm(instance=iom)
    return render(request, 'iom/iom_form.html', {'form': form, 'title': 'Edit Leave'})


@login_required
def iom_delete(request, pk):
    iom = get_object_or_404(Iom, pk=pk)
    if request.method == 'POST':
        log_deleted_data(iom, request.user)
        iom.delete()
        return redirect('iom_list')
    return render(request, 'iom/iom_confirm_delete.html', {'iom': iom})




# from django.contrib import messages
# from django.utils import timezone
# from datetime import datetime
# from tenant.models import Attendance as tenantAttendance 
# from .models import Iom


# @login_required
# def iom_approval(request, pk):

#     # Permission check
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve IOM.")
#         return redirect('iom_list')

#     iom = get_object_or_404(Iom, pk=pk)

#     # ----------------------------------------------------------------------
#     # ATTENDANCE PREVIEW (BEFORE APPROVAL)
#     # ----------------------------------------------------------------------
#     # You are using a fixed device serial — I kept it same
#     device_sn = "SMR5253000001"

#     attendance_preview = tenantAttendance.objects.filter(
#         user_id=iom.employee.id,
#         device_sn=device_sn,
#         created_at__date=iom.start_date
#     ).order_by("punch_time")

#     # ----------------------------------------------------------------------
#     # APPROVE / REJECT SUBMISSION
#     # ----------------------------------------------------------------------
#     if request.method == 'POST':
#         approved = request.POST.get("approved")

#         if approved == "True":

#             # ==============================================================
#             # INSERT / UPDATE ATTENDANCE WHEN APPROVED
#             # ==============================================================

#             user_id = iom.employee.id
#             date = iom.start_date

#             # CREATE CHECK-IN ROW
#             if iom.check_in:
#                 punch_dt = datetime.combine(date, iom.check_in)

#                 tenantAttendance.objects.create(
#                     user_id=user_id,
#                     punch_time=punch_dt,
#                     status=1,          # Present
#                     check_type=1,      # Check-In
#                     field1=0, field2=0, field3=0,
#                     field4=0, field5=0, field6=0,
#                     device_sn=device_sn
#                 )

#             # CREATE CHECK-OUT ROW
#             if iom.check_out:
#                 punch_dt = datetime.combine(date, iom.check_out)

#                 tenantAttendance.objects.create(
#                     user_id=user_id,
#                     punch_time=punch_dt,
#                     status=1,          # Present
#                     check_type=0,      # Check-Out
#                     field1=0, field2=0, field3=0,
#                     field4=0, field5=0, field6=0,
#                     device_sn=device_sn
#                 )

#             # MARK IOM APPROVED
#             iom.approved = True
#             iom.save()

#             messages.success(request, "IOM Approved Successfully and Attendance Inserted.")

#         else:
#             # REJECT
#             iom.approved = False
#             iom.save()
#             messages.success(request, "IOM Rejected.")

#         return redirect('iom_list')

#     # ----------------------------------------------------------------------
#     # SEND DATA TO HTML PAGE
#     # ----------------------------------------------------------------------
#     return render(request, 'iom/iom_approval.html', {
#         "iom": iom,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })




from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from tenant.models import Attendance as tenantAttendance
from .models import Iom


# @login_required
# def iom_approval(request, pk):

#     # Permission check
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve IOM.")
#         return redirect('iom_list')

#     iom = get_object_or_404(Iom, pk=pk)

#     device_sn = "SMR5253000001"

#     # Preview only start_date punches
#     attendance_preview = tenantAttendance.objects.filter(
#         user_id=iom.employee.id,
#         device_sn=device_sn,
#         punch_time__date=iom.start_date
#     ).order_by("punch_time")

#     if request.method == 'POST':
#         approved = request.POST.get("approved")

#         if approved == "True":

#             user_id = iom.employee.id

#             start_date = iom.start_date
#             end_date = iom.end_date or iom.start_date

#             current_date = start_date

#             # ----------------------------------------------------------
#             # LOOP THROUGH DATE RANGE
#             # ----------------------------------------------------------
#             while current_date <= end_date:

#                 # CHECK-IN
#                 if iom.check_in:
#                     punch_dt = datetime.combine(current_date, iom.check_in)

#                     tenantAttendance.objects.create(
#                         user_id=user_id,
#                         punch_time=punch_dt,
#                         status=1,
#                         check_type=1,
#                         field1=0, field2=0, field3=0,
#                         field4=0, field5=0, field6=0,
#                         device_sn=device_sn
#                     )

#                 # CHECK-OUT
#                 if iom.check_out:
#                     punch_dt = datetime.combine(current_date, iom.check_out)

#                     tenantAttendance.objects.create(
#                         user_id=user_id,
#                         punch_time=punch_dt,
#                         status=1,
#                         check_type=0,
#                         field1=0, field2=0, field3=0,
#                         field4=0, field5=0, field6=0,
#                         device_sn=device_sn
#                     )

#                 current_date += timedelta(days=1)

#             iom.approved = True
#             iom.save()

#             messages.success(
#                 request,
#                 "IOM Approved and Attendance inserted for selected dates."
#             )

#         else:
#             iom.approved = False
#             iom.save()
#             messages.success(request, "IOM Rejected.")

#         return redirect('iom_list')

#     return render(request, 'iom/iom_approval.html', {
#         "iom": iom,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })



# @login_required
# def iom_approval(request, pk):

#     # Permission check
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve IOM.")
#         return redirect('iom_list')

#     iom = get_object_or_404(Iom, pk=pk)

#     device_sn = "SMR5253000001"

#     # Preview attendance for start date
#     attendance_preview = tenantAttendance.objects.filter(
#         user_id=iom.employee.id,
#         device_sn=device_sn,
#         punch_time__date=iom.start_date
#     ).order_by("punch_time")

#     if request.method == 'POST':
#         approved = request.POST.get("approved")

#         if approved == "True":

#             user_id = iom.employee.id
#             start_date = iom.start_date
#             end_date = iom.end_date or iom.start_date

#             current_date = start_date

#             # LOOP THROUGH DATE RANGE
#             while current_date <= end_date:

#                 # -------- CHECK-IN --------
#                 if iom.check_in:
#                     punch_dt = datetime.combine(current_date, iom.check_in)

#                     tenantAttendance.objects.update_or_create(
#                         user_id=user_id,
#                         device_sn=device_sn,
#                         punch_time__date=current_date,
#                         check_type=1,  # check-in
#                         defaults={
#                             "punch_time": punch_dt,
#                             "status": 1,
#                             "field1": 0,
#                             "field2": 0,
#                             "field3": 0,
#                             "field4": 0,
#                             "field5": 0,
#                             "field6": 0,
#                         },
#                     )

#                 # -------- CHECK-OUT --------
#                 if iom.check_out:
#                     punch_dt = datetime.combine(current_date, iom.check_out)

#                     tenantAttendance.objects.update_or_create(
#                         user_id=user_id,
#                         device_sn=device_sn,
#                         punch_time__date=current_date,
#                         check_type=0,  # check-out
#                         defaults={
#                             "punch_time": punch_dt,
#                             "status": 1,
#                             "field1": 0,
#                             "field2": 0,
#                             "field3": 0,
#                             "field4": 0,
#                             "field5": 0,
#                             "field6": 0,
#                         },
#                     )

#                 current_date += timedelta(days=1)

#             iom.approved = True
#             iom.save()

#             messages.success(
#                 request,
#                 "IOM Approved and attendance updated/inserted successfully."
#             )

#         else:
#             iom.approved = False
#             iom.save()
#             messages.success(request, "IOM Rejected.")

#         return redirect('iom_list')

#     return render(request, 'iom/iom_approval.html', {
#         "iom": iom,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })




@login_required
def iom_approval(request, pk):

    if request.session.get('department') != 'admin':
        messages.error(request, "You are not authorized to approve IOM.")
        return redirect('iom_list')

    iom = get_object_or_404(Iom, pk=pk)

    device_sn = "SMR5253000001"

    attendance_preview = tenantAttendance.objects.filter(
        user_id=iom.employee.id,
        device_sn=device_sn,
        punch_time__date=iom.start_date
    ).order_by("punch_time")

    if request.method == 'POST':
        approved = request.POST.get("approved")

        if approved == "True":

            user_id = iom.employee.id
            start_date = iom.start_date
            end_date = iom.end_date or iom.start_date

            current_date = start_date

            while current_date <= end_date:

                # ---------- CHECK-IN ----------
                if iom.check_in:
                    punch_dt = datetime.combine(current_date, iom.check_in)

                    records = tenantAttendance.objects.filter(
                        user_id=user_id,
                        device_sn=device_sn,
                        punch_time__date=current_date,
                        check_type=1
                    ).order_by("id")

                    if records.exists():
                        rec = records.first()
                        rec.punch_time = punch_dt
                        rec.status = 1
                        rec.save()

                        # Remove duplicates
                        records.exclude(id=rec.id).delete()

                    else:
                        tenantAttendance.objects.create(
                            user_id=user_id,
                            punch_time=punch_dt,
                            status=1,
                            check_type=1,
                            field1=0, field2=0, field3=0,
                            field4=0, field5=0, field6=0,
                            device_sn=device_sn
                        )

                # ---------- CHECK-OUT ----------
                if iom.check_out:
                    punch_dt = datetime.combine(current_date, iom.check_out)

                    records = tenantAttendance.objects.filter(
                        user_id=user_id,
                        device_sn=device_sn,
                        punch_time__date=current_date,
                        check_type=0
                    ).order_by("id")

                    if records.exists():
                        rec = records.first()
                        rec.punch_time = punch_dt
                        rec.status = 1
                        rec.save()

                        # Remove duplicates
                        records.exclude(id=rec.id).delete()

                    else:
                        tenantAttendance.objects.create(
                            user_id=user_id,
                            punch_time=punch_dt,
                            status=1,
                            check_type=0,
                            field1=0, field2=0, field3=0,
                            field4=0, field5=0, field6=0,
                            device_sn=device_sn
                        )

                current_date += timedelta(days=1)

            iom.approved = True
            iom.save()

            messages.success(
                request,
                "IOM Approved and attendance updated successfully."
            )

        else:
            iom.approved = False
            iom.save()
            messages.success(request, "IOM Rejected.")

        return redirect('iom_list')

    return render(request, 'iom/iom_approval.html', {
        "iom": iom,
        "attendance_preview": attendance_preview,
        "print_time": timezone.now(),
    })



@login_required
def employee_iom_summary(request):
    employee_id = request.GET.get('employee_id')
    year_id = request.GET.get('year_id')
    month_id = request.GET.get('month_id')

    # Validate input
    if not (employee_id and year_id and month_id):
        return HttpResponse("Missing employee_id, year_id or month_id.", status=400)

    try:
        year = int(year_id)
        month = int(month_id)
        employee_id = int(employee_id)
    except ValueError:
        return HttpResponse("Invalid year, month or employee_id.", status=400)

    employee = get_object_or_404(RdaEmployee, id=employee_id)

    # Get the first and last date of the target month
    month_start = date(year, month, 1)
    month_end_day = monthrange(year, month)[1]
    month_end = date(year, month, month_end_day)

    # Filter leaves that overlap with the target month
    iom_records = Iom.objects.filter(
        employee=employee,
        start_date__lte=month_end,
        end_date__gte=month_start
    ).order_by('start_date')

    context = {
        'employee': employee,
        'attendance_records': iom_records,
        'year': year,
        'month': month,
        'print_time': now(),
    }
    return render(request, 'iom/iom_summary.html', context)
    
    
    



### NOte ###
@login_required
def note_list(request):
    employees = RdaEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin')
    note = Note.objects.all().order_by('-id')
    return render(request, 'note/note_list.html', {'notes': note, 'employees': employees})




    
@login_required
def note_apply(request):
    department = request.session.get('department')

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Note applied successfully.")
            return redirect('note_list')
    else:
        form = NoteForm()

    return render(request, 'note/note_form.html', {'form': form, 'title': 'Apply for Note'})



@login_required
def note_edit(request, pk):
    note = get_object_or_404(Iom, pk=pk)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('note_list')
    else:
        form = NoteForm(instance=note)
    return render(request, 'note/note_form.html', {'form': form, 'title': 'Edit Note'})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        log_deleted_data(note, request.user)
        note.delete()
        return redirect('note_list')
    return render(request, 'note/note_confirm_delete.html', {'note': note})



from django.utils import timezone

@login_required
def note_details(request, pk):
    # Allow only admin department
    if request.session.get('department') != 'admin':
        messages.error(request, "You are not authorized to view this note.")
        return redirect('note_list')

    # Fetch the note
    note = get_object_or_404(Note, pk=pk)

    context = {
        'note': note,
        'print_time': timezone.now(),
    }

    return render(request, 'note/note_details.html', context)




@login_required
def attendance_note(request, employee_id):
    # Get all notes for this employee
    employee = get_object_or_404(RdaEmployee, pk=employee_id)
    notes = Note.objects.filter(employee=employee).order_by('-date')

    context = {
        'employee': employee,
        'notes': notes,
        'print_time': timezone.now(),
    }
    return render(request, 'note/note_list_for_employee.html', context)
    
    

@login_required
def employee_iom_summary(request):
    employee_id = request.GET.get('employee_id')
    year_id = request.GET.get('year_id')
    month_id = request.GET.get('month_id')

    # Validate input
    if not (employee_id and year_id and month_id):
        return HttpResponse("Missing employee_id, year_id or month_id.", status=400)

    try:
        year = int(year_id)
        month = int(month_id)
        employee_id = int(employee_id)
    except ValueError:
        return HttpResponse("Invalid year, month or employee_id.", status=400)

    employee = get_object_or_404(RdaEmployee, id=employee_id)

    # Get the first and last date of the target month
    month_start = date(year, month, 1)
    month_end_day = monthrange(year, month)[1]
    month_end = date(year, month, month_end_day)

    # Filter leaves that overlap with the target month
    iom_records = Iom.objects.filter(
        employee=employee,
        start_date__lte=month_end,
        end_date__gte=month_start
    ).order_by('start_date')

    context = {
        'employee': employee,
        'attendance_records': iom_records,
        'year': year,
        'month': month,
        'print_time': now(),
    }
    return render(request, 'iom/iom_summary.html', context)
    
    
    
        
    
    
## -- Edit Permission----
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required

# @login_required
# @permission_required('auth.view_user', raise_exception=True)
# def user_permissions_list(request):
#     users = User.objects.all()
#     return render(request, 'hrm/user_permission_list.html', {'users': users})




#from django.contrib.auth.models import Permission

# @login_required
# @permission_required('auth.change_user', raise_exception=True)
# def edit_user_permissions(request, user_id):
#     user = get_object_or_404(User, pk=user_id)
#     all_permissions = Permission.objects.all()
#     if request.method == 'POST':
#         selected_perms = request.POST.getlist('permissions')
#         user.user_permissions.set(selected_perms)
#         return redirect('user_permissions_list')
#     return render(request, 'hrm/edit_user_permissions.html', {
#         'user_obj': user,
#         'all_permissions': all_permissions,
#         'user_permissions': user.user_permissions.all()
#     })



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_permissions_list(request):
    users = User.objects.all()
    return render(request, 'hrm/user_permission_list.html', {'users': users})

@login_required
@permission_required('auth.change_user', raise_exception=True)
def edit_user_permissions(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    # Select related content_type to group permissions efficiently
    all_permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')
    
    if request.method == 'POST':
        selected_perms = request.POST.getlist('permissions')
        user.user_permissions.set(selected_perms)
        return redirect('user_permissions_list')
        
    return render(request, 'hrm/edit_user_permissions.html', {
        'user_obj': user,
        'all_permissions': all_permissions,
        'user_permissions': user.user_permissions.all()
    })
    

    
## RDA Employee ---
# @login_required
# def rda_employee_list(request):
#     employees = RdaEmployee.objects.all()
#     return render(request, 'rda_employee/rda_employee_list.html', {'employees': employees})


# @login_required
# def rda_employee_list(request):
#     employees = RdaEmployee.objects.filter(
#         rda_active_status=True
#     ).order_by('rda_emp_name')

#     return render(
#         request,
#         'rda_employee/rda_employee_list.html',
#         {'employees': employees}
#     )



## ok code.. -- active/inactive

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .models import RdaEmployee

# @login_required
# def rda_employee_list(request):
#     status_filter = request.GET.get('status', 'active')  # default: active
#     if status_filter == 'inactive':
#         employees = RdaEmployee.objects.filter(rda_active_status=False).order_by('rda_emp_name')
#     else:
#         employees = RdaEmployee.objects.filter(rda_active_status=True).order_by('rda_emp_name')

#     return render(
#         request,
#         'rda_employee/rda_employee_list.html',
#         {'employees': employees, 'status_filter': status_filter}
#     )

# @login_required
# def rda_employee_toggle_status(request, pk):
#     employee = get_object_or_404(RdaEmployee, pk=pk)
#     employee.rda_active_status = not employee.rda_active_status
#     employee.save()

#     state = "Active" if employee.rda_active_status else "Inactive"
#     messages.success(request, f"{employee.rda_emp_name} marked as {state}.")

#     # send them back to the list they were viewing
#     next_url = request.META.get('HTTP_REFERER')
#     return redirect(next_url) if next_url else redirect('rda_employee_list')
    



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RdaEmployee

@login_required
def rda_employee_list(request):
    status_filter = request.GET.get('status', 'active')  # default: active
    
    # Query set sorted by project first (required for regrouping)
    if status_filter == 'inactive':
        employees = RdaEmployee.objects.filter(
            rda_active_status=False
        ).order_by('project_name', 'rda_emp_name')
    else:
        employees = RdaEmployee.objects.filter(
            rda_active_status=True
        ).order_by('project_name', 'rda_emp_name')

    return render(
        request,
        'rda_employee/rda_employee_list.html',
        {'employees': employees, 'status_filter': status_filter}
    )

@login_required
def rda_employee_toggle_status(request, pk):
    employee = get_object_or_404(RdaEmployee, pk=pk)
    employee.rda_active_status = not employee.rda_active_status
    employee.save()

    state = "Active" if employee.rda_active_status else "Inactive"
    messages.success(request, f"{employee.rda_emp_name} marked as {state}.")

    next_url = request.META.get('HTTP_REFERER')
    return redirect(next_url) if next_url else redirect('rda_employee_list')
    
    
@login_required
def rda_employee_add(request):
    if request.method == 'POST':
        form = RdaEmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('rda_employee_list')
    else:
        form = RdaEmployeeForm()

    project_list = ProjectFirstLevelName.objects.all() 

    context = {
        'form': form,
        'project_list': project_list,
    }
    return render(request, 'rda_employee/rda_employee_add.html', context)


@login_required
def rda_employee_edit(request, pk):
    employee = get_object_or_404(RdaEmployee, pk=pk)
    if request.method == 'POST':
        form = RdaEmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('rda_employee_list')
    else:
        form = RdaEmployeeForm(instance=employee)

    project_list = ProjectFirstLevelName.objects.all()
    return render(request, 'rda_employee/rda_employee_edit.html', {
        'form': form,
        'project_list': project_list,
        'employee': employee,  
    })
    
    

@login_required
def rda_employee_delete(request, pk):
    employee = get_object_or_404(RdaEmployee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('rda_employee_list')
    return render(request, 'rda_employee/rda_employee_delete.html', {'employee': employee})






### ADVANCE PAYMENT ###
@login_required
def loanPayment_list(request):
    records = LoanPayment.objects.all()
    return render(request, 'loanpayment/loanPayment_list.html', {'records': records})


@login_required
def loanPayment_add(request):
    if request.method == 'POST':
        form = LoanPaymentForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            # Create DebitVoucher
            debit_voucher = DebitVoucher.objects.create(
                type='Employee', 
                empl_name=str(loanvoucher.employee),
                project_name=loanvoucher.project_name,
                cash_type=loanvoucher.cash_type,
                cheque_number=loanvoucher.cheque_number,
                head_of_account=loanvoucher.head_of_account,  
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                particulars=loanvoucher.reason or "Loan to Employee",
                is_confirmed=True,
                carrier=str(loanvoucher.employee),
                create_dr=str(request.user),
            )
            print('ebitVoucher created:', debit_voucher.id)
            return redirect('loanPayment_list')
    else:
        form = LoanPaymentForm()

    # CORRECT VARIABLE NAME
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')

    return render(request, 'loanpayment/loanPayment_form.html', {
        'form': form,
        'projects': projects,              
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })


    

    
    
    

@login_required
def loanpayment_edit(request, pk):
    record = get_object_or_404(LoanPayment, pk=pk)
    if request.method == 'POST':
        form = LoanPaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('loanPayment_list')
    else:
        form = LoanPaymentForm(instance=record)
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(HeadOfAccount, head_name='Employee Account')
    return render(request, 'loanpayment/loanPayment_form.html', {'form': form, 'projects': projects,'head_of_accounts': [head_of_account], 'today': now().date()})



@login_required
def loanpayment_delete(request, pk):
    record = get_object_or_404(LoanPayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('loanPayment_list')
    return render(request, 'loanpayment/loan_confirm_delete.html', {'record': record})




from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import RdaEmployee, Attendance, AttendanceLocation, AttendanceAccessControl


def public_attendance_hrm(request):
    access = AttendanceAccessControl.objects.first()

    if access:
        employees = access.allowed_employees.filter(rda_active_status=True).order_by('rda_emp_name')
    else:
        employees = RdaEmployee.objects.none()

    if request.method == 'POST':
        punch_type = request.POST.get('punch_type')
        employee_id = request.POST.get('employee_id')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not employee_id:
            messages.error(request, "Please select your name.")
            return redirect('public_attendance_hrm')

        if not latitude or not longitude:
            messages.error(request, "Location not captured. Please allow location access and try again.")
            return redirect('public_attendance_hrm')

        # SECURITY: only allow punch if employee is in the admin's allowed list
        try:
            employee = employees.get(pk=employee_id)
        except RdaEmployee.DoesNotExist:
            messages.error(request, "You are not authorized for attendance. Contact admin.")
            return redirect('public_attendance_hrm')

        today = timezone.localdate()
        now_time = timezone.localtime().time()

        with transaction.atomic():
            existing = (Attendance.objects
                        .select_for_update()
                        .filter(employee=employee, date=today)
                        .first())

            if existing is None:
                attendance = Attendance.objects.create(
                    employee=employee, date=today, att_status='Present'
                )
            else:
                attendance = existing

            location, _ = AttendanceLocation.objects.get_or_create(attendance=attendance)

            if punch_type == 'in':
                if attendance.check_in:
                    messages.warning(
                        request,
                        f"{employee.rda_emp_name} already punched IN today at "
                        f"{attendance.check_in.strftime('%I:%M %p')}."
                    )
                    return redirect('public_attendance_hrm')

                attendance.check_in = now_time
                attendance.att_status = 'Present'
                attendance.save()

                location.check_in_latitude = latitude
                location.check_in_longitude = longitude
                location.save()

                messages.success(
                    request, f"Punch IN recorded for {employee.rda_emp_name} at {now_time.strftime('%I:%M %p')}."
                )

            elif punch_type == 'out':
                if not attendance.check_in:
                    messages.error(request, f"{employee.rda_emp_name} has not punched IN today yet.")
                    return redirect('public_attendance_hrm')

                if attendance.check_out:
                    messages.warning(
                        request,
                        f"{employee.rda_emp_name} already punched OUT today at "
                        f"{attendance.check_out.strftime('%I:%M %p')}."
                    )
                    return redirect('public_attendance_hrm')

                attendance.check_out = now_time
                attendance.save()

                location.check_out_latitude = latitude
                location.check_out_longitude = longitude
                location.save()

                messages.success(
                    request, f"Punch OUT recorded for {employee.rda_emp_name} at {now_time.strftime('%I:%M %p')}."
                )
            else:
                messages.error(request, "Invalid punch type.")

        return redirect('public_attendance_hrm')

    return render(request, 'hrm/public_attendance_hrm.html', {'employees': employees})
    
    
    

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import RdaEmployee, AttendanceAccessControl


@login_required
@permission_required('hrm.change_attendanceaccesscontrol', raise_exception=True)
def manage_attendance_access_hrm(request):
    # Only one access-control record needed; create it if it doesn't exist yet
    access, created = AttendanceAccessControl.objects.get_or_create(
        id=1, defaults={'name': 'BTP Office Attendance Access'}
    )

    all_employees = RdaEmployee.objects.filter(
        rda_active_status=True,
        project_name__project_first_name="BTP Office"
    ).order_by('rda_emp_name')

    allowed_ids = set(access.allowed_employees.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('employee_ids')  # list of checked employee IDs
        access.allowed_employees.set(selected_ids)  # replaces the whole M2M list in one go
        access.save()
        messages.success(request, "Attendance access list updated successfully.")
        return redirect('manage_attendance_access_hrm')

    context = {
        'employees': all_employees,
        'allowed_ids': allowed_ids,
    }
    return render(request, 'hrm/manage_attendance_access_hrm.html', context)
    

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .models import AttendanceLocation

@login_required
# Optional: restrict to users with the specific permission you defined in Meta
@permission_required('your_app_name.can_verify_attendance_location', login_url='denied')
def public_attendance_hrm_check(request):
    # select_related avoids the N+1 query problem for the 1-to-1 and foreign keys
    location_records = AttendanceLocation.objects.select_related(
        'attendance', 
        'attendance__employee',  
        'verified_by'
    ).order_by('-attendance__date')
    context = {
        'location_records': location_records,
    }
    
    return render(request, 'hrm/attendance_locations_list.html', context)
    
    

    
# def public_check_project(request):

#     projects = ProjectFirstLevelName.objects.filter(
#         project_first_name__in=[
#             "BTP Office",
#             "The Galleria Restauent Cafe",
#             "The Galleria Live Kitchen",
#         ]
#     )

#     if request.method == "POST":

#         project_id = request.POST.get("project")

#         project = ProjectFirstLevelName.objects.get(id=project_id)

#         if project.project_first_name == "BTP Office":

#             return redirect("public_hrm_attendance_check")

#         else:

#             return redirect("public_attendance_check")

#     return render(
#         request,
#         "attendance/select_attendance_project.html",
#         {
#             "projects": projects,
#         },
#     )