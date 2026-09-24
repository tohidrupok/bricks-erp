from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
from .models import Inventories,InventoryUse
from .forms import InventoriesForm,InventoryUseForm
from projects.models import ProjectFirstLevelName,Suppliers
from projects.forms import ProjectFirstLevelName
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django.db.models import Q,Sum, Max, Min,F, Subquery, OuterRef, ExpressionWrapper, IntegerField
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import InventoryUseForm
from .models import InventoryUse
from purchase.models import HeadOfRequisition
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import transaction
from num2words import num2words
from django.core.exceptions import ValidationError
from collections import defaultdict
from decimal import Decimal
from datetime import date
from django.utils import timezone





@login_required
def inventory_item_list(request):
    projects_first = ProjectFirstLevelName.objects.all()
    suppliers = Suppliers.objects.all() 
    inventories = Inventories.objects.all()
    context = {
        'inventories': inventories, 
        'projects_firts': projects_first,
        'suppliers': suppliers
    }
    return render(request, 'inventories/inventory_item_list.html', context)

@login_required
def inventory_item_detail(request, pk):
    inventories = get_object_or_404(Inventories, pk=pk)
    return render(request, 'inventories/inventory_item_detail.html', {'inventories': inventories})



# @login_required
# def inventory_item_summary(request):
#     project_id = request.GET.get('project_id')
#     supplier_id = request.GET.get('supplier_id')
    
#     if not project_id:
#         return HttpResponse("Missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=project_id)

#     if supplier_id:
#         supplier = get_object_or_404(Suppliers, id=supplier_id)
#         inventory_items = Inventories.objects.filter(
#             project_name=project,
#             vendor_name=supplier
#         )
#         suppliers = [supplier]
#     else:
#         supplier = None
#         inventory_items = Inventories.objects.filter(project_name=project)
#         # Get all unique suppliers from the items
#         suppliers = (
#             Suppliers.objects.filter(id__in=inventory_items.values_list('vendor_name', flat=True).distinct())
#         )

#     total_amount = inventory_items.aggregate(total=Sum('amount'))['total'] or 0
#     requisition_date = inventory_items.first().requisition_date if inventory_items.exists() else None
    
#     def amount_to_words(amount):
#         try:
#             amount = round(float(amount), 2)
#             taka = int(amount)
#             paisa = int(round((amount - taka) * 100))
    
#             def bdt_number_to_words(n):
#                 n_str = str(n).zfill(9)  # Pad to 9 digits for crore/lakh
#                 crore = int(n_str[0:2])
#                 lakh = int(n_str[2:4])
#                 thousand = int(n_str[4:6])
#                 hundred = int(n_str[6])
#                 rest = int(n_str[7:9])
    
#                 parts = []
    
#                 if crore:
#                     parts.append(num2words(crore, lang='en') + ' crore')
#                 if lakh:
#                     parts.append(num2words(lakh, lang='en') + ' lakh')
#                 if thousand:
#                     parts.append(num2words(thousand, lang='en') + ' thousand')
#                 if hundred:
#                     parts.append(num2words(hundred, lang='en') + ' hundred')
#                 if rest:
#                     parts.append(num2words(rest, lang='en'))
    
#                 return ' '.join(parts).title()
    
#             words = bdt_number_to_words(taka) + " Taka"
#             if paisa:
#                 words += " and " + num2words(paisa, lang='en').title() + " Paisa"
#             return words + " Only"
    
#         except Exception as e:
#             return f"{amount} Taka Only"
            
#     context = {
#         'project': project,
#         'supplier': supplier,
#         'suppliers': suppliers,
#         'inventory_items': inventory_items,
#         'requisition_items': inventory_items,  # <-- Fix this line
#         'total_amount': total_amount,
#         'amount_in_words': amount_to_words(total_amount),
#         'print_time': now(),
#         'requisition_date': requisition_date,
#     }
#     return render(request, 'inventories/inventory_item_summary.html', context)





@login_required
def inventory_item_summary(request):
    project_id = request.GET.get('project_id')
    item_id = request.GET.get('item_id')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

    if item_id and item_id.isdigit():
        item_name = get_object_or_404(HeadOfRequisition, id=int(item_id))
        inventories_items = Inventories.objects.filter(project_name=project, item_name=item_name)
    else:
        inventories_items = Inventories.objects.filter(project_name=project)

    # Collect all remarks, excluding empty/null ones
    remarks_list = inventories_items.exclude(remark__isnull=True).exclude(remark__exact='').values_list('remark', flat=True)

    # Handle requisition_date safely
    requisition_date = inventories_items.first().requisition_date if inventories_items.exists() else None

    context = {
        'project': project,
        'requisition_items': inventories_items,
        'remarks': remarks_list,
        'print_time': now(),
        'requisition_date': requisition_date,
    }
    return render(request, 'inventories/inventory_item_summary.html', context)







@login_required
def inventory_stock_summary(request):
    projects_first = ProjectFirstLevelName.objects.all()
    suppliers = Suppliers.objects.all() 
    headofReqs = HeadOfRequisition.objects.all() 
    summary = (
        Inventories.objects
        .values('item_name__id', 'item_name__head_requi_name') 
        .annotate(total_qty=Sum('qty'), total_qtysub=Sum('qtysub'))
        .order_by('item_name__head_requi_name')
    )
    return render(request, 'inventories/inventory_stock_summary.html', {'summary': summary, 'projects_firts': projects_first, 'suppliers': suppliers, 'headofReqs': headofReqs})



from django.http import JsonResponse
from .models import Inventories

def get_project_wise_items(request):

    project_id = request.GET.get('project_id')

    items = Inventories.objects.filter(
        project_name_id=project_id
    ).select_related('item_name').values(
        'item_name__id',
        'item_name__head_requi_name'
    ).distinct()

    item_list = []

    for item in items:
        item_list.append({
            'id': item['item_name__id'],
            'name': item['item_name__head_requi_name']
        })

    return JsonResponse({
        'items': item_list
    })
    
    

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone


def inventory_stock_item_transfer(request):
    """
    Inventory Stock Transfer between two projects.
    Supports URL params: ?project_from_id=14&project_to_id=15&item_id=3
    """

    projects = ProjectFirstLevelName.objects.all()

    # ================================
    # URL PARAMETERS (GET)
    # ================================
    url_from_project = request.GET.get("project_from_id")
    url_to_project = request.GET.get("project_to_id")
    url_item_id = request.GET.get("item_id")

    # ================================
    # POST (TRANSFER SAVE)
    # ================================
    if request.method == "POST":

        from_project = request.POST.get("from_project")
        to_project = request.POST.get("to_project")
        post_item_id = request.GET.get("item_id") or request.POST.get("item_id")

        if not from_project or not to_project:
            messages.error(request, "Please select both From and To project.")
            return redirect("inventory_stock_item_transfer")

        if from_project == to_project:
            messages.error(request, "From and To project cannot be the same.")
            return redirect("inventory_stock_item_transfer")

        item_ids = request.POST.getlist("item_id[]")
        qty_list = request.POST.getlist("transfer_qty[]")

        if not item_ids:
            messages.error(request, "No items selected for transfer.")
            return redirect("inventory_stock_item_transfer")

        try:
            with transaction.atomic():

                transferred_count = 0

                for item_id, qty in zip(item_ids, qty_list):

                    # Skip empty / zero quantities
                    try:
                        qty = float(qty) if qty else 0
                    except (ValueError, TypeError):
                        qty = 0

                    if qty <= 0:
                        continue

                    # Get source inventory row
                    try:
                        source = Inventories.objects.select_for_update().get(
                            id=item_id,
                            project_name_id=from_project
                        )
                    except Inventories.DoesNotExist:
                        messages.error(
                            request,
                            f"Source item (ID: {item_id}) not found in From Project."
                        )
                        return redirect("inventory_stock_item_transfer")

                    # Validate available stock
                    if source.qtysub is None or source.qtysub < qty:
                        messages.error(
                            request,
                            f"Not enough stock for '{source.item_name}'. "
                            f"Available: {source.qtysub}, Requested: {qty}"
                        )
                        return redirect("inventory_stock_item_transfer")

                    # ---- Decrease from source ----
                    source.qtysub -= qty
                    source.save()

                    # ---- Check destination row ----
                    dest = Inventories.objects.select_for_update().filter(
                        project_name_id=to_project,
                        item_name=source.item_name
                    ).first()

                    if dest:
                        # Increase destination qtysub
                        dest.qtysub = (dest.qtysub or 0) + qty
                        dest.save()
                    else:
                        # Create a new row in destination project
                        Inventories.objects.create(
                            requi_id=source.requi_id,
                            project_name_id=to_project,
                            employee_name=source.employee_name,
                            item_name=source.item_name,
                            vendor_name=source.vendor_name,
                            unit=source.unit,
                            qty=0,
                            rate=source.rate,
                            amount=0,
                            remark="Transfer Stock",
                            requisition_date=source.requisition_date,
                            qtysub=qty,
                            purch_id=source.purch_id,
                            purch_date=source.purch_date,
                        )

                    transferred_count += 1

                if transferred_count == 0:
                    messages.warning(request, "No items were transferred (qty was 0).")
                else:
                    messages.success(
                        request,
                        f"Transfer successful! {transferred_count} item(s) moved."
                    )

        except Exception as e:
            messages.error(request, f"Transfer failed: {str(e)}")

        # Redirect back keeping the same projects selected
        return redirect(
            f"{request.path}?project_from_id={from_project}&project_to_id={to_project}&item_id={post_item_id}"
        )

    # ================================
    # INITIAL RENDER  (GET)
    # ================================
    from_items = []
    to_items = []
    highlight_item = None

    if url_from_project:
        from_qs = Inventories.objects.filter(
            project_name_id=url_from_project
        ).select_related("item_name")

        # If a specific item_id is given, filter to that one only
        if url_item_id:
            # url_item_id refers to the head_requi item id (the item master)
            from_qs = from_qs.filter(item_name_id=url_item_id)

        from_items = list(from_qs)

    if url_to_project:
        to_qs = Inventories.objects.filter(
            project_name_id=url_to_project
        ).select_related("item_name")

        if url_item_id:
            to_qs = to_qs.filter(item_name_id=url_item_id)

        to_items = list(to_qs)

        # If item_id given but not found in destination -> we'll show a "null" row
        if url_item_id and not to_items:
            highlight_item = url_item_id

    context = {
        "projects": projects,
        "url_from_project": url_from_project,
        "url_to_project": url_to_project,
        "url_item_id": url_item_id,
        "from_items": from_items,
        "to_items": to_items,
        "highlight_item": highlight_item,
        "print_time": timezone.now(),
    }

    return render(request, "inventories/item_transfer.html", context)


# ================================
# AJAX: Get items by project id
# ================================
def get_project_items(request, project_id):
    """
    Return items for a project. Optional ?item_id=X filters to a single item.
    """
    item_id = request.GET.get("item_id")

    items = Inventories.objects.filter(
        project_name_id=project_id
    ).select_related("item_name")

    if item_id:
        items = items.filter(item_name_id=item_id)

    data = []
    for i in items:
        data.append({
            "id": i.id,
            "item_master_id": i.item_name_id,
            "item_name": i.item_name.head_requi_name if i.item_name else "",
            "rate": float(i.rate) if i.rate else 0,
            "qty": float(i.qty) if i.qty else 0,
            "qtysub": float(i.qtysub) if i.qtysub else 0,
            "unit": i.unit or "",
            "remark": i.remark or "",
        })

    return JsonResponse(data, safe=False)

    
    

# def get_project_items(request, project_id):

#     items = Inventories.objects.filter(
#         project_name_id=project_id,
#         qtysub__gt=0
#     )

#     data = []

#     for item in items:

#         data.append({
#             'id': item.id,
#             'item_name': item.item_name.item,
#             'qtysub': item.qtysub,
#             'unit': item.unit,
#         })

#     return JsonResponse(data, safe=False)
    
    


# @login_required
# def inventory_stock_summary(request):
#     projects_first = ProjectFirstLevelName.objects.all()
#     suppliers = Suppliers.objects.all() 
    
#     # get unique categories from HeadOfRequisition table
#     categories = (
#         HeadOfRequisition.objects
#         .values('requi_category__id', 'requi_category__requi_category_name')
#         .distinct()
#     )

#     summary = (
#         Inventories.objects
#         .values('item_name__id', 'item_name__head_requi_name') 
#         .annotate(total_qty=Sum('qty'), total_qtysub=Sum('qtysub'))
#         .order_by('item_name__head_requi_name')
#     )

#     return render(request, 'inventories/inventory_stock_summary.html', {
#         'summary': summary,
#         'projects_firts': projects_first,
#         'suppliers': suppliers,
#         'categories': categories,
#     })


# @login_required
# def get_items_by_category(request, category_id):
#     items = HeadOfRequisition.objects.filter(requi_category_id=category_id).values('id', 'head_requi_name')
#     return JsonResponse(list(items), safe=False)

    
    
    


# @login_required
# def inventory_stock_summary_check(request):
#     project_id = request.GET.get('project_id')
#     item_id = request.GET.get('item_id')

#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

#     # Filter inventories for the project (and optionally item)
#     queryset = Inventories.objects.filter(project_name=project)
#     if item_id and item_id.isdigit():
#         queryset = queryset.filter(item_name_id=int(item_id))

#     # Subquery to get last purchase qty for each item based on latest purch_date
#     last_purchase_subquery = Inventories.objects.filter(
#         project_name=project,
#         item_name=OuterRef('item_name')
#     ).order_by('-purch_date').values('qty')[:1]

#     # Subquery to get last remark for each item based on latest purch_date
#     last_remark_subquery = Inventories.objects.filter(
#         project_name=project,
#         item_name=OuterRef('item_name')
#     ).order_by('-purch_date').values('remark')[:1]

#     inventory_data = (
#         queryset.values('item_name', 'item_name__head_requi_name')
#         .annotate(
#             total_qty=Sum('qty'),
#             available_qty=Sum('qtysub'),
#             last_purchase_qty=Subquery(last_purchase_subquery),
#             last_remark=Subquery(last_remark_subquery),
#         )
#         .annotate(
#             use_qty=F('total_qty') - F('available_qty')
#         )
#         .order_by('item_name__head_requi_name')
#     )

#     context = {
#         'project': project,
#         'inventory_data': inventory_data,
#         'print_time': now(),
#     }
#     return render(request, 'inventories/inventory_stock_summary_check.html', context)
    


@login_required
def inventory_stock_summary_check(request):
    project_id = request.GET.get('project_id')
    item_id = request.GET.get('item_id')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

    # Base queryset filtered by project (and item if given)
    queryset = Inventories.objects.filter(project_name=project)
    if item_id and item_id.isdigit():
        queryset = queryset.filter(item_name_id=int(item_id))

    # Subquery to get last purchase qty for each item_name
    last_purchase_subquery = Inventories.objects.filter(
        project_name=project,
        item_name=OuterRef('item_name')
    ).order_by('-purch_date').values('qty')[:1]

    # Subquery to get last purchase remark for each item_name
    last_remark_subquery = Inventories.objects.filter(
        project_name=project,
        item_name=OuterRef('item_name')
    ).order_by('-purch_date').values('remark')[:1]

    # Aggregate sums grouped by item_name
    inventory_data = (
        queryset
        .values('item_name', 'item_name__head_requi_name')
        .annotate(
            total_qty=Sum('qty'),
            available_qty=Sum('qtysub'),
            last_purchase_qty=Subquery(last_purchase_subquery, output_field=IntegerField()),
            last_remark=Subquery(last_remark_subquery),
        )
        .annotate(
            use_qty=ExpressionWrapper(
                F('total_qty') - F('available_qty'),
                output_field=IntegerField()
            )
        )
        .order_by('item_name__head_requi_name')
    )

    context = {
        'project': project,
        'inventory_data': inventory_data,
        'print_time': now(),
    }

    return render(request, 'inventories/inventory_stock_summary_check.html', context)
    
    
    

@csrf_exempt
def update_inventory_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item = Inventories.objects.get(id=data['id'])

            # Bulk update qty and qtysub together
            if 'qty' in data and 'qtysub' in data:
                item.qty = float(data['qty'])
                item.qtysub = float(data['qtysub'])

            # Single field update for rate or remark
            elif 'field' in data and 'value' in data:
                field = data['field']
                value = data['value']
                if field in ['rate', 'qty', 'qtysub']:
                    setattr(item, field, float(value))
                elif field == 'remark':
                    setattr(item, field, value)
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid field'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

            item.save()
            return JsonResponse({'status': 'success'})

        except Inventories.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

            
            
## -- working code----          
            
# @login_required
# def inventory_use_create(request):
#     project_id = request.GET.get('project_id') or None
#     headRequists = HeadOfRequisition.objects.all()
#     project_first_name = ''

#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             project_id = data.get('project_id')
#             remark = data.get('remark', '')
#             items = data.get('data', [])

#             if not project_id:
#                 return JsonResponse({"status": "error", "message": "Project ID is required."}, status=400)

#             project = ProjectFirstLevelName.objects.get(pk=project_id)

#             if not items:
#                 return JsonResponse({"status": "error", "message": "No items provided."}, status=400)

#             with transaction.atomic():
#                 for item in items:
#                     head_id = item.get('item_name')
#                     qty = item.get('qty')
#                     details = item.get('details', '')

#                     if not head_id or not qty:
#                         raise ValueError("Item name and quantity are required.")

#                     try:
#                         qty = int(qty)
#                         if qty <= 0:
#                             raise ValueError()
#                     except:
#                         raise ValueError(f"Invalid quantity: {qty}")

#                     head = HeadOfRequisition.objects.get(pk=head_id)

#                     inventory_use = InventoryUse(
#                         project_name=project,
#                         item_name=head,
#                         qty=qty,
#                         details=details,
#                         remark=remark
#                     )

#                     try:
#                         inventory_use.save()  
#                     except ValidationError as ve:
#                         raise ValueError(str(ve))

#             return JsonResponse({"status": "success"})

#         except ProjectFirstLevelName.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Project not found."}, status=404)
#         except HeadOfRequisition.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Item not found."}, status=404)
#         except ValueError as ve:
#             return JsonResponse({"status": "error", "message": str(ve)}, status=400)
#         except json.JSONDecodeError as e:
#             return JsonResponse({"status": "error", "message": f"Invalid JSON: {str(e)}"}, status=400)
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

#     else:
#         form = InventoryUseForm()
#         if project_id:
#             try:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 project_first_name = project.project_first_name
#             except ProjectFirstLevelName.DoesNotExist:
#                 messages.warning(request, "Project not found.")

#         context = {
#             'form': form,
#             'project_id': project_id,
#             'project_first_name': project_first_name,
#             'headRequists': headRequists,
#         }
#         return render(request, 'inventories/inventory_use_create.html', context)


### owrking code ..end -----
# @login_required
# def inventory_use_create(request):
#     project_id = request.GET.get('project_id') or None

#     # ✅ Fetch all items used in inventories with total stock
#     headRequists = HeadOfRequisition.objects.filter(
#         id__in=Inventories.objects.values_list('item_name_id', flat=True)
#     ).annotate(
#         total_stock=Sum('inventories__qtysub')  # Adjust related_name if needed
#     ).values('id', 'head_requi_name', 'total_stock').distinct()

#     project_first_name = ''

#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             project_id = data.get('project_id')
#             remark = data.get('remark', '')
#             items = data.get('data', [])

#             if not project_id:
#                 return JsonResponse({"status": "error", "message": "Project ID is required."}, status=400)

#             project = ProjectFirstLevelName.objects.get(id=project_id)

#             if not items:
#                 return JsonResponse({"status": "error", "message": "No items provided."}, status=400)

#             with transaction.atomic():
#                 for item in items:
#                     head_id = item.get('item_name')
#                     qty = Decimal(str(item.get('qty', '0')))
#                     details = item.get('details', '')

#                     if not head_id or qty <= 0:
#                         raise ValueError("Item name and positive quantity are required.")
                        
#                     total_stock = Inventories.objects.filter(item_name_id=head_id).aggregate(
#                         total=Sum('qtysub')
#                     )['total'] or Decimal('0')

#                     if qty > total_stock:
#                         raise ValueError(
#                             f"Your use item qty ({qty}) exceeds the available stock ({total_stock})."
#                         )

#                     head = HeadOfRequisition.objects.get(id=head_id)

#                     # Create InventoryUse record (qtysub deduction logic assumed in model's save)
#                     InventoryUse.objects.create(
#                         project_name=project,
#                         item_name=head,
#                         qty=qty,
#                         details=details,
#                         remark=remark
#                     )

#             return JsonResponse({"status": "success"})

#         except ProjectFirstLevelName.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Project not found."}, status=404)
#         except HeadOfRequisition.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Item not found."}, status=404)
#         except ValueError as ve:
#             return JsonResponse({"status": "error", "message": str(ve)}, status=400)
#         except json.JSONDecodeError:
#             return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

#     else:
#         form = InventoryUseForm()
#         if project_id:
#             try:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 project_first_name = project.project_first_name
#             except ProjectFirstLevelName.DoesNotExist:
#                 messages.warning(request, "Project not found.")

#         context = {
#             'form': form,
#             'project_id': project_id,
#             'project_first_name': project_first_name,
#             'headRequists': headRequists,
#         }
#         return render(request, 'inventories/inventory_use_create.html', context)



# @login_required
# def inventory_use_create(request):
#     project_id = request.GET.get('project_id') or None

#     # Fetch all items with total stock grouped by item_name (optionally filter by project)
#     headRequists = HeadOfRequisition.objects.filter(
#         id__in=Inventories.objects.values_list('item_name_id', flat=True)
#     ).annotate(
#         total_stock=Sum('inventories__qtysub')
#     ).values('id', 'head_requi_name', 'total_stock').distinct()

#     project_first_name = ''

#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             project_id = data.get('project_id')
#             remark = data.get('remark', '')
#             items = data.get('data', [])

#             if not project_id:
#                 return JsonResponse({"status": "error", "message": "Project ID is required."}, status=400)

#             project = ProjectFirstLevelName.objects.get(id=project_id)

#             if not items:
#                 return JsonResponse({"status": "error", "message": "No items provided."}, status=400)

#             with transaction.atomic():
#                 for item in items:
#                     head_id = item.get('item_name')
#                     qty = Decimal(str(item.get('qty', '0')))
#                     details = item.get('details', '')

#                     if not head_id or qty <= 0:
#                         raise ValueError("Item name and positive quantity are required.")

#                     # Filter stock only for the current project AND item
#                     total_stock = Inventories.objects.filter(
#                         item_name_id=head_id,
#                         qtysub__gt=0
#                     ).aggregate(total=Sum('qtysub'))['total'] or Decimal('0')

#                     if qty > total_stock:
#                         raise ValueError(
#                             f"Your use item qty ({qty}) exceeds the available stock ({total_stock})."
#                         )

#                     head = HeadOfRequisition.objects.get(id=head_id)

#                     InventoryUse.objects.create(
#                         project_name=project,
#                         item_name=head,
#                         qty=qty,
#                         details=details,
#                         remark=remark
#                     )

#             return JsonResponse({"status": "success"})

#         except ProjectFirstLevelName.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Project not found."}, status=404)
#         except HeadOfRequisition.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Item not found."}, status=404)
#         except ValueError as ve:
#             return JsonResponse({"status": "error", "message": str(ve)}, status=400)
#         except json.JSONDecodeError:
#             return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

#     else:
#         form = InventoryUseForm()
#         if project_id:
#             try:
#                 project = ProjectFirstLevelName.objects.get(pk=project_id)
#                 project_first_name = project.project_first_name
#             except ProjectFirstLevelName.DoesNotExist:
#                 messages.warning(request, "Project not found.")

#         context = {
#             'form': form,
#             'project_id': project_id,
#             'project_first_name': project_first_name,
#             'headRequists': headRequists,
#         }
#         return render(request, 'inventories/inventory_use_create.html', context)




@login_required
def inventory_use_create(request):
    project_id = request.GET.get('project_id') or None
    headRequists = HeadOfRequisition.objects.filter(
        id__in=Inventories.objects.values_list('item_name_id', flat=True),
        inventories__project_name_id=project_id
    ).annotate(
        total_stock=Sum('inventories__qtysub')
    ).values('id', 'head_requi_name', 'total_stock').distinct()
    

    project_first_name = ''
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            remark = data.get('remark', '')
            items = data.get('data', [])

            if not project_id:
                return JsonResponse({"status": "error", "message": "Project ID is required."}, status=400)

            project = ProjectFirstLevelName.objects.get(id=project_id)

            if not items:
                return JsonResponse({"status": "error", "message": "No items provided."}, status=400)

            with transaction.atomic():
                for item in items:
                    inputDate = item.get('input_date')
                    head_id = item.get('item_name')
                    try:
                        qty = Decimal(str(item.get('qty', '0')))
                    except:
                        raise ValueError("Invalid quantity format.")
                    details = item.get('details', '')
            
                    if not head_id or qty <= 0:
                        raise ValueError("Item name and positive quantity are required.")
            
                    total_stock = Inventories.objects.filter(
                        project_name_id=project_id,
                        item_name_id=head_id,
                        qtysub__gt=0
                    ).aggregate(total=Sum('qtysub'))['total'] or Decimal('0')
            
                    if qty > total_stock:
                        raise ValueError(
                            f"Your use item qty ({qty}) exceeds the available stock ({total_stock})."
                        )
            
                    head = HeadOfRequisition.objects.get(id=head_id)
                    qtysub_qty = total_stock - qty
            
                    inv_use = InventoryUse(
                        project_name=project,
                        item_name=head,
                        qty=qty,
                        total_qty=total_stock,
                        qtysub_qty=qtysub_qty,
                        details=details,
                        use_date=inputDate,
                        remark=remark
                    )
                    inv_use.save()
            return JsonResponse({"status": "success"})

        except ProjectFirstLevelName.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Project not found."}, status=404)
        except HeadOfRequisition.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Item not found."}, status=404)
        except ValueError as ve:
            return JsonResponse({"status": "error", "message": str(ve)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

    else:
        form = InventoryUseForm()
        if project_id:
            try:
                project = ProjectFirstLevelName.objects.get(pk=project_id)
                project_first_name = project.project_first_name
            except ProjectFirstLevelName.DoesNotExist:
                messages.warning(request, "Project not found.")

        context = {
            'form': form,
            'project_id': project_id,
            'project_first_name': project_first_name,
            'headRequists': headRequists,
            'today': date.today().strftime('%Y-%m-%d')
        }
        return render(request, 'inventories/inventory_use_create.html', context)







@login_required
def inventory_use_list(request):
    # Optional: for filters or dropdowns
    head_reqis = HeadOfRequisition.objects.all()
    projects_first = ProjectFirstLevelName.objects.all()

    # Get all InventoryUse entries with foreign key data
    inventory_uses = InventoryUse.objects.select_related('project_name', 'item_name').order_by('-use_date')

    # Prepare data for display
    display_data = []
    for row in inventory_uses:
        display_data.append({
            'id': row.id,
            'use_date': row.use_date,
            'project_name': row.project_name.project_first_name,
            'item': row.item_name.head_requi_name,
            'qty': row.qty,
            'total_qty': row.total_qty,
            'qtysub_qty': row.qtysub_qty,
            'details': row.details,
            'remark': row.remark,
        })

    context = {
        'display_data': display_data,
        'projects_firts': projects_first,
        'head_reqis': head_reqis,
    }
    return render(request, 'inventories/inventory_use_list.html', context)





@login_required
def inventory_use_edit(request, id):
    instance = get_object_or_404(InventoryUse, pk=id)

    if request.method == 'POST':
        new_qty_str = request.POST.get('new_qty')
        action_type = request.POST.get('action_type')  # 'increment' or 'decrement'

        if not action_type or not new_qty_str:
            messages.error(request, "Please select an action and enter quantity.")
            return redirect('inventory_use_edit', id=id)

        try:
            new_qty = Decimal(new_qty_str)
            if new_qty <= 0:
                raise ValueError
        except:
            messages.error(request, "New quantity must be a positive number.")
            return redirect('inventory_use_edit', id=id)

        try:
            with transaction.atomic():
                item = instance.item_name

                # Get total qtysub across all Inventories for this item
                total_qtysub = Inventories.objects.filter(item_name=item).aggregate(
                    total=Sum('qtysub'))['total'] or Decimal('0')

                if action_type == 'increment':
                    # Check if enough stock
                    if new_qty > total_qtysub:
                        messages.error(request, f"Only {total_qtysub} available in stock.")
                        return redirect('inventory_use_edit', id=id)

                    # Update InventoryUse.qty
                    instance.qty += new_qty

                    # Subtract new_qty once from qtysub of first inventory row for item_name
                    stock = Inventories.objects.filter(item_name=item).order_by('id').first()
                    if stock:
                        stock.qtysub -= new_qty
                        if stock.qtysub < 0:
                            stock.qtysub = 0  # safeguard
                        stock.save()

                elif action_type == 'decrement':
                    if new_qty > instance.qty:
                        messages.error(request, f"Cannot decrement more than current quantity ({instance.qty}).")
                        return redirect('inventory_use_edit', id=id)

                    # Update InventoryUse.qty
                    instance.qty -= new_qty

                    # Add new_qty once to qtysub of first inventory row for item_name
                    stock = Inventories.objects.filter(item_name=item).order_by('id').first()
                    if stock:
                        stock.qtysub += new_qty
                        stock.save()

                else:
                    messages.error(request, "Invalid action type.")
                    return redirect('inventory_use_edit', id=id)

                instance.save()
                messages.success(request, "Inventory use quantity updated successfully.")
                return redirect('inventory_use_list')

        except Exception as e:
            messages.error(request, f"Error occurred: {e}")
            return redirect('inventory_use_edit', id=id)

    return render(request, 'inventories/inventory_use_edit.html', {'instance': instance})

    
    

# @login_required
# def inventory_use_edit(request, id):
#     instance = get_object_or_404(InventoryUse, pk=id)

#     if request.method == 'POST':
#         new_qty_str = request.POST.get('qty')
#         # Use the existing item_name id from instance to avoid item switching issues
#         item_name_id = instance.item_name.id

#         if not new_qty_str:
#             messages.error(request, "Quantity is required.")
#             form = InventoryUseForm(instance=instance)
#             return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})

#         try:
#             new_qty = int(new_qty_str)
#             if new_qty < 0:
#                 raise ValueError("Quantity must be non-negative.")
#         except ValueError:
#             messages.error(request, "Quantity must be a valid non-negative integer.")
#             form = InventoryUseForm(instance=instance)
#             return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})

#         old_qty = instance.qty
#         diff = new_qty - old_qty

#         try:
#             # Fetch related inventory by project and item_name
#             inventory = Inventories.objects.get(
#                 project_name=instance.project_name,
#                 item_name_id=item_name_id
#             )

#             with transaction.atomic():
#                 if diff > 0:
#                     # Requesting more quantity than before
#                     if inventory.qtysub < diff:
#                         messages.error(request, f"Not enough stock. Only {inventory.qtysub} available.")
#                         form = InventoryUseForm(instance=instance)
#                         return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})
#                     inventory.qtysub -= diff
#                 elif diff < 0:
#                     # Returning unused quantity back to inventory
#                     inventory.qtysub += abs(diff)

#                 inventory.save()

#                 # Update usage quantity after inventory updated successfully
#                 instance.qty = new_qty
#                 instance.save()

#                 messages.success(request, "Inventory usage quantity updated successfully.")
#                 return redirect('inventory_use_list')

#         except Inventories.DoesNotExist:
#             messages.error(request, "Related inventory record not found.")
#         except Exception as e:
#             messages.error(request, f"Error updating inventory: {e}")

#         form = InventoryUseForm(instance=instance)
#         return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})

#     else:
#         form = InventoryUseForm(instance=instance)

#     return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})

    
    
    
    
    
# @login_required
# def inventory_use_edit(request, id):
#     instance = get_object_or_404(InventoryUse, pk=id)
#     if request.method == 'POST':
#         form = InventoryUseForm(request.POST, instance=instance)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Inventory usage updated successfully.")
#             return redirect('inventory_use_list') 
#     else:
#         form = InventoryUseForm(instance=instance)
#     return render(request, 'inventories/inventory_use_edit.html', {'form': form, 'instance': instance})
    

# @login_required
# def inventory_use_edit(request, id):
#     instance = get_object_or_404(InventoryUse, pk=id)
#     project_list = ProjectFirstLevelName.objects.all()
#     item_list = HeadOfRequisition.objects.all()

#     if request.method == 'POST':
#         form = InventoryUseForm(request.POST, instance=instance)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Inventory usage updated successfully.")
#             return redirect('inventory_use_list') 
#     else:
#         form = InventoryUseForm(instance=instance)

#     context = {
#         'form': form,
#         'instance': instance,
#         'project_list': project_list,
#         'item_list': item_list,
#     }
#     return render(request, 'inventories/inventory_use_edit.html', context)
    


# Convert amount to words (basic version)
# @login_required
# def use_item_summary(request):
#     project_id = request.GET.get('project_id')
#     item_id = request.GET.get('item_id')

#     if not project_id or not project_id.isdigit():
#         return HttpResponse("Invalid or missing project_id.", status=400)

#     project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

#     queryset = InventoryUse.objects.filter(project_name=project)
#     if item_id and item_id.isdigit():
#         queryset = queryset.filter(item_name_id=int(item_id))

#     inventory_data = (
#         queryset.values('item_name', 'item_name__head_requi_name')
#         .annotate(
#             total_qty=Sum('total_qty'),
#             last_purchase_qty=Max('qty'),  
#             use_qty=Sum('qty'),
#             available_qty=Sum('qtysub_qty'),
#             last_remark=Max('remark')
#         )
#         .order_by('item_name__head_requi_name')
#     )

#     use_date_obj = queryset.order_by('use_date').first()
#     use_date = use_date_obj.use_date if use_date_obj else None

#     remarks_list = queryset.exclude(remark__isnull=True).exclude(remark__exact='').values_list('remark', flat=True)

#     context = {
#         'project': project,
#         'inventory_data': inventory_data,
#         'remarks': remarks_list,
#         'print_time': now(),
#         'use_date': use_date,  
#     }

#     return render(request, 'inventories/use_item_summary.html', context)
    



@login_required
def use_item_summary(request):
    project_id = request.GET.get('project_id')
    item_id = request.GET.get('item_id')

    if not project_id or not project_id.isdigit():
        return HttpResponse("Invalid or missing project_id.", status=400)

    project = get_object_or_404(ProjectFirstLevelName, id=int(project_id))

    # ✅ Now pulling from Inventories instead of InventoryUse
    queryset = Inventories.objects.filter(project_name=project)
    if item_id and item_id.isdigit():
        queryset = queryset.filter(item_name_id=int(item_id))

    inventory_data = (
        queryset.values(
            'project_name_id',                      # Project FK ID
            'project_name__project_first_name',     # Project name
            'item_name_id',                         # Item FK ID
            'item_name__head_requi_name'            # Item name
        )
        .annotate(
            total_qty=Sum('qty'),                   # Total purchased qty
            available_qty=Sum('qtysub'),            # Current available qty
            last_purchase_qty=Max('qty'),           # Last purchased qty
            last_remark=Max('remark'),              # Last remark
            first_purchase_date=Min('purch_date'),  # First purchase date
            last_purchase_date=Max('purch_date')    # Last purchase date
        )
        .order_by('project_name__project_first_name', 'item_name__head_requi_name')
    )

    remarks_list = queryset.exclude(remark__isnull=True).exclude(remark__exact='').values_list('remark', flat=True)

    context = {
        'project': project,
        'inventory_data': inventory_data,
        'remarks': remarks_list,
        'print_time': now(),
    }
    return render(request, 'inventories/use_item_summary.html', context)

    
    
    
    
    
    
    
from .models import DeletedRecord

def deleted_records_view(request):
    records = DeletedRecord.objects.all().order_by('-deleted_at')
    return render(request, 'inventories/deleted_records.html', {'records': records})


import json
from django.apps import apps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from .models import DeletedRecord

def undo_deleted_record(request, pk):
    record = get_object_or_404(DeletedRecord, pk=pk)
    model_name = record.model_name
    data = record.deleted_data.copy()  # copy to avoid modifying original

    # 🔁 Detect app & model
    Model = None
    for app in apps.get_app_configs():
        try:
            model = app.get_model(model_name)
            if model:
                Model = model
                break
        except LookupError:
            continue

    if not Model:
        messages.error(request, f"Model '{model_name}' not found.")
        return redirect('deleted_records')

    try:
        with transaction.atomic():
            # ✅ Convert foreign keys
            for field in Model._meta.fields:
                if field.is_relation and field.name in data and data[field.name] is not None:
                    rel_model = field.remote_field.model
                    data[field.name] = rel_model.objects.get(pk=data[field.name])

            obj, created = Model.objects.update_or_create(
                id=data.get("id"),
                defaults=data
            )
            record.delete()
            messages.success(request, f"{model_name} restored successfully.")
    except Exception as e:
        messages.error(request, f"Error restoring {model_name}: {e}")

    return redirect('deleted_records')

