from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer,CustomerLead,CustomerFollowup,CustInfoBank
from .forms import CustomerForm,CustomerLeadForm,CustomerFollowupForm,CustInfoBankForm
from projects.models import ProjectFirstLevelName
from hrm.models import Employee,RdaEmployee
from datetime import date
from django.http import JsonResponse
from django.contrib import messages
from inventories.utils import log_deleted_data
from accounting.utils.sms import send_sms


@login_required
def customer_bank(request):
    custInfobanks = CustInfoBank.objects.all()
    return render(request, 'customers/customer_bank_list.html', {'custInfobanks': custInfobanks})


@login_required
def customer_bank_add(request):
    projects = ProjectFirstLevelName.objects.all()
    today = date.today().isoformat() 
    employees = RdaEmployee.objects.exclude(rda_emp_name="Admin")
    if request.method == 'POST':
        form = CustInfoBankForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('customer_bank')
    else:
        form = CustInfoBankForm()

    context = {
        'form': form,
        'projects': projects,
        'title': 'Add Customer',
        'today': today,
        'employees': employees,
    }
    return render(request, 'customers/customer_bank_add.html', context)





@login_required
def customer_bank_edit(request, pk):
    customer = get_object_or_404(CustInfoBank, pk=pk)
    projects = ProjectFirstLevelName.objects.all()
    employees = RdaEmployee.objects.all()
    today = date.today().isoformat() 

    if request.method == 'POST':
        form = CustInfoBankForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_bank')
    else:
        form = CustInfoBankForm(instance=customer)

    context = {
        'form': form,
        'title': 'Edit Customer',
        'projects': projects,
        'employees': employees,
        'today': today,
    }
    return render(request, 'customers/customer_bank_edit.html', context)
    
 
 
@login_required
def customer_bank_details(request, pk):
    customer = get_object_or_404(CustInfoBank, pk=pk)
    return render(request, 'customers/customer_bank_details.html', {'customer': customer, 'title': 'Customer Details'})
    
    


@login_required
def customer_bank_delete(request, pk):
    customer = get_object_or_404(CustInfoBank, pk=pk)
    if request.method == 'POST':
        log_deleted_data(CustInfoBank, request.user)
        customer.delete()
        return redirect('customer_bank')
    return render(request, 'customers/customer_bank_delete.html', {'customer': customer})




@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-id')
    custInfobanks = CustInfoBank.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers, 'custInfobanks': custInfobanks})

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
    employees = RdaEmployee.objects.all()

    customer_id = request.GET.get("customer_id")

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        if customer_id:
            try:
                existing_customer = CustInfoBank.objects.get(id=customer_id)
                # Pre-fill form with this customer’s data
                form = CustInfoBankForm(instance=existing_customer)
            except CustInfoBank.DoesNotExist:
                form = CustInfoBankForm()
        else:
            form = CustInfoBankForm()

    context = {
        'form': form,
        'projects': projects,
        'title': 'Add Customer',
        'today': today,
        'employees': employees,
    }
    return render(request, 'customers/customer_add.html', context)





# @login_required
# def customer_add(request):
#     projects = ProjectFirstLevelName.objects.all()
#     today = date.today().isoformat() 
#     employees = RdaEmployee.objects.exclude(rda_emp_name="Admin")
#     if request.method == 'POST':
#         form = CustomerForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('customer_list')
#     else:
#         form = CustomerForm()
    
#     context = {
#         'form': form,
#         'projects': projects,
#         'title': 'Add Customer',
#         'today': today,
#         'employees': employees,
#     }
#     return render(request, 'customers/customer_add.html', context)


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
        log_deleted_data(customer, request.user)
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
            lead = form.save() 
            
            CustomerFollowup.objects.create(
                lead_id=int(lead.id), 
                followup_date=lead.followup_date,
                followup_note=lead.followup_note
            )

            return redirect('customer_lead_list')
    else:
        form = CustomerLeadForm()

    customers = CustInfoBank.objects.all()
    projects = ProjectFirstLevelName.objects.all()
    today = date.today().isoformat()

    return render(request, 'customerlead/customer_lead_add.html', {
        'form': form,
        'customers': customers,
        'projects': projects,
        'today': today
    })



@login_required
def lead_followup_list(request):
    leads = CustomerLead.objects.all().order_by('-id')
    return render(request, 'leadfollowup/lead_followup_list.html', {'leads': leads})

# @login_required
# def customer_lead_followup(request, lead_id):
#     form = CustomerFollowupForm(request.POST or None)
#     today = date.today().isoformat()

#     previous_lead = CustomerLead.objects.get(id=lead_id)
#     previous_followups = CustomerFollowup.objects.filter(lead_id=lead_id).order_by('-create_date')
#     if request.method == 'POST':
#         form = CustomerFollowupForm(request.POST)

        # if form.is_valid():
        #     followup = form.save(commit=False)
        #     followup.lead_id = lead_id
        #     followup.save()
        #     return redirect('lead_followup_list') 

#     return render(request, 'leadfollowup/customer_lead_followup.html', {
#         'form': form,
#         'today': today,
#         'lead_id': lead_id,
#         'previous_followups': previous_followups,
#         'previous_leads': previous_lead,
#     })



@login_required
def customer_lead_followup(request, lead_id):
    lead_instance = get_object_or_404(CustomerLead, id=lead_id)
    form = CustomerFollowupForm(request.POST or None)
    previous_followups = CustomerFollowup.objects.filter(lead_id=lead_id).order_by('-create_date')
    today = date.today().isoformat()

    if request.method == 'POST': 
        if form.is_valid():
            followup = form.save(commit=False)
            followup.lead_id = lead_id
            followup.save()           
            
            lead_instance.followup_date = followup.followup_date
            lead_instance.status = request.POST.get('status', lead_instance.status)
            lead_instance.save()

            return redirect('lead_followup_list')

    return render(request, 'leadfollowup/customer_lead_followup.html', {
        'form': form,
        'lead_id': lead_id,
        'today': today,
        'previous_followups': previous_followups,
        'previous_leads': lead_instance,
    })




@login_required
def toggle_lead_status(request, lead_id):
    lead = get_object_or_404(CustomerLead, id=lead_id)

    if lead.status == 'open':
        lead.status = 'close'
        lead.save()

    return redirect('lead_followup_list')


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
        log_deleted_data(lead, request.user)
        lead.delete()
        return redirect('customer_lead_list')
    return render(request, 'customerlead/customer_lead_delete.html', {'lead': lead})

@login_required
def customer_lead_detail(request, pk):
    customer_lead = get_object_or_404(CustomerLead, pk=pk)
    return render(request, 'customerlead/customer_lead_details.html', {'customer_lead': customer_lead})
    
    
 

# from .forms import BulkSMSForm
# from .models import BulkSMS, BulkSMSRecipient


# @login_required(login_url='/login/')
# def bulk_sms_send_view(request):
#     form = BulkSMSForm(request.POST or None)

#     if request.method == "POST" and form.is_valid():
#         recipients = form.cleaned_data['recipients']
#         message_text = form.cleaned_data['message'].strip()

#         if not recipients:
#             messages.warning(request, "Please select at least one recipient.")
#             return render(request, "customers/bulk_sms_form.html", {"form": form})

#         if not message_text:
#             messages.warning(request, "Message cannot be empty.")
#             return render(request, "customers/bulk_sms_form.html", {"form": form})

#         # Create BulkSMS record (initially pending)
#         bulk_sms = BulkSMS.objects.create(
#             message=message_text,
#             status="Pending"
#         )

#         failed_numbers = []

#         # Loop through each recipient
#         for customer in recipients:
#             status = "Failed"  # default
#             sent_time = None

#             try:
#                 # Attempt to send SMS
#                 sent_success = send_sms(customer.contact_no, message_text)

#                 if sent_success:
#                     status = "Sent"
#                     sent_time = timezone.now()
#                 else:
#                     failed_numbers.append(customer.contact_no)

#             except Exception as e:
#                 print(f"Error sending SMS to {customer.contact_no}: {e}")
#                 failed_numbers.append(customer.contact_no)

#             # Save recipient status
#             BulkSMSRecipient.objects.create(
#                 bulk_sms=bulk_sms,
#                 customer=customer,
#                 status=status,
#                 sent_at=sent_time
#             )

#         # Update overall BulkSMS status
#         bulk_sms.status = "Sent" if len(failed_numbers) == 0 else "Failed"
#         bulk_sms.save()

#         # Show messages
#         if failed_numbers:
#             messages.warning(
#                 request,
#                 #f"SMS sent, but some failed: {', '.join(failed_numbers)}"
#                 f"SMS sent Successfull"
#             )
#         else:
#             messages.success(request, "SMS successfully sent to all recipients!")

#         # Show empty form after sending
#         return render(request, "customers/bulk_sms_form.html", {"form": BulkSMSForm()})

#     # GET request or invalid form
#     return render(request, "customers/bulk_sms_form.html", {"form": form})


from django.utils import timezone
from .forms import BulkSMSForm
from .models import BulkSMS, BulkSMSRecipient

@login_required(login_url='/login/')
def bulk_sms_send_view(request):
    selected_project = request.GET.get("project")

    form = BulkSMSForm(request.POST or None)

    # Filter customers by project
    if selected_project:
        customers = Customer.objects.filter(project_id=selected_project, status=True)
    else:
        customers = Customer.objects.filter(status=True)

    form.fields['recipients'].queryset = customers

    projects = ProjectFirstLevelName.objects.all()

    if request.method == "POST" and form.is_valid():
        recipients = form.cleaned_data['recipients']
        message_text = form.cleaned_data['message'].strip()

        if not recipients:
            messages.warning(request, "Please select at least one recipient.")
            return render(request, "customers/bulk_sms_form.html", {
                "form": form,
                "projects": projects,
                "selected_project": selected_project,
            })

        bulk_sms = BulkSMS.objects.create(
            message=message_text,
            status="Pending"
        )

        failed_numbers = []

        for customer in recipients:
            status = "Failed"
            sent_time = None

            try:
                sent_success = send_sms(customer.contact_no, message_text)

                if sent_success:
                    status = "Sent"
                    sent_time = timezone.now()
                else:
                    failed_numbers.append(customer.contact_no)

            except Exception:
                failed_numbers.append(customer.contact_no)

            BulkSMSRecipient.objects.create(
                bulk_sms=bulk_sms,
                customer=customer,
                status=status,
                sent_at=sent_time
            )

        bulk_sms.status = "Sent" if not failed_numbers else "Failed"
        bulk_sms.save()

        messages.success(request, "SMS sending completed.")

        return render(request, "customers/bulk_sms_form.html", {
            "form": BulkSMSForm(),
            "projects": projects,
        })

    return render(request, "customers/bulk_sms_form.html", {
        "form": form,
        "projects": projects,
        "selected_project": selected_project,
    })




from .models import BulkSMSRecipient

@login_required(login_url='/login/')
def bulk_sms_recipient_list(request):
    recipients = (
        BulkSMSRecipient.objects
        .select_related("customer", "bulk_sms")
        .order_by("-sent_at")
    )

    context = {
        "recipients": recipients
    }

    return render(request, "customers/bulk_sms_recipient_list.html", context)

