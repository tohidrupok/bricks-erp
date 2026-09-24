from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import VaratiyaForm, RoomForm, ProjectNameForm, RentForm, TenantCashForm , ChequeBookForm, ChequeForm,ReceiveVoucherForm,TenantBulkSMSForm
from django.utils.timezone import now
from num2words import num2words   
from django.utils import timezone
from django.db.models import Sum 
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, datetime
import json
from decimal import Decimal 
from accounting.utils.sms import send_sms

from django.shortcuts import render

def tenant_dashboard(request):
    return render(request, 'tenant/dashboard.html')
 
    
@login_required
def project_page(request):
    if request.method == "POST":
        form = ProjectNameForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_page')
    else:
        form = ProjectNameForm()

    projects = ProjectName.objects.all()
    return render(request, "projects/add_project.html", {"form": form, "projects": projects})



@login_required
def bill_generator_home(request):
    
    return render(request, "bill_generator.html")


@login_required
def varatiya_form_and_list(request):
    # Form handle
    if request.method == 'POST':
        form = VaratiyaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('varatiya_list')  
    else:
        form = VaratiyaForm()

    # Listing handle
    varatiyas = Varatiya.objects.all()

    return render(request, 'varatiya/form_and_list.html', {
        'form': form,
        'varatiyas': varatiyas
    })


@login_required
def varatiya_update(request, pk):
    varatiya = get_object_or_404(Varatiya, pk=pk)
    
    if request.method == "POST":
        form = VaratiyaForm(request.POST, request.FILES, instance=varatiya)
        if form.is_valid():
            form.save()
            return redirect('varatiya_list')
    else:
        form = VaratiyaForm(instance=varatiya)  

    return render(request, 'varatiya/form.html', {'form': form})


@login_required
def varatiya_detail(request, pk):
    varatiya = get_object_or_404(Varatiya, pk=pk)
    rents = varatiya.rents.select_related('room', 'projectref').all()  
    return render(request, "varatiya/varatiya_detail.html", {
        "varatiya": varatiya,
        "rents": rents
    })


@login_required
def varatiya_delete(request, pk):
    varatiya = get_object_or_404(Varatiya, pk=pk)
    varatiya.delete()
    return redirect('varatiya_list')


@login_required
def room_list(request):
    rooms = Room.objects.select_related('project', 'client').all().order_by(
        'project__name', 'room_name'
    )
    return render(request, 'room/list.html', {'rooms': rooms})


@login_required
def room_create(request):
    form = RoomForm(request.POST or request.FILES)
    if form.is_valid():
        form.save()
        return redirect('room_list')
    return render(request, 'room/form.html', {'form': form})


@login_required
def room_update(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)  # Only instance for GET request

    return render(request, 'room/edit_form.html', {'form': form})



@login_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room.delete()
    return redirect('room_list')


#@login_required
def room_details(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Related rents (all)
    rents = room.rents.select_related("varatiya").all().order_by("-startmonths")

    # Active rent 
    active_rent = rents.filter(status="Active").first()

    context = {
        "room": room,
        "rents": rents,
        "active_rent": active_rent,
        "now": timezone.now(), 
    }
    return render(request, "room/details.html", context) 




@login_required
def rent_list(request):
    rents = Rent.objects.all().select_related('projectref', 'room', 'varatiya')
    return render(request, 'tenant/rent_list.html', {'rents': rents}) 


@login_required   
def rent_create(request):
    if request.method == 'POST':
        form = RentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rent_list')
    else:
        form = RentForm()
    return render(request, 'tenant/rent_form.html', {'form': form}) 

@login_required
def rent_form_and_list(request):
  
    if request.method == 'POST':

        form = RentForm(request.POST)
        print("form data",form.data) #ay khane kichu print hoy nh
        if form.is_valid():
            rent_instance = form.save(commit=False)
            
            # --- Update Room costs and meter info ---
            room = rent_instance.room
            if room:
                
                # Costs
                room.core_room_rent = request.POST.get('id_core_room_rent') or room.core_room_rent
                room.parking_cost = request.POST.get('id_parking_cost') or room.parking_cost
                room.service_rent = request.POST.get('id_service_rent') or room.service_rent
                room.gas_rent = request.POST.get('id_gas_rent') or room.gas_rent
                room.water_rent = request.POST.get('id_water_rent') or room.water_rent
                room.electricity_rent = request.POST.get('id_electricity_rent') or room.electricity_rent
                room.other_cost = request.POST.get('id_other_cost') or room.other_cost

                # New meter fields
                room.meter_number = request.POST.get('id_meter_number') or room.meter_number
                opening = request.POST.get('id_opening_reading') 
                if opening:
                        room.opening_reading = opening
                        room.last_month_reading = opening
                        
                room.unit_charge = request.POST.get('id_unit_charge') or room.unit_charge

                room.save()  # save permanently

            rent_instance.save()  # Save Rent
            messages.success(request, "Rent and Room costs updated successfully!")
            return redirect('rent_form_and_list')
    else:
        form = RentForm()

    rents = Rent.objects.all().select_related('projectref', 'room', 'varatiya')
    return render(request, 'tenant/rent_form_and_list.html', {
        'form': form,
        'rents': rents
    })


@login_required
def load_rooms(request):
    projectref_id = request.GET.get('projectref_id')
    flat = request.GET.get('flat')

    rooms = Room.objects.none()
    if projectref_id and flat:
        try:
            projectref = ProjectName.objects.get(id=projectref_id)
            rooms = Room.objects.filter(
                 project=projectref, flat=flat, status='Deactive'
            ).order_by('room_name')

        except ProjectName.DoesNotExist:
            pass

    room_list = []
    for r in rooms:
        room_list.append({
            'id': r.id,
            'name': f"{r.room_name} ({r.flat})",
            'core_room_rent': str(r.core_room_rent),
            'parking_cost': str(r.parking_cost),
            'service_rent': str(r.service_rent),
            'gas_rent': str(r.gas_rent),
            'water_rent': str(r.water_rent),
            'other_cost': str(r.other_cost),

            'meter_number': r.meter_number or '',
            'opening_reading': str(r.opening_reading),
            'last_month_reading': str(r.last_month_reading),
            'unit_charge': str(r.unit_charge),
        })

    return JsonResponse({'rooms': room_list}) 


@login_required
def rent_search(request):
    
    projectref_id = request.GET.get('projectref')
    flat = request.GET.get('flat')
    room_id = request.GET.get('room')

    rents = Rent.objects.none()
    projects = ProjectName.objects.all().order_by('name')
    rooms = Room.objects.none()

    # Flat choices always F1 to F15
    flats = [f'F{i}' for i in range(1, 16)]

    if projectref_id and flat:
        try:
            project = ProjectName.objects.get(id=projectref_id)
            # Filter rooms based on project and flat
            rooms = Room.objects.filter(project=project.project, flat=flat).exclude(status='Deactive').order_by('room_name')
        except ProjectName.DoesNotExist:
            rooms = Room.objects.none()

    if room_id:
        rents = Rent.objects.filter(room_id=room_id).select_related('projectref', 'room', 'varatiya')

    context = {
        'projects': projects,
        'flats': flats,
        'rooms': rooms,
        'rents': rents,
        'selected_project': projectref_id,
        'selected_flat': flat,
        'selected_room': room_id,
    }
    return render(request, 'tenant/rent_search.html', context)



#for basa chara dicha
@login_required
def deactiveload_rooms(request):
    
    projectref_id = request.GET.get('projectref_id')
    flat = request.GET.get('flat')
   
    rooms = Room.objects.none()
    if projectref_id and flat:
        try:
            projectref = ProjectName.objects.get(id=projectref_id)
            rooms = Room.objects.filter(project=projectref, flat=flat).exclude(status='Deactive').order_by('room_name')
        except ProjectName.DoesNotExist:
            pass

    room_list = [{'id': r.id, 'name': f"{r.room_name} ({r.flat})"} for r in rooms]
    return JsonResponse({'rooms': room_list}) 


@login_required
def deactivate_rent(request, rent_id):
    rent = get_object_or_404(Rent.objects.select_related('room'), id=rent_id)

    # Update Rent status
    rent.status = 'Deactive'
    rent.endmonths = date.today()
    rent.save()

    # Update Room status if exists
    if rent.room:
        rent.room.status = 'Deactive'
        rent.room.save()

    messages.success(request, f'Rent and Room for {rent.room} deactivated successfully!')
    return redirect(request.META.get('HTTP_REFERER', 'tenant:rent_search'))
 


# def bill_generate(request):
#     projects = ProjectFirstLevelName.objects.all()
#     return render(request, "bill/bill_generate.html", {"projects": projects})

# def get_project_rooms(request, project_id):
#     # Rent objects filter koro, status Active and room project match korche
#     rents = Rent.objects.filter(
#         status='Active',
#         room__project_id=project_id
#     ).select_related('room', 'varatiya')

#     data = []
#     total = 0

#     for rent in rents:
#         room = rent.room
#         if not room:
#             continue

#         subtotal = (room.core_room_rent or 0) + (room.service_rent or 0) + (room.other_cost or 0)
#         total += subtotal

#         data.append({
#             "room_name": room.room_name,
#             "flat": room.flat,
#             "client_name": rent.varatiya.name if rent.varatiya else '-',
#             "core_room_rent": float(room.core_room_rent or 0),
#             "service_rent": float(room.service_rent or 0),
#             "other_cost": float(room.other_cost or 0),
#             "subtotal": float(subtotal),
#         })

#     return JsonResponse({"rooms": data, "grand_total": float(total)})


 
@login_required
def bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/bill_generate.html", {
        "projects": projects,
        "current_month": current_month
    })


@login_required
def get_project_rooms(request, project_id):
    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = (room.core_room_rent or 0) + (room.other_cost or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "core_room_rent": float(room.core_room_rent or 0),
            
            "other_cost": float(room.other_cost or 0),
            "subtotal": float(subtotal),
        })

    return JsonResponse({"rooms": data, "grand_total": float(total)})

  
@login_required
def save_generated_bill(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status='Active',
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name
            ).first()

            existing_bill_qs = Bill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            # Create new bill
            bill = Bill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                core_room_rent=r.get("core_room_rent", 0),               
                other_cost=r.get("other_cost", 0),
                subtotal=r.get("subtotal", 0),
                bill_month=bill_month,
                status="Generated"
            )
            bills_created.append(bill)

            # LedgerEntry handling without description check
            if rent_obj and rent_obj.varatiya:

                description = f"Basic Rent for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"
 
                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description
                )

                if ledger_qs.exists():
                    # Update first existing entry for this tenant + month
                    ledger = ledger_qs.first()
                    ledger.debit = bill.subtotal
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    # Create new LedgerEntry
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date= timezone.now().date(),
                        description= description,
                        bill_no=None,
                        debit=bill.subtotal,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None  
                    )

        # Build message
        if new_count == 0 and updated_count > 0:
            # All data already exist
            message = f"Bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "core_room_rent": float(bill.core_room_rent),
                    
                    "other_cost": float(bill.other_cost),
                    "subtotal": float(bill.subtotal),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None
                }
                for bill in bills_created
            ]
        })


@login_required
def bulk_print_bills(request):
    print("dukcha go")
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    if projectref_id:
        bills = Bill.objects.filter( 
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")
        print("bills",bills )
       
        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name  
        
        
    else:
        bills = Bill.objects.filter(bill_month=bill_month).order_by("flat", "room_name")
        project_name = "All Projects"

    grand_total = sum(b.subtotal for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        
        "bill_month": bill_month.strftime("%B, %Y"),  # For display
        "project_name": project_name,

    }
    return render(request, "bill/bulk_print.html", context)


@login_required
def gas_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/gas_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


#Fetch active rents of a project (AJAX)
@login_required
def get_project_gas_rooms(request, project_id):

    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = float(room.gas_rent or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "gas_rent": subtotal,
        })

    return JsonResponse({"rooms": data, "grand_total": total})


@login_required
def create_gas_bills(request):
    print("gas bill generated")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status="Active",
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name,
            ).first()

            existing_bill_qs = GasBill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            bill = GasBill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                gas_rent=r.get("gas_rent", 0),
                bill_month=bill_month,
                status="Generated",
            )
            bills_created.append(bill)

            if rent_obj and rent_obj.varatiya:

                description = f"Gas Rent for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"

                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description
                )

                if ledger_qs.exists():
                    ledger = ledger_qs.first()
                    ledger.debit = bill.gas_rent  # Gas rent as debit
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date=timezone.now().date(),
                        description=description,
                        bill_no=None,
                        debit=bill.gas_rent,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None
                    ) 



        # Build message
        if new_count == 0 and updated_count > 0:
            message = f"Gas bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing gas bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new gas bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "gas_rent": float(bill.gas_rent),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None,
                }
                for bill in bills_created
            ]
        })




@login_required
def bulk_print_gas_bills(request):
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    # Filter GasBills by rent__projectref and bill_month

    if projectref_id:
        bills = GasBill.objects.filter(
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name   

    else:
        bills = GasBill.objects.filter(
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project_name = "All Projects"

    grand_total = sum(b.gas_rent for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill_month.strftime("%B, %Y"),
        "project_name": project_name,
    }
    return render(request, "bill/bulk_print_gas.html", context) 


@login_required
def water_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/water_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


# Fetch active rents of a project (AJAX)

@login_required
def get_project_water_rooms(request, project_id):

    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = float(room.water_rent or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "water_rent": subtotal,
        })

    return JsonResponse({"rooms": data, "grand_total": total})




@login_required
def create_water_bills(request):
    print("water bill generated")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status="Active",
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name,
            ).first()

            existing_bill_qs = WaterBill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            bill = WaterBill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                water_rent=r.get("water_rent", 0),
                bill_month=bill_month,
                status="Generated",
            )
            bills_created.append(bill)

            if rent_obj and rent_obj.varatiya:

                description = f"Water Rent for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"

                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description,

                )

                if ledger_qs.exists():
                    ledger = ledger_qs.first()
                    ledger.debit = bill.water_rent  # Water rent as debit
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date=timezone.now().date(),
                        description= description, 
                        bill_no=None,
                        debit=bill.water_rent,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None
                    )

        # Build message
        if new_count == 0 and updated_count > 0:
            message = f"Water bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing water bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new water bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "water_rent": float(bill.water_rent),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None,
                }
                for bill in bills_created
            ]
        })


# Bulk Print

@login_required
def bulk_print_water_bills(request):
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    # Filter WaterBills by rent__projectref and bill_month
    if projectref_id:
        bills = WaterBill.objects.filter(
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name   

    else:
        bills = WaterBill.objects.filter(
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project_name = "All Projects"

    grand_total = sum(b.water_rent for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill_month.strftime("%B, %Y"),
        "project_name": project_name,
    }
    return render(request, "bill/bulk_print_water.html", context) 





# Show project selection page
@login_required
def parking_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/parking_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


# Fetch active rents of a project (AJAX)
@login_required
def get_project_parking_rooms(request, project_id):

    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = float(room.parking_cost or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "parking_cost": subtotal,
        })

    return JsonResponse({"rooms": data, "grand_total": total})


# Generate bills and save in DB
@login_required
def create_parking_bills(request):
    print("parking bill generated")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status="Active",
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name,
            ).first()

            existing_bill_qs = ParkingBill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            bill = ParkingBill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                parking_cost=r.get("parking_cost", 0),
                bill_month=bill_month,
                status="Generated",
            )
            bills_created.append(bill)

            if rent_obj and rent_obj.varatiya:

                description = f"Parking Bill for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"

                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description,
                )

                if ledger_qs.exists():
                    ledger = ledger_qs.first()
                    ledger.debit = bill.parking_cost  # Parking cost as debit
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date=timezone.now().date(),
                        description=description,
                        bill_no=None,
                        debit=bill.parking_cost,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None
                    )


        # Build message
        if new_count == 0 and updated_count > 0:
            message = f"Parking bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing parking bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new parking bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "parking_cost": float(bill.parking_cost),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None,
                }
                for bill in bills_created
            ]
        })


#  Bulk print Parking Bills
@login_required
def bulk_print_parking_bills(request):
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    if projectref_id:
        bills = ParkingBill.objects.filter(
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name   

    else:
        bills = ParkingBill.objects.filter(
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project_name = "All Projects"

    grand_total = sum(b.parking_cost for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill_month.strftime("%B, %Y"),
        "project_name": project_name,
    }
    return render(request, "bill/bulk_print_parking.html", context)



# #  Show project selection page
# def electricity_bill_generate(request):
#     projects = ProjectFirstLevelName.objects.all()
#     current_month = date.today()
#     return render(request, "bill/electricity_rent_generator.html", {
#         "projects": projects,
#         "current_month": current_month
#     })


# #  Fetch active rents of a project (AJAX)
# def get_project_electricity_rooms(request, project_id):

#     rents = Rent.objects.filter(
#         status='Active',
#         room__project_id=project_id
#     ).select_related('room', 'varatiya')

#     data = []
#     total = 0

#     for rent in rents:
#         room = rent.room
#         if not room:
#             continue

#         subtotal = float(room.electricity_rent or 0)
#         total += subtotal

#         data.append({
#             "room_name": room.room_name,
#             "flat": room.flat,
#             "client_name": rent.varatiya.name if rent.varatiya else '-',
#             "electricity_rent": subtotal,
#         })

#     return JsonResponse({"rooms": data, "grand_total": total})


#  Generate bills and save in DB
# def create_electricity_bills(request):
#     print("electricity bill generated")
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({"success": False, "message": "Invalid JSON"})

#         rooms_list = data.get("rooms", [])
#         bill_month_str = data.get("bill_month")
#         if not bill_month_str:
#             return JsonResponse({"success": False, "message": "Bill month is required."})

#         try:
#             bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
#         except ValueError:
#             return JsonResponse({"success": False, "message": "Invalid month format."})

#         bills_created = []
#         updated_count = 0
#         new_count = 0

#         for r in rooms_list:
#             room_name = r.get("room_name", "-")
#             flat = r.get("flat", "-")
#             client_name = r.get("client_name", "-")

#             rent_obj = Rent.objects.filter(
#                 status="Active",
#                 room__room_name=room_name,
#                 room__flat=flat,
#                 varatiya__name=client_name,
#             ).first()

#             existing_bill_qs = ElectricityBill.objects.filter(
#                 bill_month=bill_month,
#                 room_name=room_name,
#                 flat=flat,
#                 varatiya_name=client_name,
#             )

#             if existing_bill_qs.exists():
#                 updated_count += existing_bill_qs.count()
#                 existing_bill_qs.delete()
#             else:
#                 new_count += 1

#             bill = ElectricityBill.objects.create(
#                 rent=rent_obj,
#                 room_name=room_name,
#                 flat=flat,
#                 varatiya_name=client_name,
#                 electricity_rent=r.get("electricity_rent", 0),
#                 bill_month=bill_month,
#                 status="Generated",
#             )
#             bills_created.append(bill)

#         # Build message
#         if new_count == 0 and updated_count > 0:
#             message = f"Electricity bills for {bill_month.strftime('%B %Y')} already generated."
#         else:
#             message_parts = []
#             if updated_count > 0:
#                 message_parts.append(f"{updated_count} existing electricity bill(s) updated")
#             if new_count > 0:
#                 message_parts.append(f"{new_count} new electricity bill(s) created")
#             message = ", ".join(message_parts) + "."

#         return JsonResponse({
#             "success": True,
#             "message": message,
#             "bills": [
#                 {
#                     "id": bill.id,
#                     "room_name": bill.room_name,
#                     "flat": bill.flat,
#                     "varatiya_name": bill.varatiya_name,
#                     "electricity_rent": float(bill.electricity_rent),
#                     "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
#                     "status": bill.status,
#                     "rent_id": bill.rent.id if bill.rent else None,
#                 }
#                 for bill in bills_created
#             ]
#         })

#  Show project selection page
@login_required
def service_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/service_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


#  Fetch active rents of a project (AJAX)
@login_required
def get_project_service_rooms(request, project_id):

    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = float(room.service_rent or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "service_rent": subtotal,
        })

    return JsonResponse({"rooms": data, "grand_total": total})


#  Generate bills and save in DB
@login_required
def create_service_bills(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status="Active",
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name,
            ).first()

            existing_bill_qs = ServiceBill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            bill = ServiceBill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                service_rent=r.get("service_rent", 0),
                bill_month=bill_month,
                status="Generated",
            )
            bills_created.append(bill)

            if rent_obj and rent_obj.varatiya:
                description = f"Service Bill for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"
                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description,
                )

                if ledger_qs.exists():
                    ledger = ledger_qs.first()
                    ledger.debit = bill.service_rent  # Service rent as debit
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date=timezone.now().date(),
                        description=description,
                        bill_no=None,
                        debit=bill.service_rent,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None
                    )


        # Build message
        if new_count == 0 and updated_count > 0:
            message = f"Service bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing service bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new service bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "service_rent": float(bill.service_rent),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None,
                }
                for bill in bills_created
            ]
        })
    

@login_required
def bulk_print_service_bills(request):
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    # Filter ServiceBills by rent__project and bill_month
    if projectref_id:
        bills = ServiceBill.objects.filter(
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name   
    else:
        bills = ServiceBill.objects.filter(
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project_name = "All Projects"

    grand_total = sum(b.service_rent for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill_month.strftime("%B, %Y"),
        "project_name": project_name,
    }
    return render(request, "bill/bulk_print_service.html", context)



# Show project selection page
@login_required
def garbage_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today()
    return render(request, "bill/garbage_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


#  Fetch active rents of a project (AJAX)

@login_required
def get_project_garbage_rooms(request, project_id):
    rents = Rent.objects.filter(
        status='Active',
        room__project_id=project_id
    ).select_related('room', 'varatiya')

    data = []
    total = 0

    for rent in rents:
        room = rent.room
        if not room:
            continue

        subtotal = float(room.garbage_rent or 0)
        total += subtotal

        data.append({
            "room_name": room.room_name,
            "flat": room.flat,
            "client_name": rent.varatiya.name if rent.varatiya else '-',
            "garbage_rent": subtotal,
        })

    return JsonResponse({"rooms": data, "grand_total": total})


#  Generate bills and save in DB

@login_required
def create_garbage_bills(request):
    print("garbage bill generated")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"})

        rooms_list = data.get("rooms", [])
        bill_month_str = data.get("bill_month")
        if not bill_month_str:
            return JsonResponse({"success": False, "message": "Bill month is required."})

        try:
            bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid month format."})

        bills_created = []
        updated_count = 0
        new_count = 0

        for r in rooms_list:
            room_name = r.get("room_name", "-")
            flat = r.get("flat", "-")
            client_name = r.get("client_name", "-")

            rent_obj = Rent.objects.filter(
                status="Active",
                room__room_name=room_name,
                room__flat=flat,
                varatiya__name=client_name,
            ).first()

            existing_bill_qs = GarbageBill.objects.filter(
                bill_month=bill_month,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
            )

            if existing_bill_qs.exists():
                updated_count += existing_bill_qs.count()
                existing_bill_qs.delete()
            else:
                new_count += 1

            bill = GarbageBill.objects.create(
                rent=rent_obj,
                room_name=room_name,
                flat=flat,
                varatiya_name=client_name,
                garbage_rent=r.get("garbage_rent", 0),
                bill_month=bill_month,
                status="Generated",
            )
            bills_created.append(bill)

            if rent_obj and rent_obj.varatiya:
                description = f"Garbage Rent for {bill.varatiya_name} ({bill.room_name}) - {bill_month.strftime('%B %Y')}"

                ledger_qs = LedgerEntry.objects.filter(
                    tenant=rent_obj.varatiya,
                    bill_month=bill_month,
                    description=description,
                )

                if ledger_qs.exists():
                    ledger = ledger_qs.first()
                    ledger.debit = bill.garbage_rent
                    ledger.credit = 0
                    ledger.date = timezone.now().date()
                    ledger.save()
                else:
                    LedgerEntry.objects.create(
                        tenant=rent_obj.varatiya,
                        bill_month=bill_month,
                        date=timezone.now().date(),
                        description=description,
                        bill_no=None,
                        debit=bill.garbage_rent,
                        credit=0,
                        is_opening=False,
                        receive_voucher=None
                    )

        # Build message
        if new_count == 0 and updated_count > 0:
            message = f"Garbage bills for {bill_month.strftime('%B %Y')} already generated."
        else:
            message_parts = []
            if updated_count > 0:
                message_parts.append(f"{updated_count} existing garbage bill(s) updated")
            if new_count > 0:
                message_parts.append(f"{new_count} new garbage bill(s) created")
            message = ", ".join(message_parts) + "."

        return JsonResponse({
            "success": True,
            "message": message,
            "bills": [
                {
                    "id": bill.id,
                    "room_name": bill.room_name,
                    "flat": bill.flat,
                    "varatiya_name": bill.varatiya_name,
                    "garbage_rent": float(bill.garbage_rent),
                    "bill_month": bill.bill_month.strftime("%Y-%m-%d"),
                    "status": bill.status,
                    "rent_id": bill.rent.id if bill.rent else None,
                }
                for bill in bills_created
            ]
        })


#  Bulk Print

@login_required
def bulk_print_garbage_bills(request):
    projectref_id = request.GET.get("projectref")
    month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

    try:
        bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        bill_month = datetime.today().date()

    # Filter GarbageBills by rent__projectref and bill_month
    if projectref_id:
        bills = GarbageBill.objects.filter(
            rent__projectref=projectref_id,
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project = get_object_or_404(ProjectName, id=projectref_id)
        project_name = project.name
    else:
        bills = GarbageBill.objects.filter(
            bill_month=bill_month
        ).order_by("flat", "room_name")

        project_name = "All Projects"

    grand_total = sum(b.garbage_rent for b in bills)
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": bills,
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill_month.strftime("%B, %Y"),
        "project_name": project_name,
    }
    return render(request, "bill/bulk_print_garbage.html", context)





# Project select 
@login_required
def electricity_bill_generate(request):
    projects = ProjectName.objects.all()
    current_month = date.today().strftime("%Y-%m")
    return render(request, "bill/electricity_rent_generator.html", {
        "projects": projects,
        "current_month": current_month
    })


# Ajax: fetch active rents under a project
@login_required
def get_project_electricity_rents(request, project_id):
    rents = Rent.objects.filter(
        status="Active",
        room__project_id=project_id
    ).select_related("room", "varatiya")

    data = []
    for rent in rents:
        room = rent.room
        if not room:
            continue
        data.append({
            "rent_id": rent.id,
            "varatiya": rent.varatiya.name if rent.varatiya else "",
            "meter_number": room.meter_number,
            "opening_reading": room.opening_reading,
            "last_month_reading": room.last_month_reading,
            "unit_charge": float(room.unit_charge or 0),
            "flat": room.flat,
            "room_name": room.room_name,
        })

    return JsonResponse({"rents": data})



@login_required
def save_electricity_bill(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method. POST required."})

    # Parse JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON format."})

    # Collect and check missing fields
    missing_fields = []
    rent_id = data.get("rent_id")
    current_month_reading = data.get("current_month_reading")
    bill_month_str = data.get("bill_month")

    if not rent_id:
        missing_fields.append("Rent / Varatiya selection")
    if current_month_reading is None:
        missing_fields.append("Current Month Reading")
    if not bill_month_str:
        missing_fields.append("Bill Month")

    if missing_fields:
        return JsonResponse({
            "success": False,
            "message": f"Missing or invalid field(s): {', '.join(missing_fields)}"
        })

    # Validate current reading
    try:
        current_month_reading = Decimal(str(current_month_reading))
    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Current Month Reading must be a valid number."
        })

    # Validate bill month
    try:
        bill_month = datetime.strptime(bill_month_str + "-01", "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({
            "success": False,
            "message": "Bill Month format is invalid. Use YYYY-MM."
        })

    # Fetch rent
    try:
        rent = Rent.objects.select_related("room", "varatiya", "room__project").get(id=rent_id)
    except Rent.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Selected rent/varatiya does not exist."
        })

    room = rent.room
    varatiya_name = rent.varatiya.name if rent.varatiya else ""
    last_month_reading = Decimal(room.last_month_reading or 0)

    # Validate reading > last month
    if current_month_reading <= last_month_reading:
        return JsonResponse({
            "success": False,
            "message": f"❌ Current reading ({current_month_reading}) must be greater than last month's reading ({last_month_reading})."
        })

    # Unit charge
    try:
        new_unit_charge = Decimal(str(data.get("unit_charge", room.unit_charge or 0)))
    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Unit Charge must be a valid number."
        })

    reading = current_month_reading - last_month_reading
    amount = reading * new_unit_charge

    # Update room
    room.last_month_reading = current_month_reading
    room.unit_charge = new_unit_charge
    room.save()

    # Check for existing bill
    existing_bill = ElectricityBill.objects.filter(
        bill_month=bill_month,
        flat=room.flat,
        room_name=room.room_name,
        varatiya_name=varatiya_name
    ).first()

    if existing_bill:
        existing_bill.electricity_rent = amount
        existing_bill.used_units = reading
        existing_bill.status = f"{request.user.username} Generated"
        existing_bill.save()
        bill = existing_bill
        message = f"⚠ Bill already exists. Updated electricity bill for {varatiya_name} ({room.flat}-{room.room_name}) for {bill_month.strftime('%B %Y')}."
       
    else:
        bill = ElectricityBill.objects.create(
            rent=rent,
            room_name=room.room_name,
            flat=room.flat,
            varatiya_name=varatiya_name,
            electricity_rent=amount,
            used_units=reading,
            bill_month=bill_month,
            status=f"{request.user.username} Generated",
        )
        message = f"Bill generated for {varatiya_name} ({bill_month.strftime('%B %Y')})"
    
    if rent.varatiya:
        
        description = (f"Electricity Usage: ({current_month_reading} - {last_month_reading}) "
                        f"= {reading} unit "
                        
                      )
                      
        # description = (f"Electricity Usage: ({current_month_reading} - {last_month_reading}) "
        #                 f"= {reading} unit | {bill.varatiya_name} "
        #                 f"({bill.room_name}) | {bill_month.strftime('%B %Y')}"
        #               )
                      
        ledger_qs = LedgerEntry.objects.filter(
            tenant=rent.varatiya,
            bill_month=bill_month,
            description=description,
        )

        if ledger_qs.exists():
            ledger = ledger_qs.first()
            ledger.debit = amount
            ledger.credit = 0
            ledger.date = timezone.now().date()
            ledger.save()
        else:
            LedgerEntry.objects.create(
                tenant=rent.varatiya,
                bill_month=bill_month,
                date=timezone.now().date(),
                description= description,
                bill_no=None,
                debit=amount,
                credit=0,
                is_opening=False,
                receive_voucher=None
            )
    # Return response
    return JsonResponse({
        "success": True,
        "message": message,
        "bill": {
            "id": bill.id,
            "project_id": room.project.id,
            "project_name": room.project.name,
            "varatiya": bill.varatiya_name,
            "flat": bill.flat,
            "room_name": bill.room_name,
            "meter_number": room.meter_number,
            "opening_reading": room.opening_reading,
            "last_month_reading": last_month_reading,
            "current_reading": current_month_reading,
            "unit_charge": float(new_unit_charge),
            "used_units": float(reading),
            "amount": float(amount),
            "bill_month": bill.bill_month.strftime("%Y-%m"),
            "status": bill.status,
        }
    })


@login_required
def bulk_print_electricity_bills(request):

    bill_id = request.GET.get("bill_id")   

    if not bill_id:
        return render(request, "bill/bulk_print_electricity.html", {"error": "Bill ID not provided."})

    # Fetch the specific bill
    bill = get_object_or_404(ElectricityBill, id=bill_id)
    print(bill)
    grand_total = bill.electricity_rent
    total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

    context = {
        "bills": [bill],  # send as list for template compatibility
        "print_time": now(),
        "grand_total": grand_total,
        "total_in_words": total_in_words,
        "bill_month": bill.bill_month.strftime("%B, %Y"),
        "project_name": bill.rent.room.project.name if bill.rent and bill.rent.room else "N/A",
    }

    return render(request, "bill/bulk_print_electricity.html", context)



# def bulk_print_electricity_bills(request):
#     projectref_id = request.GET.get("projectref")
#     month_str = request.GET.get("month", datetime.today().strftime("%Y-%m"))

#     try:
#         bill_month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
#     except ValueError:
#         bill_month = datetime.today().date()

#     # Filter ElectricityBills by rent__projectref and bill_month

#     if projectref_id:
#         bills = ElectricityBill.objects.filter(
#             rent__projectref__project_id=projectref_id,
#             bill_month=bill_month
#         ).order_by("flat", "room_name")

#         project = get_object_or_404(ProjectFirstLevelName, id=projectref_id)
#         project_name = project.project_first_name   

#     else:
#         bills = ElectricityBill.objects.filter(
#             bill_month=bill_month
#         ).order_by("flat", "room_name")

#         project_name = "All Projects"

#     grand_total = sum(b.electricity_rent for b in bills)
#     total_in_words = num2words(grand_total, lang="en").title() + " Taka Only"

#     context = {
#         "bills": bills,
#         "print_time": now(),
#         "grand_total": grand_total,
#         "total_in_words": total_in_words,
#         "bill_month": bill_month.strftime("%B, %Y"),
#         "project_name": project_name,
#     }
#     return render(request, "bill/bulk_print_electricity.html", context)  





# Input & filter page
@login_required
def tenant_ledger_input_page(request):
    projects = ProjectName.objects.all()
    return render(request, "ledger/tenant_ledger_input.html", {"projects": projects})

# Result page
@login_required
def tenant_ledger_result_page(request):
    varatiya_id = request.GET.get("varatiya_id")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    include_opening = request.GET.get("include_opening", "no")

    if not varatiya_id:
        return redirect('tenant_ledger_input_page')

    varatiya = get_object_or_404(Varatiya, id=varatiya_id)

    # Step 1: fetch main transactions
    entries = varatiya.ledger_entries.filter(is_opening=False)
    if start_date and end_date:
        entries = entries.filter(date__range=[start_date, end_date])

    # Step 2: optionally include opening balance
    if include_opening == "yes":
        opening_entries = varatiya.ledger_entries.filter(is_opening=True)
        entries = opening_entries | entries  # combine QuerySets
        entries = entries.order_by("date")   # ensure date order

    # Running balance
    running_balance = 0
    rows = []
    for entry in entries:
        running_balance += entry.debit - entry.credit
        rows.append({
            "date": entry.date.strftime("%Y-%m-%d"),
            "description": entry.description,
            "bill_month": entry.bill_month.strftime("%B %Y") if entry.bill_month else "-",
            "bill_no": entry.bill_no or "-",
            "debit": float(entry.debit),
            "credit": float(entry.credit),
            "balance": float(running_balance)
        })

    total_debit = entries.aggregate(total=Sum("debit"))["total"] or 0
    total_credit = entries.aggregate(total=Sum("credit"))["total"] or 0
    receivable = total_debit - total_credit

    return render(request, "ledger/tenant_ledger_result.html", {
        "varatiya": varatiya,
        "rows": rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "receivable": receivable
    })


@login_required
def tenant_ledger_print(request):
    varatiya_id = request.GET.get("varatiya_id")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    include_opening = request.GET.get("include_opening", "no")

    if not varatiya_id:
        return redirect('tenant_ledger_input_page')

    varatiya = get_object_or_404(Varatiya, id=varatiya_id)

    # Fetch entries
    entries = varatiya.ledger_entries.filter(is_opening=False)
    if start_date and end_date:
        entries = entries.filter(date__range=[start_date, end_date])

    if include_opening == "yes":
        opening_entries = varatiya.ledger_entries.filter(is_opening=True)
        entries = opening_entries | entries
        entries = entries.order_by("date")

    running_balance = 0
    rows = []
    for entry in entries:
        running_balance += entry.debit - entry.credit
        rows.append({
            "date": entry.date.strftime("%Y-%m-%d"),
            "description": entry.description,
            "bill_month": entry.bill_month.strftime("%B %Y") if entry.bill_month else "-",
            "bill_no": entry.bill_no or "-",
            "debit": float(entry.debit),
            "credit": float(entry.credit),
            "balance": float(running_balance)
        })

    total_debit = entries.aggregate(total=Sum("debit"))["total"] or 0
    total_credit = entries.aggregate(total=Sum("credit"))["total"] or 0
    receivable = total_debit - total_credit

    context = {
        "varatiya": varatiya,
        "rows": rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "receivable": receivable,
        "print_time": now()
    }

    return render(request, "ledger/tenant_ledger_print.html", context)


    
# Ajax: fetch active varatiyas under a project
@login_required
def get_project_varatiyas(request, project_id):
    rents = Rent.objects.filter(status="Active", room__project_id=project_id).select_related("varatiya")
    data = [{"varatiya_id": rent.varatiya.id, "varatiya_name": rent.varatiya.name} 
            for rent in rents if rent.varatiya]
    return JsonResponse({"varatiyas": data})


# Ajax: fetch ledger of a varatiya
@login_required
def get_varatiya_ledger(request, varatiya_id):
    varatiya = get_object_or_404(Varatiya, id=varatiya_id)

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    include_opening = request.GET.get("include_opening", "no")

    entries = varatiya.ledger_entries.all()
    if include_opening == "no":
        entries = entries.filter(is_opening=False)
    elif include_opening == "yes":
        entries = entries.filter(is_opening=True)

    if start_date and end_date:
        entries = entries.filter(date__range=[start_date, end_date])

    running_balance = 0
    rows = []
    for entry in entries:
        running_balance += entry.debit - entry.credit
        rows.append({
            "date": entry.date.strftime("%Y-%m-%d"),
            "description": entry.description,
            "bill_no": entry.bill_no or "-",
            "debit": float(entry.debit),
            "credit": float(entry.credit),
            "balance": float(running_balance)
        })

    total_debit = entries.aggregate(total=Sum("debit"))["total"] or 0
    total_credit = entries.aggregate(total=Sum("credit"))["total"] or 0
    receivable = total_debit - total_credit

    return JsonResponse({
        "rows": rows,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "receivable": float(receivable)
    })



@login_required
def bill_summary_page(request):
    projects = ProjectName.objects.all()
    cash_types = TenantCashType.objects.all()  
    return render(
        request, 
        "report/bill_summary.html", 
        {
            "projects": projects,
            "cash_types": cash_types, 
        }
    )


@login_required
def get_project_varatiyas(request, project_id):
    rents = Rent.objects.filter(status="Active", room__project_id=project_id).select_related("varatiya")
    data = [
        {"varatiya_id": rent.varatiya.id, "varatiya_name": rent.varatiya.name}
        for rent in rents if rent.varatiya
    ]
    return JsonResponse({"varatiyas": data})






@login_required
def project_varatiya_bills(request):
    project_id = request.GET.get("project_id")
    varatiya_id = request.GET.get("varatiya_id")
    bill_month_str = request.GET.get("bill_month")

    if not all([project_id, varatiya_id, bill_month_str]):
        return JsonResponse({"error": "project_id, varatiya_id and bill_month are required"}, status=400)

    try:
        bill_month = datetime.strptime(bill_month_str, "%Y-%m")
    except ValueError:
        return JsonResponse({"error": "bill_month format should be YYYY-MM"}, status=400)

    filters = {
        "bill_month__year": bill_month.year,
        "bill_month__month": bill_month.month,
        "rent__projectref": project_id,
        "rent__varatiya_id": varatiya_id,
    }

    # Get individual bills
    rent_bill = Bill.objects.filter(**filters).first()
    service_bill = ServiceBill.objects.filter(**filters).first()
    gas_bill = GasBill.objects.filter(**filters).first()
    water_bill = WaterBill.objects.filter(**filters).first()
    parking_bill = ParkingBill.objects.filter(**filters).first()
    electricity_bill = ElectricityBill.objects.filter(**filters).first()
    garbage_bill = GarbageBill.objects.filter(**filters).first()  # Uncomment if you have GarbageBill

    # Amounts
    bills_data = {
        "Rent": rent_bill.subtotal if rent_bill else 0,
        "Service": service_bill.service_rent if service_bill else 0,
        "Gas": gas_bill.gas_rent if gas_bill else 0,
        "Water": water_bill.water_rent if water_bill else 0,
        "Parking": parking_bill.parking_cost if parking_bill else 0,
        "Garbage": garbage_bill.garbage_rent if garbage_bill else 0,       
        "Electricity": electricity_bill.electricity_rent if electricity_bill else 0,
    }

    total_amount = sum(bills_data.values())

    # Rent object for tenant/project info
    rent_obj = Rent.objects.filter(status="Active", room__project_id=project_id, varatiya_id=varatiya_id)\
                           .select_related("varatiya", "room", "room__project").first()
    tenant_name = rent_obj.varatiya.name if rent_obj and rent_obj.varatiya else ""
    project_name = rent_obj.room.project.name if rent_obj and rent_obj.room and rent_obj.room.project else ""
    room_name = rent_obj.room.room_name if rent_obj and rent_obj.room else ""

    #  Create or get MainBill
    main_bill, created = MainBill.objects.get_or_create(
        project_id=project_id,
        tenant_id=varatiya_id,
        month=bill_month,
        defaults={
            "rent_bill": rent_bill,
            "service_bill": service_bill,
            "gas_bill": gas_bill,
            "water_bill": water_bill,
            "parking_bill": parking_bill,
            "electricity_bill": electricity_bill,
            "garbage_bill": garbage_bill,  # Uncomment if exists
        }
    )

    # If already exists, update linked bills
    if not created:
        main_bill.rent_bill = rent_bill
        main_bill.service_bill = service_bill
        main_bill.gas_bill = gas_bill
        main_bill.water_bill = water_bill
        main_bill.parking_bill = parking_bill
        main_bill.electricity_bill = electricity_bill
        main_bill.garbage_bill = garbage_bill  
        main_bill.save()

    # Calculate generated_amount
    main_bill.calculate_generated_amount()
    main_bill.save()

    return JsonResponse({
        "bills": bills_data,
        "total_amount": total_amount,
        "tenant_name": tenant_name,
        "project_name": project_name,
        "room_name": room_name,
        "main_bill_id": main_bill.id
    })


from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages


@require_POST
@login_required
def create_receive_voucher(request):
    try:
        amount = request.POST.get("amount")
        cheque_id = request.POST.get("cheque_number")

        # Convert dates
        bill_date_str = request.POST.get("bill_date")
        voucher_date_str = request.POST.get("voucher_date")

        bill_date = None
        voucher_date = None

        if bill_date_str:
            bill_date = datetime.strptime(bill_date_str, "%Y-%m-%d").date()


        # Fetch cheque instance and check status
        cheque_instance = None
        if cheque_id:
            cheque_instance = get_object_or_404(Cheque, id=cheque_id)
            
            if cheque_instance.status == "used":
                messages.error(request, f"Cheque #{cheque_instance.cheque_number} has already been used.")
                return redirect("add_tenant_advance")

        # Create ReceiveVoucher
        rv = ReceiveVoucher.objects.create(
            project_name_id=request.POST.get("project_id"),
            tenant_name_id=request.POST.get("tenant_id"),
            bill_date=request.POST.get("bill_date"),
            date=request.POST.get("voucher_date"),
            generated_amount=request.POST.get("generated_amount"),
            amount=amount,
            rent_bill_id=request.POST.get("rent_bill_id"),
            service_bill_id=request.POST.get("service_bill_id"),
            gas_bill_id=request.POST.get("gas_bill_id"),
            water_bill_id=request.POST.get("water_bill_id"),
            parking_bill_id=request.POST.get("parking_bill_id"),
            electricity_bill_id=request.POST.get("electricity_bill_id"),
            cash_type_id=request.POST.get("cash_type_id"),
            cheque_number=cheque_instance,  # Assign instance
            particulars=request.POST.get("particulars"),
            carrier=request.POST.get("carrier"),
            mainbill_id=request.POST.get("mainbill_id")
        )

        # If cheque used, mark it as used and update amount
        if cheque_instance:
            cheque_instance.status = "used"
            cheque_instance.amount = amount
            cheque_instance.issue_date = datetime.now().date()  
            cheque_instance.remarks = request.POST.get("particulars")

            tenant_id = request.POST.get("tenant_id")

            if tenant_id:
                tenant = get_object_or_404(Varatiya, id=tenant_id)
                cheque_instance.payee_name = tenant.name  

            cheque_instance.save(update_fields=["status", "amount", "issue_date", "remarks", "payee_name"])


        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def bill_view_page(request):
    project_id = request.GET.get("project_id")
    varatiya_id = request.GET.get("varatiya_id")
    bill_month_str = request.GET.get("bill_month")

    if not all([project_id, varatiya_id, bill_month_str]):
        return render(request, "report/bill_view.html", {"error": "Missing parameters"})

    try:
        bill_month = datetime.strptime(bill_month_str, "%Y-%m")
    except ValueError:
        return render(request, "report/bill_view.html", {"error": "Invalid month format"})

    filters = {
        "bill_month__year": bill_month.year,
        "bill_month__month": bill_month.month,
        "rent__projectref": project_id,
        "rent__varatiya_id": varatiya_id,
    }

    bills_data = {
        "Rent": Bill.objects.filter(**filters).aggregate(total=Sum("core_room_rent"))["total"] or 0,
        "Service": ServiceBill.objects.filter(**filters).aggregate(total=Sum("service_rent"))["total"] or 0,
        "Gas": GasBill.objects.filter(**filters).aggregate(total=Sum("gas_rent"))["total"] or 0,
        "Water": WaterBill.objects.filter(**filters).aggregate(total=Sum("water_rent"))["total"] or 0,
        "Parking": ParkingBill.objects.filter(**filters).aggregate(total=Sum("parking_cost"))["total"] or 0,
        "Garbage": GarbageBill.objects.filter(**filters).aggregate(total=Sum("garbage_rent"))["total"] or 0,
        "Electricity": ElectricityBill.objects.filter(**filters).aggregate(total=Sum("electricity_rent"))["total"] or 0,
    }

    total_amount = sum(bills_data.values())

    rent_obj = Rent.objects.filter(status="Active", room__project_id=project_id, varatiya_id=varatiya_id).select_related("varatiya", "room", "room__project").first()
    tenant_name = rent_obj.varatiya.name if rent_obj and rent_obj.varatiya else ""
    project_name = rent_obj.room.project.name if rent_obj and rent_obj.room and rent_obj.room.project else ""
    room_name = rent_obj.room.room_name if rent_obj and rent_obj.room else ""
    total_in_words = num2words(total_amount, lang="en").title() + " Taka Only"

    electricity_bill = ElectricityBill.objects.filter(**filters).first()

    if electricity_bill:
        bills_data["Electricity"] = electricity_bill.electricity_rent or 0
        used_units = electricity_bill.used_units or 0  # <-- pass separately
    else:
        used_units = 0 
    context = {
        "project_name": project_name,
        "tenant_name": tenant_name,
        "room_name": room_name,
        "bill_month": bill_month.strftime("%B, %Y"),
        "bills": bills_data,
        "total_amount": total_amount,
        "total_in_words": total_in_words,
        "print_time": timezone.now(),
        "used_units": used_units, 
    }
    return render(request, "report/bill_view.html", context)





@login_required
def receive_voucher_list(request):
    vouchers = ReceiveVoucher.objects.all().order_by('approval_rv_status','-id')
    paginator = Paginator(vouchers, 20)   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vouchers': page_obj  
    }
    return render(request, 'admin/receive_voucher_list.html', context) 



@login_required
def receive_voucher_edit(request, pk):
    # Get the voucher or 404
    voucher = get_object_or_404(ReceiveVoucher, pk=pk)

    if request.method == 'POST':
        form = ReceiveVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()  # save the edited voucher
            messages.success(request, f'Receive Voucher #{voucher.id} updated successfully.')
            return redirect('receive_voucher_list')  # change to your list URL
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReceiveVoucherForm(instance=voucher)

    context = {
        'form': form,
        'voucher': voucher
    }
    return render(request, 'admin/receive_voucher_form.html', context)
    


@login_required
def receive_voucher_delete(request, pk):
    voucher = get_object_or_404(ReceiveVoucher, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        messages.success(request, f'Receive Voucher #{pk} has been deleted.')
        return redirect('receive_voucher_list')
    return render(request, 'admin/receive_voucher_confirm_delete.html', {'voucher': voucher})
    
    

@login_required
def receive_voucher_pdf(request, pk):
    voucher = get_object_or_404(ReceiveVoucher, pk=pk)
    total_in_words = num2words(voucher.amount, lang="en").title() + " Taka Only"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': total_in_words,
    }

    return render(request, 'admin/print_receivevoucher.html', context)

@login_required
def approve_receive_voucher(request, pk):

    voucher = get_object_or_404(ReceiveVoucher, pk=pk)

    # Base case 1: already approved
    if voucher.approval_rv_status:
        messages.warning(request, f"Voucher #{voucher.id} is already approved.")
        return redirect('receive_voucher_list')

    # Base case 2: no cash_type assigned
    if not voucher.cash_type:
        messages.error(request, f"Voucher #{voucher.id} has no cash type assigned. Cannot process payment.")
        return redirect('receive_voucher_list')

    # Base case 3: no tenant assigned
    if not voucher.tenant_name:
        messages.error(request, f"Voucher #{voucher.id} has no tenant assigned. Cannot create LedgerEntry.")
        return redirect('receive_voucher_list')

    try:
        with transaction.atomic():
            #  Approve voucher
            voucher.approval_rv_status = True
            voucher.is_confirmed = True
            voucher.save()

            #  Add money to cash_type
            voucher.cash_type.add_money(voucher.amount)

            #  Update MainBill
            if voucher.mainbill and voucher.amount and voucher.amount > 0:
                voucher.mainbill.add_payment(Decimal(voucher.amount))

            #  Create LedgerEntry
            is_opening_entry = False
            
            if voucher.tenant_advance and not any([
                voucher.rent_bill,
                voucher.gas_bill,
                voucher.water_bill,
                voucher.parking_bill,
                voucher.service_bill,
                voucher.electricity_bill
            ]):
                is_opening_entry = True

            # Create LedgerEntry
            LedgerEntry.objects.create(
                tenant=voucher.tenant_name,
                bill_month=voucher.date,
                date=voucher.bill_date,
                description=f"Receive Voucher #{voucher.id} - {voucher.particulars}",
                bill_no=voucher.mr_or_bill_no,
                debit=0,
                credit=voucher.amount,
                receive_voucher=voucher,
                is_opening=is_opening_entry
            )
        
        messages.success(
            request,
            f"Voucher #{voucher.id} approved, Tk {voucher.amount} added to {voucher.cash_type}, Ledger updated."
        )
    except Exception as e:
        messages.error(request, f"Error processing voucher #{voucher.id}: {str(e)}")
    
    # ================= SMS SECTION =================

    # Static admin number
    admin_number = "8801913222203"
    
    # Dynamic tenant number (from Varatiya table)
    tenant_number = (
        voucher.tenant_name.contact
        if voucher.tenant_name and voucher.tenant_name.contact
        else None
    )
    
    # Combine both numbers (remove None + duplicates)
    sms_numbers = list(filter(None, {admin_number, tenant_number}))
    
    # Updated SMS message
    sms_message = (
        "Dear Tenant,\n"
        f"This is to confirm receipt of BDT {voucher.amount:,.2f} "
        f"as house rent for {voucher.bill_date.strftime('%B %Y')}.\n"
        f"Receipt No: {voucher.tenant_name.contact} | "
        f"Tenant: {voucher.tenant_name.name}\n"
        "Regards,\n"
        "📞 09639222203"
    )
    
    # Send SMS to all numbers safely
    for number in sms_numbers:
        if not send_sms(number, sms_message):
            print(f"SMS sending failed for {number} (ignored).")




    return redirect('receive_voucher_list')




# def add_tenant_advance(request):
#     if request.method == "POST":
#         tenant_id = request.POST.get("tenant_id")
#         amount = request.POST.get("amount")
#         remarks = request.POST.get("remarks", "")

#         tenant = get_object_or_404(Varatiya, id=tenant_id)
#         amount = float(amount)

#         #  Check if this tenant already has an advance
#         advance, created = TenantAdvance.objects.get_or_create(
#             varatiya=tenant,
#             defaults={
#                 "amount": amount,
#                 "date": timezone.now(),
#                 "remarks": remarks,
#             }
#         )

#         if not created:
#             # Update existing advance instead of creating a new one
#             advance.amount += amount
#             advance.remarks = (advance.remarks or "") + f" | Added {amount} Tk on {timezone.now().date()}"
#             advance.save()
#             messages.success(request, f"Existing advance updated. Total = {advance.amount} Tk for {tenant.name}.")
#         else:
#             messages.success(request, f"New advance of {amount} Tk added for {tenant.name}.")

#         return redirect("tenant_advance_list")

#     tenants = Varatiya.objects.all()
#     return render(request, "tenant/add_tenant_advance.html", {"tenants": tenants}) 



@login_required
def add_tenant_advance(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        project_id = request.POST.get("project_id")
        cash_type_id = request.POST.get("cash_type_id")
        amount = Decimal(request.POST.get("amount", 0))
        remarks = request.POST.get("remarks", "")
        
        cheque_id = request.POST.get("cheque_number", "")
        carrier = request.POST.get("carrier", "")
        particulars = request.POST.get("particulars", "")

        #  Required validation
        if not tenant_id or not project_id or amount <= 0:
            messages.error(request, "Please fill in all required fields properly.")
            return redirect("add_tenant_advance")

        tenant = get_object_or_404(Varatiya, id=tenant_id)
        project = get_object_or_404(ProjectName, id=project_id)
        cash_type = get_object_or_404(TenantCashType, id=cash_type_id)

        cheque_instance = None
        if cheque_id:
            cheque_instance = get_object_or_404(Cheque, id=cheque_id)

            
            if cheque_instance.status == "used":
                messages.error(request, f"Cheque #{cheque_instance.cheque_number} has already been used.")
                return redirect("add_tenant_advance")


        # Check if tenant already has an advance
        advance, created = TenantAdvance.objects.get_or_create(
            varatiya=tenant,
            defaults={
                "amount": amount,
                "date": timezone.now(),
                "remarks": remarks,
            }
        )

        if not created:
            # Update existing advance
            advance.amount += amount
            advance.remarks = (advance.remarks or "") + f" | Added {amount} Tk on {timezone.now().date()}"
            advance.save()
            msg = f"Existing advance updated. Total = {advance.amount} Tk for {tenant.name}."
        else:
            msg = f"New advance of {amount} Tk added for {tenant.name}."

        #  Always create a ReceiveVoucher (for both create & update)
        rv = ReceiveVoucher.objects.create(
            project_name=project,
            tenant_name=tenant,
            cash_type=cash_type,
            cheque_number=cheque_instance,
            carrier=carrier,
            date=timezone.now().date(),
            amount=amount,
            generated_amount=amount,
            particulars=particulars or f"Advance payment received from {tenant.name} ({amount} Tk)",
            tenant_advance=advance,
        )

        # if cheque_instance:
        #     cheque_instance.status = "used"
        #     cheque_instance.amount = amount 
        #     cheque_instance.save(update_fields=["status", "amount"])

        if cheque_instance:
            cheque_instance.status = "used"
            cheque_instance.amount = amount
            cheque_instance.issue_date = timezone.now().date()  # set issue_date to today
            cheque_instance.payee_name = tenant.name           # save tenant name
            cheque_instance.remarks = particulars or f"Advance payment received from {tenant.name} ({amount} Tk)"
            cheque_instance.save(update_fields=["status", "amount", "issue_date", "payee_name", "remarks"])

            
        messages.success(request, f"{msg} ReceiveVoucher #{rv.id} created successfully.")
        return redirect("tenant_advance_list")

    # GET request — render form
    tenants = Varatiya.objects.all()
    projects = ProjectName.objects.all()
    cash_types = TenantCashType.objects.all()
    return render(request, "tenant/add_tenant_advance.html", {
        "tenants": tenants,
        "projects": projects,
        "cash_types": cash_types,
    })

@login_required
def get_cheques_by_cash_type(request, cash_type_id):
    print(cash_type_id)
    
    cheques = Cheque.objects.filter(
        cheque_book__account_id=cash_type_id,
        cheque_book__is_active=True,
        status="unused"
    ).values("id", "cheque_number")
    return JsonResponse(list(cheques), safe=False) 

@login_required
def tenant_advance_list(request):
    advances = TenantAdvance.objects.select_related('varatiya').order_by('-date')
    context = {
        "advances": advances
    }
    return render(request, "tenant/tenant_advance_list.html", context)

@login_required
def delete_tenant_advance(request, advance_id):
    advance = get_object_or_404(TenantAdvance, id=advance_id)
    advance.delete()
    messages.success(request, "Tenant advance deleted successfully.")
    return redirect('tenant_advance_list')



@login_required
def payment_tenant_advance(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        project_id = request.POST.get("project_id")
        cash_type_id = request.POST.get("cash_type_id")
        amount = Decimal(request.POST.get("amount", 0))
        remarks = request.POST.get("remarks", "")
        cheque_id = request.POST.get("cheque_number", "")
        carrier = request.POST.get("carrier", "")
        particulars = request.POST.get("particulars", "")

        #  Validation
        if not tenant_id or not project_id or amount <= 0:
            messages.error(request, "Please fill in all required fields properly.")
            return redirect("payment_tenant_advance")

        tenant = get_object_or_404(Varatiya, id=tenant_id)
        project = get_object_or_404(ProjectName, id=project_id)
        cash_type = get_object_or_404(TenantCashType, id=cash_type_id)

        # Check tenant's advance record
        advance = TenantAdvance.objects.filter(varatiya=tenant).first()
        if not advance:
            messages.error(request, f"{tenant.name} has no advance balance.")
            return redirect("payment_tenant_advance")

        remaining = advance.remaining_balance
        if amount > remaining:
            messages.error(request, f"Insufficient advance balance! Available: Tk {remaining}.")
            return redirect("payment_tenant_advance")

        # If cheque selected, fetch instance and validate
        cheque_instance = None
        if cheque_id:
            try:
                cheque_instance = get_object_or_404(Cheque, id=cheque_id)
            except Exception:
                cheque_instance = None

            if cheque_instance:
                # prevent reuse
                if cheque_instance.status == "used":
                    messages.error(request, f"Cheque #{cheque_instance.cheque_number} has already been used.")
                    return redirect("payment_tenant_advance")


        # Update advance adjusted amount
        advance.adjusted_amount += amount
        advance.remarks = (advance.remarks or "") + f" | Adjusted {amount} Tk on {timezone.now().date()}"
        advance.save()

        msg = f"Advance adjusted. Remaining = {advance.remaining_balance} Tk for {tenant.name}."

        #  Create PaymentVoucher
        pv = PaymentVoucher.objects.create(
            project_name=project,
            tenant_name=tenant,
            cash_type=cash_type,
            cheque_number=cheque_instance,
            carrier=carrier,
            date=timezone.now().date(),
            amount=amount,
            particulars=particulars or f"Advance adjustment payment for {tenant.name} ({amount} Tk)",
            tenant_advance=advance,
        )

        # If cheque used, update cheque record
        if cheque_instance:
            cheque_instance.status = "used"
            cheque_instance.amount = amount  # set cheque amount if you want
            cheque_instance.issue_date = timezone.now().date()
            cheque_instance.payee_name = tenant.name
            cheque_instance.remarks = particulars or f"Advance adjustment payment for {tenant.name} ({amount} Tk)"
            cheque_instance.save(update_fields=["status", "amount", "issue_date", "payee_name", "remarks"])

        

        messages.success(request, f"{msg} PaymentVoucher #{pv.id} created successfully.")
        return redirect("tenant_advance_list")

    # GET request — render form
    tenants = Varatiya.objects.all()
    projects = ProjectName.objects.all()
    cash_types = TenantCashType.objects.all()
    return render(request, "tenant/payment_tenant_advance.html", {
        "tenants": tenants,
        "projects": projects,
        "cash_types": cash_types,
    })




@login_required
def payment_voucher_list(request):
    vouchers = PaymentVoucher.objects.all().order_by('approval_pv_status','-id')
    paginator = Paginator(vouchers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vouchers': page_obj
    }
    return render(request, 'admin/payment_voucher_list.html', context)


@login_required
def payment_voucher_pdf(request, pk):
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    total_in_words = num2words(voucher.amount, lang="en").title() + " Taka Only"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': total_in_words,
    }

    return render(request, 'admin/print_paymentvoucher.html', context) 


# @login_required
# def approve_payment_voucher(request, pk):
#     voucher = get_object_or_404(PaymentVoucher, pk=pk)

#     # Base case 1: already approved
#     if voucher.approval_pv_status:
#         messages.warning(request, f"Payment Voucher #{voucher.id} is already approved.")
#         return redirect('payment_voucher_list')

#     # Base case 2: no cash_type assigned
#     if not voucher.cash_type:
#         messages.error(request, f"Voucher #{voucher.id} has no cash type assigned. Cannot process payment.")
#         return redirect('payment_voucher_list')

#     # Base case 3: no tenant assigned
#     if not voucher.tenant_name:
#         messages.error(request, f"Voucher #{voucher.id} has no tenant assigned. Cannot create LedgerEntry.")
#         return redirect('payment_voucher_list')

#     try:
#         with transaction.atomic():
#             #  Approve voucher
#             voucher.approval_pv_status = True
#             voucher.save()

#             #  Deduct money from cash_type
#             voucher.cash_type.deduct_money(voucher.amount)

#             # Create LedgerEntry
#             LedgerEntry.objects.create(
#                 tenant=voucher.tenant_name,
#                 bill_month=voucher.date,
#                 date=timezone.now().date(),
#                 description=f"Payment Voucher #{voucher.id} - {voucher.particulars}",
#                 # bill_no=voucher.mr_or_bill_no,
#                 debit=voucher.amount,
#                 credit=0,
#                 payment_voucher=voucher,
#                 is_opening=True
#             )

#         messages.success(
#             request,
#             f"Payment Voucher #{voucher.id} approved, Tk {voucher.amount} deducted from {voucher.cash_type}, Ledger updated."
#         )
#     except Exception as e:
#         messages.error(request, f"Error processing payment voucher #{voucher.id}: {str(e)}")

#     return redirect('payment_voucher_list')

@login_required
def approve_payment_voucher(request, pk):
    voucher = get_object_or_404(PaymentVoucher, pk=pk)

    if voucher.approval_pv_status:
        messages.warning(request, f"Payment Voucher #{voucher.id} is already approved.")
        return redirect('payment_voucher_list')

    if not voucher.cash_type:
        messages.error(request, f"Voucher #{voucher.id} has no cash type assigned.")
        return redirect('payment_voucher_list')

    # tenant ও supplier দুটোই না থাকলে error
    if not voucher.tenant_name and not voucher.supplier:
        messages.error(
            request,
            f"Voucher #{voucher.id} has no tenant or supplier assigned."
        )
        return redirect('payment_voucher_list')

    try:
        with transaction.atomic():

            voucher.approval_pv_status = True
            voucher.save()

            voucher.cash_type.deduct_money(voucher.amount)

            # tenant case
            if voucher.tenant_name:

                LedgerEntry.objects.create(
                    tenant=voucher.tenant_name,
                    bill_month=voucher.date,
                    date=timezone.now().date(),
                    description=f"Payment Voucher #{voucher.id} - {voucher.particulars}",
                    debit=voucher.amount,
                    credit=0,
                    payment_voucher=voucher,
                    is_opening=True
                )

            # supplier case
            elif voucher.supplier:

                LedgerEntry.objects.create(
                    supplier=voucher.supplier,
                    bill_month=voucher.date,
                    date=timezone.now().date(),
                    description=f"Supplier Payment Voucher #{voucher.id} - {voucher.particulars}",
                    debit=voucher.amount,
                    credit=0,
                    payment_voucher=voucher,
                    is_opening=False
                )

        messages.success(
            request,
            f"Payment Voucher #{voucher.id} approved successfully."
        )

    except Exception as e:
        messages.error(request, f"Error processing voucher: {str(e)}")

    return redirect('payment_voucher_list')
    
    

#  List all MainBills
@login_required
def mainbill_list(request):
    bills = MainBill.objects.all().order_by('-month')
    return render(request, 'bill/mainbill_list.html', {'bills': bills})

@login_required
def main_bill_list(request):
    # --- Filter Inputs ---
    project_id = request.GET.get('project')
    tenant_id = request.GET.get('tenant')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # --- Base Query ---
    bills = MainBill.objects.all().order_by('-month')

    # --- Apply filters ---
    if project_id:
        bills = bills.filter(project_id=project_id)
    if tenant_id:
        bills = bills.filter(tenant_id=tenant_id)
    if status:
        bills = bills.filter(status=status)
    if start_date and end_date:
        bills = bills.filter(month__range=[start_date, end_date])
    elif start_date:
        bills = bills.filter(month__gte=start_date)
    elif end_date:
        bills = bills.filter(month__lte=end_date)

    # --- Subtotals ---
    totals = bills.aggregate(
        total_generated=Sum('generated_amount'),
        total_adjusted=Sum('adjusted_amount'),
        total_discount=Sum('discount_amount'),
        total_due=Sum('total_due'),
        total_paid=Sum('total_paid'),
    )
    

    # --- All Dropdown Data ---
    tenants = Varatiya.objects.all().order_by('name')
    projects = ProjectName.objects.all().order_by('name')

    context = {
        'bills': bills,
        'totals': totals,
        'tenants': tenants,
        'projects': projects,
    }
    return render(request, 'bill/mainbill_report.html', context)



#  Apply discount to a MainBill
@login_required
def apply_discount_to_mainbill(request, pk):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect('mainbill_list')

    mainbill = get_object_or_404(MainBill, pk=pk)
    discount_value = request.POST.get("discount_amount", 0)

    try:
        result = mainbill.add_discount_amount(discount_value)
        messages.success(
            request,
            f"Discount Tk {result['discount_amount']} applied successfully. Adjusted Amount: Tk {result['adjusted_amount']}, Total Due: Tk {result['total_due']}"
        )
    except Exception as e:
        messages.error(request, f"Error applying discount: {str(e)}")

    return redirect('mainbill_list')




@login_required
def cheque_book_list(request):
    # Add ChequeBook
    if request.method == 'POST':
        form = ChequeBookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cheque_book_list')
    else:
        form = ChequeBookForm()

    # Get all accounts
    accounts = TenantCashType.objects.all().order_by('account_name')

    #  Filter cheque books by selected account
    account_id = request.GET.get('account_id')
    if account_id:
        books = ChequeBook.objects.filter(account_id=account_id).order_by('-id')
        selected_account = TenantCashType.objects.get(id=account_id)
    else:
        books = None
        selected_account = None

    context = {
        'form': form,
        'accounts': accounts,
        'books': books,
        'selected_account': selected_account,
    }
    return render(request, 'cheques/cheque_book_list.html', context)

# ---- Page 2: View Cheques for a specific ChequeBook ----
@login_required
def cheque_list(request, book_id):
    book = get_object_or_404(ChequeBook, id=book_id)
    cheques = book.cheques.all().order_by('cheque_number')

    # Optional: Add new cheque manually
    if request.method == 'POST':
        form = ChequeForm(request.POST)
        if form.is_valid():
            cheque = form.save(commit=False)
            cheque.cheque_book = book
            cheque.save()
            return redirect('cheque_list', book_id=book.id)
    else:
        form = ChequeForm(initial={'cheque_book': book})

    return render(request, 'cheques/cheque_list.html', {
        'book': book,
        'cheques': cheques,
        'form': form,
    })


# ---- Edit/Delete ----
@login_required
def edit_book(request, pk):
    book = get_object_or_404(ChequeBook, pk=pk)
    if request.method == 'POST':
        form = ChequeBookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('cheque_book_list')
    else:
        form = ChequeBookForm(instance=book)
    return render(request, 'cheques/edit_book.html', {'form': form})


@login_required
def delete_book(request, pk):
    book = get_object_or_404(ChequeBook, pk=pk)
    book.delete()
    return redirect('cheque_book_list')

@login_required
def edit_cheque(request, pk):
    cheque = get_object_or_404(Cheque, pk=pk)
    if request.method == 'POST':
        form = ChequeForm(request.POST, instance=cheque)
        if form.is_valid():
            form.save()
            return redirect('cheque_list', book_id=cheque.cheque_book.id)
    else:
        form = ChequeForm(instance=cheque)
    return render(request, 'cheques/edit_cheque.html', {'form': form})

@login_required
def delete_cheque(request, pk):
    cheque = get_object_or_404(Cheque, pk=pk)
    book_id = cheque.cheque_book.id
    cheque.delete()
    return redirect('cheque_list', book_id=book_id)


@login_required
def tenantcash_list(request):
    accounts = TenantCashType.objects.all().order_by('-created_at')
    return render(request, 'accounting/tenantcash_list.html', {'accounts': accounts})

@login_required
def tenantcash_detail(request, pk):
    account = get_object_or_404(TenantCashType, pk=pk)
    return render(request, 'accounting/tenantcash_detail.html', {'account': account})

@login_required
def tenantcash_create(request):
    if request.method == 'POST':
        form = TenantCashForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_list')
    else:
        form = TenantCashForm()
    return render(request, 'accounting/tenantcash_form.html', {'form': form, 'title': 'Add Account'})


@login_required
def tenantcash_edit(request, pk):
    account = get_object_or_404(TenantCashType, pk=pk)
    if request.method == 'POST':
        form = TenantCashForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('account_detail', pk=account.pk)
    else:
        form = TenantCashForm(instance=account)
    return render(request, 'accounting/tenantcash_form.html', {'form': form, 'title': 'Edit Account'})


@login_required
@require_POST
def tenantcash_delete(request, pk):
    account = get_object_or_404(TenantCashType, pk=pk)
    account.delete()
    return JsonResponse({'success': True})
    
    
    
    
    
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Attendance
from datetime import datetime, timedelta

@csrf_exempt
def iclock_cdata(request):
    if request.method == "POST":
        raw = request.body.decode()
        lines = raw.strip().splitlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    user_id = int(parts[0])
                    punch_time = datetime.strptime(parts[1] + " " + parts[2], "%Y-%m-%d %H:%M:%S")
                    punch_time = punch_time - timedelta(hours=2)
                    
                    status = int(parts[3])
                    check_type = int(parts[4]) if len(parts) > 4 else 0
                    field1 = int(parts[5]) if len(parts) > 5 else 0
                    field2 = int(parts[6]) if len(parts) > 6 else 0
                    field3 = int(parts[7]) if len(parts) > 7 else 0
                    field4 = int(parts[8]) if len(parts) > 8 else 0
                    field5 = int(parts[9]) if len(parts) > 9 else 0
                    field6 = int(parts[10]) if len(parts) > 10 else 0
                    device_sn = request.GET.get("SN", "UNKNOWNxCpael")

                    Attendance.objects.create(
                        user_id=user_id,
                        punch_time=punch_time,
                        status=status,
                        check_type=check_type,
                        field1=field1,
                        field2=field2,
                        field3=field3,
                        field4=field4,
                        field5=field5,
                        field6=field6,
                        device_sn=device_sn
                    )
                except Exception as e:
                    print(f"Failed to parse line: {line}, Error: {e}")
    return HttpResponse("OK")
    
    
    
    
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Attendance

def upload_csv(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a CSV file.")
            return redirect('upload_csv')
        
        # Decode CSV file
        file_data = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(file_data)
        
        for row in reader:
            # Assuming CSV columns are: user_id, punch_time, status, check_type, field1,...,device_sn
            Attendance.objects.create(
                user_id=int(row.get("user_id", 0)),
                punch_time=row.get("punch_time"),
                status=int(row.get("status", 0)),
                check_type=int(row.get("check_type", 0)),
                field1=int(row.get("field1", 0)),
                field2=int(row.get("field2", 0)),
                field3=int(row.get("field3", 0)),
                field4=int(row.get("field4", 0)),
                field5=int(row.get("field5", 0)),
                field6=int(row.get("field6", 0)),
                device_sn=row.get("device_sn", ""),
            )
        
        messages.success(request, "CSV file uploaded successfully!")
        return redirect('upload_csv')
    
    return render(request, "tenant/upload_csv.html")




from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Varatiya, TenantBulkSMS, TenantBulkSMSRecipient
from .forms import TenantBulkSMSForm
from accounting.utils.sms import send_sms
from datetime import date

@login_required
def varatiya_bulk_sms(request):

    # Get all Varatiya (contact list)
    varatiya_list = Varatiya.objects.all().order_by('name')

    month_text = date.today().strftime("%B %Y")
    
    default_message = f"""Dear Tenant,
    
This is a gentle reminder that your monthly payment for {month_text} is now due.
Kindly arrange the payment within the due date.

Thank you.
BTP Limited
09639222203"""

    if request.method == "POST":

        selected_varatiya = request.POST.getlist("selected_varatiya")
        message = request.POST.get("message")

        if not selected_varatiya:
            messages.error(request, "Please select at least one contact.")
            return redirect("varatiya_bulk_sms")

        # Save bulk SMS
        bulk_sms = TenantBulkSMS.objects.create(
            message=message,
            created_by=request.user
        )

        for var_id in selected_varatiya:

            var = Varatiya.objects.filter(id=var_id).first()

            if var and var.contact:
                result = send_sms(var.contact, message)

                TenantBulkSMSRecipient.objects.create(
                    bulk_sms=bulk_sms,
                    tenant_name=var.name,
                    phone_number=var.contact,
                    status="Sent" if result else "Failed"
                )

        messages.success(request, "SMS sent successfully!")
        return redirect("varatiya_bulk_sms")

    form = TenantBulkSMSForm(initial={"message": default_message})

    context = {
        "varatiya_list": varatiya_list,
        "form": form,
    }

    return render(request, "tenant/bulk_sms.html", context)
    
    
    
@login_required
def varatiya_bulk_sms_list(request):

    sms_history = TenantBulkSMS.objects.all().order_by("-created_at")

    context = {
        "sms_history": sms_history
    }

    return render(
        request,
        "tenant/sms_history_list.html",
        context
    )
 
 
    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ProjectName, TenantCashType, Supplier

@login_required
def supplier_payment_page(request):

    projects = ProjectName.objects.all()
    cash_types = TenantCashType.objects.all()
    suppliers = Supplier.objects.all()

    return render(
        request,
        "report/supplier_payment.html",
        {
            "projects": projects,
            "cash_types": cash_types,
            "suppliers": suppliers,
        },
    )
    
    
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from datetime import datetime


@require_POST
@login_required
def create_supplier_payment(request):

    try:
        amount = request.POST.get("amount")
        cheque_id = request.POST.get("cheque_number")

        cheque_instance = None

        if cheque_id and cheque_id.isdigit():
        
            cheque_instance = get_object_or_404(Cheque, id=cheque_id)
        
            if cheque_instance.status == "used":
                return JsonResponse({
                    "success": False,
                    "error": f"Cheque #{cheque_instance.cheque_number} already used"
                })

        supplier = get_object_or_404(Supplier, id=request.POST.get("supplier_id"))

        pv = PaymentVoucher.objects.create(
            project_name_id=request.POST.get("project_id"),
            supplier=supplier,
            date=request.POST.get("voucher_date"),
            amount=amount,
            cash_type_id=request.POST.get("cash_type_id"),
            cheque_number=cheque_instance,
            particulars=request.POST.get("particulars"),
            carrier=request.POST.get("carrier"),
        )


        # Update cheque if used
        if cheque_instance:

            cheque_instance.status = "used"
            cheque_instance.amount = amount
            cheque_instance.issue_date = datetime.now().date()
            cheque_instance.remarks = request.POST.get("particulars")
            cheque_instance.payee_name = supplier.name

            cheque_instance.save(
                update_fields=[
                    "status",
                    "amount",
                    "issue_date",
                    "remarks",
                    "payee_name"
                ]
            )


        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
        
        
        
@login_required
def add_supplier(request):

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        company_name = request.POST.get("company_name")
        head_of_account = request.POST.get("head_of_account")

        Supplier.objects.create(
            name=name,
            phone=phone,
            email=email,
            address=address,
            company_name=company_name,
            head_of_account=head_of_account,
        )

        messages.success(request, "Supplier added successfully!")
        return redirect("add_supplier")

    return render(request, "report/add_supplier.html")
    
    
    