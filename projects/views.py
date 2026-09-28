from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import tempfile
from .models import BOQ
from .forms import BOQForm
from django.contrib import messages
from properties.models import Project
from projects.models import BoRevisedItem,ProjectLocation,ProjectFirstLevelName,EmployeeCost,SafetyEquipment,ExpenseCost,Suppliers,SiteSupervisor,Suppliers,ContractorActivity,MaterialEntry,Donation
from .forms import ProjectFirstLevelName,ProjectLocationForm,BoRevisedItemForm,BoQCategoryTypeForm,ContractorActivityForm,MaterialEntryForm,DonationForm
from .forms import ProjectFirstLevelNameForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from io import BytesIO
import logging
from decimal import Decimal, InvalidOperation
from .models import BoQCategory
from purchase.models import HeadOfRequisition
from .forms import BoQCategoryForm,SiteSupervisorForm,MaterialEntryForm
from django.db.models import Sum,Avg
from calendar import month_name 
from datetime import date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta 
from datetime import datetime
import calendar
from django.db.models import Min
from .forms import SuppliersForm
from datetime import datetime 
from django.utils import timezone
from .models import BoQType
from inventories.utils import log_deleted_data
from django.utils.dateparse import parse_date
from django.db.models import Min, Max
from django.db.models import F
from datetime import date
from django.core.paginator import Paginator


logger = logging.getLogger(__name__)
@login_required
def boq_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()
    boQTypes = BoQType.objects.all()
    BoQ_Category_Types = BoQCategory.objects.values('boq_cat_type').annotate(id=Min('id'))
    boqs_grouped = BOQ.objects.values(
        'project_name__id',  
        'project_name__project_first_name',
        'project_name__location',
        'project_name__project_start_date',
        'project_name__project_end_date',
        'project_name__project_duration',
    ).annotate(total_amount=Sum('amount')       
    ).order_by('project_name__project_first_name')  

    context = {
        'boqs_grouped': boqs_grouped,
        'projects_firts': projects_firt,
        'boq_cat_types': BoQ_Category_Types,
        'boQTypes': boQTypes
    }

    return render(request, 'boq/boq_list.html', context)



@login_required
def revised_item_entry(request):
    project_id = request.GET.get('project_id')
    revised_id = request.GET.get('revised_id')

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    revised_boq = get_object_or_404(BOQ, id=revised_id) if revised_id else None

    # Auto-insert original item into BoRevisedItem if not already present
    if revised_boq:
        exists = BoRevisedItem.objects.filter(
            original_boq=revised_boq,
            project_name=project,
            is_new_entry=False
        ).exists()

        if not exists:
            BoRevisedItem.objects.create(
                project_name=project,
                original_boq=revised_boq,
                linked_boq=revised_boq,  # Link to original BOQ row
                category_type=revised_boq.category_type,
                category_name=revised_boq.category_name,
                supplier_name=revised_boq.supplier_name,
                item_name=revised_boq.item_name,
                unit=revised_boq.unit,
                qty=revised_boq.qty,
                rate=revised_boq.rate,
                amount=revised_boq.qty * revised_boq.rate,
                is_new_entry=False
            )

    if request.method == 'POST':
        form = BoRevisedItemForm(request.POST)
        if form.is_valid():
            revised_item = form.save(commit=False)
            revised_item.project_name = project
            revised_item.is_new_entry = True  # mark new entries
            if revised_boq:
                revised_item.original_boq = revised_boq
                revised_item.linked_boq = revised_boq  # save linked boq for tracking
                revised_item.category_type = revised_boq.category_type
                revised_item.supplier_name = revised_boq.supplier_name
            revised_item.save()

            # Update the original BOQ row with new revised item data
            if revised_boq:
                revised_boq.category_type = revised_item.category_type
                revised_boq.category_name = revised_item.category_name
                revised_boq.supplier_name = revised_item.supplier_name
                revised_boq.item_name = revised_item.item_name
                revised_boq.unit = revised_item.unit
                revised_boq.qty = revised_item.qty
                revised_boq.rate = revised_item.rate
                revised_boq.amount = revised_item.qty * revised_item.rate
                revised_boq.status_item = 'Superseded'  # optional, mark status changed
                revised_boq.save()

            return redirect(f"{request.path}?project_id={project_id}&revised_id={revised_id}")
        
    else:
        if revised_boq:
            initial_data = {
                'category_name': revised_boq.category_name,
                'item_name': revised_boq.item_name,
                'unit': revised_boq.unit,
                'qty': revised_boq.qty,
                'rate': revised_boq.rate,
            }
            form = BoRevisedItemForm(initial=initial_data)
        else:
            form = BoRevisedItemForm()

    boq_items = BoRevisedItem.objects.filter(project_name=project)

    return render(request, 'boq/revised_item_entry.html', {
        'project': project,
        'revised_boq': revised_boq,
        'form': form,
        'boq_items': boq_items,
    })




@login_required
def boqdetails_list(request):
    project_id = request.GET.get("project_id")
    projects = ProjectFirstLevelName.objects.all()

    if project_id:
        boqs = BOQ.objects.filter(project_name_id=project_id)
    else:
        boqs = BOQ.objects.all()

    # calculate totals (on full queryset, not just current page)
    total_qty = boqs.aggregate(total=Sum("qty"))["total"] or 0
    avg_rate = boqs.aggregate(avg=Avg("rate"))["avg"] or 0
    total_amount = boqs.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "boq/boqdetails_list.html", {
        "projects": projects,
        "boqs": boqs,   
        "selected_project": project_id,
        "total_qty": total_qty,
        "avg_rate": avg_rate,
        "total_amount": total_amount,
    })
    
    
    

# @login_required
# def boq_list_details(request, project_id):
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#     boqs = BOQ.objects.filter(project_name=project)

#     projects_first_name = ProjectFirstLevelName.objects.all()
#     boq_categories = BoQCategory.objects.all()

#     context = {
#         'boqs': boqs,
#         'projects_firts': project,
#         'projects_firt_names': projects_first_name,
#         'BoQ_Categorys': boq_categories,
#     }

#     return render(request, 'boq/boq_list_details.html', context)


@login_required
def boq_list_details(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boqs = BOQ.objects.filter(project_name=project)

    projects_first_name = ProjectFirstLevelName.objects.all()
    boq_categories = BoQCategory.objects.all()

    # Get revised items of the current project
    revised_boq_items = BOQ.objects.filter(project_name=project, update_item='Revised')
    print(revised_boq_items)
    context = {
        'boqs': boqs,
        'projects_firts': project,
        'projects_firt_names': projects_first_name,
        'BoQ_Categorys': boq_categories,
        'revised_boq_items': revised_boq_items,  # add this to context
    }

    return render(request, 'boq/boq_list_details.html', context)
    
    

@login_required
def boq_mate_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            boq_data = data.get('data', [])
            category_id = str(data.get('category', '')).strip()
            project_id = data.get('project_id', '')
            remark_text = data.get('remark') or request.GET.get('remark')

            if not boq_data or not category_id or not project_id:
                raise ValueError("Missing required fields (data, category, or project_id).")

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            category_obj = get_object_or_404(BoQCategory, pk=category_id)

            for item in boq_data:
                category_name = str(item.get('cat_name', '')).strip()
                supplier_id = item.get('sup_name')

                if not category_name:
                    return JsonResponse({'status': 'error', 'message': "Category name is missing."})
                if not supplier_id:
                    return JsonResponse({'status': 'error', 'message': "Supplier ID is missing."})

                # Fetch BoQCategory by name
                try:
                    category = BoQCategory.objects.get(boq_cat_name=category_name)
                except BoQCategory.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f"BoQ Category '{category_name}' does not exist."})

                # Fetch Supplier
                try:
                    supplier = Suppliers.objects.get(pk=supplier_id)
                except Suppliers.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f"Supplier with ID {supplier_id} does not exist."})

                # Convert qty and rate safely
                try:
                    qty = Decimal(str(item.get('qty', '0')).strip() or '0')
                    rate = Decimal(str(item.get('rate', '0')).strip() or '0')
                    amount = qty * rate
                except (InvalidOperation, ValueError):
                    return JsonResponse({'status': 'error', 'message': 'Invalid numeric format in qty or rate.'})

                form = BOQForm({
                    'project_name': project.id,
                    'category_type': category.boq_cat_type,
                    'category_name': category.boq_cat_name,
                    'supplier_name': supplier.id,
                    'item_name': item.get('item_name', '').strip(),
                    'unit': item.get('unit', '').strip(),
                    'qty': qty,
                    'rate': rate,
                    'amount': amount,
                    'remark': remark_text,
                })

                if form.is_valid():
                    form.save()
                else:
                    return JsonResponse({'status': 'error', 'message': 'Form data is invalid.', 'errors': form.errors})

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except ValueError as ve:
            return JsonResponse({'status': 'error', 'message': str(ve)})
        except json.JSONDecodeError as je:
            return JsonResponse({'status': 'error', 'message': f'Invalid JSON: {je}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Unexpected error: {e}'})

    else:
        # GET method - render form
        form = BOQForm()
        project_id = request.GET.get('project_id')
        category_id = request.GET.get('category')
        suppliers = Suppliers.objects.all()

        context = {
            'form': form,
            'boq_cat_names': [],
            'project_id': project_id,
            'category': category_id,
            'project_first_name': '',
            'boq_cat_type': '',
            'suppliers': suppliers
        }

        try:
            if project_id:
                project = ProjectFirstLevelName.objects.get(pk=project_id)
                context['project_first_name'] = project.project_first_name

            if category_id:
                category = BoQCategory.objects.get(pk=category_id)
                context['boq_cat_type'] = category.boq_cat_type
                context['boq_cat_names'] = BoQCategory.objects.filter(
                    boq_cat_type=category.boq_cat_type
                ).values_list('boq_cat_name', flat=True)

        except (ProjectFirstLevelName.DoesNotExist, BoQCategory.DoesNotExist):
            pass

        return render(request, 'boq/boq_form.html', context)
        
        


# @login_required
# def labor_cost_create(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             boq_data = data.get('data', [])
#             category_id = data.get('category', '').strip()
#             project_id = data.get('project_id', '')
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not boq_data or not category_id or not project_id:
#                 raise ValueError("Missing required fields (data, category, or project_id).")

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             category_obj = get_object_or_404(BoQCategory, pk=category_id)
#             category_type = category_obj.boq_cat_type

#             for item in boq_data:
#                 qty = float(item.get('qty', 0))
#                 rate = float(item.get('rate', 0))
#                 amount = qty * rate

#                 category_name = item.get('cat_name', '').strip()
#                 supplier_id = item.get('sup_name')

#                 if not category_name:
#                     return JsonResponse({'status': 'error', 'message': "Category name is missing."})
#                 if not supplier_id:
#                     return JsonResponse({'status': 'error', 'message': "Supplier ID is missing."})

#                 try:
#                     supplier = Suppliers.objects.get(pk=supplier_id)
#                 except Suppliers.DoesNotExist:
#                     return JsonResponse({
#                         'status': 'error',
#                         'message': f"Supplier with ID {supplier_id} does not exist."
#                     })

#                 form = BOQForm({
#                     'project_name': project.id,
#                     'category_name': category_name,
#                     'supplier_name': supplier.id,
#                     'item_name': item.get('item_name', '').strip(),
#                     'unit': item.get('unit', '').strip(),
#                     'qty': qty,
#                     'rate': rate,
#                     'amount': amount,
#                     'remark': remark_text,
#                     'boq_date': timezone.now().date()
#                 })

#                 if form.is_valid():
#                     boq_instance = form.save(commit=False)
#                     # Manually set category_type on instance (bypass form validation choices)
#                     boq_instance.category_type = category_type
#                     boq_instance.save()
#                 else:
#                     return JsonResponse({
#                         'status': 'error',
#                         'message': 'Form data is invalid.',
#                         'errors': form.errors.as_json()
#                     })

#             return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

#         except ValueError as ve:
#             return JsonResponse({'status': 'error', 'message': f"Invalid data: {ve}"})
#         except json.JSONDecodeError as json_error:
#             return JsonResponse({'status': 'error', 'message': f"Invalid JSON format: {json_error}"})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"})

#     else:
#         # Handle GET request (render the form)
#         form = BOQForm()
#         project_id = request.GET.get('project_id')
#         category_id = request.GET.get('category')
#         suppliers = Suppliers.objects.all()

#         context = {
#             'form': form,
#             'boq_cat_names': [],
#             'project_id': project_id,
#             'category': category_id,
#             'suppliers': suppliers,
#             'project_first_name': '',
#             'boq_cat_type': ''
#         }

#         try:
#             if project_id:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 context['project_first_name'] = project.project_first_name

#             if category_id:
#                 category = BoQCategory.objects.get(pk=category_id)
#                 context['boq_cat_type'] = category.boq_cat_type
#                 context['boq_cat_names'] = BoQCategory.objects.filter(
#                     boq_cat_type=category.boq_cat_type
#                 ).values_list('boq_cat_name', flat=True)

#         except (ProjectFirstLevelName.DoesNotExist, BoQCategory.DoesNotExist):
#             pass

#         return render(request, 'boq/boq_labor_form.html', context)
        
      

# @login_required
# def labor_cost_create(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             boq_data = data.get('data', [])
#             category_id = data.get('category', '').strip()
#             project_id = data.get('project_id', '')
#             typeSelect_id = data.get('typeselects_id', '')
#             remark_text = data.get('remark') or request.GET.get('remark')

#             if not boq_data or not category_id or not project_id:
#                 raise ValueError("Missing required fields (data, category, or project_id).")

#             project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#             category_obj = get_object_or_404(BoQCategory, pk=category_id)
#             boq_type_obj = get_object_or_404(BoQType, pk=typeSelect_id)
#             category_type = category_obj.boq_cat_type

#             for item in boq_data:
#                 qty = Decimal(str(item.get('qty', '0')).strip() or '0')
#                 rate = Decimal(str(item.get('rate', '0')).strip() or '0')
#                 amount = qty * rate

#                 category_name = item.get('cat_name', '').strip()
#                 supplier_id = item.get('sup_name')

#                 if not category_name:
#                     return JsonResponse({'status': 'error', 'message': "Category name is missing."})
#                 if not supplier_id:
#                     return JsonResponse({'status': 'error', 'message': "Supplier ID is missing."})

#                 supplier = get_object_or_404(Suppliers, pk=supplier_id)

#                 form = BOQForm({
#                     'project_name': project.id,
#                     'category_name': category_name,
#                     'supplier_name': supplier.id,
#                     'item_name': item.get('item_name', '').strip(),
#                     'unit': item.get('unit', '').strip(),
#                     'qty': qty,
#                     'rate': rate,
#                     'amount': amount,
#                     'remark': remark_text,
#                     'boq_date': timezone.now().date(),
#                     # 'type_name': boq_type_obj.id  # optional if you include it in form
#                 })

#                 if form.is_valid():
#                     boq_instance = form.save(commit=False)
#                     boq_instance.category_type = category_type
#                     boq_instance.type_name = boq_type_obj  # ✅ Set the BoQType object
#                     boq_instance.save()
#                 else:
#                     return JsonResponse({
#                         'status': 'error',
#                         'message': 'Form data is invalid.',
#                         'errors': form.errors.as_json()
#                     })

#             return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

#         except ValueError as ve:
#             return JsonResponse({'status': 'error', 'message': f"Invalid data: {ve}"})
#         except json.JSONDecodeError as json_error:
#             return JsonResponse({'status': 'error', 'message': f"Invalid JSON format: {json_error}"})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"})

#     else:
#         # Handle GET request (render the form)
#         form = BOQForm()
#         project_id = request.GET.get('project_id')
#         category_id = request.GET.get('category')
#         typeselects_id = request.GET.get('typeSelect')
#         suppliers = Suppliers.objects.all()
#         boq_types = BoQType.objects.all() 

#         context = {
#             'form': form,
#             'boq_cat_names': [],
#             'project_id': project_id,
#             'category': category_id,
#             'suppliers': suppliers,
#             'typeselects_id': typeselects_id,
#             'boq_types': boq_types,  
#             'project_first_name': '',
#             'boq_cat_type': ''
#         }

#         try:
#             if project_id:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 context['project_first_name'] = project.project_first_name

#             if category_id:
#                 category = BoQCategory.objects.get(pk=category_id)
#                 context['boq_cat_type'] = category.boq_cat_type
#                 context['boq_cat_names'] = BoQCategory.objects.filter(
#                     boq_cat_type=category.boq_cat_type
#                 ).values_list('boq_cat_name', flat=True)

#             if typeselects_id:
#                     typeselects = BoQType.objects.get(pk=typeselects_id)
#                     context['boq_type_name'] = typeselects.boq_type_name    

#         except (ProjectFirstLevelName.DoesNotExist, BoQCategory.DoesNotExist):
#             pass

#         return render(request, 'boq/boq_labor_form.html', context)



import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

# Import your models and forms here
# from .models import ProjectFirstLevelName, BoQCategory, BoQType, Suppliers
# from .forms import BOQForm


@login_required
@transaction.atomic
def labor_cost_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            boq_data = data.get('data', [])
            category_id = str(data.get('category', '')).strip()
            project_id = data.get('project_id', '')
            typeSelect_id = data.get('typeselects_id', '')
            remark_text = data.get('remark') or request.GET.get('remark')

            if not boq_data or not category_id or not project_id:
                raise ValueError("Missing required fields (data, category, or project_id).")

            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            category_obj = get_object_or_404(BoQCategory, pk=category_id)
            boq_type_obj = get_object_or_404(BoQType, pk=typeSelect_id) if typeSelect_id else None
            category_type = category_obj.boq_cat_type

            for item in boq_data:
                qty = Decimal(str(item.get('qty', '0')).strip() or '0')
                rate = Decimal(str(item.get('rate', '0')).strip() or '0')
                amount = qty * rate

                category_name = str(item.get('cat_name', '')).strip()
                supplier_id = item.get('sup_name')
                item_id = item.get('item_name')

                if not category_name:
                    return JsonResponse({'status': 'error', 'message': "Category name is missing."})
                if not supplier_id:
                    return JsonResponse({'status': 'error', 'message': "Supplier ID is missing."})

                supplier = get_object_or_404(Suppliers, pk=supplier_id)
                itemName = get_object_or_404(HeadOfRequisition, pk=item_id)

                form = BOQForm({
                    'project_name': project.id,
                    'category_name': category_name,
                    'supplier_name': supplier.id,
                    'item_name': itemName.id,
                    'unit': str(item.get('unit', '')).strip(),
                    'qty': qty,
                    'rate': rate,
                    'amount': amount,
                    'remark': remark_text,
                    'boq_date': timezone.now().date(),
                })

                if form.is_valid():
                    boq_instance = form.save(commit=False)
                    boq_instance.category_type = category_type
                    if boq_type_obj:
                        boq_instance.type_name = boq_type_obj
                    boq_instance.save()
                else:
                    # Rolling back transaction automatically on error
                    transaction.set_rollback(True)
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Form data is invalid.',
                        'errors': form.errors.as_json()
                    })

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except ValueError as ve:
            return JsonResponse({'status': 'error', 'message': f"Invalid data: {ve}"})
        except json.JSONDecodeError as json_error:
            return JsonResponse({'status': 'error', 'message': f"Invalid JSON format: {json_error}"})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"})

    else:
        # Handle GET request
        form = BOQForm()
        project_id = request.GET.get('project_id')
        category_id = request.GET.get('category')
        typeselects_id = request.GET.get('typeSelect')
        
        suppliers = Suppliers.objects.all()
        boq_types = BoQType.objects.all()
        itemnames = HeadOfRequisition.objects.all()

        context = {
            'form': form,
            'boq_cat_names': [],
            'project_id': project_id,
            'category': category_id,
            'suppliers': suppliers,
            'item_names': itemnames,
            'typeselects_id': typeselects_id,
            'boq_types': boq_types,
            'project_first_name': '',
            'boq_cat_type': '',
            'boq_type_name': ''
        }

        try:
            if project_id:
                project = ProjectFirstLevelName.objects.get(pk=project_id)
                context['project_first_name'] = project.project_first_name

            if category_id:
                category = BoQCategory.objects.get(pk=category_id)
                context['boq_cat_type'] = category.boq_cat_type
                context['boq_cat_names'] = (
                    BoQCategory.objects.filter(boq_cat_type=category.boq_cat_type)
                    .order_by('boq_cat_name')  # Alphabetical (A-Z)
                    .values_list('boq_cat_name', flat=True)
                )

            if typeselects_id:
                typeselects = BoQType.objects.get(pk=typeselects_id)
                context['boq_type_name'] = typeselects.boq_type_name

        except (ProjectFirstLevelName.DoesNotExist, BoQCategory.DoesNotExist, BoQType.DoesNotExist):
            pass

        return render(request, 'boq/boq_labor_form.html', context)
        
        
        
        
# @login_required
# def boq_edit(request, pk):
#     boq = get_object_or_404(BOQ, pk=pk)
#     if request.method == 'POST':
#         form = BOQForm(request.POST, instance=boq)
#         if form.is_valid():
#             form.save()
#             return redirect('boq_list')
#     else:
#         form = BOQForm(instance=boq)

#     return render(request, 'boq/boq_edit.html', {'form': form, 'boq': boq})



@login_required
def boq_edit(request, pk):
    boq = get_object_or_404(BOQ, pk=pk)
    if request.method == 'POST':
        form = BOQForm(request.POST, instance=boq)
        if form.is_valid():
            updated_boq = form.save()
            return redirect('boq_list_details', project_id=updated_boq.project_name.id)
    else:
        form = BOQForm(instance=boq)

    return render(request, 'boq/boq_edit.html', {'form': form, 'boq': boq})
    
    

@login_required
def boq_delete(request, pk):
    boq = get_object_or_404(BOQ, pk=pk) 
    log_deleted_data(boq, request.user)
    boq.delete()
    messages.success(request, 'Deleted successfully!')
    return redirect('boq_list') 


# @login_required
# def project_boq_details(request):
#     project_id = request.GET.get('project_id')
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     boq_categories = BoQCategory.objects.all()

#     # Group BOQ items by category_type > category_name
#     boq_by_type_and_category = {}
#     for item in project.boq_set.all():
#         type_key = item.category_type
#         category_key = item.category_name

#         if type_key not in boq_by_type_and_category:
#             boq_by_type_and_category[type_key] = {}

#         if category_key not in boq_by_type_and_category[type_key]:
#             boq_by_type_and_category[type_key][category_key] = {
#                 'items': [],
#                 'total': Decimal('0.00')
#             }

#         boq_by_type_and_category[type_key][category_key]['items'].append(item)
#         boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

#     # Calculate the final total for all BOQ items
#     final_total = sum(item.amount or Decimal('0.00') for item in project.boq_set.all())

#     # Total by category type (Material, Labor)
#     total_by_category_type = (
#         BOQ.objects.filter(project_name=project)
#         .values('category_type')
#         .annotate(total_amount=Sum('amount'))
#         .order_by('category_type')
#     )

#     # Employee costs
#     employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
#     employees = []
#     for employee in employee_costs:
#         employees.append({
#             'employee_name': employee.employee_name,
#             'salary': employee.total_salary,
#             'first_month_salary': employee.first_month_salary,
#             'project_duration_months': employee.project_duration_months,
#         })

#     employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

#     # Safety equipment costs
#     safety_equipment_qs = SafetyEquipment.objects.filter(project_name=project.project_first_name)
#     safety_equipments = []
#     for item in safety_equipment_qs:
#         safety_equipments.append({
#             'item_name': item.item_name,
#             'item_cost': item.item_cost,
#             'quantity': item.quantity,
#             'total_cost': item.total_cost,
#         })

#     safety_equipment_total = safety_equipment_qs.aggregate(total=Sum('total_cost'))['total'] or 0

#     # Expense costs
#     expense_cost_tl = ExpenseCost.objects.filter(project_name=project.project_first_name)
#     expense_costs = []
#     for item in expense_cost_tl:
#         expense_costs.append({
#             'item_name': item.item_name,
#             'item_cost': item.item_cost,
#             'quantity': item.quantity,
#             'total_cost': item.total_cost,
#         })

#     expense_cost_total = expense_cost_tl.aggregate(total=Sum('total_cost'))['total'] or 0
#     grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total
#     if request.method == 'POST':
#         try:
#             percentage = Decimal(request.POST.get('percentage', 0))
#             percentage_value = (percentage / Decimal('100')) * grand_total
#             final_total_with_extra = grand_total + percentage_value

#             project.grand_total = grand_total
#             project.percentage = percentage
#             project.percentage_value = percentage_value
#             project.final_total_with_extra = final_total_with_extra
#             project.save()

#             messages.success(request, 'Project totals updated successfully.')
#         except Exception as e:
#             messages.error(request, f'Error updating totals: {str(e)}')

#         return redirect(f"{request.path}?project_id={project.id}")

#     return render(request, 'boq/project_boq_details.html', {
#         'project': project,
#         'boq_by_type_and_category': boq_by_type_and_category,
#         'total_by_category_type': total_by_category_type,
#         'employee_cost_total': employee_cost_total,
#         'safety_equipment_total': safety_equipment_total,
#         'expense_cost_total': expense_cost_total,
#         'grand_total': grand_total,
#         'employees': employees,
#         'safety_equipments': safety_equipments,
#         'expense_costs': expense_costs,
#         'boq_categories': boq_categories,
#     })



# def get_boq_data(project):
#     categories = project.boq_set.values_list('category', flat=True).distinct()

#     boq_by_category = {}
#     for category in categories:
#         boq_items = project.boq_set.filter(category_name=category)
#         category_total = sum(item.amount for item in boq_items)

#         boq_by_category[category] = {
#             'items': boq_items,
#             'total': category_total
#         }
#     final_total = sum(item.amount for item in project.boq_set.all())

#     return boq_by_category, final_total


@login_required
def revise_boq(request, pk, project_id):
    boq = get_object_or_404(BOQ, pk=pk)
    boq.update_item = "Revised"
    boq.save()
    return redirect(reverse('boq_list_details', kwargs={'project_id': project_id}))



# @login_required
# def project_boq_details(request):
#     project_id = request.GET.get('project_id')
#     status = request.GET.get('status')  # Get status from URL, e.g. ?status=Pending or ?status=Approved
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     boq_categories = BoQCategory.objects.all()

#     # Prepare base queryset of BOQ items for the project
#     boq_qs = project.boq_set.all()

#     # Filter based on status param
#     if status == 'Pending':
#         # Show only items with empty or blank status_item (not approved)
#         boq_qs = boq_qs.filter(status_item__in=['', None])
#     elif status == 'Approved':
#         # Show only approved items
#         boq_qs = boq_qs.filter(status_item='Approved')
#     # else: show all if no or unknown status provided

#     # Group BOQ items by category_type > category_name
#     boq_by_type_and_category = {}
#     for item in boq_qs:
#         type_key = item.category_type
#         category_key = item.category_name

#         if type_key not in boq_by_type_and_category:
#             boq_by_type_and_category[type_key] = {}

#         if category_key not in boq_by_type_and_category[type_key]:
#             boq_by_type_and_category[type_key][category_key] = {
#                 'items': [],
#                 'total': Decimal('0.00')
#             }

#         boq_by_type_and_category[type_key][category_key]['items'].append(item)
#         boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

#     # Calculate the final total for filtered BOQ items
#     final_total = sum(item.amount or Decimal('0.00') for item in boq_qs)

#     # Total by category type filtered by status
#     total_by_category_type = (
#         BOQ.objects.filter(project_name=project)
#         .filter(id__in=boq_qs.values_list('id', flat=True))  # ensure same filtering
#         .values('category_type')
#         .annotate(total_amount=Sum('amount'))
#         .order_by('category_type')
#     )

#     # (The rest of your existing code for employee_costs, safety_equipment, expense_costs...)

#     # (Same for totals below)

#     employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
#     employees = [{
#         'employee_name': e.employee_name,
#         'salary': e.total_salary,
#         'first_month_salary': e.first_month_salary,
#         'project_duration_months': e.project_duration_months,
#     } for e in employee_costs]

#     employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

#     safety_equipment_qs = SafetyEquipment.objects.filter(project_name=project.project_first_name)
#     safety_equipments = [{
#         'item_name': i.item_name,
#         'item_cost': i.item_cost,
#         'quantity': i.quantity,
#         'total_cost': i.total_cost,
#     } for i in safety_equipment_qs]

#     safety_equipment_total = safety_equipment_qs.aggregate(total=Sum('total_cost'))['total'] or 0

#     expense_cost_tl = ExpenseCost.objects.filter(project_name=project.project_first_name)
#     expense_costs = [{
#         'item_name': i.item_name,
#         'item_cost': i.item_cost,
#         'quantity': i.quantity,
#         'total_cost': i.total_cost,
#     } for i in expense_cost_tl]

#     expense_cost_total = expense_cost_tl.aggregate(total=Sum('total_cost'))['total'] or 0

#     grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

#     if request.method == 'POST':
#         try:
#             percentage_input = request.POST.get('percentage', '0') or '0'
#             try:
#                 percentage = Decimal(percentage_input)
#             except:
#                 percentage = Decimal('0')

#             percentage_value = (percentage / Decimal('100')) * grand_total
#             final_total_with_extra = grand_total + percentage_value

#             project.grand_total = grand_total
#             project.percentage = percentage
#             project.percentage_value = percentage_value
#             project.final_total_with_extra = final_total_with_extra
#             project.save()

#             BOQ.objects.filter(project_name=project).update(status_item='Approved')

#             messages.success(request, 'Project totals updated and BOQ marked as Approved.')
#         except Exception as e:
#             messages.error(request, f'Error updating totals: {str(e)}')
#         return redirect(f"{request.path}?project_id={project.id}&status=Approved")

#     return render(request, 'boq/project_boq_details.html', {
#         'project': project,
#         'boq_by_type_and_category': boq_by_type_and_category,
#         'total_by_category_type': total_by_category_type,
#         'employee_cost_total': employee_cost_total,
#         'safety_equipment_total': safety_equipment_total,
#         'expense_cost_total': expense_cost_total,
#         'grand_total': grand_total,
#         'employees': employees,
#         'safety_equipments': safety_equipments,
#         'expense_costs': expense_costs,
#         'boq_categories': boq_categories,
#         'status': status,  # pass current status to template for UI use
#     })

# def get_boq_data(project):
#     # You might want to also exclude approved here if used
#     categories = project.boq_set.exclude(status_item='Approved').values_list('category', flat=True).distinct()

#     boq_by_category = {}
#     for category in categories:
#         boq_items = project.boq_set.filter(category_name=category).exclude(status_item='Approved')
#         category_total = sum(item.amount for item in boq_items)

#         boq_by_category[category] = {
#             'items': boq_items,
#             'total': category_total
#         }
#     final_total = sum(item.amount for item in project.boq_set.exclude(status_item='Approved'))

#     return boq_by_category, final_total


@login_required
def project_boq_details(request):
    project_id = request.GET.get('project_id')
    status = request.GET.get('status')
    reqiDate = request.GET.get('reqiDate')

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boq_categories = BoQCategory.objects.all()

    boq_qs = project.boq_set.all()

    # Filter by status
    if status == 'Pending':
        boq_qs = boq_qs.filter(status_item__in=['', None])
    elif status == 'Approved':
        boq_qs = boq_qs.filter(status_item='Approved')

    # ✅ Filter by boq_date
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, '%Y-%m-%d').date()
            boq_qs = boq_qs.filter(boq_date=parsed_date)
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")

    # Organize by category_type and category_name
    boq_by_type_and_category = {}
    for item in boq_qs:
        type_key = item.category_type
        category_key = item.category_name

        if type_key not in boq_by_type_and_category:
            boq_by_type_and_category[type_key] = {}

        if category_key not in boq_by_type_and_category[type_key]:
            boq_by_type_and_category[type_key][category_key] = {
                'items': [],
                'total': Decimal('0.00')
            }

        boq_by_type_and_category[type_key][category_key]['items'].append(item)
        boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

    final_total = sum(item.amount or Decimal('0.00') for item in boq_qs)

    total_by_category_type = (
        BOQ.objects.filter(project_name=project)
        .filter(id__in=boq_qs.values_list('id', flat=True))
        .values('category_type')
        .annotate(total_amount=Sum('amount'))
        .order_by('category_type')
    )

    # Other project costs
    employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
    employees = [{
        'employee_name': e.employee_name,
        'salary': e.total_salary,
        'first_month_salary': e.first_month_salary,
        'project_duration_months': e.project_duration_months,
    } for e in employee_costs]
    employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

    safety_equipment_qs = SafetyEquipment.objects.filter(project_name=project.project_first_name)
    safety_equipments = [{
        'item_name': i.item_name,
        'item_cost': i.item_cost,
        'quantity': i.quantity,
        'total_cost': i.total_cost,
    } for i in safety_equipment_qs]
    safety_equipment_total = safety_equipment_qs.aggregate(total=Sum('total_cost'))['total'] or 0

    expense_cost_qs = ExpenseCost.objects.filter(project_name=project.project_first_name)
    expense_costs = [{
        'item_name': i.item_name,
        'item_cost': i.item_cost,
        'quantity': i.quantity,
        'total_cost': i.total_cost,
    } for i in expense_cost_qs]
    expense_cost_total = expense_cost_qs.aggregate(total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

    if request.method == 'POST':
        try:
            percentage_input = request.POST.get('percentage', '0') or '0'
            try:
                percentage = Decimal(percentage_input)
            except:
                percentage = Decimal('0')

            percentage_value = (percentage / Decimal('100')) * grand_total
            final_total_with_extra = grand_total + percentage_value

            project.grand_total = grand_total
            project.percentage = percentage
            project.percentage_value = percentage_value
            project.final_total_with_extra = final_total_with_extra
            project.save()

            BOQ.objects.filter(project_name=project).update(status_item='Approved')
            messages.success(request, 'Project totals updated and BOQ marked as Approved.')

        except Exception as e:
            messages.error(request, f'Error updating totals: {str(e)}')

        return redirect(f"{request.path}?project_id={project.id}&status=Approved")

    return render(request, 'boq/project_boq_details.html', {
        'project': project,
        'boq_by_type_and_category': boq_by_type_and_category,
        'total_by_category_type': total_by_category_type,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'expense_cost_total': expense_cost_total,
        'grand_total': grand_total,
        'employees': employees,
        'safety_equipments': safety_equipments,
        'expense_costs': expense_costs,
        'boq_categories': boq_categories,
        'status': status,
        'reqiDate': reqiDate,  # pass to template if needed
    })
    
    

# @login_required
# def project_boq_details_check(request):
#     # --- GET parameters ---
#     project_id = request.GET.get('project_id')
#     status = request.GET.get('status')
#     reqiDate = request.GET.get('reqiDate')
#     category_id = request.GET.get('category')
#     boq_type = request.GET.get('boq_type')

#     # --- Get project and categories ---
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#     boq_categories = BoQCategory.objects.all()

#     # --- Base queryset ---
#     boq_qs = project.boq_set.all()

#     # --- Filter by status ---
#     if status == 'Pending':
#         boq_qs = boq_qs.filter(status_item__in=['', None, 'Pending'])
#     elif status == 'Approved':
#         boq_qs = boq_qs.filter(status_item='Approved')

#     # --- Filter by BOQ date ---
#     if reqiDate:
#         try:
#             parsed_date = datetime.strptime(reqiDate, '%Y-%m-%d').date()
#             boq_qs = boq_qs.filter(boq_date=parsed_date)
#         except ValueError:
#             messages.error(request, "Invalid date format. Use YYYY-MM-DD.")

#     # --- Filter by category ---
#     if category_id:
#         try:
#             cat_obj = BoQCategory.objects.get(id=category_id)
#             boq_qs = boq_qs.filter(category_name=cat_obj.boq_cat_name)
#         except BoQCategory.DoesNotExist:
#             pass

#     # --- Filter by BOQ type ---
#     if boq_type:
#         boq_qs = boq_qs.filter(category_type__iexact=boq_type)

#     # --- Organize BOQs by type and category ---
#     boq_by_type_and_category = {}
#     total_by_category_type = {}

#     for item in boq_qs:
#         type_key = item.category_type or "Other"
#         category_key = item.category_name or "Uncategorized"

#         # Grouped data
#         if type_key not in boq_by_type_and_category:
#             boq_by_type_and_category[type_key] = {}
#         if category_key not in boq_by_type_and_category[type_key]:
#             boq_by_type_and_category[type_key][category_key] = {'items': [], 'total': Decimal('0.00')}
#         boq_by_type_and_category[type_key][category_key]['items'].append(item)
#         boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

#         # Totals by type
#         if type_key not in total_by_category_type:
#             total_by_category_type[type_key] = Decimal('0.00')
#         total_by_category_type[type_key] += item.amount or Decimal('0.00')

#     # Convert total_by_category_type to list of dicts for template
#     total_by_category_type_list = [
#         {'category_type': k, 'total_amount': v} for k, v in total_by_category_type.items()
#     ]

#     # --- Totals ---
#     final_total = sum(item.amount or Decimal('0.00') for item in boq_qs)
#     employee_cost_total = EmployeeCost.objects.filter(project_name=project.project_first_name).aggregate(
#         total=Sum('total_salary'))['total'] or 0
#     safety_equipment_total = SafetyEquipment.objects.filter(project_name=project.project_first_name).aggregate(
#         total=Sum('total_cost'))['total'] or 0
#     expense_cost_total = ExpenseCost.objects.filter(project_name=project.project_first_name).aggregate(
#         total=Sum('total_cost'))['total'] or 0

#     grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

#     employees = EmployeeCost.objects.filter(project_name=project.project_first_name)
#     safety_equipments = SafetyEquipment.objects.filter(project_name=project.project_first_name)
#     expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)

#     return render(request, 'boq/project_boq_details_check.html', {
#         'project': project,
#         'boq_by_type_and_category': boq_by_type_and_category,
#         'boq_categories': boq_categories,
#         'status': status,
#         'reqiDate': reqiDate,
#         'category': category_id,
#         'boq_type': boq_type,
#         'total_by_category_type': total_by_category_type_list,
#         'employee_cost_total': employee_cost_total,
#         'safety_equipment_total': safety_equipment_total,
#         'expense_cost_total': expense_cost_total,
#         'grand_total': grand_total,
#         'employees': employees,
#         'safety_equipments': safety_equipments,
#         'expense_costs': expense_costs,
#     })



@login_required
def project_boq_details_check(request):
    # --- GET parameters ---
    project_id = request.GET.get('project_id')
    status = (request.GET.get('status') or "").strip()
    reqiDate = (request.GET.get('reqiDate') or "").strip()
    boq_type = (request.GET.get('boq_type') or "").strip()  
    category = (request.GET.get('category') or "").strip() 
    category_name = (request.GET.get('category_name') or "").strip()  # 🔹 new

    # --- Get project ---
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boq_categories = (
        project.boq_set.exclude(type_name__isnull=True)
        .exclude(type_name__exact="")
        .values_list("type_name", flat=True)
        .distinct()
    )
    
    boq_category_names = (
        project.boq_set.exclude(category_name__isnull=True)
        .exclude(category_name__exact="")
        .values_list("category_name", flat=True)
        .distinct()
    ) 
    

    # --- Base queryset ---
    boq_qs = project.boq_set.all()

    # --- Filter by status ---
    if status == 'Pending':
        boq_qs = boq_qs.filter(status_item__in=['', None, 'Pending'])
    elif status == 'Approved':
        boq_qs = boq_qs.filter(status_item='Approved')

    # --- Filter by BOQ date ---
    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, '%Y-%m-%d').date()
            boq_qs = boq_qs.filter(boq_date=parsed_date)
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")

    # --- Filter by BOQ type (category_type from choices) ---
    if boq_type:
        boq_qs = boq_qs.filter(category_type__iexact=boq_type)

    # --- Filter by Category (type_name) ---
    if category:
        boq_qs = boq_qs.filter(type_name__icontains=category)

    if category_name:
        boq_qs = boq_qs.filter(category_name__icontains=category_name) 

    # --- Organize BOQs by type and category ---
    boq_by_type_and_category = {}
    total_by_category_type = {}

    for item in boq_qs:
        type_key = item.category_type or "Other"
        category_key = item.type_name or "Uncategorized"

        boq_by_type_and_category.setdefault(type_key, {})
        boq_by_type_and_category[type_key].setdefault(category_key, {'items': [], 'total': Decimal('0.00')})
        boq_by_type_and_category[type_key][category_key]['items'].append(item)
        boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

        total_by_category_type[type_key] = total_by_category_type.get(type_key, Decimal('0.00')) + (
            item.amount or Decimal('0.00')
        )

    total_by_category_type_list = [
        {'category_type': k, 'total_amount': v} for k, v in total_by_category_type.items()
    ]

    # --- Totals ---
    final_total = sum(item.amount or Decimal('0.00') for item in boq_qs)
    employee_cost_total = EmployeeCost.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_salary'))['total'] or 0
    safety_equipment_total = SafetyEquipment.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_cost'))['total'] or 0
    expense_cost_total = ExpenseCost.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

    employees = EmployeeCost.objects.filter(project_name=project.project_first_name)
    safety_equipments = SafetyEquipment.objects.filter(project_name=project.project_first_name)
    expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)

    return render(request, 'boq/project_boq_details_check.html', {
        'project': project,
        'boq_by_type_and_category': boq_by_type_and_category,
        'boq_categories': boq_categories,
        'boq_category_names': boq_category_names,
        'status': status,
        'reqiDate': reqiDate,
        'category': category,
        'category_name': category_name,
        'boq_type': boq_type,
        'total_by_category_type': total_by_category_type_list,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'expense_cost_total': expense_cost_total,
        'grand_total': grand_total,
        'employees': employees,
        'safety_equipments': safety_equipments,
        'expense_costs': expense_costs,
    })




@login_required
def project_boq_details_view(request):
    # --- GET parameters ---
    project_id = request.GET.get('project_id')
    status = (request.GET.get('status') or "").strip()
    reqiDate = (request.GET.get('reqiDate') or "").strip()
    boq_type = (request.GET.get('boq_type') or "").strip()  
    category = (request.GET.get('category') or "").strip() 
    category_name = (request.GET.get('category_name') or "").strip()

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    # --- Filters (same as your current view) ---
    boq_qs = project.boq_set.all()

    if status == 'Pending':
        boq_qs = boq_qs.filter(status_item__in=['', None, 'Pending'])
    elif status == 'Approved':
        boq_qs = boq_qs.filter(status_item='Approved')

    if reqiDate:
        try:
            parsed_date = datetime.strptime(reqiDate, '%Y-%m-%d').date()
            boq_qs = boq_qs.filter(boq_date=parsed_date)
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")

    if boq_type:
        boq_qs = boq_qs.filter(category_type__iexact=boq_type)
    if category:
        boq_qs = boq_qs.filter(type_name__icontains=category)
    if category_name:
        boq_qs = boq_qs.filter(category_name__icontains=category_name)

    # --- Organize BOQs ---
    boq_by_type_and_category = {}
    total_by_category_type = {}

    for item in boq_qs:
        type_key = item.category_type or "Other"
        category_key = item.type_name or "Uncategorized"

        boq_by_type_and_category.setdefault(type_key, {})
        boq_by_type_and_category[type_key].setdefault(category_key, {'items': [], 'total': Decimal('0.00')})
        boq_by_type_and_category[type_key][category_key]['items'].append(item)
        boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

        total_by_category_type[type_key] = total_by_category_type.get(type_key, Decimal('0.00')) + (
            item.amount or Decimal('0.00')
        )

    total_by_category_type_list = [
        {'category_type': k, 'total_amount': v} for k, v in total_by_category_type.items()
    ]

    # --- Totals ---
    final_total = sum(item.amount or Decimal('0.00') for item in boq_qs)
    employee_cost_total = EmployeeCost.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_salary'))['total'] or 0
    safety_equipment_total = SafetyEquipment.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_cost'))['total'] or 0
    expense_cost_total = ExpenseCost.objects.filter(project_name=project.project_first_name).aggregate(
        total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

    employees = EmployeeCost.objects.filter(project_name=project.project_first_name)
    safety_equipments = SafetyEquipment.objects.filter(project_name=project.project_first_name)
    expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)

    return render(request, 'boq/project_boq_details_view.html', {
        'project': project,
        'boq_by_type_and_category': boq_by_type_and_category,
        'total_by_category_type': total_by_category_type_list,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'expense_cost_total': expense_cost_total,
        'grand_total': grand_total,
        'employees': employees,
        'safety_equipments': safety_equipments,
        'expense_costs': expense_costs,
        'status': status,
        'reqiDate': reqiDate,
        'category': category,
        'category_name': category_name,
        'boq_type': boq_type,
    })



from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
# from weasyprint import HTML


def boq_pdf_view(request, project_id):
    return HttpResponse("PDF generation is currently disabled. Please enable WeasyPrint and uncomment the code in views.py to generate PDFs.")  

# @login_required
# def boq_pdf_view(request, project_id):
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#     boq_by_type_and_category = {}

#     # Group BOQ items by Category Type and Category Name
#     for item in project.boq_set.all():
#         type_key = item.category_type
#         category_key = item.category_name

#         if type_key not in boq_by_type_and_category:
#             boq_by_type_and_category[type_key] = {}

#         if category_key not in boq_by_type_and_category[type_key]:
#             boq_by_type_and_category[type_key][category_key] = {
#                 'items': [],
#                 'total': Decimal('0.00'),
#             }

#         boq_by_type_and_category[type_key][category_key]['items'].append(item)
#         boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

#     # Calculate Totals
#     final_total = sum(item.amount or Decimal('0.00') for item in project.boq_set.all())

#     total_by_category_type = (
#         BOQ.objects.filter(project_name=project)
#         .values('category_type')
#         .annotate(total_amount=Sum('amount'))
#         .order_by('category_type')
#     )

#     employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
#     employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or Decimal('0.00')

#     safety_equipment = SafetyEquipment.objects.filter(project_name=project.project_first_name)
#     safety_equipment_total = safety_equipment.aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

#     expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)
#     expense_cost_total = expense_costs.aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

#     grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

#     context = {
#         'project': project,
#         'boq_by_type_and_category': boq_by_type_and_category,
#         'grand_total': grand_total,
#         'total_by_category_type': total_by_category_type,
#         'employee_cost_total': employee_cost_total,
#         'safety_equipment_total': safety_equipment_total,
#         'employee_costs': employee_costs,
#         'safety_equipment': safety_equipment,
#         'expense_costs': expense_costs,
#         'expense_cost_total': expense_cost_total,
#     }

#     # Render Template to HTML String
#     html_string = render_to_string('boq/pdf_template.html', context)

#     # Generate PDF via WeasyPrint
#     pdf_bytes = HTML(
#         string=html_string,
#         base_url=request.build_absolute_uri('/')
#     ).write_pdf()

#     response = HttpResponse(pdf_bytes, content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; filename="boq_details.pdf"'
#     return response
    
    
    

# @login_required
# def boq_pdf_view(request, project_id):
#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#     boq_by_type_and_category = {}
#     for item in project.boq_set.all():
#         type_key = item.category_type
#         category_key = item.category_name

#         if type_key not in boq_by_type_and_category:
#             boq_by_type_and_category[type_key] = {}

#         if category_key not in boq_by_type_and_category[type_key]:
#             boq_by_type_and_category[type_key][category_key] = {
#                 'items': [],
#                 'total': Decimal('0.00')
#             }

#         boq_by_type_and_category[type_key][category_key]['items'].append(item)
#         boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

#     final_total = sum(item.amount or Decimal('0.00') for item in project.boq_set.all())

#     total_by_category_type = (
#         BOQ.objects.filter(project_name=project)
#         .values('category_type')
#         .annotate(total_amount=Sum('amount'))
#         .order_by('category_type')
#     )

#     employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
#     employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

#     safety_equipment = SafetyEquipment.objects.filter(project_name=project.project_first_name)
#     safety_equipment_total = safety_equipment.aggregate(total=Sum('total_cost'))['total'] or 0

#     expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)
#     expense_cost_total = expense_costs.aggregate(total=Sum('total_cost'))['total'] or 0

#     grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

#     context = {
#         'project': project,
#         'boq_by_type_and_category': boq_by_type_and_category,
#         'grand_total': grand_total,
#         'total_by_category_type': total_by_category_type,
#         'employee_cost_total': employee_cost_total,
#         'safety_equipment_total': safety_equipment_total,
#         'employee_costs': employee_costs,
#         'safety_equipment': safety_equipment,
#         'expense_costs': expense_costs,
#         'expense_cost_total': expense_cost_total,
#     }

#     # Render PDF
#     template_path = 'boq/pdf_template.html'
#     template = get_template(template_path)
#     html = template.render(context)

#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

#     if not pdf.err:
#         response = HttpResponse(result.getvalue(), content_type='application/pdf')
#         response['Content-Disposition'] = 'inline; filename="boq_details.pdf"'
#         return response
#     else:
#         return HttpResponse('PDF generation failed')




@login_required
def eng_boq_pdf_view(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boq_by_type_and_category = {}
    for item in project.boq_set.all():
        type_key = item.category_type
        category_key = item.category_name

        if type_key not in boq_by_type_and_category:
            boq_by_type_and_category[type_key] = {}

        if category_key not in boq_by_type_and_category[type_key]:
            boq_by_type_and_category[type_key][category_key] = {
                'items': [],
                'total': Decimal('0.00')
            }

        boq_by_type_and_category[type_key][category_key]['items'].append(item)
        boq_by_type_and_category[type_key][category_key]['total'] += item.amount or Decimal('0.00')

    final_total = sum(item.amount or Decimal('0.00') for item in project.boq_set.all())

    total_by_category_type = (
        BOQ.objects.filter(project_name=project)
        .values('category_type')
        .annotate(total_amount=Sum('amount'))
        .order_by('category_type')
    )

    employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
    employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

    safety_equipment = SafetyEquipment.objects.filter(project_name=project.project_first_name)
    safety_equipment_total = safety_equipment.aggregate(total=Sum('total_cost'))['total'] or 0

    expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)
    expense_cost_total = expense_costs.aggregate(total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

    context = {
        'project': project,
        'boq_by_type_and_category': boq_by_type_and_category,
        'grand_total': grand_total,
        'total_by_category_type': total_by_category_type,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'employee_costs': employee_costs,
        'safety_equipment': safety_equipment,
        'expense_costs': expense_costs,
        'expense_cost_total': expense_cost_total,
    }

    # Render PDF
    template_path = 'boq/pdf_template_eng.html'
    template = get_template(template_path)
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="boq_details.pdf"'
        return response
    else:
        return HttpResponse('PDF generation failed')
        
        
        
# @login_required
# def boq_category_pdf(request):
#     project_id = request.GET.get('project_id')
#     category_name = request.GET.get('category_name')

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#     boq_items = BOQ.objects.filter(project_name=project, category_name=category_name)

#     total_amount = sum(item.amount for item in boq_items)

#     template = get_template('boq/boq_category_pdf.html')
#     html = template.render({
#         'project': project,
#         'category_name': category_name,
#         'boq_items': boq_items,
#         'total_amount': total_amount,
#     })

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'filename=BOQ_{category_name}.pdf'

#     pisa_status = pisa.CreatePDF(html, dest=response)
#     if pisa_status.err:
#         return HttpResponse('PDF generation error')
#     return response


from num2words import num2words
from django.utils.timezone import now

@login_required
def boq_category_pdf(request):
    project_id = request.GET.get('project_id')
    category_name = request.GET.get('category_name')

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boq_items = BOQ.objects.filter(project_name=project, category_name=category_name)

    total_amount = sum(item.amount for item in boq_items)

    # ✅ Convert to words in Bangladeshi Taka format
    amount_in_words = num2words(total_amount, to='currency', lang='en_IN')  # Indian format
    amount_in_words = amount_in_words.replace("euro", "Taka").replace("cents", "paisa")

    template = get_template('boq/boq_category_pdf.html')
    html = template.render({
        'project': project,
        'category_name': category_name,
        'boq_items': boq_items,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words,
        'year': now().year,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=BOQ_{category_name}.pdf'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation error')
    return response



## Project Location --
@login_required
def project_location_list(request):
    locations = ProjectLocation.objects.all().order_by('-create_date')
    return render(request, 'projectLocation/project_location_list.html', {'locations': locations})

@login_required
def project_location_add(request):
    if request.method == 'POST':
        form = ProjectLocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_location_list')
    else:
        form = ProjectLocationForm()
    return render(request, 'projectLocation/project_location_add.html', {'form': form})

@login_required
def project_location_edit(request, pk):
    location = get_object_or_404(ProjectLocation, pk=pk)
    if request.method == 'POST':
        form = ProjectLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('project_location_list')
    else:
        form = ProjectLocationForm(instance=location)
    return render(request, 'projectLocation/project_location_edit.html', {'form': form})

@login_required
def project_location_delete(request, pk):
    location = get_object_or_404(ProjectLocation, pk=pk)
    if request.method == 'POST':
        log_deleted_data(location, request.user)
        location.delete()
        return redirect('project_location_list')
    return render(request, 'projectLocation/project_location_delete.html', {'location': location})


# View to list all project first level
@login_required
def first_level_list(request):
    projects = ProjectFirstLevelName.objects.all()
    return render(request, 'firstlevel/first_level_list.html', {'projects': projects})

# @login_required
# def first_level_add(request):
#     if request.method == 'POST':
#         start_month = request.POST.get('start_month')  # '4'
#         start_year = request.POST.get('start_year')    # '2025'

#         request.POST = request.POST.copy()

#         if start_month and start_year:
#             request.POST['project_start_month'] = int(start_month)

#         form = ProjectFirstLevelNameForm(request.POST, request.FILES)

#         if form.is_valid():
#             project = form.save(commit=False)

#             try:
#                 year = int(start_year)
#                 month = int(start_month)
#                 start_date = datetime(year, month, 1).date()
#                 project.project_start_date = start_date
#                 print("Project duration:", project.project_duration)
#                 if project.project_duration:
#                     end_raw = start_date + relativedelta(months=project.project_duration)
#                     last_day = calendar.monthrange(end_raw.year, end_raw.month)[1]
#                     end_date = datetime(end_raw.year, end_raw.month, last_day).date()
#                     project.project_end_date = end_date
#                     print("Calculated end date:", end_date)
#                 else:
#                     print("[WARNING] Project duration is missing or zero.")

#             except Exception as e:
#                 print(f"[ERROR] Date calculation failed: {e}")
#                 messages.error(request, "Could not calculate start/end dates.")

#             project.save()

#             messages.success(request, 'First Level (Project Name) Added successfully!')
#             return redirect('first_level_list')
#         else:
#             print("Form errors:", form.errors)
#             messages.error(request, 'There was an error adding the First Level. Please try again.')
#     else:
#         form = ProjectFirstLevelNameForm()

#     return render(request, 'firstlevel/first_level_add.html', {'form': form})

import calendar

from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect

from .models import (
    ProjectFirstLevelName,
    ProjectDocument,
    ProjectSchedule
)

from .forms import (
    ProjectFirstLevelNameForm,
    ProjectScheduleForm
)


from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import (
    ProjectFirstLevelNameForm,
    ProjectScheduleForm,
)

from .models import (
    ProjectDocument,
    ProjectScheduleItem,
)


@login_required
def first_level_add(request):

    if request.method == 'POST':

        # Project Form
        form = ProjectFirstLevelNameForm(
            request.POST,
            request.FILES
        )

        # Existing Schedule Form
        schedule_form = ProjectScheduleForm(
            request.POST
        )

        # Dynamic Schedule Data
        subject_names = request.POST.getlist(
            'subject_name[]'
        )

        start_dates = request.POST.getlist(
            'start_date[]'
        )

        end_dates = request.POST.getlist(
            'end_date[]'
        )

        schedule_types = request.POST.getlist(
            'schedule_type[]'
        )

        # Validate Main Forms
        if form.is_valid() and schedule_form.is_valid():

            try:

                with transaction.atomic():

                    # ==================================
                    # 1. Save Project
                    # ==================================

                    project = form.save(commit=False)

                    # Default Project Duration
                    if not project.project_duration:
                        project.project_duration = 12

                    # Date Calculation Removed
                    project.project_start_date = None
                    project.project_end_date = None

                    project.save()

                    # ==================================
                    # 2. Multiple Documents Upload
                    # ==================================

                    document_fields = {
                        'agreement_documents': 'agreement',
                        'test_documents': 'test',
                        'drawing_documents': 'drawing',
                        'certification_documents': 'certification',
                        'approval_documents': 'approval',
                    }

                    for field_name, document_type in document_fields.items():

                        uploaded_files = request.FILES.getlist(
                            field_name
                        )

                        for uploaded_file in uploaded_files:

                            ProjectDocument.objects.create(
                                project=project,
                                document_type=document_type,
                                document=uploaded_file
                            )

                    # ==================================
                    # 3. Existing Schedule Save
                    # ==================================

                    schedule = schedule_form.save(
                        commit=False
                    )

                    schedule.project = project
                    schedule.save()

                    # ==================================
                    # 4. Dynamic Schedule Items
                    # ==================================

                    total_rows = max(
                        len(subject_names),
                        len(start_dates),
                        len(end_dates),
                        len(schedule_types)
                    )

                    for index in range(total_rows):

                        subject = (
                            subject_names[index].strip()
                            if index < len(subject_names)
                            else ''
                        )

                        start_date = (
                            start_dates[index]
                            if index < len(start_dates)
                            else ''
                        )

                        end_date = (
                            end_dates[index]
                            if index < len(end_dates)
                            else ''
                        )

                        schedule_type = (
                            schedule_types[index]
                            if index < len(schedule_types)
                            else ''
                        )

                        # Skip completely empty rows
                        if not any([
                            subject,
                            start_date,
                            end_date,
                            schedule_type
                        ]):
                            continue

                        # Validate incomplete row
                        if not all([
                            subject,
                            start_date,
                            end_date,
                            schedule_type
                        ]):

                            raise ValueError(
                                f"Schedule row {index + 1} "
                                f"is incomplete."
                            )

                        # Validate Date Format
                        parsed_start_date = datetime.strptime(
                            start_date,
                            '%Y-%m-%d'
                        ).date()

                        parsed_end_date = datetime.strptime(
                            end_date,
                            '%Y-%m-%d'
                        ).date()

                        # Validate Date Order
                        if parsed_end_date < parsed_start_date:

                            raise ValueError(
                                f"End date cannot be earlier "
                                f"than start date in row "
                                f"{index + 1}."
                            )

                        # Validate Schedule Type
                        valid_types = [
                            'sub_structure',
                            'super_structure',
                            'finishing',
                        ]

                        if schedule_type not in valid_types:

                            raise ValueError(
                                f"Invalid schedule option "
                                f"in row {index + 1}."
                            )

                        # Save Dynamic Schedule Row
                        ProjectScheduleItem.objects.create(
                            project=project,
                            subject_name=subject,
                            start_date=parsed_start_date,
                            end_date=parsed_end_date,
                            schedule_type=schedule_type
                        )

                    # ==================================
                    # 5. Success Message
                    # ==================================

                    messages.success(
                        request,
                        'Project added successfully!'
                    )

                    return redirect(
                        'first_level_list'
                    )

            except ValueError as e:

                print(
                    "Schedule Validation Error:",
                    e
                )

                messages.error(
                    request,
                    str(e)
                )

            except Exception as e:

                print(
                    "Project Save Error:",
                    e
                )

                messages.error(
                    request,
                    'Something went wrong. Please try again.'
                )

        else:

            print(
                "Project Form Errors:",
                form.errors
            )

            print(
                "Schedule Form Errors:",
                schedule_form.errors
            )

            messages.error(
                request,
                'Please correct the errors below.'
            )

    else:

        form = ProjectFirstLevelNameForm()

        schedule_form = ProjectScheduleForm()

    return render(
        request,
        'firstlevel/first_level_add.html',
        {
            'form': form,
            'schedule_form': schedule_form,
        }
    )

def first_level_details(request, pk):

    project = get_object_or_404(
        ProjectFirstLevelName.objects.select_related(
            'location',
            'project_owner'
        ),
        pk=pk
    )

    return render(
        request,
        'firstlevel/first_level_details.html',
        {
            'project': project,
        }
    )

@login_required
def first_level_edit(request, pk):
    project = get_object_or_404(ProjectFirstLevelName, pk=pk)

    months = {
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September", "10": "October", "11": "November", "12": "December"
    }
    years = [str(y) for y in range(2025, 2041)]

    selected_month = ""
    selected_year = ""

    if request.method == 'POST':
        form = ProjectFirstLevelNameForm(request.POST, instance=project)

        # Get selected dropdown values for the month and year
        month_num = request.POST.get('start_month')
        year = request.POST.get('start_year')

        if form.is_valid():
            project = form.save(commit=False)

            if month_num and year:
                month_name = months.get(month_num)
                project.project_start_month = f"{month_name} {year}"

                # Calculate project_start_date
                start_date = date(int(year), int(month_num), 1)
                project.project_start_date = start_date

                # Calculate project_end_date
                duration = project.project_duration or 1
                end_month = start_date.month - 1 + duration
                end_year = start_date.year + end_month // 12
                end_month = end_month % 12 + 1
                end_day = monthrange(end_year, end_month)[1]
                end_date = date(end_year, end_month, end_day)

                project.project_end_date = end_date

            project.save()
            return redirect('first_level_list')  # Redirect after success
        else:
            # Debugging: Check if form is valid
            print("Form errors:", form.errors)
            selected_month = month_num
            selected_year = year
    else:
        form = ProjectFirstLevelNameForm(instance=project)
        try:
            month_name, year = project.project_start_month.split()
            selected_month = next((k for k, v in months.items() if v == month_name), "4")
            selected_year = year
        except:
            selected_month = "4"
            selected_year = "2025"

    return render(request, 'firstlevel/first_level_edit.html', {
        'form': form,
        'project': project,
        'months': months,
        'years': years,
        'selected_month': selected_month,
        'selected_year': selected_year
    })


@login_required
def first_level_delete(request, pk):
    project = get_object_or_404(ProjectFirstLevelName, pk=pk)
    
    if request.method == 'POST':
        log_deleted_data(project, request.user)
        project.delete()
        return redirect('first_level_list')
    
    return render(request, 'firstlevel/first_level_delete.html', {'project': project})

@login_required
def project_flevel_details(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    per_floor_price = 0
    per_unit_price = 0

    if project.final_total_with_extra:
        if project.number_of_floors:
            per_floor_price = project.final_total_with_extra / project.number_of_floors
        if project.number_of_units:
            per_unit_price = project.final_total_with_extra / project.number_of_units

    context = {
        'project': project,
        'per_floor_price': per_floor_price,
        'per_unit_price': per_unit_price,
    }

    return render(request, 'firstlevel/project_flevel_details.html', context)

def project_intro(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName.objects.select_related(
            'location',
            'project_owner'
        ),
        pk=pk
    )

    return render(
        request,
        'firstlevel/project_intro.html',
        {
            'project': project,
        }
    )



# from calendar import month_abbr

# def project_schedule(request, pk):
#     project = get_object_or_404(ProjectFirstLevelName, pk=pk)

#     schedule_items = ProjectScheduleItem.objects.filter(
#         project=project
#     ).order_by('start_date')

#     try:
#         schedule = ProjectSchedule.objects.get(project=project)
#     except ProjectSchedule.DoesNotExist:
#         schedule = None

#     gantt_months = []
#     gantt_items = []

#     if schedule_items:
#         min_start = min(item.start_date for item in schedule_items)
#         max_end = max(item.end_date for item in schedule_items)

#         total_months = (max_end.year - min_start.year) * 12 + (max_end.month - min_start.month) + 1

#         current_year = None
#         for i in range(total_months):
#             month_num = min_start.month + i
#             year_num = min_start.year + (month_num - 1) // 12
#             month_num = ((month_num - 1) % 12) + 1
#             gantt_months.append({
#                 'label': month_abbr[month_num],
#                 'year': year_num,
#                 'show_year': year_num != current_year,
#             })
#             current_year = year_num

#         for item in schedule_items:
#             start_offset = (item.start_date.year - min_start.year) * 12 + (item.start_date.month - min_start.month)
#             span = (item.end_date.year - item.start_date.year) * 12 + (item.end_date.month - item.start_date.month) + 1
#             gantt_items.append({
#                 'obj': item,
#                 'span': span,
#                 'col_start': start_offset + 2,
#                 'col_end': start_offset + span + 2,
#             })

#     return render(
#         request,
#         'firstlevel/project_schedule.html',
#         {
#             'project': project,
#             'schedule': schedule,
#             'schedule_items': schedule_items,
#             'gantt_months': gantt_months,
#             'gantt_items': gantt_items,
#             'gantt_total_months': len(gantt_months),
#         }
#     )

# from calendar import month_abbr
# from datetime import date

# def project_schedule(request, pk):
#     project = get_object_or_404(ProjectFirstLevelName, pk=pk)

#     schedule_items = ProjectScheduleItem.objects.filter(
#         project=project
#     ).order_by('start_date')

#     try:
#         schedule = ProjectSchedule.objects.get(project=project)
#     except ProjectSchedule.DoesNotExist:
#         schedule = None

#     gantt_months = []
#     gantt_items = []

#     if schedule_items:
#         today = date.today()

#         all_dates = []
#         for item in schedule_items:
#             all_dates.append(item.start_date)
#             all_dates.append(item.end_date)
#             if item.actual_start_date:
#                 all_dates.append(item.actual_start_date)
#             if item.actual_end_date:
#                 all_dates.append(item.actual_end_date)
#             elif item.actual_start_date:
#                 all_dates.append(today)  # still ongoing, extend range to current month

#         min_start = min(all_dates)
#         max_end = max(all_dates)

#         total_months = (max_end.year - min_start.year) * 12 + (max_end.month - min_start.month) + 1

#         def month_offset(d):
#             return (d.year - min_start.year) * 12 + (d.month - min_start.month)

#         current_year = None
#         for i in range(total_months):
#             month_num = min_start.month + i
#             year_num = min_start.year + (month_num - 1) // 12
#             month_num = ((month_num - 1) % 12) + 1
#             gantt_months.append({
#                 'label': month_abbr[month_num],
#                 'year': year_num,
#                 'show_year': year_num != current_year,
#                 'is_current': (year_num == today.year and month_num == today.month),
#             })
#             current_year = year_num

#         for item in schedule_items:
#             plan_offset = month_offset(item.start_date)
#             plan_span = (item.end_date.year - item.start_date.year) * 12 + (item.end_date.month - item.start_date.month) + 1

#             actual = None
#             if item.actual_start_date:
#                 is_ongoing = item.actual_end_date is None
#                 actual_end = item.actual_end_date if item.actual_end_date else today
#                 actual_offset = month_offset(item.actual_start_date)
#                 actual_span = (actual_end.year - item.actual_start_date.year) * 12 + (actual_end.month - item.actual_start_date.month) + 1
#                 overdue = actual_end > item.end_date

#                 actual = {
#                     'col_start': actual_offset + 2,
#                     'col_end': actual_offset + actual_span + 2,
#                     'span': actual_span,
#                     'is_ongoing': is_ongoing,
#                     'overdue': overdue,
#                 }

#             gantt_items.append({
#                 'obj': item,
#                 'span': plan_span,
#                 'col_start': plan_offset + 2,
#                 'col_end': plan_offset + plan_span + 2,
#                 'actual': actual,
#             })

#     return render(
#         request,
#         'firstlevel/project_schedule.html',
#         {
#             'project': project,
#             'schedule': schedule,
#             'schedule_items': schedule_items,
#             'gantt_months': gantt_months,
#             'gantt_items': gantt_items,
#             'gantt_total_months': len(gantt_months),
#         }
#     )


from calendar import month_abbr
from datetime import date

from django.shortcuts import get_object_or_404, render

from .models import (
    ProjectFirstLevelName,
    ProjectSchedule,
    ProjectScheduleItem,
)


def project_schedule(request, pk):

    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    schedule_items = ProjectScheduleItem.objects.filter(
        project=project
    ).order_by('start_date')

    try:
        schedule = ProjectSchedule.objects.get(
            project=project
        )
    except ProjectSchedule.DoesNotExist:
        schedule = None


    # ==========================================================
    # EXISTING GANTT CALCULATION
    # ==========================================================

    gantt_months = []
    gantt_items = []

    today = date.today()

    if schedule_items:

        all_dates = []

        for item in schedule_items:

            all_dates.append(item.start_date)
            all_dates.append(item.end_date)

            if item.actual_start_date:
                all_dates.append(item.actual_start_date)

            if item.actual_end_date:
                all_dates.append(item.actual_end_date)

            elif item.actual_start_date:
                all_dates.append(today)

        min_start = min(all_dates)
        max_end = max(all_dates)

        total_months = (
            (max_end.year - min_start.year) * 12
            + (max_end.month - min_start.month)
            + 1
        )

        def month_offset(d):
            return (
                (d.year - min_start.year) * 12
                + (d.month - min_start.month)
            )

        current_year = None

        for i in range(total_months):

            month_num = min_start.month + i

            year_num = (
                min_start.year
                + (month_num - 1) // 12
            )

            month_num = (
                (month_num - 1) % 12
            ) + 1

            gantt_months.append({
                'label': month_abbr[month_num],
                'year': year_num,

                'show_year': (
                    year_num != current_year
                ),

                'is_current': (
                    year_num == today.year
                    and month_num == today.month
                ),
            })

            current_year = year_num


        for item in schedule_items:

            plan_offset = month_offset(
                item.start_date
            )

            plan_span = (
                (item.end_date.year - item.start_date.year) * 12
                + (
                    item.end_date.month
                    - item.start_date.month
                )
                + 1
            )

            actual = None

            if item.actual_start_date:

                is_ongoing = (
                    item.actual_end_date is None
                )

                actual_end = (
                    item.actual_end_date
                    if item.actual_end_date
                    else today
                )

                actual_offset = month_offset(
                    item.actual_start_date
                )

                actual_span = (
                    (actual_end.year - item.actual_start_date.year) * 12
                    + (
                        actual_end.month
                        - item.actual_start_date.month
                    )
                    + 1
                )

                overdue = (
                    actual_end > item.end_date
                )

                actual = {
                    'col_start': actual_offset + 2,
                    'col_end': (
                        actual_offset
                        + actual_span
                        + 2
                    ),
                    'span': actual_span,
                    'is_ongoing': is_ongoing,
                    'overdue': overdue,
                }

            gantt_items.append({
                'obj': item,
                'span': plan_span,
                'col_start': plan_offset + 2,
                'col_end': (
                    plan_offset
                    + plan_span
                    + 2
                ),
                'actual': actual,
            })


    # ==========================================================
    # PART-WISE AUTOMATIC CALCULATION
    # ==========================================================

    def calculate_part(schedule_type):

        items = schedule_items.filter(
            schedule_type=schedule_type
        )

        if not items.exists():

            return {
                'scheduled_days': 0,
                'scheduled_months': 0,

                'worked_days': 0,
                'worked_months': 0,

                'remaining_days': 0,
                'remaining_months': 0,

                'progress': 0,

                'start_date': None,
                'end_date': None,
            }


        # ------------------------------------------------------
        # Scheduled Start / End
        # ------------------------------------------------------

        scheduled_start = min(
            item.start_date
            for item in items
        )

        scheduled_end = max(
            item.end_date
            for item in items
        )


        # ------------------------------------------------------
        # TOTAL SCHEDULED
        # ------------------------------------------------------

        scheduled_days = (
            scheduled_end - scheduled_start
        ).days + 1

        scheduled_months = (
            (scheduled_end.year - scheduled_start.year) * 12
            + (
                scheduled_end.month
                - scheduled_start.month
            )
            + 1
        )


        # ------------------------------------------------------
        # ACTUAL START
        # ------------------------------------------------------

        actual_started = [
            item.actual_start_date
            for item in items
            if item.actual_start_date
        ]


        if actual_started:

            actual_start = min(
                actual_started
            )

            # কাজ শুরু হয়েছে
            if actual_start <= today:

                worked_days = (
                    today - actual_start
                ).days + 1

                worked_months = (
                    (today.year - actual_start.year) * 12
                    + (
                        today.month
                        - actual_start.month
                    )
                    + 1
                )

            else:

                worked_days = 0
                worked_months = 0

        else:

            worked_days = 0
            worked_months = 0


        # ------------------------------------------------------
        # REMAINING
        # ------------------------------------------------------

        if today < scheduled_end:

            remaining_days = (
                scheduled_end - today
            ).days

            remaining_months = (
                (scheduled_end.year - today.year) * 12
                + (
                    scheduled_end.month
                    - today.month
                )
            )

        else:

            remaining_days = 0
            remaining_months = 0


        # ------------------------------------------------------
        # PROGRESS
        # ------------------------------------------------------

        if scheduled_days > 0:

            progress = (
                worked_days
                / scheduled_days
            ) * 100

            progress = min(
                max(progress, 0),
                100
            )

        else:

            progress = 0


        return {
            'scheduled_days': scheduled_days,
            'scheduled_months': scheduled_months,

            'worked_days': worked_days,
            'worked_months': worked_months,

            'remaining_days': remaining_days,
            'remaining_months': remaining_months,

            'progress': round(progress, 1),

            'start_date': scheduled_start,
            'end_date': scheduled_end,
        }


    # ==========================================================
    # 3 MAIN PARTS
    # ==========================================================

    sub_structure = calculate_part(
        'sub_structure'
    )

    super_structure = calculate_part(
        'super_structure'
    )

    finishing = calculate_part(
        'finishing'
    )


    # ==========================================================
    # OVERALL TOTAL (OPTIONAL)
    # ==========================================================

    overall = calculate_part_all = None

    if schedule_items.exists():

        overall_start = min(
            item.start_date
            for item in schedule_items
        )

        overall_end = max(
            item.end_date
            for item in schedule_items
        )

        overall_scheduled_days = (
            overall_end - overall_start
        ).days + 1

        overall_scheduled_months = (
            (overall_end.year - overall_start.year) * 12
            + (
                overall_end.month
                - overall_start.month
            )
            + 1
        )

        if today < overall_end:

            overall_remaining_days = (
                overall_end - today
            ).days

            overall_remaining_months = (
                (overall_end.year - today.year) * 12
                + (
                    overall_end.month
                    - today.month
                )
            )

        else:

            overall_remaining_days = 0
            overall_remaining_months = 0

        overall = {
            'scheduled_days': overall_scheduled_days,
            'scheduled_months': overall_scheduled_months,

            'remaining_days': overall_remaining_days,
            'remaining_months': overall_remaining_months,

            'start_date': overall_start,
            'end_date': overall_end,
        }


    # ==========================================================
    # RETURN
    # ==========================================================

    return render(
        request,
        'firstlevel/project_schedule.html',
        {
            'project': project,

            'schedule': schedule,

            'schedule_items': schedule_items,

            # Gantt
            'gantt_months': gantt_months,
            'gantt_items': gantt_items,
            'gantt_total_months': len(
                gantt_months
            ),

            # 3 Parts
            'sub_structure': sub_structure,
            'super_structure': super_structure,
            'finishing': finishing,

            # Optional overall
            'overall': overall,

            'today': today,
        }
    )

from .forms import ProjectScheduleItemForm

@login_required
def project_schedule_crud(request, pk):

    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    # =========================
    # ADD
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'add':

        form = ProjectScheduleItemForm(request.POST)

        if form.is_valid():

            schedule_item = form.save(commit=False)
            schedule_item.project = project
            schedule_item.save()

            messages.success(
                request,
                'Schedule item added successfully.'
            )

            return redirect(
                'project_schedule_crud',
                pk=project.pk
            )

    # =========================
    # UPDATE
    # =========================
    elif request.method == 'POST' and request.POST.get('action') == 'update':

        item_id = request.POST.get('item_id')

        schedule_item = get_object_or_404(
            ProjectScheduleItem,
            pk=item_id,
            project=project
        )

        form = ProjectScheduleItemForm(
            request.POST,
            instance=schedule_item
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Schedule item updated successfully.'
            )

            return redirect(
                'project_schedule_crud',
                pk=project.pk
            )

    # =========================
    # DELETE
    # =========================
    elif request.method == 'POST' and request.POST.get('action') == 'delete':

        item_id = request.POST.get('item_id')

        schedule_item = get_object_or_404(
            ProjectScheduleItem,
            pk=item_id,
            project=project
        )

        schedule_item.delete()

        messages.success(
            request,
            'Schedule item deleted successfully.'
        )

        return redirect(
            'project_schedule_crud',
            pk=project.pk
        )

    # =========================
    # EDIT
    # =========================
    edit_id = request.GET.get('edit')

    edit_item = None

    if edit_id:

        edit_item = get_object_or_404(
            ProjectScheduleItem,
            pk=edit_id,
            project=project
        )

        form = ProjectScheduleItemForm(
            instance=edit_item
        )

    else:

        # If form was not created by POST
        if request.method != 'POST':
            form = ProjectScheduleItemForm()

    # =========================
    # ALL ITEMS
    # =========================

    schedule_items = ProjectScheduleItem.objects.filter(
        project=project
    ).order_by(
        'start_date'
    )

    context = {
        'project': project,
        'schedule_items': schedule_items,
        'form': form,
        'edit_item': edit_item,
    }

    return render(
        request,
        'firstlevel/project_schedule_crud.html',
        context
    )


@login_required
def project_test(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    documents = ProjectDocument.objects.filter(
        project=project,
        document_type='test'
    ).order_by('-uploaded_at')

    # =========================
    # CREATE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'create':

        title = request.POST.get('title')
        document = request.FILES.get('document')

        if not document:
            messages.error(request, 'Please select a document.')
            return redirect('project_test', pk=project.pk)

        ProjectDocument.objects.create(
            project=project,
            document_type='test',
            title=title,
            document=document
        )

        messages.success(
            request,
            'Test document added successfully.'
        )

        return redirect('project_test', pk=project.pk)

    # =========================
    # EDIT
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'edit':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='test'
        )

        title = request.POST.get('title')
        new_document = request.FILES.get('document')

        project_document.title = title

        # Only replace file if new file is selected
        if new_document:
            project_document.document = new_document

        project_document.save()

        messages.success(
            request,
            'Test document updated successfully.'
        )

        return redirect('project_test', pk=project.pk)

    # =========================
    # DELETE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'delete':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='test'
        )

        # Delete physical file also
        if project_document.document:
            project_document.document.delete(save=False)

        project_document.delete()

        messages.success(
            request,
            'Test document deleted successfully.'
        )

        return redirect('project_test', pk=project.pk)

    return render(
        request,
        'firstlevel/project_test.html',
        {
            'project': project,
            'documents': documents,
        }
    )      

@login_required
def project_drawing(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    # =========================
    # CREATE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'create':

        title = request.POST.get('title')
        document = request.FILES.get('document')

        if not document:
            messages.error(
                request,
                'Please select a drawing document.'
            )
            return redirect('project_drawing', pk=project.pk)

        ProjectDocument.objects.create(
            project=project,
            document_type='drawing',
            title=title,
            document=document
        )

        messages.success(
            request,
            'Drawing document added successfully.'
        )

        return redirect('project_drawing', pk=project.pk)

    # =========================
    # EDIT
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'edit':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='drawing'
        )

        title = request.POST.get('title')
        new_document = request.FILES.get('document')

        project_document.title = title

        # New file দিলে পুরোনো file replace হবে
        if new_document:
            project_document.document = new_document

        project_document.save()

        messages.success(
            request,
            'Drawing document updated successfully.'
        )

        return redirect('project_drawing', pk=project.pk)

    # =========================
    # DELETE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'delete':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='drawing'
        )

        # Physical uploaded file delete
        if project_document.document:
            project_document.document.delete(save=False)

        project_document.delete()

        messages.success(
            request,
            'Drawing document deleted successfully.'
        )

        return redirect('project_drawing', pk=project.pk)

    # =========================
    # DOCUMENTS
    # =========================
    documents = ProjectDocument.objects.filter(
        project=project,
        document_type='drawing'
    ).order_by('-uploaded_at')

    return render(
        request,
        'firstlevel/project_drawing.html',
        {
            'project': project,
            'documents': documents,
        }
    )

@login_required
def project_certificate(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    # =========================
    # CREATE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'create':

        title = request.POST.get('title')
        document = request.FILES.get('document')

        if not document:
            messages.error(
                request,
                'Please select a certificate document.'
            )
            return redirect('project_certificate', pk=project.pk)

        ProjectDocument.objects.create(
            project=project,
            document_type='certification',
            title=title,
            document=document
        )

        messages.success(
            request,
            'Certificate document added successfully.'
        )

        return redirect('project_certificate', pk=project.pk)

    # =========================
    # EDIT
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'edit':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='certification'
        )

        title = request.POST.get('title')
        new_document = request.FILES.get('document')

        project_document.title = title

        # New file 
        if new_document:
            project_document.document = new_document

        project_document.save()

        messages.success(
            request,
            'Certificate document updated successfully.'
        )

        return redirect('project_certificate', pk=project.pk)

    # =========================
    # DELETE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'delete':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='certification'
        )

        # Physical uploaded file delete
        if project_document.document:
            project_document.document.delete(save=False)

        project_document.delete()

        messages.success(
            request,
            'Certificate document deleted successfully.'
        )

        return redirect('project_certificate', pk=project.pk)

    # =========================
    # DOCUMENTS
    # =========================
    documents = ProjectDocument.objects.filter(
        project=project,
        document_type='certification'
    ).order_by('-uploaded_at')

    return render(
        request,
        'firstlevel/project_certificate.html',
        {
            'project': project,
            'documents': documents,
        }
    )



@login_required
def project_approval(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    # =========================
    # CREATE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'create':

        title = request.POST.get('title')
        document = request.FILES.get('document')

        if not document:
            messages.error(
                request,
                'Please select an approval document.'
            )
            return redirect('project_approval', pk=project.pk)

        ProjectDocument.objects.create(
            project=project,
            document_type='approval',
            title=title,
            document=document
        )

        messages.success(
            request,
            'Approval document added successfully.'
        )

        return redirect('project_approval', pk=project.pk)

    # =========================
    # EDIT
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'edit':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='approval'
        )

        title = request.POST.get('title')
        new_document = request.FILES.get('document')

        project_document.title = title

        # New file দিলে পুরোনো file replace হবে
        if new_document:
            project_document.document = new_document

        project_document.save()

        messages.success(
            request,
            'Approval document updated successfully.'
        )

        return redirect('project_approval', pk=project.pk)

    # =========================
    # DELETE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'delete':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='approval'
        )

        # Physical uploaded file delete
        if project_document.document:
            project_document.document.delete(save=False)

        project_document.delete()

        messages.success(
            request,
            'Approval document deleted successfully.'
        )

        return redirect('project_approval', pk=project.pk)

    # =========================
    # DOCUMENTS
    # =========================
    documents = ProjectDocument.objects.filter(
        project=project,
        document_type='approval'
    ).order_by('-uploaded_at')

    return render(
        request,
        'firstlevel/project_approval.html',
        {
            'project': project,
            'documents': documents,
        }
    )


@login_required
def agreement_land(request, pk):
    project = get_object_or_404(
        ProjectFirstLevelName,
        pk=pk
    )

    # =========================
    # CREATE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'create':

        title = request.POST.get('title')
        document = request.FILES.get('document')

        if not document:
            messages.error(
                request,
                'Please select an agreement / land document.'
            )
            return redirect('agreement_land', pk=project.pk)

        ProjectDocument.objects.create(
            project=project,
            document_type='agreement',
            title=title,
            document=document
        )

        messages.success(
            request,
            'Agreement / Land document added successfully.'
        )

        return redirect('agreement_land', pk=project.pk)

    # =========================
    # EDIT
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'edit':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='agreement'
        )

        title = request.POST.get('title')
        new_document = request.FILES.get('document')

        project_document.title = title

        # New file 
        if new_document:
            project_document.document = new_document

        project_document.save()

        messages.success(
            request,
            'Agreement / Land document updated successfully.'
        )

        return redirect('agreement_land', pk=project.pk)

    # =========================
    # DELETE
    # =========================
    if request.method == 'POST' and request.POST.get('action') == 'delete':

        document_id = request.POST.get('document_id')

        project_document = get_object_or_404(
            ProjectDocument,
            pk=document_id,
            project=project,
            document_type='agreement'
        )

        # Physical uploaded file delete
        if project_document.document:
            project_document.document.delete(save=False)

        project_document.delete()

        messages.success(
            request,
            'Agreement / Land document deleted successfully.'
        )

        return redirect('agreement_land', pk=project.pk)

    # =========================
    # DOCUMENTS
    # =========================
    documents = ProjectDocument.objects.filter(
        project=project,
        document_type='agreement'
    ).order_by('-uploaded_at')

    return render(
        request,
        'firstlevel/agreement_land.html',
        {
            'project': project,
            'documents': documents,
        }
    )






@login_required
def pfld_pdf_view(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)

    per_floor_price = 0
    per_unit_price = 0

    if project.final_total_with_extra:
        if project.number_of_floors:
            per_floor_price = project.final_total_with_extra / project.number_of_floors
        if project.number_of_units:
            per_unit_price = project.final_total_with_extra / project.number_of_units

    context = {
        'project': project,
        'per_floor_price': per_floor_price,
        'per_unit_price': per_unit_price,
    }

    template_path = 'firstlevel/pfld_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="pfld_details.pdf"'
        return response
    else:
        return HttpResponse('PDF generation failed')
    
@login_required
def employee_costing(request):    
    project_id = request.GET.get('project_id')
    project = ProjectFirstLevelName.objects.get(id=project_id)
    return render(request, 'boq/boq_emp_cost_list.html', {'projects' : project})


@login_required
@csrf_exempt
def save_employees(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            employees = data.get("employees", [])

            for emp in employees:
                EmployeeCost.objects.create(
                    project_name=emp["project_name"],
                    employee_name=emp["employee_name"],
                    first_month_salary=emp["first_month_salary"],
                    project_duration_months=emp["project_duration_months"],
                    total_salary=emp["total_salary"],
                    yearly_data=emp["yearly_data"]  
                )

            return JsonResponse({"message": "Employees saved successfully!"})

        except Exception as e:
            print("Error saving employee data:", e)
            return JsonResponse({"message": "Error saving employees", "error": str(e)}, status=500)

@login_required
def safety_equipment_view(request):
    project_id = request.GET.get('project_id')
    project = ProjectFirstLevelName.objects.get(id=project_id)
    return render(request, 'boq/boq_syfty_cost_list.html', {'projects' : project})

@login_required
def save_safety_equipment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            project_name = data.get('project_name')
            items = data.get('items')

            if not project_name or not items:
                return JsonResponse({'message': 'Invalid data received!'}, status=400)

            for item in items:
                item_name = item.get('item_name')
                quantity = item.get('quantity')
                item_cost = item.get('item_cost')

                if not item_name or quantity is None or item_cost is None:
                    continue  # Skip incomplete rows

                # Calculate total cost per row
                total_cost = float(quantity) * float(item_cost)

                # Save to DB
                SafetyEquipment.objects.create(
                    project_name=project_name,
                    item_name=item_name,
                    quantity=quantity,
                    item_cost=item_cost,
                    total_cost=total_cost
                )

            return JsonResponse({'message': 'Safety equipment data saved successfully!'})

        except Exception as e:
            return JsonResponse({'message': f"Error: {str(e)}"}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=400)


@login_required
def expense_view(request):
    project_id = request.GET.get('project_id')
    project = ProjectFirstLevelName.objects.get(id=project_id)
    return render(request, 'boq/boq_expense_cost_list.html', {'projects' : project})

@login_required
@csrf_exempt
def save_expense(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))  # decode to avoid decode error
            project_name = data.get('project_name')
            items = data.get('items')

            if not project_name or not items:
                return JsonResponse({'message': 'Missing project name or items!'}, status=400)

            for item in items:
                item_name = item.get('item_name')
                quantity = item.get('quantity')
                item_cost = item.get('item_cost')

                if not item_name or quantity is None or item_cost is None:
                    continue

                ExpenseCost.objects.create(
                    project_name=project_name,
                    item_name=item_name,
                    quantity=quantity,
                    item_cost=item_cost
                )

            return JsonResponse({'message': 'Expense data saved successfully!'})

        except Exception as e:
            return JsonResponse({'message': f"Server Error: {str(e)}"}, status=500)

    return JsonResponse({'message': 'Only POST requests allowed'}, status=405)

@login_required
def boq_category_list(request):
    categories = BoQCategory.objects.all()
    return render(request, 'boq/boq_category_list.html', {'categories': categories})


@login_required
def add_boq_type_only(request):
    if request.method == 'POST':
        form = BoQCategoryTypeForm(request.POST)
        if form.is_valid():
            boq_cat_type = form.cleaned_data['boq_cat_type']
            BoQCategory.objects.create(
                boq_cat_type=boq_cat_type,
                boq_cat_name=None
            )
            return redirect('boq_category_list') 
    else:
        form = BoQCategoryTypeForm()
    return render(request, 'boq/boq_type_only_add.html', {'form': form})


@login_required
def create_boq_category(request):
    # Get distinct existing boq_cat_type values, excluding empty strings
    existing_types = BoQCategory.objects.values_list('boq_cat_type', flat=True).distinct()
    existing_types = [t for t in existing_types if t]

    # Prepare choices list with a default empty option
    type_choices = [('', 'Select Category Type')] + [(t, t) for t in existing_types]

    if request.method == 'POST':
        form = BoQCategoryForm(request.POST)
        # Dynamically set the choices for boq_cat_type field
        form.fields['boq_cat_type'].choices = type_choices

        if form.is_valid():
            form.save()
            return redirect('boq_category_list')
    else:
        form = BoQCategoryForm()
        form.fields['boq_cat_type'].choices = type_choices

    return render(request, 'boq/create_boq_category.html', {'form': form})
    

@login_required
def edit_boq_category(request, id):
    category = get_object_or_404(BoQCategory, pk=id)
    if request.method == 'POST':
        form = BoQCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('boq_category_list')
    else:
        form = BoQCategoryForm(instance=category)
    return render(request, 'boq/edit_category.html', {'form': form})


@login_required
def delete_boq_category(request, id):
    category = get_object_or_404(BoQCategory, pk=id)
    if request.method == 'POST':
        log_deleted_data(category, request.user)
        category.delete()
        return redirect('boq_category_list')
    return render(request, 'boq/boq_category_delete.html', {'category': category})




@login_required
def boq_contructor_list(request):
    contructo = SiteSupervisor.objects.all()
    return render(request, 'contructor/boq_contructor_list.html', {'contructos': contructo})

@login_required
def create_boq_contructor(request):
    if request.method == 'POST':
        form = SiteSupervisorForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            return redirect('boq_contructor_list') 
    else:
        form = SiteSupervisorForm()

    return render(request, 'contructor/create_boq_contructor.html', {'form': form})



@login_required
def edit_boq_contructor(request, id):
    supervisor = get_object_or_404(SiteSupervisor, pk=id)
    if request.method == 'POST':
        form = SiteSupervisorForm(request.POST, instance=supervisor)
        if form.is_valid():
            form.save()
            return redirect('boq_contructor_list')
    else:
        form = SiteSupervisorForm(instance=supervisor)
    return render(request, 'contructor/edit_contructor.html', {'form': form})


@login_required
def delete_boq_contructor(request, id):
    supervisor = get_object_or_404(SiteSupervisor, pk=id)
    if request.method == 'POST':
        log_deleted_data(supervisor, request.user)
        supervisor.delete()
        return redirect('boq_contructor_list')
    return render(request, 'contructor/boq_contructor_delete.html', {'supervisors': supervisor})


@login_required
def contractor_detail(request, id):
    contractor = get_object_or_404(SiteSupervisor, id=id)
    return render(request, 'contructor/contractor_detail.html', {'contractor': contractor})

@login_required
def boq_supplier_list(request):
    supplier = Suppliers.objects.all()
    return render(request, 'supplier/boq_supplier_list.html', {'suppliers': supplier})

  

from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from projects.models import Suppliers
from inventories.models import Inventories
from accounting.models import LedgerEntry


def round2(val):
    """Helper function to round values safely to 2 decimal places."""
    if val is None:
        val = Decimal('0.00')
    elif not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@login_required
def boq_supplier_details_view(request):
    # 1. Subquery to calculate total purchased per supplier safely in the DB
    purchase_subquery = Inventories.objects.filter(
        vendor_name=OuterRef('pk')
    ).values('vendor_name').annotate(
        total=Sum('amount')
    ).values('total')

    # 2. Subquery to calculate total paid per supplier safely in the DB
    payment_subquery = LedgerEntry.objects.filter(
        vendor=OuterRef('pk'),
        type='Vendor'
    ).values('vendor').annotate(
        total=Sum('debit')
    ).values('total')

    # 3. Main Query: Exclude ONLY 'No Supplier'
    suppliers = Suppliers.objects.exclude(
        supplier_name__iexact='No Supplier'
    ).annotate(
        total_purchased=Coalesce(
            Subquery(purchase_subquery), 
            Value(0), 
            output_field=DecimalField()
        ),
        total_paid=Coalesce(
            Subquery(payment_subquery), 
            Value(0), 
            output_field=DecimalField()
        )
    )

    # Fetch unique associated projects using 'project_name__project_first_name'
    for supplier in suppliers:
        ledger_qs = LedgerEntry.objects.filter(vendor=supplier, type='Vendor')

        # Target project_first_name
        projects = ledger_qs.values_list('project_name__project_first_name', flat=True).distinct()
        
        # Fallback if project_name stores string values
        if not any(projects):
            projects = ledger_qs.values_list('project_name', flat=True).distinct()

        clean_projects = [str(p) for p in projects if p]
        supplier.projects_list = ", ".join(clean_projects) if clean_projects else "N/A"

        # Round individual amounts
        supplier.total_purchased = round2(supplier.total_purchased)
        supplier.total_paid = round2(supplier.total_paid)
        supplier.balance_due = round2(supplier.total_purchased - supplier.total_paid)

    # 4. Global Summary Totals
    overall_total_purchased = round2(sum((s.total_purchased for s in suppliers), Decimal('0.00')))
    overall_total_paid = round2(sum((s.total_paid for s in suppliers), Decimal('0.00')))
    overall_balance_due = round2(overall_total_purchased - overall_total_paid)

    context = {
        'suppliers': suppliers,
        'print_time': timezone.now(),
        'overall_total_purchased': overall_total_purchased,
        'overall_total_paid': overall_total_paid,
        'overall_balance_due': overall_balance_due,
    }
    return render(request, 'supplier/boq_supplier_details_view.html', context)

@login_required
def create_boq_supplier(request):
    if request.method == 'POST':
        form = SuppliersForm(request.POST)  
        if form.is_valid():
            form.save()
            return redirect('boq_supplier_list')
    else:
        form = SuppliersForm()

    return render(request, 'supplier/create_boq_supplier.html', {'form': form})


@login_required
def edit_boq_supplier(request, id):
    supplier = get_object_or_404(Suppliers, pk=id)
    if request.method == 'POST':
        form = SuppliersForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('boq_supplier_list')
    else:
        form = SuppliersForm(instance=supplier)
    return render(request, 'supplier/edit_boq_supplier.html', {'form': form})


@login_required
def delete_boq_supplier(request, id):
    supplier = get_object_or_404(Suppliers, pk=id)
    if request.method == 'POST':
        log_deleted_data(supplier, request.user)
        supplier.delete()
        return redirect('boq_supplier_list')
    return render(request, 'supplier/boq_supplier_delete.html', {'suppliers': supplier})

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Suppliers, pk=pk)
    return render(request, 'supplier/supplier_detail.html', {'supplier': supplier})
    




## -- Donation --
@login_required
def donation_list(request):
    donation = Donation.objects.all()
    return render(request, 'donation/donation_list.html', {'donations': donation})



@login_required
def create_donation(request):
    if request.method == 'POST':
        form = DonationForm(request.POST)  
        if form.is_valid():
            form.save()
            return redirect('donation_list')
    else:
        form = DonationForm()

    return render(request, 'donation/create_donation.html', {'form': form})


@login_required
def edit_donation(request, id):
    donation = get_object_or_404(Donation, pk=id)
    if request.method == 'POST':
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            return redirect('donation_list')
    else:
        form = DonationForm(instance=donation)
    return render(request, 'donation/edit_donation.html', {'form': form})


@login_required
def delete_donation(request, id):
    donation = get_object_or_404(Donation, pk=id)
    if request.method == 'POST':
        log_deleted_data(donation, request.user)
        donation.delete()
        return redirect('donation_list')
    return render(request, 'donation/delete_donation.html', {'donations': donation})

@login_required
def donation_detail(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    return render(request, 'donation/donation_detail.html', {'donation': donation})
    
    
    
    
    
## boq- type ---
@login_required
def boq_type_list(request):
    boq_types = BoQType.objects.all()
    return render(request, 'firstlevel/boq_type_list.html', {'boq_types': boq_types})


@login_required
def create_boq_type(request):
    if request.method == 'POST':
        name = request.POST.get('boq_type_name')
        if name:
            BoQType.objects.create(boq_type_name=name)
            return redirect('boq_type_list')
    return render(request, 'firstlevel/create_boq_type.html')


@login_required
def boq_type_edit(request, pk):
    boq_type = get_object_or_404(BoQType, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('boq_type_name')
        boq_type.boq_type_name = name
        boq_type.save()
        return redirect('boq_type_list')
    return render(request, 'firstlevel/boq_type_edit.html', {'boq_type': boq_type})


@login_required
def boq_type_delete(request, pk):
    boq_type = get_object_or_404(BoQType, pk=pk)
    if request.method == 'POST':
        log_deleted_data(boq_type, request.user)
        boq_type.delete()
        return redirect('boq_type_list')
    return render(request, 'firstlevel/boq_type_delete.html', {'boq_type': boq_type})
    
    
    


#3 Contractor ---
@login_required
def activity_list(request):    
    project = ProjectFirstLevelName.objects.all()
    activities = ContractorActivity.objects.all().order_by('-create_date')
    return render(request, 'contructor/activity_list.html', {'activities': activities, 'projects_firts': project})


@login_required
def activity_detail(request, pk):
    activity = get_object_or_404(ContractorActivity, pk=pk)
    return render(request, 'contructor/activity_detail.html', {'activity': activity})


@login_required
@csrf_exempt
def activity_add(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            project_id = data.get("project_id")
            rows = data.get("data", [])

            if not project_id:
                return JsonResponse({'status': 'error', 'message': 'Project ID is required.'})

            project = get_object_or_404(ProjectFirstLevelName, id=project_id)

            for row in rows:
                contractor_id = row['contractor']
                contractor_instance = SiteSupervisor.objects.get(id=contractor_id)

                ContractorActivity.objects.create(
                    contractor=contractor_instance,
                    project_name=project,
                    working_head=row['working_head'],
                    work_start_date=parse_date(row['work_start_date']),
                    work_end_date=parse_date(row['work_end_date']),
                    work_description=row.get('work_description', ''),
                    amount_paid=float(row['amount_paid']),
                    status=row.get('status', 'ongoing'),
                    remarks=row.get('remarks', ''),
                )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        form = ContractorActivityForm()
        contractors = SiteSupervisor.objects.all()
        today = timezone.now().date()

        project_id = request.GET.get("project_id")
        project = None
        project_name = None

        if project_id:
            try:
                project = ProjectFirstLevelName.objects.get(id=project_id)
                project_name = project.project_first_name  # Or the appropriate field
            except ProjectFirstLevelName.DoesNotExist:
                project = None
                project_name = None

        return render(request, 'contructor/activity_form.html', {
            'form': form,
            'title': 'Add Activity',
            'contractors': contractors,
            'today': today,
            'project': project,
            'project_name': project_name,
            'project_id': project_id,
        })
    


@login_required
def activity_summary(request):
    project_id = request.GET.get("project_id")  # corrected from 'data.get(...)'

    if project_id:
        projects = ProjectFirstLevelName.objects.filter(id=project_id)
    else:
        # If no project_id given, show all
        projects = ProjectFirstLevelName.objects.all()

    result = []  # 'data' variable renamed to 'result' to avoid shadowing
    for project in projects:
        activities = ContractorActivity.objects.filter(project_name=project).order_by('work_start_date')

        if activities.exists():
            first_date = activities.aggregate(Min('work_start_date'))['work_start_date__min']
            last_date = activities.aggregate(Max('work_end_date'))['work_end_date__max']
            duration = (last_date - first_date).days if first_date and last_date else 0
        else:
            first_date = last_date = None
            duration = 0

        result.append({
            'project': project,
            'activities': activities,
            'duration': duration,
            'start': first_date,
            'end': last_date,
        })

    return render(request, 'contructor/activity_summary.html', {'data': result})



@login_required
def update_activity_status(request, pk):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        activity = ContractorActivity.objects.get(pk=pk)
        activity.status = new_status
        activity.save()
    return redirect('activity_list')



@login_required
def activity_edit(request, pk):
    activity = get_object_or_404(ContractorActivity, pk=pk)

    if request.method == 'POST':
        form = ContractorActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "Activity updated successfully.")
            return redirect('activity_list')  # or any detail page if needed
    else:
        form = ContractorActivityForm(instance=activity)

    contractors = SiteSupervisor.objects.all()
    projects = ProjectFirstLevelName.objects.all()

    return render(request, 'contructor/activity_edit.html', {
        'form': form,
        'title': 'Edit Activity',
        'contractors': contractors,
        'projects': projects,
        'activity': activity,
    })


@login_required
def activity_delete(request, pk):
    activity = get_object_or_404(ContractorActivity, pk=pk)
    if request.method == 'POST':
        activity.delete()
        messages.success(request, "Activity deleted successfully.")
        return redirect('activity_list')
    return render(request, 'contructor/activity_confirm_delete.html', {'activity': activity})
    
    

@login_required
def materialentry_list(request):
    material_entries = MaterialEntry.objects.select_related('project_name').all()
    return render(request, 'firstlevel/materialentry_list.html', {
        'material_entries': material_entries
    })
    
 

# @login_required
# def material_entry_create(request):
#     client_name = ""
#     date = ""
#     selected_project = None

#     if request.method == 'POST':
#         try:
#             project_id = request.POST.get('project_id')
#             project_name = get_object_or_404(ProjectFirstLevelName, id=project_id)
#             client_name = request.POST.get('client_name')
#             date = request.POST.get('date')

#             parties = request.POST.getlist('party[]')
#             sls = request.POST.getlist('sl[]')
#             descriptions = request.POST.getlist('description[]')
#             bands = request.POST.getlist('band[]')
#             quantities = request.POST.getlist('quantity[]')
#             rates = request.POST.getlist('rate[]')

#             if not all([parties, sls, descriptions, bands, quantities, rates]):
#                 raise ValueError("❌ One or more material entry fields are missing.")

#             for i in range(len(parties)):
#                 try:
#                     quantity = float(quantities[i])
#                     rate = float(rates[i])
#                 except ValueError:
#                     raise ValueError(f"❌ Invalid number at row {i+1}: quantity or rate.")

#                 MaterialEntry.objects.create(
#                     project_name=project_name,
#                     client_name=client_name,
#                     date=date,
#                     party=parties[i],
#                     sl=int(sls[i]) if sls[i].isdigit() else 0,
#                     description=descriptions[i],
#                     band=bands[i],
#                     quantity=quantity,
#                     rate=rate
#                 )
#             messages.success(request, "✅ Material entries saved successfully.")
#             # Redirect to same URL with project_id to load comparison data
#             url = reverse('material_entry_create')
#             redirect_url = f"{url}?project_id={project_id}"
#             return redirect(redirect_url)

#         except Exception as e:
#             messages.error(request, f"❌ Error: {e}")

#     # GET or after redirect with project_id param
#     selected_project_id = request.GET.get('project_id')
#     paired_data = []
#     total_btp = 0
#     total_client = 0
#     total_diff = 0

#     if selected_project_id:
#         try:
#             selected_project = ProjectFirstLevelName.objects.get(id=selected_project_id)

#             btp_entries = list(MaterialEntry.objects.filter(
#                 project_name=selected_project,
#                 party__iexact='BTP Office'
#             ).order_by('sl'))

#             client_entries = list(MaterialEntry.objects.filter(
#                 project_name=selected_project,
#                 party__iexact='Client'
#             ).order_by('sl'))

#             max_len = max(len(btp_entries), len(client_entries))

#             while len(btp_entries) < max_len:
#                 btp_entries.append(None)
#             while len(client_entries) < max_len:
#                 client_entries.append(None)

#             for btp, client in zip(btp_entries, client_entries):
#                 btp_amount = btp.quantity * btp.rate if btp else 0
#                 client_amount = client.quantity * client.rate if client else 0
#                 difference = btp_amount - client_amount
#                 total_btp += btp_amount
#                 total_client += client_amount
#                 total_diff += difference

#                 paired_data.append({
#                     'btp': btp,
#                     'client': client,
#                     'difference': difference
#                 })

#             if client_entries and client_entries[0]:
#                 client_name = client_entries[0].client_name
#                 date = client_entries[0].date

#         except ProjectFirstLevelName.DoesNotExist:
#             messages.warning(request, "⚠️ Project not found.")
#         except Exception as e:
#             messages.error(request, f"❌ Error loading comparison data: {e}")

#     context = {
#         'today': now().date().isoformat(), 
#         'projects': ProjectFirstLevelName.objects.all(),
#         'selected_project': selected_project,
#         'paired_data': paired_data,
#         'project': selected_project,
#         'client_name': client_name,
#         'date': date,
#         'total_btp': total_btp,
#         'total_client': total_client,
#         'total_diff': total_diff,
#     }

#     return render(request, 'firstlevel/material_entry_form.html', context)



@login_required
def material_entry_create(request):
    client_name = ""
    date = ""
    selected_project = None

    if request.method == 'POST':
        try:
            project_id = request.POST.get('project_id')
            project_name = get_object_or_404(ProjectFirstLevelName, id=project_id)
            client_name = request.POST.get('client_name')
            date = request.POST.get('date')

            parties = request.POST.getlist('party[]')
            sls = request.POST.getlist('sl[]')
            descriptions = request.POST.getlist('description[]')
            bands = request.POST.getlist('band[]')
            quantities = request.POST.getlist('quantity[]')
            rates = request.POST.getlist('rate[]')

            if not all([parties, sls, descriptions, bands, quantities, rates]):
                raise ValueError("❌ One or more material entry fields are missing.")

            for i in range(len(parties)):
                try:
                    quantity = float(quantities[i])
                    rate = float(rates[i])
                except ValueError:
                    raise ValueError(f"❌ Invalid number at row {i+1}: quantity or rate.")

                MaterialEntry.objects.create(
                    project_name=project_name,
                    client_name=client_name,
                    date=date,
                    party=parties[i],
                    sl=int(sls[i]) if sls[i].isdigit() else 0,
                    description=descriptions[i],
                    band=bands[i],
                    quantity=quantity,
                    rate=rate
                )
            messages.success(request, "✅ Material entries saved successfully.")
            # Redirect to same URL with project_id to load comparison data
            url = reverse('material_entry_create')
            redirect_url = f"{url}?project_id={project_id}&date={date}"
            return redirect(redirect_url)

        except Exception as e:
            messages.error(request, f"❌ Error: {e}")

    # GET or after redirect with project_id param
    selected_project_id = request.GET.get('project_id')
    selected_date = request.GET.get('date')
    
    paired_data = []
    total_btp = 0
    total_client = 0
    total_diff = 0
    selected_project = None
    client_name = ''
    date = selected_date or now().date().isoformat()

    if selected_project_id:
        try:
            selected_project = ProjectFirstLevelName.objects.get(id=selected_project_id)

            filters = {
                'project_name': selected_project,
            }
            if selected_date:
                filters['date'] = selected_date

            btp_entries = list(MaterialEntry.objects.filter(
                **filters,
                party__iexact='BTP Office'
            ).order_by('sl'))

            client_entries = list(MaterialEntry.objects.filter(
                **filters,
                party__iexact='Client'
            ).order_by('sl'))

            max_len = max(len(btp_entries), len(client_entries))

            while len(btp_entries) < max_len:
                btp_entries.append(None)
            while len(client_entries) < max_len:
                client_entries.append(None)

            for btp, client in zip(btp_entries, client_entries):
                btp_amount = btp.quantity * btp.rate if btp else 0
                client_amount = client.quantity * client.rate if client else 0
                difference = btp_amount - client_amount
                total_btp += btp_amount
                total_client += client_amount
                total_diff += difference

                paired_data.append({
                    'btp': btp,
                    'client': client,
                    'difference': difference
                })

            if client_entries and client_entries[0]:
                client_name = client_entries[0].client_name

        except ProjectFirstLevelName.DoesNotExist:
            messages.warning(request, "⚠️ Project not found.")
        except Exception as e:
            messages.error(request, f"❌ Error loading comparison data: {e}")

    context = {
        'today': now().date().isoformat(),
        'projects': ProjectFirstLevelName.objects.all(),
        'selected_project': selected_project,
        'paired_data': paired_data,
        'project': selected_project,
        'client_name': client_name,
        'date': date,
        'total_btp': total_btp,
        'total_client': total_client,
        'total_diff': total_diff,
    }

    return render(request, 'firstlevel/material_entry_form.html', context)