from django.shortcuts import render, redirect,get_object_or_404
from .models import Property
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import PropertyForm,LandDebitVoucherForm,LandHeadOfExpenseForm
from .models import PropertyOwner
from .forms import PropertyOwnerForm
from sales.models import PropertySales
from sales.forms import InstallmentPaymentForm
from .models import Project
from .forms import ProjectForm
from .forms import JointVentureForm
from .models import JointVenture
from .models import JVPartner
from .forms import JVPartnerForm
from .models import Tenant
from django.views.decorators.csrf import csrf_exempt
from .forms import TenantForm
from .models import LeaseAgreement
from .forms import LeaseAgreementForm
from .models import LeasePayment
from .forms import LeasePaymentForm
from .models import Buyer
from .forms import BuyerForm
from .models import SaleRecord
from .forms import SaleRecordForm
from django.db import transaction
import logging
from django.core.paginator import Paginator
from projects.models import ProjectFirstLevelName
from .models import LandPurchase,LandApprovalPayment,LandDebitVoucher,LandCreditVoucher,LandHeadOfAccount,CashMethod,LandLedgerEntry,LandTransactionHistory,LandHeadOfExpense
from .forms import LandPurchaseForm
from inventories.utils import log_deleted_data
from django.utils import timezone
from datetime import datetime, date

from decimal import Decimal
from django.urls import reverse
from django.utils.timezone import now
from num2words import num2words

from .models import PropertyOwner, LandApprovalPayment



logger = logging.getLogger(__name__)

# List all property owners
@login_required
def property_owner_list(request):
    property_owners = PropertyOwner.objects.all().order_by('id') 
    paginator_owners = Paginator(property_owners, 10)
    page_number_owners = request.GET.get('page')
    properties_page_owners = paginator_owners.get_page(page_number_owners)
    return render(request, 'propertiesowner/property_owner_list.html', {'property_owners': properties_page_owners})



@login_required
def add_property_owner(request):
    if request.method == "POST":
        form = PropertyOwnerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property Owner added successfully!')
            return redirect('property_owner_list')  # Redirect to a list of property owners
    else:
        form = PropertyOwnerForm()

    return render(request, 'propertiesowner/add_property_owner.html', {'form': form})


@login_required
def edit_property_owner(request, id):
    property_owner = get_object_or_404(PropertyOwner, id=id)
    if request.method == 'POST':
        # Add request.FILES to handle file uploads
        form = PropertyOwnerForm(request.POST, request.FILES, instance=property_owner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property Owner Updated successfully!')
            return redirect('property_owner_list')  # Redirect to the list view after successful save
        else:
            print(form.errors)  # For debugging purposes
            messages.error(request, 'There was an error updating the Property Owner. Please try again.')
    else:
        form = PropertyOwnerForm(instance=property_owner)

    return render(request, 'propertiesowner/edit_property_owner.html', {'form': form, 'property_owner': property_owner})


@login_required
def property_owner_detail(request, id):
    owner = get_object_or_404(PropertyOwner, id=id)
    return render(request, 'propertiesowner/property_owner_details.html', {
        'owner': owner
    })

@login_required
def delete_property_owner(request, id):
    property_owner = get_object_or_404(PropertyOwner, id=id)
    if request.method == 'POST':
        log_deleted_data(property_owner, request.user)
        property_owner.delete()
        return redirect('property_owner_list') 
    return render(request, 'propertiesowner/delete_property_owner.html', {'property_owner': property_owner})


# List all projects
@login_required
def project_list(request):
    projects = Project.objects.all().order_by('id') 
    paginator_proj = Paginator(projects, 10)  
    page_number_owners = request.GET.get('page')  
    properties_page_proj = paginator_proj.get_page(page_number_owners) 
    return render(request, 'projectland/project_list.html', {'projects': properties_page_proj})


@login_required
def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project added successfully!')
            return redirect('project_list')
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the project. Please try again.')
    else:
        form = ProjectForm()    
    return render(request, 'projectland/add_project.html', {'form': form})


@login_required
def edit_project(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project Updated successfully!')
            return redirect('project_list')  # Redirect to the project list page
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the project. Please try again.') 
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projectland/edit_project.html', {'form': form, 'project': project})

@login_required
def project_detail(request, project_id):
    project = Project.objects.get(id=project_id)
    return render(request, 'projectland/project_details.html', {'project': project})

@login_required
def delete_project(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        log_deleted_data(project, request.user)
        project.delete()
        return redirect('project_list')  # Redirect to the project list page
    return render(request, 'projectland/delete_project.html', {'project': project})


# List all properties
@login_required
def property_list(request):
    properties = Property.objects.all().order_by('id')   
    paginator = Paginator(properties, 10)  
    page_number = request.GET.get('page')  
    properties_page = paginator.get_page(page_number)  
    return render(request, 'properties/property_list.html', {'properties': properties_page})

@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property added successfully!')
            return redirect('property_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the Property. Please try again.')
    else:
        form = PropertyForm()
    return render(request, 'properties/add_property.html', {'form': form})

@login_required
def edit_property(request, id):
    property_instance = get_object_or_404(Property, id=id)

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_instance)
        
        if form.is_valid():
            form.save()
            logger.info(f"Property {property_instance.id} updated successfully.")
            return redirect('property_list')  # Redirect to the property list after saving
        else:
            logger.error(f"Form is not valid. Errors: {form.errors}")
            return render(request, 'properties/edit_property.html', {
                'form': form,
                'property': property_instance
            })
    else:
        form = PropertyForm(instance=property_instance)

    return render(request, 'properties/edit_property.html', {
        'form': form,
        'property': property_instance
    })


@login_required
def property_detail(request, id):
    property_instance = get_object_or_404(Property, id=id)
    return render(request, 'properties/property_detail.html', {'property': property_instance})

@login_required
def delete_property(request, id):
    property_instance = get_object_or_404(Property, id=id)
    if request.method == 'POST':
        log_deleted_data(property_instance, request.user)
        property_instance.delete()
        return redirect('property_list')  # Redirect to the property list page
    return render(request, 'properties/delete_property.html', {'property': property_instance})

# All Join Venture
# @login_required
# def add_joint_venture(request):
#     propertyowners = PropertyOwner.objects.all() 
#     properties = LandPurchase.objects.all() 
#     form = JointVentureForm(request.POST or None)     
#     if form.is_valid():
#         form.save()
#         messages.success(request, 'Joint Venture Added successfully!')
#         return redirect('joint_venture_list') 
#     else:
#         form = JointVentureForm()
#     return render(request, 'Jointventure/add_joint_venture.html', {'form': form, 'propertyowners': propertyowners, 'properties': properties})




@login_required
def add_joint_venture(request):
    propertyowners = PropertyOwner.objects.all()
    properties = LandPurchase.objects.all()

    if request.method == "POST":
        form = JointVentureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Joint Venture Added successfully!")
            return redirect("joint_venture_list")
    else:
        form = JointVentureForm()

    return render(
        request,
        "Jointventure/add_joint_venture.html",
        {"form": form, "propertyowners": propertyowners, "properties": properties},
    )





@login_required
def joint_venture_list(request):
    joint_ventures = JointVenture.objects.all().order_by('id')     
    paginator = Paginator(joint_ventures, 10)
    page_number = request.GET.get('page')
    joint_ventures_page = paginator.get_page(page_number)
    return render(request, 'Jointventure/joint_venture_list.html', {'joint_ventures': joint_ventures_page})

@login_required
def edit_joint_venture(request, id):
    properties = Property.objects.all() 
    joint_venture = get_object_or_404(JointVenture, id=id)  # Fetch the joint venture based on the id
    if request.method == 'POST':
        form = JointVentureForm(request.POST, instance=joint_venture)
        if form.is_valid():
            form.save()  # Save the edited joint venture
            messages.success(request, 'Joint Venture Updated successfully!')
            return redirect('joint_venture_list')  # Redirect to the list view
    else:
        form = JointVentureForm(instance=joint_venture)  # Pre-populate the form
    return render(request, 'Jointventure/edit_joint_venture.html', {'form': form, 'properties': properties})

@login_required
def joint_venture_detail(request, id):
    joint_venture = get_object_or_404(JointVenture, id=id)
    return render(request, 'Jointventure/join_venture_details.html', {
        'joint_venture': joint_venture,
        'print_time': timezone.now(), 
    })

@login_required
def delete_joint_venture(request, id):
    joint_venture = get_object_or_404(JointVenture, id=id)
    if request.method == 'POST':
        log_deleted_data(joint_venture, request.user)
        joint_venture.delete()  # Delete the joint venture
        return redirect('joint_venture_list')  # Redirect to the list view
    return render(request, 'Jointventure/delete_joint_venture.html', {'joint_venture': joint_venture})




@login_required
def joint_venture_installment_management(request):
    selected_customer_id = request.GET.get('customer_id')
    selected_property_id = request.GET.get('property_id')

    # Distinct customers list
    customers_qs = (
        PropertySales.objects.filter(customer_name__isnull=False)
        .values('customer_name__id', 'customer_name__customer_name')
        .distinct()
    )
    customers = [
        {'id': c['customer_name__id'], 'customer_name': c['customer_name__customer_name']}
        for c in customers_qs
    ]

    plots = PropertySales.objects.none()

    if request.method == 'POST':
        property_sales_id = request.POST.get('property_sales_id')
        project_id = request.POST.get('project_id')
        customer_id = request.POST.get('customer_id')
        sales_amount = request.POST.get('sales_amount')

        payment_types = request.POST.getlist('payment_type[]')
        months = request.POST.getlist('month[]')
        amounts = request.POST.getlist('amount[]')
        cheque_posteds = request.POST.getlist('cheque_posted[]')  # "on" values only if checked
        cheque_dates = request.POST.getlist('cheque_posted_date[]')
        cheque_nos = request.POST.getlist('cheque_no[]')

        def safe_decimal(value, default='0.00'):
            try:
                if not value:
                    return Decimal(default)
                return Decimal(str(value))
            except (InvalidOperation, ValueError):
                return Decimal(default)

        total_rows = len(payment_types)

        if not property_sales_id or total_rows == 0:
            messages.error(request, "Please fill all required fields in the installment payment form.")
            return redirect(request.path_info)

        for i in range(total_rows):
            if not payment_types[i] or not months[i] or not amounts[i]:
                messages.error(request, f"Missing required fields in row {i+1}.")
                return redirect(request.path_info)

            try:
                month = datetime.strptime(months[i] + "-01", "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, f"Invalid month format in row {i+1}.")
                return redirect(request.path_info)
            
            cheque_posted = (i < len(cheque_posteds) and cheque_posteds[i] == 'on')

            cheque_date = None
            if cheque_posted:
                if i < len(cheque_dates) and cheque_dates[i]:
                    try:
                        cheque_date = datetime.strptime(cheque_dates[i], "%Y-%m-%d").date()
                    except ValueError:
                        messages.error(request, f"Invalid cheque date format in row {i+1}.")
                        return redirect(request.path_info)
                else:
                    cheque_date = date.today()
        

            InstallmentPayment.objects.create(
                project_name_id=project_id,
                customer_name_id=customer_id,
                property_sales_id=property_sales_id,
                sales_amount=safe_decimal(sales_amount),
                payment_type=payment_types[i],
                month=month,
                amount=safe_decimal(amounts[i]),
                cheque_posted=cheque_posted,
                cheque_date=cheque_date,
                cheque_no=cheque_nos[i] if i < len(cheque_nos) else '',
                pay_status='Pending',
            )

        # Mark the sale as Done
        PropertySales.objects.filter(id=property_sales_id).update(status='Done')

        messages.success(request, "Installment payments saved successfully and status updated to Done.")
        return redirect(f"/dashboard/flat-plot-sales/installment?customer_id={customer_id}")

    # Fetch plots for dropdown/table
    if selected_customer_id:
        plots = PropertySales.objects.filter(customer_name_id=selected_customer_id).order_by('type', 'flat_no', 'unit_no')
        if selected_property_id:
            plots = plots.filter(id=selected_property_id)
            

    form = InstallmentPaymentForm()
    context = {
        'today': date.today(),
        'customers': customers,
        'plots': plots,
        'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'form': form,  # pass the form instance here
    }
    return render(request, 'Jointventure/joint_venture_installment_management.html', context)



# All JV Partner
@login_required
def jv_partner_list(request):
    partners = JVPartner.objects.all().order_by('id')    
    paginator = Paginator(partners, 10)
    page_number = request.GET.get('page')
    jv_partner_page = paginator.get_page(page_number)
    return render(request, 'Jvpartner/jv_partner_list.html', {'partners': jv_partner_page})

@login_required
def add_jv_partner(request):
    ventures = JointVenture.objects.all() 
    if request.method == 'POST':
        form = JVPartnerForm(request.POST)
        if form.is_valid():
            form.save() 
            messages.success(request, 'JV Partner Added successfully!')
            return redirect('jv_partner_list')  
    else:
        form = JVPartnerForm() 
    return render(request, 'Jvpartner/add_jv_partner.html', {'form': form, 'joint_ventures': ventures})

@login_required
def edit_jv_partner(request, id):
    partner = get_object_or_404(JVPartner, id=id)  # Fetch the JVPartner based on the id
    ventures = JointVenture.objects.all() 
    if request.method == 'POST':
        form = JVPartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()  # Save the edited JVPartner
            messages.success(request, 'JV Partner Updated successfully!')
            return redirect('jv_partner_list')  # Redirect to the list view
    else:
        form = JVPartnerForm(instance=partner)  # Pre-populate the form
    return render(request, 'Jvpartner/edit_jv_partner.html', {'form': form, 'joint_ventures': ventures})

@login_required
def jv_partner_detail(request, id):
    jv_partner = get_object_or_404(JVPartner, id=id)
    return render(request, 'Jvpartner/jv_partner_details.html', {
        'jv_partner': jv_partner
    })

@login_required
def delete_jv_partner(request, id):
    partner = get_object_or_404(JVPartner, id=id)
    if request.method == 'POST':
        log_deleted_data(partner, request.user)
        partner.delete()  # Delete the JVPartner
        return redirect('jv_partner_list')  # Redirect to the list view
    return render(request, 'Jvpartner/delete_jv_partner.html', {'partner': partner})


#List all tenants
@login_required
def tenant_list(request):
    tenants = Tenant.objects.all().order_by('id').order_by('id') 
    paginator = Paginator(tenants, 10)
    page_number = request.GET.get('page')
    tenants_page = paginator.get_page(page_number) 
    
    return render(request, 'tenant/tenant_list.html', {'tenants': tenants_page})

@login_required
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant added successfully!')
            return redirect('tenant_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the Tenant. Please try again.')
    else:
        form = TenantForm()
    return render(request, 'tenant/tenant_form.html', {'form': form})

@login_required
def edit_tenant(request, id):
    tenant = get_object_or_404(Tenant, id=id)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant Updated successfully!')
            return redirect('tenant_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error Updated the Tenant. Please try again.')
    else:
        form = TenantForm(instance=tenant)
    return render(request, 'tenant/tenant_form.html', {'form': form})

@login_required
def tenant_detail(request, id):
    tenant = get_object_or_404(Tenant, id=id)
    return render(request, 'tenant/tenant_details.html', {
        'tenant': tenant
    })

@login_required
def delete_tenant(request, id):
    tenant = get_object_or_404(Tenant, id=id)
    log_deleted_data(tenant, request.user)
    tenant.delete()
    return redirect('tenant_list')  

@login_required
def tenant_pay_history(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    lease_agreements = LeaseAgreement.objects.filter(tenant=tenant)    
    return render(request, 'tenant/lease_agreement_pay_list.html', {
        'tenant': tenant,
        'lease_agreements': lease_agreements,
    })



# List all lease agreements
@login_required
def lease_agreement_list(request):
    lease_agreements = LeaseAgreement.objects.all().order_by('id')  
    paginator = Paginator(lease_agreements, 10)
    page_number = request.GET.get('page')
    tlease_agreements_page = paginator.get_page(page_number)
    return render(request, 'leaseagreement/lease_agreement_list.html', {'lease_agreements': tlease_agreements_page})


@login_required
def add_lease_agreement(request):
    if request.method == 'POST':
        form = LeaseAgreementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  
            messages.success(request, 'Lease Agreement Added successfully!')
            return redirect('lease_agreement_list')  
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the Lease Agreement. Please try again.')
    else:
        form = LeaseAgreementForm()
        properties = LandPurchase.objects.all() 
        tenant = Tenant.objects.all() 
        print(tenant)
        context ={
            'form': form,
            'properties': properties,
            'tenant': tenant,
        }
    return render(request, 'leaseagreement/lease_agreement_form.html', context)


@login_required
def edit_lease_agreement(request, id):
    lease_agreement = get_object_or_404(LeaseAgreement, id=id)
    if request.method == 'POST':
        form = LeaseAgreementForm(request.POST, instance=lease_agreement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lease Agreement Updated successfully!')
            return redirect('lease_agreement_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error Updated the Lease Agreement. Please try again.')
    else:
        form = LeaseAgreementForm(instance=lease_agreement)
    return render(request, 'leaseagreement/lease_agreement_form.html', {'form': form})


@login_required
def lease_agreement_detail(request, id):
    lease_agreement = get_object_or_404(LeaseAgreement, id=id)
    return render(request, 'leaseagreement/lease_agreement_details.html', {
        'lease_agreement': lease_agreement
    })


@login_required
def delete_lease_agreement(request, id):
    lease_agreement = get_object_or_404(LeaseAgreement, id=id)
    log_deleted_data(lease_agreement, request.user)
    lease_agreement.delete()
    return redirect('lease_agreement_list')  # Redirect to lease agreements list after deletion


# List all lease payments
@login_required
def lease_payment_list(request):
    lease_payments = LeasePayment.objects.all().order_by('id') 
    paginator = Paginator(lease_payments, 10)
    page_number = request.GET.get('page')
    tlease_payment_page = paginator.get_page(page_number)
    return render(request, 'leasepayment/lease_payment_list.html', {'lease_payments': tlease_payment_page})

@login_required
def add_lease_payment(request):
    if request.method == 'POST':
        form = LeasePaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lease Payment Added successfully!')
            return redirect('lease_payment_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error Added the Lease Payment. Please try again.')
    else:
        form = LeasePaymentForm()
        landagreement = LeaseAgreement.objects.all() 
        context ={
            'form': form,
            'lease_agreement': landagreement,
        }
    return render(request, 'leasepayment/lease_payment_form.html', context)

@login_required
def lease_payment_detail(request, id):
    lease_payment = get_object_or_404(LeasePayment, id=id)
    return render(request, 'leasepayment/lease_payment_details.html', {
        'lease_payment': lease_payment
    })

@login_required
def edit_lease_payment(request, id):
    lease_payment = get_object_or_404(LeasePayment, id=id)
    if request.method == 'POST':
        form = LeasePaymentForm(request.POST, instance=lease_payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lease Payment Updated successfully!')
            return redirect('lease_payment_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error Updated the Lease Payment. Please try again.')
    else:
        form = LeasePaymentForm(instance=lease_payment)
    return render(request, 'leasepayment/lease_payment_form.html', {'form': form})

@login_required
def delete_lease_payment(request, id):
    lease_payment = get_object_or_404(LeasePayment, id=id)
    log_deleted_data(lease_payment, request.user)
    lease_payment.delete()
    return redirect('lease_payment_list')  # Redirect to lease payments list after deletion


# List all buyers
@login_required
def buyer_list(request):
    # Fetch all buyers, including their total sale price
    buyers = Buyer.objects.all().order_by('id')
    
    # Paginate the list of buyers (10 per page)
    paginator = Paginator(buyers, 10)
    page_number = request.GET.get('page')
    buyers_page = paginator.get_page(page_number) 
    
    return render(request, 'buyer/buyer_list.html', {'buyers': buyers_page})


@login_required
def add_buyer(request):
    if request.method == 'POST':
        form = BuyerForm(request.POST, request.FILES)  # Include request.FILES to handle image uploads
        if form.is_valid():
            form.save()
            messages.success(request, 'Buyer Added successfully!')
            return redirect('buyer_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error adding the Buyer. Please try again.')
    else:
        form = BuyerForm()
    return render(request, 'buyer/buyer_form.html', {'form': form})

from django.shortcuts import render, get_object_or_404, redirect
from .forms import BuyerForm
from .models import Buyer

@login_required
def edit_buyer(request, id):
    buyer = get_object_or_404(Buyer, id=id)
    
    if request.method == 'POST':
        form = BuyerForm(request.POST, request.FILES, instance=buyer)  # Pass request.FILES to handle image upload
        if form.is_valid():
            form.save()
            return redirect('buyer_detail', id=buyer.id)
    else:
        form = BuyerForm(instance=buyer)
    
    return render(request, 'buyer/buyer_form.html', {'form': form, 'buyer': buyer})

@login_required
def buyer_detail(request, id):
    buyer = get_object_or_404(Buyer, id=id)
    return render(request, 'buyer/buyer_details.html', {
        'buyer': buyer
    })

@login_required
def delete_buyer(request, id):
    buyer = get_object_or_404(Buyer, id=id)
    log_deleted_data(buyer, request.user)
    buyer.delete()
    return redirect('buyer_list')  # Redirect to buyer list after deleting


@login_required
def buyer_pay_history(request, buyer_id):
    buyer = get_object_or_404(Buyer, pk=buyer_id) 
    sale_records = SaleRecord.objects.filter(buyer=buyer)    
    return render(request, 'buyer/buyer_pay_history.html', {
        'buyer': buyer,
        'sale_records': sale_records,
    })


# List all sale records
@login_required
def sale_record_list(request):
    sale_records = SaleRecord.objects.all().order_by('id')
    paginator = Paginator(sale_records, 10)
    page_number = request.GET.get('page')
    sale_records_page = paginator.get_page(page_number) 
    return render(request, 'salerecord/sale_record_list.html', {'sale_records': sale_records_page})


@login_required
def add_sale_record(request):
    if request.method == 'POST':
        form = SaleRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale Record Added successfully!')
            return redirect('sale_record_list')  # Redirect to a list or other page
        else:
            print(form.errors)
            messages.error(request, 'There was an error adding the Sale Record. Please try again.')
    else:
        form = SaleRecordForm()
    return render(request, 'salerecord/sale_record_form.html', {'form': form})


@login_required
def edit_sale_record(request, id):
    sale_record = get_object_or_404(SaleRecord, id=id)
    if request.method == 'POST':
        form = SaleRecordForm(request.POST, instance=sale_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale Record Updated successfully!')
            return redirect('sale_record_list') 
        else:
            print(form.errors)  
            messages.error(request, 'There was an error Updated the Sale Record. Please try again.')
    else:
        form = SaleRecordForm(instance=sale_record)
    return render(request, 'salerecord/sale_record_form.html', {'form': form})

@login_required
def sale_record_detail(request, id):
    sale_record = get_object_or_404(SaleRecord, id=id)
    return render(request, 'salerecord/saleRecord_details.html', {
        'sale_record': sale_record
    })


@login_required
def delete_sale_record(request, id):
    sale_record = get_object_or_404(SaleRecord, id=id)
    log_deleted_data(sale_record, request.user)
    sale_record.delete()
    return redirect('sale_record_list')  # Redirect to sale record list after deleting



## lilahetalah ----
@login_required
def lilahetalah_list(request):
    lands = LandPurchase.objects.exclude(lilahetalah_per='').order_by('-id')
    return render(request, 'landpurchase/lilahetalah_list.html', {'landpurchases': lands})
    

@login_required
def lilahetalah_details(request, pk):
    land = get_object_or_404(
        LandPurchase.objects.exclude(lilahetalah_per=''),
        pk=pk
    )
    return render(request, 'landpurchase/lilahetalah_details.html', {'lanpurchase': land})
    



## Media pay ----
@login_required
def media_pay_list(request):
    lands = LandPurchase.objects.exclude(media_per='').order_by('-id')
    return render(request, 'landpurchase/media_pay_list.html', {'landpurchases': lands})
    

@login_required
def media_pay_details(request, pk):
    land = get_object_or_404(
        LandPurchase.objects.exclude(media_per=''),
        pk=pk
    )
    return render(request, 'landpurchase/media_pay_details.html', {'lanpurchase': land})
    
    

## land purchases ----
@login_required
def land_list(request):
    lands = LandPurchase.objects.all()
    return render(request, 'landpurchase/property_list.html', {'landpurchases': lands})

@login_required
def land_add(request):
    if request.method == 'POST':
        form = LandPurchaseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('land_list')
    else:
        form = LandPurchaseForm()

    # ✅ Make sure to pass the queryset here
    property_owners = PropertyOwner.objects.all()
    return render(request, 'landpurchase/landpurchase_add.html', {
        'form': form,
        'property_owners': property_owners
    })



@login_required
def upload_csv_upload(request):
    return render(request, 'records/file_record_list.html')


import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import RecordFile

@login_required
def upload_csv(request):
    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, "Please select a CSV file to upload.")
            return redirect('file_record_list')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "This is not a valid CSV file.")
            return redirect('file_record_list')

        try:
            # Handle possible encoding variants from Excel exports
            try:
                data_set = csv_file.read().decode('UTF-8')
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode('latin-1')

            io_string = io.StringIO(data_set)
            
            # Read all rows using csv.reader
            csv_reader = csv.reader(io_string, delimiter=',')
            
            # Safely skip header row
            try:
                header = next(csv_reader)
            except StopIteration:
                messages.error(request, "The uploaded CSV file is empty.")
                return redirect('file_record_list')
            
            created_count = 0
            skipped_count = 0

            for row_idx, row in enumerate(csv_reader, start=2):
                # Clean up whitespace from all elements in the row
                row = [cell.strip() for cell in row]
                
                # Check if the row is completely empty
                if not any(row):
                    continue

                # Pad row with empty strings if it has less than 9 columns
                # This prevents rows with empty trailing columns from being completely ignored
                if len(row) < 9:
                    row.extend([''] * (9 - len(row)))

                # Unpack the fixed length list safely
                date_str, file_type, file_no, dag_no, owner_client, work_type, status, responsible, remarks = row[:9]

                # If file_no is critical, adjust this block. 
                # If duplicates are allowed now, you can completely comment out this check:
                if file_no and RecordFile.objects.filter(file_no=file_no).exists():
                    skipped_count += 1
                    continue

                # Handle Excel/raw date parsing safely
                parsed_date = None
                if date_str and date_str != "0000-00-00":
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                
                # Normalize choice fields to match model expectations
                status_cleaned = status.title() if status else 'Pending'
                if status_cleaned not in ['Pending', 'In Progress', 'Completed']:
                    status_cleaned = 'Pending'

                # Create the record safely
                RecordFile.objects.create(
                    date=parsed_date, # Allows null as per your updated model
                    file_type=file_type if file_type else None,
                    file_no=file_no,
                    dag_no=dag_no,
                    owner_client=owner_client,
                    work_type=work_type,
                    status=status_cleaned,
                    responsible=responsible,
                    remarks=remarks
                )
                created_count += 1

            messages.success(request, f"Successfully uploaded {created_count} records. (Skipped {skipped_count} duplicates).")
            return redirect('file_record_list')

        except Exception as e:
            messages.error(request, f"Error processing file near row {row_idx if 'row_idx' in locals() else 'unknown'}: {str(e)}")
            return redirect('file_record_list')

    return redirect('file_record_list')
    
    

# import csv
# import io
# from datetime import datetime
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from .models import RecordFile

# @login_required
# def upload_csv(request):
#     if request.method == "POST":
#         csv_file = request.FILES.get('csv_file')
        
#         if not csv_file:
#             messages.error(request, "Please select a CSV file to upload.")
#             return redirect('file_record_list')
        
#         if not csv_file.name.endswith('.csv'):
#             messages.error(request, "This is not a valid CSV file.")
#             return redirect('file_record_list')

#         try:
#             data_set = csv_file.read().decode('UTF-8')
#             io_string = io.StringIO(data_set)
#             next(io_string) # Skip header row
            
#             created_count = 0
#             skipped_count = 0

#             for row in csv.reader(io_string, delimiter=','):
#                 if len(row) < 9:
#                     continue
                
#                 date_str, file_type, file_no, dag_no, owner_client, work_type, status, responsible, remarks = row
                
#                 # Prevent duplicate entry crashes
#                 if RecordFile.objects.filter(file_no=file_no.strip()).exists():
#                     skipped_count += 1
#                     continue

#                 try:
#                     parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
#                 except ValueError:
#                     parsed_date = datetime.today().date()

#                 RecordFile.objects.create(
#                     date=parsed_date,
#                     file_type=file_type.strip(),
#                     file_no=file_no.strip(),
#                     dag_no=dag_no.strip(),
#                     owner_client=owner_client.strip(),
#                     work_type=work_type.strip(),
#                     status=status.strip() if status.strip() else 'Pending',
#                     responsible=responsible.strip(),
#                     remarks=remarks.strip()
#                 )
#                 created_count += 1

#             messages.success(request, f"Successfully uploaded {created_count} records. (Skipped {skipped_count} duplicates).")
#             return redirect('file_record_list')

#         except Exception as e:
#             messages.error(request, f"Error processing file: {str(e)}")
#             return redirect('file_record_list')

#     return redirect('file_record_list')
    
    

from .models import RecordFile
from .forms import RecordFileForm

@login_required
def file_record_list(request):
    records = RecordFile.objects.all().order_by('-id')
    return render(request, 'records/record_list.html', {'records': records})

# @login_required
# def file_record_create(request):
#     if request.method == "POST":
#         form = RecordFileForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('file_record_list')
#     else:
#         form = RecordFileForm()
    
#     return render(request, 'records/record_form.html', {'form': form})



from django.contrib import messages
from django.shortcuts import redirect, render

@login_required
def file_record_create(request):
    if request.method == "POST":
        form = RecordFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Record created successfully!")
            return redirect('file_record_list')
    else:
        form = RecordFileForm()
    
    return render(request, 'records/record_form.html', {'form': form})
    

@login_required
def file_record_detail(request, pk):
    record = get_object_or_404(RecordFile, pk=pk)
    return render(request, 'records/detail.html', {'record': record})


@login_required
def file_record_update(request, pk):
    record = get_object_or_404(RecordFile, pk=pk)

    if request.method == "POST":
        form = RecordFileForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Record updated successfully.")
            return redirect('file_record_list')
    else:
        form = RecordFileForm(instance=record)

    return render(request, 'records/record_form.html', {
        'form': form,
        'title': 'Edit Record'
    })

# @login_required
# def file_record_update(request, pk):
#     record = get_object_or_404(RecordFile, pk=pk)

#     if request.method == "POST":
#         form = RecordFileForm(request.POST, instance=record)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Record updated successfully.")
#             return redirect('file_record_list')
#     else:
#         form = RecordFileForm(instance=record)

#     return render(request, 'records/record_form.html', {
#         'form': form,
#         'title': 'Edit Record'
#     })

@login_required
def file_record_delete(request, pk):
    record = get_object_or_404(RecordFile, pk=pk)

    if request.method == 'POST':
        record.delete()
        messages.success(request, "Record deleted successfully.")
        return redirect('file_record_list')

    return render(request, 'records/delete.html', {'record': record})
    

@login_required
def get_next_file_no(request):
    file_type = request.GET.get('file_type')

    if not file_type:
        return JsonResponse({'file_no': ''})

    last_record = (
        RecordFile.objects
        .filter(file_type=file_type)
        .order_by('-id')
        .first()
    )

    if last_record and last_record.file_no:
        try:
            last_no = int(last_record.file_no.split('-')[-1])
        except:
            last_no = 1000
    else:
        last_no = 1000

    next_no = last_no + 1

    return JsonResponse({
        'file_no': f'{file_type}-{next_no}'
    })
    


from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import RecordFile


@login_required
def file_record_dashboard(request):
    total_files = RecordFile.objects.count()
    pending_files = RecordFile.objects.filter(
        status='Pending'
    ).count()

    in_progress_files = RecordFile.objects.filter(
        status='In Progress'
    ).count()

    completed_files = RecordFile.objects.filter(
        status='Completed'
    ).count()

    file_type_summary = (
        RecordFile.objects
        .values('file_type')
        .annotate(total=Count('id'))
        .order_by('file_type')
    )

    latest_records = (
        RecordFile.objects
        .order_by('-date', '-id')[:10]
    )

    context = {
        'total_files': total_files,
        'pending_files': pending_files,
        'in_progress_files': in_progress_files,
        'completed_files': completed_files,
        'file_type_summary': file_type_summary,
        'latest_records': latest_records,
    }

    return render(
        request,
        'records/dashboard.html',
        context
    )
    
    
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import LandPurchase

@login_required
def land_dashboard(request):
    # Fetch all purchases for the table
    land_purchases = LandPurchase.objects.select_related('land_supplier').all()
    
    # Handle search/filter queries if passed via GET
    search_query = request.GET.get('search', '')
    if search_query:
        land_purchases = land_purchases.filter(
            mouza_name__icontains=search_query
        ) | land_purchases.filter(
            file_name__icontains=search_query
        ) | land_purchases.filter(
            land_supplier__name__icontains=search_query  # Assumes PropertyOwner has a name field
        )

    # Calculate Summary Statistics
    total_records = LandPurchase.objects.count()
    total_area = LandPurchase.objects.aggregate(Sum('land_area'))['land_area__sum'] or 0
    total_investment = LandPurchase.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    pending_approvals = LandPurchase.objects.filter(approval_status='pending').count()

    context = {
        'landpurchases': land_purchases,
        'total_records': total_records,
        'total_area': total_area,
        'total_investment': total_investment,
        'pending_approvals': pending_approvals,
        'search_query': search_query,
    }
    return render(request, 'landpurchase/land_dashboard.html', context)
    
    
    
@login_required
def land_edit(request, pk):
    land = get_object_or_404(LandPurchase, pk=pk)
    if request.method == 'POST':
        form = LandPurchaseForm(request.POST, request.FILES, instance=land)
        if form.is_valid():
            form.save()
            return redirect('land_list')
    else:
        form = LandPurchaseForm(instance=land)
    return render(request, 'landpurchase/landpurchase_edit.html', {'form': form})

@login_required
def land_delete(request, pk):
    land = get_object_or_404(LandPurchase, pk=pk)
    if request.method == 'POST':
        land.delete()
        return redirect('land_list')
    return render(request, 'landpurchase/delete_property.html', {'land': land})

@login_required
def land_detail(request, pk):
    land = get_object_or_404(LandPurchase, pk=pk)
    return render(request, 'landpurchase/property_detail.html', {'lanpurchase': land})



# @login_required
# def land_ledger_list(request):
#     land_ledgers = LandLedgerEntry.objects.select_related('owner', 'land_purchase', 'cash_type', 'head_of_account').order_by('-date')
#     return render(request, 'landpurchase/land_ledger_list.html', {'land_ledgers': land_ledgers})




@login_required
def land_ledger_list(request):
    selected_supplier = request.GET.get('supplier', '')

    land_ledgers = LandLedgerEntry.objects.select_related(
        'owner', 'land_purchase', 'cash_type', 'head_of_account'
    ).order_by('-date')

    if selected_supplier:
        land_ledgers = land_ledgers.filter(owner__id=selected_supplier)

    suppliers = LandLedgerEntry.objects.select_related('owner').values_list(
        'owner__id', 'owner__owner_name'
    ).distinct()

    context = {
        'land_ledgers': land_ledgers,
        'suppliers': suppliers,
        'selected_supplier': selected_supplier,
    }
    return render(request, 'landpurchase/land_ledger_list.html', context)



@login_required
def filter_land_ledger_new(request):
    """Filter land ledger and open results in a new page"""
    supplier_id = request.GET.get('supplier', '')
    ledgers = LandLedgerEntry.objects.select_related('owner', 'head_of_account').order_by('-date')

    if supplier_id:
        ledgers = ledgers.filter(owner__id=supplier_id)

    # Pass suppliers for dropdown to maintain selected value
    suppliers = [(owner.id, owner.owner_name) for owner in PropertyOwner.objects.all()]
    
    return render(request, 'landpurchase/land_ledger_filtered.html', {
        'land_ledgers': ledgers,
        'suppliers': suppliers,
        'selected_supplier': supplier_id,
    })



@login_required
def approve_land_voucher(request, pk):
    land = get_object_or_404(LandPurchase, pk=pk)

    land.approval_status = 'Approved'
    land.save()

    owner = land.land_supplier if hasattr(land, 'land_supplier') else None

    payment, created = LandApprovalPayment.objects.get_or_create(
        land_purchase=land,
        defaults={
            'land_uniq_id': f"LAND-{land.id:05d}",
            'purch_amount': land.total_price or Decimal('0.00'),
            'purchase_date': timezone.now().date(),
            'owner': owner,
        }
    )

    if created:
        print(f"LandApprovalPayment created for {land} with owner {owner}")
    else:
        print(f"Payment already exists for {land}")

    return redirect('land_detail', pk=pk)





@login_required
def land_payment_list(request):
    # Fetch all approval payment records with related purchase & owner
    payments = LandApprovalPayment.objects.select_related('land_purchase', 'owner')

    # Group payments by owner
    summary_dict = {}

    for p in payments:
        # Use the owner field directly from LandApprovalPayment
        owner = p.owner
        owner_name = owner.owner_name if owner else "N/A"
        owner_id = owner.id if owner else None
        mouza_name = p.land_purchase.mouza_name if p.land_purchase else "N/A"

        # Use a tuple of owner_id + mouza_name as key to avoid collision if multiple properties per owner
        key = (owner_id, mouza_name)

        # Initialize owner entry in dict if not present
        if key not in summary_dict:
            summary_dict[key] = {
                'owner_name': owner_name,
                'owner_id': owner_id,
                'mouza_name': mouza_name,
                'purchase_pay': 0.0,
                'approval_pay': 0.0,
                'advance_pay': 0.0,
                'requisition_pay': 0.0,  # for compatibility
                'id': p.id,
            }

        # Sum by payment_type field
        amount = float(p.purch_amount or 0)
        if p.payment_type == 'purchase_pay':
            summary_dict[key]['purchase_pay'] += amount
        elif p.payment_type == 'approval_pay':
            summary_dict[key]['approval_pay'] += amount
        elif p.payment_type == 'advance_pay':
            summary_dict[key]['advance_pay'] += amount
        elif p.payment_type == 'requisition_pay':
            summary_dict[key]['requisition_pay'] += amount

    # Calculate balances and payment status
    summary = []
    for data in summary_dict.values():
        purchase_pay = data['purchase_pay']
        approval_pay = data['approval_pay']
        advance_pay = data['advance_pay']

        payments = approval_pay + advance_pay

        # fallback if all are zero
        if purchase_pay == 0 and approval_pay == 0 and advance_pay == 0:
            balance = abs(purchase_pay)

        balance = purchase_pay - payments
        if purchase_pay > payments:
            status = "Payable"
        elif purchase_pay < payments:
            status = "Receivable"
        else:
            status = "Balanced"
        balance = abs(balance) 

        data['balance'] = abs(balance)
        data['status'] = status
        summary.append(data)

    return render(request, 'landpurchase/land_payment_list.html', {
        'summary': summary,
    })





# @login_required
# @transaction.atomic
# def land_owner_payment(request, id):
#     # Try to get the owner; if not exist, check via linked land purchases
#     owner = PropertyOwner.objects.filter(id=id).first()
#     if not owner:
#         land_purchase = LandPurchase.objects.filter(id=id).first()
#         if land_purchase and land_purchase.land_supplier:
#             owner = land_purchase.land_supplier
#         else:
#             messages.error(request, "Property owner not found.")
#             return redirect('land_payment_list')

#     # Get all land purchases for this owner
#     land_purchases = LandPurchase.objects.filter(land_supplier=owner)
#     payments = LandApprovalPayment.objects.filter(land_purchase__in=land_purchases)

#     # Calculate balances
#     total_purchase = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'purchase_pay')
#     total_approval = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'approval_pay')
#     total_advance = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'advance_pay')
#     balance_amount = max(total_purchase - (total_approval + total_advance), 0)

#     head_of_accounts = LandHeadOfAccount.objects.all()
#     cash_methods = CashMethod.objects.all()

#     if request.method == 'POST':
#         form = LandDebitVoucherForm(request.POST)
#         if form.is_valid():
#             debit_voucher = form.save(commit=False)
#             debit_voucher.land_purchases = land_purchases
#             debit_voucher.type = "Land Owner"
#             debit_voucher.owner = owner  # Assign owner here

#             if not debit_voucher.remark:
#                 debit_voucher.remark = 'Owner Payment'

#             # Auto-generate MR/Bill No
#             if not debit_voucher.mr_or_bill_no:
#                 base_code = "MBD-"
#                 last = LandDebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#                 next_id = (last.id + 1) if last else 1
#                 generated_code = f"{base_code}{next_id:05d}"
#                 while LandDebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"
#                 debit_voucher.mr_or_bill_no = generated_code

#             debit_voucher.approval_status = True
#             debit_voucher.save()

#             # Create payments and ledger entries
#             per_purchase_amount = debit_voucher.amount / len(land_purchases) if land_purchases else 0
#             for purchase in land_purchases:
#                 LandApprovalPayment.objects.create(
#                     land_purchase=purchase,
#                     owner=owner,
#                     land_uniq_id=purchase.id,
#                     payment_type='approval_pay',
#                     purch_amount=per_purchase_amount,
#                     purchase_date=debit_voucher.date,
#                     debit_voucher=debit_voucher
#                 )

#                 ledger_mr_no = debit_voucher.mr_or_bill_no
#                 suffix = 1
#                 while LandLedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
#                     ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
#                     suffix += 1

#                 LandLedgerEntry.objects.create(
#                     land_purchase=purchase,
#                     type="Land Owner",
#                     owner=owner,
#                     expense=None,
#                     cash_type=debit_voucher.cash_type,
#                     head_of_account=debit_voucher.head_of_account,
#                     mr_or_bill_no=ledger_mr_no,
#                     date=debit_voucher.date,
#                     description=debit_voucher.remark,
#                     debit=per_purchase_amount,
#                     credit=0,
#                     carrier=debit_voucher.carrier,
#                     loan_status='payment',
#                     tbl_id=debit_voucher.id,
#                     tbl_name='LandPayment',
#                     type_name='Owner Payment'
#                 )

#             # Update CashMethod
#             if debit_voucher.cash_type:
#                 debit_voucher.cash_type.type_amount -= debit_voucher.amount
#                 debit_voucher.cash_type.type_note = f"Payment of voucher ID {debit_voucher.id}"
#                 debit_voucher.cash_type.save()

#             messages.success(request, "Payment saved successfully.")
#             return redirect('land_payment_list')
#     else:
#         initial_data = {
#             'amount': balance_amount,
#             'create_dr_by': request.user.get_full_name(),
#         }
#         form = LandDebitVoucherForm(initial=initial_data)

#     context = {
#         'form': form,
#         'today': date.today(),
#         'owner': owner,
#         'balance_amount': balance_amount,
#         'land_purchases': land_purchases,
#         'head_of_accounts': head_of_accounts,
#         'cash_methods': cash_methods,
#     }
#     return render(request, 'landpurchase/land_owner_payment.html', context)





@login_required
@transaction.atomic
def land_owner_payment(request, id):
    # Step 1: Find owner
    owner = PropertyOwner.objects.filter(id=id).first()
    if not owner:
        land_purchase = LandPurchase.objects.filter(id=id).first()
        if land_purchase and land_purchase.land_supplier:
            owner = land_purchase.land_supplier
        else:
            messages.error(request, "Property owner not found.")
            return redirect('land_payment_list')

    # Step 2: Gather purchase/payment info
    land_purchases = LandPurchase.objects.filter(land_supplier=owner)
    payments = LandApprovalPayment.objects.filter(land_purchase__in=land_purchases)

    total_purchase = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'purchase_pay')
    total_approval = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'approval_pay')
    total_advance = sum(p.purch_amount or 0 for p in payments if p.payment_type == 'advance_pay')
    balance_amount = max(total_purchase - (total_approval + total_advance), 0)

    head_of_accounts = LandHeadOfAccount.objects.all()
    cash_methods = CashMethod.objects.all()

    # Step 3: Handle POST (form submit)
    if request.method == 'POST':
        form = LandDebitVoucherForm(request.POST)
        if form.is_valid():
            debit_voucher = form.save(commit=False)
            debit_voucher.land_purchases = land_purchases
            debit_voucher.type = "Land Owner"
            debit_voucher.owner = owner

            if not debit_voucher.remark:
                debit_voucher.remark = 'Owner Payment'

            # Auto-generate MR/Bill No
            if not debit_voucher.mr_or_bill_no:
                base_code = "MBD-"
                last = LandDebitVoucher.objects.filter(
                    mr_or_bill_no__startswith=base_code
                ).order_by('-id').first()
                next_id = (last.id + 1) if last else 1
                generated_code = f"{base_code}{next_id:05d}"
                while LandDebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"
                debit_voucher.mr_or_bill_no = generated_code

            debit_voucher.approval_status = True
            debit_voucher.save()

            # Step 4: Create related payments, ledgers, and history
            per_purchase_amount = debit_voucher.amount / len(land_purchases) if land_purchases else 0

            for purchase in land_purchases:
                # Create LandApprovalPayment
                LandApprovalPayment.objects.create(
                    land_purchase=purchase,
                    owner=owner,
                    land_uniq_id=purchase.id,
                    payment_type='approval_pay',
                    purch_amount=per_purchase_amount,
                    purchase_date=debit_voucher.date,
                    debit_voucher=debit_voucher
                )

                # Create LandLedgerEntry
                ledger_mr_no = debit_voucher.mr_or_bill_no
                suffix = 1
                while LandLedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
                    ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
                    suffix += 1

                LandLedgerEntry.objects.create(
                    land_purchase=purchase,
                    type="Land Owner",
                    owner=owner,
                    expense=None,
                    cash_type=debit_voucher.cash_type,
                    head_of_account=debit_voucher.head_of_account,
                    mr_or_bill_no=ledger_mr_no,
                    date=debit_voucher.date,
                    description=debit_voucher.remark,
                    debit=per_purchase_amount,
                    credit=0,
                    carrier=debit_voucher.carrier,
                    loan_status='payment',
                    tbl_id=debit_voucher.id,
                    tbl_name='LandPayment',
                    type_name='Owner Payment'
                )

                # Create Transaction History
                LandTransactionHistory.objects.create(
                    land_purchase=purchase,
                    type="Land Owner",
                    owner=owner,
                    expense=None,
                    cash_type=debit_voucher.cash_type,
                    head_of_account=debit_voucher.head_of_account,
                    amount=per_purchase_amount,
                    date=debit_voucher.date,
                    type_name='Owner Payment',
                    reference=debit_voucher.mr_or_bill_no,
                    create_by=request.user.get_full_name(),
                    particulars=f"Owner payment for {owner.owner_name or owner} (Voucher: {debit_voucher.mr_or_bill_no})",
                    tbl_id=debit_voucher.id
                )

            # Step 5: Update cash method balance
            if debit_voucher.cash_type:
                debit_voucher.cash_type.type_amount -= debit_voucher.amount
                debit_voucher.cash_type.type_note = f"Payment of voucher ID {debit_voucher.id}"
                debit_voucher.cash_type.save()

            # ✅ Step 6: Ensure all approval payments are linked to this voucher
            if debit_voucher.id:
                LandApprovalPayment.objects.filter(
                    land_purchase__in=land_purchases,
                    owner=owner,
                    payment_type='approval_pay'
                ).update(debit_voucher=debit_voucher)

            messages.success(request, "Payment and transaction recorded successfully.")
            return redirect('land_payment_list')

    # Step 7: Handle GET (form display)
    else:
        initial_data = {
            'amount': balance_amount,
            'create_dr_by': request.user.get_full_name(),
        }
        form = LandDebitVoucherForm(initial=initial_data)

    # Step 8: Render context
    context = {
        'form': form,
        'today': date.today(),
        'owner': owner,
        'balance_amount': balance_amount,
        'land_purchases': land_purchases,
        'head_of_accounts': head_of_accounts,
        'cash_methods': cash_methods,
    }
    return render(request, 'landpurchase/land_owner_payment.html', context)






from decimal import Decimal
from num2words import num2words
from django.utils.timezone import now

@login_required
def land_payment_pdf(request, owner_id):
    owner = get_object_or_404(PropertyOwner, id=owner_id)

    # Fetch payments through LandPurchase -> land_supplier
    payments = (
        LandApprovalPayment.objects
        .filter(land_purchase__land_supplier=owner)
        .select_related('land_purchase', 'debit_voucher')
        .order_by('purchase_date')
    )

    # Initialize totals
    total = {
        'purchase_pay': Decimal('0.00'),
        'approval_pay': Decimal('0.00'),
        'advance_pay': Decimal('0.00'),
    }

    for p in payments:
        amount = p.purch_amount or Decimal('0.00')
        if p.payment_type == 'purchase_pay':
            total['purchase_pay'] += amount
        elif p.payment_type == 'approval_pay':
            total['approval_pay'] += amount
        elif p.payment_type == 'advance_pay':
            total['advance_pay'] += amount

    # Convert totals to float for calculations
    purchase_pay = float(total['purchase_pay'])
    approval_pay = float(total['approval_pay'])
    advance_pay = float(total['advance_pay'])
    payments_total = approval_pay + advance_pay

    # Special case: no purchase and no payments
    if purchase_pay == 0 and approval_pay == 0 and advance_pay == 0:
        balance = 0.0
        status = "Balanced"
    else:
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
        except Exception:
            return f"{amount} taka only"

    context = {
        'owner': owner,
        'payments': payments,
        'total': total,
        'balance': balance,
        'status': status,
        'balance_in_words': amount_to_words(balance),
        'print_time': now(),
    }

    return render(request, 'landpurchase/land_payment_pdf.html', context)







@login_required
@transaction.atomic
def update_payment_amount(request, payment_id):
    payment = get_object_or_404(LandApprovalPayment, id=payment_id)

    if request.method == "POST":
        try:
            # Get new amount from POST
            new_amount = Decimal(request.POST.get("purch_amount", "0").strip() or "0")
            
            # Update payment amount
            payment.purch_amount = new_amount
            payment.save()

            # If linked to a debit voucher, update it
            debit_voucher = payment.debit_voucher
            if debit_voucher:
                debit_voucher.amount = new_amount
                debit_voucher.save()

                # Update related Ledger Entries
                ledger_entries = LandLedgerEntry.objects.filter(
                    tbl_id=str(debit_voucher.id)
                )
                for ledger in ledger_entries:
                    ledger.debit = new_amount  # adjust if needed (debit/credit logic)
                    ledger.save()

                # Update related Transaction History
                transactions = LandTransactionHistory.objects.filter(
                    tbl_id=str(debit_voucher.id)
                )
                for txn in transactions:
                    txn.amount = new_amount
                    txn.save()

            return JsonResponse({
                "success": True,
                "message": "Payment and related records updated successfully.",
                "new_amount": f"{new_amount:.2f}"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error updating amount: {str(e)}"
            })

    return JsonResponse({
        "success": False,
        "message": "Invalid request method."
    })
    
    
### Land debit voucher code 
@login_required
def land_debitvoucher_list(request):
    search_query = request.GET.get('q', '')

    vouchers = LandDebitVoucher.objects.select_related(
        'land_purchase', 'land_purchase__land_supplier',
        'owner',
        'cash_type',
        'head_of_account'
    ).order_by('-date', '-id')

    if search_query:
        vouchers = vouchers.filter(
            Q(land_purchase__mouza_name__icontains=search_query) |
            Q(land_purchase__land_supplier__owner_name__icontains=search_query) |
            Q(owner__owner_name__icontains=search_query) |
            Q(head_of_account__head_name__icontains=search_query) |
            Q(cash_type__method_name__icontains=search_query) |
            Q(mr_or_bill_no__icontains=search_query) |
            Q(remark__icontains=search_query)
        )

    paginator = Paginator(vouchers, 15)
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number)

    context = {
        'vouchers': vouchers_page,
        'search_query': search_query,
    }
    return render(request, 'landpurchase/land_debitvoucher_list.html', context)
    



@login_required
def land_creditvoucher_list(request):

    vouchers = LandCreditVoucher.objects.select_related(
        'land_purchase',
        'owner',
        'expense',
        'cash_type',
        'head_of_account'
    ).order_by('-id')

    # ✅ Date filter
    selected_date = request.GET.get("date")

    if selected_date:
        vouchers = vouchers.filter(date=selected_date)
    else:
        selected_date = date.today()

    # ✅ Pagination AFTER filtering
    paginator = Paginator(vouchers, 15)
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number)

    context = {
        'vouchers': vouchers_page,
        'selected_date': selected_date,
    }

    return render(
        request,
        'landpurchase/land_creditvoucher_list.html',
        context
    )
    
    

from .forms import LandCreditVoucherForm
@login_required
def add_land_creditvoucher(request):

    if request.method == 'POST':
        form = LandCreditVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.create_cr_by = request.user.get_full_name()
            voucher.save()
            return redirect('land_creditvoucher_list')
    else:
        form = LandCreditVoucherForm(initial={
            'date': date.today()
        })

    context = {
        'form': form,
    }

    return render(
        request,
        'landpurchase/add_land_creditvoucher.html',
        context
    )
    
    
    
# @login_required
# def add_land_debitvoucher(request):
#     if request.method == "POST":
#         form = LandDebitVoucherForm(request.POST)
#         if form.is_valid():
#             debit_voucher = form.save(commit=False)
#             debit_voucher.create_dr_by = request.user.get_full_name()
#             debit_voucher.save()
#             return redirect("land_debitvoucher_list")
#     else:
#         form = LandDebitVoucherForm()
#     landDebits = LandPurchase.objects.select_related('land_supplier').all()
#     context = {
#         "form": form,
#         "today": date.today().strftime("%Y-%m-%d"),
#         "landDebits":landDebits,
#     }
#     return render(request, "landpurchase/add_land_debitvoucher.html", context)





@login_required
@transaction.atomic
def add_land_debitvoucher(request):
    if request.method == "POST":
        form = LandDebitVoucherForm(request.POST)
        if form.is_valid():
            debit_voucher = form.save(commit=False)
            debit_voucher.create_dr_by = request.user.get_full_name()

            # ✅ Auto-generate MR/Bill number if missing
            if not debit_voucher.mr_or_bill_no:
                base_code = "MBD-"
                last = LandDebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
                next_id = (last.id + 1) if last else 1
                generated_code = f"{base_code}{next_id:05d}"
                while LandDebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"
                debit_voucher.mr_or_bill_no = generated_code

            debit_voucher.save()

            # ✅ Create corresponding Ledger Entry
            ledger_mr_no = debit_voucher.mr_or_bill_no
            suffix = 1
            while LandLedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
                ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
                suffix += 1

            LandLedgerEntry.objects.create(
                land_purchase=debit_voucher.land_purchase,
                type=debit_voucher.type,
                owner=debit_voucher.owner,
                expense=debit_voucher.expense,
                cash_type=debit_voucher.cash_type,
                head_of_account=debit_voucher.head_of_account,
                mr_or_bill_no=ledger_mr_no,
                date=debit_voucher.date,
                description=debit_voucher.remark or "Land Debit Voucher Entry",
                debit=debit_voucher.amount,
                credit=0,
                carrier=debit_voucher.carrier,
                loan_status="payment",
                tbl_id=debit_voucher.id,
                tbl_name="LandDebitVoucher",
                type_name=debit_voucher.type or "General"
            )

            # ✅ Create Transaction History record
            LandTransactionHistory.objects.create(
                land_purchase=debit_voucher.land_purchase,
                type=debit_voucher.type,
                owner=debit_voucher.owner,
                expense=debit_voucher.expense,
                cash_type=debit_voucher.cash_type,
                head_of_account=debit_voucher.head_of_account,
                amount=debit_voucher.amount,
                date=debit_voucher.date,
                type_name=debit_voucher.type or "General",
                reference=debit_voucher.mr_or_bill_no,
                create_by=request.user.get_full_name(),
                particulars=f"Transaction created for voucher {debit_voucher.mr_or_bill_no}",
                tbl_id=debit_voucher.id
            )

            # pdate CashMethod (deduct amount)
            if debit_voucher.cash_type:
                debit_voucher.cash_type.type_amount -= debit_voucher.amount
                debit_voucher.cash_type.type_note = f"Debit voucher payment (ID: {debit_voucher.id})"
                debit_voucher.cash_type.save()

            messages.success(request, "Debit Voucher, Ledger, and Transaction History saved successfully.")
            return redirect("land_debitvoucher_list")
        else:
            messages.error(request, "Form validation failed. Please check your input.")
    else:
        form = LandDebitVoucherForm()

    landDebits = LandPurchase.objects.select_related('land_supplier').all()
    context = {
        "form": form,
        "today": date.today().strftime("%Y-%m-%d"),
        "landDebits": landDebits,
    }
    return render(request, "landpurchase/add_land_debitvoucher.html", context)



from num2words import num2words
@login_required
def land_debit_voucher_pdf(request, pk):
    voucher = get_object_or_404(LandDebitVoucher, pk=pk)

    def amount_to_words(amount):
        try:
            # Convert amount to integer if necessary
            taka = int(amount)
            paisa = int(round((amount - taka) * 100))
            
            words = num2words(taka, lang='en').title() + " Taka"
            if paisa:
                words += f" and {num2words(paisa, lang='en').title()} Paisa"
            return words + " Only"
        except:
            return f"{amount} Taka Only"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'landpurchase/land_debit_voucher_pdf.html', context)
    
    
    
# @login_required
# def approve_land_pay_voucher(request, pk):
#     voucher = get_object_or_404(LandDebitVoucher, pk=pk)

#     # Approve the voucher
#     voucher.approval_status = True
#     voucher.save()

#     # Redirect back to voucher list
#     return redirect('land_debitvoucher_list')
 
 

@login_required
@transaction.atomic
def approve_land_pay_voucher(request, pk):
    voucher = get_object_or_404(LandDebitVoucher, pk=pk)
    updated_items = []

    # 1️⃣ Create LandApprovalPayment if advance_pay
    if getattr(voucher, 'advance_pay', False):
        LandApprovalPayment.objects.create(
            land_purchase=voucher.land_purchase,
            owner=voucher.owner,
            land_uniq_id=getattr(voucher, 'land_uniq_id', None),
            payment_type='advance_pay',
            purch_amount=voucher.amount,
            debit_voucher=voucher,
            purchase_date=voucher.date or timezone.now().date()
        )

    # 2️⃣ Auto-generate mr_or_bill_no if missing
    if not voucher.mr_or_bill_no:
        base_code = "MBD-"
        last = LandDebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
        next_id = (last.id + 1) if last else 1
        generated_code = f"{base_code}{next_id:05d}"
        while LandDebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
            next_id += 1
            generated_code = f"{base_code}{next_id:05d}"
        voucher.mr_or_bill_no = generated_code

    # 3️⃣ Approve voucher
    voucher.approval_status = True
    voucher.approval_dr_status = True
    voucher.save()
    updated_items.append(voucher)

    # 4️⃣ Update cash balance
    try:
        cash_type = CashMethod.objects.get(method_name=voucher.cash_type.method_name)
        cash_type.type_amount -= voucher.amount
        cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
        cash_type.save()
    except CashMethod.DoesNotExist:
        cash_type = None

    # 5️⃣ Create transaction history
    type_name = voucher.vendor if voucher.type == 'Vendor' and getattr(voucher, 'vendor', None) else None
    LandTransactionHistory.objects.create(
        land_purchase=voucher.land_purchase,
        type=voucher.type,
        head_of_account=voucher.head_of_account,
        cash_type=cash_type,
        amount=voucher.amount,
        date=voucher.date or timezone.now().date(),
        type_name=type_name,
        reference=None,
        create_by=voucher.create_dr_by,
        particulars=voucher.remark,
        tbl_id=str(voucher.id),
    )

    # 6️⃣ Create Ledger entries
    for item in updated_items:
        loan_status = 'payment'
        amount = item.amount or Decimal('0.00')
        debit_amount = amount if loan_status == 'payment' else Decimal('0.00')
        credit_amount = amount if loan_status == 'received' else Decimal('0.00')

        LandLedgerEntry.objects.create(
            land_purchase=item.land_purchase,
            type=item.type,
            owner=item.owner,
            expense=item.expense,
            type_name=item.expense if item.type == 'Expense' and item.expense else None,
            cash_type=item.cash_type,
            head_of_account=item.head_of_account,
            mr_or_bill_no=None,
            date=item.date or timezone.now().date(),
            description=item.remark or '',
            debit=debit_amount,
            credit=credit_amount,
            carrier=item.carrier,
            loan_status=loan_status,
            tbl_id=str(item.id),
            tbl_name='Payment'
        )

    # 7️⃣ Redirect back to voucher list
    return redirect('land_debitvoucher_list')



    
@login_required
def edit_land_debitvoucher(request, pk):
    # Fetch the Land Debit Voucher
    voucher = get_object_or_404(LandDebitVoucher, pk=pk)
    form = LandDebitVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        updated_voucher = form.save()

        # Update related LandLedgerEntry
        try:
            ledger_entry = LandLedgerEntry.objects.get(tbl_id=str(updated_voucher.id), tbl_name="Payment")
        except LandLedgerEntry.DoesNotExist:
            ledger_entry = None

        if ledger_entry:
            ledger_entry.land_purchase = updated_voucher.land_purchase
            ledger_entry.owner = updated_voucher.owner
            ledger_entry.cash_type = updated_voucher.cash_type
            ledger_entry.type_name = "Payment"
            ledger_entry.head_of_account = updated_voucher.head_of_account
            ledger_entry.mr_or_bill_no = updated_voucher.mr_or_bill_no
            ledger_entry.date = updated_voucher.date or timezone.now().date()
            ledger_entry.description = updated_voucher.remark or ''
            ledger_entry.debit = updated_voucher.amount or 0
            ledger_entry.credit = 0
            ledger_entry.carrier = updated_voucher.carrier
            ledger_entry.tbl_id = str(updated_voucher.id)
            ledger_entry.tbl_name = "Payment"

            ledger_entry.save()

        return redirect('land_debitvoucher_list')

    # Expenses for dropdown (if you want to use in template)
    expenses = LandHeadOfAccount.objects.all().order_by('head_exp_name')

    return render(request, 'landpurchase/edit_land_debitvoucher.html', {
        'form': form,
        'voucher': voucher,
        'expenses': expenses
    })
    
    
    
@login_required
def land_delete_debitvoucher(request, pk):
    voucher = get_object_or_404(LandDebitVoucher, pk=pk)
    if request.method == 'POST':
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('land_debitvoucher_list')
    return render(request, 'landpurchase/land_delete_debitvoucher.html', {'voucher': voucher})
    
    

## Land head of expense --
@login_required
def land_expense_head_list(request):
    headexpense = LandHeadOfExpense.objects.all()
    return render(request, 'landpurchase/land_head_of_expense_list.html', {'headexpense': headexpense})
    
    
    
@login_required
def add_land_head_of_expense(request):
    if request.method == 'POST':
        form = LandHeadOfExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('land_expense_head_list')
    else:
        form = LandHeadOfExpenseForm()
    context = {
        'form': form,
    }

    return render(request, 'landpurchase/add_land_head_of_expense.html', context)
    
    
    
@login_required
def edit_land_head_of_expense(request, pk):
    head_requisition = get_object_or_404(LandHeadOfExpense, pk=pk) 
    if request.method == 'POST':
        form = LandHeadOfExpenseForm(request.POST, instance=head_requisition)
        if form.is_valid():
            form.save()
            return redirect('land_expense_head_list')  
    else:
        form = LandHeadOfExpenseForm(instance=head_requisition)
    
    return render(request, 'landpurchase/edit_land_head_of_expense.html', {
        'form': form,
        'head_expense': head_requisition,
    })



@login_required
def delete_land_head_of_expense(request, pk):
    head_requisition = get_object_or_404(LandHeadOfExpense, pk=pk)
    if request.method == 'POST':
        head_requisition.delete()
        return redirect('land_expense_head_list')
    return render(request, 'landpurchase/delete_land_head_of_expense.html', {
        'head_requisition': head_requisition  
    })
    
    


from .models import LandDocument
from .forms import LandDocumentForm

@login_required
def new_document_list(request):
    documents = LandDocument.objects.all().order_by('-sl_no')
    return render(request, 'records/document_list.html', {'documents': documents})

@login_required
def new_edit_document(request, pk):
    document = get_object_or_404(LandDocument, pk=pk)
    if request.method == 'POST':
        form = LandDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "তথ্যটি সফলভাবে আপডেট করা হয়েছে!")
            return redirect('new_document_list')
    else:
        form = LandDocumentForm(instance=document)
    
    return render(request, 'records/document_form.html', {
        'form': form, 
        'is_edit': True, 
        'document': document
    })

@login_required
def new_delete_document(request, pk):
    document = get_object_or_404(LandDocument, pk=pk)
    if request.method == 'POST':
        document.delete()
        messages.success(request, "দলিলটি সফলভাবে মুছে ফেলা হয়েছে!")
        return redirect('new_document_list')
    return render(request, 'records/document_confirm_delete.html', {'document': document})
    
    
    
@login_required
def new_create_document(request):
    if request.method == 'POST':
        form = LandDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "তথ্যটি সফলভাবে সংরক্ষণ করা হয়েছে!")
            return redirect('new_create_document')
    else:
        form = LandDocumentForm()
        
    return render(request, 'records/document_form.html', {'form': form})


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import LandDocument

@login_required
def check_doc_no(request):
    doc_no = request.GET.get('doc_no', None)
    data = {'exists': False}
    
    if doc_no:
        doc = LandDocument.objects.filter(doc_no=doc_no).first()
        if doc:
            data = {
                'exists': True,
                'doc_no': doc.doc_no,
                'file_code': doc.get_file_code_display(),
                'buyer': doc.buyer,
                'seller': doc.seller,
                'mouza': doc.mouza,
                'dag_no': doc.dag_no,
                'current_status': doc.current_status,
                'doc_date': doc.doc_date.strftime('%Y-%m-%d') if doc.doc_date else '',
            }
    return JsonResponse(data)
    

@login_required
def update_doc_date(request):
    """ New view endpoint to update the date from within the modal overlay """
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            doc_no = body.get('doc_no')
            new_date = body.get('doc_date')
            
            doc = LandDocument.objects.filter(doc_no=doc_no).first()
            if doc and new_date:
                doc.doc_date = new_date
                doc.save()
                return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    return JsonResponse({'success': False, 'error': 'Invalid Request'}, status=400)
    
    
    
    
# @login_required    
# def new_land_document_row_detail(request, id):
#     document = get_object_or_404(LandDocument, pk=id)
#     return render(request, 'records/land_document_detail.html', {'document': document})