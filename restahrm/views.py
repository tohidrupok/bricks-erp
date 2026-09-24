from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from calendar import monthrange
from .models import RestaurantLeaveAllocation,RestaurantEmployee,RestaurantSalaryVoucher,RestaurantAttendance, RestaurantFoodBillPayment,RestIom,RestaurantAdvancePayment,RestaurantAllowances,RestaurantSalaryPayment,RestaurantLoanPayment,RestaurantPayroll,RestaurantShiftSchedule
from .forms import RestaurantEmployeeForm,RestaurantSalaryVoucherForm,RestaurantAttendanceForm,RestaurantFoodBillPaymentForm,RestaurantAllowancesForm, RestIomForm, RestaurantLoanPaymentForm,RestaurantAdvancePaymentForm, RestaurantAdvancePaymentForm, RestaurantSalaryPaymentForm,RestaurantAttendanceCheckoutForm,RestaurantShiftScheduleForm
from projects.models import ProjectFirstLevelName
from restaccounting.models import DebitRestVoucher,RestHeadOfAccount,CashRestType,Collection
from django.utils.timezone import now
from datetime import datetime, time,timedelta
from django.utils import timezone
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP,InvalidOperation
from datetime import date
from django.db.models import Sum, Q
from inventories.utils import log_deleted_data
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from .forms import RestaurantSalaryPaymentForm



# @login_required
# def restaurant_employee_list(request):
#     #employees = RestaurantEmployee.objects.all()
#     employees = RestaurantEmployee.objects.filter(
#         rda_active_status=True
#     ).order_by('rda_emp_name')
#     return render(request, 'restaurant_employee/rest_employee_list.html', {'employees': employees})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RestaurantEmployee

@login_required
def restaurant_employee_list(request):
    status_filter = request.GET.get('status', 'active')

    # Order by project_name first to ensure {% regroup %} works correctly
    if status_filter == 'inactive':
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=False
        ).order_by('project_name', 'rda_emp_name')
    else:
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True
        ).order_by('project_name', 'rda_emp_name')

    context = {
        'employees': employees,
        'status_filter': status_filter
    }
    return render(request, 'restaurant_employee/rest_employee_list.html', context)


@login_required
def restaurant_employee_toggle_status(request, pk):
    employee = get_object_or_404(RestaurantEmployee, pk=pk)
    employee.rda_active_status = not employee.rda_active_status
    employee.save()

    state = "Active" if employee.rda_active_status else "Inactive"
    messages.success(request, f"{employee.rda_emp_name} marked as {state}.")

    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    
    status_param = 'active' if employee.rda_active_status else 'inactive'
    return redirect(f"{redirect('restaurant_employee_list').url}?status={status_param}")
    
    
    
@login_required
def restaurant_employee_add(request):
    if request.method == 'POST':
        form = RestaurantEmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('restaurant_employee_list')
    else:
        form = RestaurantEmployeeForm()

    #project_list = ProjectFirstLevelName.objects.all() 
    project_list = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    context = {
        'form': form,
        'project_list': project_list,
    }
    return render(request, 'restaurant_employee/rest_employee_add.html', context)


@login_required
def restaurant_employee_edit(request, pk):
    employee = get_object_or_404(RestaurantEmployee, pk=pk)
    if request.method == 'POST':
        form = RestaurantEmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('restaurant_employee_list')
    else:
        form = RestaurantEmployeeForm(instance=employee)
    
    project_list = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )
    return render(request, 'restaurant_employee/rest_employee_edit.html', {
        'form': form,
        'project_list': project_list,
        'employee': employee,  
    })
    
    

@login_required
def restaurant_employee_delete(request, pk):
    employee = get_object_or_404(RestaurantEmployee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('restaurant_employee_list')
    return render(request, 'restaurant_employee/rest_employee_delete.html', {'employee': employee})
    
    
    
# @login_required
# def restaurant_employee_details(request):
#     employees = RestaurantEmployee.objects.all()
#     projects_firts = ProjectFirstLevelName.objects.all()
#     return render(request, 'restaurant_employee/restaurant_employee_details.html', {'employees': employees, 'projects_firts': projects_firts})


@login_required
def restaurant_employee_details(request):
    employees = RestaurantEmployee.objects.filter(
        rda_active_status=True
    ).order_by('rda_emp_name')
    projects_firts = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )
    return render(request, 'restaurant_employee/restaurant_employee_details.html', {'employees': employees, 'projects_firts': projects_firts})




@login_required
def restaurant_employee_project_details(request):
    project_id = request.GET.get("project_id")

    if project_id:
        employees = RestaurantEmployee.objects.filter(project_name_id=project_id)
    else:
        employees = RestaurantEmployee.objects.all()

    projects_firts = ProjectFirstLevelName.objects.all()

    return render(
        request,
        "restaurant_employee/restaurant_employee_details.html",
        {
            "employees": employees,
            "projects_firts": projects_firts,
            "selected_project": project_id,
        },
    )
    
    
    
    
@login_required
def restaurant_monthly_salary_generate(request):
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
    voucher, created = RestaurantSalaryVoucher.objects.get_or_create(
        project=project,
        month_name=full_month_label,
        defaults={"approval_salary_status": "Pending"},
    )

    # --- Employees ---
    employees = RestaurantEmployee.objects.filter(rda_active_status=True)
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
    return render(request, "restaurant/salary/monthly_salary_report.html", {
        "employee_groups": dict(employee_groups),
        "grand_total_salary": grand_total_salary,
        "print_time": today,
        "month_name": full_month_label,
        "project_name": project_name,
        "voucher": voucher,
        "project_id": project_id,   # always safe
    })




from urllib.parse import unquote
@login_required
def restaurant_approve_salary_generate(request, project_id, month_name):
    # Decode URL-encoded month_name (e.g., "September%202025")
    month_name = unquote(month_name)

    # Get the project
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # Update or create SalaryVoucher
    voucher, created = RestaurantSalaryVoucher.objects.get_or_create(
        project=project,
        month_name=month_name,
        defaults={
            "approval_salary_status": "Approved",
            "generate_date": timezone.now(),
        }
    )

    if not created:
        # Already exists â†’ just update status
        voucher.approval_salary_status = "Approved"
        voucher.generate_date = timezone.now()
        voucher.save()

    # Redirect back to monthly_salary_generate with the same project & month parameters
    return redirect(f"/dashboard/restaurant/monthly-salary-report/?project={project_id}&month={month_name.split()[0]}")


  
  

# from datetime import datetime, date, time, timedelta
# from django.utils import timezone
# from restahrm.models import RestaurantEmployee, RestaurantAttendance
# from tenant.models import Attendance as TenantAttendance

# @login_required
# def restaurant_attendance_list(request):
#     # ------------------ Selected date -------------------
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


#     # ------------------ Active restaurant employees -------------------
#     employees = (
#         RestaurantEmployee.objects.filter(rda_active_status=True)
#         .exclude(rda_emp_type__iexact="admin")
#         .exclude(rda_emp_name__iexact="Admin")
#     )

#     # ------------------ Get punches from tenant system -------------------
#     # punches = TenantAttendance.objects.filter(
#     #     punch_time__date=selected_date,
#     #     device_sn="SMR5253000079"  
#     # ).order_by("id")
#     punches = TenantAttendance.objects.filter(
#         punch_time__date=selected_date,
#         device_sn__in=[
#             "SMR5253000079",
#             "SMR5253000181"
#         ]
#     ).order_by("id")

#     # ------------------ Map tenant punches to employee attendance -------------------
#     for emp in employees:
#         emp_punches = punches.filter(user_id=emp.id)
#         if emp_punches.exists():
#             first_punch = timezone.localtime(emp_punches.first().punch_time)
#             last_punch = timezone.localtime(emp_punches.last().punch_time)

#             check_in = first_punch.time()
#             check_out = last_punch.time() if emp_punches.count() > 1 else time(0, 0)

#             # Get or create restaurant attendance record
#             r_att, created = RestaurantAttendance.objects.get_or_create(
#                 employee=emp,
#                 date=selected_date,
#                 defaults={
#                     "check_in": check_in,
#                     "check_out": check_out,
#                     "att_status": "Present",
#                 }
#             )

#             if not created:
#                 r_att.check_in = check_in
#                 r_att.check_out = check_out
#                 r_att.att_status = "Present"
#                 r_att.save()
#         else:
#             # Mark absent if no punches
#             if not RestaurantAttendance.objects.filter(employee=emp, date=selected_date).exists():
#                 RestaurantAttendance.objects.create(
#                     employee=emp,
#                     date=selected_date,
#                     att_status="Absent"
#                 )

#     # ------------------ Build attendance list for template -------------------
#     records = RestaurantAttendance.objects.filter(date=selected_date).select_related("employee")

#     for r in records:
#         # Determine shift-specific expected times
#         emp_shift = (r.emp_shift or "Morning").strip().lower()
#         if emp_shift == "morning":
#             expected_checkin = time(10, 40)
#         elif emp_shift == "evening":
#             expected_checkin = time(13, 15)
#         else:
#             expected_checkin = time(10, 40)

#         expected_checkout = time(23, 59)

#         # Late check-in
#         r.is_late = bool(r.check_in and r.check_in > expected_checkin)
#         # Left early
#         r.left_early = bool(r.check_out and r.check_out < expected_checkout)

#         # Duration
#         if r.check_in and r.check_out and r.check_out != time(0, 0):
#             in_dt = datetime.combine(selected_date, r.check_in)
#             out_dt = datetime.combine(selected_date, r.check_out)
#             if out_dt < in_dt:
#                 out_dt += timedelta(days=1)
#             diff = out_dt - in_dt
#             hours, remainder = divmod(diff.total_seconds(), 3600)
#             minutes, _ = divmod(remainder, 60)
#             r.duration = f"{int(hours)}h {int(minutes)}m"
#         else:
#             r.duration = "-"

#     projects_first = ProjectFirstLevelName.objects.all()

#     return render(
#         request,
#         "restaurant/attendance/attendance_list.html",
#         {
#             "records": records,
#             "employees": employees,
#             "projects_firts": projects_first,
#             "selected_date": selected_date.isoformat(),
#         }
#     )



from datetime import datetime, date, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from restahrm.models import RestaurantEmployee, RestaurantAttendance
from tenant.models import Attendance as TenantAttendance
from projects.models import ProjectFirstLevelName


@login_required
def restaurant_attendance_list(request):
    # ------------------ Selected date -------------------
    selected_date_str = request.GET.get("date")
    today = date.today()
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # ------------------ Only these two projects are shown / filterable -------------
    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    # ------------------ Project filter selected on the page (?project_id=) --------
    selected_project_id = request.GET.get("project_id") or ""

    # ------------------ Active restaurant employees, in the two projects only -----
    employees = (
        RestaurantEmployee.objects.filter(
            rda_active_status=True,
            project_name__in=projects_first,
        )
        .exclude(rda_emp_type__iexact="admin")
        .exclude(rda_emp_name__iexact="Admin")
    )

    if selected_project_id:
        employees = employees.filter(project_name_id=selected_project_id)

    # ------------------ Get punches from tenant system -------------------
    punches = TenantAttendance.objects.filter(
        punch_time__date=selected_date,
        device_sn__in=[
            "SMR5253000079",
            "SMR5253000181"
        ]
    ).order_by("id")

    # ------------------ Map tenant punches to employee attendance -------------------
    for emp in employees:
        emp_punches = punches.filter(user_id=emp.id)
        if emp_punches.exists():
            first_punch = timezone.localtime(emp_punches.first().punch_time)
            last_punch = timezone.localtime(emp_punches.last().punch_time)

            check_in = first_punch.time()
            check_out = last_punch.time() if emp_punches.count() > 1 else time(0, 0)

            # Get or create restaurant attendance record
            r_att, created = RestaurantAttendance.objects.get_or_create(
                employee=emp,
                date=selected_date,
                defaults={
                    "check_in": check_in,
                    "check_out": check_out,
                    "att_status": "Present",
                }
            )

            if not created:
                r_att.check_in = check_in
                r_att.check_out = check_out
                r_att.att_status = "Present"
                r_att.save()
        else:
            # Mark absent if no punches
            if not RestaurantAttendance.objects.filter(employee=emp, date=selected_date).exists():
                RestaurantAttendance.objects.create(
                    employee=emp,
                    date=selected_date,
                    att_status="Absent"
                )

    # ------------------ Build attendance list for template -------------------
    # Only active employees inside the two allowed projects (and the selected
    # project, if filtered) ever show up here.
    # records = (
    #     RestaurantAttendance.objects.filter(
    #         date=selected_date,
    #         employee__in=employees,
    #     )
    #     .select_related("employee")
    #     .order_by("employee__rda_emp_name")
    # )
    records = (
        RestaurantAttendance.objects.filter(
            date=selected_date,
            employee__in=employees,
            employee__rda_active_status=True,   # ← explicit safety filter
        )
        .select_related("employee")
        .order_by("employee__rda_emp_name")
    )

    for r in records:
        emp_shift = (r.employee.rda_shift or "Morning").strip().lower()
        if emp_shift == "morning":
            expected_checkin = time(10, 40)
        elif emp_shift == "evening":
            expected_checkin = time(13, 15)
        else:
            expected_checkin = time(10, 40)

        expected_checkout = time(23, 59)

        # Late check-in
        r.is_late = bool(r.check_in and r.check_in > expected_checkin)
        # Left early
        r.left_early = bool(r.check_out and r.check_out < expected_checkout)

        # Duration
        if r.check_in and r.check_out and r.check_out != time(0, 0):
            in_dt = datetime.combine(selected_date, r.check_in)
            out_dt = datetime.combine(selected_date, r.check_out)
            if out_dt < in_dt:
                out_dt += timedelta(days=1)
            diff = out_dt - in_dt
            hours, remainder = divmod(diff.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            r.duration = f"{int(hours)}h {int(minutes)}m"
        else:
            r.duration = "-"

    return render(
        request,
        "restaurant/attendance/attendance_list.html",
        {
            "records": records,
            "employees": employees,
            "projects_firts": projects_first,
            "selected_date": selected_date.isoformat(),
            "selected_project_id": selected_project_id,
        }
    )


@login_required
def shift_list(request):
    shifts = RestaurantShiftSchedule.objects.all()
    return render(request, "shift/shift_list.html", {"shifts": shifts})





@login_required
def shift_add(request):
    if request.method == "POST":
        form = RestaurantShiftScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Shift added successfully!")
            return redirect("shift_list")
    else:
        form = RestaurantShiftScheduleForm()

    return render(request, "shift/shift_add.html", {"form": form})




@login_required
def shift_edit(request, pk):
    shift = get_object_or_404(RestaurantShiftSchedule, pk=pk)

    if request.method == "POST":
        form = RestaurantShiftScheduleForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, "Shift updated successfully!")
            return redirect("shift_list")
    else:
        form = RestaurantShiftScheduleForm(instance=shift)

    return render(request, "shift/shift_edit.html", {"form": form, "shift": shift})



@login_required
def shift_delete(request, pk):
    shift = get_object_or_404(RestaurantShiftSchedule, pk=pk)
    shift.delete()
    messages.success(request, "Shift deleted successfully!")
    return redirect("shift_list")



    


@login_required
def restaurant_attendance_create(request):
    if request.method == 'POST':
        form = RestaurantAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurant_attendance_list')
    else:
        form = RestaurantAttendanceForm()
    return render(request, 'restaurant/attendance/attendance_form.html', {'form': form})
    


@login_required
def restaurant_attendance_edit(request, pk):
    record = get_object_or_404(RestaurantAttendance, pk=pk)

    if request.method == 'POST':
        form = RestaurantAttendanceForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save()
            selected_date = updated_record.date.strftime("%Y-%m-%d")
            return redirect(f"/dashboard/restaurant/attendance/?date={selected_date}")
    else:
        form = RestaurantAttendanceForm(instance=record)

    return render(request, 'restaurant/attendance/attendance_edit.html', {'form': form})



@login_required
def restaurant_attendance_delete(request, pk):
    record = get_object_or_404(RestaurantAttendance, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('restaurant_attendance_list')
    return render(request, 'restaurant/attendance/attendance_confirm_delete.html', {'record': record})



@login_required
def RestaurantAttendanceCheckoutUpdateView(request, pk):
    attendance = get_object_or_404(RestaurantAttendance, pk=pk)

    if request.method == "POST":
        form = RestaurantAttendanceCheckoutForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('restaurant_attendance_list')  # replace with your attendance list URL name
    else:
        form = RestaurantAttendanceCheckoutForm(instance=attendance)

    return render(request, 'attendance/restaurant_attendance_checkout_update.html', {'form': form, 'attendance': attendance})
    
    
    
    
    
@login_required
def restaurant_employee_attendance_summary(request):
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
    attendance_records = RestaurantAttendance.objects.filter(
        date__year=year,
        date__month=month,
        employee__project_name=project
    ).order_by('date')

    employee = None
    if employee_id:  # If employee_id is provided
        employee = get_object_or_404(RestaurantEmployee, id=employee_id, project_name=project)
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
    return render(request, "restaurant/attendance/attendance_summary.html", context)



@login_required
def restaurant_advance_list(request):
    records = RestaurantAdvancePayment.objects.all()
    return render(request, 'restaurant/advancepayment/advance_list.html', {'records': records})
    
    
    
# @login_required
# def restaurant_advance_create(request):
#     if request.method == 'POST':
#         form = RestaurantAdvancePaymentForm(request.POST)
#         if form.is_valid():
#             loanvoucher = form.save(commit=False)
#             loanvoucher.save()

#             # Ensure RestHeadOfAccount exists
#             rest_head, created = RestHeadOfAccount.objects.get_or_create(
#                 head_name=loanvoucher.head_of_account.head_name
#             )
            
#             debit_voucher = DebitRestVoucher.objects.create(
#                 type='Employee',
#                 empl_name=str(loanvoucher.employee),
#                 project_name=loanvoucher.project_name,
#                 cash_type=loanvoucher.cash_type,
#                 cheque_number=loanvoucher.cheque_number,
#                 head_of_account=rest_head,
#                 amount=loanvoucher.amount,
#                 date=loanvoucher.date or timezone.now().date(),
#                 particulars=loanvoucher.reason or "Advance to Employee",
#                 is_confirmed=True,
#                 carrier=str(loanvoucher.employee),
#                 create_dr=str(request.user),
#             )

#             print('DebitVoucher created:', debit_voucher.id)
#             return redirect('restaurant_advance_list')
#     else:
#         form = RestaurantAdvancePaymentForm()

#     projects = ProjectFirstLevelName.objects.all()
#     head_of_account = get_object_or_404(
#         RestHeadOfAccount,
#         head_name='Employee Account'
#     )

#     return render(request, 'restaurant/advancepayment/advance_form.html', {
#         'form': form,
#         'projects': projects,
#         'head_of_accounts': [head_of_account],
#         'today': now().date(),
#     })

    
    
    
# @login_required
# def restuarant_advance_edit(request, pk):
#     record = get_object_or_404(RestaurantAdvancePayment, pk=pk)
#     if request.method == 'POST':
#         form = RestaurantAdvancePaymentForm(request.POST, instance=record)
#         if form.is_valid():
#             form.save()
#             return redirect('restaurant_advance_list')
#     else:
#         form = RestaurantAdvancePaymentForm(instance=record)
#     projects = ProjectFirstLevelName.objects.all()
#     head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')
#     return render(request, 'restaurant/advancepayment/advance_form.html', {'form': form, 'projects': projects,'head_of_accounts': [head_of_account]})



@login_required
def restaurant_advance_create(request):
    if request.method == 'POST':
        form = RestaurantAdvancePaymentForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            rest_head, created = RestHeadOfAccount.objects.get_or_create(
                head_name=loanvoucher.head_of_account.head_name
            )

            debit_voucher = DebitRestVoucher.objects.create(
                type='Employee',
                empl_name=str(loanvoucher.employee),
                project_name=loanvoucher.project_name,
                cash_type=loanvoucher.cash_type,
                cheque_number=loanvoucher.cheque_number,
                head_of_account=rest_head,
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                particulars=loanvoucher.reason or "Advance to Employee",
                is_confirmed=True,
                carrier=str(loanvoucher.employee),
                create_dr=str(request.user),
                requi_id=loanvoucher.id,
            )

            # link voucher
            loanvoucher.debit_voucher_id = debit_voucher.id
            loanvoucher.save()

            return redirect('restaurant_advance_list')

    else:
        form = RestaurantAdvancePaymentForm()

    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(
        RestHeadOfAccount,
        head_name='Employee Account'
    )

    return render(request, 'restaurant/advancepayment/advance_form.html', {
        'form': form,
        'projects': projects,
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })



@login_required
def restuarant_advance_edit(request, pk):
    record = get_object_or_404(RestaurantAdvancePayment, pk=pk)

    if request.method == 'POST':
        form = RestaurantAdvancePaymentForm(request.POST, instance=record)

        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            # Ensure correct RestHeadOfAccount
            rest_head, created = RestHeadOfAccount.objects.get_or_create(
                head_name=loanvoucher.head_of_account.head_name
            )

            # ✅ Get voucher using ID (IMPORTANT)
            voucher_id = loanvoucher.id

            if voucher_id:
                voucher = DebitRestVoucher.objects.get(requi_id=voucher_id)

                # ✅ Update voucher fields
                voucher.type = 'Employee'
                voucher.empl_name = str(loanvoucher.employee)
                voucher.project_name = loanvoucher.project_name
                voucher.cash_type = loanvoucher.cash_type
                voucher.cheque_number = loanvoucher.cheque_number
                voucher.head_of_account = rest_head
                voucher.amount = loanvoucher.amount
                voucher.date = loanvoucher.date or timezone.now().date()
                voucher.particulars = loanvoucher.reason or "Advance to Employee"
                voucher.is_confirmed = True
                voucher.carrier = str(loanvoucher.employee)
                voucher.create_dr = str(request.user)

                voucher.save(update_fields=[
                    'type','empl_name','project_name','cash_type','cheque_number',
                    'head_of_account','amount','date','particulars',
                    'is_confirmed','carrier','create_dr'
                ])

            return redirect('restaurant_advance_list')

    else:
        form = RestaurantAdvancePaymentForm(instance=record)

    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(
        RestHeadOfAccount,
        head_name='Employee Account'
    )

    return render(
        request,
        'restaurant/advancepayment/advance_form.html',
        {
            'form': form,
            'projects': projects,
            'head_of_accounts': [head_of_account]
        }
    )





# @login_required
# def restuarant_advance_delete(request, pk):
#     record = get_object_or_404(RestaurantAdvancePayment, pk=pk)
#     if request.method == 'POST':
#         log_deleted_data(record, request.user)
#         record.delete()
#         return redirect('restaurant_advance_list')
#     return render(request, 'restaurant/advancepayment/advance_confirm_delete.html', {'record': record})
    

from django.db import transaction

@login_required
def restuarant_advance_delete(request, pk):
    record = get_object_or_404(RestaurantAdvancePayment, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():

            # log first
            log_deleted_data(record, request.user)

            # ✅ delete linked voucher using requi_id
            DebitRestVoucher.objects.filter(requi_id=record.id).delete()

            # ✅ delete main record
            record.delete()

        return redirect('restaurant_advance_list')

    return render(
        request,
        'restaurant/advancepayment/advance_confirm_delete.html',
        {'record': record}
    )


    

@login_required
def restaurant_payroll_list(request):
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
    employees = RestaurantEmployee.objects.filter(rda_active_status=True)
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
        allowances = RestaurantAllowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # Attendance
        present_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Present'
        ).count()

        leave_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Absent'
        ).count()

        absent_days = days_in_month - (present_days + leave_days)

        # Salary calculation
        daily_salary = (rda_salary / Decimal(days_in_month)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        basic_salary = (daily_salary * Decimal(present_days + leave_days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Advance deductions
        deductions = RestaurantAdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # ðŸ”¹ Loan Payments (with start_month, end_month, and month_name validation)
        loans_qs = RestaurantLoanPayment.objects.filter(
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
        RestaurantPayroll.objects.update_or_create(
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

    #projects_first = RestaurantEmployee.objects.all()
    projects_first = ProjectFirstLevelName.objects.all()
    selected_project_obj = RestaurantEmployee.objects.filter(id=project_id).first() if project_id else None

    return render(request, 'restaurant/payroll/payroll_list.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'default_month': default_month_str,
        'default_year': default_year,
        'employees': employees,
        #'projects_first': projects_first,
        'projects_first': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_deductions': total_deductions,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
        'selected_project': selected_project_obj,
    })



    



# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP
# from django.db.models import Sum
# from django.utils import timezone


# @login_required
# def restaurant_payroll_print(request):
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

#     # Filter employees
#     if project_id and project_id.isdigit():
#         employees = RestaurantEmployee.objects.filter(
#             rda_active_status=True,
#             project_name_id=int(project_id)
#         ).exclude(rda_emp_name__iexact='admin')
#     else:
#         employees = RestaurantEmployee.objects.filter(
#             rda_active_status=True
#         ).exclude(rda_emp_name__iexact='admin')

#     # Special payable days
#     SPECIAL_PAYABLE_DAYS = {
#         2: 30, 27: 30, 3: 30, 5: 30, 7: 30, 8: 30,
#         47: 30, 10: 30, 11: 30, 26: 30,24:30,
#         13: 30, 14: 30, 34: 30, 52:30,
#         33: 30, 25: 30, 56: 30, 57: 30, 58: 30,
#         1:30, 35:30, 36:30, 37:30, 38:30, 39:30,
#         40:30, 42:30, 44:30, 45:30, 46:30, 49:30, 54:30,
#         59:30, 60:30,61:30,62:30,67:30,68:30, 69:30,71:30,72:30,74:30,76:30,77:30,78:30,79:30,80:30,
#         81:30,82:30,83:30,84:30,85:30,86:30,87:30,
        
#     }
#     # SPECIAL_PAYABLE_DAYS = {
#     #     0: 0
        
#     # }
#     # SPECIAL_PAYABLE_DAYS = {
#     #     0: 0
        
#     # }
#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)

#         # ========================
#         # ATTENDANCE
#         # ========================
#         present_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Present'
#         ).values('date').distinct().count()

#         leave_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Leave'
#         ).values('date').distinct().count()

#         off_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Off Day'
#         ).values('date').distinct().count()

#         absent_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Absent'
#         ).values('date').distinct().count()

#         attendance_days = days_in_month - absent_days

#         if emp.id in SPECIAL_PAYABLE_DAYS:
#             attendance_days = SPECIAL_PAYABLE_DAYS[emp.id]

#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')

#         basic_salary = (daily_salary * attendance_days).quantize(
#             Decimal('0.01'),
#             rounding=ROUND_HALF_UP
#         )

#         # ========================
#         # RESTAURANT ALLOWANCE (ADD)
#         # ========================
#         allowances = RestaurantAllowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # ========================
#         # ADVANCE (SUBTRACT)
#         # ========================
#         total_advance = RestaurantAdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
#         # ========================
#         # Foodbill (SUBTRACT)
#         # ========================
#         total_foodPay = RestaurantFoodBillPayment.objects.filter(
#             employee=emp,
#             customer_type='Employee',
#             date__range=(start_date, end_date)
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
#         # ========================
#         # LOAN (SUBTRACT)
#         # ========================
#         loans_qs = RestaurantLoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal('0')

#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal('0')

#         # ========================
#         # NET SALARY
#         # ========================
#         net_salary = (
#             basic_salary +
#             allowances -
#             total_advance -
#             total_foodPay -
#             total_loan_deduction
#         ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

#         # Save payroll
#         RestaurantPayroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances + allowances,
#                 'deductions': total_advance + total_foodPay + total_loan_deduction,
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
#             'basic_salary': basic_salary + allowances,
#             'allowances': allowances,
#             'advance_amount': total_advance,
#             'foodPay_amount': total_foodPay,
#             'loan_amount': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     # ========================
#     # TOTALS
#     # ========================
#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['advance_amount'] for item in payroll_data)
#     total_foodPay = sum(item['foodPay_amount'] for item in payroll_data)
#     total_loans = sum(item['loan_amount'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     # ✅ TOTAL MONTHLY SALARY COLUMN
#     total_rda_salary = sum(
#         Decimal(item['employee'].rda_salary or 0)
#         for item in payroll_data
#     )

#     return render(request, 'restaurant/payroll/payroll_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_foodPay': total_foodPay,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'total_rda_salary': total_rda_salary,  # ✅ ADDED
#         'print_time': timezone.now(),
#     })
    
    
    
## ok code...is ---

# from datetime import datetime
# from calendar import monthrange
# from decimal import Decimal, ROUND_HALF_UP
# from django.db.models import Sum
# from django.utils import timezone


# @login_required
# def restaurant_payroll_print(request):
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

#     # Filter employees
#     if project_id and project_id.isdigit():
#         employees = RestaurantEmployee.objects.filter(
#             rda_active_status=True,
#             project_name_id=int(project_id)
#         ).exclude(rda_emp_name__iexact='admin')
#     else:
#         employees = RestaurantEmployee.objects.filter(
#             rda_active_status=True
#         ).exclude(rda_emp_name__iexact='admin')

#     # Special payable days
#     # SPECIAL_PAYABLE_DAYS = {
#     #     2: 30, 27: 30, 3: 30, 5: 30, 7: 30, 8: 30,
#     #     47: 30, 10: 30, 11: 30, 26: 30,24:30,
#     #     13: 30, 14: 30, 34: 30, 52:30,
#     #     33: 30, 25: 30, 56: 30, 57: 30, 58: 30,
#     #     1:30, 35:30, 36:30, 37:30, 38:30, 39:30,
#     #     40:30, 42:30, 44:30, 45:30, 46:30, 49:30, 54:30,
#     #     59:30, 60:30,61:30,62:30,67:30,68:30, 69:30,71:30,72:30,74:30,76:30,77:30,78:30,79:30,80:30,
#     #     81:30,82:30,83:30,84:30,85:30,86:30,87:30,
        
#     # }
    
#     # SPECIAL_PAYABLE_DAYS = {
#     #     7: 31, 39:31, 54:31, 59:31, 67:31, 74:31, 81:31, 87:31
        
#     # }
#     if selected_month_dt.month == 7:
#         # SPECIAL_PAYABLE_DAYS = {
#         #     7: 31, 39: 31, 54: 31, 59: 31, 67: 31, 74: 31, 81: 31, 87: 31
#         # }
#         SPECIAL_PAYABLE_DAYS = {
#             2: 31, 27: 31, 3: 31, 5: 31, 7: 31, 8: 31,
#             47: 31, 10: 31, 11: 31, 26: 31, 24: 31,
#             13: 31, 14: 31, 34: 31, 52: 31,
#             33: 31, 25: 31, 56: 31, 57: 31, 58: 31,
#             1: 31, 35: 31, 36: 31, 37: 31, 38: 31, 39: 31,
#             40: 31, 42: 15, 44: 31, 45: 31, 46: 31, 49: 31, 54: 31,
#             59: 31, 60: 31, 61: 31, 62: 31, 67: 31, 68: 31, 69: 31, 71: 31, 72: 31, 74: 31, 76: 31, 77: 31, 78: 31, 79: 31, 80: 31,
#             81: 31, 82: 31, 83: 31, 84: 31, 85: 31, 86: 31, 87: 31,
#         }
#     else:
#         SPECIAL_PAYABLE_DAYS = {}
    
#     for emp in employees:
#         rda_salary = Decimal(emp.rda_salary or 0)

#         # ========================
#         # ATTENDANCE
#         # ========================
#         present_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Present'
#         ).values('date').distinct().count()

#         leave_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Leave'
#         ).values('date').distinct().count()

#         off_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Off Day'
#         ).values('date').distinct().count()

#         absent_days = RestaurantAttendance.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             att_status='Absent'
#         ).values('date').distinct().count()

#         attendance_days = days_in_month - absent_days

#         if emp.id in SPECIAL_PAYABLE_DAYS:
#             attendance_days = SPECIAL_PAYABLE_DAYS[emp.id]

#         daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')

#         basic_salary = (daily_salary * attendance_days).quantize(
#             Decimal('0.01'),
#             rounding=ROUND_HALF_UP
#         )

#         # ========================
#         # RESTAURANT ALLOWANCE (ADD)
#         # ========================
#         allowances = RestaurantAllowances.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # ========================
#         # ADVANCE (SUBTRACT)
#         # ========================
#         total_advance = RestaurantAdvancePayment.objects.filter(
#             employee=emp,
#             date__range=(start_date, end_date),
#             status='due'
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
#         # ========================
#         # Foodbill (SUBTRACT)
#         # ========================
#         # total_foodPay = RestaurantFoodBillPayment.objects.filter(
#         #     employee=emp,
#         #     customer_type='Employee',
#         #     date__range=(start_date, end_date)
#         # ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
#         # ================================================================
#         # 🍔 Foodbill & Employee Collection Deductions (SUBTRACT)
#         # ================================================================
#         # 1. Fetch from the legacy RestaurantFoodBillPayment table
#         legacy_food_pay = RestaurantFoodBillPayment.objects.filter(
#             employee=emp,
#             customer_type='Employee',
#             date__range=(start_date, end_date)
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
#         # 2. Fetch from your new accounting Collection table (Filter: type='Employee')
#         collection_food_pay = Collection.objects.filter(
#             employee=emp,
#             type='Employee',
#             date__range=(start_date, end_date)
#         ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         # 3. Combine both values cleanly so no data is dropped
#         total_foodPay = legacy_food_pay + collection_food_pay
        
#         # ========================
#         # LOAN (SUBTRACT)
#         # ========================
#         loans_qs = RestaurantLoanPayment.objects.filter(
#             employee=emp,
#             status='due',
#             start_month__lte=end_date,
#             end_month__gte=start_date
#         )

#         total_loan_deduction = Decimal('0')

#         for loan in loans_qs:
#             if loan.month_name and selected_month in loan.month_name:
#                 total_loan_deduction += loan.deduction_amount or Decimal('0')

#         # ========================
#         # NET SALARY
#         # ========================
#         net_salary = (
#             basic_salary +
#             allowances -
#             total_advance -
#             total_foodPay -
#             total_loan_deduction
#         ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

#         # Save payroll
#         RestaurantPayroll.objects.update_or_create(
#             employee=emp,
#             month=selected_month,
#             year=year_input,
#             defaults={
#                 'basic_salary': basic_salary,
#                 'allowances': allowances + allowances,
#                 'deductions': total_advance + total_foodPay + total_loan_deduction,
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
#             'basic_salary': basic_salary + allowances,
#             'allowances': allowances,
#             'advance_amount': total_advance,
#             'foodPay_amount': total_foodPay,
#             'loan_amount': total_loan_deduction,
#             'net_salary': net_salary,
#         })

#     # ========================
#     # TOTALS
#     # ========================
#     total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
#     total_allowances = sum(item['allowances'] for item in payroll_data)
#     total_advance = sum(item['advance_amount'] for item in payroll_data)
#     total_foodPay = sum(item['foodPay_amount'] for item in payroll_data)
#     total_loans = sum(item['loan_amount'] for item in payroll_data)
#     total_net_salary = sum(item['net_salary'] for item in payroll_data)

#     # ✅ TOTAL MONTHLY SALARY COLUMN
#     total_rda_salary = sum(
#         Decimal(item['employee'].rda_salary or 0)
#         for item in payroll_data
#     )

#     return render(request, 'restaurant/payroll/payroll_print.html', {
#         'payrolls': payroll_data,
#         'month': selected_month,
#         'year': year_input,
#         'default_month': default_month_str,
#         'default_year': default_year,
#         'total_basic_salary': total_basic_salary,
#         'total_allowances': total_allowances,
#         'total_advance': total_advance,
#         'total_foodPay': total_foodPay,
#         'total_loans': total_loans,
#         'total_net_salary': total_net_salary,
#         'total_rda_salary': total_rda_salary,  # ✅ ADDED
#         'print_time': timezone.now(),
#     })
    



from datetime import datetime
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from django.utils import timezone


@login_required
def restaurant_payroll_print(request):
    today = datetime.today()
    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    month_input = request.GET.get('month', default_month_str)
    year_input_str = request.GET.get('year', str(default_year))
    project_id = request.GET.get('project_id')

    # Parse year
    try:
        year_input = int(year_input_str)
    except ValueError:
        year_input = default_year

    # Parse month
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

    # Filter employees
    if project_id and project_id.isdigit():
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True,
            project_name_id=int(project_id)
        ).exclude(rda_emp_name__iexact='admin')
    else:
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True
        ).exclude(rda_emp_name__iexact='admin')

    # Special payable days mapping
    if selected_month_dt.month == 7:
        SPECIAL_PAYABLE_DAYS = {
            2: 31, 27: 31, 3: 31, 5: 31, 7: 31, 8: 31,
            47: 31, 10: 31, 11: 31, 26: 31, 24: 31,
            13: 31, 14: 31, 34: 31, 52: 31,
            33: 31, 25: 31, 56: 31, 57: 31, 58: 31,
            1: 31, 35: 31, 36: 31, 37: 31, 38: 31, 39: 31,
            40: 31, 42: 15, 44: 31, 45: 31, 46: 31, 49: 31, 53:31, 54: 31,
            59: 31, 60: 31, 61: 31, 62: 31, 67: 31, 68: 31, 69: 31, 71: 31, 72: 31, 74: 31, 76: 31, 77: 31, 78: 31, 79: 31, 80: 31,
            81: 31, 82: 31, 83: 31, 84: 31, 85: 31, 86: 31, 87: 31,88:31,90:31,91:31,96:31,98:31,100:31,101:31
        }
    else:
        SPECIAL_PAYABLE_DAYS = {}

    # Manual Gross Salary Overrides (Employee ID -> Fixed Salary Amount)
    MANUAL_SALARY_OVERRIDES = {
        102: Decimal('12500.00'),
    }
    
    for emp in employees:
        # Check if manual override exists for this employee ID
        is_overridden = emp.id in MANUAL_SALARY_OVERRIDES
        
        if is_overridden:
            rda_salary = MANUAL_SALARY_OVERRIDES[emp.id]
        else:
            rda_salary = Decimal(emp.rda_salary or 0)

        # ========================
        # ATTENDANCE
        # ========================
        present_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Present'
        ).values('date').distinct().count()

        leave_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Leave'
        ).values('date').distinct().count()

        off_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Off Day'
        ).values('date').distinct().count()

        absent_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Absent'
        ).values('date').distinct().count()

        attendance_days = days_in_month - absent_days

        if emp.id in SPECIAL_PAYABLE_DAYS:
            attendance_days = SPECIAL_PAYABLE_DAYS[emp.id]

        # ========================
        # ALLOWANCES
        # ========================
        allowances = RestaurantAllowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # If it's overridden, we treat rda_salary directly as the fixed target basic salary for the month
        if is_overridden:
            basic_salary = rda_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            daily_salary = (rda_salary / Decimal(days_in_month)) if rda_salary else Decimal('0')
            basic_salary = (daily_salary * attendance_days).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )

        # ========================
        # ADVANCE (SUBTRACT)
        # ========================
        total_advance = RestaurantAdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # ================================================================
        # 🍔 Foodbill & Employee Collection Deductions (SUBTRACT)
        # ================================================================
        legacy_food_pay = RestaurantFoodBillPayment.objects.filter(
            employee=emp,
            customer_type='Employee',
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        collection_food_pay = Collection.objects.filter(
            employee=emp,
            type='Employee',
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        total_foodPay = legacy_food_pay + collection_food_pay
        
        # ========================
        # LOAN (SUBTRACT)
        # ========================
        loans_qs = RestaurantLoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        total_loan_deduction = Decimal('0')

        for loan in loans_qs:
            if loan.month_name and selected_month in loan.month_name:
                total_loan_deduction += loan.deduction_amount or Decimal('0')

        # ========================
        # NET SALARY
        # ========================
        net_salary = (
            basic_salary +
            allowances -
            total_advance -
            total_foodPay -
            total_loan_deduction
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Save payroll
        RestaurantPayroll.objects.update_or_create(
            employee=emp,
            month=selected_month,
            year=year_input,
            defaults={
                'basic_salary': basic_salary,
                'allowances': allowances,
                'deductions': total_advance + total_foodPay + total_loan_deduction,
                'net_salary': net_salary
            }
        )

        # For display output purposes: if overridden, show original database salary (25000) under RDA salary if needed, 
        # but force the calculated basic salary row to reflect 12500.00
        display_rda_salary = Decimal(emp.rda_salary or 0) if not is_overridden else Decimal('25000.00')

        payroll_data.append({
            'employee': emp,
            'days_in_month': days_in_month,
            'present_days': present_days,
            'leave_days': leave_days,
            'off_days': off_days,
            'absent_days': absent_days,
            'working_days': attendance_days,
            'basic_salary': basic_salary,
            'allowances': allowances,
            'advance_amount': total_advance,
            'foodPay_amount': total_foodPay,
            'loan_amount': total_loan_deduction,
            'net_salary': net_salary,
            'override_rda_salary': display_rda_salary, # Used for custom template columns if required
        })

    # ========================
    # TOTALS
    # ========================
    total_basic_salary = sum(item['basic_salary'] for item in payroll_data)
    total_allowances = sum(item['allowances'] for item in payroll_data)
    total_advance = sum(item['advance_amount'] for item in payroll_data)
    total_foodPay = sum(item['foodPay_amount'] for item in payroll_data)
    total_loans = sum(item['loan_amount'] for item in payroll_data)
    total_net_salary = sum(item['net_salary'] for item in payroll_data)

    total_rda_salary = sum(
        Decimal(item['employee'].rda_salary or 0) if item['employee'].id not in MANUAL_SALARY_OVERRIDES 
        else MANUAL_SALARY_OVERRIDES[item['employee'].id]
        for item in payroll_data
    )

    return render(request, 'restaurant/payroll/payroll_print.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'default_month': default_month_str,
        'default_year': default_year,
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_advance': total_advance,
        'total_foodPay': total_foodPay,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
        'total_rda_salary': total_rda_salary,
        'print_time': timezone.now(),
    })


from datetime import datetime
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    RestaurantEmployee,
    RestaurantAttendance,
    RestaurantAllowances,
    RestaurantAdvancePayment,
    RestaurantFoodBillPayment,
    RestaurantLoanPayment,
    RestaurantPayroll,
)

from projects.models import ProjectFirstLevelName


@login_required
def restaurant_payroll_print_manual(request):

    today = datetime.today()
    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    month_input = request.GET.get('month', default_month_str)
    year_input_str = request.GET.get('year', str(default_year))
    project_id = request.GET.get('project_id')

    # =========================
    # MANUAL PAYABLE DAYS
    # =========================
    manual_payable_days = {}

    for key, value in request.GET.items():
        if key.startswith("payable_days_"):
            try:
                emp_id = int(key.replace("payable_days_", ""))
                manual_payable_days[emp_id] = int(value)
            except:
                pass

    # Year
    try:
        year_input = int(year_input_str)
    except:
        year_input = default_year

    # Month
    try:
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")
    except:
        selected_month_dt = datetime(today.year, today.month, 1)

    selected_month = selected_month_dt.strftime('%B %Y')

    start_date = selected_month_dt.replace(day=1).date()
    end_day = monthrange(year_input, selected_month_dt.month)[1]
    end_date = selected_month_dt.replace(day=end_day).date()
    days_in_month = end_day

    payroll_data = []

    # =========================
    # EMPLOYEES FILTER
    # =========================
    if project_id and project_id.isdigit():
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True,
            project_name_id=int(project_id)
        ).exclude(rda_emp_name__iexact='admin')
    else:
        employees = RestaurantEmployee.objects.filter(
            rda_active_status=True
        ).exclude(rda_emp_name__iexact='admin')

    # =========================
    # TOTAL VARIABLES
    # =========================
    total_rda_salary = Decimal('0')
    total_basic_salary = Decimal('0')
    total_allowances = Decimal('0')
    total_advance = Decimal('0')
    total_foodPay = Decimal('0')
    total_loans = Decimal('0')
    total_net_salary = Decimal('0')

    # =========================
    # MAIN LOOP
    # =========================
    for emp in employees:
        salary = Decimal(emp.rda_salary or 0)

        present_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Present'
        ).count()

        leave_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Leave'
        ).count()

        off_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Off Day'
        ).count()

        absent_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            att_status='Absent'
        ).count()

        # =========================
        # PAYABLE DAYS
        # =========================
        default_days = days_in_month - absent_days
        attendance_days = manual_payable_days.get(emp.id, default_days)

        daily_salary = (salary / Decimal(days_in_month)) if salary else Decimal('0')

        basic_salary = (daily_salary * attendance_days).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # =========================
        # ALLOWANCE
        # =========================
        allowances = RestaurantAllowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # =========================
        # ADVANCE
        # =========================
        advance_amount = RestaurantAdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # =========================
        # FOOD BILL
        # =========================
        foodPay_amount = RestaurantFoodBillPayment.objects.filter(
            employee=emp,
            customer_type='Employee',
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # =========================
        # LOAN
        # =========================
        loan_amount = Decimal('0')

        loans = RestaurantLoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        for loan in loans:
            if loan.month_name and selected_month in loan.month_name:
                loan_amount += loan.deduction_amount or Decimal('0')

        # =========================
        # NET SALARY
        # =========================
        net_salary = (
            basic_salary +
            allowances -
            advance_amount -
            foodPay_amount -
            loan_amount
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # =========================
        # SAVE PAYROLL
        # =========================
        RestaurantPayroll.objects.update_or_create(
            employee=emp,
            month=selected_month,
            year=year_input,
            defaults={
                'basic_salary': basic_salary,
                'allowances': allowances,
                'deductions': advance_amount + foodPay_amount + loan_amount,
                'net_salary': net_salary
            }
        )

        # =========================
        # APPEND DATA
        # =========================
        payroll_data.append({
            'employee': emp,
            'days_in_month': days_in_month,
            'present_days': present_days,
            'leave_days': leave_days,
            'off_days': off_days,
            'absent_days': absent_days,
            'working_days': attendance_days,
            'basic_salary': basic_salary,
            'allowances': allowances,
            'advance_amount': advance_amount,
            'foodPay_amount': foodPay_amount,
            'loan_amount': loan_amount,
            'net_salary': net_salary,
            'rda_salary': salary,
        })

        # =========================
        # TOTALS
        # =========================
        total_rda_salary += salary
        total_basic_salary += basic_salary
        total_allowances += allowances
        total_advance += advance_amount
        total_foodPay += foodPay_amount
        total_loans += loan_amount
        total_net_salary += net_salary

    return render(request, 'restaurant/payroll/payroll_print_manual.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'print_time': timezone.now(),

        # TOTALS
        'total_rda_salary': total_rda_salary,
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_advance': total_advance,
        'total_foodPay': total_foodPay,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
    })


from datetime import datetime
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


@login_required
def restaurant_payslip_print(request):
    today = datetime.today()
    default_month_str = today.strftime('%Y-%m')
    default_year = today.year

    month_input = request.GET.get('month', default_month_str)
    year_input_str = request.GET.get('year', str(default_year))
    project_id = request.GET.get('project_id')
    employee_id = request.GET.get('employee_id')

    # Parse year
    try:
        year_input = int(year_input_str)
    except ValueError:
        year_input = default_year

    # Parse month
    try:
        selected_month_dt = datetime.strptime(month_input, "%Y-%m")
    except ValueError:
        selected_month_dt = datetime(today.year, today.month, 1)

    selected_month = selected_month_dt.strftime('%B')
    start_date = selected_month_dt.replace(day=1).date()
    end_day = monthrange(year_input, selected_month_dt.month)[1]
    end_date = selected_month_dt.replace(day=end_day).date()

    payroll_data = []

    # Employees
    employees = RestaurantEmployee.objects.filter(
        rda_active_status=True
    ).exclude(
        rda_emp_name__iexact='admin'
    )
    
    if project_id and project_id.isdigit():
        employees = employees.filter(project_name_id=int(project_id))

    if employee_id:
        employees = employees.filter(id=employee_id)

    # ✅ EMPLOYEE-ID WISE PAYABLE DAYS
    SPECIAL_PAYABLE_DAYS = {
        0: 0,
    }

    for emp in employees:
        rda_salary = Decimal(emp.rda_salary or 0)

        # Allowances
        allowances = RestaurantAllowances.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # Attendance (simple count)
        attendance_days = RestaurantAttendance.objects.filter(
            employee=emp,
            date__range=(start_date, end_date)
        ).count()

        # ✅ EMP-ID override
        payable_days = SPECIAL_PAYABLE_DAYS.get(emp.id, attendance_days)

        # Salary calculation (fixed 30 days as per your logic)
        daily_salary = rda_salary / Decimal(30) if rda_salary else Decimal('0')

        basic_salary = (daily_salary * Decimal(payable_days)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Advance deductions
        total_advance = RestaurantAdvancePayment.objects.filter(
            employee=emp,
            date__range=(start_date, end_date),
            status='due'
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)

        # Loan deductions
        loans_qs = RestaurantLoanPayment.objects.filter(
            employee=emp,
            status='due',
            start_month__lte=end_date,
            end_month__gte=start_date
        )

        total_loan_deduction = Decimal(0)
        for loan in loans_qs:
            if loan.month_name and selected_month in loan.month_name:
                total_loan_deduction += loan.deduction_amount or Decimal(0)

        # Net salary
        net_salary = (
            basic_salary
            + allowances
            - total_advance
            - total_loan_deduction
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Save payroll
        RestaurantPayroll.objects.update_or_create(
            employee=emp,
            month=selected_month,
            year=year_input,
            defaults={
                'basic_salary': basic_salary,
                'allowances': allowances,
                'deductions': total_advance + total_loan_deduction,
                'net_salary': net_salary,
            }
        )

        payroll_data.append({
            'employee': emp,
            'working_days': attendance_days,
            'payable_days': payable_days,   # 👈 important for payslip
            'basic_salary': basic_salary,
            'allowances': allowances,
            'advance_deduction': total_advance,
            'loan_deduction': total_loan_deduction,
            'net_salary': net_salary,
        })

    # Totals
    total_basic_salary = sum(p['basic_salary'] for p in payroll_data)
    total_allowances = sum(p['allowances'] for p in payroll_data)
    total_advance = sum(p['advance_deduction'] for p in payroll_data)
    total_loans = sum(p['loan_deduction'] for p in payroll_data)
    total_net_salary = sum(p['net_salary'] for p in payroll_data)

    return render(request, 'restaurant/payroll/payslip_print.html', {
        'payrolls': payroll_data,
        'month': selected_month,
        'year': year_input,
        'default_month': default_month_str,
        'default_year': default_year,
        'total_basic_salary': total_basic_salary,
        'total_allowances': total_allowances,
        'total_advance': total_advance,
        'total_loans': total_loans,
        'total_net_salary': total_net_salary,
        'print_time': timezone.now(),
    })





# def restaurant_advance_pdf(request, pk):
#     # Get record by ID
#     record = get_object_or_404(RestaurantAdvancePayment, pk=pk)

#     # Load template
#     template_path = 'restaurant/advancepayment/print_advance_payment.html'
#     context = {'record': record}
#     template = get_template(template_path)
#     html = template.render(context)

#     # Create PDF
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'filename="advance_{record.pk}.pdf"'
#     pisa_status = pisa.CreatePDF(html, dest=response)

#     if pisa_status.err:
#         return HttpResponse('Error generating PDF <pre>' + html + '</pre>')
#     return response





from num2words import num2words

def restaurant_advance_pdf(request, pk):
    record = get_object_or_404(RestaurantAdvancePayment, pk=pk)

    # Safe amount conversion
    try:
        amount_decimal = Decimal(record.amount)
        amount_in_words = num2words(amount_decimal, to='currency', lang='en')
        amount_in_words = amount_in_words.replace("euro", "Taka")
    except (InvalidOperation, ValueError, TypeError):
        amount_in_words = ""

    context = {
        'voucher': record,   # your template uses "voucher"
        'record': record,
        'amount_in_words': amount_in_words,
        'print_time': timezone.now(),
    }

    return render(request, 'restaurant/advancepayment/print_advance_payment.html', context)

 
 
 
 ### LEAVE ###
from restahrm.models import RestaurantLeave
from .forms import RestaurantLeaveForm
# @login_required
# def restau_leavelist(request):
#     restuemployees = RestaurantEmployee.objects.filter(rda_active_status=True)
#     restuleaves = RestaurantLeave.objects.all()
#     return render(request, 'restaurant/leave/leave_list.html', {'leaves': restuleaves, 'employees': restuemployees})
    
    
# @login_required
# def rest_leaveapply(request):
#     department = request.session.get('department')

#     if request.method == 'POST':
#         form = RestaurantLeaveForm(request.POST, department=department)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Leave applied successfully.")
#             return redirect('restau_leavelist')
#     else:
#         form = RestaurantLeaveForm(department=department)

#     return render(request, 'restaurant/leave/leave_form.html', {'form': form, 'title': 'Apply for Leave'})
    
    
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

#     employee = get_object_or_404(RestaurantEmployee, id=employee_id)

#     # Get the first and last date of the target month
#     month_start = date(year, month, 1)
#     month_end_day = monthrange(year, month)[1]
#     month_end = date(year, month, month_end_day)

#     # Filter leaves that overlap with the target month
#     leave_records = RestaurantLeave.objects.filter(
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
#     return render(request, 'restaurant/leave/leave_summary.html', context)





# from datetime import datetime, timedelta, time
# from django.contrib import messages
# from django.utils import timezone
# from tenant.models import Attendance as tenantAttendance


# @login_required
# def restu_leave_approval(request, pk):
#     # Only admin can approve
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve leaves.")
#         return redirect('restau_leavelist')

#     leave = get_object_or_404(RestaurantLeave, pk=pk)
#     device_sn = " SMR5253000079"

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

#         return redirect('restau_leavelist')

#     return render(request, 'restaurant/leave/leave_approval.html', {
#         "leave": leave,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })





# from datetime import datetime, timedelta, time
# from tenant.models import Attendance as tenantAttendance
# from restahrm.models import RestaurantLeave, RestaurantAttendance


# @login_required
# def restu_leave_approval(request, pk):
#     # Only admin can approve
#     if request.session.get('department') != 'admin':
#         messages.error(request, "You are not authorized to approve leaves.")
#         return redirect('restau_leavelist')

#     leave = get_object_or_404(RestaurantLeave, pk=pk)
#     device_sn = leave.device_sn

#     # Attendance preview
#     attendance_preview = tenantAttendance.objects.filter(
#         user_id=leave.employee.id,
#         device_sn=device_sn,
#         created_at__date__range=[leave.start_date, leave.end_date]
#     ).order_by("punch_time")

#     # APPROVE / REJECT
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
#                 # TENANT APP - CHECK-IN
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
#                     if in_qs.count() > 1:
#                         in_qs.exclude(id=main_in.id).delete()
#                     if main_in.status != 1:
#                         main_in.punch_time = punch_in
#                         main_in.status = 2  # Leave
#                         main_in.created_at = day
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
#                         created_at=day
#                     )

#                 # ------------------------------
#                 # TENANT APP - CHECK-OUT
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

#                 # ------------------------------
#                 # RESTAHRM APP - RestaurantAttendance
#                 # ------------------------------
#                 RestaurantAttendance.objects.update_or_create(
#                     employee=leave.employee,
#                     date=day,
#                     defaults={
#                         'emp_shift': leave.employee.rda_shift,
#                         'check_in': manual_check_in,
#                         'check_out': manual_check_out,
#                         'att_status': 'Leave'
#                     }
#                 )

#             messages.success(
#                 request,
#                 f"Leave approved and attendance updated successfully for {leave.employee.rda_emp_name}."
#             )

#         else:
#             leave.approved = False
#             leave.save()
#             messages.success(
#                 request,
#                 f"Leave rejected for {leave.employee.rda_emp_name}."
#             )

#         return redirect('restau_leavelist')

#     return render(request, 'restaurant/leave/leave_approval.html', {
#         "leave": leave,
#         "attendance_preview": attendance_preview,
#         "print_time": timezone.now(),
#     })





# @login_required
# def restu_leave_edit(request, pk):
#     leave = get_object_or_404(RestaurantLeave, pk=pk)
#     if request.method == 'POST':
#         form = RestaurantLeaveForm(request.POST, instance=leave)
#         if form.is_valid():
#             form.save()
#             return redirect('restau_leavelist')
#     else:
#         form = RestaurantLeaveForm(instance=leave)
#     return render(request, 'restaurant/leave/leave_form.html', {'form': form, 'title': 'Edit Leave'})


# @login_required
# def restu_leave_delete(request, pk):
#     leave = get_object_or_404(RestaurantLeave, pk=pk)
#     if request.method == 'POST':
#         log_deleted_data(leave, request.user)
#         leave.delete()
#         return redirect('restau_leavelist')
#     return render(request, 'restaurant/leave/leave_confirm_delete.html', {'leave': leave})
    
    
    




# from datetime import date, datetime, timedelta, time
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.utils import timezone

from .forms import RestaurantLeaveForm, RestaurantLeaveAllocationForm 

# # Target projects for filter inclusion/exclusion rules
RESTAURANT_PROJECTS = [
    "The Galleria Restauent Cafe",
    "The Galleria Live Kitchen"
]


def sync_restaurant_leave_and_attendance(leave):
    """
    1. Updates Leave Allocation counters upon approval.
    2. Syncs daily attendance in both tenantAttendance and RestaurantAttendance models.
    """
    if not leave.approved:
        return

    # ------------------------------
    # 1. UPDATE ALLOCATION COUNTERS
    # ------------------------------
    year = leave.start_date.year
    alloc, _ = RestaurantLeaveAllocation.objects.get_or_create(
        employee=leave.employee, 
        year=year
    )

    days = leave.total_days
    if leave.leave_type == 'CL':
        alloc.casual_leave_used += days
    elif leave.leave_type == 'SL':
        alloc.sick_leave_used += days
    elif leave.leave_type == 'EL':
        alloc.earned_leave_used += days
    alloc.save()

    # ------------------------------
    # 2. MULTI-DATE ATTENDANCE SYNC
    # ------------------------------
    manual_check_in = time(9, 59)
    manual_check_out = time(19, 40)
    device_sn = leave.device_sn
    
    curr_date = leave.start_date
    while curr_date <= leave.end_date:
        
        # --- A. TENANT APP: CHECK-IN ---
        punch_in = datetime.combine(curr_date, manual_check_in)
        in_qs = tenantAttendance.objects.filter(
            user_id=leave.employee.id,
            device_sn=device_sn,
            created_at__date=curr_date,
            check_type=1
        ).order_by('id')

        if in_qs.exists():
            main_in = in_qs.first()
            if in_qs.count() > 1:
                in_qs.exclude(id=main_in.id).delete()
            if main_in.status != 1:
                main_in.punch_time = punch_in
                main_in.status = 2  # Leave Status
                main_in.created_at = curr_date
                main_in.save()
        else:
            tenantAttendance.objects.create(
                user_id=leave.employee.id,
                device_sn=device_sn,
                check_type=1,
                punch_time=punch_in,
                status=2,
                field1=0, field2=0, field3=0,
                field4=0, field5=0, field6=0,
                created_at=curr_date
            )

        # --- B. TENANT APP: CHECK-OUT ---
        punch_out = datetime.combine(curr_date, manual_check_out)
        out_qs = tenantAttendance.objects.filter(
            user_id=leave.employee.id,
            device_sn=device_sn,
            created_at__date=curr_date,
            check_type=0
        ).order_by('id')

        if out_qs.exists():
            main_out = out_qs.first()
            if out_qs.count() > 1:
                out_qs.exclude(id=main_out.id).delete()
            if main_out.status != 1:
                main_out.punch_time = punch_out
                main_out.status = 2
                main_out.created_at = curr_date
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
                created_at=curr_date
            )

        # --- C. RESTAURANT APP: RestaurantAttendance ---
        RestaurantAttendance.objects.update_or_create(
            employee=leave.employee,
            date=curr_date,
            defaults={
                'emp_shift': leave.employee.rda_shift,
                'check_in': manual_check_in,
                'check_out': manual_check_out,
                'att_status': 'Leave'
            }
        )

        curr_date += timedelta(days=1)


# ==========================================
# RESTAURANT LEAVE MANAGEMENT VIEWS
# ==========================================

@login_required
def restau_leavelist(request):
    """View active restaurant leaves and employee list"""
    employees = RestaurantEmployee.objects.filter(
        rda_active_status=True,
        project_name__project_first_name__in=RESTAURANT_PROJECTS
    ).exclude(
        rda_emp_type__iexact='admin'
    )

    leaves = RestaurantLeave.objects.filter(
        employee__in=employees
    ).order_by('-id')

    return render(request, 'restaurant/leave/leave_list.html', {
        'leaves': leaves,
        'employees': employees
    })


@login_required
def rest_leaveapply(request):
    department = request.session.get('department')

    if request.method == 'POST':
        form = RestaurantLeaveForm(request.POST, request.FILES, department=department)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.full_clean()
            leave.save()
            if leave.approved:
                sync_restaurant_leave_and_attendance(leave)
            messages.success(request, "Leave applied successfully.")
            return redirect('restau_leavelist')
    else:
        form = RestaurantLeaveForm(department=department)

    return render(request, 'restaurant/leave/leave_form.html', {
        'form': form, 
        'title': 'Apply for Leave'
    })


@login_required
def restu_leave_edit(request, pk):
    leave = get_object_or_404(RestaurantLeave, pk=pk)
    department = request.session.get('department')

    if request.method == 'POST':
        form = RestaurantLeaveForm(request.POST, request.FILES, instance=leave, department=department)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.full_clean()
            leave.save()
            if leave.approved:
                sync_restaurant_leave_and_attendance(leave)
            messages.success(request, "Leave updated successfully.")
            return redirect('restau_leavelist')
    else:
        form = RestaurantLeaveForm(instance=leave, department=department)

    return render(request, 'restaurant/leave/leave_form.html', {
        'form': form, 
        'title': 'Edit Leave'
    })


@login_required
def restu_leave_delete(request, pk):
    leave = get_object_or_404(RestaurantLeave, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, "Leave deleted successfully.")
        return redirect('restau_leavelist')
    return render(request, 'restaurant/leave/leave_confirm_delete.html', {'leave': leave})


@login_required
def restu_leave_approval(request, pk):
    """Toggle Approval status and execute attendance/allocation sync"""
    if request.session.get('department') != 'admin':
        messages.error(request, "You are not authorized to approve leaves.")
        return redirect('restau_leavelist')

    leave = get_object_or_404(RestaurantLeave, pk=pk)

    if request.method == 'POST':
        approved = request.POST.get('approved')
        if approved == 'True':
            leave.approved = True
            leave.save()
            sync_restaurant_leave_and_attendance(leave)
            messages.success(request, f"Leave for {leave.employee.rda_emp_name} approved and synced successfully.")
        else:
            leave.approved = False
            leave.save()
            messages.warning(request, f"Leave for {leave.employee.rda_emp_name} rejected.")

        return redirect('restau_leavelist')

    attendance_preview = tenantAttendance.objects.filter(
        user_id=leave.employee.id,
        device_sn=leave.device_sn,
        created_at__date__range=[leave.start_date, leave.end_date]
    ).order_by("punch_time")

    return render(request, 'restaurant/leave/leave_approval.html', {
        "leave": leave,
        "attendance_preview": attendance_preview,
        "print_time": timezone.now(),
    })

from datetime import date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def restu_employee_leave_summary(request):
    """Popup report view for employee leave balances and history"""
    emp_id = request.GET.get('employee_id')
    current_year = date.today().year
    year_id = request.GET.get('year_id', current_year)

    employee = get_object_or_404(RestaurantEmployee, pk=emp_id)
    alloc, _ = RestaurantLeaveAllocation.objects.get_or_create(
        employee=employee, 
        year=int(year_id)
    )

    leave_history = RestaurantLeave.objects.filter(
        employee=employee,
        approved=True,
        start_date__year=year_id
    ).order_by('-start_date')

    context = {
        'employee': employee,
        'alloc': alloc,
        'year': year_id,
        'current_year': current_year,  # <-- Added here
        'leave_history': leave_history
    }
    return render(request, 'restaurant/leave/leave_summary_popup.html', context)
    
    

# # ==========================================
# # RESTAURANT LEAVE ALLOCATION VIEWS (CRUD)
# # ==========================================

@login_required
def restu_allocation_list(request):
    """View leave allocations for active restaurant staff"""
    allocations = RestaurantLeaveAllocation.objects.filter(
        employee__rda_active_status=True,
        employee__project_name__project_first_name__in=RESTAURANT_PROJECTS
    ).exclude(
        employee__rda_emp_type__iexact='admin'
    ).order_by('-year', 'employee__rda_emp_name')

    return render(request, 'restaurant/leave/allocation_list.html', {
        'allocations': allocations
    })


@login_required
def restu_allocation_create(request):
    if request.method == 'POST':
        form = RestaurantLeaveAllocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave allocation created successfully.")
            return redirect('restu_allocation_list')
    else:
        form = RestaurantLeaveAllocationForm()

    return render(request, 'restaurant/leave/allocation_form.html', {
        'form': form, 
        'title': 'Add Leave Allocation'
    })


@login_required
def restu_allocation_edit(request, pk):
    alloc = get_object_or_404(RestaurantLeaveAllocation, pk=pk)
    if request.method == 'POST':
        form = RestaurantLeaveAllocationForm(request.POST, instance=alloc)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave allocation updated successfully.")
            return redirect('restu_allocation_list')
    else:
        # Fixed typo: changed RestaurantAllocationForm to RestaurantLeaveAllocationForm
        form = RestaurantLeaveAllocationForm(instance=alloc)

    return render(request, 'restaurant/leave/allocation_form.html', {
        'form': form, 
        'title': 'Edit Leave Allocation'
    })


@login_required
def restu_allocation_delete(request, pk):
    alloc = get_object_or_404(RestaurantLeaveAllocation, pk=pk)
    if request.method == 'POST':
        alloc.delete()
        messages.success(request, "Leave allocation deleted successfully.")
        return redirect('restu_allocation_list')

    return render(request, 'restaurant/leave/allocation_confirm_delete.html', {
        'alloc': alloc
    })
    


    
### IOM ###
@login_required
def restau_iom_list(request):
    employees = RestaurantEmployee.objects.filter(rda_active_status=True).exclude(rda_emp_type__iexact='admin')
    iom = RestIom.objects.all().order_by('-id')
    return render(request, 'restaurant/iom/iom_list.html', {'ioms': iom, 'employees': employees})


@login_required
def restau_iom_apply(request):
    department = request.session.get('department')

    if request.method == 'POST':
        form = RestIomForm(request.POST, department=department)
        if form.is_valid():
            form.save()
            messages.success(request, "IOM applied successfully.")
            return redirect('restau_iom_list')
    else:
        form = RestIomForm(department=department)

    return render(request, 'restaurant/iom/iom_form.html', {'form': form, 'title': 'Apply for IOM'})





@login_required
def restau_iom_edit(request, pk):
    iom = get_object_or_404(RestIom, pk=pk)
    if request.method == 'POST':
        form = RestIomForm(request.POST, instance=iom)
        if form.is_valid():
            form.save()
            return redirect('restau_iom_list')
    else:
        form = RestIomForm(instance=iom)
    return render(request, 'restaurant/iom/iom_form.html', {'form': form, 'title': 'Edit Leave'})


@login_required
def restau_iom_delete(request, pk):
    iom = get_object_or_404(RestIom, pk=pk)
    if request.method == 'POST':
        log_deleted_data(iom, request.user)
        iom.delete()
        return redirect('restau_iom_list')
    return render(request, 'restaurant/iom/iom_confirm_delete.html', {'iom': iom})





from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, time
from tenant.models import Attendance as tenantAttendance

@login_required
def restau_iom_approval(request, pk):
    # Only admin can approve
    if request.session.get('department') != 'admin':
        messages.error(request, "You are not authorized to approve IOM.")
        return redirect('restau_iom_list')

    iom = get_object_or_404(RestIom, pk=pk)
    device_sn = iom.device_sn

    # Attendance preview for all days in the IOM range
    attendance_preview = tenantAttendance.objects.filter(
        user_id=iom.employee.id,
        device_sn=device_sn,
        created_at__date__range=[iom.start_date, iom.end_date]
    ).order_by("punch_time")

    if request.method == 'POST':
        approved = request.POST.get("approved")

        if approved == "True":
            iom.approved = True
            iom.save()

            # Use actual check-in/out from IOM or fallback manual times
            manual_check_in = iom.check_in if iom.check_in else time(9, 0)
            manual_check_out = iom.check_out if iom.check_out else time(18, 0)

            start = iom.start_date
            end = iom.end_date
            day_count = (end - start).days + 1

            for i in range(day_count):
                day = start + timedelta(days=i)

                # -------------------------
                # TENANT APP - CHECK-IN
                # -------------------------
                punch_in = datetime.combine(day, manual_check_in)
                in_qs = tenantAttendance.objects.filter(
                    user_id=iom.employee.id,
                    device_sn=device_sn,
                    created_at__date=day,
                    check_type=1
                ).order_by('id')

                if in_qs.exists():
                    main_in = in_qs.first()
                    if in_qs.count() > 1:
                        in_qs.exclude(id=main_in.id).delete()
                    main_in.punch_time = punch_in
                    main_in.status = 1  # Present
                    main_in.created_at = day
                    main_in.save()
                else:
                    tenantAttendance.objects.create(
                        user_id=iom.employee.id,
                        device_sn=device_sn,
                        check_type=1,
                        punch_time=punch_in,
                        status=1,
                        field1=0, field2=0, field3=0,
                        field4=0, field5=0, field6=0,
                        created_at=day
                    )

                # -------------------------
                # TENANT APP - CHECK-OUT
                # -------------------------
                punch_out = datetime.combine(day, manual_check_out)
                out_qs = tenantAttendance.objects.filter(
                    user_id=iom.employee.id,
                    device_sn=device_sn,
                    created_at__date=day,
                    check_type=0
                ).order_by('id')

                if out_qs.exists():
                    main_out = out_qs.first()
                    if out_qs.count() > 1:
                        out_qs.exclude(id=main_out.id).delete()
                    main_out.punch_time = punch_out
                    main_out.status = 1
                    main_out.created_at = day
                    main_out.save()
                else:
                    tenantAttendance.objects.create(
                        user_id=iom.employee.id,
                        device_sn=device_sn,
                        check_type=0,
                        punch_time=punch_out,
                        status=1,
                        field1=0, field2=0, field3=0,
                        field4=0, field5=0, field6=0,
                        created_at=day
                    )

            messages.success(request, f"IOM approved and attendance updated for {iom.employee.rda_emp_name}.")

        else:
            # REJECT
            iom.approved = False
            iom.save()
            messages.success(request, f"IOM rejected for {iom.employee.rda_emp_name}.")

        return redirect('restau_iom_list')

    return render(request, 'restaurant/iom/iom_approval.html', {
        "iom": iom,
        "attendance_preview": attendance_preview,
        "print_time": timezone.now(),
    })



@login_required
def restau_employee_iom_summary(request):
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

    employee = get_object_or_404(RestaurantEmployee, id=employee_id)

    # Get the first and last date of the target month
    month_start = date(year, month, 1)
    month_end_day = monthrange(year, month)[1]
    month_end = date(year, month, month_end_day)

    # Filter leaves that overlap with the target month
    iom_records = RestIom.objects.filter(
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
    return render(request, 'restaurant/iom/iom_summary.html', context)
    
    
    


### SALARY PAYMENT ###
@login_required
def rest_salary_list(request):
    employees = RestaurantEmployee.objects.all()
    records = RestaurantSalaryPayment.objects.all()
    return render(request, 'restaurant/salary/salary_list.html', {'records': records, 'employees': employees})



@login_required
def rest_salary_create(request):
    if request.method == 'POST':
        form = RestaurantSalaryPaymentForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            # Ensure RestHeadOfAccount exists
            rest_head, _ = RestHeadOfAccount.objects.get_or_create(
                head_name=loanvoucher.head_of_account.head_name
            )
            
            # Ensure CashRestType exists
            cash_rest_type, _ = CashRestType.objects.get_or_create(
                cash_type_name=loanvoucher.cash_type.cash_type_name
            )
            
            # Create DebitRestVoucher
            debit_voucher = DebitRestVoucher.objects.create(
                type='Employee',
                empl_name=str(loanvoucher.employee),
                project_name=loanvoucher.project_name,
                cash_type=cash_rest_type,   # ✅ Correct instance
                cheque_number=loanvoucher.cheque_number,
                head_of_account=rest_head,  # ✅ Correct instance
                amount=loanvoucher.amount,
                date=loanvoucher.date or now().date(),
                particulars=loanvoucher.reason or "Salary to Employee",
                is_confirmed=True,
                carrier=str(loanvoucher.employee),
                create_dr=str(request.user),
            )


            print('DebitVoucher created:', debit_voucher.id)
            return redirect('rest_salary_list')
    else:
        form = RestaurantSalaryPaymentForm()

    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')

    return render(request, 'restaurant/salary/salary_form.html', {
        'form': form,
        'projects': projects,
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })


    
@login_required
def rest_salary_edit(request, pk):
    record = get_object_or_404(RestaurantSalaryPayment, pk=pk)
    if request.method == 'POST':
        form = RestaurantSalaryPaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('rest_salary_list')
    else:
        form = RestaurantSalaryPaymentForm(instance=record)
        
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')
    return render(request, 'restaurant/salary/salary_form.html', {
        'form': form,
        'projects': projects,               
        'head_of_accounts': [head_of_account],
        'today': date.today(), 
    })



@login_required
def rest_salary_delete(request, pk):
    record = get_object_or_404(RestaurantSalaryPayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('rest_salary_list')
    return render(request, 'restaurant/salary/salary_confirm_delete.html', {'record': record})
    
    



### FOODBILL PAYMENT ###
@login_required
def rest_foodbill_list(request):
    employees = RestaurantEmployee.objects.all()
    records = RestaurantFoodBillPayment.objects.all()
    return render(request, 'restaurant/foodbill/rest_foodbill_list.html', {'records': records, 'employees': employees})



# @login_required
# def rest_foodbill_create(request):

#     # ✅ Always define first
#     projects = ProjectFirstLevelName.objects.all()

#     if request.method == 'POST':
#         form = RestaurantFoodBillPaymentForm(request.POST)

#         if form.is_valid():
#             foodbill = form.save()

#             voucher_type = foodbill.customer_type
#             employee_name = None
#             customer_obj = None

#             if voucher_type == "Employee":
#                 employee_name = str(foodbill.employee) if foodbill.employee else None

#             elif voucher_type == "Customer":
#                 customer_obj = foodbill.customer_name

#             DebitRestVoucher.objects.create(
#                 type=voucher_type,
#                 empl_name=employee_name,
#                 customer_name=customer_obj,
#                 project_name=foodbill.project_name,
#                 cash_type=foodbill.cash_type,
#                 cheque_number=foodbill.cheque_number,
#                 head_of_account=foodbill.head_of_account,
#                 amount=foodbill.amount,
#                 date=foodbill.date,
#                 particulars=foodbill.reason,
#                 is_confirmed=True,
#                 carrier=str(request.user),
#                 create_dr=str(request.user),
#             )

#             return redirect('rest_foodbill_list')

#     else:
#         form = RestaurantFoodBillPaymentForm()

#     return render(request, 'restaurant/foodbill/foodbill_form.html', {
#         'form': form,
#         'projects': projects,   # ✅ Always available now
#         'today': now().date(),
#     })



from django.utils.timezone import now

@login_required
def rest_foodbill_create(request):

    projects = ProjectFirstLevelName.objects.all()

    if request.method == 'POST':
        form = RestaurantFoodBillPaymentForm(request.POST)

        if form.is_valid():
            foodbill = form.save()

            voucher_type = foodbill.customer_type
            employee_name = None
            customer_obj = None

            if voucher_type == "Employee":
                employee_name = foodbill.employee

            elif voucher_type == "Customer":
                customer_obj = foodbill.customer_name

            DebitRestVoucher.objects.create(
                type=voucher_type,
                empl_name=employee_name,
                customer_name=customer_obj,
                project_name=foodbill.project_name,
                cash_type=foodbill.cash_type,
                cheque_number=foodbill.cheque_number,
                head_of_account=foodbill.head_of_account,
                amount=foodbill.amount,
                date=foodbill.date,
                particulars=foodbill.reason,
                is_confirmed=True,
                carrier=str(request.user),
                create_dr=str(request.user),
            )

            return redirect('rest_foodbill_list')

    else:
        form = RestaurantFoodBillPaymentForm()

    return render(request, 'restaurant/foodbill/foodbill_form.html', {
        'form': form,
        'projects': projects,
        'today': now().date(),
    })
    
    
    
    
   
@login_required
def rest_foodbill_edit(request, pk):
    record = get_object_or_404(RestaurantFoodBillPayment, pk=pk)
    if request.method == 'POST':
        form = RestaurantFoodBillPaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('rest_foodbill_list')
    else:
        form = RestaurantFoodBillPaymentForm(instance=record)
        
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')
    return render(request, 'restaurant/foodbill/foodbill_form.html', {
        'form': form,
        'projects': projects,               
        'head_of_accounts': [head_of_account],
        'today': date.today(), 
    })



@login_required
def rest_foodbill_delete(request, pk):
    record = get_object_or_404(RestaurantFoodBillPayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('rest_foodbill_list')
    return render(request, 'restaurant/foodbill/foodbill_confirm_delete.html', {'record': record})



### ADVANCE PAYMENT ###
@login_required
def restau_loanPayment_list(request):
    records = RestaurantLoanPayment.objects.all()
    return render(request, 'restaurant/loanpayment/loanPayment_list.html', {'records': records})


@login_required
def restau_loanPayment_add(request):
    if request.method == 'POST':
        form = RestaurantLoanPaymentForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)
            loanvoucher.save()

            # Create DebitVoucher
            debit_voucher = DebitRestVoucher.objects.create(
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
                requi_id=loanvoucher.id,
            )
            print('ebitVoucher created:', debit_voucher.id)
            return redirect('restau_loanPayment_list')
    else:
        form = RestaurantLoanPaymentForm()

    # CORRECT VARIABLE NAME
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')

    return render(request, 'restaurant/loanpayment/loanPayment_form.html', {
        'form': form,
        'projects': projects,              
        'head_of_accounts': [head_of_account],
        'today': now().date(),
    })



@login_required
def restau_loanpayment_edit(request, pk):
    record = get_object_or_404(RestaurantLoanPayment, pk=pk)
    if request.method == 'POST':
        form = RestaurantLoanPaymentForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('restau_loanPayment_list')
    else:
        form = RestaurantLoanPaymentForm(instance=record)
    projects = ProjectFirstLevelName.objects.all()
    head_of_account = get_object_or_404(RestHeadOfAccount, head_name='Employee Account')
    return render(request, 'restaurant/loanpayment/loanPayment_form.html', {'form': form, 'projects': projects,'head_of_accounts': [head_of_account], 'today': now().date()})



@login_required
def restau_loanpayment_delete(request, pk):
    record = get_object_or_404(RestaurantLoanPayment, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('restau_loanPayment_list')
    return render(request, 'restaurant/loanpayment/loan_confirm_delete.html', {'record': record})
    
    
@login_required
def restau_allowances_list(request):
    records = RestaurantAllowances.objects.all().order_by('-id')

    projects = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    return render(request, 'restaurant/allowances/allowances_list.html', {
        'records': records,
        'projects': projects,
    })
    
    
@login_required
def restau_allowances_create(request):
    if request.method == 'POST':
        form = RestaurantAllowancesForm(request.POST)

        if form.is_valid():
            allowance = form.save(commit=False)

            # project (safe override if needed)
            project_id = request.POST.get('project_name')
            if project_id:
                allowance.project_name = get_object_or_404(
                    ProjectFirstLevelName,
                    id=project_id
                )

            if not allowance.date:
                allowance.date = now().date()

            allowance.save()
            return redirect('restau_allowances_list')

    else:
        form = RestaurantAllowancesForm()

    return render(request, 'restaurant/allowances/allowances_form.html', {
        'form': form,
        'projects': ProjectFirstLevelName.objects.all(),
        'today': now().date(),
    })


from django.shortcuts import get_list_or_404

@login_required
def restau_allowances_edit(request, pk):
    record = get_object_or_404(RestaurantAllowances, pk=pk)

    if request.method == 'POST':
        form = RestaurantAllowancesForm(request.POST, instance=record)

        if form.is_valid():
            allowance = form.save(commit=False)

            if not allowance.date:
                allowance.date = now().date()

            allowance.save()
            return redirect('restau_allowances_list')

    else:
        form = RestaurantAllowancesForm(instance=record)

    return render(request, 'restaurant/allowances/allowances_form.html', {
        'form': form,
        'projects': ProjectFirstLevelName.objects.all(),
        'today': now().date(),
    })
    
    


    
    
@login_required
def restau_allowances_delete(request, pk):
    record = get_object_or_404(RestaurantAllowances, pk=pk)
    if request.method == 'POST':
        log_deleted_data(record, request.user)
        record.delete()
        return redirect('restau_allowances_list')
    return render(request, 'restaurant/allowances/allowances_confirm_delete.html', {'record': record})
    
    
    

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import (
    RestaurantEmployee, RestaurantAttendance,
    RestaurantAttendanceLocation, RestaurantAttendanceAccessControl
)
from projects.models import ProjectFirstLevelName


def public_attendance_restaurant(request):
    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    access = RestaurantAttendanceAccessControl.objects.first()

    if access:
        employees = access.allowed_employees.filter(
            rda_active_status=True,
            project_name__in=projects_first
        ).select_related('project_name').order_by('rda_emp_name')
    else:
        employees = RestaurantEmployee.objects.none()

    if request.method == 'POST':
        punch_type = request.POST.get('punch_type')
        employee_id = request.POST.get('employee_id')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not employee_id:
            messages.error(request, "Please select your name.")
            return redirect('public_attendance_restaurant')

        if not latitude or not longitude:
            messages.error(request, "Location not captured. Please allow location access and try again.")
            return redirect('public_attendance_restaurant')

        try:
            employee = employees.get(pk=employee_id)
        except RestaurantEmployee.DoesNotExist:
            messages.error(request, "You are not authorized for attendance. Contact admin.")
            return redirect('public_attendance_restaurant')

        today = timezone.localdate()
        now_time = timezone.localtime().time()

        with transaction.atomic():
            existing = (RestaurantAttendance.objects
                        .select_for_update()
                        .filter(employee=employee, date=today)
                        .first())

            if existing is None:
                attendance = RestaurantAttendance.objects.create(
                    employee=employee, date=today, att_status='Present',
                    emp_shift=employee.rda_shift
                )
            else:
                attendance = existing

            location, _ = RestaurantAttendanceLocation.objects.get_or_create(attendance=attendance)

            if punch_type == 'in':
                if attendance.check_in:
                    messages.warning(
                        request,
                        f"{employee.rda_emp_name} already punched IN today at "
                        f"{attendance.check_in.strftime('%I:%M %p')}."
                    )
                    return redirect('public_attendance_restaurant')

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
                    return redirect('public_attendance_restaurant')

                if attendance.check_out:
                    messages.warning(
                        request,
                        f"{employee.rda_emp_name} already punched OUT today at "
                        f"{attendance.check_out.strftime('%I:%M %p')}."
                    )
                    return redirect('public_attendance_restaurant')

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

        return redirect('public_attendance_restaurant')

    context = {
        'employees': employees,
        'projects': projects_first,
    }
    return render(request, 'restaurant/public_attendance_restaurant.html', context)
    
    
    
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import RestaurantEmployee, RestaurantAttendanceAccessControl
from projects.models import ProjectFirstLevelName


@login_required
@permission_required('restahrm.change_restaurantattendanceaccesscontrol', raise_exception=True)
def manage_attendance_access_restaurant(request):
    access, created = RestaurantAttendanceAccessControl.objects.get_or_create(
        id=1, defaults={'name': 'Restaurant Attendance Access'}
    )

    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    all_employees = RestaurantEmployee.objects.filter(
        rda_active_status=True,
        project_name__in=projects_first
    ).select_related('project_name').order_by('rda_emp_name')

    allowed_ids = set(access.allowed_employees.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('employee_ids')
        access.allowed_employees.set(selected_ids)
        access.save()
        messages.success(request, "Attendance access list updated successfully.")
        return redirect('manage_attendance_access_restaurant')

    context = {
        'employees': all_employees,
        'allowed_ids': allowed_ids,
        'projects': projects_first,
    }
    return render(request, 'restaurant/manage_attendance_access_restaurant.html', context)
    



def public_attendance_portal(request):

    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "BTP Office",
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    context = {
        "projects": projects_first,
    }

    return render(
        request,
        "restaurant/public_attendance_portal.html",
        context,
    )
  


def public_attendance_emp_portal(request):

    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "BTP Office",
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen",
        ]
    )

    context = {
        "projects": projects_first,
    }

    return render(
        request,
        "restaurant/public_attendance_emp_portal.html",
        context,
    )
    

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .models import RestaurantAttendanceLocation

@login_required
@permission_required('restahrm.can_verify_restaurant_attendance_location', login_url='denied')
def public_attendance_resthrmcafe_check(request):
    project_id = request.GET.get('project')
    location_records = RestaurantAttendanceLocation.objects.select_related(
        'attendance', 
        'attendance__employee',  
        'verified_by'
    ).order_by('-attendance__date')
    
    if project_id:
        location_records = location_records.filter(attendance__employee__project_name__id=project_id)
        
    context = {
        'location_records': location_records,
    }
    
    return render(request, 'restaurant/attendance_locations_cafe_list.html', context)
    
    
@login_required
@permission_required('restahrm.can_verify_restaurant_attendance_location', login_url='denied')
def public_attendance_resthrmlive_check(request):
    project_id = request.GET.get('project')
    location_records = RestaurantAttendanceLocation.objects.select_related(
        'attendance', 
        'attendance__employee',  
        'verified_by'
    ).order_by('-attendance__date')
    if project_id:
        location_records = location_records.filter(attendance__employee__project_name__id=project_id)
    context = {
        'location_records': location_records,
    }
    
    return render(request, 'restaurant/attendance_locations_live_list.html', context)
    