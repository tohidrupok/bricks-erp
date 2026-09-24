from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Sales,FlatPlot,PropertyFlatPlot,PropertySales,InstallmentPayment,SharePlot,SharePerson,ShareInstallmentPayment
from .forms import SalesForm,FlatPlotForm,PropertyFlatPlotForm,PropertySalesForm,InstallmentPaymentForm,SharePlotForm, SharePersonFormSet,ShareInstallmentPaymentForm
import locale
from projects.models import ProjectFirstLevelName,Donation
from django.contrib import messages
from collections import defaultdict
from crm.models import Customer
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal,InvalidOperation
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.timezone import now
from accounting.models import CashType,CreditVoucher,LedgerEntry,TransactionHistory,HeadOfAccount
from django.db import transaction
import traceback
from purchase.models import HeadOfExpense
from accounting.utils.sms import send_sms


# Set locale to use comma formatting (e.g., 1,000,000)
locale.setlocale(locale.LC_ALL, '')
@login_required
def sales_list(request):
    sales = Sales.objects.all()
    for sale in sales:
        sale.total_amount_fmt = locale.format_string("%.2f", sale.total_amount, grouping=True)
        sale.pay_amount_fmt = locale.format_string("%.2f", sale.pay_amount, grouping=True)
    return render(request, 'sales/sales_list.html', {'sales': sales})


@login_required
def sales_add(request):
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales_list')
    else:
        form = SalesForm()
    return render(request, 'sales/sales_form.html', {'form': form})


@login_required
def sales_edit(request, pk):
    sale = get_object_or_404(Sales, pk=pk)
    if request.method == 'POST':
        form = SalesForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            return redirect('sales_list')
    else:
        form = SalesForm(instance=sale)
    return render(request, 'sales/sales_form.html', {'form': form})


@login_required
def sales_delete(request, pk):
    sale = get_object_or_404(Sales, pk=pk)
    if request.method == 'POST':
        sale.delete()
        return redirect('sales_list')
    return render(request, 'sales/sales_confirm_delete.html', {'sale': sale})



# @login_required
# def flat_plot_summary(request):
#     summary = {}

#     plots = FlatPlot.objects.select_related('project_name').order_by('project_name__project_first_name', 'flat_no', 'unit_no')

#     for plot in plots:
#         project = plot.project_name.project_first_name if plot.project_name else "Unknown"

#         if project not in summary:
#             summary[project] = {
#                 'flats': set(),
#                 'units': set()
#             }

#         summary[project]['flats'].add(plot.flat_no)
#         summary[project]['units'].add(plot.unit_no)

#     for project_data in summary.values():
#         project_data['flats'] = sorted(project_data['flats'])
#         project_data['units'] = sorted(project_data['units'])

#     return render(request, 'sales/flat_plot_summary.html', {'summary': summary})




# @login_required
# def flat_plot_summary(request):
#     summary = {}

#     plots = FlatPlot.objects.select_related('project_name').order_by(
#         'project_name__project_first_name', 'flat_no', 'unit_no'
#     )

#     for plot in plots:
#         project = plot.project_name.project_first_name if plot.project_name else "Unknown"
#         type_label = plot.type.lower()  # 'flat' or 'plot'

#         if project not in summary:
#             summary[project] = {}

#         if type_label not in summary[project]:
#             summary[project][type_label] = {
#                 'flats': defaultdict(set),  # flat_no -> set of unit_no
#                 'units': set(),             # all unique units across type
#             }

#         summary[project][type_label]['flats'][plot.flat_no].add(plot.unit_no)
#         summary[project][type_label]['units'].add(plot.unit_no)

#     # Convert sets to sorted lists and calculate total unit count (including duplicates)
#     for project_data in summary.values():
#         for type_data in project_data.values():
#             type_data['flats'] = {
#                 flat: sorted(units)
#                 for flat, units in sorted(type_data['flats'].items())
#             }
#             type_data['units'] = sorted(type_data['units'])
#             # Sum all unit counts for each flat (including duplicates)
#             type_data['total_units_count'] = sum(len(units) for units in type_data['flats'].values())

#     return render(request, 'sales/flat_plot_summary.html', {'summary': summary})


@login_required
def flat_plot_summary(request):
    summary = {}

    plots = FlatPlot.objects.select_related('project_name').order_by(
        'project_name__project_first_name', 'flat_no', 'unit_no'
    )

    for plot in plots:
        project_obj = plot.project_name  # actual object
        type_label = plot.type.lower()  # 'flat' or 'plot'

        if project_obj not in summary:
            summary[project_obj] = {}

        if type_label not in summary[project_obj]:
            summary[project_obj][type_label] = {
                'flats': defaultdict(set),  # flat_no -> set of unit_no
                'units': set(),
            }

        summary[project_obj][type_label]['flats'][plot.flat_no].add(plot.unit_no)
        summary[project_obj][type_label]['units'].add(plot.unit_no)

    # Convert sets to sorted lists and calculate total unit count
    for project_data in summary.values():
        for type_data in project_data.values():
            type_data['flats'] = {flat: sorted(units) for flat, units in sorted(type_data['flats'].items())}
            type_data['units'] = sorted(type_data['units'])
            type_data['total_units_count'] = sum(len(units) for units in type_data['flats'].values())

    return render(request, 'sales/flat_plot_summary.html', {'summary': summary})
    
    
    
@login_required
def flatplot_project_detail(request, project_id):
    project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
    flatsplots = FlatPlot.objects.filter(project_name=project).order_by('type', 'flat_no', 'unit_no')
    return render(request, 'sales/flatplot_project_detail.html', {
        'project': project,
        'flatsplots': flatsplots
    })
    

@login_required
def flatplot_edit(request, id):
    fp = get_object_or_404(FlatPlot, id=id)

    if request.method == 'POST':
        form = FlatPlotForm(request.POST, instance=fp)
        if form.is_valid():
            form.save()
            return redirect('flat_plot_summary')
    else:
        form = FlatPlotForm(instance=fp)

    return render(request, 'sales/flatplot_edit.html', {'form': form, 'title': 'Edit Flat/Plot'})



@login_required
def flatplot_delete(request, id):
    fp = get_object_or_404(FlatPlot, id=id)
    if request.method == 'POST':
        fp.delete()
        return redirect('flat_plot_summary')
    return render(request, 'sales/flatplot_confirm_delete.html', {'object': fp})
    
    

@login_required
def flat_plot_add(request):
    if request.method == 'POST':
        project_id = request.POST.get('project_name')
        if not project_id:
            messages.error(request, "Please select a project.")
            return redirect('flat_plot_summary')

        project = get_object_or_404(ProjectFirstLevelName, id=project_id)
        selected_units = request.POST.getlist('unit_checkbox')

        if not selected_units:
            messages.error(request, "Please select at least one unit.")
            return redirect('flat_plot_add')

        # Determine the type from the first unit (all should be same type)
        type_label = selected_units[0].split('-')[0]

        # For each selected unit, delete existing record if exists (project, type, flat_no, unit_no)
        for item in selected_units:
            parts = item.split('-')
            unit_type = parts[0]  # "flat" or "plot"
            flat_no = int(parts[1])
            unit_no = int(parts[2])

            # Delete any existing record matching project, type, flat_no, unit_no
            FlatPlot.objects.filter(
                project_name=project,
                type=unit_type,
                flat_no=flat_no,
                unit_no=unit_no
            ).delete()

            # Then create new record
            FlatPlot.objects.create(
                flat_no=flat_no,
                unit_no=unit_no,
                project_name=project,
                type=unit_type
            )

        messages.success(request, f"{type_label.title()} selections saved successfully.")
        return redirect('flat_plot_summary')

    # For checkbox state retention
    saved_units = FlatPlot.objects.all()
    saved_units_set = set(f"{unit.type}-{unit.flat_no}-{unit.unit_no}" for unit in saved_units)

    context = {
        'saved_units': saved_units_set,
        'flat_range': range(1, 2),     
        'unit_range': range(1, 7),
        'plot_range': range(1, 2),
        'flat_number_options': range(1, 21),  
        'project_names': ProjectFirstLevelName.objects.all(),
    }
    return render(request, 'sales/flat_plot_add.html', context)




@login_required
def share_plot_add(request):
    if request.method == "POST":
        form = SharePlotForm(request.POST)
        formset = SharePersonFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            share_plot = form.save()
            formset.instance = share_plot
            formset.save()
            messages.success(request, "Share Plot record added successfully!")
            return redirect("share_plot_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SharePlotForm()
        formset = SharePersonFormSet()

    return render(request, "sales/sharePlotAdd.html", {
        "form": form,
        "formset": formset,
    })



@login_required
def share_installment_list(request):
    installments = ShareInstallmentPayment.objects.all()
    return render(request, "sales/share_installment_list.html", {"installments": installments})



@login_required
def sharePlotList(request):
    plots = SharePlot.objects.prefetch_related("persons").all()
    return render(request, "sales/sharePlotList.html", {"plots": plots})
    
    

@login_required
def delete_share_plot(request, pk):
    plot = get_object_or_404(SharePlot, pk=pk)

    if request.method == "POST":
        plot.delete()  # This will also delete related SharePerson records (CASCADE)
        return redirect("share_plot_list")  # Change this to your list page name

    return render(request, "sales/share_plot_delete.html", {"plot": plot})




from django.utils import timezone
from num2words import num2words

@login_required
def share_plot_pdf(request, pk):
    share_plot = get_object_or_404(SharePlot, pk=pk)
    
    # Convert total value to words
    amount_in_words = num2words(share_plot.value, to='currency', lang='en').title()
    
    context = {
        'share_plot': share_plot,
        'amount_in_words': amount_in_words,
        'print_time': timezone.now(),
    }
    return render(request, 'sales/share_plot_pdf.html', context)


# @login_required
# def share_plot_add(request):
#     if request.method == 'POST':
#         project_id = request.POST.get('project_name')
#         if not project_id:
#             messages.error(request, "Please select a project.")
#             return redirect('flat_plot_summary')

#         project = get_object_or_404(ProjectFirstLevelName, id=project_id)
#         selected_units = request.POST.getlist('unit_checkbox')

#         if not selected_units:
#             messages.error(request, "Please select at least one unit.")
#             return redirect('flat_plot_add')

#         # Determine the type from the first unit (all should be same type)
#         type_label = selected_units[0].split('-')[0]

#         # For each selected unit, delete existing record if exists (project, type, flat_no, unit_no)
#         for item in selected_units:
#             parts = item.split('-')
#             unit_type = parts[0]  # "flat" or "plot"
#             flat_no = int(parts[1])
#             unit_no = int(parts[2])

#             # Delete any existing record matching project, type, flat_no, unit_no
#             FlatPlot.objects.filter(
#                 project_name=project,
#                 type=unit_type,
#                 flat_no=flat_no,
#                 unit_no=unit_no
#             ).delete()

#             # Then create new record
#             FlatPlot.objects.create(
#                 flat_no=flat_no,
#                 unit_no=unit_no,
#                 project_name=project,
#                 type=unit_type
#             )

#         messages.success(request, f"{type_label.title()} selections saved successfully.")
#         return redirect('flat_plot_summary')

#     # For checkbox state retention
#     saved_units = FlatPlot.objects.all()
#     saved_units_set = set(f"{unit.type}-{unit.flat_no}-{unit.unit_no}" for unit in saved_units)

#     context = {
#         'saved_units': saved_units_set,
#         'flat_range': range(1, 2),     
#         'unit_range': range(1, 7),
#         'plot_range': range(1, 2),
#         'flat_number_options': range(1, 21),  
#         'project_names': ProjectFirstLevelName.objects.all(),
#     }
#     return render(request, 'sales/sharePlotAdd.html', context)
    
    
    

@login_required
def share_plot_list(request):
    plots = PropertyFlatPlot.objects.select_related('project_name').order_by('project_name', 'flat_no', 'unit_no')
    return render(request, 'sales/share_plot_list.html', {'plots': plots})
    
    
    


@login_required
def flat_plot_property_list(request):
    plots = PropertyFlatPlot.objects.select_related('project_name').order_by('project_name', 'flat_no', 'unit_no')
    return render(request, 'sales/flat_plot_property_list.html', {'plots': plots})


@login_required
def property_edit(request, id):
    prop = get_object_or_404(PropertyFlatPlot, id=id)

    if request.method == 'POST':
        form = PropertyFlatPlotForm(request.POST, instance=prop)
        if form.is_valid():
            form.save()
            return redirect('flat_plot_property_list')
    else:
        form = PropertyFlatPlotForm(instance=prop)

    return render(request, 'sales/flat_plot_property_edit.html', {
        'form': form,
        'prop': prop
    })


@login_required
def property_delete(request, id):
    prop = get_object_or_404(PropertyFlatPlot, id=id)

    if request.method == "POST":
        prop.delete()
        return redirect('flat_plot_property_list')

    return render(request, 'sales/flat_plot_property_delete.html', {'prop': prop})
    
    

@login_required
def flat_plot_property_add(request):
    project_id = request.GET.get('project_name') or request.POST.get('project_name')
    unit_type = request.GET.get('type') or request.POST.get('type')

    project = None
    plots = []

    if project_id and unit_type:
        try:
            project = ProjectFirstLevelName.objects.get(id=project_id)
            # ✅ Filter only plots with Pending status
            plots = FlatPlot.objects.filter(project_name=project, type=unit_type, status='Pending')
        except ProjectFirstLevelName.DoesNotExist:
            messages.error(request, "Selected project does not exist.")

    if request.method == 'POST' and 'save_properties' in request.POST:
        for plot in plots:
            flat_no = plot.flat_no
            unit_no = plot.unit_no

            property_name = request.POST.get(f'property_name_{plot.id}', '').strip()
            property_code = request.POST.get(f'property_code_{plot.id}', '').strip()
            square_fit = request.POST.get(f'square_fit_{plot.id}', '').strip()
            per_square_rate = request.POST.get(f'per_square_rate_{plot.id}', '').strip()
            total_amount = request.POST.get(f'total_amount_{plot.id}', '').strip()
            details = request.POST.get(f'details_{plot.id}', '').strip()
            status = request.POST.get(f'status_{plot.id}', 'Pending')

            # ✅ Check if any actual data is filled in the row
            if any([property_name, property_code, square_fit, per_square_rate, total_amount, details]):
                try:
                    square_fit = float(square_fit) if square_fit else 0
                except ValueError:
                    square_fit = 0

                try:
                    per_square_rate = float(per_square_rate) if per_square_rate else 0
                except ValueError:
                    per_square_rate = 0

                try:
                    total_amount = float(total_amount) if total_amount else 0
                except ValueError:
                    total_amount = 0

                # ✅ Delete any existing data for this flat/unit/type
                PropertyFlatPlot.objects.filter(
                    project_name=project,
                    flat_no=flat_no,
                    unit_no=unit_no,
                    type=unit_type
                ).delete()

                # ✅ Save only non-empty rows
                PropertyFlatPlot.objects.create(
                    project_name=project,
                    flat_no=flat_no,
                    unit_no=unit_no,
                    type=unit_type,
                    property_name=property_name,
                    property_code=property_code,
                    square_fit=square_fit,
                    per_square_rate=per_square_rate,
                    total_amount=total_amount,
                    details=details,
                    status='Not Sold'
                )

                # ✅ Update FlatPlot status to "Done" only for saved ones
                plot.status = 'Done'
                plot.save()

        messages.success(request, "Only filled-in properties were saved successfully.")
        return redirect('flat_plot_property_add')

    context = {
        'project_names': ProjectFirstLevelName.objects.all(),
        'plots': plots,  # Only pending plots shown
        'selected_project_id': int(project_id) if project_id else '',
        'selected_type': unit_type if unit_type else '',
    }
    return render(request, 'sales/flat_plot_property_add.html', context)




@login_required
def flat_plot_sales(request):
    plots = PropertySales.objects.all()
    return render(request, 'sales/flat_plot_sales.html', {'plots': plots})


# @login_required
# def property_sales_report(request, id):
#     sale = get_object_or_404(PropertySales, id=id)

#     return render(request, 'sales/property_sales_report.html', {
#         'sale': sale,
#         "print_time": timezone.now(),
#     })
    

@login_required
def property_sales_report(request, id):
    sale = get_object_or_404(PropertySales, id=id)

    # Calculate Final Amount
    final_amount = (
        (sale.total_amount or 0) +
        (sale.utility or 0) +
        (sale.parking or 0)
    )

    context = {
        "sale": sale,
        "final_amount": final_amount,
        "print_time": timezone.now(),
    }
    return render(request, "sales/property_sales_report.html", context)
    
    

@login_required
def edit_property_sale(request, sales_id):
    prop = get_object_or_404(PropertySales, id=sales_id)
    if request.method == "POST":
        form = PropertySalesForm(request.POST, instance=prop)
        if form.is_valid():
            form.save()
            return redirect('flat_plot_sales')
    else:
        form = PropertySalesForm(instance=prop)
    return render(request, 'sales/edit_property_sale.html', {'form': form, 'prop': prop})


@login_required
def delete_property_sale(request, sales_id):
    prop = get_object_or_404(PropertySales, id=sales_id)
    if request.method == "POST":
        prop.delete()
        return redirect('flat_plot_sales')
    return render(request, 'sales/delete_property_sale.html', {'prop': prop})


@login_required
def sales_lilahetalah_list(request):
    lilahetalahs = PropertySales.objects.filter(
        lilahetalah_percent__gt=0,
        lilahetalah_amount__gt=0
    )
    return render(request, 'sales/sales_lilahetalah_list.html', {'lilahetalahs': lilahetalahs})



@login_required
def sales_commission_list(request):
    plots = PropertySales.objects.filter(media_persion__isnull=False)
    return render(request, 'sales/sales_commission_list.html', {'plots': plots})

    
       
    


@login_required 
def flat_plot_sales_add(request):
    project_id = request.GET.get('project_name') or request.POST.get('project_name')
    selected_property_id = request.GET.get('property_id') or request.POST.get('property_id')
    selected_customer_id = request.GET.get('customer_id') or request.POST.get('customer_id')
    selected_donation_id = request.GET.get('donaton_name') or request.POST.get('donaton_name')


    project = None
    properties = PropertyFlatPlot.objects.none()
    customers = Customer.objects.none()
    plots = PropertyFlatPlot.objects.none()
    selected_customer = None
    donations = Donation.objects.all()
    

    # Get selected project
    if project_id:
        try:
            project = ProjectFirstLevelName.objects.get(id=project_id)
        except ProjectFirstLevelName.DoesNotExist:
            messages.error(request, "Selected project does not exist.")
            project = None

    # Fetch properties and customers for project (Not Sold only)
    # if project:
    #     properties = PropertyFlatPlot.objects.filter(
    #         project_name=project,
    #         status='Not Sold'
    #     ).order_by('type', 'flat_no', 'unit_no')
    #     customers = Customer.objects.filter(project=project, status=True)
    
    if project:
        properties = PropertyFlatPlot.objects.filter(
            project_name=project,
            status__in=['Pending', 'Not Sold']
        ).order_by('type', 'flat_no', 'unit_no')
        customers = Customer.objects.filter(status=True)

        if selected_property_id:
            plots = properties.filter(id=selected_property_id)
        else:
            plots = properties

    # Get selected customer object if any
    if selected_customer_id:
        try:
            selected_customer = Customer.objects.get(id=selected_customer_id)
        except Customer.DoesNotExist:
            selected_customer = None

    # Handle save request for properties and sales
    if request.method == 'POST':
        if 'save_properties' in request.POST:
            # Update PropertyFlatPlot fields
            for prop in plots:
                property_name = request.POST.get(f'property_name_{prop.id}', '').strip()
                property_code = request.POST.get(f'property_code_{prop.id}', '').strip()
                square_fit = request.POST.get(f'square_fit_{prop.id}', '').strip()
                per_square_rate = request.POST.get(f'per_square_rate_{prop.id}', '').strip()
                total_amount = request.POST.get(f'total_amount_{prop.id}', '').strip()
                details = request.POST.get(f'details_{prop.id}', '').strip()

                prop.property_name = property_name or None
                prop.property_code = property_code or None
                prop.details = details or None
                prop.status = 'Not Sold'

                try:
                    prop.square_fit = float(square_fit) if square_fit else None
                except ValueError:
                    prop.square_fit = None

                try:
                    prop.per_square_rate = float(per_square_rate) if per_square_rate else None
                except ValueError:
                    prop.per_square_rate = None

                try:
                    prop.total_amount = float(total_amount) if total_amount else None
                except ValueError:
                    prop.total_amount = None

                prop.save()

            messages.success(request, "Property updated successfully.")
            return redirect(
                f"{reverse('flat_plot_sales_add')}?project_name={project_id}&property_id={selected_property_id or ''}&customer_id={selected_customer_id or ''}"
            )

        elif 'save_sales' in request.POST:
            # Get form values
            utility = request.POST.get('utility', '0').strip()
            parking = request.POST.get('parking', '0').strip()
            discount_percent = request.POST.get('discount_percent', '0').strip()
            discount = request.POST.get('discount', '0').strip()
            media_persion_id = request.POST.get('media_persion', '').strip() or None
            commisoin_percent = request.POST.get('commisoin_percent', '0').strip()
            media_commisoin = request.POST.get('media_commisoin', '0').strip()
            donaton_name = request.POST.get('donaton_name', '0').strip()
            lilahetalah_percent = request.POST.get('lilahetalah_percent', '0').strip()
            lilahetalah_amount = request.POST.get('lilahetalah_amount', '0').strip()
            description = request.POST.get('description', '').strip()
            sales_date = request.POST.get('sales_date', '').strip()
            sales_amount = request.POST.get('sales_amount', '0').strip()

            # Convert safely to numbers
            def to_float(val):
                try:
                    return float(val) if val else 0
                except ValueError:
                    return 0

            utility = to_float(utility)
            parking = to_float(parking)
            discount_percent = to_float(discount_percent)
            discount = to_float(discount)
            commisoin_percent = to_float(commisoin_percent)
            media_commisoin = to_float(media_commisoin)
            donaton_name = to_float(donaton_name)
            lilahetalah_percent = to_float(lilahetalah_percent)
            lilahetalah_amount = to_float(lilahetalah_amount)
            sales_amount = to_float(sales_amount)

            # Parse date
            try:
                sales_date = datetime.strptime(sales_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                sales_date = None

            # Get media person object
            media_persion = None
            if media_persion_id:
                media_persion = Customer.objects.filter(pk=media_persion_id).first()
                
            donation_obj = None
            if donaton_name:
                try:
                    donation_obj = HeadOfExpense.objects.get(id=int(donaton_name))
                except (HeadOfExpense.DoesNotExist, ValueError):
                    donation_obj = None

            for prop in plots:
                PropertySales.objects.create(
                    project_name=project,
                    type=prop.type,
                    flat_no=prop.flat_no,
                    unit_no=prop.unit_no,
                    property_name=prop.property_name,
                    property_code=prop.property_code,
                    square_fit=prop.square_fit,
                    per_square_rate=prop.per_square_rate,
                    total_amount=prop.total_amount,
                    customer_name=selected_customer,
                    utility=utility,
                    parking=parking,
                    discount_percent=discount_percent,
                    discount=discount,
                    media_persion=media_persion,
                    commisoin_percent=commisoin_percent,
                    media_commisoin=media_commisoin,
                    donaton_name=donation_obj,
                    lilahetalah_percent=lilahetalah_percent,
                    lilahetalah_amount=lilahetalah_amount,
                    sales_amount=sales_amount,
                    details=description,
                    sales_date=sales_date
                )

                prop.status = 'Sold'
                prop.save()


            messages.success(request, "Property sales record(s) saved successfully.")
            return redirect(
                f"{reverse('flat_plot_sales')}?project_name={project_id}&property_id={selected_property_id or ''}&customer_id={selected_customer_id or ''}"
            )

    total_amount = sum(plot.total_amount or 0 for plot in plots)
    context = {
        'project_names': ProjectFirstLevelName.objects.all(),
        'properties': properties,
        'selected_project_id': int(project_id) if project_id else None,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'customers': customers,
        'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
        'donations': donations,
        'selected_donation_id': int(selected_donation_id) if selected_donation_id else None,  # <-- use defined variable
        'plots': plots,
        'selected_customer': selected_customer,
        'total_amount': total_amount,
        'today': date.today(),
    }

    return render(request, 'sales/flat_plot_sales_add.html', context)




# @login_required
# def flat_plot_installment_management(request):
#     selected_customer_id = request.GET.get('customer_id')
#     selected_property_id = request.GET.get('property_id')

#     # Distinct customers list
#     customers_qs = (
#         PropertySales.objects.filter(customer_name__isnull=False)
#         .values('customer_name__id', 'customer_name__customer_name')
#         .distinct()
#     )
#     customers = [
#         {'id': c['customer_name__id'], 'customer_name': c['customer_name__customer_name']}
#         for c in customers_qs
#     ]

#     plots = PropertySales.objects.none()

#     if request.method == 'POST':
#         property_sales_id = request.POST.get('property_sales_id')
#         project_id = request.POST.get('project_id')
#         customer_id = request.POST.get('customer_id')
#         sales_amount = request.POST.get('sales_amount')

#         payment_types = request.POST.getlist('payment_type[]')
#         months = request.POST.getlist('month[]')
#         amounts = request.POST.getlist('amount[]')
#         cheque_posteds = request.POST.getlist('cheque_posted[]')  # "on" values only if checked
#         cheque_dates = request.POST.getlist('cheque_posted_date[]')
#         cheque_nos = request.POST.getlist('cheque_no[]')

#         def safe_decimal(value, default='0.00'):
#             try:
#                 if not value:
#                     return Decimal(default)
#                 return Decimal(str(value))
#             except (InvalidOperation, ValueError):
#                 return Decimal(default)

#         total_rows = len(payment_types)

#         if not property_sales_id or total_rows == 0:
#             messages.error(request, "Please fill all required fields in the installment payment form.")
#             return redirect(request.path_info)

#         for i in range(total_rows):
#             if not payment_types[i] or not months[i] or not amounts[i]:
#                 messages.error(request, f"Missing required fields in row {i+1}.")
#                 return redirect(request.path_info)

#             try:
#                 month = datetime.strptime(months[i] + "-01", "%Y-%m-%d").date()
#             except ValueError:
#                 messages.error(request, f"Invalid month format in row {i+1}.")
#                 return redirect(request.path_info)
            
#             cheque_posted = (i < len(cheque_posteds) and cheque_posteds[i] == 'on')

#             cheque_date = None
#             if cheque_posted:
#                 if i < len(cheque_dates) and cheque_dates[i]:
#                     try:
#                         cheque_date = datetime.strptime(cheque_dates[i], "%Y-%m-%d").date()
#                     except ValueError:
#                         messages.error(request, f"Invalid cheque date format in row {i+1}.")
#                         return redirect(request.path_info)
#                 else:
#                     cheque_date = date.today()
        

#             InstallmentPayment.objects.create(
#                 project_name_id=project_id,
#                 customer_name_id=customer_id,
#                 property_sales_id=property_sales_id,
#                 sales_amount=safe_decimal(sales_amount),
#                 payment_type=payment_types[i],
#                 month=month,
#                 amount=safe_decimal(amounts[i]),
#                 cheque_posted=cheque_posted,
#                 cheque_date=cheque_date,
#                 cheque_no=cheque_nos[i] if i < len(cheque_nos) else '',
#                 pay_status='Pending',
#             )

#         # Mark the sale as Done
#         PropertySales.objects.filter(id=property_sales_id).update(status='Done')

#         messages.success(request, "Installment payments saved successfully and status updated to Done.")
#         return redirect(f"/dashboard/flat-plot-sales/installment?customer_id={customer_id}")

#     # Fetch plots for dropdown/table
#     if selected_customer_id:
#         plots = PropertySales.objects.filter(customer_name_id=selected_customer_id).order_by('type', 'flat_no', 'unit_no')
#         if selected_property_id:
#             plots = plots.filter(id=selected_property_id)
            

#     form = InstallmentPaymentForm()
#     context = {
#         'today': date.today(),
#         'customers': customers,
#         'plots': plots,
#         'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
#         'selected_property_id': int(selected_property_id) if selected_property_id else None,
#         'form': form,  # pass the form instance here
#     }
#     return render(request, 'sales/flat_plot_installment_management.html', context)
    
    


# @login_required
# def flat_plot_installment_management(request):
#     selected_customer_id = request.GET.get('customer_id')
#     selected_property_id = request.GET.get('property_id')

#     # Distinct customers list
#     customers_qs = (
#         PropertySales.objects.filter(customer_name__isnull=False)
#         .values('customer_name__id', 'customer_name__customer_name')
#         .distinct()
#     )
#     customers = [
#         {'id': c['customer_name__id'], 'customer_name': c['customer_name__customer_name']}
#         for c in customers_qs
#     ]

#     plots = PropertySales.objects.none()

#     if request.method == 'POST':
#         property_sales_id = request.POST.get('property_sales_id')
#         project_id = request.POST.get('project_id')
#         customer_id = request.POST.get('customer_id')
#         sales_amount = request.POST.get('sales_amount')

#         # Lists from the POST data
#         payment_types = request.POST.getlist('payment_type[]')
#         months = request.POST.getlist('month[]')
#         amounts = request.POST.getlist('amount[]')
#         cheque_posteds = request.POST.getlist('cheque_posted[]')
#         cheque_dates = request.POST.getlist('cheque_posted_date[]')
#         cheque_nos = request.POST.getlist('cheque_no[]')
#         cash_types = request.POST.getlist('cash_type[]')
#         pay_notes = request.POST.getlist('pay_note[]')

#         def safe_decimal(value, default='0.00'):
#             try:
#                 if not value:
#                     return Decimal(default)
#                 return Decimal(str(value))
#             except (InvalidOperation, ValueError):
#                 return Decimal(default)

#         total_rows = len(payment_types)

#         if not property_sales_id or total_rows == 0:
#             messages.error(request, "Please fill all required fields in the installment payment form.")
#             return redirect(request.path_info)

#         for i in range(total_rows):
#             if not payment_types[i] or not months[i] or not amounts[i]:
#                 messages.error(request, f"Missing required fields in row {i+1}.")
#                 return redirect(request.path_info)

#             # Parse month safely
#             try:
#                 month = datetime.strptime(months[i] + "-01", "%Y-%m-%d").date()
#             except ValueError:
#                 messages.error(request, f"Invalid month format in row {i+1}.")
#                 return redirect(request.path_info)

#             # Cheque posted logic
#             cheque_posted = (i < len(cheque_posteds) and cheque_posteds[i] == 'on')

#             cheque_date = None
#             if cheque_posted:
#                 if i < len(cheque_dates) and cheque_dates[i]:
#                     try:
#                         cheque_date = datetime.strptime(cheque_dates[i], "%Y-%m-%d").date()
#                     except ValueError:
#                         messages.error(request, f"Invalid cheque date format in row {i+1}.")
#                         return redirect(request.path_info)
#                 else:
#                     cheque_date = date.today()

#             # Safe cash_type and pay_note
#             cash_type_id = cash_types[i] if i < len(cash_types) else None
#             pay_note = pay_notes[i] if i < len(pay_notes) else ""

#             # Create InstallmentPayment entry
#             InstallmentPayment.objects.create(
#                 project_name_id=project_id,
#                 customer_name_id=customer_id,
#                 property_sales_id=property_sales_id,
#                 sales_amount=safe_decimal(sales_amount),
#                 payment_type=payment_types[i],
#                 month=month,
#                 amount=safe_decimal(amounts[i]),
#                 cheque_posted=cheque_posted,
#                 cheque_date=cheque_date,
#                 cheque_no=cheque_nos[i] if i < len(cheque_nos) else '',
#                 cash_type_id=cash_type_id,
#                 pay_note=pay_note,
#                 pay_status='Pending',
#             )

#         # Mark the sale as Done
#         PropertySales.objects.filter(id=property_sales_id).update(status='Done')

#         messages.success(request, "Installment payments saved successfully and status updated to Done.")
#         return redirect(f"/dashboard/flat-plot-sales/installment?customer_id={customer_id}")

#     # --- Fetch plots ---
#     if selected_customer_id:
#         plots = PropertySales.objects.filter(customer_name_id=selected_customer_id).order_by('type', 'flat_no', 'unit_no')
#         if selected_property_id:
#             plots = plots.filter(id=selected_property_id)

#     form = InstallmentPaymentForm()
#     context = {
#         'today': date.today(),
#         'customers': customers,
#         'plots': plots,
#         'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
#         'selected_property_id': int(selected_property_id) if selected_property_id else None,
#         'form': form,
#     }
#     return render(request, 'sales/flat_plot_installment_management.html', context)




@login_required
def flat_plot_installment_management(request):
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
        # 🔍 DEBUG: echo full POST data
        print("POST DATA:", dict(request.POST))
    
        property_sales_id = request.POST.get('property_sales_id')
        project_id = request.POST.get('project_id')
        customer_id = request.POST.get('customer_id')
        sales_amount = request.POST.get('sales_amount')
    
        payment_types = request.POST.getlist('payment_type[]')
        months = request.POST.getlist('month[]')
        amounts = request.POST.getlist('amount[]')
    
        cheque_posteds = request.POST.getlist('cheque_posted[]')
        cheque_dates = request.POST.getlist('cheque_posted_date[]')
        cheque_nos = request.POST.getlist('cheque_no[]')
        cash_types = request.POST.getlist('cash_type[]')
        pay_notes = request.POST.getlist('pay_note[]')
    
        # 🔍 DEBUG: echo key values
        debug_msg = (
            f"property_sales_id={property_sales_id}, "
            f"payment_types={payment_types}, "
            f"months={months}, "
            f"amounts={amounts}"
        )
        print(debug_msg)
    
        if not property_sales_id:
            messages.error(request, "DEBUG: property_sales_id is missing")
            return redirect(request.path_info)
    
        if not payment_types:
            messages.error(request, "DEBUG: payment_type[] not received from form")
            return redirect(request.path_info)
    
        if not months:
            messages.error(request, "DEBUG: month[] not received from form")
            return redirect(request.path_info)
    
        if not amounts:
            messages.error(request, "DEBUG: amount[] not received from form")
            return redirect(request.path_info)
    
        total_rows = len(payment_types)
    
        for i in range(total_rows):
            missing = []
    
            if not payment_types[i]:
                missing.append("payment_type")
            if i >= len(months) or not months[i]:
                missing.append("month")
            if i >= len(amounts) or not amounts[i]:
                missing.append("amount")
    
            if missing:
                messages.error(
                    request,
                    f"DEBUG: Row {i+1} missing fields: {', '.join(missing)}"
                )
                return redirect(request.path_info)
    
            try:
                month = datetime.strptime(months[i] + "-01", "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, f"DEBUG: Invalid month format in row {i+1}")
                return redirect(request.path_info)
    
            cheque_posted = i < len(cheque_posteds) and cheque_posteds[i] == 'on'
    
            cheque_date = None
            if cheque_posted:
                if i < len(cheque_dates) and cheque_dates[i]:
                    try:
                        cheque_date = datetime.strptime(
                            cheque_dates[i], "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        messages.error(request, f"DEBUG: Invalid cheque date in row {i+1}")
                        return redirect(request.path_info)
                else:
                    cheque_date = date.today()
    
            InstallmentPayment.objects.create(
                project_name_id=project_id,
                customer_name_id=customer_id,
                property_sales_id=property_sales_id,
                sales_amount=sales_amount or 0,
                payment_type=payment_types[i],
                month=month,
                amount=amounts[i],
                cheque_posted=cheque_posted,
                cheque_date=cheque_date,
                mr_or_bill_no=None,
                cheque_no=cheque_nos[i] if i < len(cheque_nos) else '',
                cash_type_id=cash_types[i] if i < len(cash_types) else None,
                pay_note=pay_notes[i] if i < len(pay_notes) else '',
                pay_status='Pending',
            )
    
        PropertySales.objects.filter(id=property_sales_id).update(status='Done')
    
        messages.success(request, "Installment payments saved successfully.")
        return redirect(f"/dashboard/flat-plot-sales/installment?customer_id={customer_id}")


    # --- Fetch plots ---
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
        'form': form,
    }
    return render(request, 'sales/flat_plot_installment_management.html', context)
    
    


@login_required
def installment_payment_edit(request, pk):
    installment = get_object_or_404(InstallmentPayment, pk=pk)

    if request.method == 'POST':
        form = InstallmentPaymentForm(request.POST, instance=installment)
        if form.is_valid():
            form.save()
            return redirect('flat_plot_sales')  # change to your listing page
    else:
        form = InstallmentPaymentForm(instance=installment)

    return render(request, 'sales/installment_payment_edit.html', {'form': form, 'installment': installment})
    
    
    

@login_required
def installment_payment_delete(request, pk):
    installment = get_object_or_404(InstallmentPayment, pk=pk)

    if request.method == 'POST':
        installment.delete()
        return redirect('flat_plot_sales')  # redirect to your listing page

    return render(request, 'sales/installment_payment_delete.html', {'installment': installment})
    
    
    



# @login_required
# def share_installment_management(request):
#     selected_customer_id = request.GET.get("customer_id")
#     selected_property_id = request.GET.get("property_id")

#     customers = SharePerson.objects.all()
#     plots = []

#     if selected_customer_id:
#         plots = SharePlot.objects.filter(persons__id=selected_customer_id).distinct()

#     if request.method == "POST":
#         try:
#             with transaction.atomic():
#                 share_sales_sl = request.POST.get("share_sales")
#                 project_id = request.POST.get("project_id")
#                 customer_id = request.POST.get("customer_id")

#                 if not share_sales_sl or not str(share_sales_sl).isdigit():
#                     messages.error(request, "Invalid plot selected.")
#                     return redirect(request.path)

#                 share_sales_sl = int(share_sales_sl)

#                 project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
#                 customer = get_object_or_404(SharePerson, pk=customer_id)
#                 share_sales = get_object_or_404(SharePlot, sl=share_sales_sl)

#                 payment_types = request.POST.getlist("payment_type[]")
#                 months = request.POST.getlist("month[]")
#                 amounts = request.POST.getlist("amount[]")
#                 cheque_posted_list = request.POST.getlist("cheque_posted[]")
#                 cheque_posted_dates = request.POST.getlist("cheque_posted_date[]")
#                 cheque_nos = request.POST.getlist("cheque_no[]")
#                 cash_type_ids = request.POST.getlist("cash_type_id[]")

#                 for i in range(len(payment_types)):
#                     month_value = months[i].strip()
#                     if len(month_value) == 7:
#                         month_value += "-01"
#                     try:
#                         amount_value = Decimal(amounts[i])
#                     except:
#                         amount_value = Decimal("0")

#                     cheque_posted = cheque_posted_list[i] == "on" if i < len(cheque_posted_list) else False
#                     cheque_date = cheque_posted_dates[i] if (cheque_posted and i < len(cheque_posted_dates)) else None
#                     cheque_no = cheque_nos[i] if i < len(cheque_nos) else None
#                     cash_type = get_object_or_404(CashType, pk=cash_type_ids[i]) if i < len(cash_type_ids) else None

#                     ShareInstallmentPayment.objects.create(
#                         project_name=project,
#                         customer_name=customer,
#                         share_sales=share_sales,
#                         sales_amount=share_sales.value,
#                         payment_type=payment_types[i],
#                         month=month_value,
#                         amount=amount_value,
#                         cheque_posted=cheque_posted,
#                         cheque_date=cheque_date,
#                         cheque_no=cheque_no,
#                         cash_type=cash_type,
#                         pay_status="Pending",
#                     )

#                 messages.success(request, "Installments saved successfully!")
#                 return redirect(request.path + f"?customer_id={customer_id}&property_id={share_sales_sl}")

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"Error saving data: {str(e)}")

#     context = {
#         "customers": customers,
#         "plots": plots,
#         "ShareInstallmentPayment": ShareInstallmentPayment,
#         "selected_customer_id": int(selected_customer_id) if selected_customer_id else None,
#         "selected_property_id": int(selected_property_id) if selected_property_id else None,
#         "cash_types": CashType.objects.all(),
#         "today": timezone.now().date(),
#     }
#     return render(request, "sales/sales_plot_installment_management.html", context)




@login_required
def share_installment_management(request):
    selected_customer_id = request.GET.get("customer_id")
    selected_property_id = request.GET.get("property_id")

    customers = SharePerson.objects.all()
    plots = []

    if selected_customer_id:
        plots = SharePlot.objects.filter(persons__id=selected_customer_id).distinct()

    if request.method == "POST":
        try:
            with transaction.atomic():
                share_sales_sl = request.POST.get("share_sales")
                project_id = request.POST.get("project_id")
                customer_id = request.POST.get("customer_id")

                if not share_sales_sl or not str(share_sales_sl).isdigit():
                    messages.error(request, "Invalid plot selected.")
                    return redirect(request.path)

                share_sales_sl = int(share_sales_sl)

                project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
                customer = get_object_or_404(SharePerson, pk=customer_id)
                share_sales = get_object_or_404(SharePlot, sl=share_sales_sl)

                payment_types = request.POST.getlist("payment_type[]")
                months = request.POST.getlist("month[]")
                amounts = request.POST.getlist("amount[]")
                cheque_posted_list = request.POST.getlist("cheque_posted[]")
                cheque_posted_dates = request.POST.getlist("cheque_posted_date[]")
                cheque_nos = request.POST.getlist("cheque_no[]")
                cash_type_ids = request.POST.getlist("cash_type_id[]")

                for i in range(len(payment_types)):
                    month_value = months[i].strip()
                    if len(month_value) == 7:
                        month_value += "-01"
                    try:
                        amount_value = Decimal(amounts[i])
                    except:
                        amount_value = Decimal("0")

                    cheque_posted = cheque_posted_list[i] == "on" if i < len(cheque_posted_list) else False
                    cheque_date = cheque_posted_dates[i] if (cheque_posted and i < len(cheque_posted_dates)) else None
                    cheque_no = cheque_nos[i] if i < len(cheque_nos) else None
                    cash_type = get_object_or_404(CashType, pk=cash_type_ids[i]) if i < len(cash_type_ids) else None

                    ShareInstallmentPayment.objects.create(
                        project_name=project,
                        customer_name=customer,
                        share_sales=share_sales,
                        sales_amount=share_sales.value,
                        payment_type=payment_types[i],
                        month=month_value,
                        amount=amount_value,
                        cheque_posted=cheque_posted,
                        cheque_date=cheque_date,
                        cheque_no=cheque_no,
                        cash_type=cash_type,
                        pay_status="Pending",
                    )
                    
                customer.pay_status = "Done"
                customer.save(update_fields=["pay_status"])

                messages.success(request, "Installments saved successfully!")
                return redirect(request.path + f"?customer_id={customer_id}&property_id={share_sales_sl}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error saving data: {str(e)}")

    context = {
        "customers": customers,
        "plots": plots,
        "ShareInstallmentPayment": ShareInstallmentPayment,
        "selected_customer_id": int(selected_customer_id) if selected_customer_id else None,
        "selected_property_id": int(selected_property_id) if selected_property_id else None,
        "cash_types": CashType.objects.all(),
        "today": timezone.now().date(),
    }
    return render(request, "sales/sales_plot_installment_management.html", context)
    
    


# @csrf_exempt
# @login_required
# def update_pay_status(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             sl = data.get("sl")
#             status = data.get("status")

#             installment = ShareInstallmentPayment.objects.get(sl=sl)
#             installment.pay_status = status
#             installment.save()

#             return JsonResponse({"success": True, "sl": sl, "new_status": status})
#         except Exception as e:
#             return JsonResponse({"success": False, "error": str(e)})
#     return JsonResponse({"success": False, "error": "Invalid request"})



import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction

@csrf_exempt
@login_required
def update_pay_status(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        data = json.loads(request.body)
        sl = data.get("sl")
        new_status = data.get("status")

        if not sl or new_status is None:
            return JsonResponse({"success": False, "error": "Missing sl or status"})

        installment = ShareInstallmentPayment.objects.select_related(
            "voucher"
        ).get(sl=sl)

        old_status = installment.pay_status
        voucher = installment.voucher

        with transaction.atomic():

            # Update status ONLY if changed
            if old_status != new_status:
                installment.pay_status = new_status
                installment.save(update_fields=["pay_status"])

                # ----------------------------
                # Ensure UNIQUE MR / BILL NO
                # ----------------------------
                original_no = voucher.mr_or_bill_no
                unique_no = generate_unique_mr_or_bill_no(original_no)

                if unique_no != original_no:
                    voucher.mr_or_bill_no = unique_no
                    voucher.save(update_fields=["mr_or_bill_no"])

                # ----------------------------
                # Ledger Entry (safe)
                # ----------------------------
                LedgerEntry.objects.get_or_create(
                    mr_or_bill_no=voucher.mr_or_bill_no,
                    defaults={
                        "date": voucher.date,
                        "amount": voucher.amount,
                        "voucher": voucher,
                    }
                )

        # ----------------------------
        # SMS Notification (ONLY when PAID)
        # ----------------------------
        if old_status != "PAID" and new_status == "PAID":

            sms_numbers = set()
            STATIC_NUMBER = "8801913222203"
            sms_numbers.add(STATIC_NUMBER)

            sms_message = ""

            if voucher.type == "Customer" and voucher.customer_name:
                customer = Customer.objects.filter(
                    id=voucher.customer_name.id
                ).first()

                if customer and customer.contact_no:
                    sms_numbers.add(
                        normalize_phone(customer.contact_no)
                    )

                sms_message = (
                    f"Dear Customer,\n"
                    f"We have successfully received your payment of ৳{voucher.amount} "
                    f"on {voucher.date.strftime('%d-%m-%Y')}.\n"
                    f"Reference No: {voucher.mr_or_bill_no}\n"
                    f"BTP Limited\n"
                    f"Thank you."
                )

            for number in sms_numbers:
                result = send_sms(number, sms_message)
                if not result:
                    print(f"❌ SMS failed for {number}")
                else:
                    print(f"✅ SMS sent to {number}")

        return JsonResponse({
            "success": True,
            "sl": sl,
            "old_status": old_status,
            "new_status": new_status,
            "mr_or_bill_no": voucher.mr_or_bill_no
        })

    except ShareInstallmentPayment.DoesNotExist:
        return JsonResponse({"success": False, "error": "Installment not found"})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})





@login_required
def installment_list(request, id):
    property_sale = get_object_or_404(PropertySales, id=id)
    installments = InstallmentPayment.objects.filter(property_sales=property_sale)
    cash_types = CashType.objects.all()
    
    context = {
        'property_sale': property_sale,
        'installments': installments,
        'cash_types': cash_types,
    }
    return render(request, 'sales/installments_list.html', context)


# @login_required
# def sales_payment_invoice(request, pk):
#     installment = get_object_or_404(InstallmentPayment, pk=pk)
#     context = {
#         'installment': installment
#     }
#     return render(request, 'sales/installment_invoice.html', context)
    

from decimal import Decimal

@login_required
def sales_payment_invoice(request, pk):
    installment = get_object_or_404(InstallmentPayment, pk=pk)

    def amount_to_words(amount):
        # Remove commas and convert to Decimal
        amount = Decimal(str(amount).replace(',', ''))

        # Split Taka and Paisa
        taka = int(amount)
        paisa = int(round((amount - taka) * 100))

        # Words arrays
        units = [
            "", "One", "Two", "Three", "Four", "Five", "Six",
            "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
            "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
            "Eighteen", "Nineteen"
        ]
        tens = [
            "", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"
        ]

        def two_digit(n):
            if n < 20:
                return units[n]
            return tens[n // 10] + (" " + units[n % 10] if n % 10 else "")

        def three_digit(n):
            if n < 100:
                return two_digit(n)
            return units[n // 100] + " Hundred" + (" " + two_digit(n % 100) if n % 100 else "")

        words = []

        # Crore
        if taka >= 10000000:
            words.append(three_digit(taka // 10000000) + " Crore")
            taka %= 10000000
        # Lakh
        if taka >= 100000:
            words.append(three_digit(taka // 100000) + " Lakh")
            taka %= 100000
        # Thousand
        if taka >= 1000:
            words.append(three_digit(taka // 1000) + " Thousand")
            taka %= 1000
        # Remaining Taka
        if taka > 0:
            words.append(three_digit(taka))

        amount_words = " ".join(words) + " Taka"
        if paisa > 0:
            amount_words += " and " + two_digit(paisa) + " Paisa"

        return amount_words + " Only"


    return render(request, 'sales/installment_invoice.html', {
        'installment': installment,
        'amount_in_words': amount_to_words(installment.amount),
    })




@login_required
def flat_plot_sales_summary(request, id):
    property_sale = get_object_or_404(PropertySales, id=id)
    installments = InstallmentPayment.objects.filter(property_sales=property_sale)
    
    context = {
        'property_sale': property_sale,
        'installments': installments,
        'print_time': now(),
    }
    return render(request, 'sales/flat_plot_sales_summary.html', context)
    
 
 
# @login_required
# @csrf_exempt
# def update_installment_status(request):
#     if request.method != 'POST':
#         return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#     try:
#         data = json.loads(request.body)
#         installment_id = data.get('installment_id')
#         new_status = data.get('pay_status')
#         cash_type_id = data.get('cash_type')
#         cheque_number = data.get('cheque_number')
#         mr_or_bill_no = data.get('mr_or_bill_no')

#         if new_status not in ['Pending', 'Done']:
#             return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

#         with transaction.atomic():
#             # Lock and update InstallmentPayment
#             installment = InstallmentPayment.objects.select_for_update().get(id=installment_id)
#             installment.pay_status = new_status

#             if cash_type_id:
#                 try:
#                     cash_type_obj = CashType.objects.get(id=cash_type_id)
#                     installment.cash_type = cash_type_obj
#                 except CashType.DoesNotExist:
#                     return JsonResponse({'success': False, 'message': 'Invalid cash type'}, status=400)

#             if cheque_number is not None:
#                 installment.cheque_no = cheque_number

#             # Generate or use MR/Bill No
#             if mr_or_bill_no:
#                 installment.mr_or_bill_no = mr_or_bill_no
#             else:
#                 base_code = "MSC-"
#                 last = InstallmentPayment.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#                 next_id = (last.id + 1) if last else 1
#                 generated_code = f"{base_code}{next_id:05d}"
#                 while InstallmentPayment.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"
#                 installment.mr_or_bill_no = generated_code

#             installment.save()

#             # Update property_sales last payment status
#             property_sale = installment.property_sales
#             property_sale.pay_last_status = installment.payment_type
#             property_sale.save()

#             # Get HeadOfAccount (mandatory for LedgerEntry)
#             try:
#                 installment_head = HeadOfAccount.objects.get(head_name="Customer Account")  # use the actual name
#             except HeadOfAccount.DoesNotExist:
#                 return JsonResponse({'success': False, 'message': 'HeadOfAccount "Customer Accounts" not found'}, status=500)
            
            
#             # Create or update CreditVoucher
#             credit_voucher, created = CreditVoucher.objects.update_or_create(
#                 mr_or_bill_no=installment.mr_or_bill_no,
#                 defaults={
#                     'project_name': property_sale.project_name,
#                     'type': 'Customer',
#                     'cash_type': installment.cash_type,
#                     'cheque_number': installment.cheque_no,
#                     'bill_date':installment.cheque_date,
#                     'head_of_account': installment_head,
#                     'date': installment.cheque_date or property_sale.date,
#                     'amount': installment.amount,
#                     'particulars': f'{installment.get_payment_type_display()} payment update',
#                     'is_confirmed': True,
#                     'approval_cr_status': True,
#                     'customer_name': installment.customer_name,
#                     'create_cr':request.user.username
#                 }
#             )

#             # Create LedgerEntry
#             LedgerEntry.objects.create(
#                 project_name=property_sale.project_name,
#                 type='Customer',
#                 customer_name=installment.customer_name,
#                 cash_type=installment.cash_type,
#                 cheque_number=installment.cheque_no,
#                 mr_or_bill_no=installment.mr_or_bill_no,
#                 head=installment_head,
#                 date=installment.cheque_date or property_sale.date,
#                 description=f'{installment.get_payment_type_display()} installment payment',
#                 debit=0,
#                 credit=installment.amount,
#                 tbl_id=str(installment.id),
#                 tbl_name='InstallmentPayment'
#             )

#             # Create TransactionHistory (assign the same HeadOfAccount)
#             TransactionHistory.objects.create(
#                 project=property_sale.project_name,
#                 transaction_type='Customer',
#                 head_of_account=installment_head,  # mandatory
#                 cash_type=installment.cash_type,
#                 cheque_number=installment.cheque_no,
#                 amount=installment.amount,
#                 date=installment.cheque_date or property_sale.date,
#                 type_name='Customer Payment',
#                 reference=installment.mr_or_bill_no,
#                 particulars=f'{installment.get_payment_type_display()} installment',
#                 create_by=request.user.username
#             )

#         redirect_url = reverse('flat_plot_sales')  # replace with your list URL
#         return JsonResponse({'success': True, 'redirect_url': redirect_url})

#     except InstallmentPayment.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Installment not found'}, status=404)
#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)





# @login_required
# @csrf_exempt
# def update_installment_status(request):
#     if request.method != 'POST':
#         return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#     try:
#         data = json.loads(request.body)
#         installment_id = data.get('installment_id')
#         new_status = data.get('pay_status')
#         cash_type_id = data.get('cash_type')
#         cheque_number = data.get('cheque_number')
#         mr_or_bill_no = data.get('mr_or_bill_no')

#         if new_status not in ['Pending', 'Done']:
#             return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

#         with transaction.atomic():
#             # Lock and fetch InstallmentPayment
#             installment = InstallmentPayment.objects.select_for_update().get(id=installment_id)
#             installment.pay_status = new_status

#             # Assign cash_type safely
#             if cash_type_id:
#                 try:
#                     cash_type_obj = CashType.objects.get(id=cash_type_id)
#                     installment.cash_type = cash_type_obj
#                 except CashType.DoesNotExist:
#                     return JsonResponse({'success': False, 'message': 'Invalid cash type'}, status=400)

#             # Assign cheque number safely
#             installment.cheque_no = cheque_number or None

#             # Handle mr_or_bill_no safely to avoid UNIQUE constraint
#             if mr_or_bill_no:
#                 installment.mr_or_bill_no = mr_or_bill_no
#             else:
#                 base_code = "MSC-"
#                 last = InstallmentPayment.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#                 next_id = (last.id + 1) if last else 1
#                 generated_code = f"{base_code}{next_id:05d}"

#                 # Ensure uniqueness
#                 while InstallmentPayment.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 installment.mr_or_bill_no = generated_code

#             installment.save()

#             # Update property_sales last payment status
#             property_sale = installment.property_sales
#             property_sale.pay_last_status = installment.payment_type
#             property_sale.save()

#             # Fetch HeadOfAccount safely
#             try:
#                 installment_head = HeadOfAccount.objects.get(head_name="Customer Account")
#             except HeadOfAccount.DoesNotExist:
#                 return JsonResponse({'success': False, 'message': 'HeadOfAccount "Customer Account" not found'}, status=500)

#             # Create or update CreditVoucher safely
#             credit_voucher, created = CreditVoucher.objects.update_or_create(
#                 mr_or_bill_no=installment.mr_or_bill_no,
#                 defaults={
#                     'project_name': property_sale.project_name,
#                     'type': 'Customer',
#                     'cash_type': installment.cash_type,
#                     'cheque_number': installment.cheque_no,
#                     'bill_date': installment.cheque_date or date.today(),
#                     'head_of_account': installment_head,
#                     'date': installment.cheque_date or property_sale.date,
#                     'amount': installment.amount,
#                     'particulars': f'{installment.get_payment_type_display()} payment update',
#                     'is_confirmed': True,
#                     'approval_cr_status': True,
#                     'customer_name': installment.customer_name,
#                     'create_cr': request.user.username
#                 }
#             )

#             # Create or update LedgerEntry safely to avoid UNIQUE constraint
#             ledger_entry, created = LedgerEntry.objects.update_or_create(
#                 mr_or_bill_no=installment.mr_or_bill_no,
#                 defaults={
#                     'project_name': property_sale.project_name,
#                     'type': 'Customer',
#                     'customer_name': installment.customer_name,
#                     'cash_type': installment.cash_type,
#                     'cheque_number': installment.cheque_no,
#                     'head': installment_head,
#                     'date': installment.cheque_date or property_sale.date,
#                     'description': f'{installment.get_payment_type_display()} installment payment',
#                     'debit': 0,
#                     'credit': installment.amount,
#                     'tbl_id': str(installment.id),
#                     'tbl_name': 'InstallmentPayment'
#                 }
#             )

#             # Create TransactionHistory safely
#             TransactionHistory.objects.create(
#                 project=property_sale.project_name,
#                 transaction_type='Customer',
#                 head_of_account=installment_head,
#                 cash_type=installment.cash_type,
#                 cheque_number=installment.cheque_no,
#                 amount=installment.amount,
#                 date=installment.cheque_date or property_sale.date,
#                 type_name='Customer Payment',
#                 reference=installment.mr_or_bill_no,
#                 particulars=f'{installment.get_payment_type_display()} installment',
#                 create_by=request.user.username
#             )

#         redirect_url = reverse('flat_plot_sales')  # replace with your list URL
#         return JsonResponse({'success': True, 'redirect_url': redirect_url})

#     except InstallmentPayment.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Installment not found'}, status=404)
#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)




@login_required
@csrf_exempt
def update_installment_status(request):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'message': 'Invalid request method'},
            status=405
        )

    try:
        data = json.loads(request.body)
        installment_id = data.get('installment_id')
        new_status = data.get('pay_status')
        cash_type_id = data.get('cash_type')
        cheque_number = data.get('cheque_number')
        mr_or_bill_no = data.get('mr_or_bill_no')

        if new_status not in ['Pending', 'Done']:
            return JsonResponse(
                {'success': False, 'message': 'Invalid status'},
                status=400
            )

        with transaction.atomic():

            # 🔒 Lock installment row
            installment = InstallmentPayment.objects.select_for_update().get(
                id=installment_id
            )

            installment.pay_status = new_status

            # ✅ Assign Cash Type
            if cash_type_id:
                try:
                    cash_type_obj = CashType.objects.get(id=cash_type_id)
                    installment.cash_type = cash_type_obj
                except CashType.DoesNotExist:
                    return JsonResponse(
                        {'success': False, 'message': 'Invalid cash type'},
                        status=400
                    )

            # ✅ Assign Cheque Number (optional)
            installment.cheque_no = cheque_number or None

            # ✅ Handle MR/Bill No (UNIQUE safe)
            if mr_or_bill_no:
                installment.mr_or_bill_no = mr_or_bill_no
            else:
                base_code = "MSC-"
                last = InstallmentPayment.objects.filter(
                    mr_or_bill_no__startswith=base_code
                ).order_by('-id').first()

                next_id = (last.id + 1) if last else 1
                generated_code = f"{base_code}{next_id:05d}"

                while InstallmentPayment.objects.filter(
                    mr_or_bill_no=generated_code
                ).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"

                installment.mr_or_bill_no = generated_code

            installment.save()

            # ✅ Update Property Sale Last Payment Status
            property_sale = installment.property_sales
            property_sale.pay_last_status = installment.payment_type
            property_sale.save()

            # ✅ Head Of Account
            try:
                installment_head = HeadOfAccount.objects.get(
                    head_name="Customer Account"
                )
            except HeadOfAccount.DoesNotExist:
                return JsonResponse(
                    {'success': False,
                     'message': 'HeadOfAccount "Customer Account" not found'},
                    status=500
                )

            # 🔥 IMPORTANT CHANGE HERE
            # We DO NOT use cheque_date anymore
            transaction_date = date.today()

            # ✅ Credit Voucher
            CreditVoucher.objects.update_or_create(
                mr_or_bill_no=installment.mr_or_bill_no,
                defaults={
                    'project_name': property_sale.project_name,
                    'type': 'Customer',
                    'cash_type': installment.cash_type,
                    'cheque_number': installment.cheque_no,
                    'bill_date': transaction_date,
                    'head_of_account': installment_head,
                    'date': transaction_date,
                    'amount': installment.amount,
                    'particulars': f'{installment.get_payment_type_display()} payment update',
                    'is_confirmed': True,
                    'approval_cr_status': True,
                    'customer_name': installment.customer_name,
                    'create_cr': request.user.username
                }
            )

            # ✅ Ledger Entry
            LedgerEntry.objects.update_or_create(
                mr_or_bill_no=installment.mr_or_bill_no,
                defaults={
                    'project_name': property_sale.project_name,
                    'type': 'Customer',
                    'customer_name': installment.customer_name,
                    'cash_type': installment.cash_type,
                    'cheque_number': installment.cheque_no,
                    'head': installment_head,
                    'date': transaction_date,
                    'description': f'{installment.get_payment_type_display()} installment payment',
                    'debit': 0,
                    'credit': installment.amount,
                    'tbl_id': str(installment.id),
                    'tbl_name': 'InstallmentPayment'
                }
            )

            # ✅ Transaction History
            TransactionHistory.objects.create(
                project=property_sale.project_name,
                transaction_type='Customer',
                head_of_account=installment_head,
                cash_type=installment.cash_type,
                cheque_number=installment.cheque_no,
                amount=installment.amount,
                date=transaction_date,
                type_name='Customer Payment',
                reference=installment.mr_or_bill_no,
                particulars=f'{installment.get_payment_type_display()} installment',
                create_by=request.user.username
            )

        redirect_url = reverse('flat_plot_sales')

        return JsonResponse({
            'success': True,
            'redirect_url': redirect_url
        })

    except InstallmentPayment.DoesNotExist:
        return JsonResponse(
            {'success': False, 'message': 'Installment not found'},
            status=404
        )

    except Exception as e:
        traceback.print_exc()
        return JsonResponse(
            {'success': False, 'message': f'Error: {str(e)}'},
            status=500
        )
        
        


# @login_required
# @csrf_exempt
# def update_installment_status(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         installment_id = data.get('installment_id')
#         new_status = data.get('pay_status')

#         if new_status not in ['Pending', 'Done']:
#             return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

#         try:
#             installment = InstallmentPayment.objects.get(id=installment_id)
#             installment.pay_status = new_status
#             installment.save()

#             property_sale = installment.property_sales
#             property_sale.pay_last_status = installment.payment_type
#             property_sale.save()

#             redirect_url = reverse('flat_plot_sales')  # your named URL here

#             return JsonResponse({'success': True, 'redirect_url': redirect_url})
#         except InstallmentPayment.DoesNotExist:
#             return JsonResponse({'success': False, 'message': 'Installment not found'}, status=404)

#     return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)