from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer,CustomerLead
from .forms import CustomerForm,CustomerLeadForm
from projects.models import ProjectFirstLevelName
from hrm.models import Employee
from datetime import date



@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})

# @login_required
# def customer_add(request):
#     if request.method == 'POST':
#         form = CustomerForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('customer_list')
#     else:
#         form = CustomerForm()
#     return render(request, 'customers/customer_add.html', {'form': form, 'title': 'Add Customer'})



@login_required
def customer_add(request):
    projects = ProjectFirstLevelName.objects.all()
    today = date.today().isoformat() 
    employees = Employee.objects.exclude(employee_name="Admin")
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'projects': projects,
        'title': 'Add Customer',
        'today': today,
        'employees': employees,
    }
    return render(request, 'customers/customer_add.html', context)


# @login_required
# def customer_edit(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)
#     if request.method == 'POST':
#         form = CustomerForm(request.POST, request.FILES, instance=customer)
#         if form.is_valid():
#             form.save()
#             return redirect('customer_list')
#     else:
#         form = CustomerForm(instance=customer)
#     return render(request, 'customers/customer_edit.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    projects = ProjectFirstLevelName.objects.all()
    employees = Employee.objects.all()
    today = date.today().isoformat()  # YYYY-MM-DD format for date field fallback

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)

    context = {
        'form': form,
        'title': 'Edit Customer',
        'projects': projects,
        'employees': employees,
        'today': today,
    }
    return render(request, 'customers/customer_edit.html', context)



@login_required
def customer_details(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'customers/customer_details.html', {'customer': customer, 'title': 'Customer Details'})



@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customers/customer_delete.html', {'customer': customer})


@login_required
def customer_lead_list(request):
    leads = CustomerLead.objects.all()
    return render(request, 'customerlead/customer_lead_list.html', {'leads': leads})


@login_required
def customer_lead_add(request):
    if request.method == 'POST':
        form = CustomerLeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_lead_list')
    else:
        form = CustomerLeadForm()

    customers = Customer.objects.all()
    projects = ProjectFirstLevelName.objects.all()

    return render(request, 'customerlead/customer_lead_add.html', {'form': form, 'customers': customers, 'projects': projects })


@login_required
def customer_lead_edit(request, pk):
    lead = get_object_or_404(CustomerLead, pk=pk)
    if request.method == 'POST':
        form = CustomerLeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect('customer_lead_list')
    else:
        form = CustomerLeadForm(instance=lead)

    customers = Customer.objects.all()
    projects = ProjectFirstLevelName.objects.all()
    return render(request, 'customerlead/customer_lead_edit.html', {
        'form': form, 
        'lead': lead, 
        'customers': customers, 
        'projects': projects
    })



@login_required
def customer_lead_delete(request, pk):
    lead = get_object_or_404(CustomerLead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        return redirect('customer_lead_list')
    return render(request, 'customerlead/customer_lead_delete.html', {'lead': lead})

@login_required
def customer_lead_detail(request, pk):
    customer_lead = get_object_or_404(CustomerLead, pk=pk)
    return render(request, 'customerlead/customer_lead_details.html', {'customer_lead': customer_lead})
