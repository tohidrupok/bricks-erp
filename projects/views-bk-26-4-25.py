from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import tempfile
from .models import BOQ
from .forms import BOQForm
from django.contrib import messages
from properties.models import Project
from projects.models import ProjectFirstLevelName,EmployeeCost,SafetyEquipment,ExpenseCost,Suppliers,SiteSupervisor,Suppliers
from .forms import ProjectFirstLevelName
from .forms import ProjectFirstLevelNameForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from io import BytesIO
import logging
from decimal import Decimal
from .models import BoQCategory
from .forms import BoQCategoryForm,SiteSupervisorForm
from django.db.models import Sum
from calendar import month_name 
from datetime import date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta 
from datetime import datetime
import calendar
from django.db.models import Min
from .forms import SuppliersForm

logger = logging.getLogger(__name__)
@login_required
def boq_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()
    #BoQ_Category = BoQCategory.objects.all()
    #BoQ_Category_type = BoQCategory.objects.values_list('boq_cat_type', flat=True).distinct()
    BoQ_Category_Types = BoQCategory.objects.values('boq_cat_type').annotate(id=Min('id'))
    boqs_grouped = BOQ.objects.values(
        'project_name__project_first_name',  
        'project_name__location',           
        'project_name__project_start_date',
        'project_name__project_end_date',   
        'project_name__project_duration'    
    ).annotate(
        total_amount=Sum('amount')           
    ).order_by('project_name__project_first_name')  

    context = {
        'boqs_grouped': boqs_grouped,
        'projects_firts': projects_firt,
        'boq_cat_types': BoQ_Category_Types
    }

    return render(request, 'boq/boq_list.html', context)


@login_required
def boq_list_details(request, project_name):
    projects_firt_name = ProjectFirstLevelName.objects.all()
    project = get_object_or_404(ProjectFirstLevelName, project_first_name=project_name)
    # Now filter BOQs by project
    boqs = BOQ.objects.filter(project_name=project)

    BoQ_Category = BoQCategory.objects.all()
    context = {
        'boqs': boqs, 
        'projects_firts': project,
        'projects_firt_names': projects_firt_name,
        'BoQ_Categorys': BoQ_Category
    }
    return render(request, 'boq/boq_list_details.html', context)


@login_required
def boq_mate_create(request):
    if request.method == "POST":
        try:
            # Parse the JSON data sent from the frontend
            data = json.loads(request.body)
            boq_data = data.get('data', [])
            category_id = data.get('category', '').strip()
            project_id = data.get('project_id', '')

            # Validate the required fields
            if not boq_data or not category_id or not project_id:
                raise ValueError("Missing required fields (data, category, or project_id).")

            # Get project and category details
            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            category_obj = get_object_or_404(BoQCategory, pk=category_id)

            category_name = category_obj.boq_cat_name
            category_type = category_obj.boq_cat_type

            for item in boq_data:
                qty = float(item.get('qty', 0))
                rate = float(item.get('rate', 0))
                amount = qty * rate

                supplier_id = item.get('sup_name')
                if not supplier_id:
                    raise ValueError("Missing Supplier ID.")
                try:
                    supplier = Suppliers.objects.get(pk=supplier_id)
                except Suppliers.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Supplier with ID {supplier_id} does not exist."
                    })

                # Create form and validate
                form = BOQForm({
                    'project_name': project.id,
                    'category_type': category_type,
                    'category_name': category_name,
                    'supplier_name': supplier.id,
                    'item_name': item.get('item_name', ''),
                    'unit': item.get('unit', ''),
                    'qty': qty,
                    'rate': rate,
                    'amount': amount
                })

                # If form is valid, save it
                if form.is_valid():
                    form.save()
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Form data is invalid: {form.errors}'
                    })

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except ValueError as ve:
            return JsonResponse({'status': 'error', 'message': f"Invalid data: {ve}"})
        except json.JSONDecodeError as json_error:
            return JsonResponse({'status': 'error', 'message': f"Invalid JSON format: {json_error}"})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"})

    else:
        # Handle GET request (render the form)
        form = BOQForm()
        project_id = request.GET.get('project_id')
        category_id = request.GET.get('category')
        suppliers = Suppliers.objects.all()

        context = {
            'form': form,
            'boq_cat_names': [],
            'project_id': project_id,
            'category': category_id,
            'suppliers': suppliers,
            'project_first_name': '',
            'boq_cat_type': ''
        }

        try:
            # Populate context with project and category information
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

        # Render the template with the context
        return render(request, 'boq/boq_form.html', context)


@login_required
def labor_cost_create(request):
    if request.method == "POST":
        try:
            # Parse the JSON data sent from the frontend
            data = json.loads(request.body)
            boq_data = data.get('data', [])
            category_id = data.get('category', '').strip()
            project_id = data.get('project_id', '')

            # Validate the required fields
            if not boq_data or not category_id or not project_id:
                raise ValueError("Missing required fields (data, category, or project_id).")

            # Get project and category details
            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            category_obj = get_object_or_404(BoQCategory, pk=category_id)

            category_name = category_obj.boq_cat_name
            category_type = category_obj.boq_cat_type

            for item in boq_data:
                qty = float(item.get('qty', 0))
                rate = float(item.get('rate', 0))
                amount = qty * rate

                supplier_id = item.get('sup_name')
                if not supplier_id:
                    raise ValueError("Missing supervisor ID.")
                try:
                    supplier = Suppliers.objects.get(pk=supplier_id)
                except Suppliers.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Supplier with ID {supplier_id} does not exist."
                    })

                # Create form and validate
                form = BOQForm({
                    'project_name': project.id,
                    'category_type': category_type,
                    'category_name': category_name,
                    'supplier_name': supplier.id,
                    'item_name': item.get('item_name', ''),
                    'unit': item.get('unit', ''),
                    'qty': qty,
                    'rate': rate,
                    'amount': amount
                })

                # If form is valid, save it
                if form.is_valid():
                    form.save()
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Form data is invalid: {form.errors}'
                    })

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except ValueError as ve:
            return JsonResponse({'status': 'error', 'message': f"Invalid data: {ve}"})
        except json.JSONDecodeError as json_error:
            return JsonResponse({'status': 'error', 'message': f"Invalid JSON format: {json_error}"})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"An error occurred: {str(e)}"})

    else:
        # Handle GET request (render the form)
        form = BOQForm()
        project_id = request.GET.get('project_id')
        category_id = request.GET.get('category')
        suppliers = Suppliers.objects.all()

        context = {
            'form': form,
            'boq_cat_names': [],
            'project_id': project_id,
            'category': category_id,
            'suppliers': suppliers,
            'project_first_name': '',
            'boq_cat_type': ''
        }

        try:
            # Populate context with project and category information
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

        # Render the template with the context
        return render(request, 'boq/boq_labor_form.html', context)
    

@login_required
def boq_edit(request, pk):
    # Fetch the BOQ entry by its primary key (pk)
    boq = get_object_or_404(BOQ, pk=pk)
    
    # If the request method is POST, handle the form submission
    if request.method == 'POST':
        form = BOQForm(request.POST, instance=boq)  # Pre-fill the form with existing data
        if form.is_valid():
            form.save()  # Save the updated BOQ data
            # Show success message and redirect to the BOQ list page
            return redirect('boq_list')  # Or any other page you want after saving
    else:
        form = BOQForm(instance=boq)  # If GET request, just show the form with existing data

    return render(request, 'boq/boq_edit.html', {'form': form, 'boq': boq})


@login_required
def boq_delete(request, pk):
    boq = get_object_or_404(BOQ, pk=pk)    
    boq.delete()
    messages.success(request, 'Deleted successfully!')
    return redirect('boq_list') 


@login_required
def project_boq_details(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(ProjectFirstLevelName, id=project_id)    
    boq_categories = BoQCategory.objects.all()   
    categories = project.boq_set.values_list('category_name', flat=True).distinct()

    # Group BOQ items by category and calculate category totals
    boq_by_category = {}
    for category in categories:
        boq_items = project.boq_set.filter(category_name=category)
        category_total = sum(item.amount for item in boq_items)
        boq_by_category[category] = {
            'items': boq_items,
            'total': category_total
        }

    # Calculate the final total for all BOQ items
    final_total = sum(item.amount for item in project.boq_set.all())
    employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)

    employees = []
    for employee in employee_costs:
        employees.append({
            'employee_name': employee.employee_name,
            'salary': employee.total_salary,
            'first_month_salary': employee.first_month_salary,
            'project_duration_months': employee.project_duration_months,
        })

    employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

    safety_equipment_qs = SafetyEquipment.objects.filter(project_name=project.project_first_name)

    safety_equipments = []
    for item in safety_equipment_qs:
        safety_equipments.append({
            'item_name': item.item_name,
            'item_cost': item.item_cost,
            'quantity': item.quantity,
            'total_cost': item.total_cost,
        })

    safety_equipment_total = safety_equipment_qs.aggregate(total=Sum('total_cost'))['total'] or 0

    expense_cost_tl = ExpenseCost.objects.filter(project_name=project.project_first_name)

    expense_costs = []
    for item in expense_cost_tl:
        expense_costs.append({
            'item_name': item.item_name,
            'item_cost': item.item_cost,
            'quantity': item.quantity,
            'total_cost': item.total_cost,
        })

    expense_cost_total = expense_cost_tl.aggregate(total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total

    # Handle POST: update percentage data
    if request.method == 'POST':
        try:
            percentage = Decimal(request.POST.get('percentage', 0))
            percentage_value = (percentage / Decimal('100')) * grand_total
            final_total_with_extra = grand_total + percentage_value
            project.grand_total = grand_total
            project.percentage = percentage
            project.percentage_value = percentage_value
            project.final_total_with_extra = final_total_with_extra
            project.save()

            messages.success(request, 'Project totals updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating totals: {str(e)}')

        return redirect(f"{request.path}?project_id={project.id}")

    return render(request, 'boq/project_boq_details.html', {
        'project': project,
        'boq_by_category': boq_by_category,
        'final_total': final_total,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'expense_cost_total': expense_cost_total,
        'grand_total': grand_total,
        'employees': employees,
        'safety_equipments': safety_equipments,
        'expense_costs': expense_costs,         
        'boq_categories': boq_categories,
    })



def get_boq_data(project):
    # Get unique categories from this project's BOQ items
    categories = project.boq_set.values_list('category', flat=True).distinct()

    boq_by_category = {}
    for category in categories:
        boq_items = project.boq_set.filter(category_name=category)

        # Calculate total for this category
        category_total = sum(item.amount for item in boq_items)

        boq_by_category[category] = {
            'items': boq_items,
            'total': category_total
        }

    # Final total for all BOQ items under the project
    final_total = sum(item.amount for item in project.boq_set.all())

    return boq_by_category, final_total


@login_required
def boq_pdf_view(request, project_id):
    project = ProjectFirstLevelName.objects.get(id=project_id)
    boq_by_category = {}
    categories = project.boq_set.values_list('category_name', flat=True).distinct()
    for category in categories:
        boq_items = project.boq_set.filter(category_name=category)
        category_total = sum(item.amount for item in boq_items)
        boq_by_category[category] = {
            'items': boq_items,
            'total': category_total
        }
    final_total = sum(item.amount for item in project.boq_set.all())

    # Fetch employee costs
    employee_costs = EmployeeCost.objects.filter(project_name=project.project_first_name)
    employee_cost_total = employee_costs.aggregate(total=Sum('total_salary'))['total'] or 0

    # Fetch safety equipment costs
    safety_equipment = SafetyEquipment.objects.filter(project_name=project.project_first_name)
    safety_equipment_total = safety_equipment.aggregate(total=Sum('total_cost'))['total'] or 0

    # Fetch Expense costs
    expense_costs = ExpenseCost.objects.filter(project_name=project.project_first_name)
    expense_cost_total = expense_costs.aggregate(total=Sum('total_cost'))['total'] or 0

    grand_total = final_total + employee_cost_total + safety_equipment_total + expense_cost_total
    # Prepare context for the PDF template
    context = {
        'project': project,
        'boq_by_category': boq_by_category,
        'grand_total': grand_total,
        'employee_cost_total': employee_cost_total,
        'safety_equipment_total': safety_equipment_total,
        'employee_costs': employee_costs,
        'safety_equipment': safety_equipment,
        'expense_costs': expense_costs,
        'expense_cost_total': expense_cost_total,
    }

    # Render the HTML content using the template
    template_path = 'boq/pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    # Convert HTML to PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="boq_details.pdf"'
        return response
    else:
        return HttpResponse('PDF generation failed')


@login_required
def boq_category_pdf(request):
    project_id = request.GET.get('project_id')
    category_name = request.GET.get('category_name')

    project = get_object_or_404(ProjectFirstLevelName, id=project_id)
    boq_items = BOQ.objects.filter(project_name=project, category_name=category_name)

    total_amount = sum(item.amount for item in boq_items)

    template = get_template('boq/boq_category_pdf.html')
    html = template.render({
        'project': project,
        'category_name': category_name,
        'boq_items': boq_items,
        'total_amount': total_amount,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=BOQ_{category_name}.pdf'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation error')
    return response

# View to list all project first level
@login_required
def first_level_list(request):
    projects = ProjectFirstLevelName.objects.all()
    return render(request, 'firstlevel/first_level_list.html', {'projects': projects})

@login_required
def first_level_add(request):
    if request.method == 'POST':
        start_month = request.POST.get('start_month')  # '4'
        start_year = request.POST.get('start_year')    # '2025'

        request.POST = request.POST.copy()

        if start_month and start_year:
            request.POST['project_start_month'] = int(start_month)

        form = ProjectFirstLevelNameForm(request.POST, request.FILES)

        if form.is_valid():
            project = form.save(commit=False)

            try:
                year = int(start_year)
                month = int(start_month)
                start_date = datetime(year, month, 1).date()
                project.project_start_date = start_date
                print("Project duration:", project.project_duration)
                if project.project_duration:
                    end_raw = start_date + relativedelta(months=project.project_duration)
                    last_day = calendar.monthrange(end_raw.year, end_raw.month)[1]
                    end_date = datetime(end_raw.year, end_raw.month, last_day).date()
                    project.project_end_date = end_date
                    print("Calculated end date:", end_date)
                else:
                    print("[WARNING] Project duration is missing or zero.")

            except Exception as e:
                print(f"[ERROR] Date calculation failed: {e}")
                messages.error(request, "Could not calculate start/end dates.")

            project.save()

            messages.success(request, 'First Level (Project Name) Added successfully!')
            return redirect('first_level_list')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'There was an error adding the First Level. Please try again.')
    else:
        form = ProjectFirstLevelNameForm()

    return render(request, 'firstlevel/first_level_add.html', {'form': form})



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
def create_boq_category(request):
    if request.method == 'POST':
        form = BoQCategoryForm(request.POST)
        if form.is_valid():
            form.save()  # Save the BoQCategory to the database
            return redirect('boq_category_list')  # Redirect to the list view after saving
    else:
        form = BoQCategoryForm()
    
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
        category.delete()
        return redirect('boq_category_list')
    return render(request, 'boq/boq_category_delete.html', {'category': category})




@login_required
def boq_supervisor_list(request):
    supervisor = SiteSupervisor.objects.all()
    return render(request, 'boq/boq_supervisor_list.html', {'supervisors': supervisor})

@login_required
def create_boq_supervisor(request):
    if request.method == 'POST':
        form = SiteSupervisorForm(request.POST)  
        if form.is_valid():
            form.save()
            return redirect('boq_supervisor_list')
    else:
        form = SiteSupervisorForm()

    return render(request, 'boq/create_boq_supervisor.html', {'form': form})


@login_required
def edit_boq_supervisor(request, id):
    supervisor = get_object_or_404(SiteSupervisor, pk=id)
    if request.method == 'POST':
        form = SiteSupervisorForm(request.POST, instance=supervisor)
        if form.is_valid():
            form.save()
            return redirect('boq_supervisor_list')
    else:
        form = SiteSupervisorForm(instance=supervisor)
    return render(request, 'boq/edit_supervisour.html', {'form': form})


@login_required
def delete_boq_supervisor(request, id):
    supervisor = get_object_or_404(SiteSupervisor, pk=id)
    if request.method == 'POST':
        supervisor.delete()
        return redirect('boq_supervisor_list')
    return render(request, 'boq/boq_supervisour_delete.html', {'supervisors': supervisor})


@login_required
def boq_supplier_list(request):
    supplier = Suppliers.objects.all()
    return render(request, 'supplier/boq_supplier_list.html', {'suppliers': supplier})



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
        supplier.delete()
        return redirect('boq_supplier_list')
    return render(request, 'supplier/boq_supplier_delete.html', {'suppliers': supplier})