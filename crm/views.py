from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Customer, CustomerLead, CustomerFollowup, CustInfoBank, Campaign
from .forms import CustomerForm, CustomerLeadForm, CustomerFollowupForm, CustInfoBankForm, CampaignForm
from projects.models import ProjectFirstLevelName
from hrm.models import Employee, RdaEmployee
from datetime import date
from django.http import JsonResponse
from django.contrib import messages
from inventories.utils import log_deleted_data
from accounting.utils.sms import send_sms
from django.db.models import Q


@login_required
def crm_dashboard(request):
    today = timezone.now().date()
    
    # 1. Top Metrics (Counts based on your stages/statuses)
    context = {
        'total_leads_count': CustomerLead.objects.count(),
        'junk_leads_count': CustomerLead.objects.filter(status='junk').count(),
        'sold_count': CustomerLead.objects.filter(stage='Sold').count(),
        'high_prospect_count': CustomerLead.objects.filter(lead_category='High Prospect').count(),
        'priority_count': CustomerLead.objects.filter(lead_category='Priority').count(),
        'lost_count': CustomerLead.objects.filter(stage='Lost').count(),
        'closed_count': CustomerLead.objects.filter(status='close').count(),
        'negotiation_count': CustomerLead.objects.filter(stage='Negotiation Meeting').count(),
        'hot_count': CustomerLead.objects.filter(lead_category='Hot').count(),
        'query_count': CustomerLead.objects.filter(query__isnull=False).count(),
        
        # To-Do counts
        'todays_followups': CustomerFollowup.objects.filter(followup_date=today).count(),
        'todays_calls': CustomerFollowup.objects.filter(task_date=today, task_type='Call').count(),
        'todays_visits': CustomerFollowup.objects.filter(task_date=today, task_type='Visit').count(),
        'missed_followups': CustomerFollowup.objects.filter(followup_date__lt=today).count(),
        'missed_visits': CustomerFollowup.objects.filter(task_date__lt=today, task_type='Visit').count(),
        
        # Lists for columns
        'new_leads': CustomerLead.objects.filter(stage='New').order_by('-create_date')[:10],
        'followup_leads': CustomerLead.objects.filter(stage='Booking').order_by('-create_date')[:10], 
        'tasks_visits': CustomerFollowup.objects.filter(activity_type='task_visit').order_by('-create_date')[:10],
    }
    
    # Correct template directory path matching your project structure
    return render(request, 'customers/crm_dashboard.html', context)
    

@login_required
def campaign_list(request):
    campaigns = Campaign.objects.all().order_by('-created_at')
    return render(request, 'customers/campaign_list.html', {'campaigns': campaigns})


@login_required
def campaign_add(request):
    form = CampaignForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Campaign created successfully.")
        return redirect('campaign_list')
    return render(request, 'customers/campaign_form.html', {'form': form})


@login_required
def campaign_edit(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    form = CampaignForm(request.POST or None, request.FILES or None, instance=campaign)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Campaign updated successfully.")
        return redirect('campaign_list')
    return render(request, 'customers/campaign_form.html', {'form': form, 'campaign': campaign, 'is_edit': True})


@login_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    return render(request, 'customers/campaign_detail.html', {'campaign': campaign})


@login_required
def campaign_delete(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    campaign.delete()
    messages.success(request, "Campaign deleted successfully.")
    return redirect('campaign_list')


# ------------------------------------------------------------------
# LEAD CRM
# ------------------------------------------------------------------

LEAD_SOURCE_CHOICES = ['Facebook', 'Website', 'Walk-in', 'Referral', 'Self', 'Online Add', 'Campaign', 'Other']
LEAD_CATEGORY_CHOICES = ['Ready Flat', 'Ongoing', 'Upcoming','Junk','Used Flat','Lead Share']
PROFESSION_CHOICES = ['Service Holder', 'Businessman', 'Doctor', 'Engineer', 'Others']


def lead_list(request):
    """ Main Lead CRM table view with search and filter """
    query = request.GET.get('q', '')
    show_junk = request.GET.get('view') == 'junk'

    leads_qs = CustomerLead.objects.select_related('customer', 'project_name', 'campaign') \
        .order_by('-create_date')

    if show_junk:
        leads_qs = leads_qs.filter(status='junk')
    else:
        leads_qs = leads_qs.exclude(status='junk')

    if query:
        leads_qs = leads_qs.filter(
            Q(lead_code__icontains=query) |
            Q(customer__customer_name__icontains=query) |
            Q(customer__contact_no__icontains=query) |
            Q(customer__address__icontains=query)
        )

    leads = list(leads_qs)
    for lead in leads:
        lead.last_activity = lead.followups.order_by('-create_date').first()
        lead.next_activity = lead.followups.exclude(next_followup_date__isnull=True) \
            .order_by('-next_followup_date').first()

    context = {
        'leads': leads,
        'search_query': query,
        'show_junk': show_junk,
        'projects': ProjectFirstLevelName.objects.all(),
        'campaigns': Campaign.objects.all(),
        'lead_sources': LEAD_SOURCE_CHOICES,
        'lead_categories': LEAD_CATEGORY_CHOICES,
        'professions': PROFESSION_CHOICES,
        'stage_choices': CustomerLead.STAGE_CHOICES,
        # Preview of the code that WILL be assigned to the next lead created
        # (matches the "Lead Code" box already showing a real value, e.g.
        # L260915-0023, in the Lead Accounts modal before you hit Submit).
        'next_lead_code': CustomerLead.generate_next_code(),
    }
    return render(request, 'customers/lead_list.html', context)


def lead_create_or_update(request, lead_id=None):
    """ Handles adding a new lead or updating an existing lead (Lead Accounts modal) """
    customer_lead = get_object_or_404(CustomerLead, id=lead_id) if lead_id else None
    customer = customer_lead.customer if customer_lead else None

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        secondary_phone = request.POST.get('secondary_phone')
        entry_date = request.POST.get('date')
        assign_user = request.POST.get('assign_user') or 'Admin'
        cr = request.POST.get('cr')
        lead_stage = request.POST.get('lead_stage') or 'New'

        # Lead Details
        source = request.POST.get('lead_source')
        project_id = request.POST.get('interested_project')
        lead_category = request.POST.get('lead_category')
        campaign_id = request.POST.get('campaign')

        # Personal Info
        organization = request.POST.get('organization')
        designation = request.POST.get('designation')
        birth_date = request.POST.get('birth_date') or None
        anniversary_date = request.POST.get('anniversary_date') or None
        profession = request.POST.get('profession')
        address = request.POST.get('address')
        email = request.POST.get('email')

        # 1. Manage Customer profile (find by phone to avoid duplicates)
        if not customer:
            customer = Customer.objects.filter(contact_no=phone).first()

        if customer:
            customer.customer_name = name
            customer.contact_no = phone
            customer.secondary_phone = secondary_phone or customer.secondary_phone
            customer.profession = profession or customer.profession
            customer.designation = designation or customer.designation
            customer.lead_source = source or customer.lead_source
            customer.organization = organization or customer.organization
            customer.email = email or customer.email
            customer.address = address or customer.address or ''
            customer.assign_to_user = assign_user
            customer.birth_date = birth_date or customer.birth_date
            customer.anniversary_date = anniversary_date or customer.anniversary_date
            if entry_date:
                customer.date = entry_date
            customer.save()
        else:
            customer = Customer.objects.create(
                customer_name=name,
                contact_no=phone,
                secondary_phone=secondary_phone,
                profession=profession,
                designation=designation,
                lead_source=source,
                organization=organization,
                email=email,
                address=address or '',
                assign_to_user=assign_user,
                birth_date=birth_date,
                anniversary_date=anniversary_date,
                date=entry_date if entry_date else None,
            )

        # 2. Manage the CustomerLead record
        project_obj = ProjectFirstLevelName.objects.filter(id=project_id).first() if project_id else None
        campaign_obj = Campaign.objects.filter(id=campaign_id).first() if campaign_id else None

        if not customer_lead:
            customer_lead = CustomerLead()

        customer_lead.customer = customer
        customer_lead.lead_name = f"Lead for {name}"
        customer_lead.project_name = project_obj
        customer_lead.campaign = campaign_obj
        customer_lead.lead_category = lead_category
        customer_lead.cr = cr
        customer_lead.stage = lead_stage

        customer_lead.save()
        messages.success(request, f"Lead '{name}' saved successfully!")
        return redirect('lead_list')

    return redirect('lead_list')


def lead_activity_detail(request, lead_id):
    """ View for the Lead Activity pop-up modal """
    lead = get_object_or_404(CustomerLead, id=lead_id)
    followups = CustomerFollowup.objects.filter(lead=lead).order_by('-create_date')
    last_activity = followups.first()

    context = {
        'lead': lead,
        'last_activity': last_activity,
        'followups': followups,
        'stage_choices': CustomerLead.STAGE_CHOICES,
    }
    return render(request, 'customers/lead_detail_modal.html', context)


# def add_lead_activity(request, lead_id):
#     """
#     Save a Followup or a Task/Visit for a lead, update its stage
#     (including Move to junk / Mark as Sold), and capture customer
#     feedback rating + salesperson possibility marking.
#     """
#     if request.method == 'POST':
#         lead = get_object_or_404(CustomerLead, id=lead_id)
#         customer = lead.customer

#         # --- quick edits to the customer's basic info from the left panel ---
#         # (Category, Name, Phone, Email, Organization, Designation, Profession,
#         #  Source, Address, CR, Remark, Query — the full 2-column grid shown
#         #  in the activity modal.)
#         name = request.POST.get('name')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         organization = request.POST.get('organization')
#         designation = request.POST.get('designation')
#         profession = request.POST.get('profession')
#         source = request.POST.get('source')
#         address = request.POST.get('address')

#         if name:
#             customer.customer_name = name
#         if phone:
#             customer.contact_no = phone
#         if email is not None:
#             customer.email = email
#         if organization is not None:
#             customer.organization = organization
#         if designation is not None:
#             customer.designation = designation
#         if profession:
#             customer.profession = profession
#         if source is not None:
#             customer.lead_source = source
#         if address is not None:
#             customer.address = address
#         customer.save()

#         # --- Category, CR, Remark, Query also live on the left panel but belong to the lead ---
#         lead_category = request.POST.get('lead_category')
#         cr = request.POST.get('cr')
#         remark = request.POST.get('remark')
#         query = request.POST.get('query')

#         if lead_category:
#             lead.lead_category = lead_category
#         if cr is not None:
#             lead.cr = cr
#         if remark is not None:
#             lead.note = remark
#         if query is not None:
#             lead.query = query

#         # --- stage handling ---
#         stage = request.POST.get('stage') or lead.stage
#         move_to_junk = request.POST.get('junk')
#         mark_as_sold = request.POST.get('sold')

#         if move_to_junk:
#             lead.stage = 'Junk'
#             lead.status = 'junk'
#         elif mark_as_sold:
#             lead.stage = 'Sold'
#             lead.status = 'close'
#         else:
#             lead.stage = stage
#             if lead.status == 'junk':
#                 lead.status = 'open'

#         # --- possibility marking + customer feedback ---
#         possibility = request.POST.get('possibility')
#         feedback_rating = request.POST.get('feedback_rating')

#         if possibility not in (None, ''):
#             lead.salesperson_marking_possibility = possibility
#         if feedback_rating not in (None, ''):
#             lead.customer_feedback_rating = feedback_rating

#         lead.save()

#         # --- current activity: Followup vs Task/Visit ---
#         activity_type = request.POST.get('activity_type', 'followup')

#         next_activity_type = request.POST.get('next_activity_type')
#         next_date_raw = request.POST.get('next_date') or None
#         next_note = request.POST.get('next_note')

#         followup = CustomerFollowup(
#             lead=lead,
#             activity_type=activity_type,
#             salesperson_marking=possibility or 0.00,
#             next_activity_type=next_activity_type,
#             next_followup_date=next_date_raw,
#             next_followup_note=next_note,
#         )

#         if activity_type == 'task_visit':
#             followup.task_type = request.POST.get('task_type')
#             followup.task_date = request.POST.get('task_date') or None
#             followup.task_status = request.POST.get('task_status')
#             followup.visit_place = request.POST.get('visit_place')
#             followup.comment = request.POST.get('comment')
#         else:
#             followup.communication_status = request.POST.get('status')
#             followup.followup_note = request.POST.get('comment')
#             followup.followup_date = timezone.now().date()

#         followup.save()

#         # keep the lead's quick-reference followup fields in sync
#         lead.followup_note = followup.followup_note or followup.comment or lead.followup_note
#         if next_date_raw:
#             lead.followup_date = followup.next_followup_date
#         lead.save()

#         messages.success(request, "Activity updated successfully.")
#         return redirect('lead_list')

#     return redirect('lead_list')



def add_lead_activity(request, lead_id):
    if request.method == 'POST':
        lead = get_object_or_404(CustomerLead, id=lead_id)
        customer = lead.customer

        # --- quick edits to the customer's basic info from the left panel ---
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        organization = request.POST.get('organization')
        designation = request.POST.get('designation')
        profession = request.POST.get('profession')
        source = request.POST.get('source')
        address = request.POST.get('address')

        if name:
            customer.customer_name = name
        if phone:
            customer.contact_no = phone
        if email is not None:
            customer.email = email
        if organization is not None:
            customer.organization = organization
        if designation is not None:
            customer.designation = designation
        if profession:
            customer.profession = profession
        if source is not None:
            customer.lead_source = source
        if address is not None:
            customer.address = address
        customer.save()

        # --- Category, CR, Remark, Query also live on the left panel but belong to the lead ---
        lead_category = request.POST.get('lead_category')
        cr = request.POST.get('cr')
        remark = request.POST.get('remark')
        query = request.POST.get('query')

        if lead_category:
            lead.lead_category = lead_category
        if cr is not None:
            lead.cr = cr
        if remark is not None:
            lead.note = remark
        if query is not None:
            lead.query = query

        # --- stage handling ---
        stage = request.POST.get('stage') or lead.stage
        move_to_junk = request.POST.get('junk')
        mark_as_sold = request.POST.get('sold')

        if move_to_junk:
            lead.stage = 'Junk'
            lead.status = 'junk'
        elif mark_as_sold:
            lead.stage = 'Sold'
            lead.status = 'close'
        else:
            lead.stage = stage
            if lead.status == 'junk':
                lead.status = 'open'

        # --- possibility marking + customer feedback ---
        possibility = request.POST.get('possibility')                    # top "Possibility" (stage row)
        task_sales_possibility = request.POST.get('sales_possibility')   # task/visit section's own field
        feedback_rating = request.POST.get('feedback_rating')

        if possibility not in (None, ''):
            lead.salesperson_marking_possibility = possibility
        if feedback_rating not in (None, ''):
            lead.customer_feedback_rating = feedback_rating

        lead.save()

        # --- current activity: Followup vs Task/Visit ---
        activity_type = request.POST.get('activity_type', 'followup')

        next_activity_type = request.POST.get('next_activity_type')
        next_date_raw = request.POST.get('next_date') or None
        next_note = request.POST.get('next_note')

        followup = CustomerFollowup(
            lead=lead,
            activity_type=activity_type,
            next_activity_type=next_activity_type,
            next_followup_date=next_date_raw,
            next_followup_note=next_note,
        )

        if activity_type == 'task_visit':
            followup.task_type = request.POST.get('task_type')
            followup.task_date = request.POST.get('task_date') or None
            followup.task_status = request.POST.get('task_status')
            followup.visit_place = request.POST.get('visit_place')
            followup.task_note = request.POST.get('task_note')
            followup.comment = request.POST.get('task_comment')
            followup.salesperson_marking = task_sales_possibility or possibility or 0.00
        else:
            followup.communication_status = request.POST.get('status')
            followup.followup_note = request.POST.get('comment')
            followup.followup_date = timezone.now().date()
            followup.salesperson_marking = possibility or 0.00

        followup.save()

        # keep the lead's quick-reference followup fields in sync
        lead.followup_note = followup.followup_note or followup.comment or lead.followup_note
        if next_date_raw:
            lead.followup_date = followup.next_followup_date
        lead.save()

        messages.success(request, "Activity updated successfully.")
        return redirect('lead_list')

    return redirect('lead_list')
    
    

def lead_edit_modal(request, lead_id):
    """ Renders the 'Lead Accounts' modal pre-filled with an existing lead's data, for editing """
    lead = get_object_or_404(CustomerLead, id=lead_id)
    customer = lead.customer

    context = {
        'lead': lead,
        'customer': customer,
        'projects': ProjectFirstLevelName.objects.all(),
        'campaigns': Campaign.objects.all(),
        'lead_sources': LEAD_SOURCE_CHOICES,
        'lead_categories': LEAD_CATEGORY_CHOICES,
        'professions': PROFESSION_CHOICES,
        'stage_choices': CustomerLead.STAGE_CHOICES,
    }
    return render(request, 'customers/lead_edit_modal.html', context)
    
    

def stop_lead_activity(request, lead_id):
    """
    'Stop Followup/Visit' — clears any scheduled next activity for this
    lead so it drops off the Next Activity column / any upcoming-followup
    reminders, without touching the lead's stage or activity history.
    """
    lead = get_object_or_404(CustomerLead, id=lead_id)

    # Clear the lead's own quick-reference followup date
    lead.followup_date = None
    lead.save()

    # Clear the "next" fields on the most recent followup entry, if any,
    # so it no longer shows up as an upcoming/pending activity.
    latest_followup = lead.followups.order_by('-create_date').first()
    if latest_followup:
        latest_followup.next_activity_type = None
        latest_followup.next_followup_date = None
        latest_followup.next_followup_note = None
        latest_followup.save()

    messages.success(request, "Follow-up / Visit schedule stopped.")
    return redirect('lead_list')


def convert_to_customer(request):
    """ Bulk or single Lead convert action """
    if request.method == "POST":
        selected_ids = request.POST.getlist('selected_leads')
        if selected_ids:
            leads = CustomerLead.objects.filter(id__in=selected_ids)
            count = leads.count()
            for lead in leads:
                lead.status = 'close'
                lead.save()
            messages.success(request, f"Successfully processed {count} lead(s)!")
        else:
            messages.warning(request, "Please select at least one lead.")
    return redirect('lead_list')


def lead_delete(request, lead_id):
    """ Delete lead entry """
    lead = get_object_or_404(CustomerLead, id=lead_id)
    lead.delete()
    messages.success(request, "Lead deleted successfully!")
    return redirect('lead_list')


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



def load_lead_modal(request, lead_id):
    # Corrected model reference: CustomerLead instead of Lead
    lead = get_object_or_404(CustomerLead, id=lead_id)
    
    # Fetch related followups safely (if a related_name exists on your followup model)
    followups = lead.followups.all() if hasattr(lead, 'followups') else []
    
    context = {
        'lead': lead,
        'followups': followups,
        'stage_choices': CustomerLead.STAGE_CHOICES,
    }
    return render(request, 'customers/lead_detail_modal.html', context)
    
    
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


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    projects = ProjectFirstLevelName.objects.all()
    employees = Employee.objects.all()
    today = date.today().isoformat()

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


from django.utils import timezone as tz
from .forms import BulkSMSForm
from .models import BulkSMS, BulkSMSRecipient


@login_required(login_url='/login/')
def bulk_sms_send_view(request):
    selected_project = request.GET.get("project")

    form = BulkSMSForm(request.POST or None)

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
                    sent_time = tz.now()
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
