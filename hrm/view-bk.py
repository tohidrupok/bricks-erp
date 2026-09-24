from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Employee
from .forms import EmployeeForm
from django.contrib.auth.models import User, Group


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee/employee_list.html', {'employees': employees})


# @login_required
# def employee_add(request):
#     form = EmployeeForm(request.POST or None, request.FILES or None)
#     if form.is_valid():
#         form.save()
#         return redirect('employee_list')
#     return render(request, 'employee/employee_form.html', {'form': form, 'title': 'Add Employee'})

from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import EmployeeForm

@login_required
def employee_add(request):
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        employee = form.save(commit=False)
        # Use email username or generate a username
        #username = employee.email.split('@')[0]
        username = employee.emp_name

        # Create user with default password '123456'
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

        # Link user to employee
        employee.user = user
        employee.save()

        # Optionally, you can add a message to inform admin about the default password
        # messages.success(request, 'Employee added with default password "123456". Please ask the user to change it on first login.')

        return redirect('employee_list')

    return render(request, 'employee/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
    if form.is_valid():
        form.save()
        return redirect('employee_list')
    return render(request, 'employee/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.delete()
        return redirect('employee_list')
    return render(request, 'employee/employee_confirm_delete.html', {'employee': employee})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employee/employee_detail.html', {'employee': employee})
