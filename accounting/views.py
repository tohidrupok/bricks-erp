from accounting.utils.sms import send_sms
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CapitalAccount,CashType, HeadOfAccount,CreditVoucher,DebitVoucher,JournalVoucher,ContraVoucher,LedgerEntry,TransactionHistory,BalanceTransfer,LoanVoucher,OpenBlanceVoucher, BankStatementTransaction, AccountReconciliation,BankStatementTransaction,BalanceItem,BalanceSheetHead,MainChequeBook,MainCheque,ProjectProfitRecord
from .forms import CapitalAccountForm,CashTypeForm, HeadOfAccountForm,CreditVoucherForm,DebitVoucherForm,JournalVoucherForm,ContraVoucherForm,LedgerReportForm,BalanceTransferForm,LoanVoucherForm,OpenBlanceVoucherForm,LedgerFilterForm,TransactionHistoryForm,BankStatementUploadForm, ReconciliationForm,BalanceItemForm,BalanceSheetHeadForm,MainChequeBookForm,MainChequeForm
from django.utils.timezone import now
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from projects.models import ProjectFirstLevelName,Suppliers,BOQ,SiteSupervisor,Donation
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from django.db.models import Sum
from datetime import date
from django.contrib import messages
from purchase.models import HeadOfExpense,HeadOfRequisition,BillRequisition,RequisitionApprovalPayment,Suppliers,RequisitionApprovalPayment,BillRequisitionApprovalPayment
from collections import defaultdict
import csv, io
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.views.decorators.http import require_POST
from django.db.models import Sum, Min 
from purchase.models import Requisition
from inventories.utils import log_deleted_data
from hrm.models import Employee,AdvancePayment,Allowances,RdaEmployee,LoanPayment,SalaryVoucher,RdaPayEmpSalary,RdaPayEmpSalary
from django.utils.dateparse import parse_date
from inventories.models import Inventories
from crm.models import Sale,Customer
from .models import LedgerEntry, LoanVoucher
from datetime import datetime, timedelta
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from datetime import datetime
from decimal import Decimal
from num2words import num2words
from django.db.models.functions import Coalesce
from inventories.models import InventoryUse,Inventories
from django.core.paginator import Paginator
import traceback
from django.urls import reverse
from sales.models import PropertySales
from properties.models import LandPurchase




@login_required
def cash_type_list(request):
    cash_types = CashType.objects.all()
    return render(request, 'accounting/cash_type.html', {'cash_types': cash_types})

@login_required
def add_cash_type(request):
    if request.method == 'POST':
        form = CashTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cash_type_list')
    else:
        form = CashTypeForm()
    return render(request, 'accounting/add_cash_type.html', {'form': form})

@login_required
def edit_cash_type(request, pk):
    cash_type = get_object_or_404(CashType, pk=pk)
    if request.method == 'POST':
        form = CashTypeForm(request.POST, instance=cash_type)
        if form.is_valid():
            form.save()
            return redirect('cash_type_list')
    else:
        form = CashTypeForm(instance=cash_type)
    return render(request, 'accounting/edit_cash_type.html', {'form': form, 'cash_type': cash_type})


@login_required
def delete_cash_type(request, pk):
    cash_type = get_object_or_404(CashType, pk=pk)

    if request.method == 'POST':
        log_deleted_data(cash_type, request.user)
        cash_type.delete()
        return redirect('cash_type_list')

    return render(request, 'accounting/delete_cash_type.html', {'cash_type': cash_type})


@login_required
def head_of_account_list(request):
    head_accounts = HeadOfAccount.objects.all()
    return render(request, 'accounting/head_of_account_list.html', {'head_accounts': head_accounts})


@login_required
def add_head_of_account(request):
    if request.method == 'POST':
        form = HeadOfAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('head_of_account_list')  
    else:
        form = HeadOfAccountForm()
    return render(request, 'accounting/add_head_of_account.html', {'form': form})



@login_required
def edit_head_of_account(request, pk):
    head_account = get_object_or_404(HeadOfAccount, pk=pk)
    
    if request.method == 'POST':
        form = HeadOfAccountForm(request.POST, instance=head_account)
        if form.is_valid():
            form.save()
            return redirect('head_of_account_list')  
    else:
        form = HeadOfAccountForm(instance=head_account)
    
    return render(request, 'accounting/edit_head_of_account.html', {
        'form': form,
        'head_account': head_account
    })


@login_required
def delete_head_of_account(request, pk):
    head_account = get_object_or_404(HeadOfAccount, pk=pk)
    if request.method == 'POST':
        log_deleted_data(head_account, request.user)
        head_account.delete()
        return redirect('head_of_account_list')
    return render(request, 'accounting/delete_head_of_account.html', {
        'head_account': head_account  
    })


### credit voucher code 
# @login_required
# def creditvoucher_list(request):
#     vouchers = CreditVoucher.objects.all().order_by('-id')
#     paginator = Paginator(vouchers, 15)  
#     page_number = request.GET.get('page')
#     vouchers_page = paginator.get_page(page_number) 
#     return render(request, 'creditvoucher/creditvoucher_list.html', {'vouchers': vouchers, 'vouchers': vouchers_page})




@login_required
def creditvoucher_list(request):

    vouchers = CreditVoucher.objects.all().order_by('-id')

    # ✅ Date filter
    selected_date = request.GET.get("date")

    if selected_date:
        vouchers = vouchers.filter(date=selected_date)
    else:
        selected_date = date.today()

    # ✅ Pagination after filtering
    paginator = Paginator(vouchers, 15)
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number)

    context = {
        'vouchers': vouchers_page,
        'selected_date': selected_date,
    }

    return render(
        request,
        'creditvoucher/creditvoucher_list.html',
        context
    )





@login_required
def approve_cr_voucher(request, pk):
    voucher = get_object_or_404(CreditVoucher, pk=pk)
    updated_items = []

    # If already approved, redirect
    if voucher.approval_cr_status:
        return redirect('creditvoucher_list')

    # Generate MR/Bill No if not set
    if not voucher.mr_or_bill_no:
        base_code = "MBC-"
        last = (
            CreditVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
            .order_by('-id')
            .first()
        )
        next_id = (last.id + 1) if last else 1
        generated_code = f"{base_code}{next_id:05d}"

        while CreditVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
            next_id += 1
            generated_code = f"{base_code}{next_id:05d}"

        voucher.mr_or_bill_no = generated_code

    # Approve the voucher
    voucher.approval_cr_status = True
    voucher.save()
    updated_items.append(voucher)

    # Update CashType balance
    try:
        cash_type = CashType.objects.get(cash_type_name=voucher.cash_type)
        cash_type.type_amount += voucher.amount
        cash_type.type_note = f"Update Received Amount of voucher ID {voucher.id}"
        cash_type.save()
    except CashType.DoesNotExist:
        cash_type = None  # prevent crash later
    
    type_name = voucher.customer_name if voucher.type == 'Customer' and voucher.customer_name else None
    # Log transaction
    TransactionHistory.objects.create(
        project=voucher.project_name,  # FK to ProjectFirstLevelName
        transaction_type=voucher.type,
        head_of_account=voucher.head_of_account,
        cash_type=cash_type,
        amount=voucher.amount,
        cheque_number=voucher.cheque_number,
        date=timezone.now().date(),
        type_name=type_name,
        reference=voucher.mr_or_bill_no,
        create_by=voucher.create_cr,
        particulars=voucher.particulars,
        tbl_id=voucher.id,
        tbl_name='Received',
    )

    # Create ledger entries
    for item in updated_items:
        loan_status = 'received'
        amount = item.amount or 0
        debit_amount = amount if loan_status == 'payment' else 0
        credit_amount = amount if loan_status == 'received' else 0

        LedgerEntry.objects.create(
            project_name=item.project_name,  # FK to ProjectFirstLevelName
            type=item.type,
            contructor=getattr(item, 'contructor', None),
            vendor=getattr(item, 'vendor', None),
            customer_name=getattr(item, 'customer_name', None),
            bankName=getattr(item, 'bankName', None),  # reused field
            capi_name=getattr(item, 'capi_name', None),
            donation_name=getattr(item, 'donation_name', None),
            invest_name=getattr(item, 'invest_name', None),
            cash_type=item.cash_type,
            cheque_number=item.cheque_number,
            head=item.head_of_account,
            mr_or_bill_no=None,
            date=timezone.now().date(),
            description=item.particulars or '',
            debit=debit_amount,
            credit=credit_amount,
            carrier=getattr(item, 'carrier', None),
            loan_status=loan_status,
            tbl_id=item.id,
            tbl_name='Received'
        )
    
    sms_number = "8801723111218"
    sms_message = (
        f"We have successfully received your payment of ৳{voucher.amount}.\n"
        f"Thank you for your transaction.\n"
        f"BTP Limited"
    )
    
    # Send SMS safely (no crash even if SMS fails)
    if not send_sms(sms_number, sms_message):
        print("SMS sending failed (ignored).")


    return redirect('creditvoucher_list')
    
    
    



# @login_required
# def approve_cr_voucher(request, pk):
#     voucher = get_object_or_404(CreditVoucher, pk=pk)
#     updated_items = []

#     # If already approved, redirect
#     if voucher.approval_cr_status:
#         return redirect('creditvoucher_list')

#     # Generate MR/Bill No if not set
#     if not voucher.mr_or_bill_no:
#         base_code = "MBC-"
#         last = (
#             CreditVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#             .order_by('-id')
#             .first()
#         )
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"

#         while CreditVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#             next_id += 1
#             generated_code = f"{base_code}{next_id:05d}"

#         voucher.mr_or_bill_no = generated_code

#     # Approve the voucher
#     voucher.approval_cr_status = True
#     voucher.save()
#     updated_items.append(voucher)

#     # Update CashType balance
#     try:
#         cash_type = CashType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount += voucher.amount or 0
#         cash_type.type_note = f"Update Received Amount of voucher ID {voucher.id}"
#         cash_type.save()
#     except CashType.DoesNotExist:
#         cash_type = None

#     # Log transaction
#     type_name = voucher.customer_name if voucher.type == 'Customer' and voucher.customer_name else None
#     TransactionHistory.objects.create(
#         project=voucher.project_name,
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount or 0,
#         cheque_number=voucher.cheque_number,
#         date=voucher.date or timezone.now(),
#         type_name=type_name,
#         reference=voucher.mr_or_bill_no,
#         create_by=voucher.create_cr,
#         particulars=voucher.particulars,
#         tbl_id=voucher.id,
#         tbl_name='Received',
#     )

#     # Create ledger entries
#     for item in updated_items:
#         loan_status = 'received'
#         amount = item.amount or 0
#         debit_amount = amount if loan_status == 'payment' else 0
#         credit_amount = amount if loan_status == 'received' else 0

#         LedgerEntry.objects.create(
#             project_name=item.project_name,  # FK to ProjectFirstLevelName
#             type=item.type,
#             contructor=getattr(item, 'contructor', None),
#             vendor=getattr(item, 'vendor', None),
#             customer_name=getattr(item, 'customer_name', None),
#             bankName=getattr(item, 'bankName', None),  # reused field
#             capi_name=getattr(item, 'capi_name', None),
#             donation_name=getattr(item, 'donation_name', None),
#             invest_name=getattr(item, 'invest_name', None),
#             cash_type=item.cash_type,
#             cheque_number=item.cheque_number,
#             head=item.head_of_account,
#             mr_or_bill_no=item.mr_or_bill_no,
#             date=item.date or timezone.now(),
#             description=item.particulars or '',
#             debit=debit_amount,
#             credit=credit_amount,
#             carrier=getattr(item, 'carrier', None),
#             loan_status=loan_status,
#             tbl_id=item.id,
#             tbl_name='Received'
#         )


#     # ✅ Send SMS safely
#     sms_number = "01723111218"
#     sms_message = (
#         f"Received Amount!\n"
#         f"MR No: {voucher.mr_or_bill_no}\n"
#         f"Amount: {voucher.amount}\n"
#         f"Date: {voucher.date}"
#     )

#     try:
#         send_sms(sms_number, sms_message)
#     except Exception as e:
#         print("SMS error ignored:", e)

#     return redirect('creditvoucher_list')

    
    
    
    

# @login_required
# def add_creditvoucher(request):
#     if request.method == 'POST':
#         form = CreditVoucherForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('creditvoucher_list')  # or your list view
#     else:
#         form = CreditVoucherForm()
#     employees = RdaEmployee.objects.all()
#     return render(request, 'creditvoucher/add_creditvoucher.html', {'form': form, 'today': date.today().strftime('%Y-%m-%d')})





@login_required
def add_creditvoucher(request):
    if request.method == 'POST':
        form = CreditVoucherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('creditvoucher_list')  # redirect after save
    else:
        form = CreditVoucherForm()

    employees = RdaEmployee.objects.all()  # ✅ load employees
    context = {
        'form': form,
        'employees': employees,  # ✅ pass to template
        'today': date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'creditvoucher/add_creditvoucher.html', context)





from django.utils import timezone

@login_required
def edit_creditvoucher(request, pk):
    voucher = get_object_or_404(CreditVoucher, pk=pk)
    form = CreditVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        updated_voucher = form.save()

        # Update or create LedgerEntry linked to this CreditVoucher
        ledger_entry, created = LedgerEntry.objects.update_or_create(
            tbl_id=str(updated_voucher.id),
            tbl_name="Received",  # CreditVoucher = Receipt
            defaults={
                "project_name": updated_voucher.project_name,
                "type": updated_voucher.type,
                "contructor": None,
                "vendor": None,
                "customer_name": updated_voucher.customer_name,
                "exp_name": None,
                "empl_name": None,
                "capi_name": updated_voucher.capi_name,
                "invest_name": updated_voucher.invest_name,
                "cash_type": updated_voucher.cash_type,
                "bankName": None,
                "cheque_number": updated_voucher.cheque_number,
                "mr_or_bill_no": updated_voucher.mr_or_bill_no,
                "head": updated_voucher.head_of_account,
                "date": updated_voucher.date or timezone.now().date(),  # ✅ ensures NOT NULL
                "description": updated_voucher.particulars,
                "credit": updated_voucher.amount,   # CreditVoucher → credit
                "debit": 0,
                "carrier": updated_voucher.carrier,
            }
        )
        TransactionHistory.objects.update_or_create(
                tbl_id=str(updated_voucher.id),       
                tbl_name="Received",               
                defaults={
                    "project": updated_voucher.project_name,
                    "transaction_type": "Credit",
                    "head_of_account": updated_voucher.head_of_account,
                    "cash_type": updated_voucher.cash_type,
                    "cheque_number": updated_voucher.cheque_number,
                    "amount": updated_voucher.amount,
                    "date": updated_voucher.date or timezone.now().date(),
                    "type_name": updated_voucher.type,
                    "reference": getattr(updated_voucher, 'voucher_no', None),
                    "create_by": request.user.username,
                    "particulars": updated_voucher.particulars,
                }
            )

        return redirect('creditvoucher_list')

    return render(request, 'creditvoucher/edit_creditvoucher.html', {
        'form': form,
        'voucher': voucher
    })


    
    

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

@login_required
def delete_creditvoucher(request, pk):
    voucher = get_object_or_404(CreditVoucher, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Log before delete
            log_deleted_data(voucher, request.user)

            LedgerEntry.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Received" 
            ).delete()

            
            TransactionHistory.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Received"
            ).delete()

            voucher.delete()

        return redirect('creditvoucher_list')

    return render(
        request,
        'creditvoucher/delete_creditvoucher.html',
        {'voucher': voucher}
    )



@login_required
def details_creditvoucher(request, pk):
    voucher = get_object_or_404(CreditVoucher, pk=pk)
    return render(request, 'creditvoucher/details_creditvoucher.html', {'voucher': voucher})


@login_required
def credit_voucher_pdf(request, pk):
    voucher = get_object_or_404(CreditVoucher, pk=pk)
  
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
    return render(request, 'creditvoucher/print_creditvoucher.html', context)



### debit voucher code 
# @login_required
# def debitvoucher_list(request):
#     projects_firt = ProjectFirstLevelName.objects.all()    
#     filtered_vouchers = DebitVoucher.objects.filter(
#         vendor__isnull=False,
#         cash_type__isnull=True,
#         requi_id__isnull=False
#     )    
#     vendor_ids = filtered_vouchers.values_list('vendor_id', flat=True).distinct()    
#     suppliers = Suppliers.objects.filter(id__in=vendor_ids)    
#     vouchers = DebitVoucher.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")).order_by('-id')
    
#     paginator = Paginator(vouchers, 15)  
#     page_number = request.GET.get('page')
#     vouchers_page = paginator.get_page(page_number) 
#     context = {
#         'projects_firts': projects_firt,
#         'suppliers': suppliers,
#         'vouchers': vouchers,
#         'vouchers': vouchers_page,
#     }
#     return render(request, 'debitvoucher/debitvoucher_list.html', context)





@login_required
def debitvoucher_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()

    filtered_vouchers = DebitVoucher.objects.filter(
        vendor__isnull=False,
        cash_type__isnull=True,
        requi_id__isnull=False
    )

    vendor_ids = filtered_vouchers.values_list('vendor_id', flat=True).distinct()
    suppliers = Suppliers.objects.filter(id__in=vendor_ids)

    # Base vouchers query
    vouchers = DebitVoucher.objects.filter(
        Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")
    ).order_by('-id')

    # ✅ Date filter
    selected_date = request.GET.get("date")

    if selected_date:
        vouchers = vouchers.filter(date=selected_date)
    else:
        selected_date = date.today()

    # ✅ Pagination after filtering
    paginator = Paginator(vouchers, 15)
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number)

    context = {
        'projects_firts': projects_firt,
        'suppliers': suppliers,
        'vouchers': vouchers_page,
        'selected_date': selected_date,
    }

    return render(request, 'debitvoucher/debitvoucher_list.html', context)






import re

@login_required
def approve_dr_voucher(request, pk):
    voucher = get_object_or_404(DebitVoucher, pk=pk)

    if voucher.approval_dr_status:
        return redirect('debitvoucher_list')

    # Handle advance payment
    if voucher.advance_pay:
        RequisitionApprovalPayment.objects.create(
            requisition=None,
            requi_item_name=None,
            requi_uniq_id=None,
            supplier=getattr(voucher, 'vendor', None),
            payment_type='advance_pay',
            requi_amount=voucher.amount,
            requisition_date=timezone.now().date()
        )

    # Auto-generate mr_or_bill_no if missing
    if not voucher.mr_or_bill_no:
        base_code = "MBD-"
        last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
        next_id = (last.id + 1) if last else 1
        generated_code = f"{base_code}{next_id:05d}"
        while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
            next_id += 1
            generated_code = f"{base_code}{next_id:05d}"
        voucher.mr_or_bill_no = generated_code

    # -------------------------
    # Extract numeric ID from string like "32 - EXC-00032 - Lillahitaala"
    expense_obj = None
    if voucher.expense:
        match = re.match(r"(\d+)\s*-\s*.*", str(voucher.expense))
        if match:
            expense_id = int(match.group(1))
            expense_obj = HeadOfExpense.objects.filter(id=expense_id).first()
        # Optionally store the full name in DebitVoucher.expense for display
        voucher.expense = expense_obj.head_exp_name if expense_obj else voucher.expense
    # -------------------------

    voucher.approval_dr_status = True
    voucher.save()

    # Update cash balance
    try:
        cash_type = CashType.objects.get(cash_type_name=voucher.cash_type)
        cash_type.type_amount = (cash_type.type_amount or 0) - (voucher.amount or 0)
        cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
        cash_type.save()
    except CashType.DoesNotExist:
        cash_type = None

    # Create Transaction History
    TransactionHistory.objects.create(
        project=voucher.project_name,
        transaction_type=voucher.type,
        head_of_account=voucher.head_of_account,
        cash_type=cash_type,
        amount=voucher.amount,
        cheque_number=voucher.cheque_number,
        date=timezone.now().date(),
        type_name=expense_obj.head_exp_name if expense_obj else None,
        reference=voucher.mr_or_bill_no,
        create_by=voucher.create_dr,
        particulars=voucher.particulars,
        tbl_id=voucher.id,
        tbl_name='Payment',
    )

    # Create LedgerEntry
    LedgerEntry.objects.create(
        project_name=voucher.project_name,
        type=voucher.type,
        contructor=getattr(voucher, 'contructor', None),
        vendor=getattr(voucher, 'vendor', None),
        customer_name=getattr(voucher, 'customer_name', None),
        bankName=getattr(voucher, 'bankName', None),
        exp_name=expense_obj,  # <-- must be HeadOfExpense instance
        empl_name=getattr(voucher, 'empl_name', None),
        donation_name=getattr(voucher, 'donation_name', None),
        invest_name=getattr(voucher, 'invest_name', None),
        type_name=expense_obj.head_exp_name if expense_obj else None,
        cash_type=voucher.cash_type,
        cheque_number=voucher.cheque_number,
        head=voucher.head_of_account,
        mr_or_bill_no=voucher.mr_or_bill_no,
        date=timezone.now().date(),
        description=voucher.particulars or '',
        debit=voucher.amount or 0,
        credit=0,
        carrier=getattr(voucher, 'carrier', None),
        loan_status='payment',
        tbl_id=voucher.id,
        tbl_name='Payment'
    )
    
    # ----------------------------
    # SMS Notification
    # ----------------------------
    sms_numbers = []
    
    STATIC_NUMBER = "8801723111218"  # static number
    sms_numbers.append(STATIC_NUMBER)
    
    # Prepare SMS message based on voucher type
    sms_message = ""  # default empty
    
    if voucher.type == 'Customer' and voucher.customer_name:
        customer = Customer.objects.filter(id=voucher.customer_name.id).first()
        if customer and customer.contact_no:
            sms_numbers.append(customer.contact_no)
        
        sms_message = (
            f"Dear Customer,\n"
            f"We have successfully received your payment of ৳{voucher.amount} on {voucher.date.strftime('%d-%m-%Y')}.\n"
            f"Reference No: {voucher.mr_or_bill_no}\n"
            f"Thank you for your transaction.\n"
            f"BTP Limited\n"
            f"Thank you."
        )
    
    elif voucher.type == 'Vendor' and voucher.vendor:
        supplier = Suppliers.objects.filter(id=voucher.vendor.id).first()
        if supplier and supplier.phone:
            sms_numbers.append(supplier.phone)
        
        sms_message = (
            f"Dear Supplier,\n"
            f"We have successfully made a payment of ৳{voucher.amount} to you.\n"
            f"Reference: {voucher.mr_or_bill_no}\n"
            f"BTP Limited\n"
            f"Thank you."
        )
    
    elif voucher.type == 'Contractor' and voucher.contructor:
        contractor = SiteSupervisor.objects.filter(id=voucher.contructor.id).first()
        if contractor and contractor.phone:
            sms_numbers.append(contractor.phone)
        
        sms_message = (
            f"Dear Contractor,\n"
            f"We have successfully made a payment of ৳{voucher.amount} to you.\n"
            f"Reference: {voucher.mr_or_bill_no}\n"
            f"BTP Limited\n"
            f"Thank you."
        )
    
    # Remove duplicate numbers (important)
    sms_numbers = list(set(sms_numbers))
    
    # Send SMS safely
    for number in sms_numbers:
        if not send_sms(number, sms_message):
            print(f"SMS sending failed for {number} (ignored).")

    return redirect(reverse('debit_voucher_pdf', args=[voucher.pk]))
    
    
    

    
# import re

# @login_required
# def approve_dr_voucher(request, pk):
#     voucher = get_object_or_404(DebitVoucher, pk=pk)

#     if voucher.approval_dr_status:
#         return redirect('debitvoucher_list')

#     # Handle advance payment
#     if voucher.advance_pay:
#         RequisitionApprovalPayment.objects.create(
#             requisition=None,
#             requi_item_name=None,
#             requi_uniq_id=None,
#             supplier=getattr(voucher, 'vendor', None),
#             payment_type='advance_pay',
#             requi_amount=voucher.amount,
#             requisition_date=voucher.date or timezone.now().date()
#         )

#     # Auto-generate mr_or_bill_no if missing
#     if not voucher.mr_or_bill_no:
#         base_code = "MBD-"
#         last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"
#         while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#             next_id += 1
#             generated_code = f"{base_code}{next_id:05d}"
#         voucher.mr_or_bill_no = generated_code

#     # -------------------------
#     # Extract numeric ID from string like "32 - EXC-00032 - Lillahitaala"
#     expense_obj = None
#     if voucher.expense:
#         match = re.match(r"(\d+)\s*-\s*.*", str(voucher.expense))
#         if match:
#             expense_id = int(match.group(1))
#             expense_obj = HeadOfExpense.objects.filter(id=expense_id).first()
#         # Optionally store the full name in DebitVoucher.expense for display
#         voucher.expense = expense_obj.head_exp_name if expense_obj else voucher.expense
#     # -------------------------

#     voucher.approval_dr_status = True
#     voucher.save()

#     # Update cash balance
#     try:
#         cash_type = CashType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount = (cash_type.type_amount or 0) - (voucher.amount or 0)
#         cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
#         cash_type.save()
#     except CashType.DoesNotExist:
#         cash_type = None

#     # Create Transaction History
#     TransactionHistory.objects.create(
#         project=voucher.project_name,
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount,
#         cheque_number=voucher.cheque_number,
#         date=voucher.date,
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         reference=voucher.mr_or_bill_no,
#         create_by=voucher.create_dr,
#         particulars=voucher.particulars,
#         tbl_id=voucher.id,
#         tbl_name='Payment',
#     )

#     # Create LedgerEntry
#     LedgerEntry.objects.create(
#         project_name=voucher.project_name,
#         type=voucher.type,
#         contructor=getattr(voucher, 'contructor', None),
#         vendor=getattr(voucher, 'vendor', None),
#         customer_name=getattr(voucher, 'customer_name', None),
#         bankName=getattr(voucher, 'bankName', None),
#         exp_name=expense_obj,  # <-- must be HeadOfExpense instance
#         empl_name=getattr(voucher, 'empl_name', None),
#         donation_name=getattr(voucher, 'donation_name', None),
#         invest_name=getattr(voucher, 'invest_name', None),
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         cash_type=voucher.cash_type,
#         cheque_number=voucher.cheque_number,
#         head=voucher.head_of_account,
#         mr_or_bill_no=voucher.mr_or_bill_no,
#         date=voucher.date or timezone.now().date(),
#         description=voucher.particulars or '',
#         debit=voucher.amount or 0,
#         credit=0,
#         carrier=getattr(voucher, 'carrier', None),
#         loan_status='payment',
#         tbl_id=voucher.id,
#         tbl_name='Payment'
#     )
    
#     # ----------------------------
#     # SMS Notification
#     # ----------------------------
#     sms_number = None
#     sms_message = (
#         f"Dear Sir,\n"
#         f"We have transferred your payment.\n"
#         f"Amount: {voucher.amount} BDT\n"
#         f"Date: {voucher.date.strftime('%d-%m-%Y')}\n"
#         f"Voucher No: {voucher.mr_or_bill_no}\n"
#         f"Thank\n"
#         f"BTP LIMITED."
#     )


#     if voucher.type == 'Vendor' and voucher.vendor:
#         supplier = Suppliers.objects.filter(id=voucher.vendor.id).first()
#         if supplier and supplier.phone:
#             sms_number = supplier.phone

#     elif voucher.type == 'Customer' and voucher.customer_name:
#         customer = Customer.objects.filter(id=voucher.customer_name.id).first()
#         if customer and customer.contact_no:
#             sms_number = customer.contact_no

#     elif voucher.type == 'Contractor' and voucher.contructor:
#         contractor = SiteSupervisor.objects.filter(id=voucher.contructor.id).first()
#         if contractor and contractor.phone:
#             sms_number = contractor.phone

#     # Optional: send SMS
#     if sms_number:
#         if not send_sms(sms_number, sms_message):
#             print("SMS sending failed (ignored).")

#     return redirect(reverse('debit_voucher_pdf', args=[voucher.pk]))
    
    
    



# import re


# @login_required
# def approve_dr_voucher(request, pk):
#     voucher = get_object_or_404(DebitVoucher, pk=pk)

#     if voucher.approval_dr_status:
#         return redirect('debitvoucher_list')

#     # Handle advance payment
#     if voucher.advance_pay:
#         RequisitionApprovalPayment.objects.create(
#             requisition=None,
#             requi_item_name=None,
#             requi_uniq_id=None,
#             supplier=getattr(voucher, 'vendor', None),
#             payment_type='advance_pay',
#             requi_amount=voucher.amount,
#             requisition_date=voucher.date or timezone.now().date()
#         )

#     # Auto-generate mr_or_bill_no if missing
#     if not voucher.mr_or_bill_no:
#         base_code = "MBD-"
#         last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"
#         while DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#             next_id += 1
#             generated_code = f"{base_code}{next_id:05d}"
#         voucher.mr_or_bill_no = generated_code

#     # Extract numeric ID from expense string
#     expense_obj = None
#     if voucher.expense:
#         match = re.match(r"(\d+)\s*-\s*.*", str(voucher.expense))
#         if match:
#             expense_id = int(match.group(1))
#             expense_obj = HeadOfExpense.objects.filter(id=expense_id).first()
#         voucher.expense = expense_obj.head_exp_name if expense_obj else voucher.expense

#     # Mark voucher approved
#     voucher.approval_dr_status = True
#     voucher.save()

#     # Update cash balance
#     try:
#         cash_type = CashType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount = (cash_type.type_amount or 0) - (voucher.amount or 0)
#         cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
#         cash_type.save()
#     except CashType.DoesNotExist:
#         cash_type = None

#     # Transaction History
#     TransactionHistory.objects.create(
#         project=voucher.project_name,
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount,
#         cheque_number=voucher.cheque_number,
#         date=voucher.date,
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         reference=voucher.mr_or_bill_no,
#         create_by=voucher.create_dr,
#         particulars=voucher.particulars,
#         tbl_id=voucher.id,
#         tbl_name='Payment',
#     )

#     # Ledger Entry
#     LedgerEntry.objects.create(
#         project_name=voucher.project_name,
#         type=voucher.type,
#         contructor=getattr(voucher, 'contructor', None),
#         vendor=getattr(voucher, 'vendor', None),
#         customer_name=getattr(voucher, 'customer_name', None),
#         bankName=getattr(voucher, 'bankName', None),
#         exp_name=expense_obj,
#         empl_name=getattr(voucher, 'empl_name', None),
#         donation_name=getattr(voucher, 'donation_name', None),
#         invest_name=getattr(voucher, 'invest_name', None),
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         cash_type=voucher.cash_type,
#         cheque_number=voucher.cheque_number,
#         head=voucher.head_of_account,
#         mr_or_bill_no=voucher.mr_or_bill_no,
#         date=voucher.date or timezone.now().date(),
#         description=voucher.particulars or '',
#         debit=voucher.amount or 0,
#         credit=0,
#         carrier=getattr(voucher, 'carrier', None),
#         loan_status='payment',
#         tbl_id=voucher.id,
#         tbl_name='Payment'
#     )

#     # ----------------------------
#     # SMS Notification
#     # ----------------------------
#     sms_number = None
#     sms_message = (
#         f"Received Amount!\n"
#         f"Amount: {voucher.amount}\n"
#         f"Date: {voucher.date}\n"
#         f"Voucher: {voucher.mr_or_bill_no}"
#     )

#     if voucher.type == 'Vendor' and voucher.vendor:
#         supplier = Suppliers.objects.filter(id=voucher.vendor.id).first()
#         if supplier and supplier.phone:
#             sms_number = supplier.phone

#     elif voucher.type == 'Customer' and voucher.customer_name:
#         customer = Customer.objects.filter(id=voucher.customer_name.id).first()
#         if customer and customer.contact_no:
#             sms_number = customer.contact_no

#     elif voucher.type == 'Contractor' and voucher.contructor:
#         contractor = SiteSupervisor.objects.filter(id=voucher.contructor.id).first()
#         if contractor and contractor.phone:
#             sms_number = contractor.phone

#     # Optional: send SMS
#     if sms_number:
#         if not send_sms(sms_number, sms_message):
#             print("SMS sending failed (ignored).")

#     return redirect(reverse('debit_voucher_pdf', args=[voucher.pk]))





@login_required
def add_debitvoucher(request):
    form = DebitVoucherForm(request.POST or None)

    if form.is_valid():
        debit_voucher = form.save(commit=False)

        cheque_id = request.POST.get('cheque_number')  # ID from dropdown

        if cheque_id:
            try:
                cheque = MainCheque.objects.get(id=cheque_id)

                # Save the actual cheque number text into DebitVoucher
                debit_voucher.cheque_number = cheque.cheque_number  

                debit_voucher.save()

                # Update MainCheque status
                cheque.status = 'used'
                cheque.remarks = debit_voucher.particulars or ''
                cheque.issue_date = debit_voucher.date
                cheque.amount = debit_voucher.amount
                cheque.save()

            except MainCheque.DoesNotExist:
                print("Cheque not found")
        else:
            debit_voucher.save()

        return redirect('debitvoucher_list')

    return render(
        request,
        'debitvoucher/add_debitvoucher.html',
        {
            'form': form,
            'expenses': HeadOfExpense.objects.all(),
            'today': date.today().strftime('%Y-%m-%d'),
        }
    )




# from decimal import Decimal
# from datetime import date
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.db import transaction
# from django.utils import timezone
# from django.contrib import messages

# @login_required
# @transaction.atomic
# def requi_contractor_payment(request, id):
#     requis_pay = get_object_or_404(BillRequisitionApprovalPayment, id=id)
#     contractor_obj = requis_pay.contractors  # SiteSupervisor instance

#     # ✅ Get all payments for this contractor
#     payments = BillRequisitionApprovalPayment.objects.filter(contractors=contractor_obj)

#     # ✅ Calculate totals
#     total_purchase = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'purchase_pay')
#     total_advance = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'advance_pay')
#     total_approval = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'approval_pay')
#     total_requisition = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'requisition_pay')

#     # ✅ Default balance calculation
#     balance_amount = total_purchase - (total_advance + total_approval)
#     if total_purchase == 0 and total_advance == 0 and total_approval == 0:
#         balance_amount = total_requisition
#     balance_amount = max(balance_amount, Decimal('0.00'))

#     if request.method == 'POST':
#         amount_val = request.POST.get('amount')
#         head_of_account_val = request.POST.get('head_of_account')
#         project_name_val = request.POST.get('project_name')
#         cash_type_val = request.POST.get('cash_type')
#         bill_phase_val = request.POST.get('bill_phase')
#         bill_date_val = request.POST.get('bill_date')
#         mr_or_bill_no_val = request.POST.get('mr_or_bill_no')
#         date_val = request.POST.get('date')
#         particulars_val = request.POST.get('particulars')
#         carrier_val = request.POST.get('carrier')
#         cheque_number_id = request.POST.get('cheque_number')
#         create_dr_val = request.POST.get('create_dr') or str(request.user.get_full_name())

#         # ✅ Resolve CashType instance safely whether cash_type is a ForeignKey or CharField
#         cash_obj = None
#         if cash_type_val:
#             try:
#                 # Check if it's an ID (digit) or name string
#                 if str(cash_type_val).isdigit():
#                     cash_obj = CashType.objects.filter(id=int(cash_type_val)).first()
#                 if not cash_obj:
#                     cash_obj = CashType.objects.filter(cash_type_name=cash_type_val).first()
#             except Exception:
#                 cash_obj = None

#         # ✅ Auto-generate mr_or_bill_no if missing
#         if not mr_or_bill_no_val:
#             base_code = "MBD-"
#             last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#             next_id = (last.id + 1) if last else 1
#             mr_or_bill_no_val = f"{base_code}{next_id:05d}"
#             while DebitVoucher.objects.filter(mr_or_bill_no=mr_or_bill_no_val).exists():
#                 next_id += 1
#                 mr_or_bill_no_val = f"{base_code}{next_id:05d}"

#         # ✅ Create DebitVoucher (handles foreign key assignment safely)
#         debit_voucher_kwargs = {
#             'type': 'Contractor',
#             'contructor': contractor_obj,
#             'bill_phase': bill_phase_val,
#             'bill_date': bill_date_val if bill_date_val else None,
#             'mr_or_bill_no': mr_or_bill_no_val,
#             'date': date_val if date_val else timezone.now().date(),
#             'amount': Decimal(amount_val) if amount_val else Decimal('0.00'),
#             'particulars': particulars_val,
#             'carrier': carrier_val,
#             'create_dr': create_dr_val,
#             'approval_dr_status': True
#         }

#         if head_of_account_val:
#             debit_voucher_kwargs['head_of_account_id'] = head_of_account_val
#         if project_name_val:
#             debit_voucher_kwargs['project_name_id'] = project_name_val

#         # Assign cash_type based on field type compatibility
#         try:
#             debit_voucher = DebitVoucher(**debit_voucher_kwargs)
#             # Try assigning object if it's a ForeignKey, otherwise assign name/string
#             debit_voucher.cash_type = cash_obj if cash_obj else cash_type_val
#             debit_voucher.save()
#         except Exception:
#             # Fallback if cash_type expects string name instead of instance
#             debit_voucher_kwargs['cash_type'] = cash_obj.cash_type_name if cash_obj else cash_type_val
#             debit_voucher = DebitVoucher.objects.create(**debit_voucher_kwargs)

#         # ✅ Cheque Update Section
#         cheque_number_str = None
#         if cheque_number_id:
#             try:
#                 cheque = MainCheque.objects.get(id=cheque_number_id)
#                 cheque_number_str = cheque.cheque_number
#                 debit_voucher.cheque_number = cheque_number_str
#                 debit_voucher.save()

#                 cheque.status = 'used'
#                 cheque.remarks = debit_voucher.particulars or ''
#                 cheque.issue_date = debit_voucher.date
#                 cheque.amount = debit_voucher.amount
#                 cheque.save()
#             except MainCheque.DoesNotExist:
#                 pass

#         # ✅ Create BillRequisitionApprovalPayment entry
#         BillRequisitionApprovalPayment.objects.create(
#             requisition=requis_pay.requisition,
#             requi_item_name=requis_pay.requi_item_name,
#             requi_uniq_id=requis_pay.requi_uniq_id,
#             contractors=contractor_obj,
#             payment_type='approval_pay',
#             requi_amount=debit_voucher.amount,
#             debit_voucher=debit_voucher,
#             requisition_date=debit_voucher.date or timezone.now().date()
#         )

#         # ✅ Update CashType balance amount
#         if cash_obj:
#             try:
#                 cash_obj.type_amount -= debit_voucher.amount
#                 cash_obj.type_note = f"Payment of voucher ID {debit_voucher.id}"
#                 cash_obj.save()
#             except Exception:
#                 pass

#         # ✅ Create TransactionHistory
#         TransactionHistory.objects.create(
#             project=debit_voucher.project_name,
#             transaction_type=debit_voucher.type,
#             head_of_account=debit_voucher.head_of_account,
#             cash_type=cash_obj,
#             amount=debit_voucher.amount,
#             cheque_number=debit_voucher.cheque_number,
#             date=debit_voucher.date,
#             type_name=contractor_obj,
#             reference=debit_voucher.mr_or_bill_no,
#             create_by=debit_voucher.create_dr,
#             particulars=debit_voucher.particulars,
#             tbl_id=debit_voucher.id,
#             tbl_name='Payment'
#         )

#         # ✅ Create LedgerEntry with unique mr no check
#         ledger_mr_no = debit_voucher.mr_or_bill_no
#         suffix = 1
#         while LedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
#             ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
#             suffix += 1

#         LedgerEntry.objects.create(
#             project_name=debit_voucher.project_name,
#             type=debit_voucher.type,
#             contructor=contractor_obj,
#             type_name=
#             cash_type=cash_obj,
#             cheque_number=debit_voucher.cheque_number,
#             head=debit_voucher.head_of_account,
#             mr_or_bill_no=ledger_mr_no,
#             date=debit_voucher.date or timezone.now(),
#             description=debit_voucher.particulars or '',
#             debit=debit_voucher.amount,
#             credit=0,
#             carrier=debit_voucher.carrier,
#             loan_status='payment',
#             tbl_id=debit_voucher.id,
#             tbl_name='Payment'
#         )

#         messages.success(request, "Contractor payment voucher saved successfully!")
#         return redirect('bill_reqs_payment_list')

#     form = DebitVoucherForm(initial={
#         'type': 'Contructor',
#         'contructor': contractor_obj.id if contractor_obj else None,
#         'amount': balance_amount,
#         'particulars': f"Payment for Contractor: {contractor_obj.supervisor_name if contractor_obj else 'N/A'}",
#     })

#     context = {
#         'form': form,
#         'today': date.today().strftime('%Y-%m-%d'),
#         'contractor': contractor_obj,
#         'max_amount': balance_amount,
#     }

#     return render(request, 'debitvoucher/requi_contractor_payment.html', context)

from decimal import Decimal
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.contrib import messages

@login_required
@transaction.atomic
def requi_contractor_payment(request, id):
    requis_pay = get_object_or_404(BillRequisitionApprovalPayment, id=id)
    contractor_obj = requis_pay.contractors  # SiteSupervisor instance

    # ✅ Get all payments for this contractor
    payments = BillRequisitionApprovalPayment.objects.filter(contractors=contractor_obj)

    # ✅ Calculate totals
    total_purchase = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'purchase_pay')
    total_advance = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'advance_pay')
    total_approval = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'approval_pay')
    total_requisition = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'requisition_pay')

    # ✅ Default balance calculation
    balance_amount = total_purchase - (total_advance + total_approval)
    if total_purchase == 0 and total_advance == 0 and total_approval == 0:
        balance_amount = total_requisition
    balance_amount = max(balance_amount, Decimal('0.00'))

    if request.method == 'POST':
        amount_val = request.POST.get('amount')
        head_of_account_val = request.POST.get('head_of_account')
        project_name_val = request.POST.get('project_name')
        cash_type_val = request.POST.get('cash_type')
        bill_phase_val = request.POST.get('bill_phase')
        bill_date_val = request.POST.get('bill_date')
        mr_or_bill_no_val = request.POST.get('mr_or_bill_no')
        date_val = request.POST.get('date')
        particulars_val = request.POST.get('particulars')
        carrier_val = request.POST.get('carrier')
        cheque_number_id = request.POST.get('cheque_number')
        create_dr_val = request.POST.get('create_dr') or str(request.user.get_full_name())

        # ✅ Resolve CashType instance safely whether cash_type is a ForeignKey or CharField
        cash_obj = None
        if cash_type_val:
            try:
                if str(cash_type_val).isdigit():
                    cash_obj = CashType.objects.filter(id=int(cash_type_val)).first()
                if not cash_obj:
                    cash_obj = CashType.objects.filter(cash_type_name=cash_type_val).first()
            except Exception:
                cash_obj = None

        # ✅ Auto-generate mr_or_bill_no if missing
        if not mr_or_bill_no_val:
            base_code = "MBD-"
            last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            mr_or_bill_no_val = f"{base_code}{next_id:05d}"
            while DebitVoucher.objects.filter(mr_or_bill_no=mr_or_bill_no_val).exists():
                next_id += 1
                mr_or_bill_no_val = f"{base_code}{next_id:05d}"

        # ✅ Create DebitVoucher (handles foreign key assignment safely)
        debit_voucher_kwargs = {
            'type': 'Contractor',
            'contructor': contractor_obj,
            'bill_phase': bill_phase_val,
            'bill_date': bill_date_val if bill_date_val else None,
            'mr_or_bill_no': mr_or_bill_no_val,
            'date': date_val if date_val else timezone.now().date(),
            'amount': Decimal(amount_val) if amount_val else Decimal('0.00'),
            'particulars': particulars_val,
            'carrier': carrier_val,
            'create_dr': create_dr_val,
            'approval_dr_status': True
        }

        if head_of_account_val:
            debit_voucher_kwargs['head_of_account_id'] = head_of_account_val
        if project_name_val:
            debit_voucher_kwargs['project_name_id'] = project_name_val

        try:
            debit_voucher = DebitVoucher(**debit_voucher_kwargs)
            debit_voucher.cash_type = cash_obj if cash_obj else cash_type_val
            debit_voucher.save()
        except Exception:
            debit_voucher_kwargs['cash_type'] = cash_obj.cash_type_name if cash_obj else cash_type_val
            debit_voucher = DebitVoucher.objects.create(**debit_voucher_kwargs)

        # ✅ Cheque Update Section
        cheque_number_str = None
        if cheque_number_id:
            try:
                cheque = MainCheque.objects.get(id=cheque_number_id)
                cheque_number_str = cheque.cheque_number
                debit_voucher.cheque_number = cheque_number_str
                debit_voucher.save()

                cheque.status = 'used'
                cheque.remarks = debit_voucher.particulars or ''
                cheque.issue_date = debit_voucher.date
                cheque.amount = debit_voucher.amount
                cheque.save()
            except MainCheque.DoesNotExist:
                pass

        # ✅ Create BillRequisitionApprovalPayment entry
        BillRequisitionApprovalPayment.objects.create(
            requisition=requis_pay.requisition,
            requi_item_name=requis_pay.requi_item_name,
            requi_uniq_id=requis_pay.requi_uniq_id,
            contractors=contractor_obj,
            payment_type='approval_pay',
            requi_amount=debit_voucher.amount,
            debit_voucher=debit_voucher,
            requisition_date=debit_voucher.date or timezone.now().date()
        )

        # ✅ Update CashType balance amount
        if cash_obj:
            try:
                cash_obj.type_amount -= debit_voucher.amount
                cash_obj.type_note = f"Payment of voucher ID {debit_voucher.id}"
                cash_obj.save()
            except Exception:
                pass

        # ✅ Create TransactionHistory
        TransactionHistory.objects.create(
            project=debit_voucher.project_name,
            transaction_type=debit_voucher.type,
            head_of_account=debit_voucher.head_of_account,
            cash_type=cash_obj,
            amount=debit_voucher.amount,
            cheque_number=debit_voucher.cheque_number,
            date=debit_voucher.date,
            type_name=contractor_obj,
            reference=debit_voucher.mr_or_bill_no,
            create_by=debit_voucher.create_dr,
            particulars=debit_voucher.particulars,
            tbl_id=debit_voucher.id,
            tbl_name='Payment'
        )

        # ✅ Create LedgerEntry with unique mr no check
        ledger_mr_no = debit_voucher.mr_or_bill_no
        suffix = 1
        while LedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
            ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
            suffix += 1

        LedgerEntry.objects.create(
            project_name=debit_voucher.project_name,
            type=debit_voucher.type,
            contructor=contractor_obj,
            type_name=contractor_obj.supervisor_name if hasattr(contractor_obj, 'supervisor_name') else str(contractor_obj),
            cash_type=cash_obj,
            cheque_number=debit_voucher.cheque_number,
            head=debit_voucher.head_of_account,
            mr_or_bill_no=ledger_mr_no,
            date=debit_voucher.date or timezone.now(),
            description=debit_voucher.particulars or '',
            debit=debit_voucher.amount,
            credit=0,
            carrier=debit_voucher.carrier,
            loan_status='payment',
            tbl_id=debit_voucher.id,
            tbl_name='Payment'
        )

        messages.success(request, "Contractor payment voucher saved successfully!")
        return redirect('bill_reqs_payment_list')

    form = DebitVoucherForm(initial={
        'type': 'Contructor',
        'contructor': contractor_obj.id if contractor_obj else None,
        'amount': balance_amount,
        'particulars': f"Payment for Contractor: {contractor_obj.supervisor_name if contractor_obj else 'N/A'}",
    })

    context = {
        'form': form,
        'today': date.today().strftime('%Y-%m-%d'),
        'contractor': contractor_obj,
        'max_amount': balance_amount,
    }

    return render(request, 'debitvoucher/requi_contractor_payment.html', context)
    



@login_required
@transaction.atomic
def requi_supplier_payment(request, id):
    requis_pay = get_object_or_404(RequisitionApprovalPayment, id=id)
    supplier_obj = requis_pay.supplier

    # ✅ Get all payments for this supplier
    payments = RequisitionApprovalPayment.objects.filter(supplier=supplier_obj)

    # ✅ Calculate totals
    total_purchase = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'purchase_pay')
    total_advance = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'advance_pay')
    total_approval = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'approval_pay')
    total_requisition = sum(p.requi_amount or 0 for p in payments if p.payment_type == 'requisition_pay')

    # ✅ Default balance calculation
    balance_amount = total_purchase - (total_advance + total_approval)
    if total_purchase == 0 and total_advance == 0 and total_approval == 0:
        balance_amount = total_requisition
    balance_amount = max(balance_amount, 0)

    # ✅ Prepare form
    if request.method == 'GET':
        initial_data = {
            'type': 'Vendor',
            'vendor': supplier_obj.id if supplier_obj else None,
            'amount': balance_amount,
            'particulars': f"Payment for Supplier: {supplier_obj.supplier_name}",
        }
        form = DebitVoucherForm(initial=initial_data)
    else:
        form = DebitVoucherForm(request.POST)

    if form.is_valid():
        debit_voucher = form.save(commit=False)

        # ✅ Auto-generate mr_or_bill_no if missing
        if not debit_voucher.mr_or_bill_no:
            base_code = "MBD-"
            last = DebitVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            generated = f"{base_code}{next_id:05d}"

            while DebitVoucher.objects.filter(mr_or_bill_no=generated).exists():
                next_id += 1
                generated = f"{base_code}{next_id:05d}"

            debit_voucher.mr_or_bill_no = generated

        # ✅ Auto-approve
        debit_voucher.approval_dr_status = True
        debit_voucher.save()

        # ✅ Create RequisitionApprovalPayment entry
        RequisitionApprovalPayment.objects.create(
            requisition=requis_pay.requisition,
            requi_item_name=requis_pay.requi_item_name,
            requi_uniq_id=requis_pay.requi_uniq_id,
            supplier=supplier_obj,
            payment_type='approval_pay',
            requi_amount=debit_voucher.amount,
            debit_voucher=debit_voucher,
            requisition_date=debit_voucher.date or timezone.now().date()
        )

        # ✅ Update CashType
        cash_obj = None
        if debit_voucher.cash_type:
            try:
                cash_obj = CashType.objects.get(cash_type_name=debit_voucher.cash_type)
                cash_obj.type_amount -= debit_voucher.amount
                cash_obj.type_note = f"Payment of voucher ID {debit_voucher.id}"
                cash_obj.save()
            except CashType.DoesNotExist:
                cash_obj = None

        # ------------------------------------------------------------------
        # ✅ NEW UPDATED CHEQUE UPDATE SECTION (your requested replacement)
        # ------------------------------------------------------------------
        cheque_id = request.POST.get('cheque_number')  # ID from dropdown

        if cheque_id:
            try:
                cheque = MainCheque.objects.get(id=cheque_id)

                # Save the TEXT cheque number into DebitVoucher
                debit_voucher.cheque_number = cheque.cheque_number
                debit_voucher.save()

                # Update MainCheque
                cheque.status = 'used'
                cheque.remarks = debit_voucher.particulars or ''
                cheque.issue_date = debit_voucher.date
                cheque.amount = debit_voucher.amount
                cheque.save()

            except MainCheque.DoesNotExist:
                print("⚠️ Cheque not found")
        else:
            # No cheque selected → save again normally
            debit_voucher.save()
        # ------------------------------------------------------------------

        # ✅ Create TransactionHistory
        TransactionHistory.objects.create(
            project=debit_voucher.project_name,
            transaction_type=debit_voucher.type,
            head_of_account=debit_voucher.head_of_account,
            cash_type=cash_obj,
            amount=debit_voucher.amount,
            cheque_number=debit_voucher.cheque_number,
            date=debit_voucher.date,
            type_name=debit_voucher.vendor if debit_voucher.type == 'Vendor' else None,
            reference=debit_voucher.mr_or_bill_no,
            create_by=debit_voucher.create_dr,
            particulars=debit_voucher.particulars,
            tbl_id=debit_voucher.id,
            tbl_name='Payment'
        )

        # ✅ Create LedgerEntry with safe unique mr no
        ledger_mr_no = debit_voucher.mr_or_bill_no
        suffix = 1
        while LedgerEntry.objects.filter(mr_or_bill_no=ledger_mr_no).exists():
            ledger_mr_no = f"{debit_voucher.mr_or_bill_no}-{suffix}"
            suffix += 1

        LedgerEntry.objects.create(
            project_name=debit_voucher.project_name,
            type=debit_voucher.type,
            contructor=getattr(debit_voucher, 'contructor', None),
            vendor=getattr(debit_voucher, 'vendor', None),
            customer_name=getattr(debit_voucher, 'customer_name', None),
            bankName=getattr(debit_voucher, 'bankName', None),
            exp_name=getattr(debit_voucher, 'exp_name', None),
            empl_name=getattr(debit_voucher, 'empl_name', None),
            invest_name=getattr(debit_voucher, 'invest_name', None),
            type_name=debit_voucher.expense if debit_voucher.type == 'Expense' and debit_voucher.expense else None,
            cash_type=cash_obj,
            cheque_number=debit_voucher.cheque_number,
            head=debit_voucher.head_of_account,
            mr_or_bill_no=ledger_mr_no,
            date=debit_voucher.date or timezone.now(),
            description=debit_voucher.particulars or '',
            debit=debit_voucher.amount,
            credit=0,
            carrier=getattr(debit_voucher, 'carrier', None),
            loan_status='payment',
            tbl_id=debit_voucher.id,
            tbl_name='Payment'
        )

        return redirect('requisition_payment_list')

    context = {
        'form': form,
        'today': date.today().strftime('%Y-%m-%d'),
        'supplier': supplier_obj,
        'max_amount': balance_amount,
    }

    return render(request, 'debitvoucher/requi_supplier_payment.html', context)

    
    




from django.utils import timezone
@login_required
def edit_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitVoucher, pk=pk)
    form = DebitVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        updated_voucher = form.save()

        # Get existing ledger entry linked to this DebitVoucher
        try:
            ledger_entry = LedgerEntry.objects.get(tbl_id=str(updated_voucher.id), tbl_name="Payment")
        except LedgerEntry.DoesNotExist:
            # If you want, you can raise an error or skip updating
            ledger_entry = None

        if ledger_entry:
            # Map fields from DebitVoucher -> LedgerEntry
            ledger_entry.project_name = updated_voucher.project_name
            ledger_entry.type = updated_voucher.type or ''
            ledger_entry.contructor = updated_voucher.contructor
            ledger_entry.vendor = updated_voucher.vendor
            ledger_entry.exp_name = form.cleaned_data.get('exp_name')  # ✅ get from form
            ledger_entry.empl_name = getattr(updated_voucher, 'empl_name', None)
            ledger_entry.capi_name = updated_voucher.capi_name
            ledger_entry.invest_name = updated_voucher.invest_name
            ledger_entry.cash_type = updated_voucher.cash_type
            ledger_entry.bankName = None
            ledger_entry.cheque_number = updated_voucher.cheque_number
            ledger_entry.head = updated_voucher.head_of_account
            ledger_entry.date = updated_voucher.date or timezone.now().date()
            ledger_entry.description = updated_voucher.particulars or ''
            ledger_entry.debit = updated_voucher.amount or 0
            ledger_entry.credit = 0
            ledger_entry.carrier = getattr(updated_voucher, 'carrier', None)

            ledger_entry.save()
            
            
            TransactionHistory.objects.update_or_create(
                tbl_id=str(updated_voucher.id),       
                tbl_name="Payment",               
                defaults={
                    "project": updated_voucher.project_name,
                    "transaction_type": "Debit",
                    "head_of_account": updated_voucher.head_of_account,
                    "cash_type": updated_voucher.cash_type,
                    "cheque_number": updated_voucher.cheque_number,
                    "amount": updated_voucher.amount,
                    "date": updated_voucher.date or timezone.now().date(),
                    "type_name": updated_voucher.type,
                    "reference": getattr(updated_voucher, 'voucher_no', None),
                    "create_by": request.user.username,
                    "particulars": updated_voucher.particulars,
                }
            )


        return redirect('debitvoucher_list')

    # Pass expenses to template for the Expense dropdown
    expenses = HeadOfExpense.objects.all().order_by('head_exp_name')

    return render(request, 'debitvoucher/edit_debitvoucher.html', {
        'form': form,
        'voucher': voucher,
        'expenses': expenses
    })



@login_required
def delete_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitVoucher, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Log before delete
            log_deleted_data(voucher, request.user)

            # Delete LedgerEntry linked by tbl_id
            LedgerEntry.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Payment"
            ).delete()

            # Delete TransactionHistory linked by tbl_id
            TransactionHistory.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Payment"
            ).delete()

            # Finally delete DebitVoucher
            voucher.delete()

        return redirect('debitvoucher_list')

    return render(
        request,
        'debitvoucher/delete_debitvoucher.html',
        {'voucher': voucher}
    )



@login_required
def details_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitVoucher, pk=pk)
    return render(request, 'debitvoucher/details_debitvoucher.html', {'voucher': voucher})


from num2words import num2words
@login_required
def debit_voucher_pdf(request, pk):
    voucher = get_object_or_404(DebitVoucher, pk=pk)

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
    return render(request, 'debitvoucher/print_debitvoucher.html', context)
    
    
## Cash Type..................
@login_required
def vendor_cashtype_update(request):
    project_id = request.POST.get('project_id') or request.GET.get('project_id')
    supplier_id = request.POST.get('supplier_id') or request.GET.get('supplier_id')

    selected_project = None
    selected_supplier = None

    if project_id:
        try:
            selected_project = ProjectFirstLevelName.objects.get(id=project_id)
        except ProjectFirstLevelName.DoesNotExist:
            selected_project = None

    if supplier_id:
        try:
            selected_supplier = Suppliers.objects.get(id=supplier_id)
        except Suppliers.DoesNotExist:
            selected_supplier = None

    form = DebitVoucherForm(request.POST or None) 

    context = {
        'form': form,
        'project_id': project_id,
        'supplier_id': supplier_id,
        'selected_project': selected_project,
        'selected_supplier': selected_supplier,
    }
    return render(request, 'debitvoucher/vendor_cashtype_update.html', context)


@login_required
def vendor_cashtype_update_submit(request):
    project_id = request.GET.get('project_id')
    supplier_id = request.GET.get('supplier_id')

    form = DebitVoucherForm(request.POST or None)

    if request.method == 'POST' and form.is_valid() and project_id and supplier_id:
        cash_type = form.cleaned_data.get('cash_type')
        cheque_number = form.cleaned_data.get('cheque_number')

        DebitVoucher.objects.filter(
            project_name_id=project_id,
            vendor_id=supplier_id,
            requi_id__isnull=False,
            return_requisition="No"
        ).update(
            cash_type=cash_type,
            cheque_number=cheque_number,
        )

        return redirect('debitvoucher_list')

    

## journal voucher ##
@login_required
def journal_voucher_list(request):
    vouchers = JournalVoucher.objects.all()
    return render(request, 'journalvouchers/journal_vouchers_list.html', {'vouchers': vouchers})


# @login_required
# def journal_voucher_add(request):
#     form = JournalVoucherForm(request.POST or None)

#     customer_data = Customer.objects.filter(status=True).values('id', 'customer_name')
#     supervisor_data = SiteSupervisor.objects.filter(active=True).values('id', 'supervisor_name')
#     supplier_data = Suppliers.objects.filter(active=True).values('id', 'supplier_name')
#     cash_data = CashType.objects.all().values('id', 'cash_type_name')
#     employee_data = Employee.objects.filter(active_status=True).values('id', 'employee_name')

#     combined_options = []

#     for c in customer_data:
#         combined_options.append({"type": "Customer", "id": c['id'], "name": c['customer_name']})
#     for s in supervisor_data:
#         combined_options.append({"type": "SiteSupervisor", "id": s['id'], "name": s['supervisor_name']})
#     for s in supplier_data:
#         combined_options.append({"type": "Supplier", "id": s['id'], "name": s['supplier_name']})
#     for c in cash_data:
#         combined_options.append({"type": "CashType", "id": c['id'], "name": c['cash_type_name']})
#     for e in employee_data:
#         combined_options.append({"type": "Employee", "id": e['id'], "name": e['employee_name']})

#     if request.method == 'POST' and form.is_valid():
#         form.save()
#         return redirect('journal_voucher_list')  # Redirect to the voucher list page

#     context = {
#         'form': form,
#         'combined_options': combined_options,
#     }
#     return render(request, 'journalvouchers/add_journal_vouchers.html', context)
    

###-----------------------

@login_required
def journal_voucher_add(request):
    form = JournalVoucherForm(request.POST or None)

    customer_data = Customer.objects.filter(status=True).values('id', 'customer_name')
    supervisor_data = SiteSupervisor.objects.filter(active=True).values('id', 'supervisor_name')
    supplier_data = Suppliers.objects.filter(active=True).values('id', 'supplier_name')
    cash_data = CashType.objects.all().values('id', 'cash_type_name')
    employee_data = Employee.objects.filter(active_status=True).values('id', 'employee_name')

    combined_options = []

    for c in customer_data:
        combined_options.append({"type": "Customer", "id": c['id'], "name": c['customer_name']})
    for s in supervisor_data:
        combined_options.append({"type": "SiteSupervisor", "id": s['id'], "name": s['supervisor_name']})
    for s in supplier_data:
        combined_options.append({"type": "Supplier", "id": s['id'], "name": s['supplier_name']})
    for c in cash_data:
        combined_options.append({"type": "CashType", "id": c['id'], "name": c['cash_type_name']})
    for e in employee_data:
        combined_options.append({"type": "Employee", "id": e['id'], "name": e['employee_name']})

    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)  

        if not instance.mr_or_bill_no:
            base_code = "AJUR-"
            last_voucher = (
                JournalVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                .order_by('-id')
                .first()
            )
            next_id = (last_voucher.id + 1) if last_voucher else 1
            generated_code = f"{base_code}{next_id:05d}"

            while JournalVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                next_id += 1
                generated_code = f"{base_code}{next_id:05d}"

            instance.mr_or_bill_no = generated_code

        instance.save()  
        
        TransactionHistory.objects.create(
            project=instance.project,
            transaction_type=instance.head_of_account_to.get_transaction_type(),
            head_of_account=instance.head_of_account_to,
            cash_type=None,
            amount=instance.amount,
            cheque_number=instance.cheque_number,
            date=instance.date,
            type_name=instance.party_to_combined,
            reference=instance.mr_or_bill_no,
            create_by=request.user,
            particulars=instance.description,
        )
         
        TransactionHistory.objects.create(
            project=instance.project,
            #transaction_type=extract_transaction_type(instance.head_of_account_to),
            transaction_type=instance.head_of_account_from.get_transaction_type(),
            head_of_account=instance.head_of_account_from,
            cash_type=None,
            amount=instance.amount,  
            cheque_number=instance.cheque_number,
            date=instance.date,
            type_name=instance.party_from_combined,
            reference=instance.mr_or_bill_no,
            create_by=request.user,
            particulars=instance.description,
        )
        
        def map_transaction_type(tx_type):
            if tx_type == 'Supplier':
                return 'Vendor'
            return tx_type
            
        LedgerEntry.objects.create(
            project_name=instance.project,
            type=map_transaction_type(instance.head_of_account_to.get_transaction_type()),
            vendor=Suppliers.objects.filter(supplier_name=instance.party_to_combined).first() if map_transaction_type(instance.head_of_account_to.get_transaction_type()) == "Vendor" else None,
            customer_name=Customer.objects.filter(customer_name=instance.party_to_combined).first() if map_transaction_type(instance.head_of_account_to.get_transaction_type()) == "Customer" else None,
            contructor=SiteSupervisor.objects.filter(supervisor_name=instance.party_to_combined).first() if map_transaction_type(instance.head_of_account_to.get_transaction_type()) == "Contructor" else None,
            bankName=CashType.objects.filter(cash_type_name=instance.party_to_combined).first() if map_transaction_type(instance.head_of_account_to.get_transaction_type()) == "Bank" else None,
            empl_name=instance.party_to_combined if map_transaction_type(instance.head_of_account_to.get_transaction_type()) == "Employee" else None,
            type_name=instance.party_to_combined,
            cash_type=None,
            mr_or_bill_no=f"C-{instance.mr_or_bill_no}",
            head=instance.head_of_account_to,
            date=instance.date,
            description=instance.description,
            debit=0,
            credit=instance.amount
        )
        
        # Party FROM (Debit)
        LedgerEntry.objects.create(
            project_name=instance.project,
            type=map_transaction_type(instance.head_of_account_from.get_transaction_type()),
            vendor=Suppliers.objects.filter(supplier_name=instance.party_from_combined).first() if map_transaction_type(instance.head_of_account_from.get_transaction_type()) == "Vendor" else None,
            customer_name=Customer.objects.filter(customer_name=instance.party_from_combined).first() if map_transaction_type(instance.head_of_account_from.get_transaction_type()) == "Customer" else None,
            contructor=SiteSupervisor.objects.filter(supervisor_name=instance.party_from_combined).first() if map_transaction_type(instance.head_of_account_from.get_transaction_type()) == "Contructor" else None,
            bankName=CashType.objects.filter(cash_type_name=instance.party_from_combined).first() if map_transaction_type(instance.head_of_account_from.get_transaction_type()) == "Bank" else None,
            empl_name=instance.party_from_combined if map_transaction_type(instance.head_of_account_from.get_transaction_type()) == "Employee" else None,
            type_name=instance.party_from_combined,
            cash_type=None,
            mr_or_bill_no=f"D-{instance.mr_or_bill_no}",
            head=instance.head_of_account_from,
            date=instance.date,
            description=instance.description,
            debit=instance.amount,
            credit=0
        )
        return redirect('journal_voucher_list')
    
    context = {
        'form': form,
        'combined_options': combined_options,
        'today': date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'journalvouchers/add_journal_vouchers.html', context)
    
    
    
    
# @login_required
# def journal_voucher_add(request):
#     form = JournalVoucherForm(request.POST or None)

#     customer_data = Customer.objects.filter(status=True).values('id', 'customer_name')
#     supervisor_data = SiteSupervisor.objects.filter(active=True).values('id', 'supervisor_name')
#     supplier_data = Suppliers.objects.filter(active=True).values('id', 'supplier_name')
#     cash_data = CashType.objects.all().values('id', 'cash_type_name')
#     employee_data = Employee.objects.filter(active_status=True).values('id', 'employee_name')

#     combined_options = []

#     for c in customer_data:
#         combined_options.append({"type": "Customer", "id": c['id'], "name": c['customer_name']})
#     for s in supervisor_data:
#         combined_options.append({"type": "SiteSupervisor", "id": s['id'], "name": s['supervisor_name']})
#     for s in supplier_data:
#         combined_options.append({"type": "Supplier", "id": s['id'], "name": s['supplier_name']})
#     for c in cash_data:
#         combined_options.append({"type": "CashType", "id": c['id'], "name": c['cash_type_name']})
#     for e in employee_data:
#         combined_options.append({"type": "Employee", "id": e['id'], "name": e['employee_name']})

#     if request.method == 'POST' and form.is_valid():
#         instance = form.save(commit=False)  

#         if not instance.mr_or_bill_no:
#             base_code = "AJUR-"
#             last_voucher = (
#                 JournalVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#                 .order_by('-id')
#                 .first()
#             )
#             next_id = (last_voucher.id + 1) if last_voucher else 1
#             generated_code = f"{base_code}{next_id:05d}"

#             while JournalVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                 next_id += 1
#                 generated_code = f"{base_code}{next_id:05d}"

#             instance.mr_or_bill_no = generated_code

#         instance.save()  
        
#         TransactionHistory.objects.create(
#             project=instance.project,
#             transaction_type=instance.head_of_account_to.get_transaction_type(),
#             head_of_account=instance.head_of_account_to,
#             cash_type=None,
#             amount=instance.amount,
#             date=instance.date,
#             type_name=instance.party_to_combined,
#             reference=instance.mr_or_bill_no
#         )
         
#         TransactionHistory.objects.create(
#             project=instance.project,
#             #transaction_type=extract_transaction_type(instance.head_of_account_to),
#             transaction_type=instance.head_of_account_from.get_transaction_type(),
#             head_of_account=instance.head_of_account_from,
#             cash_type=None,
#             amount=instance.amount,  
#             date=instance.date,
#             type_name=instance.party_from_combined,
#             reference=instance.mr_or_bill_no
#         )
#         LedgerEntry.objects.create(
#             project_name=instance.project,
#             type=instance.head_of_account_to.get_transaction_type(),
#             vendor=Suppliers.objects.filter(supplier_name=instance.party_to_combined).first() if instance.head_of_account_to.get_transaction_type() == "Vendor" else None,
#             customer_name=Customer.objects.filter(customer_name=instance.party_to_combined).first() if instance.head_of_account_to.get_transaction_type() == "Customer" else None,
#             contructor=SiteSupervisor.objects.filter(supervisor_name=instance.party_to_combined).first() if instance.head_of_account_to.get_transaction_type() == "Contructor" else None,
#             bankName=CashType.objects.filter(cash_type_name=instance.party_to_combined).first() if instance.head_of_account_to.get_transaction_type() == "Bank" else None,
#             empl_name=instance.party_to_combined if instance.head_of_account_to.get_transaction_type() == "Employee" else None,
#             type_name=instance.party_to_combined,
#             cash_type=None,
#             mr_or_bill_no=f"C-{instance.mr_or_bill_no}",
#             head=instance.head_of_account_to,
#             date=instance.date,
#             description=instance.description,
#             debit=0,
#             credit=instance.amount
#         )

#         # Party FROM (Debit)
#         LedgerEntry.objects.create(
#             project_name=instance.project,
#             type=instance.head_of_account_from.get_transaction_type(),
#             vendor=Suppliers.objects.filter(supplier_name=instance.party_from_combined).first() if instance.head_of_account_from.get_transaction_type() == "Supplier" else None,
#             customer_name=Customer.objects.filter(customer_name=instance.party_from_combined).first() if instance.head_of_account_from.get_transaction_type() == "Customer" else None,
#             contructor=SiteSupervisor.objects.filter(supervisor_name=instance.party_from_combined).first() if instance.head_of_account_from.get_transaction_type() == "Contructor" else None,
#             bankName=CashType.objects.filter(cash_type_name=instance.party_from_combined).first() if instance.head_of_account_from.get_transaction_type() == "Bank" else None,
#             empl_name=instance.party_from_combined if instance.head_of_account_from.get_transaction_type() == "Employee" else None,
#             type_name=instance.party_from_combined,
#             cash_type=None,
#             mr_or_bill_no=f"D-{instance.mr_or_bill_no}",
#             head=instance.head_of_account_from,
#             date=instance.date,
#             description=instance.description,
#             debit=instance.amount,
#             credit=0
#         )
#         return redirect('journal_voucher_list')
    
#     context = {
#         'form': form,
#         'combined_options': combined_options,
#         'today': date.today().strftime('%Y-%m-%d'),
#     }
#     return render(request, 'journalvouchers/add_journal_vouchers.html', context)
    
    



@login_required
def journal_voucher_edit(request, pk):
    voucher = get_object_or_404(JournalVoucher, pk=pk)
    if request.method == 'POST':
        form = JournalVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('journal_voucher_list')
    else:
        form = JournalVoucherForm(instance=voucher)
    return render(request, 'journalvouchers/edit_journal_vouchers.html', {'form': form, 'voucher': voucher})


@login_required
def journal_voucher_delete(request, pk):
    voucher = get_object_or_404(JournalVoucher, pk=pk)
    if request.method == 'POST':
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('journal_voucher_list')
    return render(request, 'journalvouchers/delete_journal_vouchers.html', {'voucher': voucher})



@login_required
def journal_voucher_pdf(request, pk):
    voucher = get_object_or_404(JournalVoucher, pk=pk)
    def amount_to_words(amount):
        def num_to_words(n):
            ones = [
                "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
                "Sixteen", "Seventeen", "Eighteen", "Nineteen"
            ]
            tens = [
                "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
            ]

            if n < 20:
                return ones[n]
            elif n < 100:
                return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
            elif n < 1000:
                return ones[n // 100] + " Hundred" + (" " + num_to_words(n % 100) if n % 100 != 0 else "")
            elif n < 100000:
                return num_to_words(n // 1000) + " Thousand" + (" " + num_to_words(n % 1000) if n % 1000 != 0 else "")
            elif n < 10000000:
                return num_to_words(n // 100000) + " Lakh" + (" " + num_to_words(n % 100000) if n % 100000 != 0 else "")
            else:
                return num_to_words(n // 10000000) + " Crore" + (" " + num_to_words(n % 10000000) if n % 10000000 != 0 else "")

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return "Invalid Amount"

        if amount == 0:
            return "Zero Taka Only"
        else:
            return num_to_words(amount) + " Taka Only"


    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount_dr),  
    }
    return render(request, 'journalvouchers/print_journalvouchers.html', context)



## contra voucher ##
@login_required
def contra_voucher_list(request):
    vouchers = ContraVoucher.objects.all()
    return render(request, 'contra_voucher/contra_voucher_list.html', {'vouchers': vouchers})



@login_required
def contra_voucher_add(request):
    if request.method == 'POST':
        form = ContraVoucherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contra_voucher_list')
    else:
        form = ContraVoucherForm()
    return render(request, 'contra_voucher/contra_voucher_add.html', {'form': form})



@login_required
def contra_voucher_edit(request, pk):
    voucher = get_object_or_404(ContraVoucher, pk=pk)
    if request.method == 'POST':
        form = ContraVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('contra_voucher_list')
    else:
        form = ContraVoucherForm(instance=voucher)
    return render(request, 'contra_voucher/contra_voucher_edit.html', {'form': form, 'voucher': voucher})


@login_required
def contra_voucher_delete(request, pk):
    voucher = get_object_or_404(ContraVoucher, pk=pk)
    if request.method == 'POST':
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('contra_voucher_list')
    return render(request, 'contra_voucher/contra_voucher_delete.html', {'voucher': voucher})


@login_required
def contra_voucher_pdf(request, pk):
    voucher = get_object_or_404(ContraVoucher, pk=pk)
    def amount_to_words(amount):
        return f"{amount} Taka"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'contra_voucher/print_contra_voucher.html', context)




@login_required
def ledger_manage_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id') 
    form = LedgerReportForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'ledgermanage/ledger_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })



@login_required
def ledger_manage_add(request):
    if request.method == 'POST':
        form = LedgerReportForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                item = form.save(commit=False)
                item.save()

                loan_status = (item.loan_status or '').strip().lower()

                try:
                    cash_type = item.cash_type 
                    if not cash_type:
                        return redirect('ledger_manage_list')
                except (CashType.DoesNotExist, AttributeError):
                    return redirect('ledger_manage_list')

                current_balance = cash_type.type_amount or 0
                
                if loan_status == 'payment':
                    amount = item.debit
                    cash_type.type_amount = current_balance - amount
                    cash_type.type_note = f"Payment of item ID {item.id}"
                elif loan_status == 'received':
                    amount = item.credit
                    cash_type.type_amount = current_balance + amount
                    cash_type.type_note = f"Received for item ID {item.id}"
                else:
                    amount = 0  

                cash_type.save()

                TransactionHistory.objects.create(
                    project=item.project_name,
                    transaction_type=item.type,
                    head_of_account=item.head,
                    cash_type=cash_type,
                    amount=amount,
                    cheque_number=cheque_number,
                    date=item.date,
                    type_name = f"{item.type}_{item.loan_status}",
                    reference=item.cheque_number,
                    create_by=request.user,
                    particulars=item.description,
                )

            return redirect('ledger_manage_list')
    else:
        form = LedgerReportForm()

    return render(request, 'ledgermanage/ledger_manage_add.html', {'form': form})




@login_required
def ledger_manage_edit(request, pk):
    entry = get_object_or_404(LedgerEntry, pk=pk)
    if request.method == 'POST':
        form = LedgerReportForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('ledger_manage_list')
    else:
        form = LedgerReportForm(instance=entry)
    return render(request, 'ledgermanage/ledger_manage_edit.html', {'form': form, 'entry': entry})


@login_required
def ledger_entry_delete(request, pk):
    ledger_entry = get_object_or_404(LedgerEntry, pk=pk)

    if request.method == 'POST':
        log_deleted_data(ledger_entry, request.user)
        ledger_entry.delete()
        return redirect('ledger_manage_list') 
    return render(request, 'ledgermanage/ledger_manage_delete.html', {'ledger_entry': ledger_entry})


@login_required
def transaction_history_list(request):
    transactions = TransactionHistory.objects.select_related('project', 'head_of_account', 'cash_type').order_by('-date')
    return render(request, 'transactionhistory/transaction_history_list.html', {'transactions': transactions})


@login_required
def head_wise_transaction_view(request, head_id):
    head = get_object_or_404(HeadOfAccount, id=head_id)

    cash_types = CashType.objects.filter(transactionhistory__head_of_account=head).distinct()
    transactions = TransactionHistory.objects.filter(head_of_account=head).order_by('date')
    total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'head': head,
        'cash_types': cash_types,
        'transactions': transactions,
        'total_amount': total_amount,
        'print_time': timezone.now(),
    }
    return render(request, 'transactionhistory/head_wise_transactions.html', context)



@login_required
def cashType_balance_list(request):
    cash_types = CashType.objects.all().order_by('cash_type_name')
    return render(request, 'transactionhistory/cash_type_balance_list.html', {'cash_types': cash_types})


## Balance Transfer History --
@login_required
def transfer_list(request):
    transfers = BalanceTransfer.objects.all().order_by('-id')
    today = timezone.now()
    return render(request, 'transferbalance/transfer_list.html', {'transfers': transfers,'today': today})



from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import ProjectBalanceTransfer
from num2words import num2words

def number_to_bdt_words(amount):
    """Converts a decimal amount into Bangladeshi Taka words format safely."""
    try:
        amount_decimal = Decimal(str(amount))
        integer_part = int(amount_decimal)
        fractional_part = int((amount_decimal - integer_part) * 100)
        
        words = num2words(integer_part, lang='en').title() + " Taka"
        
        if fractional_part > 0:
            fractional_words = num2words(fractional_part, lang='en').title()
            words += f" and {fractional_words} Poisha"
            
        return words + " Only"
    except Exception:
        return f"{amount} Taka Only"

def project_transfer_detail(request, pk):
    transfer = get_object_or_404(ProjectBalanceTransfer, pk=pk)
    
    # Safely generate amount in words
    amount_in_words = number_to_bdt_words(transfer.transfer_amount)

    context = {
        'transfer': transfer,
        'amount_in_words': amount_in_words,
        'print_time': timezone.now(),
    }
    return render(request, 'transferbalance/project_transfer_detail.html', context)





# @login_required
# def transfer_add(request):
#     if request.method == 'POST':
#         form = BalanceTransferForm(request.POST)
#         if form.is_valid():
#             source = form.cleaned_data['source_type']
#             destination = form.cleaned_data['destination_type']
#             amount = form.cleaned_data['transfer_amount']
#             transfer_date = form.cleaned_data['transfer_date']
#             note = form.cleaned_data['note']
#             project = form.cleaned_data['project_name']

#             # Check available balance
#             if source.type_amount < amount:
#                 messages.error(request, 'Insufficient balance in Source Cash Type.')
#                 return redirect('transfer_add')

#             try:
#                 with transaction.atomic():
#                     # Save main transfer
#                     transfer = form.save()

#                     # Get or create "Balance Transfer Account" head
#                     head, _ = HeadOfAccount.objects.get_or_create(
#                         head_name='Balance Transfer Account'
#                     )

#                     # Create Ledger entries
#                     source_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=source,
#                         cash_type=source,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Transfer to {destination.cash_type_name} - {note}',
#                         debit=amount,
#                         credit=0,
#                         cheque_number=getattr(transfer, 'cheque_number', None),
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Transfer to {destination.cash_type_name}'
#                     )

#                     dest_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=destination,
#                         cash_type=destination,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Received from {source.cash_type_name} - {note}',
#                         debit=0,
#                         credit=amount,
#                         cheque_number=getattr(transfer, 'cheque_number', None),
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Received from {source.cash_type_name}'
#                     )

#                     # Create TransactionHistory entries
#                     username = request.user.username if request.user.is_authenticated else "System"
#                     cheque_number = getattr(transfer, 'cheque_number', None)
#                     ref_trans_id = f"BTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
#                     # Transfer OUT
#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=source_ledger.type,
#                         head_of_account=head,
#                         cash_type=source,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{source_ledger.type}_Out",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=source_ledger.description
#                     )

#                     # Transfer IN
#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=dest_ledger.type,
#                         head_of_account=head,
#                         cash_type=destination,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{dest_ledger.type}_In",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=dest_ledger.description
#                     )

#                     messages.success(request, 'Balance transfer saved and recorded in Transaction History.')
#                     return redirect('transfer_list')

#             except Exception as e:
#                 print("Error creating transaction:", e)
#                 messages.error(request, f"Error saving TransactionHistory: {e}")
#                 return redirect('transfer_add')

#     else:
#         form = BalanceTransferForm()

#     return render(request, 'transferbalance/transfer_add.html', {'form': form})




# @login_required
# def transfer_add(request):
#     if request.method == 'POST':
#         form = BalanceTransferForm(request.POST)
#         if form.is_valid():
#             source = form.cleaned_data['source_type']
#             destination = form.cleaned_data['destination_type']
#             amount = form.cleaned_data['transfer_amount']
#             transfer_date = form.cleaned_data['transfer_date']
#             note = form.cleaned_data['note']
#             project = form.cleaned_data['project_name']

#             # Get cheque_id from POST
#             cheque_id = request.POST.get('cheque_number')  # ID from dropdown
#             cheque_number = None
#             if cheque_id:
#                 try:
#                     cheque = MainCheque.objects.get(id=cheque_id)
#                     cheque_number = cheque.cheque_number
#                     # Update MainCheque status
#                     cheque.status = 'used'
#                     cheque.remarks = note
#                     cheque.issue_date = transfer_date
#                     cheque.amount = amount
#                     cheque.save()
#                 except MainCheque.DoesNotExist:
#                     messages.error(request, 'Selected cheque not found.')
#                     return redirect('transfer_add')

#             # Check available balance
#             if source.type_amount < amount:
#                 messages.error(request, 'Insufficient balance in Source Cash Type.')
#                 return redirect('transfer_add')

#             try:
#                 with transaction.atomic():
#                     # Save main transfer
#                     transfer = form.save(commit=False)
#                     transfer.cheque_number = cheque_number
#                     transfer.save()

#                     # Get or create "Balance Transfer Account" head
#                     head, _ = HeadOfAccount.objects.get_or_create(head_name='Balance Transfer Account')

#                     # Create Ledger entries
#                     source_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=source,
#                         cash_type=source,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Transfer to {destination.cash_type_name} - {note}',
#                         debit=amount,
#                         credit=0,
#                         cheque_number=cheque_number,
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Transfer to {destination.cash_type_name}'
#                     )

#                     dest_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=destination,
#                         cash_type=destination,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Received from {source.cash_type_name} - {note}',
#                         debit=0,
#                         credit=amount,
#                         cheque_number=cheque_number,
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Received from {source.cash_type_name}'
#                     )

#                     # Create TransactionHistory entries
#                     username = request.user.username if request.user.is_authenticated else "System"
#                     ref_trans_id = f"BTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"

#                     # Transfer OUT
#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=source_ledger.type,
#                         head_of_account=head,
#                         cash_type=source,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{source_ledger.type}_Out",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=source_ledger.description
#                     )

#                     # Transfer IN
#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=dest_ledger.type,
#                         head_of_account=head,
#                         cash_type=destination,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{dest_ledger.type}_In",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=dest_ledger.description
#                     )

#                     messages.success(request, 'Balance transfer saved and recorded in Transaction History.')
#                     return redirect('transfer_list')

#             except Exception as e:
#                 print("Error creating transaction:", e)
#                 messages.error(request, f"Error saving TransactionHistory: {e}")
#                 return redirect('transfer_add')

#     else:
#         form = BalanceTransferForm()

#     return render(request, 'transferbalance/transfer_add.html', {'form': form})



# @login_required
# def transfer_add(request):
#     if request.method == 'POST':
#         form = BalanceTransferForm(request.POST)
#         if form.is_valid():
#             source = form.cleaned_data['source_type']
#             destination = form.cleaned_data['destination_type']
#             amount = form.cleaned_data['transfer_amount']
#             transfer_date = form.cleaned_data['transfer_date']
#             note = form.cleaned_data['note']
#             project = form.cleaned_data['project_name']

#             # Handle cheque if selected
#             cheque_id = request.POST.get('cheque_number')
#             cheque_number = None
#             if cheque_id:
#                 try:
#                     cheque = MainCheque.objects.get(id=cheque_id)
#                     cheque_number = cheque.cheque_number
#                     cheque.status = 'used'
#                     cheque.remarks = note
#                     cheque.issue_date = transfer_date
#                     cheque.amount = amount
#                     cheque.save()
#                 except MainCheque.DoesNotExist:
#                     messages.error(request, 'Selected cheque not found.')
#                     return redirect('transfer_add')

#             try:
#                 with transaction.atomic():
#                     # Save main transfer
#                     transfer = form.save(commit=False)
#                     transfer.cheque_number = cheque_number
#                     transfer.save()

#                     # Ensure head exists
#                     head, _ = HeadOfAccount.objects.get_or_create(head_name='Balance Transfer Account')

#                     # Ledger entries
#                     source_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=source,
#                         cash_type=source,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Transfer to {destination.cash_type_name} - {note}',
#                         debit=amount,
#                         credit=0,
#                         cheque_number=cheque_number,
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Transfer to {destination.cash_type_name}'
#                     )

#                     dest_ledger = LedgerEntry.objects.create(
#                         project_name=project,
#                         type='Balance_Trf',
#                         type_name='Balance Transfer',
#                         bankName=destination,
#                         cash_type=destination,
#                         head=head,
#                         date=transfer_date,
#                         description=f'Received from {source.cash_type_name} - {note}',
#                         debit=0,
#                         credit=amount,
#                         cheque_number=cheque_number,
#                         carrier=getattr(transfer, 'carrier', None),
#                         balance_trf=f'Received from {source.cash_type_name}'
#                     )

#                     # Transaction History
#                     username = request.user.username if request.user.is_authenticated else "System"
#                     ref_trans_id = f"BTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"

#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=source_ledger.type,
#                         head_of_account=head,
#                         cash_type=source,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{source_ledger.type}_Out",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=source_ledger.description
#                     )

#                     TransactionHistory.objects.create(
#                         project=project,
#                         transaction_type=dest_ledger.type,
#                         head_of_account=head,
#                         cash_type=destination,
#                         amount=amount,
#                         cheque_number=cheque_number,
#                         date=transfer_date or timezone.now().date(),
#                         type_name=f"{dest_ledger.type}_In",
#                         reference=ref_trans_id,
#                         create_by=username,
#                         particulars=dest_ledger.description
#                     )

#                     messages.success(request, 'Balance transfer saved and recorded in Transaction History.')
#                     return redirect('transfer_list')

#             except Exception as e:
#                 print("Error creating transaction:", e)
#                 messages.error(request, f"Error saving TransactionHistory: {e}")
#                 return redirect('transfer_add')

#     else:
#         form = BalanceTransferForm()

#     return render(request, 'transferbalance/transfer_add.html', {'form': form})



@login_required
def transfer_add(request):
    if request.method == 'POST':
        form = BalanceTransferForm(request.POST)

        if form.is_valid():

            source = form.cleaned_data['source_type']
            destination = form.cleaned_data['destination_type']
            amount = form.cleaned_data['transfer_amount']
            transfer_date = form.cleaned_data['transfer_date']
            note = form.cleaned_data['note']
            project = form.cleaned_data['project_name']

            cheque_id = request.POST.get('cheque_number')
            cheque_number = None

            if cheque_id:
                try:
                    cheque = MainCheque.objects.get(id=cheque_id)
                    cheque_number = cheque.cheque_number
                    cheque.status = 'used'
                    cheque.remarks = note
                    cheque.issue_date = transfer_date
                    cheque.amount = amount
                    cheque.save()
                except MainCheque.DoesNotExist:
                    messages.error(request, 'Selected cheque not found.')
                    return redirect('transfer_add')

            try:
                with transaction.atomic():

                    # save transfer
                    transfer = form.save(commit=False)
                    transfer.cheque_number = cheque_number

                    # IMPORTANT:
                    # bypass model validation if clean() raises error
                    BalanceTransfer.objects.create(
                        source_type=source,
                        destination_type=destination,
                        transfer_amount=amount,
                        transfer_date=transfer_date,
                        note=note,
                        project_name=project,
                        cheque_number=cheque_number
                    )

                    head, created = HeadOfAccount.objects.get_or_create(
                        head_name='Balance Transfer Account'
                    )

                    source_ledger = LedgerEntry.objects.create(
                        project_name=project,
                        type='Balance_Trf',
                        type_name='Balance Transfer',
                        bankName=source,
                        cash_type=source,
                        head=head,
                        date=transfer_date,
                        description=f'Transfer to {destination.cash_type_name} - {note}',
                        debit=amount,
                        credit=0,
                        cheque_number=cheque_number,
                        balance_trf=f'Transfer to {destination.cash_type_name}'
                    )

                    dest_ledger = LedgerEntry.objects.create(
                        project_name=project,
                        type='Balance_Trf',
                        type_name='Balance Transfer',
                        bankName=destination,
                        cash_type=destination,
                        head=head,
                        date=transfer_date,
                        description=f'Received from {source.cash_type_name} - {note}',
                        debit=0,
                        credit=amount,
                        cheque_number=cheque_number,
                        balance_trf=f'Received from {source.cash_type_name}'
                    )

                    username = request.user.username

                    ref_trans_id = (
                        f"BTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                    )

                    TransactionHistory.objects.create(
                        project=project,
                        transaction_type='Balance_Trf',
                        head_of_account=head,
                        cash_type=source,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date,
                        type_name='Balance_Trf_Out',
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=source_ledger.description
                    )

                    TransactionHistory.objects.create(
                        project=project,
                        transaction_type='Balance_Trf',
                        head_of_account=head,
                        cash_type=destination,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date,
                        type_name='Balance_Trf_In',
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=dest_ledger.description
                    )

                    messages.success(
                        request,
                        'Balance transfer saved successfully.'
                    )

                    return redirect('transfer_list')

            except Exception as e:
                messages.error(request, str(e))
                return redirect('transfer_add')

    else:
        form = BalanceTransferForm()

    return render(
        request,
        'transferbalance/transfer_add.html',
        {'form': form}
    )
    



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import ProjectBalanceTransfer, CashType, HeadOfAccount, LedgerEntry, TransactionHistory, MainCheque
from .forms import ProjectBalanceTransferForm

@login_required
def project_transfer_list(request):
    transfers = ProjectBalanceTransfer.objects.all().order_by('-transfer_date', '-id')
    return render(request, 'transferbalance/project_transfer_list.html', {'transfers': transfers})

@login_required
def project_transfer_add(request):
    if request.method == 'POST':
        form = ProjectBalanceTransferForm(request.POST)
        if form.is_valid():
            source_proj = form.cleaned_data['source_project']
            dest_proj = form.cleaned_data['destination_project']
            source_cash = form.cleaned_data['source_cash_type']
            dest_cash = form.cleaned_data['destination_cash_type']
            amount = form.cleaned_data['transfer_amount']
            transfer_date = form.cleaned_data['transfer_date']
            note = form.cleaned_data['note']
            carrier = form.cleaned_data['carrier']

            if source_proj == dest_proj and source_cash == dest_cash:
                messages.error(request, 'Source and Destination cannot be identical.')
                return redirect('project_transfer_add')

            cheque_id = request.POST.get('cheque_number')
            cheque_number = None

            if cheque_id:
                try:
                    cheque = MainCheque.objects.get(id=cheque_id)
                    cheque_number = cheque.cheque_number
                    cheque.status = 'used'
                    cheque.remarks = note
                    cheque.issue_date = transfer_date
                    cheque.amount = amount
                    cheque.save()
                except MainCheque.DoesNotExist:
                    messages.error(request, 'Selected cheque not found.')
                    return redirect('project_transfer_add')

            try:
                with transaction.atomic():
                    # Lock and update Cash types
                    src_cash_obj = CashType.objects.select_for_update().get(id=source_cash.id)
                    src_cash_obj.type_amount -= amount
                    src_cash_obj.type_note = f"Debited {amount} for Project Transfer to {dest_proj.project_first_name}"
                    src_cash_obj.save()

                    dst_cash_obj = CashType.objects.select_for_update().get(id=dest_cash.id)
                    dst_cash_obj.type_amount += amount
                    dst_cash_obj.type_note = f"Credited {amount} for Project Transfer from {source_proj.project_first_name}"
                    dst_cash_obj.save()

                    transfer = form.save(commit=False)
                    transfer.cheque_number = cheque_number
                    transfer.save()

                    head, _ = HeadOfAccount.objects.get_or_create(head_name='Project Balance Transfer Account')

                    # Ledger Entries (Type updated to Blance_Trf)
                    source_ledger = LedgerEntry.objects.create(
                        project_name=source_proj,
                        type='Blance_Trf',
                        type_name='Project Balance Transfer',
                        bankName=source_cash,
                        cash_type=source_cash,
                        head=head,
                        date=transfer_date,
                        description=f'Transfer to {dest_proj.project_first_name} ({dest_cash.cash_type_name}) - {note}',
                        debit=amount,
                        credit=0,
                        cheque_number=cheque_number,
                    )

                    dest_ledger = LedgerEntry.objects.create(
                        project_name=dest_proj,
                        type='Blance_Trf',
                        type_name='Project Balance Transfer',
                        bankName=dest_cash,
                        cash_type=dest_cash,
                        head=head,
                        date=transfer_date,
                        description=f'Received from {source_proj.project_first_name} ({source_cash.cash_type_name}) - {note}',
                        debit=0,
                        credit=amount,
                        cheque_number=cheque_number,
                    )

                    username = request.user.username
                    ref_trans_id = f"PBTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    TransactionHistory.objects.create(
                        project=source_proj,
                        transaction_type='Blance_Trf',
                        head_of_account=head,
                        cash_type=source_cash,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date,
                        type_name='Blance_Trf_Out',
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=source_ledger.description
                    )

                    TransactionHistory.objects.create(
                        project=dest_proj,
                        transaction_type='Blance_Trf',
                        head_of_account=head,
                        cash_type=dest_cash,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date,
                        type_name='Blance_Trf_In',
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=dest_ledger.description
                    )

                    messages.success(request, 'Project balance transfer completed successfully.')
                    return redirect('project_transfer_list')

            except Exception as e:
                messages.error(request, str(e))
                return redirect('project_transfer_add')
    else:
        form = ProjectBalanceTransferForm()

    return render(request, 'transferbalance/project_transfer_add.html', {'form': form})

@login_required
def project_transfer_edit(request, pk):
    transfer = get_object_or_404(ProjectBalanceTransfer, pk=pk)
    old_source_cash = transfer.source_cash_type
    old_dest_cash = transfer.destination_cash_type
    old_amount = transfer.transfer_amount

    if request.method == 'POST':
        form = ProjectBalanceTransferForm(request.POST, instance=transfer)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Revert old balance changes
                    src_old = CashType.objects.select_for_update().get(id=old_source_cash.id)
                    src_old.type_amount += old_amount
                    src_old.save()

                    dst_old = CashType.objects.select_for_update().get(id=old_dest_cash.id)
                    dst_old.type_amount -= old_amount
                    dst_old.save()

                    # Apply new values
                    updated_transfer = form.save()

                    src_new = CashType.objects.select_for_update().get(id=updated_transfer.source_cash_type.id)
                    src_new.type_amount -= updated_transfer.transfer_amount
                    src_new.type_note = f"Debited {updated_transfer.transfer_amount} for Project Transfer to {updated_transfer.destination_project.project_first_name}"
                    src_new.save()

                    dst_new = CashType.objects.select_for_update().get(id=updated_transfer.destination_cash_type.id)
                    dst_new.type_amount += updated_transfer.transfer_amount
                    dst_new.type_note = f"Credited {updated_transfer.transfer_amount} for Project Transfer from {updated_transfer.source_project.project_first_name}"
                    dst_new.save()

                messages.success(request, 'Project balance transfer updated successfully.')
                return redirect('project_transfer_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ProjectBalanceTransferForm(instance=transfer)

    return render(request, 'transferbalance/project_transfer_edit.html', {'form': form})


@login_required
def project_transfer_delete(request, pk):
    transfer = get_object_or_404(ProjectBalanceTransfer, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Revert balances
                src_cash = CashType.objects.select_for_update().get(id=transfer.source_cash_type.id)
                src_cash.type_amount += transfer.transfer_amount
                src_cash.save()

                dst_cash = CashType.objects.select_for_update().get(id=transfer.destination_cash_type.id)
                dst_cash.type_amount -= transfer.transfer_amount
                dst_cash.save()

                transfer.delete()

            messages.success(request, 'Project balance transfer deleted and balances restored.')
            return redirect('project_transfer_list')
        except Exception as e:
            messages.error(request, str(e))
            
    return render(request, 'transferbalance/project_transfer_delete.html', {'transfer': transfer})
    
    

@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(BalanceTransfer, pk=pk)

    def amount_to_words(amount):
        try:
            taka = int(amount)
            paisa = int(round((amount - taka) * 100))

            words = num2words(taka, lang='en').title() + " Taka"
            if paisa:
                words += f" and {num2words(paisa, lang='en').title()} Paisa"
            return words + " Only"
        except:
            return f"{amount} Taka Only"

    amount_in_words = amount_to_words(float(transfer.transfer_amount))

    context = {
        'transfer': transfer,
        'amount_in_words': amount_in_words,
        'print_time': timezone.now(),
    }
    return render(request, 'transferbalance/transfer_detail.html', context)
    

### Loan voucher code 
# @login_required
# def loanvoucher_list(request):
#     vouchers = LoanVoucher.objects.all()
#     return render(request, 'loanvoucher/loanvoucher_list.html', {'vouchers': vouchers})

# @login_required
# def loanvoucher_list(request):
#     vouchers = LoanVoucher.objects.all().order_by('id')
#     print("Loaded vouchers:", vouchers)

#     running_balance = 0
#     voucher_list = []

#     for v in vouchers:
#         print("Voucher:", v.loan_status, v.amount)
#         if v.loan_status == "Receivable":
#             running_balance += v.amount
#         elif v.loan_status == "Payable":
#             running_balance -= v.amount

#         voucher_list.append({
#             'voucher': v,
#             'balance': running_balance,
#         })

#     print("Voucher list for template:", voucher_list)

#     return render(request, 'loanvoucher/loanvoucher_list.html', {
#         'vouchers': voucher_list
#     })



@login_required
def loanvoucher_list(request):
    date_filter = request.GET.get('date')

    vouchers = LoanVoucher.objects.all().order_by('-id')

    # Apply date filter if selected
    if date_filter:
        vouchers = vouchers.filter(date=date_filter)

    running_balance = 0
    voucher_list = []

    for v in vouchers:
        if v.loan_status == "Receivable":
            running_balance += v.amount
        elif v.loan_status == "Payable":
            running_balance -= v.amount

        voucher_list.append({
            'voucher': v,
            'balance': running_balance,
        })

    return render(request, 'loanvoucher/loanvoucher_list.html', {
        'vouchers': voucher_list,
    })


    
    

# @login_required
# def loanvoucher_pay_list(request):
#     vouchers = LoanVoucher.objects.select_related(
#         'project_name', 'customer_name', 'conductor_name', 'expense_name'
#     ).filter(loan_status="Payable").order_by('-date') 

#     return render(request, 'loanvoucher/loanvoucher_pay_list.html', {
#         'vouchers': vouchers,
#     })



@login_required
def loanvoucher_pay_list(request):
    date_filter = request.GET.get('date')
    vouchers = LoanVoucher.objects.select_related(
        'project_name', 'customer_name', 'conductor_name', 'expense_name'
    ).filter(loan_status="Payable")

    if date_filter:
        vouchers = vouchers.filter(date=date_filter)

    vouchers = vouchers.order_by('-date')

    return render(request, 'loanvoucher/loanvoucher_pay_list.html', {
        'vouchers': vouchers,
    })




# @login_required
# def loanvoucher_recv_list(request):
#     vouchers = LoanVoucher.objects.select_related(
#         'project_name', 'customer_name', 'conductor_name', 'expense_name'
#     ).filter(loan_status="Receivable").order_by('-date') 

#     return render(request, 'loanvoucher/loanvoucher_recv_list.html', {
#         'vouchers': vouchers,
#     })




@login_required
def loanvoucher_recv_list(request):
    date_filter = request.GET.get('date')

    vouchers = LoanVoucher.objects.select_related(
        'project_name', 'customer_name', 'conductor_name', 'expense_name'
    ).filter(loan_status="Receivable")

    if date_filter:
        vouchers = vouchers.filter(date=date_filter)

    vouchers = vouchers.order_by('-date')

    return render(request, 'loanvoucher/loanvoucher_recv_list.html', {
        'vouchers': vouchers,
    })





@login_required
def add_loanvoucher(request):
    if request.method == 'POST':
        form = LoanVoucherForm(request.POST)
        if form.is_valid():
            loanvoucher = form.save(commit=False)

            # ---------------------------------------------------
            # AUTO MR/BILL NUMBER GENERATION
            # ---------------------------------------------------
            if not loanvoucher.mr_or_bill_no:
                base_code = "APY-"
                last_voucher = (
                    LoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                    .order_by('-id')
                    .first()
                )
                next_id = (last_voucher.id + 1) if last_voucher else 1
                generated_code = f"{base_code}{next_id:05d}"

                while LoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"

                loanvoucher.mr_or_bill_no = generated_code

            # Default status
            loanvoucher.loan_status = 'Payable'
            loanvoucher.save()

            amount = loanvoucher.amount or 0

            # ---------------------------------------------------
            # UNIQUE MR/BILL NO FOR LEDGER ROWS
            # ---------------------------------------------------
            base_mr = loanvoucher.mr_or_bill_no
            mr_expense = f"{base_mr}-A"   # First row
            mr_main = f"{base_mr}-B"      # Second row

            # ---------------------------------------------------
            # STATIC VALUES ALWAYS USED
            # ---------------------------------------------------
            no_method = CashType.objects.get(cash_type_name="No_Method")
            expense_head = HeadOfAccount.objects.get(head_name="Expense Account")

            # ---------------------------------------------------
            # FIRST LEDGER ENTRY — STATIC EXPENSE
            # ---------------------------------------------------
            LedgerEntry.objects.create(
                project_name=loanvoucher.project_name,
                type="Expense",
                customer_name=None,
                contructor=None,
                vendor=None,
                exp_name=loanvoucher.source_name,
                bankName=None,
                type_name=loanvoucher.source_name.head_exp_name if loanvoucher.source_name else "",
                cash_type=no_method,        # ALWAYS No_Method
                head=expense_head,          # ALWAYS Expense Account
                mr_or_bill_no=mr_expense,
                date=loanvoucher.date,
                description=f"Expense entry for {loanvoucher.particulars}",
                debit=amount,
                credit=0,
                carrier=loanvoucher.carrier,
                loan_status="Expense",
                tbl_id=loanvoucher.id,
                tbl_name='Payment'
            )

            # ---------------------------------------------------
            # DETERMINE SECOND ENTRY DEBIT/CREDIT
            # ---------------------------------------------------
            loan_status = "Received"  # your business rule
            debit_amount = amount if loan_status.lower() == 'payment' else 0
            credit_amount = amount if loan_status.lower() == 'received' else 0

            # ---------------------------------------------------
            # FIND TYPE NAME
            # ---------------------------------------------------
            type_name = None
            if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
                type_name = loanvoucher.vendor_name
            elif loanvoucher.type == 'Contructor' and loanvoucher.conductor_name:
                type_name = loanvoucher.conductor_name
            elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
                type_name = loanvoucher.customer_name
            elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
                type_name = loanvoucher.expense_name
            elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
                type_name = loanvoucher.bankName.cash_type_name

            # ---------------------------------------------------
            # SECOND LEDGER ENTRY — MAIN ENTRY
            # ---------------------------------------------------
            LedgerEntry.objects.create(
                project_name=loanvoucher.project_name,
                type=loanvoucher.type,
                customer_name=loanvoucher.customer_name,
                contructor=loanvoucher.conductor_name,
                vendor=loanvoucher.vendor_name,
                exp_name=loanvoucher.expense_name,
                bankName=loanvoucher.bankName,
                type_name=type_name,
                cash_type=no_method,        # ALWAYS No_Method
                head=loanvoucher.headAcct,
                mr_or_bill_no=mr_main,
                date=loanvoucher.date,
                description=loanvoucher.particulars,
                debit=debit_amount,
                credit=credit_amount,
                carrier=loanvoucher.carrier,
                loan_status=loan_status,
                tbl_id=loanvoucher.id,
                tbl_name='Payment'
            )
            
            TransactionHistory.objects.create(
                project=loanvoucher.project_name,
                transaction_type=loanvoucher.type,
                head_of_account=loanvoucher.headAcct,
                cash_type=no_method,
                cheque_number=getattr(loanvoucher, 'cheque_number', None),
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                type_name=type_name,
                reference=getattr(loanvoucher, 'mr_no', None),
                create_by=loanvoucher.created_by if hasattr(loanvoucher, 'created_by') else '',
                particulars=loanvoucher.particulars,
                tbl_id=str(loanvoucher.id),
                tbl_name='Payment'
            )
    
            return redirect('loanvoucher_list')

    else:
        form = LoanVoucherForm()

    expenses = HeadOfExpense.objects.all()
    selected_expense_name = ''

    if form.is_bound and form.is_valid():
        selected_expense = form.cleaned_data.get('expense_name')
        if selected_expense:
            selected_expense_name = f"{selected_expense.head_exp_code} - {selected_expense.head_exp_name}"

    No_Method = get_object_or_404(CashType, cash_type_name='No_Method')

    return render(request, 'loanvoucher/add_loanvoucher.html', {
        'No_Method': [No_Method],
        'form': form,
        'expenses': expenses,
        'selected_expense_name': selected_expense_name,
        'today': now().date(),
    })





# @login_required
# def add_rechvoucher(request):
#     if request.method == 'POST':
#         form = LoanVoucherForm(request.POST)
#         if form.is_valid():
#             loanvoucher = form.save(commit=False)
#             # Generate MR/Bill No if not provided
#             if not loanvoucher.mr_or_bill_no:
#                 base_code = "ARC-"
#                 last_voucher = (
#                     LoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#                     .order_by('-id')
#                     .first()
#                 )
#                 next_id = (last_voucher.id + 1) if last_voucher else 1
#                 generated_code = f"{base_code}{next_id:05d}"

#                 while LoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 loanvoucher.mr_or_bill_no = generated_code

#             # Set loan status
#             loanvoucher.loan_status = 'Receivable'
#             loanvoucher.save()

#             # Determine loan status and amounts
#             loan_status = 'Payment'  # adjust as per your logic
#             amount = loanvoucher.amount or 0
#             debit_amount = amount if loan_status.lower() == 'payment' else 0
#             credit_amount = amount if loan_status.lower() == 'received' else 0

#             # Assign type_name dynamically based on type field
#             type_name = None
#             if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
#                 type_name = loanvoucher.vendor_name
#             elif loanvoucher.type == 'Conductor' and loanvoucher.conductor_name:
#                 type_name = loanvoucher.conductor_name
#             elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
#                 type_name = loanvoucher.customer_name
#             elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
#                 type_name = loanvoucher.expense_name
#             elif loanvoucher.type == 'Employee':
#                 type_name = loanvoucher.empl_name
#             elif loanvoucher.type == 'Bank':
#                 type_name = loanvoucher.bankName.cash_type_name
           

#             # Create LedgerEntry record
#             LedgerEntry.objects.create(
#                 project_name=loanvoucher.project_name,
#                 type=loanvoucher.type,
#                 customer_name=loanvoucher.customer_name,
#                 contructor=loanvoucher.conductor_name,
#                 vendor=loanvoucher.vendor_name,
#                 exp_name=loanvoucher.expense_name,
#                 bankName=loanvoucher.bankName,
#                 type_name=type_name,
#                 cash_type=loanvoucher.cash_type,
#                 head=loanvoucher.headAcct,
#                 mr_or_bill_no=loanvoucher.mr_or_bill_no,
#                 date=loanvoucher.date or timezone.now(),
#                 description=loanvoucher.particulars or '',
#                 debit=debit_amount,
#                 credit=credit_amount,
#                 carrier=loanvoucher.carrier,
#                 loan_status=loan_status,
#             )

#             return redirect('loanvoucher_list')
#     else:
#         form = LoanVoucherForm()

#     expenses = HeadOfExpense.objects.all()
#     rdaEmployees = RdaEmployee.objects.all()
#     selected_expense_name = ''
    
#     form.fields['empl_name'].choices = [('', 'Select Employee Name')] + [
#         (emp.rda_emp_name, emp.rda_emp_name) for emp in rdaEmployees
#     ]

#     if form.is_bound and form.is_valid():
#         selected_expense = form.cleaned_data.get('expense_name')
#         if selected_expense:
#             selected_expense_name = f"{selected_expense.head_exp_code} - {selected_expense.head_exp_name}"
    
#     No_Method = get_object_or_404(CashType, cash_type_name='No_Method')
#     return render(request, 'loanvoucher/add_rechvoucher.html', {
#         'No_Method': [No_Method],
#         'form': form,
#         'expenses': expenses,
#         'selected_expense_name': selected_expense_name,
#         'today': now().date(),
#     })
    
    


@login_required
def add_rechvoucher(request):
    if request.method == 'POST':
        form = LoanVoucherForm(request.POST)

        if form.is_valid():
            loanvoucher = form.save(commit=False)

            # ---------------------------------------------------
            # AUTO MR/BILL NUMBER GENERATION (ARC-)
            # ---------------------------------------------------
            if not loanvoucher.mr_or_bill_no:
                base_code = "ARC-"
                last_voucher = (
                    LoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                    .order_by('-id')
                    .first()
                )
                next_id = (last_voucher.id + 1) if last_voucher else 1
                generated_code = f"{base_code}{next_id:05d}"

                while LoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"

                loanvoucher.mr_or_bill_no = generated_code

            # Default status
            loanvoucher.loan_status = 'Receivable'
            loanvoucher.save()

            amount = loanvoucher.amount or 0

            # ---------------------------------------------------
            # UNIQUE MR/BILL NO FOR LEDGER ROWS
            # ---------------------------------------------------
            base_mr = loanvoucher.mr_or_bill_no
            mr_expense = f"{base_mr}-A"   # First row
            mr_main = f"{base_mr}-B"      # Second row

            # ---------------------------------------------------
            # STATIC VALUES ALWAYS USED
            # ---------------------------------------------------
            no_method = CashType.objects.get(cash_type_name="No_Method")
            expense_head = HeadOfAccount.objects.get(head_name="Expense Account")

            # ---------------------------------------------------
            # FIRST LEDGER ENTRY — STATIC EXPENSE ROW
            # ---------------------------------------------------
            LedgerEntry.objects.create(
                project_name=loanvoucher.project_name,
                type="Expense",
                customer_name=None,
                contructor=None,
                vendor=None,
                exp_name=loanvoucher.source_name,
                bankName=None,
                type_name=loanvoucher.source_name.head_exp_name if loanvoucher.source_name else "",
                cash_type=no_method,            # ALWAYS No_Method
                head=expense_head,              # ALWAYS Expense Account
                mr_or_bill_no=mr_expense,
                date=loanvoucher.date,
                description=f"Expense entry for {loanvoucher.particulars}",
                debit=amount,
                credit=0,
                carrier=loanvoucher.carrier,
                loan_status="Expense",
                tbl_id=loanvoucher.id,
                tbl_name='Received'
            )
            
            TransactionHistory.objects.create(
                project=loanvoucher.project_name,
                transaction_type="Expense",
                head_of_account=expense_head,
                cash_type=no_method,
                cheque_number=None,
                amount=amount,
                date=loanvoucher.date or timezone.now().date(),
                type_name=type_name,
                reference=mr_expense,
                create_by=getattr(loanvoucher, 'created_by', ''),  # or request.user.username if in view
                particulars=f"Expense entry for {loanvoucher.particulars}",
                tbl_id=str(loanvoucher.id),
                tbl_name='Received'
            )

            # ---------------------------------------------------
            # PAYMENT IS RECEIVABLE → CREDIT ENTRY
            # ---------------------------------------------------
            loan_status = "Payment"
            debit_amount = amount if loan_status.lower() == "payment" else 0
            credit_amount = amount if loan_status.lower() == "received" else 0

            # ---------------------------------------------------
            # DYNAMIC TYPE NAME
            # ---------------------------------------------------
            type_name = None
            if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
                type_name = loanvoucher.vendor_name
            elif loanvoucher.type == 'Conductor' and loanvoucher.conductor_name:
                type_name = loanvoucher.conductor_name
            elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
                type_name = loanvoucher.customer_name
            elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
                type_name = loanvoucher.expense_name
            elif loanvoucher.type == 'Employee' and loanvoucher.empl_name:
                type_name = loanvoucher.empl_name
            elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
                type_name = loanvoucher.bankName.cash_type_name

            # ---------------------------------------------------
            # SECOND LEDGER ENTRY — MAIN ENTRY
            # ---------------------------------------------------
            LedgerEntry.objects.create(
                project_name=loanvoucher.project_name,
                type=loanvoucher.type,
                customer_name=loanvoucher.customer_name,
                contructor=loanvoucher.conductor_name,
                vendor=loanvoucher.vendor_name,
                exp_name=loanvoucher.expense_name,
                bankName=loanvoucher.bankName,
                type_name=type_name,
                cash_type=no_method,            # ALWAYS No_Method
                head=loanvoucher.headAcct,
                mr_or_bill_no=mr_main,
                date=loanvoucher.date,
                description=loanvoucher.particulars,
                debit=debit_amount,
                credit=credit_amount,
                carrier=loanvoucher.carrier,
                loan_status=loan_status,
            )

            return redirect('loanvoucher_list')

    else:
        form = LoanVoucherForm()

    # -----------------------------------------------------------
    # PAGE LOAD SUPPORT DATA
    # -----------------------------------------------------------
    expenses = HeadOfExpense.objects.all()
    rdaEmployees = RdaEmployee.objects.all()
    selected_expense_name = ''

    form.fields['empl_name'].choices = [('', 'Select Employee Name')] + [
        (emp.rda_emp_name, emp.rda_emp_name) for emp in rdaEmployees
    ]

    if form.is_bound and form.is_valid():
        selected_expense = form.cleaned_data.get('expense_name')
        if selected_expense:
            selected_expense_name = f"{selected_expense.head_exp_code} - {selected_expense.head_exp_name}"

    No_Method = get_object_or_404(CashType, cash_type_name='No_Method')

    return render(request, 'loanvoucher/add_rechvoucher.html', {
        'No_Method': [No_Method],
        'form': form,
        'expenses': expenses,
        'selected_expense_name': selected_expense_name,
        'today': now().date(),
    })



# @login_required
# def edit_loanvoucher(request, pk):
#     voucher = get_object_or_404(LoanVoucher, pk=pk)
#     form = LoanVoucherForm(request.POST or None, instance=voucher)
#     if form.is_valid():
#         form.save()
#         return redirect('loanvoucher_list')
#     return render(request, 'loanvoucher/edit_loanvoucher.html', {'form': form, 'voucher': voucher})
    



@login_required
def edit_loanvoucher(request, pk):
    voucher = get_object_or_404(LoanVoucher, pk=pk)
    form = LoanVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        with transaction.atomic():
            loanvoucher = form.save()

            # -------------------------------
            # Determine type_name
            # -------------------------------
            type_name = None
            if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
                type_name = loanvoucher.vendor_name.name  # ensure string
            elif loanvoucher.type == 'Contructor' and loanvoucher.conductor_name:
                type_name = loanvoucher.conductor_name.name if hasattr(loanvoucher.conductor_name, 'name') else str(loanvoucher.conductor_name)
            elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
                type_name = loanvoucher.customer_name.name if hasattr(loanvoucher.customer_name, 'name') else str(loanvoucher.customer_name)
            elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
                type_name = loanvoucher.expense_name.head_exp_name if hasattr(loanvoucher.expense_name, 'head_exp_name') else str(loanvoucher.expense_name)
            elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
                type_name = loanvoucher.bankName.cash_type_name if hasattr(loanvoucher.bankName, 'cash_type_name') else str(loanvoucher.bankName)

            # -------------------------------
            # Compute debit / credit
            # -------------------------------
            loan_status = 'Payable'  # adjust if dynamic
            amount = loanvoucher.amount or 0
            debit_amount = amount if loan_status == 'payment' else 0
            credit_amount = amount if loan_status == 'received' else 0
            no_method = None
            mr_main = getattr(loanvoucher, 'mr_no', None)

            # -------------------------------
            # UPDATE LedgerEntry
            # -------------------------------
            LedgerEntry.objects.filter(
                tbl_id=loanvoucher.id,
                tbl_name='Payment'
            ).update(
                project_name=loanvoucher.project_name,
                type=loanvoucher.type,
                customer_name=loanvoucher.customer_name,
                contructor=loanvoucher.conductor_name,
                vendor=loanvoucher.vendor_name,
                exp_name=loanvoucher.expense_name,
                bankName=loanvoucher.bankName,
                type_name=type_name,
                cash_type=no_method,
                head=loanvoucher.headAcct,
                mr_or_bill_no=mr_main,
                date=loanvoucher.date or timezone.now().date(),
                description=loanvoucher.particulars,
                debit=debit_amount,
                credit=credit_amount,
                carrier=loanvoucher.carrier,
                loan_status=loan_status,
            )

            # -------------------------------
            # UPDATE TransactionHistory
            # -------------------------------
            TransactionHistory.objects.filter(
                tbl_id=str(loanvoucher.id),
                tbl_name='Payment'
            ).update(
                project=loanvoucher.project_name,
                transaction_type=loanvoucher.type,
                head_of_account=loanvoucher.headAcct,
                cash_type=no_method,
                cheque_number=getattr(loanvoucher, 'cheque_number', None),
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                type_name=type_name,
                reference=mr_main,
                create_by=getattr(loanvoucher, 'created_by', '') or '',
                particulars=loanvoucher.particulars,
            )

        return redirect('loanvoucher_list')

    return render(
        request,
        'loanvoucher/edit_loanvoucher.html',
        {'form': form, 'voucher': voucher}
    )



    
# @login_required
# def exp_loanvoucher(request, pk):
#     voucher = get_object_or_404(LoanVoucher, pk=pk)

#     if request.method == "POST":

#         amount = voucher.amount or 0
#         base_mr = voucher.mr_or_bill_no

#         # Generate MR no for Expense line
#         mr_expense = f"{base_mr}-A"

#         # Static values
#         no_method = CashType.objects.get(cash_type_name="No_Method")
#         expense_head = HeadOfAccount.objects.get(head_name="Expense Account")

#         # Safe type_name value
#         type_name_value = (
#             voucher.source_name.head_exp_name
#             if voucher.source_name and voucher.source_name.head_exp_name
#             else ""
#         )

#         # -----------------------------------
#         # INSERT LEDGER ENTRY (EXPENSE ONLY)
#         # -----------------------------------
#         LedgerEntry.objects.create(
#             project_name=voucher.project_name,
#             type="Expense",
#             customer_name=None,
#             contructor=None,
#             vendor=None,
#             exp_name=voucher.source_name,
#             bankName=None,
#             type_name=type_name_value,
#             cash_type=no_method,
#             head=expense_head,
#             mr_or_bill_no=mr_expense,
#             date=voucher.date,
#             description=f"Expense entry for {voucher.particulars}",
#             debit=amount,
#             credit=0,
#             carrier=voucher.carrier,
#             loan_status="Expense"
#         )

#         return redirect('loanvoucher_list')

#     # Only display form (NO SAVE)
#     form = LoanVoucherForm(instance=voucher)
#     return render(request, 'loanvoucher/exp_loanvoucher.html', {
#         'form': form,
#         'voucher': voucher
#     })




# @login_required
# def exp_loanvoucher(request, pk):
#     voucher = get_object_or_404(LoanVoucher, pk=pk)

#     amount = voucher.amount or 0
#     base_mr = voucher.mr_or_bill_no

#     # Generate MR no for Expense line
#     mr_expense = f"{base_mr}-A"

#     # Static values
#     no_method = CashType.objects.get(cash_type_name="No_Method")
#     expense_head = HeadOfAccount.objects.get(head_name="Expense Account")

#     # Use voucher.source_name if exists, else default HeadOfExpense id=31
#     if voucher.source_name:
#         exp_obj = voucher.source_name
#     else:
#         exp_obj = HeadOfExpense.objects.get(id=31)

#     # Safe type_name
#     type_name_value = exp_obj.head_exp_name if exp_obj.head_exp_name else ""

#     # -----------------------------------
#     # INSERT LEDGER ENTRY (EXPENSE ONLY)
#     # -----------------------------------
#     LedgerEntry.objects.create(
#         project_name=voucher.project_name,
#         type="Expense",
#         customer_name=None,
#         contructor=None,
#         vendor=None,
#         exp_name=exp_obj,
#         bankName=None,
#         type_name=type_name_value,
#         cash_type=no_method,
#         head=expense_head,
#         mr_or_bill_no=mr_expense,
#         date=voucher.date,
#         description=f"Expense entry for {voucher.particulars}",
#         debit=amount,
#         credit=0,
#         carrier=voucher.carrier,
#         loan_status="Expense"
#     )

#     messages.success(request, "Expense voucher exported into LedgerEntry successfully.")

#     return redirect('loanvoucher_pay_list')



@login_required
def exp_loanvoucher(request, pk):
    voucher = get_object_or_404(LoanVoucher, pk=pk)

    amount = voucher.amount or 0
    base_mr = voucher.mr_or_bill_no

    # Generate unique MR no for Expense line
    mr_expense = f"{base_mr}-A"
    counter = 1
    while LedgerEntry.objects.filter(mr_or_bill_no=mr_expense).exists():
        counter += 1
        mr_expense = f"{base_mr}-A-{counter}"

    # Static values
    no_method = CashType.objects.get(cash_type_name="No_Method")
    expense_head = HeadOfAccount.objects.get(head_name="Expense Account")

    # Use voucher.source_name if exists, else default HeadOfExpense id=31
    if voucher.source_name:
        exp_obj = voucher.source_name
    else:
        exp_obj = HeadOfExpense.objects.get(id=31)

    type_name_value = exp_obj.head_exp_name if exp_obj.head_exp_name else ""

    # Insert ledger entry
    LedgerEntry.objects.create(
        project_name=voucher.project_name,
        type="Expense",
        customer_name=None,
        contructor=None,
        vendor=None,
        exp_name=exp_obj,
        bankName=None,
        type_name=type_name_value,
        cash_type=no_method,
        head=expense_head,
        mr_or_bill_no=mr_expense,
        date=voucher.date,
        description=f"Expense entry for {voucher.particulars}",
        debit=amount,
        credit=0,
        carrier=voucher.carrier,
        loan_status="Expense"
    )

    messages.success(request, "Expense voucher exported into LedgerEntry successfully.")
    return redirect('loanvoucher_pay_list')



 


@login_required
def delete_loanvoucher(request, pk):
    voucher = get_object_or_404(LoanVoucher, pk=pk)
    if request.method == 'POST':
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('loanvoucher_list')
    return render(request, 'loanvoucher/delete_loanvoucher.html', {'voucher': voucher})


@login_required
def details_loanvoucher(request, pk):
    voucher = get_object_or_404(LoanVoucher, pk=pk)
    return render(request, 'loanvoucher/details_loanvoucher.html', {'voucher': voucher})


@login_required
def loan_voucher_pdf(request, pk):
    voucher = get_object_or_404(LoanVoucher, pk=pk)

    def amount_to_words(amount):
        try:
            amount = float(amount)
            words = num2words(amount, lang='en_IN').replace('and', '').strip()
            return f"{words.capitalize()} Taka"
        except Exception:
            return "Invalid amount"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'loanvoucher/print_loanvoucher.html', context)
    
    



## Open Balance ---
@login_required
def openbalance_voucher_list(request):
    OpenBlances = OpenBlanceVoucher.objects.all()
    return render(request, 'openblance/openvoucher_list.html', {'OpenBlances': OpenBlances})



# @login_required
# def add_openbalance_voucher(request):
#     updated_items = []
#     form = OpenBlanceVoucherForm(request.POST or None)

#     if form.is_valid():
#         item = form.save()
#         updated_items.append(item)  

#         approved_items = [
#             item for item in updated_items
#             if item.type != ''
#         ]

#         for item in approved_items:
#             loan_status = 'received'
#             amount = item.amount or 0
#             debit_amount = amount if loan_status == 'payment' else 0
#             credit_amount = amount if loan_status == 'received' else 0

#             LedgerEntry.objects.create(
#                 project_name=item.project_name,            
#                 type=item.type,  
#                 contructor=getattr(item, 'contructor', None),                
#                 vendor=getattr(item, 'vendor', None),                        
#                 customer_name=getattr(item, 'customer_name', None),          
#                 bankName=getattr(item, 'bankName', None),                     
#                 cash_type=item.cash_type,                    
#                 cheque_number=item.cheque_number,
#                 head=item.head_of_account,                  
#                 date=item.date or timezone.now(),           
#                 description=item.particulars or '',          
#                 debit=debit_amount,
#                 credit=credit_amount,
#                 carrier=getattr(item, 'carrier', None),
#                 loan_status=loan_status,
#             )    

#         return redirect('openbalance_voucher_list')
    
#     projects_first = ProjectFirstLevelName.objects.all()
#     context = {
#         'form': form,
#         'projects_firts': projects_first,
#     }
#     return render(request, 'openblance/add_openvoucher.html', context)


@login_required
def add_openbalance_voucher(request):
    updated_items = []
    form = OpenBlanceVoucherForm(request.POST or None)

    if form.is_valid():
        item = form.save()  
        updated_items.append(item) 
        
        type_name = item.vendor if item.type == 'Vendor' and item.vendor else None
        
        TransactionHistory.objects.create(
            project=item.project_name,
            transaction_type=item.type,
            head_of_account=item.head_of_account,
            cash_type=item.cash_type,
            amount=item.amount,
            cheque_number=item.cheque_number,
            date=item.date,
            type_name=type_name,
            create_by=request.user,
            particulars=item.particulars,
            tbl_id=item.id,
            tbl_name='Received',
        )
        
        approved_items = [
            item for item in updated_items
            if item.type != ''
        ]

        for item in approved_items:
            loan_status = 'received'
            amount = item.amount or 0
            debit_amount = amount if loan_status == 'payment' else 0
            credit_amount = amount if loan_status == 'received' else 0

            LedgerEntry.objects.create(
                project_name=item.project_name,            
                type=item.type,  
                contructor=getattr(item, 'contructor', None),                
                vendor=getattr(item, 'vendor', None),                        
                customer_name=getattr(item, 'customer_name', None),          
                bankName=getattr(item, 'bankName', None),
                cash_type=item.cash_type,
                head=item.head_of_account,                  
                date=item.date or timezone.now(),           
                description=item.particulars or '',          
                debit=debit_amount,
                credit=credit_amount,
                carrier=getattr(item, 'carrier', None),
                loan_status=loan_status,
                tbl_id=item.id,
                tbl_name='Received',
            )    

        return redirect('openbalance_voucher_list')
    
    #project = get_object_or_404(ProjectFirstLevelName, project_first_name='BTP Office')
    
    projects_first = ProjectFirstLevelName.objects.all()
    cashs = get_object_or_404(CashType, cash_type_name='Cash') 
    context = {
        'projects_firts': projects_first, 
        'cashs': [cashs], 
        'form': form,
        'today': now().date(),
    }
    return render(request, 'openblance/add_openvoucher.html', context)


# @login_required
# def add_openbalance_voucher(request):
#     updated_items = []
#     form = OpenBlanceVoucherForm(request.POST or None)

#     if form.is_valid():
#         item = form.save()
#         updated_items.append(item)  

#         try:
#             cash_type = CashType.objects.get(type_name=item.cash_type)
#             cash_type.type_amount += item.amount
#             cash_type.type_note = f"Open Balance of item ID {item.id}"
#             cash_type.save()
#         except CashType.DoesNotExist:
#             pass     
    
#         TransactionHistory.objects.create(
#             project=item.project_name,
#             transaction_type=item.type,
#             head_of_account=item.head_of_account,
#             cash_type=cash_type,
#             amount=item.amount,
#             date=item.date,
#             type_name=f"{item.type}_Open_Balance",
#             reference=item.mr_or_bill_no, 
#         )
        
#         approved_items = [
#             item for item in updated_items
#             if item.type != ''
#         ]

#         for item in approved_items:
#             loan_status = 'received'
#             amount = item.amount or 0
#             debit_amount = amount if loan_status == 'payment' else 0
#             credit_amount = amount if loan_status == 'received' else 0

#             LedgerEntry.objects.create(
#                 project_name=item.project_name,            
#                 type=item.type,  
#                 contructor=getattr(item, 'contructor', None),                
#                 vendor=getattr(item, 'vendor', None),                        
#                 customer_name=getattr(item, 'customer_name', None),          
#                 bankName=getattr(item, 'bankName', None),                     
#                 cash_type=item.cash_type,                    
#                 cheque_number=item.cheque_number,
#                 head=item.head_of_account,                  
#                 date=item.date or timezone.now(),           
#                 description=item.particulars or '',          
#                 debit=debit_amount,
#                 credit=credit_amount,
#                 carrier=getattr(item, 'carrier', None),
#                 loan_status=loan_status,
#             )    

#         return redirect('openbalance_voucher_list')
    
#     projects_first = ProjectFirstLevelName.objects.all()
#     context = {
#         'form': form,
#         'projects_firts': projects_first,
#     }
#     return render(request, 'openblance/add_openvoucher.html', context)



# @login_required
# def edit_openbalance_voucher(request, pk):
#     voucher = get_object_or_404(OpenBlanceVoucher, pk=pk)
#     projects_first = ProjectFirstLevelName.objects.all()
#     form = OpenBlanceVoucherForm(request.POST or None, instance=voucher)
#     if form.is_valid():
#         form.save()
#         return redirect('openbalance_voucher_list')
    
#     context = {
#         'form': form,
#         'voucher': voucher,
#         'projects_firts': projects_first,
#     }
#     return render(request, 'openblance/edit_openvoucher.html', context)



@login_required
def edit_openbalance_voucher(request, pk):
    voucher = get_object_or_404(OpenBlanceVoucher, pk=pk)
    projects_first = ProjectFirstLevelName.objects.all()
    form = OpenBlanceVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        with transaction.atomic():
            item = form.save()

            # ==============================
            # TRANSACTION HISTORY UPDATE
            # ==============================
            type_name = None
            if item.type == 'Vendor' and item.vendor:
                # Use correct field from Suppliers model
                type_name = item.vendor.supplier_name  # change if your field is different

            TransactionHistory.objects.filter(
                tbl_id=item.id,
                tbl_name='Received'
            ).update(
                project=item.project_name,
                transaction_type=item.type,
                head_of_account=item.head_of_account,
                cash_type=item.cash_type,
                amount=item.amount,
                cheque_number=item.cheque_number,
                date=item.date,
                type_name=type_name,
                create_by=request.user.username,
                particulars=item.particulars,
            )

            # ==============================
            # LEDGER ENTRY UPDATE
            # ==============================
            loan_status = 'received'
            amount = item.amount or 0

            debit_amount = amount if loan_status == 'payment' else 0
            credit_amount = amount if loan_status == 'received' else 0

            LedgerEntry.objects.filter(
                tbl_id=item.id,
                tbl_name='Received'
            ).update(
                project_name=item.project_name,
                type=item.type,
                contructor=getattr(item, 'contructor', None),
                vendor=getattr(item, 'vendor', None),
                customer_name=getattr(item, 'customer_name', None),
                bankName=getattr(item, 'bankName', None),
                cash_type=item.cash_type,
                head=item.head_of_account,
                date=item.date or timezone.now(),
                description=item.particulars or '',
                debit=debit_amount,
                credit=credit_amount,
                carrier=getattr(item, 'carrier', None),
                loan_status=loan_status,
            )

        return redirect('openbalance_voucher_list')

    return render(
        request,
        'openblance/edit_openvoucher.html',
        {
            'form': form,
            'voucher': voucher,
            'projects_firts': projects_first,
        }
    )





@login_required
def delete_openbalance_voucher(request, pk):
    voucher = get_object_or_404(OpenBlanceVoucher, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Log deleted data
            log_deleted_data(voucher, request.user)

            # Delete related LedgerEntry rows
            LedgerEntry.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name='Received'  # make sure tbl_name matches your create logic
            ).delete()

            # Delete related TransactionHistory rows
            TransactionHistory.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name='Received'
            ).delete()

            # Delete the OpenBalanceVoucher itself
            voucher.delete()

        return redirect('openbalance_voucher_list')

    return render(
        request,
        'openblance/delete_openvoucher.html',
        {'voucher': voucher}
    )



@login_required
def openbalance_voucher_pdf(request, pk):
    voucher = get_object_or_404(OpenBlanceVoucher, pk=pk)
    
    def amount_to_words(amount):
        try:
            amount = round(float(amount), 2)
            taka = int(amount)
            paisa = int(round((amount - taka) * 100))
    
            def bdt_number_to_words(n):
                n_str = str(n).zfill(9)  # Pad to 9 digits for crore/lakh
                crore = int(n_str[0:2])
                lakh = int(n_str[2:4])
                thousand = int(n_str[4:6])
                hundred = int(n_str[6])
                rest = int(n_str[7:9])
    
                parts = []
    
                if crore:
                    parts.append(num2words(crore, lang='en') + ' crore')
                if lakh:
                    parts.append(num2words(lakh, lang='en') + ' lakh')
                if thousand:
                    parts.append(num2words(thousand, lang='en') + ' thousand')
                if hundred:
                    parts.append(num2words(hundred, lang='en') + ' hundred')
                if rest:
                    parts.append(num2words(rest, lang='en'))
    
                return ' '.join(parts).title()
    
            words = bdt_number_to_words(taka) + " Taka"
            if paisa:
                words += " and " + num2words(paisa, lang='en').title() + " Paisa"
            return words + " Only"
    
        except Exception as e:
            return f"{amount} Taka"

    context = {
        'voucher': voucher,
        'print_time': now(),
        'amount_in_words': amount_to_words(voucher.amount),
    }
    return render(request, 'openblance/print_openvoucher.html', context)


## Reports module ----
@login_required
def reports_manage_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id') 
    form = LedgerReportForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'reportmanage/reports_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })


# @login_required
# def ledger_manage(request):
#     projectName = ProjectFirstLevelName.objects.all()
#     head = HeadOfAccount.objects.all()
#     form = LedgerFilterForm(request.GET or None)
#     head_exp_name = HeadOfExpense.objects.all()
#     cashTypes = CashType.objects.all()
#     context = {
#         'projectNames': projectName,
#         'heads': head,
#         'form': form,
#         'cashTypes': cashTypes,
#         'head_exp_name': head_exp_name,
#         'today': date.today(),
#     }
#     return render(request, 'reportmanage/ledger_manage.html', context)





##  -------------------------------


## Bank Reports ---
@login_required
def bank_reports_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id') 
    form = LedgerReportForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'bankreport/bank_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })


@login_required
def bank_ledger_manage(request):
    cashTypes = CashType.objects.all()
    form = LedgerFilterForm(request.GET or None)

    context = {
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'bankreport/bank_ledger_manage.html', context)



@login_required
def bank_ledger_report(request):
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude')  
    transaction_option = request.GET.get('transaction', 'datewise')  

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()
   
    # if is_valid(cash_type_id):
    #     entries = entries.filter(cash_type_id=cash_type_id)

    if is_valid(cash_type_id) and balance_option != 'all':
        entries = entries.filter(cash_type_id=cash_type_id)
   
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)
   
    if balance_option == 'exclude':
        entries = entries.exclude(head__head_name='Open Balance Account')

    entries = entries.order_by('date', 'id')
   
    balance = Decimal('0.00')
    entry_data = []

    if balance_option == 'include' and is_valid(cash_type_id) and fd:       
        opening_entries = LedgerEntry.objects.filter(
            cash_type_id=cash_type_id,
            head__head_name='Open Balance Account',
            date__lt=fd
        )
        for e in opening_entries:
            balance += e.credit - e.debit

    elif balance_option == 'all':
            # Include opening balance for all cash types
            opening_entries = LedgerEntry.objects.filter(
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                balance += e.credit - e.debit
   
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    # Dropdown data
    projectNames = ProjectFirstLevelName.objects.all()
    heads = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()

    return render(request, 'bankreport/bank_ledger_report.html', {
        'entry_data': entry_data,
        'projectNames': projectNames,
        'heads': heads,
        'cashTypes': cashTypes,
        'selected_filters': {
            'cash_type_name': cash_type_id,
            'from_date': from_date,
            'to_date': to_date,
            'balance': balance_option,
            'transaction': transaction_option,
        }
    })



@login_required
def bank_ledger_manage_pdf(request):
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude')  # include or exclude
    transaction_option = request.GET.get('transaction', 'datewise')  # all or datewise

    # Additional filters
    project = request.GET.get('project', '')
    vendor = request.GET.get('vendor', '')
    type_ = request.GET.get('type', '')
    head = request.GET.get('head', '')
    contractor = request.GET.get('contractor', '')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()  

    if is_valid(cash_type_id) and balance_option != 'all':
        entries = entries.filter(cash_type_id=cash_type_id)

    if is_valid(project):
        entries = entries.filter(project_name__icontains=project)
    if is_valid(vendor):
        entries = entries.filter(vendor__icontains=vendor)
    if is_valid(type_):
        entries = entries.filter(type__icontains=type_)
    if is_valid(head):
        entries = entries.filter(head__head_name__icontains=head)
    if is_valid(contractor):
        entries = entries.filter(contractor__icontains=contractor)

    # Apply date filters
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)

    if balance_option == 'exclude':
        entries = entries.exclude(head__head_name='Open Balance Account')

    entries = entries.order_by('date', 'id')

    balance = Decimal('0.00')
    entry_data = []

    if balance_option == 'include' and is_valid(cash_type_id) and fd:
        opening_entries = LedgerEntry.objects.filter(
            cash_type_id=cash_type_id,
            head__head_name='Open Balance Account',
            date__lt=fd
        )
        for e in opening_entries:
            balance += e.credit - e.debit
    
    elif balance_option == 'all':
            # Include opening balance for all cash types
            opening_entries = LedgerEntry.objects.filter(
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                balance += e.credit - e.debit

    # Running balance
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    # Totals
    total_debit = sum(e['entry'].debit for e in entry_data)
    total_credit = sum(e['entry'].credit for e in entry_data)
    final_balance = total_credit - total_debit

    
    cash_type_name = ''
    if is_valid(cash_type_id):
        ct = CashType.objects.filter(id=cash_type_id).first()
        cash_type_name = ct.cash_type_name if ct else ''

    grouped_entries = defaultdict(list)
    for row in entry_data:
        ct_name = row['entry'].cash_type.cash_type_name if row['entry'].cash_type else 'Unknown'
        grouped_entries[ct_name].append(row)
    
    def amount_to_words(amount):
        try:
            amount = float(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en').title() + " Taka"
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
            words += " only"
            return words
        except:
            return f"{amount} Taka only"
            
    context = {
        'grouped_entries': dict(grouped_entries),
        'entry_data': entry_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': final_balance,
        'balance_in_words': amount_to_words(final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'project': project,
            'vendor': vendor,
            'type': type_,
            'head': head,
            'contractor': contractor,
            'cash_type': cash_type_name,
            'from_date': from_date,
            'to_date': to_date,
            'balance': balance_option,
            'transaction': transaction_option,
        }
    }

    return render(request, 'bankreport/bank_ledger_manage_pdf.html', context)




## Transaction Reports ---
@login_required
def transaction_reports_list(request):
    entries = TransactionHistory.objects.all().order_by('-id')
    form = TransactionHistoryForm()
    
    balance = Decimal('0.00')
    entry_data = []

    for entry in entries:
        if entry.type_name and '_payment' in entry.type_name.lower():
            debit = entry.amount
            credit = Decimal('0.00')
        else:
            credit = entry.amount
            debit = Decimal('0.00')

        # Calculate balance (credit - debit)
        balance += credit - debit

        # Append calculated data to the context list
        entry_data.append({
            'entry': entry,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    return render(request, 'transactionreport/transaction_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })



@login_required
def transaction_ledger_manage(request):
    projectNames = ProjectFirstLevelName.objects.all()
    headNames = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()
    form = LedgerFilterForm(request.GET or None)

    context = {
        'projectNames': projectNames,
        'headNames': headNames,
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'transactionreport/transaction_ledger_manage.html', context)



@login_required
def transaction_ledger_report(request):
    project_id = request.GET.get('project')
    projectalow = request.GET.get('projectalow')
    head_type = request.GET.get('head')
    type_value_id = request.GET.get('head_value')
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude_all')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    form = TransactionHistoryForm()

    # Start with all entries ordered by date ascending for cumulative balance
    entries = TransactionHistory.objects.all().order_by('date', 'id')

    # Apply filters based on projectalow and project_id
    if projectalow == 'oneproject' and is_valid(project_id):
        entries = entries.filter(project_id=project_id)

    if is_valid(type_value_id):
        entries = entries.filter(head_of_account_id=type_value_id)

    # if is_valid(cash_type_id):
    #     entries = entries.filter(cash_type_id=cash_type_id)

    # Filter by date only if transaction_option == 'datewise'
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)

    balance = Decimal('0.00')
    entry_data = []

    for entry in entries:
        if entry.type_name and '_payment' in entry.type_name.lower():
            debit = entry.amount
            credit = Decimal('0.00')
        else:
            credit = entry.amount
            debit = Decimal('0.00')

        balance += credit - debit

        entry_data.append({
            'entry': entry,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    context = {
        'form': form,
        'entry_data': entry_data,
    }

    return render(request, 'transactionreport/transaction_ledger_report.html', context)





# @login_required
# def transaction_ledger_manage_pdf(request):
#     # Get filter values from GET request
#     project_id = request.GET.get('project')
#     projectalow = request.GET.get('projectalow')
#     head_type = request.GET.get('head')
#     type_value_id = request.GET.get('head_value')
#     cash_type_id = request.GET.get('cash_type_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(value):
#         return value is not None and value != ''

#     def parse_date(date_str):
#         try:
#             return datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     form = TransactionHistoryForm()

#     # Base query
#     entries = TransactionHistory.objects.all().order_by('date', 'id')

#     if projectalow == 'oneproject' and is_valid(project_id):
#         entries = entries.filter(project_id=project_id)

#     if is_valid(type_value_id):
#         entries = entries.filter(head_of_account_id=type_value_id)

#     if transaction_option == 'datewise':
#         if fd:
#             entries = entries.filter(date__gte=fd)
#         if td:
#             entries = entries.filter(date__lte=td)

#     # Calculate running balance for all entries (no grouping)
#     entry_data = []
#     balance = Decimal('0.00')

#     for entry in entries:
#         if entry.type_name and '_payment' in entry.type_name.lower():
#             debit = entry.amount
#             credit = Decimal('0.00')
#         else:
#             credit = entry.amount
#             debit = Decimal('0.00')

#         balance += credit - debit

#         entry_data.append({
#             'entry': entry,
#             'debit': debit,
#             'credit': credit,
#             'balance': balance,
#         })

#     # Convert balance to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)

#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))

#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"

#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"

#             words += " only"

#             if is_negative:
#                 words = "- " + words

#             return words
#         except Exception:
#             return f"{amount} Taka only"

#     context = {
#         'form': form,
#         'entry_data': entry_data,
#         'selected_filters': {
#             'from_date': from_date,
#             'to_date': to_date,
#             'project': project_id,
#             'cash_type': cash_type_id,
#             'head_value': type_value_id,
#             'transaction_option': transaction_option,
#         },
#         'balance_in_words': amount_to_words(balance),
#         'print_time': now(),
#     }

#     return render(request, 'transactionreport/transaction_ledger_manage_pdf.html', context)




# @login_required
# def transaction_ledger_manage_pdf(request):
#     project_id = request.GET.get('project')
#     projectalow = request.GET.get('projectalow')
#     head_type = request.GET.get('head')
#     type_value_id = request.GET.get('head_value')
#     cash_type_id = request.GET.get('cash_type_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(value):
#         return value is not None and value != ''

#     def parse_date(date_str):
#         try:
#             return datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     form = TransactionHistoryForm()
#     entries = TransactionHistory.objects.all().order_by('date', 'id')

#     # Filters
#     if projectalow == 'oneproject' and is_valid(project_id):
#         entries = entries.filter(project_id=project_id)
#     if is_valid(type_value_id):
#         entries = entries.filter(head_of_account_id=type_value_id)
#     if transaction_option == 'datewise':
#         if fd:
#             entries = entries.filter(date__gte=fd)
#         if td:
#             entries = entries.filter(date__lte=td)

#     # Prepare totals and data
#     entry_data = []
#     balance = Decimal('0.00')
#     total_debit = Decimal('0.00')
#     total_credit = Decimal('0.00')

#     for entry in entries:
#         if entry.type_name and 'Balance_Trf_Out' in entry.type_name.lower():
#             debit = entry.amount
#             credit = Decimal('0.00')
#         else:
#             credit = entry.amount
#             debit = Decimal('0.00')

#         balance += credit - debit
#         total_debit += debit
#         total_credit += credit

#         entry_data.append({
#             'entry': entry,
#             'debit': debit,
#             'credit': credit,
#             'balance': balance,
#         })

#     # Amount in words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
#             words += " only"
#             if is_negative:
#                 words = "- " + words
#             return words
#         except Exception:
#             return f"{amount} Taka only"

#     context = {
#         'form': form,
#         'entry_data': entry_data,
#         'total_debit': total_debit,
#         'total_credit': total_credit,
#         'final_balance': balance,
#         'selected_filters': {
#             'from_date': from_date,
#             'to_date': to_date,
#             'project': project_id,
#             'cash_type': cash_type_id,
#             'head_value': type_value_id,
#             'transaction_option': transaction_option,
#         },
#         'balance_in_words': amount_to_words(balance),
#         'print_time': now(),
#     }

#     return render(request, 'transactionreport/transaction_ledger_manage_pdf.html', context)



@login_required
def transaction_ledger_manage_pdf(request):
    project_id = request.GET.get('project')
    projectalow = request.GET.get('projectalow')
    head_type = request.GET.get('head')
    type_value_id = request.GET.get('head_value')
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    form = TransactionHistoryForm()
    entries = TransactionHistory.objects.all().order_by('date', 'id')

    # ✅ Apply filters
    if projectalow == 'oneproject' and is_valid(project_id):
        entries = entries.filter(project_id=project_id)
    if is_valid(type_value_id):
        entries = entries.filter(head_of_account_id=type_value_id)
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)

    # ✅ Prepare totals and data
    entry_data = []
    balance = Decimal('0.00')
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for entry in entries:
        debit = Decimal('0.00')
        credit = Decimal('0.00')

        if entry.type_name:
            type_name = entry.type_name.lower().strip()

            # ✅ Money going out
            if 'balance_trf_out' in type_name or 'payment' in type_name or 'withdraw' in type_name:
                credit = entry.amount

            # ✅ Money coming in
            elif 'balance_trf_in' in type_name or 'receive' in type_name or 'deposit' in type_name:
                debit = entry.amount

            else:
                # Default: treat as credit
                credit = entry.amount
        else:
            credit = entry.amount

        # ✅ Running balance (debit adds, credit subtracts)
        balance += debit - credit
        total_debit += debit
        total_credit += credit

        entry_data.append({
            'entry': entry,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    # ✅ Convert amount to words
    def amount_to_words(amount):
        try:
            amount = float(amount)
            is_negative = amount < 0
            amount = abs(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en_IN').title().replace(",", "")
            words += " Taka"
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
            words += " only"
            if is_negative:
                words = "- " + words
            return words
        except Exception:
            return f"{amount} Taka only"

    context = {
        'form': form,
        'entry_data': entry_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': balance,
        'selected_filters': {
            'from_date': from_date,
            'to_date': to_date,
            'project': project_id,
            'cash_type': cash_type_id,
            'head_value': type_value_id,
            'transaction_option': transaction_option,
        },
        'balance_in_words': amount_to_words(balance),
        'print_time': now(),
    }

    return render(request, 'transactionreport/transaction_ledger_manage_pdf.html', context)

## top sheet reports----
@login_required
def topsheet_reports_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id')
    form = LedgerReportForm()
    
    balance = Decimal('0.00')
    entry_data = []

    for entry in entries:
        debit = entry.debit or Decimal('0.00')
        credit = entry.credit or Decimal('0.00')

        # Calculate running balance (credit - debit)
        balance += credit - debit

        entry_data.append({
            'entry': entry,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    return render(request, 'topsheetreport/topsheet_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })

    
    
    
    
# @login_required
# def topsheet_reports_list(request):
#     entries = TransactionHistory.objects.all().order_by('-date', '-id')
#     form = TransactionHistoryForm()
    
#     balance = Decimal('0.00')
#     entry_data = []

#     for entry in entries:
#         # Identify debit or credit based on whether 'type_name' contains '_payment'
#         if entry.type_name and '_payment' in entry.type_name.lower():
#             debit = entry.amount
#             credit = Decimal('0.00')
#         else:
#             credit = entry.amount
#             debit = Decimal('0.00')

#         # Calculate balance (credit - debit)
#         balance += credit - debit

#         # Append calculated data to the context list
#         entry_data.append({
#             'entry': entry,
#             'debit': debit,
#             'credit': credit,
#             'balance': balance,
#         })

#     return render(request, 'topsheetreport/topsheet_reports_list.html', {
#         'form': form,
#         'entry_data': entry_data
#     })



@login_required
def topsheet_ledger_manage(request):
    projectNames = ProjectFirstLevelName.objects.all()
    headNames = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()
    form = LedgerFilterForm(request.GET or None)

    context = {
        'projectNames': projectNames,
        'headNames': headNames,
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'topsheetreport/topsheet_ledger_manage.html', context)





@login_required
def topsheet_ledger_report(request):    
    head_type = request.GET.get('head') 
    type_value_id = request.GET.get('head_value') 
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')  

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()
   
    if is_valid(type_value_id):
        entries = entries.filter(head_id=type_value_id)
   
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)  
    

    entries = entries.order_by('date', 'id')
   
    balance = Decimal('0.00')
    entry_data = []
  
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    # Dropdown data
    projectNames = ProjectFirstLevelName.objects.all()
    heads = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()

    return render(request, 'topsheetreport/topsheet_ledger_report.html', {
        'entry_data': entry_data,
        'projectNames': projectNames,
        'heads': heads,
        'cashTypes': cashTypes,
        'selected_filters': {
            'from_date': from_date,
            'to_date': to_date,
            'head': head_type,
            'transaction': transaction_option,
        }
    })



# @login_required
# def topsheet_ledger_manage_pdf(request):
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     project = request.GET.get('project', '')
#     vendor = request.GET.get('vendor', '')

#     def is_valid(value):
#         return value is not None and value != ''

#     def parse_date(date_str):
#         try:
#             return datetime.strptime(date_str, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)
#     if not fd or not td:
#         fd = td = datetime.today().date()

#     date_cursor = fd
#     data_by_date = {}
#     while date_cursor <= td:
#         data_by_date[date_cursor] = {
#             'purchase': 0,
#             'supplier_payment': 0,
#             'sale': 0,
#             'sale_discount': 0,
#             'customer_collection': 0,
#             'expense': 0,
#         }
#         date_cursor += timedelta(days=1)

#     # Purchase from Inventories
#     inv_filters = Q()
#     if is_valid(vendor):
#         inv_filters &= Q(vendor_name__name__icontains=vendor)
#     if fd:
#         inv_filters &= Q(requisition_date__gte=fd)
#     if td:
#         inv_filters &= Q(requisition_date__lte=td)

#     inv_data = Inventories.objects.filter(inv_filters).values('requisition_date').annotate(total=Sum('amount'))
#     for item in inv_data:
#         date_key = item['requisition_date']
#         if date_key in data_by_date:
#             data_by_date[date_key]['purchase'] += float(item['total'] or 0)

#     # Supplier Payment, Customer Collection, Expense from LedgerEntry
#     ledger_filters = Q()
#     if is_valid(vendor):
#         ledger_filters &= Q(vendor__name__icontains=vendor)
#     if fd:
#         ledger_filters &= Q(date__gte=fd)
#     if td:
#         ledger_filters &= Q(date__lte=td)

#     ledger_entries = LedgerEntry.objects.filter(ledger_filters)
#     for entry in ledger_entries:
#         d = entry.date
#         if d not in data_by_date:
#             continue
#         if entry.type == "Vendor":
#             data_by_date[d]['supplier_payment'] += float(entry.debit or 0)
#         elif entry.type == "Customer":
#             data_by_date[d]['customer_collection'] += float(entry.credit or 0)
#         elif entry.type == "Expense":
#             data_by_date[d]['expense'] += float(entry.debit or 0)

#     # Sales
#     sale_filters = Q()
#     if is_valid(project):
#         sale_filters &= Q(project_name__name__icontains=project)
#     if is_valid(vendor):
#         sale_filters &= Q(customer__name__icontains=vendor)
#     if fd:
#         sale_filters &= Q(sale_date__gte=fd)
#     if td:
#         sale_filters &= Q(sale_date__lte=td)

#     sales = Sale.objects.filter(sale_filters).values('sale_date').annotate(
#         total_sale=Sum('total_amount'),
#         total_discount=Sum('sales_discount')
#     )
#     for item in sales:
#         d = item['sale_date']
#         if d in data_by_date:
#             data_by_date[d]['sale'] = float(item['total_sale'] or 0)
#             data_by_date[d]['sale_discount'] = float(item['total_discount'] or 0)

#     context = {
#         'data_by_date': dict(sorted(data_by_date.items(), reverse=True)), 
#         'from_date': fd,
#         'to_date': td,
#         'print_time': datetime.now(),
#         'selected_filters': {
#             'project': project,
#             'vendor': vendor,
#             'from_date': from_date,
#             'to_date': to_date,
#         }
#     }
#     return render(request, 'topsheetreport/topsheet_ledger_manage_pdf.html', context)
 



@login_required
def topsheet_ledger_manage_pdf(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    project = request.GET.get('project', '')
    vendor = request.GET.get('vendor', '')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)
    if not fd or not td:
        fd = td = datetime.today().date()

    date_cursor = fd
    data_by_date = {}
    while date_cursor <= td:
        data_by_date[date_cursor] = {
            'purchase': 0,
            'supplier_payment': 0,
            'sale': 0,
            'sale_discount': 0,
            'customer_collection': 0,
            'expense': 0,
        }
        date_cursor += timedelta(days=1)

    # Purchase from Inventories
    inv_filters = Q()
    if is_valid(vendor):
        inv_filters &= Q(vendor_name__name__icontains=vendor)
    if fd:
        inv_filters &= Q(purch_date__gte=fd)
    if td:
        inv_filters &= Q(purch_date__lte=td)

    inv_data = Inventories.objects.filter(inv_filters).values('purch_date').annotate(total=Sum('amount'))
    for item in inv_data:
        date_key = item['purch_date']
        if date_key in data_by_date:
            data_by_date[date_key]['purchase'] += float(item['total'] or 0)

    # Supplier Payment, Customer Collection, Expense from LedgerEntry
    ledger_filters = Q()
    if is_valid(vendor):
        ledger_filters &= Q(vendor__name__icontains=vendor)
    if fd:
        ledger_filters &= Q(date__gte=fd)
    if td:
        ledger_filters &= Q(date__lte=td)

    ledger_entries = LedgerEntry.objects.filter(ledger_filters)
    for entry in ledger_entries:
        d = entry.date
        if d not in data_by_date:
            continue
        if entry.type == "Vendor":
            data_by_date[d]['supplier_payment'] += float(entry.debit or 0)
        elif entry.type == "Customer":
            data_by_date[d]['customer_collection'] += float(entry.credit or 0)
        elif entry.type == "Expense":
            data_by_date[d]['expense'] += float(entry.debit or 0)

    # Sales
    sale_filters = Q()
    if is_valid(project):
        sale_filters &= Q(project_name__name__icontains=project)
    if is_valid(vendor):
        sale_filters &= Q(customer__name__icontains=vendor)
    if fd:
        sale_filters &= Q(sale_date__gte=fd)
    if td:
        sale_filters &= Q(sale_date__lte=td)

    sales = Sale.objects.filter(sale_filters).values('sale_date').annotate(
        total_sale=Sum('total_amount'),
        total_discount=Sum('sales_discount')
    )
    for item in sales:
        d = item['sale_date']
        if d in data_by_date:
            data_by_date[d]['sale'] = float(item['total_sale'] or 0)
            data_by_date[d]['sale_discount'] = float(item['total_discount'] or 0)

    # === Totals Calculation ===
    totals = {
        'purchase': 0,
        'supplier_payment': 0,
        'sale': 0,
        'sale_discount': 0,
        'customer_collection': 0,
        'expense': 0,
    }

    for row in data_by_date.values():
        totals['purchase'] += row['purchase']
        totals['supplier_payment'] += row['supplier_payment']
        totals['sale'] += row['sale']
        totals['sale_discount'] += row['sale_discount']
        totals['customer_collection'] += row['customer_collection']
        totals['expense'] += row['expense']
    
    totals['grand_total'] = (
        totals['purchase'] +
        totals['supplier_payment'] +
        totals['sale'] +
        totals['sale_discount'] +
        totals['customer_collection'] +
        totals['expense']
    )

    context = {
        'data_by_date': dict(sorted(data_by_date.items())), 
        'from_date': fd,
        'to_date': td,
        'print_time': datetime.now(),
        'totals': totals,
        'selected_filters': {
            'project': project,
            'vendor': vendor,
            'from_date': from_date,
            'to_date': to_date,
        }
    }
    return render(request, 'topsheetreport/topsheet_ledger_manage_pdf.html', context)
    
    
    
    
    
## Montly Collection Reports ---
@login_required
def monthly_collection_reports_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id') 
    form = LedgerReportForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })
    
    return render(request, 'monthlycollreport/monthly_collection_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })


@login_required
def monthly_collection_manage(request):
    cashTypes = CashType.objects.all()
    form = LedgerFilterForm(request.GET or None)
    projectNames = ProjectFirstLevelName.objects.all()

    context = {
        'projectNames': projectNames,
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'monthlycollreport/monthly_collection_manage.html', context)



@login_required
def monthly_collection_report(request):
    project_id = request.GET.get('project')
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude')  # 'include', 'exclude', or 'all'
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()

    # Filter by project
    if is_valid(project_id):
        entries = entries.filter(project_name_id=project_id)

    # Filter by cash type (if not using "all")
    if is_valid(cash_type_id) and balance_option != 'all':
        entries = entries.filter(cash_type_id=cash_type_id)

    # Filter by date
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)

    # Exclude "Open Balance Account" unless specifically included
    if balance_option == 'exclude':
        entries = entries.exclude(head__head_name='Open Balance Account')

    entries = entries.order_by('date', 'id')

    balance = Decimal('0.00')
    entry_data = []

    # Opening Balance Calculation
    if fd:
        if balance_option == 'include' and is_valid(cash_type_id):
            # Include opening balance for selected cash type
            opening_entries = LedgerEntry.objects.filter(
                cash_type_id=cash_type_id,
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                balance += e.credit - e.debit

        elif balance_option == 'all':
            # Include opening balance for all cash types
            opening_entries = LedgerEntry.objects.filter(
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                balance += e.credit - e.debit

    # Running balance calculation
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    # Dropdown options
    projectNames = ProjectFirstLevelName.objects.all()
    heads = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()

    return render(request, 'monthlycollreport/monthly_collection_report.html', {
        'entry_data': entry_data,
        'projectNames': projectNames,
        'heads': heads,
        'cashTypes': cashTypes,
        'selected_filters': {
            'project': project_id,
            'cash_type_name': cash_type_id,
            'from_date': from_date,
            'to_date': to_date,
            'balance': balance_option,
            'transaction': transaction_option,
        }
    })


@login_required
def monthly_collection_manage_pdf(request):
    project_id = request.GET.get('project')
    cash_type_id = request.GET.get('cash_type_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude')
    transaction_option = request.GET.get('transaction', 'datewise')

    vendor = request.GET.get('vendor', '')
    type_ = request.GET.get('type', '')
    head = request.GET.get('head', '')
    contractor = request.GET.get('contractor', '')

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()

    # Apply filters
    if is_valid(cash_type_id) and balance_option != 'all':
        entries = entries.filter(cash_type_id=cash_type_id)
    if is_valid(project_id):
        entries = entries.filter(project_name_id=project_id)
    if is_valid(vendor):
        entries = entries.filter(vendor__icontains=vendor)
    if is_valid(type_):
        entries = entries.filter(type__icontains=type_)
    if is_valid(head):
        entries = entries.filter(head__head_name__icontains=head)
    if is_valid(contractor):
        entries = entries.filter(contractor__icontains=contractor)

    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)

    if balance_option == 'exclude':
        entries = entries.exclude(head__head_name='Open Balance Account')

    entries = entries.order_by('date', 'id')

    # Opening balance calculation
    opening_balance = Decimal('0.00')
    if fd:
        if balance_option == 'include' and is_valid(cash_type_id):
            opening_entries = LedgerEntry.objects.filter(
                cash_type_id=cash_type_id,
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                opening_balance += e.credit - e.debit

        elif balance_option == 'all':
            opening_entries = LedgerEntry.objects.filter(
                head__head_name='Open Balance Account',
                date__lt=fd
            )
            for e in opening_entries:
                opening_balance += e.credit - e.debit

    # Grouping entries by date
    grouped_data = defaultdict(list)
    for entry in entries:
        grouped_data[entry.date].append(entry)

    entry_data = []
    running_balance = opening_balance
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for date in sorted(grouped_data.keys()):
        daily_entries = grouped_data[date]
        daily_data = []
        daily_debit = Decimal('0.00')
        daily_credit = Decimal('0.00')

        for entry in daily_entries:
            running_balance += entry.credit - entry.debit
            daily_debit += entry.debit
            daily_credit += entry.credit
            daily_data.append({
                'entry': entry,
                'balance': running_balance
            })

        entry_data.append({
            'date': date,
            'entries': daily_data,
            'daily_debit': daily_debit,
            'daily_credit': daily_credit,
            'daily_balance': running_balance
        })

        total_debit += daily_debit
        total_credit += daily_credit

    final_balance = total_credit - total_debit

    from num2words import num2words

    def amount_to_words(amount):
        try:
            amount = float(amount)
            is_negative = amount < 0
            amount = abs(amount)
    
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
    
            words = num2words(integer_part, lang='en_IN').title().replace(",", "")
            words += " Taka"
    
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
    
            words += " only"
    
            if is_negative:
                words = "- " + words
    
            return words
        except Exception as e:
            return f"{amount} Taka only"


    cash_type_name = ''
    if is_valid(cash_type_id):
        ct = CashType.objects.filter(id=cash_type_id).first()
        cash_type_name = ct.cash_type_name if ct else ''

    context = {
        'entry_data': entry_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': final_balance,
        'balance_in_words': amount_to_words(final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'project': project_id,
            'vendor': vendor,
            'type': type_,
            'head': head,
            'contractor': contractor,
            'cash_type': cash_type_name,
            'from_date': from_date,
            'to_date': to_date,
            'balance': balance_option,
            'transaction': transaction_option,
        }
    }

    return render(request, 'monthlycollreport/monthly_collection_manage_pdf.html', context)



## -----  Bank Reconsoluion -----
@login_required
def upload_statement(request):
    if request.method == 'POST':
        form = BankStatementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('upload_statement')
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip header row if exists

            for row in csv.reader(io_string, delimiter=',', quotechar='"'):
                # Expected CSV columns: bank_id, date, description, amount
                # Adjust indices according to your CSV format
                bank_id = int(row[0])
                date = row[1]
                description = row[2]
                amount = float(row[3])
                bank = get_object_or_404(CashType, pk=bank_id)

                BankStatementTransaction.objects.create(
                    bank=bank,
                    date=date,
                    description=description,
                    amount=amount,
                )
            messages.success(request, 'Bank statement uploaded successfully.')
            return redirect('upload_statement')
    else:
        form = BankStatementUploadForm()
    return render(request, 'accounting/upload_statement.html', {'form': form})


# @login_required
# def reconciliation_dashboard(request):
#     bank_accounts = CashType.objects.all()
#     return render(request, 'accounting/reconciliation_dashboard.html', {'bank_accounts': bank_accounts})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from .models import LedgerEntry, CashType

@login_required
def reconciliation_dashboard(request):
    """
    Bank Reconciliation Dashboard:
    Display each cash_type name with total debit and total credit
    """
    # Aggregate debit and credit per cash_type
    bank_summary = (
        LedgerEntry.objects
        .filter(cash_type__isnull=False)
        .exclude(cash_type__cash_type_name='No_Method') 
        .values('cash_type', 'cash_type__cash_type_name')  # cash_type_name from CashType
        .annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        .order_by('cash_type__cash_type_name')
    )

    return render(
        request,
        'accounting/reconciliation_dashboard.html',
        {'bank_summary': bank_summary}
    )



# @login_required
# def reconciliation_list(request, bank_id):
#     bank = get_object_or_404(CashType, pk=bank_id)
#     transactions = BankStatementTransaction.objects.filter(bank=bank)
#     return render(request, 'accounting/reconciliation_list.html', {'bank': bank, 'transactions': transactions})



from .models import CashType, TransactionHistory

@login_required
def reconciliation_list(request, bank_id):
    # Get the CashType object
    bank = get_object_or_404(CashType, pk=bank_id)

    # Fetch all transactions linked to this cash_type
    transactions = TransactionHistory.objects.filter(
        cash_type=bank
    ).exclude(cash_type__cash_type_name='No_Method')  # exclude 'No_Method'

    # Optional: order by date
    transactions = transactions.order_by('-date', '-id')

    return render(
        request,
        'accounting/reconciliation_list.html',
        {
            'bank': bank,
            'transactions': transactions
        }
    )


@login_required
def reconciliation_create(request, bank_id):
    bank = get_object_or_404(CashType, id=bank_id)

    if request.method == 'POST':
        form = ReconciliationForm(request.POST, bank=bank)
        if form.is_valid():
            reconciliation = form.save(commit=False)
            reconciliation.bank_account = bank
            reconciliation.reconciled_by = request.user.username
            reconciliation.save()

            # Mark the statement transaction as matched
            reconciliation.statement_txn.matched = True
            reconciliation.statement_txn.save()

            return redirect('reconciliation_list', bank_id=bank.id)
    else:
        form = ReconciliationForm(bank=bank)

    return render(request, 'accounting/reconciliation_form.html', {
        'form': form,
        'bank': bank,
    })


@login_required
def reconciliation_report(request, bank_id):
    bank = get_object_or_404(CashType, pk=bank_id)
    reconciliations = AccountReconciliation.objects.filter(bank_account=bank)
    return render(request, 'accounting/reconciliation_report.html', {'bank': bank, 'reconciliations': reconciliations})



## Supplier Reports module ----
@login_required
def supplier_reports_manage_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id') 
    form = LedgerReportForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'supplierledger/supplier_reports_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })



@login_required
def supplier_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    head = HeadOfAccount.objects.all()
    form = LedgerFilterForm(request.GET or None)
    head_exp_name = HeadOfExpense.objects.all()
    cashTypes = CashType.objects.all()
    context = {
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'head_exp_name': head_exp_name,
        'today': date.today(),
    }
    return render(request, 'supplierledger/supplier_ledger_manage.html', context)


@login_required
def ledger_sup_details(request):
    vendor_id = request.GET.get('cash_type_name')
    project_id = request.GET.get('project')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction')  # 'alldate' or 'datewise'

    inventories = Inventories.objects.all()

    if vendor_id:
        inventories = inventories.filter(vendor_name_id=vendor_id)

    if project_id:
        inventories = inventories.filter(project_name_id=project_id)

    if transaction_option == 'datewise':
        fd = parse_date(from_date)
        td = parse_date(to_date)

        if fd:
            inventories = inventories.filter(purch_date__gte=fd)
        if td:
            inventories = inventories.filter(purch_date__lte=td)
    elif transaction_option == 'alldate':
        # No date filter, all dates for this vendor and project
        pass

    context = {
        'inventories': inventories,
        'filters': request.GET,
    }
    return render(request, 'supplierledger/ledger_report_details.html', context)
    





@login_required
def supplier_ledger_report(request):
    project_id = request.GET.get('project')
    vendor_id = request.GET.get('vendor')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Filter suppliers
    suppliers = Suppliers.objects.all()
    if is_valid(vendor_id):
        suppliers = suppliers.filter(id=vendor_id)

    report_data = []

    for supplier in suppliers:
        # === Filter Requisitions ===
        requisitions = Requisition.objects.filter(type='Supplier', vendor_name=supplier, purch_appov='Yes')

        if is_valid(project_id):
            requisitions = requisitions.filter(project_name_id=project_id)

        if transaction_option == 'datewise':
            if fd:
                requisitions = requisitions.filter(requisition_date__gte=fd)
            if td:
                requisitions = requisitions.filter(requisition_date__lte=td)

        boq_total = requisitions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Filter Debit Vouchers ===
        debits = DebitVoucher.objects.filter(vendor=supplier, type='Vendor', approval_dr_status=True)

        if is_valid(project_id):
            debits = debits.filter(project_name_id=project_id)

        if transaction_option == 'datewise':
            if fd:
                debits = debits.filter(date__gte=fd)
            if td:
                debits = debits.filter(date__lte=td)

        debit_total = debits.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Calculate Balance ===
        balance = boq_total - debit_total

        # === Prepare report data ===
        report_data.append({
            'supplier': supplier,
            'boq_total': boq_total,
            'debit_total': debit_total,
            'balance': balance,
            'requisitions': requisitions,
            'debit_entries': debits,
        })

    # === Render to template ===
    return render(request, 'supplierledger/supplier_ledger_report.html', {
        'report_data': report_data,
        'filters': {
            'project': project_id,
            'vendor': vendor_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })



##  -------------------------------

# @login_required
# def supplier_ledger_manage_pdf(request):
#     project_id = request.GET.get('project')
#     vendor_id = request.GET.get('vendor')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except Exception:
#             return None

#     def get_name(model_class, obj_id, name_field):
#         if is_valid(obj_id):
#             obj = model_class.objects.filter(id=obj_id).first()
#             return getattr(obj, name_field, "All") if obj else "All"
#         return "All"

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     suppliers = Suppliers.objects.all()
#     if is_valid(vendor_id):
#         suppliers = suppliers.filter(id=vendor_id)

#     report_data = []

#     for supplier in suppliers:
#         requisitions = Requisition.objects.filter(
#             type='Supplier', vendor_name=supplier, purch_appov='Yes'
#         )
#         if is_valid(project_id):
#             requisitions = requisitions.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 requisitions = requisitions.filter(requisition_date__gte=fd)
#             if td:
#                 requisitions = requisitions.filter(requisition_date__lte=td)

#         grouped_requisitions = requisitions.values('requi_uniq_id').annotate(
#             total_amount=Sum('amount'),
#             requisition_date=Min('requisition_date'),
#             remark=Min('remark'),
#             item=Min('item_name__head_requi_name'),
#             employee=Min('employee_name__employee_name')
#         ).order_by('requisition_date')

#         boq_total = grouped_requisitions.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

#         debits = DebitVoucher.objects.filter(
#             vendor=supplier,
#             type='Vendor',
#             approval_dr_status=True  # âœ… Show only approved
#         )
#         if is_valid(project_id):
#             debits = debits.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 debits = debits.filter(date__gte=fd)
#             if td:
#                 debits = debits.filter(date__lte=td)

#         debit_total = debits.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         balance = boq_total - debit_total

#         combined_entries = []

#         for req in grouped_requisitions:
#             combined_entries.append({
#                 'date': req['requisition_date'],
#                 'type': 'Requisition',
#                 'description': req['remark'] or '',
#                 'chq_rec_no': f"Requi-{req['requi_uniq_id']}",
#                 'payment': None,
#                 'received': req['total_amount'],
#                 'head_name': '',
#                 'carrier': req['employee'] or '-',
#             })

#         for debit in debits:
#             combined_entries.append({
#                 'date': debit.date,
#                 'type': 'Debit Voucher',
#                 'description': debit.particulars or '',
#                 'chq_rec_no': debit.cheque_number or '-',
#                 'payment': debit.amount,
#                 'received': None,
#                 'head_name': debit.head_of_account.head_name if debit.head_of_account else '',
#                 'carrier': debit.carrier or '-',
#             })

#         combined_entries.sort(key=lambda x: x['date'])

#         running_balance = 0
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += (received - payment)
#             entry['balance'] = running_balance

#         report_data.append({
#             'supplier': supplier,
#             'boq_total': boq_total,
#             'debit_total': debit_total,
#             'balance': balance,
#             'ledger_entries': combined_entries,
#         })

#     total_boq = sum(x['boq_total'] for x in report_data)
#     total_debit = sum(x['debit_total'] for x in report_data)
#     final_balance = total_boq - total_debit

#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'total_boq': total_boq,
#         'total_debit': total_debit,
#         'final_balance': final_balance,
#         'balance_in_words': amount_to_words(final_balance),
#         'print_time': datetime.now(),
#         'selected_filters': {
#             'project': get_name(ProjectFirstLevelName, project_id, 'project_first_name'),
#             'vendor': get_name(Suppliers, vendor_id, 'supplier_name'),
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'supplierledger/supplier_ledger_report_print.html', context)

 
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from num2words import num2words


@login_required
def supplier_ledger_manage_pdf(request):
    project_id = request.GET.get('project')
    vendor_id = request.GET.get('vendor')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null', '0']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    def get_name(model_class, obj_id, name_field):
        if is_valid(obj_id):
            obj = model_class.objects.filter(id=obj_id).first()
            return getattr(obj, name_field, "All") if obj else "All"
        return "All"

    fd = parse_date(from_date)
    td = parse_date(to_date)

    suppliers = Suppliers.objects.all()
    if is_valid(vendor_id):
        suppliers = suppliers.filter(id=vendor_id)

    report_data = []

    for supplier in suppliers:
        raw_entries = []

        # 1. FETCH PAYMENTS / DEBITS FROM LedgerEntry (Vendor type)
        ledger_qs = LedgerEntry.objects.filter(type='Vendor', vendor=supplier)
        if is_valid(project_id):
            ledger_qs = ledger_qs.filter(project_name_id=project_id)
        if transaction_option == 'datewise':
            if fd:
                ledger_qs = ledger_qs.filter(date__gte=fd)
            if td:
                ledger_qs = ledger_qs.filter(date__lte=td)

        for entry in ledger_qs:
            raw_entries.append({
                'source': 'ledger',
                'date': entry.date,
                'type': 'Payment',
                'description': entry.description or '',
                'chq_rec_no': getattr(entry, 'cheque_number', '') or '-',
                'payment': entry.debit or Decimal('0.00'),   # Payment made to vendor
                'received': entry.credit or Decimal('0.00'),  # Any credit adjustment
                'head_name': entry.head.head_name if entry.head else '',
                'carrier': '-',
            })

        # 2. FETCH PURCHASES FROM Inventories (Grouped by Date)
        inv_qs = Inventories.objects.filter(vendor_name=supplier)
        if is_valid(project_id):
            inv_qs = inv_qs.filter(project_name_id=project_id)
        if transaction_option == 'datewise':
            if fd:
                inv_qs = inv_qs.filter(purch_date__gte=fd)
            if td:
                inv_qs = inv_qs.filter(purch_date__lte=td)

        grouped_inventory = (
            inv_qs
            .values('purch_date', 'project_name')
            .annotate(total_amount=Sum('amount'))
            .order_by('purch_date')
        )

        for inv in grouped_inventory:
            # Build comma-separated list of purchased item names for the day
            same_day_items = Inventories.objects.filter(
                vendor_name=supplier,
                purch_date=inv['purch_date']
            )
            if is_valid(project_id):
                same_day_items = same_day_items.filter(project_name_id=project_id)

            item_names = ", ".join(
                same_day_items.values_list(
                    'item_name__head_requi_name', flat=True
                ).distinct()
            )

            raw_entries.append({
                'source': 'inventory',
                'date': inv['purch_date'],
                'type': 'Inventory Purchase',
                'description': f"Purchase - {item_names}" if item_names else "Inventory Purchase",
                'chq_rec_no': 'INV',
                'payment': Decimal('0.00'),
                'received': inv['total_amount'] or Decimal('0.00'),  # Goods received/purchased
                'head_name': 'Inventory Purchase',
                'carrier': '-',
            })

        # 3. SORT CHRONOLOGICALLY
        raw_entries.sort(key=lambda x: x['date'])

        # 4. CALCULATE RUNNING BALANCE & SUPPLIER TOTALS
        supplier_boq_total = Decimal('0.00')
        supplier_debit_total = Decimal('0.00')
        running_balance = Decimal('0.00')

        for entry in raw_entries:
            received = entry['received']
            payment = entry['payment']
            supplier_boq_total += received
            supplier_debit_total += payment
            running_balance += (received - payment)
            entry['balance'] = running_balance

        balance = supplier_boq_total - supplier_debit_total

        report_data.append({
            'supplier': supplier,
            'boq_total': supplier_boq_total,
            'debit_total': supplier_debit_total,
            'balance': balance,
            'ledger_entries': raw_entries,
        })

    # OVERALL SUMMARY CALCULATIONS
    total_boq = sum(x['boq_total'] for x in report_data)
    total_debit = sum(x['debit_total'] for x in report_data)
    final_balance = total_boq - total_debit

    def amount_to_words(amount):
        try:
            amount = float(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en').title() + " Taka"
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
            words += " only"
            return words
        except Exception:
            return f"{amount} Taka only"

    context = {
        'report_data': report_data,
        'total_boq': total_boq,
        'total_debit': total_debit,
        'final_balance': final_balance,
        'balance_in_words': amount_to_words(final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'project': get_name(ProjectFirstLevelName, project_id, 'project_first_name'),
            'vendor': get_name(Suppliers, vendor_id, 'supplier_name'),
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    }

    return render(request, 'supplierledger/supplier_ledger_report_print.html', context)
    
    
@login_required
def supplier_summary_report(request):
    suppliers = Suppliers.objects.all()
    report_data = []
    
    for supplier in suppliers:
        #boq_items = Requisition.objects.filter(vendor_name=supplier.supplier_name) 
        boq_items = Requisition.objects.filter(type='Supplier',vendor_name=supplier.supplier_name,purch_appov='Yes')
        boq_total = boq_items.aggregate(total_amount=Sum('amount'))['total_amount'] or 0 
        debit_entries = DebitVoucher.objects.filter(vendor=supplier)
        debit_total = debit_entries.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        print(debit_total)
        report_data.append({
            'supplier': supplier,
            'boq_items': boq_items,
            'boq_total': boq_total,
            'debit_entries': debit_entries,
            'debit_total': debit_total,
        })

    return render(request, 'reportmanage/supplier_summary.html', {'report_data': report_data})
    


@login_required
def project_ledger_list(request):
    projectNames = ProjectFirstLevelName.objects.select_related('location', 'project_owner').all()
    context = {
        'projectNames': projectNames,
        'today': date.today(),
    }
    return render(request, 'projectreport/project_ledger_list.html', context)
    
  
  
@login_required
def project_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    head = HeadOfAccount.objects.all()
    form = LedgerFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  # <-- clearer naming
    cashTypes = CashType.objects.all()
    
    context = {
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'projectreport/project_ledger_manage.html', context)



# @login_required
# def project_ledger_report(request):
#     project_id = request.GET.get('project')
#     vendor_id = request.GET.get('vendor')
#     item_id = request.GET.get('item')  
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except Exception:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Start with all inventory entries
#     inventories = Inventories.objects.all()

#     # Filter by vendor if provided
#     if is_valid(vendor_id):
#         inventories = inventories.filter(vendor_name_id=vendor_id)

#     # Filter by project if provided
#     if is_valid(project_id):
#         inventories = inventories.filter(project_name_id=project_id)

#     # Filter by item if provided
#     if is_valid(item_id):
#         inventories = inventories.filter(item_name_id=item_id)

#     # Filter by date range if transaction option is datewise
#     if transaction_option == 'datewise':
#         if fd:
#             inventories = inventories.filter(requisition_date__gte=fd)
#         if td:
#             inventories = inventories.filter(requisition_date__lte=td)

#     # Prepare report data grouped by vendor
#     report_data = []

#     # Get distinct vendor ids from filtered inventories
#     vendor_ids = inventories.values_list('vendor_name_id', flat=True).distinct()

#     for vid in vendor_ids:
#         vendor = get_object_or_404(Suppliers, id=vid)
#         vendor_inventories = inventories.filter(vendor_name_id=vid)
#         total_amount = vendor_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         report_data.append({
#             'supplier': vendor,
#             'boq_total': total_amount,
#             'requisitions': vendor_inventories,
#         })

#     return render(request, 'projectreport/project_ledger_report.html', {
#         'report_data': report_data,
#         'filters': {
#             'project': project_id,
#             'vendor': vendor_id,
#             'item': item_id,
#             'from_date': from_date,
#             'to_date': to_date,
#             'transaction': transaction_option,
#         }
#     })
    
    


@login_required
def project_ledger_report(request):
    project_id = request.GET.get('project')
    vendor_id = request.GET.get('vendor')
    item_id = request.GET.get('item')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Start with all inventory entries
    inventories = Inventories.objects.all()

    # Filter by project/vendor/item/date
    if is_valid(project_id):
        inventories = inventories.filter(project_name_id=project_id)
    if is_valid(vendor_id):
        inventories = inventories.filter(vendor_name_id=vendor_id)
    if is_valid(item_id):
        inventories = inventories.filter(item_name_id=item_id)
    if transaction_option == 'datewise':
        if fd:
            inventories = inventories.filter(requisition_date__gte=fd)
        if td:
            inventories = inventories.filter(requisition_date__lte=td)

    # Group by project first
    project_ids = inventories.values_list('project_name_id', flat=True).distinct()
    report_data = []

    for pid in project_ids:
        project = get_object_or_404(ProjectFirstLevelName, id=pid)
        project_inventories = inventories.filter(project_name_id=pid)

        # Group by vendor within this project
        vendor_groups = []
        vendor_ids = project_inventories.values_list('vendor_name_id', flat=True).distinct()
        for vid in vendor_ids:
            vendor = get_object_or_404(Suppliers, id=vid) if vid else None
            vendor_inventories = project_inventories.filter(vendor_name_id=vid)
            total_amount = vendor_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            vendor_groups.append({
                'vendor': vendor,
                'inventory_list': vendor_inventories,
                'inventory_total': total_amount,
            })

        report_data.append({
            'project': project,
            'inventory_list': project_inventories,
            'inventory_total': project_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'vendor_groups': vendor_groups,
        })

    return render(request, 'projectreport/project_ledger_report.html', {
        'report_data': report_data,
        'selected_filters': {
            'project': project_id,
            'vendor': vendor_id,
            'item': item_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        },
        'print_time': datetime.now(),
    })
    
    

# @login_required
# def project_ledger_manage_pdf(request):
#     type_option = request.GET.get('type', 'Project')
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Get projects queryset
#     if is_valid(project_id):
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     report_data = []

#     # Initialize grand totals
#     grand_boq_total = Decimal('0.00')
#     grand_requisition_total = Decimal('0.00')
#     grand_inventory_total = Decimal('0.00')
#     grand_ledger_total_payment = Decimal('0.00')
#     grand_ledger_total_received = Decimal('0.00')
#     grand_loanvoucher_total = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'boq_list': [],
#             'requisition_list': [],
#             'inventory_list': [],
#             'ledger_list': [],
#             'loanvoucher_list': [],
#         }

#         # 1. BOQ
#         boq_items = BOQ.objects.filter(project_name=project)
#         project_block['boq_list'] = boq_items

#         # 2. Requisition
#         requisitions = Requisition.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 requisitions = requisitions.filter(requisition_date__gte=fd)
#             if td:
#                 requisitions = requisitions.filter(requisition_date__lte=td)
#         project_block['requisition_list'] = requisitions

#         # 3. Inventories
#         inventories = Inventories.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(requisition_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(requisition_date__lte=td)
#         project_block['inventory_list'] = inventories

#         # 4. Ledger Entries
#         ledgers = LedgerEntry.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         project_block['ledger_list'] = ledgers

#         # 5. Loan Voucher Entries
#         loanvouchers = LoanVoucher.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 loanvouchers = loanvouchers.filter(date__gte=fd)
#             if td:
#                 loanvouchers = loanvouchers.filter(date__lte=td)
#         loanvouchers = loanvouchers.order_by('date')
#         project_block['loanvoucher_list'] = loanvouchers

#         # Totals
#         boq_total = sum(item.amount for item in boq_items)
#         requisition_total = sum(item.amount for item in requisitions)
#         inventory_total = sum(item.amount for item in inventories)
#         ledger_total_payment = sum(item.debit for item in ledgers)
#         ledger_total_received = sum(item.credit for item in ledgers)
#         loanvoucher_total = sum(item.amount for item in loanvouchers)

#         project_block['boq_total'] = boq_total
#         project_block['requisition_total'] = requisition_total
#         project_block['inventory_total'] = inventory_total
#         project_block['ledger_total_payment'] = ledger_total_payment
#         project_block['ledger_total_received'] = ledger_total_received
#         project_block['loanvoucher_total'] = loanvoucher_total

#         # Ledger balance for project
#         project_ledger = ledger_total_received - ledger_total_payment
#         project_block['project_ledger'] = project_ledger

#         # Add to grand totals
#         grand_boq_total += boq_total
#         grand_requisition_total += requisition_total
#         grand_inventory_total += inventory_total
#         grand_ledger_total_payment += ledger_total_payment
#         grand_ledger_total_received += ledger_total_received
#         grand_loanvoucher_total += loanvoucher_total

#         report_data.append(project_block)

#     # Convert amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)

#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))

#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"

#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"

#             words += " only"

#             if is_negative:
#                 words = "- " + words

#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'project_ledger': project_ledger if projects else Decimal('0.00'),
#         'grand_boq_total': grand_boq_total,
#         'grand_requisition_total': grand_requisition_total,
#         'grand_inventory_total': grand_inventory_total,
#         'grand_ledger_total_payment': grand_ledger_total_payment,
#         'grand_ledger_total_received': grand_ledger_total_received,
#         'grand_loanvoucher_total': grand_loanvoucher_total,
#         'grand_total_amount': grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total,
#         'grand_total_in_words': amount_to_words(grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'type': type_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'projectreport/project_ledger_manage_pdf.html', context)




# @login_required
# def project_ledger_manage_pdf(request):
#     type_option = request.GET.get('type', 'Project')
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Get projects queryset
#     if is_valid(project_id):
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     report_data = []

#     # Initialize grand totals
#     grand_boq_total = Decimal('0.00')
#     grand_requisition_total = Decimal('0.00')
#     grand_inventory_total = Decimal('0.00')
#     grand_ledger_total_payment = Decimal('0.00')
#     grand_ledger_total_received = Decimal('0.00')
#     grand_loanvoucher_total = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'boq_list': [],
#             'requisition_list': [],
#             'inventory_list': [],
#             'ledger_list': [],
#             'loanvoucher_list': [],
#         }

#         # 1. BOQ
#         boq_items = BOQ.objects.filter(project_name=project)
#         project_block['boq_list'] = boq_items

#         # 2. Requisition
#         requisitions = Requisition.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 requisitions = requisitions.filter(requisition_date__gte=fd)
#             if td:
#                 requisitions = requisitions.filter(requisition_date__lte=td)
#         project_block['requisition_list'] = requisitions

#         # 3. Inventories
#         inventories = Inventories.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(requisition_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(requisition_date__lte=td)
#         project_block['inventory_list'] = inventories

#         # 4. Ledger Entries
#         #ledgers = LedgerEntry.objects.filter(project_name=project)
#         ledgers = LedgerEntry.objects.filter(project_name=project).exclude(cash_type__cash_type_name='No_Method')

#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledgers = ledgers.order_by('date', 'id')  # ensure consistent order

#         # --- Calculate running balance per ledger entry ---
#         running_balance = Decimal('0.00')
#         ledger_list_with_balance = []
#         for entry in ledgers:
#             running_balance += (entry.credit or Decimal('0.00')) - (entry.debit or Decimal('0.00'))
#             entry.running_balance = running_balance
#             ledger_list_with_balance.append(entry)
#         project_block['ledger_list'] = ledger_list_with_balance

#         # 5. Loan Voucher Entries
#         #loanvouchers = LoanVoucher.objects.filter(project_name=project).exclude(cash_type__cash_type_name='No_Method')
#         loanvouchers = LoanVoucher.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 loanvouchers = loanvouchers.filter(date__gte=fd)
#             if td:
#                 loanvouchers = loanvouchers.filter(date__lte=td)
#         loanvouchers = loanvouchers.order_by('date')
#         project_block['loanvoucher_list'] = loanvouchers

#         # Totals
#         boq_total = sum(item.amount for item in boq_items)
#         requisition_total = sum(item.amount for item in requisitions)
#         inventory_total = sum(item.amount for item in inventories)
#         ledger_total_payment = sum(item.debit for item in ledgers)
#         ledger_total_received = sum(item.credit for item in ledgers)
#         loanvoucher_total = sum(item.amount for item in loanvouchers)

#         project_block['boq_total'] = boq_total
#         project_block['requisition_total'] = requisition_total
#         project_block['inventory_total'] = inventory_total
#         project_block['ledger_total_payment'] = ledger_total_payment
#         project_block['ledger_total_received'] = ledger_total_received
#         project_block['loanvoucher_total'] = loanvoucher_total

#         # Ledger balance for project
#         project_ledger = ledger_total_received - ledger_total_payment
#         project_block['project_ledger'] = project_ledger

#         # Add to grand totals
#         grand_boq_total += boq_total
#         grand_requisition_total += requisition_total
#         grand_inventory_total += inventory_total
#         grand_ledger_total_payment += ledger_total_payment
#         grand_ledger_total_received += ledger_total_received
#         grand_loanvoucher_total += loanvoucher_total

#         report_data.append(project_block)

#     # Convert amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
#             words += " only"
#             if is_negative:
#                 words = "- " + words
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'project_ledger': project_ledger if projects else Decimal('0.00'),
#         'grand_boq_total': grand_boq_total,
#         'grand_requisition_total': grand_requisition_total,
#         'grand_inventory_total': grand_inventory_total,
#         'grand_ledger_total_payment': grand_ledger_total_payment,
#         'grand_ledger_total_received': grand_ledger_total_received,
#         'grand_loanvoucher_total': grand_loanvoucher_total,
#         'grand_total_amount': grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total,
#         'grand_total_in_words': amount_to_words(grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'type': type_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'projectreport/project_ledger_manage_pdf.html', context)
   


from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from num2words import num2words

# NOTE: keep your existing model imports (ProjectFirstLevelName, BOQ, Requisition,
# Inventories, LedgerEntry, LoanVoucher) exactly as they already are in this file.


## -- design --ok project update design

# @login_required
# def project_ledger_manage_pdf(request):
#     type_option = request.GET.get('type', 'Project')
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except (TypeError, ValueError):
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Get projects queryset
#     if is_valid(project_id):
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     report_data = []

#     # Initialize grand totals
#     grand_boq_total = Decimal('0.00')
#     grand_requisition_total = Decimal('0.00')
#     grand_inventory_total = Decimal('0.00')
#     grand_ledger_total_payment = Decimal('0.00')
#     grand_ledger_total_received = Decimal('0.00')
#     grand_loanvoucher_total = Decimal('0.00')
#     grand_stock_value = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'boq_list': [],
#             'requisition_list': [],
#             'inventory_list': [],
#             'ledger_list': [],
#             'loanvoucher_list': [],
#             'stock_summary': [],
#             'boq_status_summary': [],
#         }

#         # 1. BOQ
#         boq_items = BOQ.objects.filter(project_name=project)
#         project_block['boq_list'] = boq_items

#         # 2. Requisition
#         requisitions = Requisition.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 requisitions = requisitions.filter(requisition_date__gte=fd)
#             if td:
#                 requisitions = requisitions.filter(requisition_date__lte=td)
#         project_block['requisition_list'] = requisitions

#         # 3. Inventories (Purchase)
#         inventories = Inventories.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(requisition_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(requisition_date__lte=td)
#         project_block['inventory_list'] = inventories

#         # 4. Ledger Entries
#         ledgers = LedgerEntry.objects.filter(project_name=project).exclude(
#             cash_type__cash_type_name='No_Method'
#         )
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledgers = ledgers.order_by('date', 'id')

#         # --- Calculate running balance per ledger entry ---
#         running_balance = Decimal('0.00')
#         ledger_list_with_balance = []
#         for entry in ledgers:
#             running_balance += (entry.credit or Decimal('0.00')) - (entry.debit or Decimal('0.00'))
#             entry.running_balance = running_balance
#             ledger_list_with_balance.append(entry)
#         project_block['ledger_list'] = ledger_list_with_balance

#         # 5. Loan Voucher Entries (Payable / Receivable)
#         loanvouchers = LoanVoucher.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 loanvouchers = loanvouchers.filter(date__gte=fd)
#             if td:
#                 loanvouchers = loanvouchers.filter(date__lte=td)
#         loanvouchers = loanvouchers.order_by('date')
#         project_block['loanvoucher_list'] = loanvouchers

#         # --- Totals ---
#         boq_total = sum((item.amount or Decimal('0.00')) for item in boq_items)
#         requisition_total = sum((item.amount or Decimal('0.00')) for item in requisitions)
#         inventory_total = sum((item.amount or Decimal('0.00')) for item in inventories)
#         ledger_total_payment = sum((item.debit or Decimal('0.00')) for item in ledgers)
#         ledger_total_received = sum((item.credit or Decimal('0.00')) for item in ledgers)
#         loanvoucher_total = sum((item.amount or Decimal('0.00')) for item in loanvouchers)

#         project_block['boq_total'] = boq_total
#         project_block['requisition_total'] = requisition_total
#         project_block['inventory_total'] = inventory_total
#         project_block['ledger_total_payment'] = ledger_total_payment
#         project_block['ledger_total_received'] = ledger_total_received
#         project_block['loanvoucher_total'] = loanvoucher_total

#         # Net ledger position for the project (used as "Profit / Loss" card)
#         project_ledger = ledger_total_received - ledger_total_payment
#         project_block['project_ledger'] = project_ledger
#         project_block['profit_loss'] = project_ledger

#         # Budget vs actual purchase spend (BOQ planned vs Inventory actual)
#         project_block['budget_balance'] = boq_total - inventory_total

#         # --- 6. Stock Summary (aggregated per item, like the "Store & Stock" widget) ---
#         stock_map = OrderedDict()
#         for inv in inventories:
#             key = inv.item_name_id
#             if key not in stock_map:
#                 stock_map[key] = {
#                     'item_name': inv.item_name,
#                     'unit': inv.unit,
#                     'received': 0,
#                     'balance': 0,
#                     'amount': Decimal('0.00'),
#                 }
#             stock_map[key]['received'] += inv.qty
#             stock_map[key]['balance'] += inv.qtysub
#             stock_map[key]['amount'] += (inv.amount or Decimal('0.00'))

#         stock_summary = []
#         stock_value_total = Decimal('0.00')
#         for s in stock_map.values():
#             s['issued'] = s['received'] - s['balance']
#             unit_rate = (s['amount'] / s['received']) if s['received'] else Decimal('0.00')
#             s['stock_value'] = (Decimal(s['balance']) * unit_rate).quantize(Decimal('0.01'))
#             stock_value_total += s['stock_value']
#             stock_summary.append(s)

#         project_block['stock_summary'] = stock_summary
#         project_block['stock_value'] = stock_value_total
#         grand_stock_value += stock_value_total

#         # --- 7. BOQ status-wise breakdown (Completed / Running / Pending / Variation etc.) ---
#         boq_status_map = OrderedDict()
#         for item in boq_items:
#             key = item.status_item or 'Not Set'
#             if key not in boq_status_map:
#                 boq_status_map[key] = {'status': key, 'count': 0, 'amount': Decimal('0.00')}
#             boq_status_map[key]['count'] += 1
#             boq_status_map[key]['amount'] += (item.amount or Decimal('0.00'))
#         project_block['boq_status_summary'] = list(boq_status_map.values())
#         project_block['boq_item_count'] = boq_items.count()

#         # Add to grand totals
#         grand_boq_total += boq_total
#         grand_requisition_total += requisition_total
#         grand_inventory_total += inventory_total
#         grand_ledger_total_payment += ledger_total_payment
#         grand_ledger_total_received += ledger_total_received
#         grand_loanvoucher_total += loanvoucher_total

#         report_data.append(project_block)

#     grand_profit_loss = grand_ledger_total_received - grand_ledger_total_payment
#     grand_budget_balance = grand_boq_total - grand_inventory_total

#     # Convert amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
#             words += " only"
#             if is_negative:
#                 words = "- " + words
#             return words
#         except (ValueError, TypeError):
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'grand_boq_total': grand_boq_total,
#         'grand_requisition_total': grand_requisition_total,
#         'grand_inventory_total': grand_inventory_total,
#         'grand_ledger_total_payment': grand_ledger_total_payment,
#         'grand_ledger_total_received': grand_ledger_total_received,
#         'grand_loanvoucher_total': grand_loanvoucher_total,
#         'grand_stock_value': grand_stock_value,
#         'grand_profit_loss': grand_profit_loss,
#         'grand_budget_balance': grand_budget_balance,
#         'grand_total_amount': grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total,
#         'grand_total_in_words': amount_to_words(
#             grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total
#         ),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'type': type_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'projectreport/project_ledger_manage_pdf.html', context)




## ok code --

# from collections import OrderedDict
# from datetime import datetime
# from decimal import Decimal

# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from num2words import num2words

# # NOTE: keep your existing model imports (ProjectFirstLevelName, BOQ, Requisition,
# # Inventories, LedgerEntry, LoanVoucher) exactly as they already are in this file.


# @login_required
# def project_ledger_manage_pdf(request):
#     type_option = request.GET.get('type', 'Project')
#     project_id = request.GET.get('project')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except (TypeError, ValueError):
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Get projects queryset
#     if is_valid(project_id):
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     report_data = []

#     # Initialize grand totals
#     grand_boq_total = Decimal('0.00')
#     grand_requisition_total = Decimal('0.00')
#     grand_inventory_total = Decimal('0.00')
#     grand_ledger_total_payment = Decimal('0.00')
#     grand_ledger_total_received = Decimal('0.00')
#     grand_loanvoucher_total = Decimal('0.00')
#     grand_stock_value = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'boq_list': [],
#             'requisition_list': [],
#             'inventory_list': [],
#             'ledger_list': [],
#             'loanvoucher_list': [],
#             'stock_summary': [],
#             'boq_status_summary': [],
#         }

#         # 1. BOQ
#         boq_items = BOQ.objects.filter(project_name=project)
#         project_block['boq_list'] = boq_items

#         # 2. Requisition
#         requisitions = Requisition.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 requisitions = requisitions.filter(requisition_date__gte=fd)
#             if td:
#                 requisitions = requisitions.filter(requisition_date__lte=td)
#         project_block['requisition_list'] = requisitions

#         # 3. Inventories (Purchase)
#         inventories = Inventories.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(requisition_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(requisition_date__lte=td)
#         project_block['inventory_list'] = inventories

#         # 4. Ledger Entries
#         ledgers = LedgerEntry.objects.filter(project_name=project).exclude(
#             cash_type__cash_type_name='No_Method'
#         )
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledgers = ledgers.order_by('date', 'id')

#         # --- Calculate running balance per ledger entry ---
#         running_balance = Decimal('0.00')
#         ledger_list_with_balance = []
#         for entry in ledgers:
#             running_balance += (entry.credit or Decimal('0.00')) - (entry.debit or Decimal('0.00'))
#             entry.running_balance = running_balance
#             ledger_list_with_balance.append(entry)
#         project_block['ledger_list'] = ledger_list_with_balance

#         # 5. Loan Voucher Entries (Payable / Receivable)
#         loanvouchers = LoanVoucher.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 loanvouchers = loanvouchers.filter(date__gte=fd)
#             if td:
#                 loanvouchers = loanvouchers.filter(date__lte=td)
#         loanvouchers = loanvouchers.order_by('date')
#         project_block['loanvoucher_list'] = loanvouchers

#         # --- Totals ---
#         boq_total = sum((item.amount or Decimal('0.00')) for item in boq_items)
#         requisition_total = sum((item.amount or Decimal('0.00')) for item in requisitions)
#         inventory_total = sum((item.amount or Decimal('0.00')) for item in inventories)
#         ledger_total_payment = sum((item.debit or Decimal('0.00')) for item in ledgers)
#         ledger_total_received = sum((item.credit or Decimal('0.00')) for item in ledgers)
#         loanvoucher_total = sum((item.amount or Decimal('0.00')) for item in loanvouchers)

#         project_block['boq_total'] = boq_total
#         project_block['requisition_total'] = requisition_total
#         project_block['inventory_total'] = inventory_total
#         project_block['ledger_total_payment'] = ledger_total_payment
#         project_block['ledger_total_received'] = ledger_total_received
#         project_block['loanvoucher_total'] = loanvoucher_total

#         # Net ledger position for the project (used as "Profit / Loss" card)
#         project_ledger = ledger_total_received - ledger_total_payment
#         project_block['project_ledger'] = project_ledger
#         project_block['profit_loss'] = project_ledger

#         # Budget vs actual purchase spend (BOQ planned vs Inventory actual)
#         project_block['budget_balance'] = boq_total - inventory_total

#         # --- 6. Stock Summary (aggregated per item, like the "Store & Stock" widget) ---
#         stock_map = OrderedDict()
#         for inv in inventories:
#             key = inv.item_name_id
#             if key not in stock_map:
#                 stock_map[key] = {
#                     'item_name': inv.item_name,
#                     'unit': inv.unit,
#                     'received': 0,
#                     'balance': 0,
#                     'amount': Decimal('0.00'),
#                 }
#             stock_map[key]['received'] += inv.qty
#             stock_map[key]['balance'] += inv.qtysub
#             stock_map[key]['amount'] += (inv.amount or Decimal('0.00'))

#         stock_summary = []
#         stock_value_total = Decimal('0.00')
#         for s in stock_map.values():
#             s['issued'] = s['received'] - s['balance']
#             unit_rate = (s['amount'] / s['received']) if s['received'] else Decimal('0.00')
#             s['stock_value'] = (Decimal(s['balance']) * unit_rate).quantize(Decimal('0.01'))
#             stock_value_total += s['stock_value']
#             stock_summary.append(s)

#         project_block['stock_summary'] = stock_summary
#         project_block['stock_value'] = stock_value_total
#         grand_stock_value += stock_value_total

#         # --- 7. BOQ status-wise breakdown (Completed / Running / Pending / Variation etc.) ---
#         boq_status_map = OrderedDict()
#         for item in boq_items:
#             key = item.status_item or 'Not Set'
#             if key not in boq_status_map:
#                 boq_status_map[key] = {'status': key, 'count': 0, 'amount': Decimal('0.00')}
#             boq_status_map[key]['count'] += 1
#             boq_status_map[key]['amount'] += (item.amount or Decimal('0.00'))
#         boq_status_summary = list(boq_status_map.values())
#         for s in boq_status_summary:
#             s['pct'] = float((s['amount'] / boq_total * 100)) if boq_total else 0
#         project_block['boq_status_summary'] = boq_status_summary
#         project_block['boq_item_count'] = boq_items.count()

#         # --- 8. Stock overview bars (balance as % of total received, per item) ---
#         for s in stock_summary:
#             s['balance_pct'] = float((s['balance'] / s['received'] * 100)) if s['received'] else 0
#         # Top 6 items by stock value for the compact "Stock Overview" panel
#         project_block['stock_overview_top'] = sorted(
#             stock_summary, key=lambda x: x['stock_value'], reverse=True
#         )[:6]

#         # --- 9. Ledger breakdown by Head of Account (drives "Finance Overview" bars) ---
#         head_map = OrderedDict()
#         for entry in ledgers:
#             key = entry.head_id
#             if key not in head_map:
#                 head_map[key] = {'head': entry.head, 'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
#             head_map[key]['debit'] += (entry.debit or Decimal('0.00'))
#             head_map[key]['credit'] += (entry.credit or Decimal('0.00'))
#         head_breakdown = sorted(head_map.values(), key=lambda x: x['debit'], reverse=True)
#         for h in head_breakdown:
#             h['pct'] = float((h['debit'] / ledger_total_payment * 100)) if ledger_total_payment else 0
#         project_block['head_breakdown'] = head_breakdown[:6]

#         # --- 10. Client collection (Customer-type ledger credit entries) ---
#         project_block['client_collection'] = sum(
#             (e.credit or Decimal('0.00')) for e in ledger_list_with_balance if e.type == 'Customer'
#         )

#         # --- 11. Payable / Receivable status-wise breakdown ---
#         loan_status_map = OrderedDict()
#         for loan in loanvouchers:
#             key = loan.loan_status or 'Not Set'
#             if key not in loan_status_map:
#                 loan_status_map[key] = {'status': key, 'count': 0, 'amount': Decimal('0.00')}
#             loan_status_map[key]['count'] += 1
#             loan_status_map[key]['amount'] += (loan.amount or Decimal('0.00'))
#         project_block['loan_status_summary'] = list(loan_status_map.values())

#         # --- 12. Simple counts for the "Purchase Status" panel ---
#         project_block['requisition_count'] = requisitions.count()
#         project_block['inventory_count'] = inventories.count()
#         project_block['ledger_count'] = len(ledger_list_with_balance)
#         project_block['loanvoucher_count'] = loanvouchers.count()

#         # Add to grand totals
#         grand_boq_total += boq_total
#         grand_requisition_total += requisition_total
#         grand_inventory_total += inventory_total
#         grand_ledger_total_payment += ledger_total_payment
#         grand_ledger_total_received += ledger_total_received
#         grand_loanvoucher_total += loanvoucher_total

#         report_data.append(project_block)

#     grand_profit_loss = grand_ledger_total_received - grand_ledger_total_payment
#     grand_budget_balance = grand_boq_total - grand_inventory_total

#     # Convert amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             is_negative = amount < 0
#             amount = abs(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en_IN').title().replace(",", "")
#             words += " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
#             words += " only"
#             if is_negative:
#                 words = "- " + words
#             return words
#         except (ValueError, TypeError):
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'grand_boq_total': grand_boq_total,
#         'grand_requisition_total': grand_requisition_total,
#         'grand_inventory_total': grand_inventory_total,
#         'grand_ledger_total_payment': grand_ledger_total_payment,
#         'grand_ledger_total_received': grand_ledger_total_received,
#         'grand_loanvoucher_total': grand_loanvoucher_total,
#         'grand_stock_value': grand_stock_value,
#         'grand_profit_loss': grand_profit_loss,
#         'grand_budget_balance': grand_budget_balance,
#         'grand_total_amount': grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total,
#         'grand_total_in_words': amount_to_words(
#             grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total
#         ),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'type': type_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'projectreport/project_ledger_manage_pdf.html', context)



from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from num2words import num2words

# NOTE: keep your existing model imports (ProjectFirstLevelName, BOQ, Requisition,
# Inventories, LedgerEntry, LoanVoucher) exactly as they already are in this file.


# --- Fixed colors for known BOQ statuses (matches the dashboard's ring-chart legend) ---
STATUS_COLORS = OrderedDict([
    ('Completed', '#10b981'),   # green
    ('Running',   '#f59e0b'),   # orange
    ('Pending',   '#94a3b8'),   # gray
    ('Variation', '#ef4444'),   # red
])
FALLBACK_COLORS = ['#6366f1', '#ec4899', '#14b8a6', '#8b5cf6', '#2563eb']


def get_status_color(status_name, fallback_index):
    """Return the fixed color for known statuses, otherwise cycle through fallback colors."""
    if status_name in STATUS_COLORS:
        return STATUS_COLORS[status_name]
    return FALLBACK_COLORS[fallback_index % len(FALLBACK_COLORS)]


def build_conic_gradient(segments, value_key='count_pct', base_color='#e2e8f0'):
    """
    Build a CSS conic-gradient() string from a list of dicts, each containing
    'color' and a percentage value under value_key. Automatically fills any
    remainder with base_color so the ring always completes to 100%.
    """
    stops = []
    cum = 0.0
    for seg in segments:
        pct = float(seg.get(value_key) or 0)
        if pct <= 0:
            continue
        start = cum
        cum += pct
        stops.append(f"{seg['color']} {start:.2f}% {min(cum, 100):.2f}%")
    if cum < 100:
        stops.append(f"{base_color} {cum:.2f}% 100%")
    if not stops:
        stops.append(f"{base_color} 0% 100%")
    return "conic-gradient(" + ", ".join(stops) + ")"


def build_single_value_ring(pct, fill_color='#10b981', base_color='#e2e8f0'):
    """Build a conic-gradient ring for a single percentage value (e.g. Overall Progress)."""
    pct = max(0.0, min(100.0, float(pct or 0)))
    return f"conic-gradient({fill_color} 0% {pct:.2f}%, {base_color} {pct:.2f}% 100%)"


@login_required
def project_ledger_manage_pdf(request):
    type_option = request.GET.get('type', 'Project')
    project_id = request.GET.get('project')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Get projects queryset
    if is_valid(project_id):
        projects = ProjectFirstLevelName.objects.filter(id=project_id)
    else:
        projects = ProjectFirstLevelName.objects.all()

    report_data = []

    # Initialize grand totals
    grand_boq_total = Decimal('0.00')
    grand_requisition_total = Decimal('0.00')
    grand_inventory_total = Decimal('0.00')
    grand_ledger_total_payment = Decimal('0.00')
    grand_ledger_total_received = Decimal('0.00')
    grand_loanvoucher_total = Decimal('0.00')
    grand_stock_value = Decimal('0.00')

    for project in projects:
        project_block = {
            'project': project,
            'boq_list': [],
            'requisition_list': [],
            'inventory_list': [],
            'ledger_list': [],
            'loanvoucher_list': [],
            'stock_summary': [],
            'boq_status_summary': [],
        }

        # 1. BOQ
        boq_items = BOQ.objects.filter(project_name=project)
        project_block['boq_list'] = boq_items

        # 2. Requisition
        requisitions = Requisition.objects.filter(project_name=project)
        if transaction_option == 'datewise':
            if fd:
                requisitions = requisitions.filter(requisition_date__gte=fd)
            if td:
                requisitions = requisitions.filter(requisition_date__lte=td)
        project_block['requisition_list'] = requisitions

        # 3. Inventories (Purchase)
        inventories = Inventories.objects.filter(project_name=project)
        if transaction_option == 'datewise':
            if fd:
                inventories = inventories.filter(requisition_date__gte=fd)
            if td:
                inventories = inventories.filter(requisition_date__lte=td)
        project_block['inventory_list'] = inventories

        # 4. Ledger Entries
        ledgers = LedgerEntry.objects.filter(project_name=project).exclude(
            cash_type__cash_type_name='No_Method'
        )
        if transaction_option == 'datewise':
            if fd:
                ledgers = ledgers.filter(date__gte=fd)
            if td:
                ledgers = ledgers.filter(date__lte=td)
        ledgers = ledgers.order_by('date', 'id')

        # --- Calculate running balance per ledger entry ---
        running_balance = Decimal('0.00')
        ledger_list_with_balance = []
        for entry in ledgers:
            running_balance += (entry.credit or Decimal('0.00')) - (entry.debit or Decimal('0.00'))
            entry.running_balance = running_balance
            ledger_list_with_balance.append(entry)
        project_block['ledger_list'] = ledger_list_with_balance

        # 5. Loan Voucher Entries (Payable / Receivable)
        loanvouchers = LoanVoucher.objects.filter(project_name=project)
        if transaction_option == 'datewise':
            if fd:
                loanvouchers = loanvouchers.filter(date__gte=fd)
            if td:
                loanvouchers = loanvouchers.filter(date__lte=td)
        loanvouchers = loanvouchers.order_by('date')
        project_block['loanvoucher_list'] = loanvouchers

        # --- Totals ---
        boq_total = sum((item.amount or Decimal('0.00')) for item in boq_items)
        requisition_total = sum((item.amount or Decimal('0.00')) for item in requisitions)
        inventory_total = sum((item.amount or Decimal('0.00')) for item in inventories)
        ledger_total_payment = sum((item.debit or Decimal('0.00')) for item in ledgers)
        ledger_total_received = sum((item.credit or Decimal('0.00')) for item in ledgers)
        loanvoucher_total = sum((item.amount or Decimal('0.00')) for item in loanvouchers)

        project_block['boq_total'] = boq_total
        project_block['requisition_total'] = requisition_total
        project_block['inventory_total'] = inventory_total
        project_block['ledger_total_payment'] = ledger_total_payment
        project_block['ledger_total_received'] = ledger_total_received
        project_block['loanvoucher_total'] = loanvoucher_total

        # Net ledger position for the project (used as "Profit / Loss" card)
        project_ledger = ledger_total_received - ledger_total_payment
        project_block['project_ledger'] = project_ledger
        project_block['profit_loss'] = project_ledger

        # Budget vs actual purchase spend (BOQ planned vs Inventory actual)
        project_block['budget_balance'] = boq_total - inventory_total

        # --- 6. Stock Summary (aggregated per item, like the "Store & Stock" widget) ---
        stock_map = OrderedDict()
        for inv in inventories:
            key = inv.item_name_id
            if key not in stock_map:
                stock_map[key] = {
                    'item_name': inv.item_name,
                    'unit': inv.unit,
                    'received': 0,
                    'balance': 0,
                    'amount': Decimal('0.00'),
                }
            stock_map[key]['received'] += inv.qty
            stock_map[key]['balance'] += inv.qtysub
            stock_map[key]['amount'] += (inv.amount or Decimal('0.00'))

        stock_summary = []
        stock_value_total = Decimal('0.00')
        for s in stock_map.values():
            s['issued'] = s['received'] - s['balance']
            unit_rate = (s['amount'] / s['received']) if s['received'] else Decimal('0.00')
            s['stock_value'] = (Decimal(s['balance']) * unit_rate).quantize(Decimal('0.01'))
            stock_value_total += s['stock_value']
            stock_summary.append(s)

        project_block['stock_summary'] = stock_summary
        project_block['stock_value'] = stock_value_total
        grand_stock_value += stock_value_total

        # --- 7. BOQ status-wise breakdown (Completed / Running / Pending / Variation etc.) ---
        # Order known statuses first (Completed, Running, Pending, Variation) so the
        # ring-chart legend always lines up the same way as the dashboard, then
        # append any custom/unknown statuses after.
        boq_status_map = OrderedDict()
        for item in boq_items:
            key = item.status_item or 'Not Set'
            if key not in boq_status_map:
                boq_status_map[key] = {'status': key, 'count': 0, 'amount': Decimal('0.00')}
            boq_status_map[key]['count'] += 1
            boq_status_map[key]['amount'] += (item.amount or Decimal('0.00'))

        known_order = list(STATUS_COLORS.keys())
        ordered_keys = [k for k in known_order if k in boq_status_map] + \
                       [k for k in boq_status_map if k not in known_order]

        total_boq_items = boq_items.count()
        boq_status_summary = []
        fallback_idx = 0
        for key in ordered_keys:
            s = boq_status_map[key]
            s['amount_pct'] = float((s['amount'] / boq_total * 100)) if boq_total else 0
            s['count_pct'] = float((s['count'] / total_boq_items * 100)) if total_boq_items else 0
            s['pct'] = s['amount_pct']  # kept for backward compatibility with existing bar markup
            if key in STATUS_COLORS:
                s['color'] = STATUS_COLORS[key]
            else:
                s['color'] = FALLBACK_COLORS[fallback_idx % len(FALLBACK_COLORS)]
                fallback_idx += 1
            boq_status_summary.append(s)

        project_block['boq_status_summary'] = boq_status_summary
        project_block['boq_item_count'] = total_boq_items

        # Ring-chart gradient for the BOQ Progress donut (based on item-count share, like the dashboard)
        project_block['boq_donut_style'] = build_conic_gradient(
            boq_status_summary, value_key='count_pct'
        )

        # Ring-chart gradient for the project's Overall Progress indicator.
        # Prefer the manually maintained project.percentage field; if that hasn't
        # been set (0 / None), fall back to calculating progress from BOQ
        # completion (amount-weighted) so the ring isn't stuck at 0% just
        # because nobody updated the project's percentage field yet.
        COMPLETED_STATUS_WORDS = ('completed', 'approved', 'done', 'finished', 'closed')

        def is_completed_status(status_name):
            return (status_name or '').strip().lower() in COMPLETED_STATUS_WORDS

        manual_pct = float(project.percentage) if getattr(project, 'percentage', None) else 0
        if manual_pct:
            overall_pct = manual_pct
        else:
            completed_amount = sum(
                s['amount'] for s in boq_status_summary if is_completed_status(s['status'])
            )
            if boq_total:
                overall_pct = float(completed_amount / boq_total * 100)
            elif total_boq_items:
                # Fall back to item-count share if amounts are all 0/blank
                completed_count = sum(
                    s['count'] for s in boq_status_summary if is_completed_status(s['status'])
                )
                overall_pct = float(completed_count / total_boq_items * 100)
            else:
                overall_pct = 0
        project_block['overall_pct'] = overall_pct
        project_block['progress_ring_style'] = build_single_value_ring(
            overall_pct, fill_color='#10b981', base_color='#e2e8f0'
        )

        # --- 8. Stock overview bars (balance as % of total received, per item) ---
        for s in stock_summary:
            s['balance_pct'] = float((s['balance'] / s['received'] * 100)) if s['received'] else 0
        # Top 6 items by stock value for the compact "Stock Overview" panel
        project_block['stock_overview_top'] = sorted(
            stock_summary, key=lambda x: x['stock_value'], reverse=True
        )[:6]

        # --- 9. Ledger breakdown by Head of Account (drives "Finance Overview" bars) ---
        head_map = OrderedDict()
        for entry in ledgers:
            key = entry.head_id
            if key not in head_map:
                head_map[key] = {'head': entry.head, 'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
            head_map[key]['debit'] += (entry.debit or Decimal('0.00'))
            head_map[key]['credit'] += (entry.credit or Decimal('0.00'))
        head_breakdown = sorted(head_map.values(), key=lambda x: x['debit'], reverse=True)
        for h in head_breakdown:
            h['pct'] = float((h['debit'] / ledger_total_payment * 100)) if ledger_total_payment else 0
        project_block['head_breakdown'] = head_breakdown[:6]

        # --- 10. Client collection (Customer-type ledger credit entries) ---
        project_block['client_collection'] = sum(
            (e.credit or Decimal('0.00')) for e in ledger_list_with_balance if e.type == 'Customer'
        )

        # --- 11. Payable / Receivable status-wise breakdown ---
        loan_status_map = OrderedDict()
        for loan in loanvouchers:
            key = loan.loan_status or 'Not Set'
            if key not in loan_status_map:
                loan_status_map[key] = {'status': key, 'count': 0, 'amount': Decimal('0.00')}
            loan_status_map[key]['count'] += 1
            loan_status_map[key]['amount'] += (loan.amount or Decimal('0.00'))
        project_block['loan_status_summary'] = list(loan_status_map.values())

        # --- 12. Simple counts for the "Purchase Status" panel ---
        project_block['requisition_count'] = requisitions.count()
        project_block['inventory_count'] = inventories.count()
        project_block['ledger_count'] = len(ledger_list_with_balance)
        project_block['loanvoucher_count'] = loanvouchers.count()

        # Add to grand totals
        grand_boq_total += boq_total
        grand_requisition_total += requisition_total
        grand_inventory_total += inventory_total
        grand_ledger_total_payment += ledger_total_payment
        grand_ledger_total_received += ledger_total_received
        grand_loanvoucher_total += loanvoucher_total

        report_data.append(project_block)

    grand_profit_loss = grand_ledger_total_received - grand_ledger_total_payment
    grand_budget_balance = grand_boq_total - grand_inventory_total

    # Convert amount to words
    def amount_to_words(amount):
        try:
            amount = float(amount)
            is_negative = amount < 0
            amount = abs(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en_IN').title().replace(",", "")
            words += " Taka"
            if fractional_part:
                words += " and " + num2words(fractional_part, lang='en_IN').title() + " Paisa"
            words += " only"
            if is_negative:
                words = "- " + words
            return words
        except (ValueError, TypeError):
            return f"{amount} Taka only"

    context = {
        'report_data': report_data,
        'grand_boq_total': grand_boq_total,
        'grand_requisition_total': grand_requisition_total,
        'grand_inventory_total': grand_inventory_total,
        'grand_ledger_total_payment': grand_ledger_total_payment,
        'grand_ledger_total_received': grand_ledger_total_received,
        'grand_loanvoucher_total': grand_loanvoucher_total,
        'grand_stock_value': grand_stock_value,
        'grand_profit_loss': grand_profit_loss,
        'grand_budget_balance': grand_budget_balance,
        'grand_total_amount': grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total,
        'grand_total_in_words': amount_to_words(
            grand_boq_total + grand_requisition_total + grand_inventory_total + grand_loanvoucher_total
        ),
        'selected_filters': {
            'project': project_id,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
            'type': type_option,
        },
        'print_time': datetime.now(),
    }

    return render(request, 'projectreport/project_ledger_manage_pdf.html', context)



@login_required
def purchase_summary_report(request):
    suppliers = Suppliers.objects.all()
    report_data = []

    for supplier in suppliers:
        inventory_items = Inventories.objects.filter(vendor_name=supplier)
        grouped_by_purch_id = defaultdict(list)
        for item in inventory_items:
            grouped_by_purch_id[item.purch_id].append(item)

        # Create a list of groups with totals
        supplier_groups = []
        for purch_id, items in grouped_by_purch_id.items():
            total = sum(item.amount for item in items)
            supplier_groups.append({
                'purch_id': purch_id,
                'items': items,
                'total': total,
            })

        report_data.append({
            'supplier': supplier,
            'groups': supplier_groups,
        })

    return render(request, 'purchasemanage/purchase_summary_report.html', {
        'report_data': report_data
    })


@login_required
def purchase_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    head = HeadOfAccount.objects.all()
    form = LedgerFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  # <-- clearer naming
    cashTypes = CashType.objects.all()
    
    context = {
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'purchasemanage/purchase_ledger_manage.html', context)




@login_required
def purchase_ledger_report(request):
    project_id = request.GET.get('project')
    vendor_id = request.GET.get('vendor')
    item_id = request.GET.get('item')  
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Start with all inventory entries
    inventories = Inventories.objects.all()

    # Filter by vendor if provided
    if is_valid(vendor_id):
        inventories = inventories.filter(vendor_name_id=vendor_id)

    # Filter by project if provided
    if is_valid(project_id):
        inventories = inventories.filter(project_name_id=project_id)

    # Filter by item if provided
    if is_valid(item_id):
        inventories = inventories.filter(item_name_id=item_id)

    # Filter by date range if transaction option is datewise
    if transaction_option == 'datewise':
        if fd:
            inventories = inventories.filter(requisition_date__gte=fd)
        if td:
            inventories = inventories.filter(requisition_date__lte=td)

    # Prepare report data grouped by vendor
    report_data = []

    # Get distinct vendor ids from filtered inventories
    vendor_ids = inventories.values_list('vendor_name_id', flat=True).distinct()

    for vid in vendor_ids:
        vendor = get_object_or_404(Suppliers, id=vid)
        vendor_inventories = inventories.filter(vendor_name_id=vid)
        total_amount = vendor_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        report_data.append({
            'supplier': vendor,
            'boq_total': total_amount,
            'requisitions': vendor_inventories,
        })

    return render(request, 'purchasemanage/purchase_ledger_report.html', {
        'report_data': report_data,
        'filters': {
            'project': project_id,
            'vendor': vendor_id,
            'item': item_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })


@login_required
def purchase_ledger_manage_pdf(request):
    # GET parameters
    type_option = request.GET.get('type', 'Project')
    project_id = request.GET.get('project')
    vendor_id = request.GET.get('vendor')
    item_id = request.GET.get('item')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except:
            return None

    def get_name(model_class, obj_id, name_field):
        if is_valid(obj_id):
            obj = model_class.objects.filter(id=obj_id).first()
            return getattr(obj, name_field, "All") if obj else "All"
        return "All"

    fd = parse_date(from_date)
    td = parse_date(to_date)

    base_queryset = Inventories.objects.all()

    if is_valid(project_id):
        base_queryset = base_queryset.filter(project_name_id=project_id)
    if is_valid(vendor_id):
        base_queryset = base_queryset.filter(vendor_name_id=vendor_id)
    if is_valid(item_id):
        base_queryset = base_queryset.filter(item_name_id=item_id)

    if transaction_option == 'datewise':
        if fd:
            base_queryset = base_queryset.filter(purch_date__gte=fd)
        if td:
            base_queryset = base_queryset.filter(purch_date__lte=td)

    report_data = []

    def generate_ledger(label, entries):
        # Calculate total amount for group
        boq_total = entries.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Order entries for display
        ordered_entries = entries.order_by('requisition_date', 'id')

        running_balance = Decimal('0.00')
        ledger_entries = []
        for entry in ordered_entries:
            received = entry.amount or Decimal('0.00')
            payment = Decimal('0.00')  # Adjust if you have payments

            running_balance += (received - payment)

            ledger_entries.append({
                'date': entry.requisition_date,
                'type': 'Requisition',
                'description': entry.remark or '',
                'chq_rec_no': f"Requi-{entry.purch_id}",
                'payment': payment,
                'received': received,
                'qty': entry.qty,
                'rate': (entry.amount / entry.qty) if entry.qty else Decimal('0.00'),
                'head_name': getattr(entry.item_name, 'head_requi_name', ''),
                'carrier': getattr(entry.employee_name, 'employee_name', ''),
                'balance': running_balance,
            })

        return {
            'group_label': label,
            'boq_total': boq_total,
            'ledger_entries': ledger_entries,
        }

    if type_option == "Vendor":
        vendors = Suppliers.objects.filter(id=vendor_id) if is_valid(vendor_id) else Suppliers.objects.all()
        for vendor in vendors:
            related_projects = base_queryset.filter(vendor_name=vendor).values_list('project_name', flat=True).distinct()
            for proj_id in related_projects:
                project = ProjectFirstLevelName.objects.filter(id=proj_id).first()
                if not project:
                    continue
                label = f"{vendor.supplier_name} - {project.project_first_name}"
                entries = base_queryset.filter(vendor_name=vendor, project_name=project)
                if entries.exists():
                    report_data.append(generate_ledger(label, entries))

    elif type_option == "Project":
        projects = ProjectFirstLevelName.objects.filter(id=project_id) if is_valid(project_id) else ProjectFirstLevelName.objects.all()
        for project in projects:
            related_vendors = base_queryset.filter(project_name=project).values_list('vendor_name', flat=True).distinct()
            for vend_id in related_vendors:
                vendor = Suppliers.objects.filter(id=vend_id).first()
                if not vendor:
                    continue
                label = f"{project.project_first_name} - {vendor.supplier_name}"
                entries = base_queryset.filter(project_name=project, vendor_name=vendor)
                if entries.exists():
                    report_data.append(generate_ledger(label, entries))

    elif type_option == "Item":
        items = HeadOfRequisition.objects.filter(id=item_id) if is_valid(item_id) else HeadOfRequisition.objects.all()
        for item in items:
            related_entries = base_queryset.filter(item_name=item)
            grouped_pairs = related_entries.values('project_name', 'vendor_name').distinct()
            for pair in grouped_pairs:
                project = ProjectFirstLevelName.objects.filter(id=pair['project_name']).first()
                vendor = Suppliers.objects.filter(id=pair['vendor_name']).first()
                if not project or not vendor:
                    continue
                label = f"{item.head_requi_name} - {project.project_first_name} - {vendor.supplier_name}"
                entries = related_entries.filter(project_name=project, vendor_name=vendor)
                if entries.exists():
                    report_data.append(generate_ledger(label, entries))

    total_boq = sum(x['boq_total'] for x in report_data)
    final_balance = total_boq

    def amount_to_words(amount):
        try:
            amount = Decimal(amount)
            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))
            words = num2words(integer_part, lang='en_IN').replace(',', '').capitalize()
            result = f"{words} Taka"
            if fractional_part > 0:
                paisa_words = num2words(fractional_part, lang='en_IN').replace(',', '')
                result += f" and {paisa_words} Paisa"
            return result + " only"
        except:
            return f"{amount} Taka only"

    context = {
        'report_data': report_data,
        'total_boq': total_boq,
        'total_debit': Decimal('0.00'),
        'final_balance': final_balance,
        'balance_in_words': amount_to_words(final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'project': get_name(ProjectFirstLevelName, project_id, 'project_first_name'),
            'vendor': get_name(Suppliers, vendor_id, 'supplier_name'),
            'item': get_name(HeadOfRequisition, item_id, 'head_requi_name'),
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
            'type': type_option,
        }
    }

    return render(request, 'purchasemanage/purchase_ledger_manage_pdf.html', context)


   
@login_required
def capital_account_list(request):
    accounts = CapitalAccount.objects.select_related('head_of_account')
    return render(request, 'capital_accounts/account_head_list.html', {'accounts': accounts})


@login_required
def capital_account_create(request):
    if request.method == 'POST':
        form = CapitalAccountForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('capital_account_list')
    else:
        form = CapitalAccountForm()
    return render(request, 'capital_accounts/account_head_form.html', {'form': form, 'title': 'Add Capital Account'})


@login_required
def capital_account_edit(request, pk):
    account = get_object_or_404(CapitalAccount, pk=pk)
    if request.method == 'POST':
        form = CapitalAccountForm(request.POST, request.FILES, instance=account)
        if form.is_valid():
            form.save()
            return redirect('capital_account_list')
    else:
        form = CapitalAccountForm(instance=account)
    return render(request, 'capital_accounts/account_head_form.html', {'form': form, 'title': 'Edit Capital Account'})


@login_required
def capital_account_delete(request, pk):
    account = get_object_or_404(CapitalAccount, pk=pk)
    log_deleted_data(account, request.user)
    account.delete()
    return redirect('capital_account_list')
    
    


## ----- New code- General Report ---

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

# Import your models
from .models import LedgerEntry, CashType, ProjectFirstLevelName, HeadOfAccount

@login_required
def ledger_manage(request):
    # Initial queryset
    ledger_entries = LedgerEntry.objects.all()

    # Filter by Head of Account if selected
    head_id = request.GET.get('head')
    if head_id:
        ledger_entries = ledger_entries.filter(head_id=head_id)

    # Filter by Vendor/Contructor/Bank (type)
    type_id = request.GET.get('cash_type_name')
    if type_id:
        ledger_entries = ledger_entries.filter(
            Q(vendor_id=type_id) |
            Q(contructor_id=type_id) |
            Q(bankName_id=type_id)
        )

    # Filter by project if selected
    project_id = request.GET.get('project')
    if project_id:
        ledger_entries = ledger_entries.filter(project_name_id=project_id)

    # Prepare dropdown options for Head, CashType and Project based on filtered ledger_entries
    head_ids = ledger_entries.exclude(head__isnull=True).values_list('head', flat=True).distinct()
    project_ids = ledger_entries.exclude(project_name__isnull=True).values_list('project_name', flat=True).distinct()

    # Collect all vendor, contructor, bank ids
    vendor_ids = ledger_entries.exclude(vendor_id__isnull=True).values_list('vendor_id', flat=True)
    contructor_ids = ledger_entries.exclude(contructor_id__isnull=True).values_list('contructor_id', flat=True)
    bank_ids = ledger_entries.exclude(bankName_id__isnull=True).values_list('bankName_id', flat=True)

    used_cash_ids = set(vendor_ids) | set(contructor_ids) | set(bank_ids)
    cashTypes = CashType.objects.filter(id__in=used_cash_ids)

    heads = HeadOfAccount.objects.filter(id__in=head_ids)
    projects = ProjectFirstLevelName.objects.filter(id__in=project_ids)

    context = {
        'heads': heads,
        'cashTypes': cashTypes,
        'projectNames': projects,
        'today': date.today(),
    }

    return render(request, 'reportmanage/ledger_manage.html', context)






### --  Genarel Ledger --- New Code---
@login_required
def get_types_by_head(request, head_id):
    ledger_entries = LedgerEntry.objects.filter(head_id=head_id)

    unique_ids = set()
    data = []

    for entry in ledger_entries:
        #print(entry.vendor)
        if entry.vendor and entry.vendor.id not in unique_ids:            
            unique_ids.add(entry.vendor.id)
            data.append({'id': entry.vendor.id, 'type': entry.type, 'name': entry.vendor.supplier_name})

        if entry.contructor and entry.contructor.id not in unique_ids:            
            unique_ids.add(entry.contructor.id)
            data.append({'id': entry.contructor.id,'type': entry.type, 'name': entry.contructor.supervisor_name})

        if entry.bankName and entry.bankName.id not in unique_ids:            
            unique_ids.add(entry.bankName.id)
            data.append({'id': entry.bankName.id, 'type': entry.type, 'name': entry.bankName.cash_type_name}) 

        if entry.exp_name and entry.exp_name.id not in unique_ids:           
            unique_ids.add(entry.exp_name.id)
            data.append({'id': entry.exp_name.id, 'type': entry.type, 'name': entry.exp_name.head_exp_name})
        
        if entry.capi_name and entry.capi_name.id not in unique_ids:          
            unique_ids.add(entry.capi_name.id)
            data.append({'id': entry.capi_name.id, 'type': entry.type, 'name': entry.capi_name.person_name}) 
        
        # if entry.capi_name and entry.capi_name.id not in unique_ids:
        #     if entry.capi_name.head_of_account.head_name == 'Capital Account':
        #         unique_ids.add(entry.capi_name.id)
        #         data.append({
        #             'id': entry.capi_name.id,
        #             'type': 'Capital',  # you can keep type explicitly
        #             'name': entry.capi_name.person_name
        #         })
            
        if entry.invest_name and entry.invest_name.id not in unique_ids:          
            unique_ids.add(entry.invest_name.id)
            data.append({'id': entry.invest_name.id, 'type': entry.type, 'name': entry.invest_name.person_name}) 
        
        # Investment
        # if entry.invest_name and entry.invest_name.id not in unique_ids:
        #     if entry.invest_name.head_of_account.head_name == 'Investment Account':
        #         unique_ids.add(entry.invest_name.id)
        #         data.append({
        #             'id': entry.invest_name.id,
        #             'type': 'Investment',  # explicitly mark type
        #             'name': entry.invest_name.person_name
        #         })

    return JsonResponse(data, safe=False)
    

@login_required
def get_projects_by_head_cash(request, head_id, cash_type_id):

    entries = LedgerEntry.objects.filter(head_id=head_id).filter(
        Q(vendor_id=cash_type_id) | Q(contructor_id=cash_type_id) | Q(bankName_id=cash_type_id) | Q(capi_name_id=cash_type_id)| Q(exp_name_id=cash_type_id) | Q(invest_name_id=cash_type_id)
    )   
    project_ids = entries.values_list('project_name', flat=True).distinct()
    projects = ProjectFirstLevelName.objects.filter(id__in=project_ids)

    data = [{'id': p.id, 'name': p.project_first_name} for p in projects]
    return JsonResponse(data, safe=False)

  


@login_required
def ledger_report(request):
    head_id = request.GET.get('head')
    entity_id = request.GET.get('cash_type_name')  
    project_id = request.GET.get('project')
    type_value = request.GET.get('type')  # Default: Vendor
    transaction_option = request.GET.get('transaction', 'datewise')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    def is_valid(val):
        return val not in [None, '', '0']

    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # -------------------------
    # Filter Ledger Entries
    # -------------------------
    ledger_entries = LedgerEntry.objects.filter(type=type_value)

    if is_valid(project_id):
        ledger_entries = ledger_entries.filter(project_name_id=project_id)

    if is_valid(head_id):
        ledger_entries = ledger_entries.filter(head_id=head_id)

    if is_valid(entity_id):
        if type_value == 'Vendor':
            ledger_entries = ledger_entries.filter(vendor_id=entity_id)
        elif type_value == 'Contractor':
            ledger_entries = ledger_entries.filter(contructor_id=entity_id)
        elif type_value == 'Capital':
            ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
        elif type_value == 'Customer':
            ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
        elif type_value == 'Bank':
            ledger_entries = ledger_entries.filter(bankName_id=entity_id)
        elif type_value == 'Expense':
            ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

    if transaction_option == 'datewise':
        if fd:
            ledger_entries = ledger_entries.filter(date__gte=fd)
        if td:
            ledger_entries = ledger_entries.filter(date__lte=td)

    ledger_entries = ledger_entries.order_by('date', 'id')

    # -------------------------
    # Prepare Combined Data
    # -------------------------
    entry_data = []
    balance = Decimal('0.00')

    for entry in ledger_entries:
        if entry.type == 'Vendor' and entry.vendor:
            name = entry.vendor.supplier_name

        elif entry.type == 'Contractor' and entry.contractor:
            name = entry.contructor.supervisor_name

        elif entry.type == 'Capital' and entry.capi_name:
            # CapitalAccount -> person_name (valid)
            name = entry.capi_name.person_name

        elif entry.type == 'Customer' and entry.customer_name:
            name = entry.customer_name.customer_name

        elif entry.type == 'Bank' and entry.bankName:
            name = entry.bankName.cash_type_name

        elif entry.type == 'Expense' and entry.exp_name:
            # HeadOfExpense -> head_exp_name (valid)
            name = entry.exp_name.head_exp_name

        else:
            name = 'N/A'

        print(name)


        balance += entry.credit - entry.debit

        entry_data.append({
            'source': 'ledger',
            'project_name': entry.project_name,
            'head': entry.head.head_name if entry.head else '',
            'name': name,
            'date': entry.date,
            'description': entry.description,
            'debit': entry.debit,
            'credit': entry.credit,
            'balance': balance,
        })

    # -------------------------
    # If Vendor: Load Inventory Entries
    # -------------------------
    if type_value == 'Vendor':
        inventories = Inventories.objects.all()

        if is_valid(entity_id):
            inventories = inventories.filter(vendor_name_id=entity_id)
        if is_valid(project_id):
            inventories = inventories.filter(project_name_id=project_id)
        if transaction_option == 'datewise':
            if fd:
                inventories = inventories.filter(purch_date__gte=fd)
            if td:
                inventories = inventories.filter(purch_date__lte=td)

        for inv in inventories:
            entry_data.append({
                'source': 'inventory',
                'project_name': inv.project_name,
                'head': inv.item_name.head_requi_name if inv.item_name else '',
                'name': inv.vendor_name.supplier_name if inv.vendor_name else '',
                'date': inv.requisition_date,
                'description': inv.remark,
                'debit': Decimal('0.00'),
                'credit': inv.amount,
                'balance': '',
            })

    # -------------------------
    # Final Sorting
    # -------------------------
    entry_data.sort(key=lambda x: (x['date'] or datetime.min.date()))

    return render(request, 'reportmanage/ledger_report.html', {
        'entry_data': entry_data,
        'projectNames': ProjectFirstLevelName.objects.all(),
        'heads': HeadOfAccount.objects.all(),
        'vendors': Suppliers.objects.all(),           # optional dropdown
        'supervisors': SiteSupervisor.objects.all(),  # optional dropdown
        'capital_accounts': CapitalAccount.objects.all(),  # optional dropdown
        'selected_filters': {
            'type': type_value,
            'head': head_id,
            'cash_type_name': entity_id,
            'project': project_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })





# @login_required
# def ledger_manage_pdf(request):
#     head_id = request.GET.get('head')
#     entity_id = request.GET.get('cash_type_name')  
#     project_id = request.GET.get('project')
#     type_value = request.GET.get('type', 'Vendor')
#     transaction_option = request.GET.get('transaction', 'datewise')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     def is_valid(val):
#         return val not in [None, '', '0']

#     def parse_date(s):
#         try:
#             return datetime.strptime(s, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Filter Ledger Entries
#     ledger_entries = LedgerEntry.objects.filter(type=type_value)
#     if is_valid(project_id):
#         ledger_entries = ledger_entries.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         ledger_entries = ledger_entries.filter(head_id=head_id)
#     if is_valid(entity_id):
#         if type_value == 'Vendor':
#             ledger_entries = ledger_entries.filter(vendor_id=entity_id)
#         elif type_value == 'Contructor':
#             ledger_entries = ledger_entries.filter(contructor_id=entity_id)
#         elif type_value == 'Capital':
#             ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
#         elif type_value == 'Customer':
#             ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
#         elif type_value == 'Bank':
#             ledger_entries = ledger_entries.filter(bankName_id=entity_id)
#         elif type_value == 'Expense':
#             ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

#     if transaction_option == 'datewise':
#         if fd:
#             ledger_entries = ledger_entries.filter(date__gte=fd)
#         if td:
#             ledger_entries = ledger_entries.filter(date__lte=td)

#     ledger_entries = ledger_entries.order_by('date', 'id')

#     # Combine ledger, inventory, and bill requisitions into one list
#     raw_entries = []
#     for entry in ledger_entries:
#         if entry.type == 'Vendor' and entry.vendor:
#             name = entry.vendor.supplier_name
#         elif entry.type == 'Contructor' and entry.contructor:
#             name = entry.contructor.supervisor_name
#         elif entry.type == 'Capital' and entry.capi_name:
#             name = entry.capi_name.person_name
#         elif entry.type == 'Customer' and entry.customer_name:
#             name = entry.customer_name.customer_name
#         elif entry.type == 'Bank' and entry.bankName:
#             name = entry.bankName.cash_type_name
#         elif entry.type == 'Expense' and entry.exp_name:
#             name = entry.exp_name.head_exp_name
#         else:
#             name = 'N/A'

#         raw_entries.append({
#             'source': 'ledger',
#             'project_name': entry.project_name,
#             'head': entry.head.head_name if entry.head else '',
#             'name': name,
#             'date': entry.date,
#             'description': entry.description,
#             'cheque_number': getattr(entry, 'cheque_number', ''),
#             'payment': entry.debit,
#             'received': entry.credit,
#         })

#     # Add inventories (Vendor only)
#     if type_value == 'Vendor':
#         inventories = Inventories.objects.all()
#         if is_valid(entity_id):
#             inventories = inventories.filter(vendor_name_id=entity_id)
#         if is_valid(project_id):
#             inventories = inventories.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(purch_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(purch_date__lte=td)

#         for inv in inventories:
#             raw_entries.append({
#                 'source': 'inventory',
#                 'project_name': inv.project_name,
#                 'head': inv.item_name.head_requi_name if inv.item_name else '',
#                 'name': inv.vendor_name.supplier_name if inv.vendor_name else '',
#                 'date': inv.purch_date,
#                 'description': inv.remark,
#                 'cheque_number': '',
#                 'payment': Decimal('0.00'),
#                 'received': inv.amount,
#             })

#     # Add BillRequisition entries
#     bill_reqs = BillRequisition.objects.filter(approv_status="approved")
#     if is_valid(project_id):
#         bill_reqs = bill_reqs.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         bill_reqs = bill_reqs.filter(head_of_account_id=head_id)
        
#     if is_valid(entity_id):
#         bill_reqs = bill_reqs.filter(vendor_name=entity_id)
    
#     # if is_valid(type_value):
#     #     bill_reqs = bill_reqs.filter(type=type_value)
    
#     if transaction_option == 'datewise':
#         if fd:
#             bill_reqs = bill_reqs.filter(requisition_date__gte=fd)
#         if td:
#             bill_reqs = bill_reqs.filter(requisition_date__lte=td)

#     for breq in bill_reqs:
#         raw_entries.append({
#             'source': 'bill_requisition',
#             'project_name': breq.project_name,
#             'head': breq.head_of_account.head_name if breq.head_of_account else '',
#             'name': breq.vendor_name if breq.vendor_name else '',
#             'date': breq.requisition_date,
#             'description': breq.remark,
#             'cheque_number': breq.mr_or_bill_no,
#             'payment': Decimal('0.00'),
#             'received': breq.amount,
#         })

#     # Sort all combined entries
#     raw_entries.sort(key=lambda x: (x['date'], x.get('project_name').id if x.get('project_name') else 0))

#     # Balance calculation
#     balance = Decimal('0.00')
#     total_payment = Decimal('0.00')
#     total_received = Decimal('0.00')
#     entry_data = []

#     for entry in raw_entries:
#         payment = entry['payment']
#         received = entry['received']
#         balance += received - payment
#         total_payment += payment
#         total_received += received
#         entry['balance'] = balance
#         entry_data.append(entry)

#     return render(request, 'reportmanage/ledger_report_print.html', {
#         'entry_data': entry_data,
#         'total_payment': total_payment,
#         'total_received': total_received,
#         'final_balance': balance,
#         'print_time': datetime.now(),
#         'projectNames': ProjectFirstLevelName.objects.all(),
#         'heads': HeadOfAccount.objects.all(),
#         'vendors': Suppliers.objects.all(),
#         'supervisors': SiteSupervisor.objects.all(),
#         'capital_accounts': CapitalAccount.objects.all(),
#         'selected_filters': {
#             'type': type_value,
#             'head': head_id,
#             'cash_type_name': entity_id,
#             'project': project_id,
#             'project_name': ProjectFirstLevelName.objects.get(id=project_id).project_first_name if is_valid(project_id) else 'All',
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     })






# @login_required
# def ledger_manage_pdf(request):
#     head_id = request.GET.get('head')
#     entity_id = request.GET.get('cash_type_name')  
#     project_id = request.GET.get('project')
#     type_value = request.GET.get('type', 'Vendor')
#     transaction_option = request.GET.get('transaction', 'datewise')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     def is_valid(val):
#         return val not in [None, '', '0']

#     def parse_date(s):
#         try:
#             return datetime.strptime(s, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Filter Ledger Entries
#     ledger_entries = LedgerEntry.objects.filter(type=type_value)
#     if is_valid(project_id):
#         ledger_entries = ledger_entries.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         ledger_entries = ledger_entries.filter(head_id=head_id)
#     if is_valid(entity_id):
#         if type_value == 'Vendor':
#             ledger_entries = ledger_entries.filter(vendor_id=entity_id)
#         elif type_value == 'Contructor':
#             ledger_entries = ledger_entries.filter(contructor_id=entity_id)
#         elif type_value == 'Capital':
#             ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
#         elif type_value == 'Customer':
#             ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
#         elif type_value == 'Bank':
#             ledger_entries = ledger_entries.filter(bankName_id=entity_id)
#         elif type_value == 'Expense':
#             ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

#     if transaction_option == 'datewise':
#         if fd:
#             ledger_entries = ledger_entries.filter(date__gte=fd)
#         if td:
#             ledger_entries = ledger_entries.filter(date__lte=td)

#     ledger_entries = ledger_entries.order_by('date', 'id')

#     # Combine ledger, inventory, and bill requisitions into one list
#     raw_entries = []
#     for entry in ledger_entries:
#         if entry.type == 'Vendor' and entry.vendor:
#             name = entry.vendor.supplier_name
#         elif entry.type == 'Contructor' and entry.contructor:
#             name = entry.contructor.supervisor_name
#         elif entry.type == 'Capital' and entry.capi_name:
#             name = entry.capi_name.person_name
#         elif entry.type == 'Customer' and entry.customer_name:
#             name = entry.customer_name.customer_name
#         elif entry.type == 'Bank' and entry.bankName:
#             name = entry.bankName.cash_type_name
#         elif entry.type == 'Expense' and entry.exp_name:
#             name = entry.exp_name.head_exp_name
#         else:
#             name = 'N/A'

#         raw_entries.append({
#             'source': 'ledger',
#             'project_name': entry.project_name,
#             'head': entry.head.head_name if entry.head else '',
#             'name': name,
#             'date': entry.date,
#             'description': entry.description,
#             'cheque_number': getattr(entry, 'cheque_number', ''),
#             'payment': entry.debit,
#             'received': entry.credit,
#         })

#     # Add inventories (Vendor only)
#     if type_value == 'Vendor':
#         inventories = Inventories.objects.all()
#         if is_valid(entity_id):
#             inventories = inventories.filter(vendor_name_id=entity_id)
#         if is_valid(project_id):
#             inventories = inventories.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(purch_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(purch_date__lte=td)

#         for inv in inventories:
#             raw_entries.append({
#                 'source': 'inventory',
#                 'project_name': inv.project_name,
#                 'head': inv.item_name.head_requi_name if inv.item_name else '',
#                 'name': inv.vendor_name.supplier_name if inv.vendor_name else '',
#                 'date': inv.purch_date,
#                 'description': inv.remark,
#                 'cheque_number': '',
#                 'payment': Decimal('0.00'),
#                 'received': inv.amount,
#             })

#     # Add BillRequisition entries
#     bill_reqs = BillRequisition.objects.filter(approv_status="approved")
#     if is_valid(project_id):
#         bill_reqs = bill_reqs.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         bill_reqs = bill_reqs.filter(head_of_account_id=head_id)
        
#     if is_valid(entity_id):
#         bill_reqs = bill_reqs.filter(vendor_name=entity_id)
    
#     # if is_valid(type_value):
#     #     bill_reqs = bill_reqs.filter(type=type_value)
    
#     if transaction_option == 'datewise':
#         if fd:
#             bill_reqs = bill_reqs.filter(requisition_date__gte=fd)
#         if td:
#             bill_reqs = bill_reqs.filter(requisition_date__lte=td)

#     for breq in bill_reqs:
#         raw_entries.append({
#             'source': 'bill_requisition',
#             'project_name': breq.project_name,
#             'head': breq.head_of_account.head_name if breq.head_of_account else '',
#             'name': breq.vendor_name if breq.vendor_name else '',
#             'date': breq.requisition_date,
#             'description': breq.remark,
#             'cheque_number': breq.mr_or_bill_no,
#             'payment': Decimal('0.00'),
#             'received': breq.amount,
#         })
    
    
#     # Add PropertySales entries when Expense is selected
#     if type_value == 'Expense' and entity_id:
#         try:
#             entity_id_int = int(entity_id)
#         except ValueError:
#             entity_id_int = None
    
#         if entity_id_int:
#             sales_qs = PropertySales.objects.filter(donaton_name_id=entity_id_int)
    
#             if transaction_option == 'datewise':
#                 if fd:
#                     sales_qs = sales_qs.filter(sales_date__gte=fd)
#                 if td:
#                     sales_qs = sales_qs.filter(sales_date__lte=td)
    
#             # Debug: check how many records are returned
#             print("PropertySales entries count:", sales_qs.count())
    
#             for sale in sales_qs:
#                 raw_entries.append({
#                     'source': 'property_sales',
#                     'project_name': sale.project_name,
#                     'head': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'name': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'date': sale.sales_date,
#                     'description': sale.details,
#                     'cheque_number': '',
#                     'payment': Decimal('0.00'),
#                     'received': sale.lilahetalah_amount,
#                 })


#     # Sort all combined entries
#     raw_entries.sort(key=lambda x: (x['date'], x.get('project_name').id if x.get('project_name') else 0))

#     # Balance calculation
#     balance = Decimal('0.00')
#     total_payment = Decimal('0.00')
#     total_received = Decimal('0.00')
#     entry_data = []

#     for entry in raw_entries:
#         payment = entry['payment']
#         received = entry['received']
#         balance += received - payment
#         total_payment += payment
#         total_received += received
#         entry['balance'] = balance
#         entry_data.append(entry)

#     return render(request, 'reportmanage/ledger_report_print.html', {
#         'entry_data': entry_data,
#         'total_payment': total_payment,
#         'total_received': total_received,
#         'final_balance': balance,
#         'print_time': datetime.now(),
#         'projectNames': ProjectFirstLevelName.objects.all(),
#         'heads': HeadOfAccount.objects.all(),
#         'vendors': Suppliers.objects.all(),
#         'supervisors': SiteSupervisor.objects.all(),
#         'capital_accounts': CapitalAccount.objects.all(),
#         'selected_filters': {
#             'type': type_value,
#             'head': head_id,
#             'cash_type_name': entity_id,
#             'project': project_id,
#             'project_name': ProjectFirstLevelName.objects.get(id=project_id).project_first_name if is_valid(project_id) else 'All',
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     })
    

# from django.db.models import Sum
# @login_required
# def ledger_manage_pdf(request):
#     head_id = request.GET.get('head')
#     entity_id = request.GET.get('cash_type_name')  
#     project_id = request.GET.get('project')
#     type_value = request.GET.get('type', 'Vendor')
#     transaction_option = request.GET.get('transaction', 'datewise')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     def is_valid(val):
#         return val not in [None, '', '0']

#     def parse_date(s):
#         try:
#             return datetime.strptime(s, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Filter Ledger Entries
#     ledger_entries = LedgerEntry.objects.filter(type=type_value)
#     if is_valid(project_id):
#         ledger_entries = ledger_entries.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         ledger_entries = ledger_entries.filter(head_id=head_id)
#     if is_valid(entity_id):
#         if type_value == 'Vendor':
#             ledger_entries = ledger_entries.filter(vendor_id=entity_id)
#         elif type_value == 'Contructor':
#             ledger_entries = ledger_entries.filter(contructor_id=entity_id)
#         elif type_value == 'Capital':
#             ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
#         elif type_value == 'Customer':
#             ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
#         elif type_value == 'Bank':
#             ledger_entries = ledger_entries.filter(bankName_id=entity_id)
#         elif type_value == 'Expense':
#             ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

#     if transaction_option == 'datewise':
#         if fd:
#             ledger_entries = ledger_entries.filter(date__gte=fd)
#         if td:
#             ledger_entries = ledger_entries.filter(date__lte=td)

#     ledger_entries = ledger_entries.order_by('date', 'id')

#     # Combine ledger, inventory, and bill requisitions into one list
#     raw_entries = []
#     for entry in ledger_entries:
#         if entry.type == 'Vendor' and entry.vendor:
#             name = entry.vendor.supplier_name
#         elif entry.type == 'Contructor' and entry.contructor:
#             name = entry.contructor.supervisor_name
#         elif entry.type == 'Capital' and entry.capi_name:
#             name = entry.capi_name.person_name
#         elif entry.type == 'Customer' and entry.customer_name:
#             name = entry.customer_name.customer_name
#         elif entry.type == 'Bank' and entry.bankName:
#             name = entry.bankName.cash_type_name
#         elif entry.type == 'Expense' and entry.exp_name:
#             name = entry.exp_name.head_exp_name
#         else:
#             name = 'N/A'

#         raw_entries.append({
#             'source': 'ledger',
#             'project_name': entry.project_name,
#             'head': entry.head.head_name if entry.head else '',
#             'name': name,
#             'date': entry.date,
#             'description': entry.description,
#             'cheque_number': getattr(entry, 'cheque_number', ''),
#             'payment': entry.debit,
#             'received': entry.credit,
#         })

#     # Add inventories (Vendor only)
#     if type_value == 'Vendor':
#         inventories = Inventories.objects.all()
#         if is_valid(entity_id):
#             inventories = inventories.filter(vendor_name_id=entity_id)
#         if is_valid(project_id):
#             inventories = inventories.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(purch_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(purch_date__lte=td)

#         for inv in inventories:
#             raw_entries.append({
#                 'source': 'inventory',
#                 'project_name': inv.project_name,
#                 'head': inv.item_name.head_requi_name if inv.item_name else '',
#                 'name': inv.vendor_name.supplier_name if inv.vendor_name else '',
#                 'date': inv.purch_date,
#                 'description': inv.remark,
#                 'cheque_number': '',
#                 'payment': Decimal('0.00'),
#                 'received': inv.amount,
#             })
    

#     # Add BillRequisition entries
#     bill_reqs = BillRequisition.objects.filter(approv_status="approved")
#     if is_valid(project_id):
#         bill_reqs = bill_reqs.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         bill_reqs = bill_reqs.filter(head_of_account_id=head_id)
        
#     if is_valid(entity_id):
#         bill_reqs = bill_reqs.filter(vendor_name=entity_id)
    
#     # if is_valid(type_value):
#     #     bill_reqs = bill_reqs.filter(type=type_value)
    
#     if transaction_option == 'datewise':
#         if fd:
#             bill_reqs = bill_reqs.filter(requisition_date__gte=fd)
#         if td:
#             bill_reqs = bill_reqs.filter(requisition_date__lte=td)

#     for breq in bill_reqs:
#         raw_entries.append({
#             'source': 'bill_requisition',
#             'project_name': breq.project_name,
#             'head': breq.head_of_account.head_name if breq.head_of_account else '',
#             'name': breq.vendor_name if breq.vendor_name else '',
#             'date': breq.requisition_date,
#             'description': breq.remark,
#             'cheque_number': breq.mr_or_bill_no,
#             'payment': Decimal('0.00'),
#             'received': breq.amount,
#         })
    
    
#     # Add PropertySales entries when Expense is selected
#     if type_value == 'Expense' and entity_id:
#         try:
#             entity_id_int = int(entity_id)
#         except ValueError:
#             entity_id_int = None
    
#         if entity_id_int:
#             sales_qs = PropertySales.objects.filter(donaton_name_id=entity_id_int)
    
#             if transaction_option == 'datewise':
#                 if fd:
#                     sales_qs = sales_qs.filter(sales_date__gte=fd)
#                 if td:
#                     sales_qs = sales_qs.filter(sales_date__lte=td)
    
#             # Debug: check how many records are returned
#             print("PropertySales entries count:", sales_qs.count())
    
#             for sale in sales_qs:
#                 raw_entries.append({
#                     'source': 'property_sales',
#                     'project_name': sale.project_name,
#                     'head': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'name': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'date': sale.sales_date,
#                     'description': sale.details,
#                     'cheque_number': '',
#                     'payment': Decimal('0.00'),
#                     'received': sale.lilahetalah_amount,
#                 })


#     # Sort all combined entries
#     raw_entries.sort(key=lambda x: (x['date'], x.get('project_name').id if x.get('project_name') else 0))

#     # Balance calculation
#     balance = Decimal('0.00')
#     total_payment = Decimal('0.00')
#     total_received = Decimal('0.00')
#     entry_data = []

#     for entry in raw_entries:
#         payment = entry['payment']
#         received = entry['received']
#         balance += received - payment
#         total_payment += payment
#         total_received += received
#         entry['balance'] = balance
#         entry_data.append(entry)

#     return render(request, 'reportmanage/ledger_report_print.html', {
#         'entry_data': entry_data,
#         'total_payment': total_payment,
#         'total_received': total_received,
#         'final_balance': balance,
#         'print_time': datetime.now(),
#         'projectNames': ProjectFirstLevelName.objects.all(),
#         'heads': HeadOfAccount.objects.all(),
#         'vendors': Suppliers.objects.all(),
#         'supervisors': SiteSupervisor.objects.all(),
#         'capital_accounts': CapitalAccount.objects.all(),
#         'selected_filters': {
#             'type': type_value,
#             'head': head_id,
#             'cash_type_name': entity_id,
#             'project': project_id,
#             'project_name': ProjectFirstLevelName.objects.get(id=project_id).project_first_name if is_valid(project_id) else 'All',
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     })
    

from django.db.models import Sum
@login_required
def ledger_manage_pdf(request):
    head_id = request.GET.get('head')
    entity_id = request.GET.get('cash_type_name')  
    project_id = request.GET.get('project')
    type_value = request.GET.get('type', 'Vendor')
    transaction_option = request.GET.get('transaction', 'datewise')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    def is_valid(val):
        return val not in [None, '', '0']

    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Filter Ledger Entries
    ledger_entries = LedgerEntry.objects.filter(type=type_value)
    if is_valid(project_id):
        ledger_entries = ledger_entries.filter(project_name_id=project_id)
    if is_valid(head_id):
        ledger_entries = ledger_entries.filter(head_id=head_id)
    if is_valid(entity_id):
        if type_value == 'Vendor':
            ledger_entries = ledger_entries.filter(vendor_id=entity_id)
        elif type_value == 'Contructor':
            ledger_entries = ledger_entries.filter(contructor_id=entity_id)
        elif type_value == 'Capital':
            ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
        elif type_value == 'Customer':
            ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
        elif type_value == 'Bank':
            ledger_entries = ledger_entries.filter(bankName_id=entity_id)
        elif type_value == 'Expense':
            ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

    if transaction_option == 'datewise':
        if fd:
            ledger_entries = ledger_entries.filter(date__gte=fd)
        if td:
            ledger_entries = ledger_entries.filter(date__lte=td)

    ledger_entries = ledger_entries.order_by('date', 'id')

    # Combine ledger, inventory, and bill requisitions into one list
    raw_entries = []
    for entry in ledger_entries:
        if entry.type == 'Vendor' and entry.vendor:
            name = entry.vendor.supplier_name
        elif entry.type == 'Contructor' and entry.contructor:
            name = entry.contructor.supervisor_name
        elif entry.type == 'Capital' and entry.capi_name:
            name = entry.capi_name.person_name
        elif entry.type == 'Customer' and entry.customer_name:
            name = entry.customer_name.customer_name
        elif entry.type == 'Bank' and entry.bankName:
            name = entry.bankName.cash_type_name
        elif entry.type == 'Expense' and entry.exp_name:
            name = entry.exp_name.head_exp_name
        else:
            name = 'N/A'

        raw_entries.append({
            'source': 'ledger',
            'project_name': entry.project_name,
            'head': entry.head.head_name if entry.head else '',
            'name': name,
            'date': entry.date,
            'description': entry.description,
            'cheque_number': getattr(entry, 'cheque_number', ''),
            'payment': entry.debit,
            'received': entry.credit,
        })

   
    # =========================
    # INVENTORY DAY-WISE TOTAL
    # =========================
    
    # if type_value == 'Vendor':
    
    #     inventories = Inventories.objects.all()
    
    #     if is_valid(entity_id):
    #         inventories = inventories.filter(
    #             vendor_name_id=entity_id
    #         )
    
    #     if is_valid(project_id):
    #         inventories = inventories.filter(
    #             project_name_id=project_id
    #         )
    
    #     if transaction_option == 'datewise':
    
    #         if fd:
    #             inventories = inventories.filter(
    #                 purch_date__gte=fd
    #             )
    
    #         if td:
    #             inventories = inventories.filter(
    #                 purch_date__lte=td
    #             )
    
    #     # =========================
    #     # GROUP BY DATE
    #     # =========================
    
    #     inventories = (
    #         inventories
    #         .values(
    #             'purch_date',
    #             'project_name',
    #             'vendor_name'
    #         )
    #         .annotate(
    #             total_amount=Sum('amount')
    #         )
    #         .order_by('purch_date')
    #     )
    
    #     # =========================
    #     # APPEND DAYWISE ENTRY
    #     # =========================
    
    #     for inv in inventories:
    
    #         project_obj = ProjectFirstLevelName.objects.filter(
    #             id=inv['project_name']
    #         ).first()
    
    #         vendor_obj = Suppliers.objects.filter(
    #             id=inv['vendor_name']
    #         ).first()
    
    #         raw_entries.append({
    
    #             'source': 'inventory',
    
    #             'project_name': project_obj,
    
    #             'head': 'Inventory Purchase',
    
    #             'name': (
    #                 vendor_obj.supplier_name
    #                 if vendor_obj else ''
    #             ),
    
    #             'date': inv['purch_date'],
    
    #             'description': (
    #                 f"Inventory Purchase Total "
    #                 f"({inv['purch_date']})"
    #             ),
    
    #             'cheque_number': '',
    
    #             # CREDIT
    #             'payment': Decimal('0.00'),
    
    #             'received': (
    #                 inv['total_amount']
    #                 or Decimal('0.00')
    #             ),
    
    #         })
    
    
    
    # =========================
    # INVENTORY DAY-WISE TOTAL
    # =========================
    
    if type_value == 'Vendor':
    
        inventories = Inventories.objects.all()
    
        if is_valid(entity_id):
            inventories = inventories.filter(
                vendor_name_id=entity_id
            )
    
        if is_valid(project_id):
            inventories = inventories.filter(
                project_name_id=project_id
            )
    
        if transaction_option == 'datewise':
    
            if fd:
                inventories = inventories.filter(
                    purch_date__gte=fd
                )
    
            if td:
                inventories = inventories.filter(
                    purch_date__lte=td
                )
    
        # =========================
        # GROUP SAME DATE
        # =========================
    
        grouped_inventory = (
            inventories
            .values(
                'purch_date',
                'project_name',
                'vendor_name'
            )
            .annotate(
                total_amount=Sum('amount')
            )
            .order_by('purch_date')
        )
    
        # =========================
        # LOOP
        # =========================
    
        for inv in grouped_inventory:
    
            project_obj = ProjectFirstLevelName.objects.filter(
                id=inv['project_name']
            ).first()
    
            vendor_obj = Suppliers.objects.filter(
                id=inv['vendor_name']
            ).first()
    
            # =========================
            # GET ITEM NAMES
            # =========================
    
            same_day_items = Inventories.objects.filter(
                purch_date=inv['purch_date']
            )
    
            if is_valid(entity_id):
                same_day_items = same_day_items.filter(
                    vendor_name_id=entity_id
                )
    
            if is_valid(project_id):
                same_day_items = same_day_items.filter(
                    project_name_id=project_id
                )
    
            item_names = ", ".join(
                list(
                    same_day_items.values_list(
                        'item_name__head_requi_name',
                        flat=True
                    ).distinct()
                )
            )
    
            # =========================
            # APPEND ENTRY
            # =========================
    
            raw_entries.append({
    
                'source': 'inventory',
    
                'project_name': project_obj,
    
                'head': 'Inventory Purchase',
    
                'name': (
                    vendor_obj.supplier_name
                    if vendor_obj else ''
                ),
    
                'date': inv['purch_date'],
    
                'description': (
                    f"Purchase "
                    #f"({inv['purch_date']}) "
                    f"- {item_names}"
                ),
    
                'cheque_number': 'INV',
    
                # CREDIT
                'payment': Decimal('0.00'),
    
                'received': (
                    inv['total_amount']
                    or Decimal('0.00')
                ),
    
            })
            
    # Add BillRequisition entries
    bill_reqs = BillRequisition.objects.filter(approv_status="approved")
    if is_valid(project_id):
        bill_reqs = bill_reqs.filter(project_name_id=project_id)
    if is_valid(head_id):
        bill_reqs = bill_reqs.filter(head_of_account_id=head_id)
        
    if is_valid(entity_id):
        bill_reqs = bill_reqs.filter(vendor_name=entity_id)
    
    # if is_valid(type_value):
    #     bill_reqs = bill_reqs.filter(type=type_value)
    
    if transaction_option == 'datewise':
        if fd:
            bill_reqs = bill_reqs.filter(requisition_date__gte=fd)
        if td:
            bill_reqs = bill_reqs.filter(requisition_date__lte=td)

    for breq in bill_reqs:
        raw_entries.append({
            'source': 'bill_requisition',
            'project_name': breq.project_name,
            'head': breq.head_of_account.head_name if breq.head_of_account else '',
            'name': breq.vendor_name if breq.vendor_name else '',
            'date': breq.requisition_date,
            'description': breq.remark,
            'cheque_number': breq.mr_or_bill_no,
            'payment': Decimal('0.00'),
            'received': breq.amount,
        })
    
    
    # Add PropertySales entries when Expense is selected
    if type_value == 'Expense' and entity_id:
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            entity_id_int = None
    
        if entity_id_int:
            sales_qs = PropertySales.objects.filter(donaton_name_id=entity_id_int)
    
            if transaction_option == 'datewise':
                if fd:
                    sales_qs = sales_qs.filter(sales_date__gte=fd)
                if td:
                    sales_qs = sales_qs.filter(sales_date__lte=td)
    
            # Debug: check how many records are returned
            print("PropertySales entries count:", sales_qs.count())
    
            for sale in sales_qs:
                raw_entries.append({
                    'source': 'property_sales',
                    'project_name': sale.project_name,
                    'head': sale.donaton_name.head_exp_name if sale.donaton_name else '',
                    'name': sale.donaton_name.head_exp_name if sale.donaton_name else '',
                    'date': sale.sales_date,
                    'description': sale.details,
                    'cheque_number': '',
                    'payment': Decimal('0.00'),
                    'received': sale.lilahetalah_amount,
                })


    # Sort all combined entries
    raw_entries.sort(key=lambda x: (x['date'], x.get('project_name').id if x.get('project_name') else 0))

    # Balance calculation
    balance = Decimal('0.00')
    total_payment = Decimal('0.00')
    total_received = Decimal('0.00')
    entry_data = []

    for entry in raw_entries:
        payment = entry['payment']
        received = entry['received']
        balance += received - payment
        total_payment += payment
        total_received += received
        entry['balance'] = balance
        entry_data.append(entry)

    return render(request, 'reportmanage/ledger_report_print.html', {
        'entry_data': entry_data,
        'total_payment': total_payment,
        'total_received': total_received,
        'final_balance': balance,
        'print_time': datetime.now(),
        'projectNames': ProjectFirstLevelName.objects.all(),
        'heads': HeadOfAccount.objects.all(),
        'vendors': Suppliers.objects.all(),
        'supervisors': SiteSupervisor.objects.all(),
        'capital_accounts': CapitalAccount.objects.all(),
        'selected_filters': {
            'type': type_value,
            'head': head_id,
            'cash_type_name': entity_id,
            'project': project_id,
            'project_name': ProjectFirstLevelName.objects.get(id=project_id).project_first_name if is_valid(project_id) else 'All',
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    })
    

# @login_required
# def ledger_manage_pdf(request):
#     head_id = request.GET.get('head')
#     entity_id = request.GET.get('cash_type_name')
#     project_id = request.GET.get('project')
#     type_value = request.GET.get('type', 'Vendor')
#     transaction_option = request.GET.get('transaction', 'datewise')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     def is_valid(val):
#         return val not in [None, '', '0']

#     def parse_date(s):
#         try:
#             return datetime.strptime(s, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Convert entity_id to int for proper ForeignKey matching
#     if is_valid(entity_id) and entity_id.isdigit():
#         entity_id = int(entity_id)
#     else:
#         entity_id = None

#     # Filter Ledger Entries
#     ledger_entries = LedgerEntry.objects.filter(type=type_value)
#     if is_valid(project_id):
#         ledger_entries = ledger_entries.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         ledger_entries = ledger_entries.filter(head_id=head_id)
#     if entity_id:
#         if type_value == 'Vendor':
#             ledger_entries = ledger_entries.filter(vendor_id=entity_id)
#         elif type_value == 'Contructor':
#             ledger_entries = ledger_entries.filter(contructor_id=entity_id)
#         elif type_value == 'Capital':
#             ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
#         elif type_value == 'Customer':
#             ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
#         elif type_value == 'Bank':
#             ledger_entries = ledger_entries.filter(bankName_id=entity_id)
#         elif type_value == 'Expense':
#             ledger_entries = ledger_entries.filter(exp_name_id=entity_id)

#     if transaction_option == 'datewise':
#         if fd:
#             ledger_entries = ledger_entries.filter(date__gte=fd)
#         if td:
#             ledger_entries = ledger_entries.filter(date__lte=td)

#     ledger_entries = ledger_entries.order_by('date', 'id')

#     # Combine ledger, inventory, and bill requisitions into one list
#     raw_entries = []
#     for entry in ledger_entries:
#         if entry.type == 'Vendor' and entry.vendor:
#             name = entry.vendor.supplier_name
#         elif entry.type == 'Contructor' and entry.contructor:
#             name = entry.contructor.supervisor_name
#         elif entry.type == 'Capital' and entry.capi_name:
#             name = entry.capi_name.person_name
#         elif entry.type == 'Customer' and entry.customer_name:
#             name = entry.customer_name.customer_name
#         elif entry.type == 'Bank' and entry.bankName:
#             name = entry.bankName.cash_type_name
#         elif entry.type == 'Expense' and entry.exp_name:
#             name = entry.exp_name.head_exp_name
#         else:
#             name = 'N/A'

#         raw_entries.append({
#             'source': 'ledger',
#             'project_name': entry.project_name,
#             'head': entry.head.head_name if entry.head else '',
#             'name': name,
#             'date': entry.date,
#             'description': entry.description,
#             'cheque_number': getattr(entry, 'cheque_number', ''),
#             'payment': entry.debit,
#             'received': entry.credit,
#         })

#     # Add inventories (Vendor only)
#     if type_value == 'Vendor':
#         inventories = Inventories.objects.all()
#         if entity_id:
#             inventories = inventories.filter(vendor_name_id=entity_id)
#         if is_valid(project_id):
#             inventories = inventories.filter(project_name_id=project_id)
#         if transaction_option == 'datewise':
#             if fd:
#                 inventories = inventories.filter(purch_date__gte=fd)
#             if td:
#                 inventories = inventories.filter(purch_date__lte=td)

#         for inv in inventories:
#             raw_entries.append({
#                 'source': 'inventory',
#                 'project_name': inv.project_name,
#                 'head': inv.item_name.head_requi_name if inv.item_name else '',
#                 'name': inv.vendor_name.supplier_name if inv.vendor_name else '',
#                 'date': inv.purch_date,
#                 'description': inv.remark,
#                 'cheque_number': '',
#                 'payment': Decimal('0.00'),
#                 'received': inv.amount,
#             })

#     # Add BillRequisition entries
#     bill_reqs = BillRequisition.objects.filter(approv_status="approved")
#     if is_valid(project_id):
#         bill_reqs = bill_reqs.filter(project_name_id=project_id)
#     if is_valid(head_id):
#         bill_reqs = bill_reqs.filter(head_of_account_id=head_id)
#     if entity_id:
#         bill_reqs = bill_reqs.filter(vendor_name=entity_id)
#     if transaction_option == 'datewise':
#         if fd:
#             bill_reqs = bill_reqs.filter(requisition_date__gte=fd)
#         if td:
#             bill_reqs = bill_reqs.filter(requisition_date__lte=td)

#     for breq in bill_reqs:
#         raw_entries.append({
#             'source': 'bill_requisition',
#             'project_name': breq.project_name,
#             'head': breq.head_of_account.head_name if breq.head_of_account else '',
#             'name': breq.vendor_name if breq.vendor_name else '',
#             'date': breq.requisition_date,
#             'description': breq.remark,
#             'cheque_number': breq.mr_or_bill_no,
#             'payment': Decimal('0.00'),
#             'received': breq.amount,
#         })

#     # Add PropertySales entries when Expense is selected
#     if type_value == 'Expense' and entity_id:
#         try:
#             entity_id_int = int(entity_id)
#         except ValueError:
#             entity_id_int = None
    
#         if entity_id_int:
#             sales_qs = PropertySales.objects.filter(donaton_name_id=entity_id_int)
    
#             if transaction_option == 'datewise':
#                 if fd:
#                     sales_qs = sales_qs.filter(sales_date__gte=fd)
#                 if td:
#                     sales_qs = sales_qs.filter(sales_date__lte=td)
    
#             # Debug: check how many records are returned
#             print("PropertySales entries count:", sales_qs.count())
    
#             for sale in sales_qs:
#                 raw_entries.append({
#                     'source': 'property_sales',
#                     'project_name': sale.project_name,
#                     'head': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'name': sale.donaton_name.head_exp_name if sale.donaton_name else '',
#                     'date': sale.sales_date,
#                     'description': sale.details,
#                     'cheque_number': '',
#                     'payment': Decimal('0.00'),
#                     'received': sale.lilahetalah_amount,
#                 })


#     # Sort all combined entries
#     raw_entries.sort(key=lambda x: (x['date'], x.get('project_name').id if x.get('project_name') else 0))

#     # Balance calculation
#     balance = Decimal('0.00')
#     total_payment = Decimal('0.00')
#     total_received = Decimal('0.00')
#     entry_data = []

#     for entry in raw_entries:
#         payment = entry['payment']
#         received = entry['received']
#         balance += received - payment
#         total_payment += payment
#         total_received += received
#         entry['balance'] = balance
#         entry_data.append(entry)

#     return render(request, 'reportmanage/ledger_report_print.html', {
#         'entry_data': entry_data,
#         'total_payment': total_payment,
#         'total_received': total_received,
#         'final_balance': balance,
#         'print_time': datetime.now(),
#         'projectNames': ProjectFirstLevelName.objects.all(),
#         'heads': HeadOfAccount.objects.all(),
#         'vendors': Suppliers.objects.all(),
#         'supervisors': SiteSupervisor.objects.all(),
#         'capital_accounts': CapitalAccount.objects.all(),
#         'selected_filters': {
#             'type': type_value,
#             'head': head_id,
#             'cash_type_name': entity_id,
#             'project': project_id,
#             'project_name': ProjectFirstLevelName.objects.get(id=project_id).project_first_name if is_valid(project_id) else 'All',
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     })





# @login_required
# def employee_summary_report(request):
#     today = timezone.now()
#     current_month_start = today.replace(day=1)

#     employees = Employee.objects.all()
#     report_data = []

#     for employee in employees:
#         # Advance this month
#         advances = AdvancePayment.objects.filter(
#             employee=employee,
#             date__gte=current_month_start,
#             date__lte=today
#         )
#         advance_total = advances.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

#         # Allowance this month
#         allowances = Allowances.objects.filter(
#             employee=employee,
#             date__gte=current_month_start,
#             date__lte=today
#         )
#         allowance_total = allowances.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

#         # Ledger Entry (employee name match) this month
#         ledger_entries = LedgerEntry.objects.filter(
#             type='Employee',
#             empl_name=employee.employee_name,
#             date__gte=current_month_start,
#             date__lte=today
#         )
#         ledger_debit_total = ledger_entries.aggregate(total_debit=Sum('debit'))['total_debit'] or 0

#         # Use salary from model
#         salary = employee.salary if hasattr(employee, 'salary') else 0

#         # âœ… New Final Balance logic
#         final_balance = salary - ledger_debit_total

#         report_data.append({
#             'employee': employee,
#             'advance_total': advance_total,
#             'allowance_total': allowance_total,
#             'total_received': advance_total + allowance_total,
#             'ledger_debit_total': ledger_debit_total,
#             'salary': salary,
#             'final_balance': final_balance,
#         })

#     return render(request, 'reportmanage/employee_summary.html', {'report_data': report_data})




@login_required
def employee_summary_report(request):
    today = timezone.now()
    current_month_start = today.replace(day=1)
    current_month_name = today.strftime('%B %Y')  # e.g., "September 2025"

    employees = RdaEmployee.objects.filter(rda_active_status=True)
    report_data = []

    for employee in employees:
        # Advance this month (deduction)
        advances = AdvancePayment.objects.filter(
            employee=employee,
            date__gte=current_month_start,
            date__lte=today,
            status='due'
        )
        advance_total = advances.aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal(0)

        # Allowance this month (addition)
        allowances = Allowances.objects.filter(
            employee=employee,
            date__gte=current_month_start,
            date__lte=today,
            status='due'
        )
        allowance_total = allowances.aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal(0)

        # LoanPayment deduction this month
        loans_qs = LoanPayment.objects.filter(
            employee=employee,
            status='due',
            start_month__lte=today,
            end_month__gte=current_month_start
        )
        loan_deduction_total = Decimal(0)
        for loan in loans_qs:
            if loan.month_name and current_month_name in loan.month_name:
                loan_deduction_total += loan.deduction_amount or Decimal(0)

        # LedgerEntry debit this month (hidden, just for calculation)
        ledger_entries = LedgerEntry.objects.filter(
            type='Employee',
            empl_name=employee.rda_emp_name,
            date__gte=current_month_start,
            date__lte=today
        )
        ledger_debit_total = ledger_entries.aggregate(total_debit=Sum('debit'))['total_debit'] or Decimal(0)

        # Salary from RdaEmployee model
        salary = employee.rda_salary or Decimal(0)

        # Final balance calculation
        final_balance = salary + allowance_total - advance_total - loan_deduction_total - ledger_debit_total

        report_data.append({
            'employee': employee,
            'advance_total': advance_total,
            'allowance_total': allowance_total,
            'total_received': advance_total + allowance_total,
            'loan_deduction_total': loan_deduction_total,
            'ledger_debit_total': ledger_debit_total,
            'salary': salary,
            'final_balance': final_balance,
        })

    return render(request, 'reportmanage/employee_summary.html', {
        'report_data': report_data
    })




@login_required
def employee_ledger_manage(request):
    employees = RdaEmployee.objects.all()    
    context = {
        'employees': employees,
        'today': date.today(),
    }
    return render(request, 'reportmanage/employee_ledger_manage.html', context)



# @login_required
# def employee_ledger_report(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     month_from_ledger = None

#     if is_valid(employee_id) and type_param == "Employee":
#         employee = get_object_or_404(Employee, id=employee_id)
#         salary = employee.salary if hasattr(employee, 'salary') else Decimal('0.00')

#         # === Advance Payments ===
#         advances = AdvancePayment.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#         advance_total = advances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Allowances ===
#         allowances = Allowances.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 allowances = allowances.filter(date__gte=fd)
#             if td:
#                 allowances = allowances.filter(date__lte=td)
#         allowance_total = allowances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Ledger Entries (Employee) ===
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.employee_name)
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)

#         ledger_total = ledgers.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

#         # === Month from first ledger entry ===
#         first_ledger = ledgers.order_by('date').first()
#         month_from_ledger = first_ledger.date.strftime('%B %Y') if first_ledger else None

#         # === Final Balance (salary - ledger paid)
#         balance = salary - ledger_total

#         report_data.append({
#             'employee': employee,
#             'salary': salary,
#             'advance_total': advance_total,
#             'allowance_total': allowance_total,
#             'total_received': advance_total + allowance_total,
#             'ledger_total': ledger_total,
#             'balance': balance,
#             'advances': advances,
#             'allowances': allowances,
#             'ledger_entries': ledgers,
#         })

#     return render(request, 'reportmanage/employee_ledger_report.html', {
#         'report_data': report_data,
#         'month_from_ledger': month_from_ledger,
#         'filters': {
#             'type': type_param,
#             'employee_name': employee_id,
#             'from_date': from_date,
#             'to_date': to_date,
#             'transaction': transaction_option,
#         }
#     })




@login_required
def employee_ledger_report(request):
    type_param = request.GET.get('type')
    employee_id = request.GET.get('employee_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'all')

    def is_valid(val):
        return val not in [None, '', 'null']

    def try_parse_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except:
            return None

    fd = try_parse_date(from_date)
    td = try_parse_date(to_date)

    report_data = []
    month_from_ledger = None

    if is_valid(employee_id) and type_param == "Employee":
        employee = get_object_or_404(RdaEmployee, id=employee_id)
        salary = employee.rda_salary or Decimal('0.00')

        today = now().date()
        current_month_str = today.strftime("%B")
        current_year = today.year

        # === Advance Payments (deduction) ===
        advances = AdvancePayment.objects.filter(employee=employee)
        if transaction_option == 'datewise':
            if fd: advances = advances.filter(date__gte=fd)
            if td: advances = advances.filter(date__lte=td)
        advance_total = advances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Allowances (addition) ===
        allowances = Allowances.objects.filter(employee=employee)
        if transaction_option == 'datewise':
            if fd: allowances = allowances.filter(date__gte=fd)
            if td: allowances = allowances.filter(date__lte=td)
        allowance_total = allowances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Loan Payments (deduction) ===
        loan_payments = LoanPayment.objects.filter(employee=employee)
        if transaction_option == 'datewise':
            if fd: loan_payments = loan_payments.filter(date__gte=fd)
            if td: loan_payments = loan_payments.filter(date__lte=td)

        loan_deduction_total = Decimal('0.00')
        for lp in loan_payments:
            include_month = False
            if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
                include_month = True
            if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
                include_month = True
            if include_month:
                loan_deduction_total += lp.deduction_amount or Decimal('0.00')

        # === Ledger Entries (deduction) ===
        ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)
        if transaction_option == 'datewise':
            if fd: ledgers = ledgers.filter(date__gte=fd)
            if td: ledgers = ledgers.filter(date__lte=td)
        ledger_total = ledgers.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

        # === Total Deduction ===
        total_deductions = advance_total + ledger_total + loan_deduction_total

        # === Final Balance ===
        final_balance = salary + allowance_total - total_deductions

        # First ledger month
        first_ledger = ledgers.order_by('date').first()
        month_from_ledger = first_ledger.date.strftime('%B %Y') if first_ledger else None

        report_data.append({
            'employee': employee,
            'salary': salary,
            'advance_total': advance_total,
            'allowance_total': allowance_total,
            'total_received': allowance_total,  # Only allowances considered addition
            'ledger_total': ledger_total,
            'loan_deductions': loan_deduction_total,
            'total_deductions': total_deductions,
            'balance': final_balance,
            'advances': advances,
            'allowances': allowances,
            'ledger_entries': ledgers,
        })

    return render(request, 'reportmanage/employee_ledger_report.html', {
        'report_data': report_data,
        'month_from_ledger': month_from_ledger,
        'filters': {
            'type': type_param,
            'employee_name': employee_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })


    
    


# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except Exception:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []

#     if is_valid(employee_id) and type_param == "RdaEmployee":
#         employee = get_object_or_404(RdaEmployee, id=employee_id)
#         salary = employee.salary if hasattr(employee, 'salary') else Decimal('0.00')

#         # === Advance Payments ===
#         advances = AdvancePayment.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#         advance_total = advances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Allowances ===
#         allowances = Allowances.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 allowances = allowances.filter(date__gte=fd)
#             if td:
#                 allowances = allowances.filter(date__lte=td)
#         allowance_total = allowances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Ledger Entries (Employee) ===
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.employee_name)
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledger_total = ledgers.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

#         # === Combine All Transactions ===
#         combined_entries = []

#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'type': 'Advance',
#                 'description': adv.reason or '',
#                 'chq_rec_no': adv.cheque_number or '-',
#                 'payment': None,
#                 'received': adv.amount,
#                 'head_name': adv.cash_type.cash_type_name if adv.cash_type else '',
#                 'carrier': 'Advance',
#             })

#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'type': 'Allowance',
#                 'description': allow.reason or '',
#                 'chq_rec_no': allow.cheque_number or '-',
#                 'payment': None,
#                 'received': allow.amount,
#                 'head_name': allow.cash_type.cash_type_name if allow.cash_type else '',
#                 'carrier': 'Allowance',
#             })

#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'type': 'Ledger',
#                 'description': ledger.description or '',
#                 'chq_rec_no': ledger.cheque_number or '-',
#                 'payment': ledger.debit if ledger.debit else None,
#                 'received': ledger.credit if ledger.credit else None,
#                 'head_name': ledger.head.head_name if ledger.head else '',
#                 'carrier': ledger.carrier or '-',
#             })

#         combined_entries.sort(key=lambda x: x['date'])

#         # === Running Balance Calculation ===
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # === Totals and Final Balance ===
#         total_received = advance_total + allowance_total + (ledgers.aggregate(total_credit=Sum('credit'))['total_credit'] or Decimal('0.00'))
#         total_paid = ledger_total
#         final_balance = salary - total_paid  # Based on salary, not received

#         report_data.append({
#             'employee': employee,
#             'salary': salary,
#             'advance_total': advance_total,
#             'allowance_total': allowance_total,
#             'ledger_total': ledger_total,
#             'total_received': total_received,
#             'total_paid': total_paid,
#             'final_balance': final_balance,
#             'ledger_entries': combined_entries,
#         })

#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except Exception:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'print_time': datetime.now(),
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.employee_name if is_valid(employee_id) else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'reportmanage/employee_ledger_report_print.html', context)




# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except Exception:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     employee = None  # Prevent UnboundLocalError

#     if is_valid(employee_id) and type_param == "Employee":
#         employee = get_object_or_404(RdaEmployee, id=employee_id)
#         salary = employee.rda_salary or Decimal('0.00')

#         today = now().date()
#         current_month_str = today.strftime("%B")
#         current_year = today.year

#         # === Advance Payments ===
#         advances = AdvancePayment.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#         advance_total = advances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Allowances ===
#         allowances = Allowances.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 allowances = allowances.filter(date__gte=fd)
#             if td:
#                 allowances = allowances.filter(date__lte=td)
#         allowance_total = allowances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#         # === Loan Payments (deductions) ===
#         loan_payments = LoanPayment.objects.filter(employee=employee)
#         if transaction_option == 'datewise':
#             if fd:
#                 loan_payments = loan_payments.filter(date__gte=fd)
#             if td:
#                 loan_payments = loan_payments.filter(date__lte=td)

#         loan_deduction_total = Decimal('0.00')
#         for lp in loan_payments:
#             include_month = False
#             # Check if current date falls within start/end month
#             if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
#                 include_month = True
#             # Check if current month/year is in month_name field
#             if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
#                 include_month = True
#             if include_month:
#                 loan_deduction_total += lp.deduction_amount or Decimal('0.00')

#         # === Ledger Entries ===
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledger_total = ledgers.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

#         # === Combine All Transactions for table display ===
#         combined_entries = []

#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'type': 'Advance',
#                 'description': adv.reason or '',
#                 'chq_rec_no': adv.cheque_number or '-',
#                 'payment': None,
#                 'received': adv.amount,
#                 'head_name': adv.cash_type.cash_type_name if adv.cash_type else '',
#                 'carrier': 'Advance',
#             })

#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'type': 'Allowance',
#                 'description': allow.reason or '',
#                 'chq_rec_no': allow.cheque_number or '-',
#                 'payment': None,
#                 'received': allow.amount,
#                 'head_name': allow.cash_type.cash_type_name if allow.cash_type else '',
#                 'carrier': 'Allowance',
#             })

#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'type': 'Ledger',
#                 'description': ledger.description or '',
#                 'chq_rec_no': ledger.cheque_number or '-',
#                 'payment': ledger.debit or Decimal('0.00'),
#                 'received': ledger.credit or None,
#                 'head_name': ledger.head.head_name if ledger.head else '',
#                 'carrier': ledger.carrier or '-',
#             })

#         combined_entries.sort(key=lambda x: x['date'])

#         # === Running Balance Calculation ===
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # === Totals and Final Balance ===
#         total_received = advance_total + allowance_total
#         total_deductions = ledger_total + loan_deduction_total
#         final_balance = salary + total_received - total_deductions

#         report_data.append({
#             'employee': employee,
#             'salary': salary,
#             'advance_total': advance_total,
#             'allowance_total': allowance_total,
#             'ledger_total': ledger_total,
#             'loan_deductions': loan_deduction_total,
#             'total_received': total_received,
#             'total_paid': total_deductions,
#             'final_balance': final_balance,
#             'ledger_entries': combined_entries,
#         })

#     # === Convert amount to words ===
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except Exception:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'print_time': datetime.now(),
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name if employee else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'reportmanage/employee_ledger_report_print.html', context)


# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     employee = None

#     if is_valid(employee_id) and type_param == "Employee":
#         employee = get_object_or_404(RdaEmployee, id=employee_id)
#         salary = employee.rda_salary or Decimal('0.00')

#         today = datetime.now().date()
#         current_month_str = today.strftime("%B")
#         current_year = today.year

#         # === Fetch all transactions ===
#         advances = AdvancePayment.objects.filter(employee=employee)
#         allowances = Allowances.objects.filter(employee=employee)
#         loan_payments = LoanPayment.objects.filter(employee=employee)
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)

#         # Apply date filter if needed
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#                 allowances = allowances.filter(date__gte=fd)
#                 loan_payments = loan_payments.filter(date__gte=fd)
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#                 allowances = allowances.filter(date__lte=td)
#                 loan_payments = loan_payments.filter(date__lte=td)
#                 ledgers = ledgers.filter(date__lte=td)

#         # === Combine transactions into a single ledger list ===
#         combined_entries = []

#         # Advances (deduction)
#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason or '',
#                 'payment': adv.amount,
#                 'received': None,
#                 'head_name': adv.cash_type.cash_type_name if adv.cash_type else '',
#                 'carrier': 'Advance',
#             })

#         # Allowances (addition)
#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason or '',
#                 'payment': None,
#                 'received': allow.amount,
#                 'head_name': allow.cash_type.cash_type_name if allow.cash_type else '',
#                 'carrier': 'Allowance',
#             })

#         # Loan Payments (deduction)
#         for lp in loan_payments:
#             include_month = False
#             if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
#                 include_month = True
#             if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
#                 include_month = True
#             if include_month:
#                 combined_entries.append({
#                     'date': lp.date,
#                     'description': lp.reason or '',
#                     'payment': lp.deduction_amount or Decimal('0.00'),
#                     'received': None,
#                     'head_name': lp.cash_type.cash_type_name if lp.cash_type else '',
#                     'carrier': 'Loan',
#                 })

#         # Ledger entries (debit = payment, credit = received)
#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'description': ledger.description or '',
#                 'payment': ledger.debit or None,
#                 'received': ledger.credit or None,
#                 'head_name': ledger.head.head_name if ledger.head else '',
#                 'carrier': ledger.carrier or '-',
#             })

#         # Sort combined entries by date
#         combined_entries.sort(key=lambda x: x['date'])

#         # === Running balance ===
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # Totals
#         total_received = sum(e['received'] or 0 for e in combined_entries)
#         total_deductions = sum(e['payment'] or 0 for e in combined_entries)
#         final_balance = salary + total_received - total_deductions

#         report_data.append({
#             'employee': employee,
#             'salary': salary,
#             'ledger_entries': combined_entries,
#             'total_received': total_received,
#             'total_deductions': total_deductions,
#             'final_balance': final_balance,
#         })

#     # Amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'report_data': report_data,
#         'print_time': datetime.now(),
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name if employee else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'reportmanage/employee_ledger_report_print.html', context)




# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     employee = None

#     # Fetch employee safely
#     if is_valid(employee_id) and type_param == "Employee":
#         try:
#             employee = RdaEmployee.objects.get(id=employee_id)
#         except RdaEmployee.DoesNotExist:
#             employee = None

#     if employee:
#         today = datetime.now().date()
#         current_month_str = today.strftime("%B")
#         current_year = today.year

#         # --- Fetch all transactions ---
#         advances = AdvancePayment.objects.filter(employee=employee)
#         allowances = Allowances.objects.filter(employee=employee)
#         loan_payments = LoanPayment.objects.filter(employee=employee)
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)

#         # --- Apply date filters ---
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#                 allowances = allowances.filter(date__gte=fd)
#                 loan_payments = loan_payments.filter(date__gte=fd)
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#                 allowances = allowances.filter(date__lte=td)
#                 loan_payments = loan_payments.filter(date__lte=td)
#                 ledgers = ledgers.filter(date__lte=td)

#         # --- Fetch Salary Vouchers (approved) ---
#         salary_vouchers = SalaryVoucher.objects.filter(
#             project=employee.project_name,
#             approval_salary_status='Approved'
#         ).order_by('generate_date')

#         combined_entries = []

#         # Advances (deduction)
#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'approval_date': None,
#                 'description': adv.reason or '',
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': getattr(adv, 'cheque_number', '-'),
#                 'carrier': 'Advance',
#                 'source': 'advance',
#             })

#         # Allowances (addition)
#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'approval_date': None,
#                 'description': allow.reason or '',
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': getattr(allow, 'cheque_number', '-'),
#                 'carrier': 'Allowance',
#                 'source': 'allowance',
#             })

#         # Loan Payments (deduction)
#         for lp in loan_payments:
#             include_month = False
#             if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
#                 include_month = True
#             if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
#                 include_month = True
#             if include_month:
#                 combined_entries.append({
#                     'date': lp.date,
#                     'approval_date': None,
#                     'description': lp.reason or '',
#                     'payment': lp.deduction_amount or Decimal('0.00'),
#                     'received': None,
#                     'cheque_number': getattr(lp, 'cheque_number', '-'),
#                     'carrier': 'Loan',
#                     'source': 'loan',
#                 })

#         # Ledger entries
#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'approval_date': None,
#                 'description': ledger.description or '',
#                 'payment': ledger.debit or None,
#                 'received': ledger.credit or None,
#                 'cheque_number': getattr(ledger, 'cheque_number', '-'),
#                 'carrier': ledger.carrier or '-',
#                 'source': 'ledger',
#             })

#         # Salary entries (as credit) — each salary voucher is a separate row
#         for sv in salary_vouchers:
#             combined_entries.append({
#                 'date': sv.generate_date.date(),
#                 'approval_date': sv.generate_date.date(),
#                 'description': f"Salary for {sv.month_name}",
#                 'payment': None,
#                 'received': employee.rda_salary or Decimal('0.00'),
#                 'cheque_number': '-',
#                 'carrier': 'Salary',
#                 'source': 'salary',
#             })

#         # Sort combined entries by date
#         combined_entries.sort(key=lambda x: x['date'])

#         # Running balance
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # Totals
#         total_received = sum(e['received'] or 0 for e in combined_entries)
#         total_payment = sum(e['payment'] or 0 for e in combined_entries)
#         final_balance = total_received - total_payment

#         report_data.append({
#             'employee': employee,
#             'ledger_entries': combined_entries,
#             'total_received': total_received,
#             'total_payment': total_payment,
#             'final_balance': final_balance,
#         })

#     # Amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'entry_data': report_data[0]['ledger_entries'] if report_data else [],
#         'print_time': datetime.now(),
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'total_payment': report_data[0]['total_payment'] if report_data else 0,
#         'total_received': report_data[0]['total_received'] if report_data else 0,
#         'final_balance': report_data[0]['final_balance'] if report_data else 0,
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name if employee else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'project_name': employee.project_name.project_first_name if employee and employee.project_name else "All",
#         }
#     }

#     return render(request, 'reportmanage/employee_ledger_report_print.html', context)




# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     employee = None

#     # Fetch employee safely
#     if is_valid(employee_id) and type_param == "Employee":
#         try:
#             employee = RdaEmployee.objects.get(id=employee_id)
#         except RdaEmployee.DoesNotExist:
#             employee = None

#     if employee:
#         today = datetime.now().date()
#         current_month_str = today.strftime("%B")
#         current_year = today.year

#         # --- Fetch all transactions ---
#         advances = AdvancePayment.objects.filter(employee=employee)
#         allowances = Allowances.objects.filter(employee=employee)
#         loan_payments = LoanPayment.objects.filter(employee=employee)
#         ledgers = LedgerEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)

#         # --- Apply date filters to transactions ---
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#                 allowances = allowances.filter(date__gte=fd)
#                 loan_payments = loan_payments.filter(date__gte=fd)
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#                 allowances = allowances.filter(date__lte=td)
#                 loan_payments = loan_payments.filter(date__lte=td)
#                 ledgers = ledgers.filter(date__lte=td)

#         # --- Fetch Salary Vouchers (Approved) ---
#         salary_vouchers = SalaryVoucher.objects.filter(
#             project=employee.project_name,
#             approval_salary_status='Approved'
#         ).order_by('generate_date')

#         # Filter salary vouchers by month if from_date/to_date provided
#         if fd or td:
#             filtered_vouchers = []
#             for sv in salary_vouchers:
#                 sv_date = sv.generate_date.date()
#                 if fd and sv_date < fd:
#                     continue
#                 if td and sv_date > td:
#                     continue
#                 filtered_vouchers.append(sv)
#             salary_vouchers = filtered_vouchers

#         combined_entries = []

#         # --- Advances (deduction) ---
#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'approval_date': None,
#                 'description': adv.reason or '',
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': getattr(adv, 'cheque_number', '-'),
#                 'carrier': 'Advance',
#                 'source': 'advance',
#             })

#         # --- Allowances (addition) ---
#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'approval_date': None,
#                 'description': allow.reason or '',
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': getattr(allow, 'cheque_number', '-'),
#                 'carrier': 'Allowance',
#                 'source': 'allowance',
#             })

#         # --- Loan Payments (deduction) ---
#         for lp in loan_payments:
#             include_month = False
#             if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
#                 include_month = True
#             if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
#                 include_month = True
#             if include_month:
#                 combined_entries.append({
#                     'date': lp.date,
#                     'approval_date': None,
#                     'description': lp.reason or '',
#                     'payment': lp.deduction_amount or Decimal('0.00'),
#                     'received': None,
#                     'cheque_number': getattr(lp, 'cheque_number', '-'),
#                     'carrier': 'Loan',
#                     'source': 'loan',
#                 })

#         # --- Ledger entries ---
#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'approval_date': None,
#                 'description': ledger.description or '',
#                 'payment': ledger.debit or None,
#                 'received': ledger.credit or None,
#                 'cheque_number': getattr(ledger, 'cheque_number', '-'),
#                 'carrier': ledger.carrier or '-',
#                 'source': 'ledger',
#             })

#         # --- Salary entries (as credit) ---
#         for sv in salary_vouchers:
#             combined_entries.append({
#                 'date': sv.generate_date.date(),
#                 'approval_date': sv.generate_date.date(),
#                 'description': f"Salary for {sv.month_name}",
#                 'payment': None,
#                 'received': employee.rda_salary or Decimal('0.00'),
#                 'cheque_number': '-',
#                 'carrier': 'Salary',
#                 'source': 'salary',
#             })

#         # --- Sort combined entries by date ---
#         combined_entries.sort(key=lambda x: x['date'])

#         # --- Running balance ---
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # Totals
#         total_received = sum(e['received'] or 0 for e in combined_entries)
#         total_payment = sum(e['payment'] or 0 for e in combined_entries)
#         final_balance = total_received - total_payment

#         report_data.append({
#             'employee': employee,
#             'ledger_entries': combined_entries,
#             'total_received': total_received,
#             'total_payment': total_payment,
#             'final_balance': final_balance,
#         })

#     # Amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             words += " only"
#             return words
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'entry_data': report_data[0]['ledger_entries'] if report_data else [],
#         'print_time': datetime.now(),
#         'employee': employee,
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'total_payment': report_data[0]['total_payment'] if report_data else 0,
#         'total_received': report_data[0]['total_received'] if report_data else 0,
#         'final_balance': report_data[0]['final_balance'] if report_data else 0,
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name if employee else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'project_name': employee.project_name.project_first_name if employee and employee.project_name else "All",
#         }
#     }

#     return render(request, 'reportmanage/employee_ledger_report_print.html', context)
    



## ok code ---

# from decimal import Decimal
# from datetime import datetime
# from calendar import monthrange
# from num2words import num2words

# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def try_parse_date(value):
#         try:
#             return datetime.strptime(value, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     report_data = []
#     employee = None

#     # Fetch employee
#     if is_valid(employee_id) and type_param == "Employee":
#         try:
#             employee = RdaEmployee.objects.get(id=employee_id)
#         except RdaEmployee.DoesNotExist:
#             employee = None

#     if employee:
#         today = datetime.now().date()
#         current_month_str = today.strftime("%B")
#         current_year = today.year

#         # Fetch transactions
#         advances = AdvancePayment.objects.filter(employee=employee)
#         allowances = Allowances.objects.filter(employee=employee)
#         loan_payments = LoanPayment.objects.filter(employee=employee)
#         ledgers = LedgerEntry.objects.filter(
#             type='Employee',
#             empl_name=employee.rda_emp_name
#         )

#         # Apply date filters
#         if transaction_option == 'datewise':
#             if fd:
#                 advances = advances.filter(date__gte=fd)
#                 allowances = allowances.filter(date__gte=fd)
#                 loan_payments = loan_payments.filter(date__gte=fd)
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 advances = advances.filter(date__lte=td)
#                 allowances = allowances.filter(date__lte=td)
#                 loan_payments = loan_payments.filter(date__lte=td)
#                 ledgers = ledgers.filter(date__lte=td)

#         combined_entries = []

#         # Advances (Debit)
#         for adv in advances:
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason or '',
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': getattr(adv, 'cheque_number', '-'),
#                 'source': 'advance',
#             })

#         # Allowances (Credit)
#         for allow in allowances:
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason or '',
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': getattr(allow, 'cheque_number', '-'),
#                 'source': 'allowance',
#             })

#         # Loan deductions (Debit)
#         for lp in loan_payments:
#             include_month = False
#             if lp.start_month and lp.end_month and lp.start_month <= today <= lp.end_month:
#                 include_month = True
#             if lp.month_name and current_month_str in lp.month_name and str(current_year) in lp.month_name:
#                 include_month = True

#             if include_month:
#                 combined_entries.append({
#                     'date': lp.date,
#                     'description': lp.reason or '',
#                     'payment': lp.deduction_amount or Decimal('0.00'),
#                     'received': None,
#                     'cheque_number': getattr(lp, 'cheque_number', '-'),
#                     'source': 'loan',
#                 })

#         # Manual ledger entries
#         for ledger in ledgers:
#             combined_entries.append({
#                 'date': ledger.date,
#                 'description': ledger.description or '',
#                 'payment': ledger.debit,
#                 'received': ledger.credit,
#                 'cheque_number': getattr(ledger, 'cheque_number', '-'),
#                 'source': 'ledger',
#             })

#         # ===============================
#         # BASIC SALARY (Employee-wise)
#         # ===============================
#         salary_amount = employee.rda_salary or Decimal('0.00')

#         if td:
#             salary_date = td
#         elif fd:
#             salary_date = fd
#         else:
#             salary_date = today.replace(
#                 day=monthrange(today.year, today.month)[1]
#             )

#         combined_entries.append({
#             'date': salary_date,
#             'description': 'Basic Salary',
#             'payment': None,
#             'received': salary_amount,
#             'cheque_number': '-',
#             'source': 'salary',
#         })

#         # Sort by date
#         combined_entries.sort(key=lambda x: x['date'])

#         # Running balance
#         running_balance = Decimal('0.00')
#         for entry in combined_entries:
#             received = entry['received'] or Decimal('0.00')
#             payment = entry['payment'] or Decimal('0.00')
#             running_balance += received - payment
#             entry['balance'] = running_balance

#         # Totals
#         total_received = sum(e['received'] or 0 for e in combined_entries)
#         total_payment = sum(e['payment'] or 0 for e in combined_entries)
#         final_balance = total_received - total_payment

#         report_data.append({
#             'ledger_entries': combined_entries,
#             'total_received': total_received,
#             'total_payment': total_payment,
#             'final_balance': final_balance,
#         })

#     # Amount to words
#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             integer_part = int(amount)
#             fractional_part = int(round((amount - integer_part) * 100))
#             words = num2words(integer_part, lang='en').title() + " Taka"
#             if fractional_part:
#                 words += " and " + num2words(fractional_part, lang='en').title() + " Paisa"
#             return words + " only"
#         except:
#             return f"{amount} Taka only"

#     context = {
#         'entry_data': report_data[0]['ledger_entries'] if report_data else [],
#         'employee': employee,
#         'print_time': datetime.now(),
#         'total_payment': report_data[0]['total_payment'] if report_data else 0,
#         'total_received': report_data[0]['total_received'] if report_data else 0,
#         'final_balance': report_data[0]['final_balance'] if report_data else 0,
#         'balance_in_words': amount_to_words(report_data[0]['final_balance']) if report_data else '',
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name if employee else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#             'project_name': employee.project_name.project_first_name if employee and employee.project_name else "All",
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )



## end ok code ----



# from decimal import Decimal
# from datetime import datetime
# from calendar import monthrange
# from django.db.models import Count
# from num2words import num2words

# from hrm.models import RdaEmployee, Attendance


# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     salary_amount = employee.rda_salary or Decimal('0.00')
#     use_date_filter = (transaction_option == 'datewise')

#     # ===============================
#     # MONTH RANGE
#     # ===============================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     if fd and td:
#         months_list = month_range(fd, td)
#     else:
#         today = datetime.today().date()
#         months_list = [today.replace(day=1)]

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ===============================
#     # MONTH-WISE PROCESSING
#     # ===============================
#     for month_start in months_list:
#         last_day = monthrange(month_start.year, month_start.month)[1]
#         month_end = month_start.replace(day=last_day)

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         combined_entries.append({
#             'date': month_start,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         for allow in Allowances.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan =================
#         for loan in LoanPayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': loan.date,
#                 'description': loan.reason,
#                 'payment': loan.deduction_amount or Decimal('0.00'),
#                 'received': None,
#                 'cheque_number': loan.cheque_number or '-',
#                 'source': 'loan',
#             })

#         # ================= Manual Ledger =================
#         for ledger in LedgerEntry.objects.filter(
#             type='Employee',
#             empl_name=employee.rda_emp_name,
#             date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': ledger.date,
#                 'description': ledger.description,
#                 'payment': ledger.debit,
#                 'received': ledger.credit,
#                 'cheque_number': ledger.cheque_number or '-',
#                 'source': 'ledger',
#             })

#         # ================= Salary (IMAGE LOGIC) =================
#         # 1️⃣ FULL BASIC SALARY FIRST
#         combined_entries.append({
#             'date': month_start,
#             'description': f"Salary : {employee.rda_emp_name}-{month_start.strftime('%b-%Y').lower()}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # 2️⃣ ABSENT DEDUCTION SEPARATE
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': month_start,
#                 'description': f"Salary Deduction ({absent_days} Absent Day)",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ===============================
#     # SORT & RUNNING BALANCE
#     # ===============================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ===============================
#     # CONTEXT
#     # ===============================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )






# from decimal import Decimal
# from datetime import datetime
# from calendar import monthrange
# from django.db.models import Count, Min
# from num2words import num2words

# from hrm.models import RdaEmployee, Attendance


# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     today = datetime.today().date()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # ALL DATE FILTER (EMPLOYEE START → TODAY)
#     # ==================================================
#     if transaction_option == 'all' and not fd and not td:
#         first_dates = []

#         first_dates.append(
#             Attendance.objects.filter(employee=employee).aggregate(d=Min('date'))['d']
#         )
#         first_dates.append(
#             AdvancePayment.objects.filter(employee=employee).aggregate(d=Min('date'))['d']
#         )
#         first_dates.append(
#             Allowances.objects.filter(employee=employee).aggregate(d=Min('date'))['d']
#         )
#         first_dates.append(
#             LoanPayment.objects.filter(employee=employee).aggregate(d=Min('date'))['d']
#         )

#         first_dates = [d for d in first_dates if d]

#         fd = min(first_dates) if first_dates else today
#         td = today

#     use_date_filter = (transaction_option == 'datewise')

#     # ==================================================
#     # MONTH RANGE
#     # ==================================================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ==================================================
#     # MONTH-WISE PROCESSING
#     # ==================================================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         combined_entries.append({
#             'date': month_start,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         for allow in Allowances.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan =================
#         for loan in LoanPayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': loan.date,
#                 'description': loan.reason,
#                 'payment': loan.deduction_amount or Decimal('0.00'),
#                 'received': None,
#                 'cheque_number': loan.cheque_number or '-',
#                 'source': 'loan',
#             })

#         # ================= Salary =================
#         combined_entries.append({
#             'date': month_start,
#             'description': f"Salary : {employee.rda_emp_name}-{month_start.strftime('%b-%Y').lower()}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ================= Salary Deduction =================
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': month_start,
#                 'description': f"Salary Deduction ({absent_days} Absent Day)",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ==================================================
#     # SORT & RUNNING BALANCE
#     # ==================================================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ==================================================
#     # CONTEXT
#     # ==================================================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )




# from decimal import Decimal
# from datetime import datetime, date
# from calendar import monthrange
# from django.db.models import Count, Min
# from num2words import num2words

# from hrm.models import RdaEmployee, Attendance, AdvancePayment, Allowances, LoanPayment, SalaryPayment

# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # FIXED RULE: transaction = all → employee's first SalaryPayment → today
#     # ==================================================
#     if transaction_option == 'all':
#         first_salary = SalaryPayment.objects.filter(employee=employee).order_by('date').first()
#         fd = first_salary.date if first_salary else date(2025, 10, 1)
#         td = today

#     use_date_filter = (transaction_option == 'datewise')

#     # ==================================================
#     # MONTH RANGE
#     # ==================================================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ==================================================
#     # MONTH-WISE PROCESSING
#     # ==================================================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         combined_entries.append({
#             'date': month_start,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         for allow in Allowances.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan =================
#         loans = LoanPayment.objects.filter(employee=employee)
#         for loan in loans:
#             include_month = False
#             if loan.start_month and loan.end_month:
#                 include_month = loan.start_month.replace(day=1) <= month_start <= loan.end_month.replace(day=1)
#             if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
#                 include_month = True

#             if include_month:
#                 combined_entries.append({
#                     'date': month_start,
#                     'description': loan.reason,
#                     'payment': loan.deduction_amount or Decimal('0.00'),
#                     'received': None,
#                     'cheque_number': loan.cheque_number or '-',
#                     'source': 'loan',
#                 })

#         # ================= SalaryPayment (Debit) =================
#         for sp in SalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"SalaryPayment ({sp.monthofsalary})",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Salary =================
#         combined_entries.append({
#             'date': month_start,
#             'description': f"Salary : {employee.rda_emp_name}-{month_start.strftime('%b-%Y').lower()}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ================= Salary Deduction =================
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': month_end,
#                 'description': f"Salary Deduction ({absent_days} Absent Day)",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ==================================================
#     # SORT & RUNNING BALANCE
#     # ==================================================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ==================================================
#     # CONTEXT
#     # ==================================================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )


### -- ok----

# from decimal import Decimal
# from datetime import datetime, date, timedelta
# from calendar import monthrange
# from django.db.models import Count
# from num2words import num2words

# from hrm.models import RdaEmployee, Attendance, AdvancePayment, Allowances, LoanPayment, SalaryPayment
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render

# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # FIXED RULE: transaction = all → employee's first SalaryPayment → today
#     # ==================================================
#     if transaction_option == 'all':
#         first_salary = SalaryPayment.objects.filter(employee=employee).order_by('date').first()
#         fd = first_salary.date if first_salary else date(2025, 10, 1)
#         td = today

#     use_date_filter = (transaction_option == 'datewise')

#     # ==================================================
#     # MONTH RANGE
#     # ==================================================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ==================================================
#     # MONTH-WISE PROCESSING
#     # ==================================================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         # Attendance is labeled for the current month, date = last day of month
#         combined_entries.append({
#             'date': month_end,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         for allow in Allowances.objects.filter(
#             employee=employee, date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan =================
#         loans = LoanPayment.objects.filter(employee=employee)
#         loan_deduction = Decimal('0.00')
#         for loan in loans:
#             include_month = False
#             if loan.start_month and loan.end_month:
#                 include_month = loan.start_month.replace(day=1) <= month_start <= loan.end_month.replace(day=1)
#             if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
#                 include_month = True

#             if include_month:
#                 loan_deduction += loan.deduction_amount or Decimal('0.00')

#         # ================= SalaryPayment (Existing Records) =================
#         for sp in SalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"SalaryPayment ({sp.monthofsalary})",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Salary (Generated for Previous Month) =================
#         salary_payment_date = (month_end + timedelta(days=1))  # first day of next month
#         prev_month_name = month_start.strftime('%b-%Y').lower()
#         combined_entries.append({
#             'date': salary_payment_date,
#             'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ================= Salary Deduction (Absent Days) =================
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Salary Deduction ({absent_days} Absent Day) for {prev_month_name}",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#         # ================= Loan Deduction =================
#         if loan_deduction > 0:
#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Loan Deduction ({loan_deduction} TK) for {prev_month_name}",
#                 'payment': loan_deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ==================================================
#     # SORT & RUNNING BALANCE
#     # ==================================================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ==================================================
#     # CONTEXT
#     # ==================================================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )





# from decimal import Decimal
# from datetime import datetime, date, timedelta
# from calendar import monthrange
# from django.db.models import Count
# from num2words import num2words

# from hrm.models import RdaEmployee, Attendance, AdvancePayment, Allowances, LoanPayment, SalaryPayment

# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # FIXED RULE: transaction = all → employee's first SalaryPayment → today
#     # ==================================================
#     if transaction_option == 'all':
#         first_salary = SalaryPayment.objects.filter(employee=employee).order_by('date').first()
#         fd = first_salary.date if first_salary else date(2025, 10, 1)
#         td = today

#     use_date_filter = (transaction_option == 'datewise')

#     # ==================================================
#     # MONTH RANGE
#     # ==================================================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     # Ensure we do not include future months
#     td = min(td, today)
#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ==================================================
#     # MONTH-WISE PROCESSING
#     # ==================================================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

#         # SKIP CURRENT MONTH (only process fully passed months)
#         if month_end >= today:
#             continue

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         prev_month_name = month_start.strftime('%b-%Y').lower()
#         salary_payment_date = month_end + timedelta(days=1)  # first day of next month

#         # ================= Previous Month Salary =================
#         combined_entries.append({
#             'date': salary_payment_date,
#             'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ================= Existing Salary Payments =================
#         for sp in SalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         combined_entries.append({
#             'date': month_end,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         # for allow in Allowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#         #     combined_entries.append({
#         #         'date': allow.date,
#         #         'description': allow.reason,
#         #         'payment': None,
#         #         'received': allow.amount,
#         #         'cheque_number': allow.cheque_number or '-',
#         #         'source': 'allowance',
#         #     })
        
#         for allow in Allowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan Deduction =================
#         loans = LoanPayment.objects.filter(employee=employee)
#         loan_deduction = Decimal('0.00')
#         for loan in loans:
#             include_month = False
#             if loan.start_month and loan.end_month:
#                 include_month = loan.start_month.replace(day=1) <= month_start <= loan.end_month.replace(day=1)
#             if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
#                 include_month = True

#             if include_month:
#                 loan_deduction += loan.deduction_amount or Decimal('0.00')

#         if loan_deduction > 0:
#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Loan Deduction ({loan_deduction} TK) for {prev_month_name}",
#                 'payment': loan_deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#         # ================= Salary Deduction (Absent Days) =================
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Salary Deduction ({absent_days} Absent Day) for {prev_month_name}",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ==================================================
#     # SORT & RUNNING BALANCE
#     # ==================================================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ==================================================
#     # CONTEXT
#     # ==================================================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )





from decimal import Decimal
from datetime import datetime, date, timedelta
from calendar import monthrange
from django.db.models import Count
from num2words import num2words

from hrm.models import RdaEmployee, Attendance, AdvancePayment, Allowances, LoanPayment, SalaryPayment

@login_required
def employee_ledger_manage_pdf(request):
    type_param = request.GET.get('type')
    employee_id = request.GET.get('employee_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'all')

    def try_parse_date(val):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except:
            return None

    fd = try_parse_date(from_date)
    td = try_parse_date(to_date)

    employee = RdaEmployee.objects.filter(id=employee_id).first()
    if not employee:
        return render(request, 'reportmanage/employee_ledger_report_print.html', {})

    today = date.today()
    #salary_amount = employee.rda_salary or Decimal('0.00')
    salary_amount = RdaPayEmpSalary.objects.filter(
        rda_emp_name=employee,
        pay_date__range=(fd, td)
    ).aggregate(total=Sum('rda_pay_salary'))['total'] or Decimal('0.00')

    # ==================================================
    # FIXED RULE: transaction = all → employee's first SalaryPayment → today
    # ==================================================
    if transaction_option == 'all':
        first_salary = SalaryPayment.objects.filter(employee=employee).order_by('date').first()
        fd = first_salary.date if first_salary else date(2025, 10, 1)
        td = today

    use_date_filter = (transaction_option == 'datewise')

    # ==================================================
    # MONTH RANGE
    # ==================================================
    def month_range(start, end):
        months = []
        cur = start.replace(day=1)
        while cur <= end:
            months.append(cur)
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
        return months

    # Ensure we do not include future months
    td = min(td, today)
    months_list = month_range(fd, td)

    combined_entries = []
    attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

    # ==================================================
    # MONTH-WISE PROCESSING
    # ==================================================
    for month_start in months_list:
        month_end = month_start.replace(
            day=monthrange(month_start.year, month_start.month)[1]
        )

        # SKIP CURRENT MONTH (only process fully passed months)
        if month_end >= today:
            continue

        range_start = month_start
        range_end = month_end

        if use_date_filter:
            if fd:
                range_start = max(fd, month_start)
            if td:
                range_end = min(td, month_end)

        prev_month_name = month_start.strftime('%b-%Y').lower()
        salary_payment_date = month_end + timedelta(days=1)  # first day of next month

        # ================= Previous Month Salary =================
        combined_entries.append({
            'date': salary_payment_date,
            'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
            'payment': None,
            'received': salary_amount.quantize(Decimal('0.01')),
            'cheque_number': 'N/A',
            'source': 'salary',
        })

        # ================= Existing Salary Payments =================
        for sp in SalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
            combined_entries.append({
                'date': sp.date,
                'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
                'payment': sp.amount,
                'received': None,
                'cheque_number': sp.cheque_number or '-',
                'source': 'salary_payment',
            })

        # ================= Attendance =================
        month_attendance = Attendance.objects.filter(
            employee=employee,
            date__range=(range_start, range_end)
        )

        att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
        month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

        for row in att_summary:
            month_att[row['att_status']] = row['c']
            attendance_counts[row['att_status']] += row['c']

        combined_entries.append({
            'date': month_end,
            'description': (
                f"Attendance ({month_start.strftime('%B %Y')}) | "
                f"P:{month_att['Present']} "
                f"A:{month_att['Absent']} "
                f"L:{month_att['Leave']} "
                f"O:{month_att['Off Day']}"
            ),
            'payment': None,
            'received': None,
            'cheque_number': '-',
            'source': 'attendance'
        })

        # ================= Advances =================
        for adv in AdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
            combined_entries.append({
                'date': adv.date,
                'description': adv.reason,
                'payment': adv.amount,
                'received': None,
                'cheque_number': adv.cheque_number or '-',
                'source': 'advance',
            })

        # ================= Allowances =================
        # for allow in Allowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
        #     combined_entries.append({
        #         'date': allow.date,
        #         'description': allow.reason,
        #         'payment': None,
        #         'received': allow.amount,
        #         'cheque_number': '-',
        #         'source': 'allowance',
        #     })

        # ================= Loan Deduction =================
        loans = LoanPayment.objects.filter(employee=employee)
        loan_deduction = Decimal('0.00')
        for loan in loans:
            include_month = False
            if loan.start_month and loan.end_month:
                include_month = loan.start_month.replace(day=1) <= month_start <= loan.end_month.replace(day=1)
            if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
                include_month = True

            if include_month:
                loan_deduction += loan.deduction_amount or Decimal('0.00')

        if loan_deduction > 0:
            combined_entries.append({
                'date': salary_payment_date,
                'description': f"Loan Deduction ({loan_deduction} TK) for {prev_month_name}",
                'payment': loan_deduction,
                'received': None,
                'cheque_number': '-',
                'source': 'deduction',
            })

        # ================= Salary Deduction (Absent Days) =================
        total_days = month_attendance.count()
        absent_days = month_att['Absent']

        if total_days > 0 and absent_days > 0:
            per_day_salary = salary_amount / total_days
            deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

            combined_entries.append({
                'date': salary_payment_date,
                'description': f"Salary Deduction ({absent_days} Absent Day) for {prev_month_name}",
                'payment': deduction,
                'received': None,
                'cheque_number': '-',
                'source': 'deduction',
            })

    # ==================================================
    # SORT & RUNNING BALANCE
    # ==================================================
    combined_entries.sort(key=lambda x: x['date'])

    balance = Decimal('0.00')
    for e in combined_entries:
        balance += (e['received'] or 0) - (e['payment'] or 0)
        e['balance'] = balance

    total_received = sum(e['received'] or 0 for e in combined_entries)
    total_payment = sum(e['payment'] or 0 for e in combined_entries)
    final_balance = total_received - total_payment

    # ==================================================
    # CONTEXT
    # ==================================================
    context = {
        'entry_data': combined_entries,
        'employee': employee,
        'attendance_counts': attendance_counts,
        'print_time': datetime.now(),
        'total_received': total_received,
        'total_payment': total_payment,
        'final_balance': final_balance,
        'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
        'selected_filters': {
            'type': type_param,
            'employee_name': employee.rda_emp_name,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    }

    return render(
        request,
        'reportmanage/employee_ledger_report_print.html',
        context
    )
    
    

# from decimal import Decimal
# from datetime import datetime, date, timedelta
# from calendar import monthrange
# from django.db.models import Count
# from num2words import num2words


# from hrm.models import RdaEmployee, Attendance, AdvancePayment, Allowances, LoanPayment, SalaryPayment
# from decimal import Decimal, ROUND_HALF_UP

        
# @login_required
# def employee_ledger_manage_pdf(request):
#     type_param = request.GET.get('type')
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     employee = RdaEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'reportmanage/employee_ledger_report_print.html', {})

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # FIXED RULE: transaction = all → employee's first SalaryPayment → today
#     # ==================================================
#     if transaction_option == 'all':
#         first_salary = SalaryPayment.objects.filter(employee=employee).order_by('date').first()
#         fd = first_salary.date if first_salary else date(2025, 10, 1)
#         td = today

#     use_date_filter = (transaction_option == 'datewise')

#     # ==================================================
#     # MONTH RANGE
#     # ==================================================
#     def month_range(start, end):
#         months = []
#         cur = start.replace(day=1)
#         while cur <= end:
#             months.append(cur)
#             if cur.month == 12:
#                 cur = cur.replace(year=cur.year + 1, month=1)
#             else:
#                 cur = cur.replace(month=cur.month + 1)
#         return months

#     # Ensure we do not include future months
#     td = min(td, today)
#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ==================================================
#     # MONTH-WISE PROCESSING
#     # ==================================================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

#         # SKIP CURRENT MONTH (only process fully passed months)
#         if month_end >= today:
#             continue

#         range_start = month_start
#         range_end = month_end

#         if use_date_filter:
#             if fd:
#                 range_start = max(fd, month_start)
#             if td:
#                 range_end = min(td, month_end)

#         prev_month_name = month_start.strftime('%b-%Y').lower()
#         salary_payment_date = month_end + timedelta(days=1)  # first day of next month

#         # ================= Previous Month Salary =================
#         combined_entries.append({
#             'date': salary_payment_date,
#             'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ================= Existing Salary Payments =================
#         def to_two_decimal(v):
#             try:
#                 return Decimal(str(v or 0)).quantize(
#                     Decimal("0.00"),
#                     rounding=ROUND_HALF_UP
#                 )
#             except:
#                 return Decimal("0.00")
        
#         salary_entries = RdaPayEmpSalary.objects.filter(
#             rda_emp_name=employee,
#             pay_date__range=(range_start, range_end)
#         ).order_by("pay_date")
        
#         for sp in salary_entries:
        
#             combined_entries.append({
#                 'date': sp.pay_date,
#                 'description': sp.project_name.project_first_name if sp.project_name else "Salary Payment",
#                 'payment': None,   # credit side
#                 'received': to_two_decimal(sp.rda_pay_salary),
#                 'cheque_number': '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Attendance =================
#         month_attendance = Attendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))
#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             month_att[row['att_status']] = row['c']
#             attendance_counts[row['att_status']] += row['c']

#         combined_entries.append({
#             'date': month_end,
#             'description': (
#                 f"Attendance ({month_start.strftime('%B %Y')}) | "
#                 f"P:{month_att['Present']} "
#                 f"A:{month_att['Absent']} "
#                 f"L:{month_att['Leave']} "
#                 f"O:{month_att['Off Day']}"
#             ),
#             'payment': None,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'attendance'
#         })

#         # ================= Advances =================
#         for adv in AdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         # for allow in Allowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#         #     combined_entries.append({
#         #         'date': allow.date,
#         #         'description': allow.reason,
#         #         'payment': None,
#         #         'received': allow.amount,
#         #         'cheque_number': allow.cheque_number or '-',
#         #         'source': 'allowance',
#         #     })
        
#         for allow in Allowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan Deduction =================
#         loans = LoanPayment.objects.filter(employee=employee)
#         loan_deduction = Decimal('0.00')
#         for loan in loans:
#             include_month = False
#             if loan.start_month and loan.end_month:
#                 include_month = loan.start_month.replace(day=1) <= month_start <= loan.end_month.replace(day=1)
#             if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
#                 include_month = True

#             if include_month:
#                 loan_deduction += loan.deduction_amount or Decimal('0.00')

#         if loan_deduction > 0:
#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Loan Deduction ({loan_deduction} TK) for {prev_month_name}",
#                 'payment': loan_deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#         # ================= Salary Deduction (Absent Days) =================
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Salary Deduction ({absent_days} Absent Day) for {prev_month_name}",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ==================================================
#     # SORT & RUNNING BALANCE
#     # ==================================================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ==================================================
#     # CONTEXT
#     # ==================================================
#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#         'selected_filters': {
#             'type': type_param,
#             'employee_name': employee.rda_emp_name,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(
#         request,
#         'reportmanage/employee_ledger_report_print.html',
#         context
#     )







@login_required
def invStock_ledger_list(request):
    # Your existing data fetching and processing...
    purchases = Inventories.objects.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'purch_date'
    ).annotate(
        purchase_qty=Coalesce(Sum('qty'), 0)
    )

    usages = InventoryUse.objects.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'use_date'
    ).annotate(
        use_qty=Coalesce(Sum('qty'), 0)
    )

    data = []
    for p in purchases:
        data.append({
            'project_name': p['project_name__project_first_name'],
            'project_id': p['project_name_id'],
            'date': p['purch_date'],
            'item_name': p['item_name__head_requi_name'],
            'purchase_qty': p['purchase_qty'],
            'use_qty': 0,
        })

    for u in usages:
        data.append({
            'project_name': u['project_name__project_first_name'],
            'project_id': u['project_name_id'],
            'date': u['use_date'],
            'item_name': u['item_name__head_requi_name'],
            'purchase_qty': 0,
            'use_qty': u['use_qty'],
        })

    # Sort data by project, date, and item
    data.sort(key=lambda x: (
        x['project_name'],
        x['date'] if x['date'] is not None else date.min,
        x['item_name']
    ))

    # Calculate running balance per project + item
    balances = {}
    for row in data:
        key = (row['project_name'], row['item_name'])
        prev_balance = balances.get(key, 0)
        balance = prev_balance + row['purchase_qty'] - row['use_qty']
        row['balance_qty'] = balance
        balances[key] = balance

    # Calculate total sums for the whole dataset
    total_purchase = sum(row['purchase_qty'] for row in data)
    total_use = sum(row['use_qty'] for row in data)
    total_balance = sum(row['balance_qty'] for row in data)

    context = {
        'summary': data,
        'print_time': now(),
        'total_purchase': total_purchase,
        'total_use': total_use,
        'total_balance': total_balance,
    }

    return render(request, 'invstockreport/invStock_ledger_list.html', context)




@login_required
def invStock_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    context = {
        'projectNames': projectName,
        'today': date.today(),
    }
    return render(request, 'invstockreport/invStock_ledger_manage.html', context)
    
    

@login_required
def invStock_ledger_report(request):
    project_id = request.GET.get('project')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')  # <-- included

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date_str)
    td = parse_date(to_date_str)

    # Start with all purchases
    purchases_qs = Inventories.objects.all()
    if project_id:
        purchases_qs = purchases_qs.filter(project_name_id=project_id)
    if transaction_option == 'datewise':
        if fd:
            purchases_qs = purchases_qs.filter(purch_date__gte=fd)
        if td:
            purchases_qs = purchases_qs.filter(purch_date__lte=td)

    purchases = purchases_qs.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'purch_date'
    ).annotate(
        purchase_qty=Coalesce(Sum('qty'), 0)
    )

    # Start with all usages
    usages_qs = InventoryUse.objects.all()
    if project_id:
        usages_qs = usages_qs.filter(project_name_id=project_id)
    if transaction_option == 'datewise':
        if fd:
            usages_qs = usages_qs.filter(use_date__gte=fd)
        if td:
            usages_qs = usages_qs.filter(use_date__lte=td)

    usages = usages_qs.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'use_date'
    ).annotate(
        use_qty=Coalesce(Sum('qty'), 0)
    )

    # Combine purchases and usages
    data = []
    for p in purchases:
        data.append({
            'project_name': p['project_name__project_first_name'],
            'project_id': p['project_name_id'],
            'date': p['purch_date'],
            'item_name': p['item_name__head_requi_name'],
            'purchase_qty': p['purchase_qty'],
            'use_qty': 0,
        })

    for u in usages:
        data.append({
            'project_name': u['project_name__project_first_name'],
            'project_id': u['project_name_id'],
            'date': u['use_date'],
            'item_name': u['item_name__head_requi_name'],
            'purchase_qty': 0,
            'use_qty': u['use_qty'],
        })

    # Sort by project, date, item name
    data.sort(key=lambda x: (
        x['project_name'],
        x['date'] if x['date'] is not None else date.min,
        x['item_name']
    ))

    # Running balance per (project, item)
    balances = {}
    for row in data:
        key = (row['project_name'], row['item_name'])
        prev_balance = balances.get(key, 0)
        balance = prev_balance + row['purchase_qty'] - row['use_qty']
        row['balance_qty'] = balance
        balances[key] = balance

    # Totals
    total_purchase = sum(row['purchase_qty'] for row in data)
    total_use = sum(row['use_qty'] for row in data)
    total_balance = sum(row['balance_qty'] for row in data)

    context = {
        'summary': data,
        'print_time': now(),
        'total_purchase': total_purchase,
        'total_use': total_use,
        'total_balance': total_balance,
        'filters': {
            'project': project_id,
            'from_date': from_date_str,
            'to_date': to_date_str,
            'transaction': transaction_option,
        }
    }

    return render(request, 'invstockreport/invStock_ledger_report.html', context)





@login_required
def invStock_ledger_manage_pdf(request):
    project_id = request.GET.get('project')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except Exception:
            return None

    fd = parse_date(from_date_str)
    td = parse_date(to_date_str)

    # Purchase queryset
    purchases_qs = Inventories.objects.all()
    if project_id:
        purchases_qs = purchases_qs.filter(project_name_id=project_id)
    if transaction_option == 'datewise':
        if fd:
            purchases_qs = purchases_qs.filter(purch_date__gte=fd)
        if td:
            purchases_qs = purchases_qs.filter(purch_date__lte=td)

    purchases = purchases_qs.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'purch_date'
    ).annotate(
        purchase_qty=Coalesce(Sum('qty'), 0)
    )

    # Usage queryset
    usages_qs = InventoryUse.objects.all()
    if project_id:
        usages_qs = usages_qs.filter(project_name_id=project_id)
    if transaction_option == 'datewise':
        if fd:
            usages_qs = usages_qs.filter(use_date__gte=fd)
        if td:
            usages_qs = usages_qs.filter(use_date__lte=td)

    usages = usages_qs.values(
        'project_name__project_first_name',
        'project_name_id',
        'item_name__head_requi_name',
        'use_date'
    ).annotate(
        use_qty=Coalesce(Sum('qty'), 0)
    )

    # Merge purchases and usages
    data = []
    for p in purchases:
        # Get a sample remark for this group
        remark = Inventories.objects.filter(
            project_name_id=p['project_name_id'],
            item_name__head_requi_name=p['item_name__head_requi_name'],
            purch_date=p['purch_date']
        ).values_list('remark', flat=True).first() or ''

        data.append({
            'project_name': p['project_name__project_first_name'],
            'project_id': p['project_name_id'],
            'date': p['purch_date'],
            'item_name': p['item_name__head_requi_name'],
            'purchase_qty': p['purchase_qty'],
            'use_qty': 0,
            'remark': remark,
        })

    for u in usages:
        # Get a sample remark for this group
        remark = InventoryUse.objects.filter(
            project_name_id=u['project_name_id'],
            item_name__head_requi_name=u['item_name__head_requi_name'],
            use_date=u['use_date']
        ).values_list('details', flat=True).first() or ''

        data.append({
            'project_name': u['project_name__project_first_name'],
            'project_id': u['project_name_id'],
            'date': u['use_date'],
            'item_name': u['item_name__head_requi_name'],
            'purchase_qty': 0,
            'use_qty': u['use_qty'],
            'remark': remark,
        })

    # Sort records
    data.sort(key=lambda x: (
        x['project_name'],
        x['date'] if x['date'] else date.min,
        x['item_name']
    ))

    # Calculate balance per project + item
    balances = {}
    for row in data:
        key = (row['project_name'], row['item_name'])
        prev_balance = balances.get(key, 0)
        balance = prev_balance + row['purchase_qty'] - row['use_qty']
        row['balance_qty'] = balance
        balances[key] = balance

    # Totals
    total_purchase = sum(row['purchase_qty'] for row in data)
    total_use = sum(row['use_qty'] for row in data)
    total_balance = sum(row['balance_qty'] for row in data)

    # Convert amount to words
    def amount_to_words(amount):
        try:
            amount = float(amount)
            is_negative = amount < 0
            amount = abs(amount)

            integer_part = int(amount)
            fractional_part = int(round((amount - integer_part) * 100))

            from num2words import num2words
            words = num2words(integer_part, lang='en_IN').title().replace(",", "")
            words += " Taka"
            if fractional_part:
                words += f" and {num2words(fractional_part, lang='en_IN').title()} Paisa"
            words += " only"
            if is_negative:
                words = "- " + words
            return words
        except:
            return f"{amount} Taka only"

    context = {
        'summary': data,
        'print_time': now(),
        'total_purchase': total_purchase,
        'total_use': total_use,
        'total_balance': total_balance,
        'total_in_words': amount_to_words(total_balance),
        'filters': {
            'project': project_id,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    }

    return render(request, 'invstockreport/invStock_ledger_manage_pdf.html', context)
    
    
    
@login_required
def customer_summary_report(request):
    customers = Customer.objects.all()
    report_data = []

    for customer in customers:
        entries = LedgerEntry.objects.filter(type='Customer', customer_name=customer).order_by('date')

        if not entries.exists():
            continue  # Skip if no entries for this customer

        first_entry = entries.first()
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        balance = total_debit - total_credit

        report_data.append({
            'customer': customer,
            'project_name': first_entry.project_name.project_first_name if first_entry.project_name else '',
            'first_date': first_entry.date,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance': balance,
        })

    return render(request, 'reportmanage/customer_summary_report.html', {
        'report_data': report_data
    })



@login_required
def customer_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    head = HeadOfAccount.objects.all()
    form = LedgerFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  
    cashTypes = CashType.objects.all()
    
    context = {
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'reportmanage/customer_ledger_manage.html', context)





from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def customer_ledger_report(request):
    customer_id = request.GET.get('customer_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null', 'None']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Filter customers
    customers = Customer.objects.filter(id=customer_id) if is_valid(customer_id) else Customer.objects.all()

    report_data = []

    for customer in customers:
        # Fetch property sales and ledger entries
        sales_entries = PropertySales.objects.filter(customer_name=customer).order_by('sales_date')
        ledger_entries = LedgerEntry.objects.filter(type='Customer', customer_name=customer).select_related('head', 'project_name').order_by('date')

        # Apply date filters
        if transaction_option == 'datewise':
            if fd:
                sales_entries = sales_entries.filter(sales_date__gte=fd)
                ledger_entries = ledger_entries.filter(date__gte=fd)
            if td:
                sales_entries = sales_entries.filter(sales_date__lte=td)
                ledger_entries = ledger_entries.filter(date__lte=td)

        combined_entries = []

        # 1. From Property Sales (DEBIT)
        for s in sales_entries:
            # Safely get sales debit value across common naming conventions
            debit_value = (
                getattr(s, 'sales_amount', None) or 
                getattr(s, 'sale_amount', None) or 
                getattr(s, 'total_amount', None) or 
                getattr(s, 'amount', 0)
            )

            # Build readable property string
            prop_info = []
            if getattr(s, 'property_name', None):
                prop_info.append(str(s.property_name))
            if getattr(s, 'flat_no', None) or getattr(s, 'unit_no', None):
                prop_info.append(f"({getattr(s, 'flat_no', '')}/{getattr(s, 'unit_no', '')})")
            
            desc = f"Property Sale: {' '.join(prop_info)}".strip()

            combined_entries.append({
                'type': 'Property Sale',
                'date': s.sales_date,
                'project_name': s.project_name.project_first_name if s.project_name else '',
                'head_name': 'Property Sale',  # Matching table column expectation
                'description': desc,
                'debit': float(debit_value or 0),
                'credit': 0.00
            })

        # 2. From LedgerEntry (CREDIT / RECEIPT)
        for e in ledger_entries:
            head_title = e.head.head_name if e.head else 'Customer Payment'
            
            combined_entries.append({
                'type': 'Ledger',
                'date': e.date,
                'project_name': e.project_name.project_first_name if e.project_name else '',
                'head_name': head_title,  # Matching table column expectation
                'description': e.description or '',
                'debit': float(e.debit or 0),
                'credit': float(e.credit or 0)
            })

        # Sort combined entries by date
        combined_entries.sort(key=lambda x: x['date'])

        if not combined_entries:
            continue

        # Calculate Totals
        total_debit = sum(e['debit'] for e in combined_entries)
        total_credit = sum(e['credit'] for e in combined_entries)
        balance = total_debit - total_credit

        # Main project name extraction
        project_title = combined_entries[0]['project_name'] if combined_entries else ''

        report_data.append({
            'customer': customer,
            'project_name': project_title,
            'first_date': combined_entries[0]['date'],
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance': balance,
            'entries': combined_entries
        })

    return render(request, 'reportmanage/customer_ledger_report.html', {
        'report_data': report_data,
        'filters': {
            'customer_id': customer_id,
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })
   


# from datetime import datetime
# from decimal import Decimal
# from num2words import num2words

# @login_required
# def customer_ledger_manage_pdf(request):
#     customer_id = request.GET.get('customer_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'datewise')

#     def is_valid(val):
#         return val not in [None, '', 'null']

#     def parse_date(val):
#         try:
#             return datetime.strptime(val, '%Y-%m-%d').date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # Filter customers
#     customers = Customer.objects.filter(id=customer_id) if is_valid(customer_id) else Customer.objects.all()

#     report_data = []

#     for customer in customers:
#         sales_entries = PropertySales.objects.filter(customer_name=customer)
#         ledger_entries = LedgerEntry.objects.filter(type='Customer', customer_name=customer)

#         if transaction_option == 'datewise':
#             if fd:
#                 sales_entries = sales_entries.filter(sales_date__gte=fd)
#                 ledger_entries = ledger_entries.filter(date__gte=fd)
#             if td:
#                 sales_entries = sales_entries.filter(sales_date__lte=td)
#                 ledger_entries = ledger_entries.filter(date__lte=td)

#         combined_entries = []

#         # Property Sales → DEBIT
#         for s in sales_entries:
#             combined_entries.append({
#                 'date': s.sales_date,
#                 'customer': customer.customer_name,
#                 'project': s.project_name.project_first_name if s.project_name else '-',
#                 'description': f'Property Sale: {s.property_name or ""} ({s.flat_no}/{s.unit_no})',
#                 'debit': s.sales_amount or Decimal('0.00'),
#                 'credit': Decimal('0.00'),
#             })

#         # Ledger Entries → CREDIT
#         for l in ledger_entries:
#             combined_entries.append({
#                 'date': l.date,
#                 'customer': customer.customer_name,
#                 'project': l.project_name.project_first_name if l.project_name else '-',
#                 'description': l.description or '',
#                 'debit': Decimal('0.00'),
#                 'credit': l.credit or Decimal('0.00'),
#             })

#         # Sort by date
#         combined_entries.sort(key=lambda x: x['date'])

#         # Running balance
#         running_balance = Decimal('0.00')
#         for row in combined_entries:
#             running_balance += row['debit'] - row['credit']
#             row['balance'] = running_balance

#         if combined_entries:
#             report_data.append({
#                 'customer_name': customer.customer_name,
#                 'project_name': combined_entries[0]['project'],  # first project for header
#                 'ledger_entries': combined_entries,
#                 'total_debit': sum(r['debit'] for r in combined_entries),
#                 'total_credit': sum(r['credit'] for r in combined_entries),
#                 'final_balance': running_balance,
#             })

#     def amount_to_words(amount):
#         try:
#             amount = float(amount)
#             if amount < 0:
#                 return "Minus " + num2words(abs(amount), lang='en').title() + " Taka"
#             return num2words(amount, lang='en').title() + " Taka"
#         except:
#             return "Invalid Amount"

#     context = {
#         'report_data': report_data,
#         'total_debit': sum(group['total_debit'] for group in report_data),
#         'total_credit': sum(group['total_credit'] for group in report_data),
#         'final_balance': sum(group['final_balance'] for group in report_data),
#         'balance_in_words': amount_to_words(sum(group['final_balance'] for group in report_data)),
#         'print_time': datetime.now(),
#         'selected_filters': {
#             'customer': customers.first().customer_name if is_valid(customer_id) else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'reportmanage/customer_ledger_manage_pdf.html', context)



from datetime import datetime
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from num2words import num2words

@login_required
def customer_ledger_manage_pdf(request):
    customer_id = request.GET.get('customer_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')

    def is_valid(val):
        return val not in [None, '', 'null', 'None']

    def parse_date(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    def to_decimal(val):
        if val is None:
            return Decimal('0.00')
        try:
            return Decimal(str(val))
        except:
            return Decimal('0.00')

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Filter customers
    customers = Customer.objects.filter(id=customer_id) if is_valid(customer_id) else Customer.objects.all()

    report_data = []

    for customer in customers:
        sales_entries = PropertySales.objects.filter(customer_name=customer)
        ledger_entries = LedgerEntry.objects.filter(type='Customer', customer_name=customer)

        # Apply date filters
        if transaction_option == 'datewise':
            if fd:
                sales_entries = sales_entries.filter(sales_date__gte=fd)
                ledger_entries = ledger_entries.filter(date__gte=fd)
            if td:
                sales_entries = sales_entries.filter(sales_date__lte=td)
                ledger_entries = ledger_entries.filter(date__lte=td)

        combined_entries = []

        # Property Sales → DEBIT
        for s in sales_entries:
            # Check sales_amount or alternative model field names
            raw_debit = (
                getattr(s, 'sales_amount', None) or 
                getattr(s, 'sale_amount', None) or 
                getattr(s, 'total_amount', None) or 
                getattr(s, 'amount', None)
            )
            debit_val = to_decimal(raw_debit)

            # Build detailed description
            prop_info = []
            if getattr(s, 'property_name', None):
                prop_info.append(str(s.property_name))
            flat_no = getattr(s, 'flat_no', '') or ''
            unit_no = getattr(s, 'unit_no', '') or ''
            if flat_no or unit_no:
                prop_info.append(f"({flat_no}/{unit_no})")

            desc = f"Property Sale: {' '.join(prop_info)}".strip()

            combined_entries.append({
                'date': s.sales_date,
                'customer': customer.customer_name,
                'project': s.project_name.project_first_name if getattr(s, 'project_name', None) else '-',
                'description': desc,
                'debit': debit_val,
                'credit': Decimal('0.00'),
            })

        # Ledger Entries → CREDIT
        for l in ledger_entries:
            combined_entries.append({
                'date': l.date,
                'customer': customer.customer_name,
                'project': l.project_name.project_first_name if getattr(l, 'project_name', None) else '-',
                'description': l.description or '',
                'debit': to_decimal(getattr(l, 'debit', 0)),
                'credit': to_decimal(getattr(l, 'credit', 0)),
            })

        if not combined_entries:
            continue

        # Sort by date
        combined_entries.sort(key=lambda x: x['date'])

        # Calculate Running Balance
        running_balance = Decimal('0.00')
        for row in combined_entries:
            running_balance += row['debit'] - row['credit']
            row['balance'] = running_balance

        total_group_debit = sum((r['debit'] for r in combined_entries), Decimal('0.00'))
        total_group_credit = sum((r['credit'] for r in combined_entries), Decimal('0.00'))

        report_data.append({
            'customer_name': customer.customer_name,
            'project_name': combined_entries[0]['project'],  # first project for header
            'ledger_entries': combined_entries,
            'total_debit': total_group_debit,
            'total_credit': total_group_credit,
            'final_balance': running_balance,
        })

    def amount_to_words(amount):
        try:
            amt_float = float(amount)
            if amt_float < 0:
                return "Minus " + num2words(abs(amt_float), lang='en').title() + " Taka"
            return num2words(amt_float, lang='en').title() + " Taka"
        except:
            return "Zero Taka"

    grand_total_debit = sum((group['total_debit'] for group in report_data), Decimal('0.00'))
    grand_total_credit = sum((group['total_credit'] for group in report_data), Decimal('0.00'))
    grand_final_balance = grand_total_debit - grand_total_credit

    # Determine filter customer display text safely
    selected_customer_name = "All"
    if is_valid(customer_id) and customers.exists():
        selected_customer_name = customers.first().customer_name
        
    def amount_to_words(amount):
        try:
            amt_decimal = Decimal(str(amount))
            if amt_decimal == 0:
                return "Zero Taka Only"
    
            prefix = "Minus " if amt_decimal < 0 else ""
            abs_amt = abs(amt_decimal)
    
            # Split whole taka and paisa/poisha
            taka = int(abs_amt)
            paisa = int(round((abs_amt - taka) * 100))
    
            # lang='en_IN' uses Lakh and Crore naming conventions
            taka_words = num2words(taka, lang='en_IN').title()
            result = f"{prefix}{taka_words} Taka"
    
            if paisa > 0:
                paisa_words = num2words(paisa, lang='en_IN').title()
                result += f" And {paisa_words} Poisha"
    
            return result + " Only"
        except Exception as e:
            return "Zero Taka Only"

    context = {
        'report_data': report_data,
        'total_debit': grand_total_debit,
        'total_credit': grand_total_credit,
        'final_balance': grand_final_balance,
        'balance_in_words': amount_to_words(grand_final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'customer': selected_customer_name,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    }

    return render(request, 'reportmanage/customer_ledger_manage_pdf.html', context)
    
    

## Trail Balance reports----
@login_required
def trial_balance_list(request):
    entries = LedgerEntry.objects.all().order_by('-date', '-id')
    form = LedgerReportForm()
    
    balance = Decimal('0.00')
    entry_data = []

    for entry in entries:
        debit = entry.debit or Decimal('0.00')
        credit = entry.credit or Decimal('0.00')

        # Calculate running balance (credit - debit)
        balance += credit - debit

        entry_data.append({
            'entry': entry,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    return render(request, 'trailbalance/trial_balance_list.html', {
        'form': form,
        'entry_data': entry_data
    })

    
    

@login_required
def trial_balance_ledger_manage(request):
    projectNames = ProjectFirstLevelName.objects.all()
    headNames = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()
    form = LedgerFilterForm(request.GET or None)

    context = {
        'projectNames': projectNames,
        'headNames': headNames,
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'trailbalance/trial_balance_ledger_manage.html', context)





@login_required
def trial_balance_ledger_report(request):    
    head_type = request.GET.get('head') 
    type_value_id = request.GET.get('head_value') 
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'datewise')  

    def is_valid(value):
        return value is not None and value != ''

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    entries = LedgerEntry.objects.all()
   
    if is_valid(type_value_id):
        entries = entries.filter(head_id=type_value_id)
   
    if transaction_option == 'datewise':
        if fd:
            entries = entries.filter(date__gte=fd)
        if td:
            entries = entries.filter(date__lte=td)  
    

    entries = entries.order_by('date', 'id')
   
    balance = Decimal('0.00')
    entry_data = []
  
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    # Dropdown data
    projectNames = ProjectFirstLevelName.objects.all()
    heads = HeadOfAccount.objects.all()
    cashTypes = CashType.objects.all()

    return render(request, 'trailbalance/trial_balance_ledger_report.html', {
        'entry_data': entry_data,
        'projectNames': projectNames,
        'heads': heads,
        'cashTypes': cashTypes,
        'selected_filters': {
            'from_date': from_date,
            'to_date': to_date,
            'head': head_type,
            'transaction': transaction_option,
        }
    })



@login_required
def trial_balance_ledger_manage_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    project_id = request.GET.get("project", "")
    vendor_id = request.GET.get("vendor", "")

    from datetime import datetime
    from decimal import Decimal
    from django.db.models import Q, Sum

    def is_valid(v):
        return v is not None and v != ""

    def parse_date(v):
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    if not fd or not td:
        fd = td = datetime.today().date()

    project_obj = ProjectFirstLevelName.objects.filter(id=project_id).first() if is_valid(project_id) else None
    vendor_obj = Vendor.objects.filter(id=vendor_id).first() if is_valid(vendor_id) else None

    # ================= MAIN LEDGER (EXCLUDE EMPLOYEE) =================
    ledger_filters = Q(date__gte=fd, date__lte=td)

    if project_obj:
        ledger_filters &= Q(project_name=project_obj)

    if vendor_obj:
        ledger_filters &= (
            Q(vendor=vendor_obj) |
            Q(customer_name__id=vendor_obj.id) |
            Q(contructor__id=vendor_obj.id) |
            Q(bankName__id=vendor_obj.id)
        )

    # Exclude employee from main ledger loop
    ledger_entries = LedgerEntry.objects.filter(ledger_filters).exclude(type="Employee").order_by("type")

    # ================= EMPLOYEE LEDGER (for DEBIT only) =================
    employee_ledger_filters = Q(type="Employee", date__gte=fd, date__lte=td)
    if project_obj:
        employee_ledger_filters &= Q(project_name=project_obj)

    employee_ledger_entries = LedgerEntry.objects.filter(employee_ledger_filters)

    # ================= TRANSFERS =================
    trf_filters = Q(transfer_date__gte=fd, transfer_date__lte=td)
    if project_obj:
        trf_filters &= Q(project_name=project_obj)

    transfers = BalanceTransfer.objects.filter(trf_filters)

    cash_type_summary = (
        LedgerEntry.objects.filter(
            cash_type__isnull=False,
            date__gte=fd,
            date__lte=td,
        )
        .exclude(cash_type__cash_type_name="No_Method")
        .values("cash_type__id", "cash_type__cash_type_name")
        .annotate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit"),
            balance=Sum("credit") - Sum("debit"),
        )
        .order_by("cash_type__cash_type_name")
    )

    data_by_type = {}
    totals = {"debit": 0, "credit": 0, "balance": 0}

    def safe_id_name(obj, default_name=None):
        if obj is None:
            return None, default_name or "N/A"
        if hasattr(obj, "id"):
            return getattr(obj, "id"), str(obj)
        return None, str(obj)

    # ================= NORMAL LEDGER (NON-EMPLOYEE) =================
    for entry in ledger_entries:
        type_key = entry.type or "Others"

        if type_key not in data_by_type:
            data_by_type[type_key] = {}

        acc_id = None
        name = "N/A"

        if entry.type == "Vendor":
            acc_id, name = safe_id_name(entry.vendor, getattr(entry.vendor, "supplier_name", str(entry.vendor)))

        elif entry.type == "Customer":
            acc_id, name = safe_id_name(entry.customer_name, getattr(entry.customer_name, "customer_name", str(entry.customer_name)))

        elif entry.type == "Contructor":
            acc_id, name = safe_id_name(entry.contructor, getattr(entry.contructor, "supervisor_name", str(entry.contructor)))

        elif entry.type == "Bank":
            acc_id, name = safe_id_name(entry.bankName, getattr(entry.bankName, "cash_type_name", str(entry.bankName)))

        elif entry.type == "Capital":
            acc_id, name = safe_id_name(entry.capi_name, getattr(entry.capi_name, "person_name", str(entry.capi_name)))

        elif entry.type == "Investment":
            acc_id, name = safe_id_name(entry.invest_name, getattr(entry.invest_name, "person_name", str(entry.invest_name)))

        elif entry.type == "Expense":
            acc_id, name = safe_id_name(entry.exp_name, getattr(entry.exp_name, "head_exp_name", str(entry.exp_name)))

            # exclude bill
            if "EXC-00031" in str(name):
                continue

        else:
            acc_id, name = None, entry.type_name or "N/A"

        if name not in data_by_type[type_key]:
            data_by_type[type_key][name] = {
                "id": acc_id,
                "name": name,
                "debit": 0,
                "credit": 0,
                "balance": 0,
            }

        data_by_type[type_key][name]["debit"] += entry.debit or 0
        data_by_type[type_key][name]["credit"] += entry.credit or 0
        data_by_type[type_key][name]["balance"] = (
            data_by_type[type_key][name]["debit"]
            - data_by_type[type_key][name]["credit"]
        )

        totals["debit"] += entry.debit or 0
        totals["credit"] += entry.credit or 0

    # =====================================================================
    # ================= EMPLOYEE SECTION (FULL REBUILT) ===================
    # =====================================================================
    # STEP 1: Get ALL employees from RdaPayEmpSalary in date range
    #         → Credit = sum of rda_pay_salary
    # STEP 2: Add debit from LedgerEntry (type=Employee) for each employee
    # STEP 3: Calculate balance
    # =====================================================================

    from decimal import Decimal
    from django.db.models import Sum, Q
    
    
    # ==========================================================
    # SAFE DECIMAL FUNCTION (MUST BE TOP OF FILE)
    # ==========================================================
    def to_two_decimal(v):
        try:
            return Decimal(str(v or 0)).quantize(Decimal("0.00"))
        except:
            return Decimal("0.00")
    
    
    # ==========================================================
    # EMPLOYEE SECTION
    # ==========================================================
    
    employee_type_key = "Employee"
    data_by_type[employee_type_key] = {}
    
    totals.setdefault("credit", Decimal("0.00"))
    totals.setdefault("debit", Decimal("0.00"))
    
    
    # ==========================================================
    # EMPLOYEE SALARY CREDIT SECTION
    # ==========================================================
    
    salary_filters = Q(pay_date__gte=fd, pay_date__lte=td)
    
    if project_obj:
        salary_filters &= Q(project_name=project_obj)
    
    salary_qs = (
        RdaPayEmpSalary.objects
        .filter(salary_filters)
        .select_related("rda_emp_name")
    )
    
    salary_map = {}
    
    for row in salary_qs:
    
        if not row.rda_emp_name:
            continue
    
        emp_id = row.rda_emp_name.id
        emp_name = row.rda_emp_name.rda_emp_name
    
        pay_amount = to_two_decimal(row.rda_pay_salary)
    
        if emp_id not in salary_map:
            salary_map[emp_id] = {
                "id": emp_id,
                "name": emp_name,
                "credit": Decimal("0.00")
            }
    
        salary_map[emp_id]["credit"] += pay_amount
    
    
    # ==========================================================
    # PUSH INTO FINAL DATA STRUCTURE
    # ==========================================================
    
    for emp_id, data in salary_map.items():
    
        credit_value = to_two_decimal(data["credit"])
    
        data_by_type[employee_type_key][emp_id] = {
            "id": emp_id,
            "name": data["name"],
            "debit": Decimal("0.00"),
            "credit": credit_value,
            "balance": Decimal("0.00"),
        }
    
        totals["credit"] += credit_value
    
    
    # ==========================================================
    # STEP 2: DEBIT (LEDGER ENTRY)
    # ==========================================================
    for entry in employee_ledger_entries:
    
        debit_amount = to_two_decimal(entry.debit)
    
        acc_id, name = safe_id_name(entry.empl_name, str(entry.empl_name))
    
        emp_obj = None
    
        if hasattr(entry.empl_name, "id") and entry.empl_name.id:
            emp_obj = RdaEmployee.objects.filter(id=entry.empl_name.id).first()
    
        if emp_obj is None:
            emp_obj = RdaEmployee.objects.filter(
                rda_emp_name=str(entry.empl_name)
            ).first()
    
        if emp_obj:
            emp_id = emp_obj.id
            emp_name = emp_obj.rda_emp_name
        else:
            emp_id = acc_id
            emp_name = name
    
        if emp_id not in data_by_type[employee_type_key]:
            data_by_type[employee_type_key][emp_id] = {
                "id": emp_id,
                "name": emp_name,
                "debit": Decimal("0.00"),
                "credit": Decimal("0.00"),
                "balance": Decimal("0.00"),
            }
    
        data_by_type[employee_type_key][emp_id]["debit"] += debit_amount
        totals["debit"] += debit_amount
    
    
    # ==========================================================
    # STEP 3: BALANCE CALCULATION
    # ==========================================================
    for emp_id, row in data_by_type[employee_type_key].items():
    
        debit = to_two_decimal(row["debit"])
        credit = to_two_decimal(row["credit"])
    
        row["debit"] = debit
        row["credit"] = credit
        row["balance"] = debit - credit

    # ================= PURCHASE =================
    inv_filters = Q(purch_date__gte=fd, purch_date__lte=td)

    if project_obj:
        inv_filters &= Q(project_name=project_obj)

    if vendor_obj:
        inv_filters &= Q(vendor_name=vendor_obj)

    inventory_rows = (
        Inventories.objects.filter(inv_filters)
        .values("vendor_name__id", "vendor_name__supplier_name")
        .annotate(total_purchase=Sum("amount"))
    )

    if inventory_rows:
        vendor_type_key = "Vendor"

        if vendor_type_key not in data_by_type:
            data_by_type[vendor_type_key] = {}

        for row in inventory_rows:
            v_id = row["vendor_name__id"]
            v_name = row["vendor_name__supplier_name"] or "Unknown Vendor"

            purchase_amount = to_two_decimal(row["total_purchase"] or 0)

            if v_name not in data_by_type[vendor_type_key]:
                data_by_type[vendor_type_key][v_name] = {
                    "id": v_id,
                    "name": v_name,
                    "debit": Decimal("0.00"),
                    "credit": Decimal("0.00"),
                    "balance": Decimal("0.00"),
                }

            data_by_type[vendor_type_key][v_name]["credit"] += purchase_amount

    # If Employee section is empty, remove it
    if employee_type_key in data_by_type and not data_by_type[employee_type_key]:
        del data_by_type[employee_type_key]

    # ================= FINAL =================
    for key in data_by_type:
        data_by_type[key] = list(data_by_type[key].values())

    return render(request, "trailbalance/trial_balance_ledger_manage_pdf.html", {
        "data_by_type": data_by_type,
        "cash_type_summary": cash_type_summary,
        "from_date": fd,
        "to_date": td,
        "print_time": datetime.now(),
        "totals": totals,
    })
    
    
    




## Balance Sheet ------
@login_required
def balance_item_list(request):
    items = BalanceItem.objects.all().order_by('-date')
    headNames = BalanceSheetHead.objects.all()
    return render(request, 'accounting/balance_item_list.html', {'items': items, 'headNames': headNames})



@login_required
def balance_item_create(request):
    if request.method == "POST":
        form = BalanceItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('balance_item_list')
    else:
        form = BalanceItemForm()

    heads = BalanceSheetHead.objects.all()
    return render(request, 'accounting/balance_item_form.html', {'form': form, 'heads': heads})


@login_required
def balance_item_edit(request, pk):
    item = get_object_or_404(BalanceItem, pk=pk)
    if request.method == "POST":
        form = BalanceItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('balance_item_list')
    else:
        form = BalanceItemForm(instance=item)
    heads = BalanceSheetHead.objects.all()
    return render(request, 'accounting/balance_item_form.html', {'form': form, 'heads': heads})



@login_required
def balance_item_delete(request, pk):
    item = get_object_or_404(BalanceItem, pk=pk)
    item.delete()
    return redirect('balance_item_list')



@login_required
def balance_item_detail(request, pk):
    voucher = get_object_or_404(BalanceItem, pk=pk)
    amount_in_words = num2words(voucher.value, lang='en').title()  # convert to words
    print_time = timezone.now()
    return render(request, 'accounting/balance_item_detail.html', {
        'voucher': voucher,
        'amount_in_words': amount_in_words,
        'print_time': print_time
    })



@login_required
def approve_balance_item(request, pk):
    item = get_object_or_404(BalanceItem, pk=pk)
    item.status = 'Approved'
    item.save()
    return redirect('balance_item_detail', pk=pk)






# @login_required
# def balance_sheet_report(request):
#     # Get all unique dates (sorted)
#     dates = sorted(BalanceItem.objects.values_list("date", flat=True).distinct())
#     years = sorted(set(d.year for d in dates))

#     # Aggregate values
#     # items = BalanceItem.objects.values(
#     #     "head__head_name", "type_name", "name", "date"
#     # ).annotate(total=Sum("value")).order_by("head__head_name", "type_name", "name", "date")
    
#     items = (
#         BalanceItem.objects.filter(status="Approved")
#         .values("head__head_name", "type_name", "name", "date")
#         .annotate(total=Sum("value"))
#         .order_by("head__head_name", "type_name", "name", "date")
#     )


#     # Build grouped data
#     grouped = {}
#     totals = [0 for _ in years]  # overall grand totals
#     for i in items:
#         head_name = i["head__head_name"]
#         type_name = i["type_name"] or "General"
#         name = i["name"]
#         year = i["date"].year

#         head_group = grouped.setdefault(head_name, {})
#         type_group = head_group.setdefault(type_name, {})
#         values_list = type_group.setdefault(name, [0 for _ in years])

#         idx = years.index(year)
#         values_list[idx] += i["total"]
#         totals[idx] += i["total"]

#     context = {
#         "company_name": "BTP Limited",
#         "currency": "BDT",
#         "grouped": grouped,
#         "years": years,
#         "totals": totals,
#         "print_time": now(),
#     }
#     return render(request, "accounting/balance_sheet_report.html", context)




from django.db.models import Sum
from django.utils.timezone import now
from .models import BalanceItem, ProjectFirstLevelName
from datetime import datetime

@login_required
def balance_sheet_report(request):
    # Get filter parameters
    project_id = request.GET.get("project")  # project filter
    month = request.GET.get("month")         # month filter (1-12)
    year = request.GET.get("year")           # year filter

    # Get all unique dates (sorted)
    dates = sorted(BalanceItem.objects.values_list("date", flat=True).distinct())
    years = sorted(set(d.year for d in dates))

    # Base queryset: only approved items
    items_qs = BalanceItem.objects.filter(status="Approved")

    # Apply project filter
    if project_id:
        items_qs = items_qs.filter(project_name_id=project_id)

    # Apply month filter
    if month:
        items_qs = items_qs.filter(date__month=int(month))
    if year:
        items_qs = items_qs.filter(date__year=int(year))

    # Aggregate values
    items = (
        items_qs
        .values("head__head_name", "type_name", "name", "date")
        .annotate(total=Sum("value"))
        .order_by("head__head_name", "type_name", "name", "date")
    )

    # Build grouped data
    grouped = {}
    totals = [0 for _ in years]  # overall grand totals
    for i in items:
        head_name = i["head__head_name"]
        type_name = i["type_name"] or "General"
        name = i["name"]
        year_item = i["date"].year

        head_group = grouped.setdefault(head_name, {})
        type_group = head_group.setdefault(type_name, {})
        values_list = type_group.setdefault(name, [0 for _ in years])

        idx = years.index(year_item)
        values_list[idx] += i["total"]
        totals[idx] += i["total"]

    # Get all projects for filter dropdown
    projects = ProjectFirstLevelName.objects.all()

    context = {
        "company_name": "BTP Limited",
        "currency": "BDT",
        "grouped": grouped,
        "years": years,
        "totals": totals,
        "print_time": now(),
        "projects": projects,
        "selected_project": int(project_id) if project_id else None,
        "selected_month": int(month) if month else None,
        "selected_year": int(year) if year else None,
        "months": range(1, 13),
    }
    return render(request, "accounting/balance_sheet_report.html", context)



@login_required
def balance_sheet_check(request):
    year_filter = request.GET.get('year')
    head_filter = request.GET.get('head')

    # Filter BalanceItem queryset
    #items_qs = BalanceItem.objects.all()
    items_qs = BalanceItem.objects.filter(status="Approved")
    
    if year_filter:
        items_qs = items_qs.filter(date__year=year_filter)
    if head_filter:
        items_qs = items_qs.filter(head_id=head_filter)

    # Get unique years in filtered data
    dates = items_qs.values_list("date", flat=True)
    years = sorted(set(d.year for d in dates)) if dates else []

    # Aggregate values
    items = items_qs.values(
        "head__head_name", "type_name", "name", "date"
    ).annotate(total=Sum("value")).order_by("head__head_name", "type_name", "name", "date")

    # Build grouped data
    grouped = {}
    totals = [0 for _ in years]
    for i in items:
        head_name = i["head__head_name"]
        type_name = i["type_name"] or "General"
        name = i["name"]
        year = i["date"].year

        head_group = grouped.setdefault(head_name, {})
        type_group = head_group.setdefault(type_name, {})
        values_list = type_group.setdefault(name, [0 for _ in years])

        idx = years.index(year)
        values_list[idx] += i["total"]
        totals[idx] += i["total"]

    context = {
        "company_name": "BTP Limited",
        "currency": "BDT",
        "grouped": grouped,
        "years": years,
        "totals": totals,
        "print_time": now(),
        "selected_year": year_filter,
        "selected_head": head_filter,
    }
    return render(request, "accounting/balance_sheet_check.html", context)




# List View
@login_required
def balance_sheet_head_list(request):
    heads = BalanceSheetHead.objects.all()
    return render(request, 'balancesheethead/balance_sheet_head_list.html', {'heads': heads})

# Add View
@login_required
def balance_sheet_head_add(request):
    if request.method == 'POST':
        form = BalanceSheetHeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('balance_sheet_head_list')
    else:
        form = BalanceSheetHeadForm()
    return render(request, 'balancesheethead/balance_sheet_head_form.html', {'form': form, 'title': 'Add Balance Sheet Head'})

# Edit View
@login_required
def balance_sheet_head_edit(request, id):
    head = get_object_or_404(BalanceSheetHead, id=id)
    if request.method == 'POST':
        form = BalanceSheetHeadForm(request.POST, instance=head)
        if form.is_valid():
            form.save()
            return redirect('balance_sheet_head_list')
    else:
        form = BalanceSheetHeadForm(instance=head)
    return render(request, 'balancesheethead/balance_sheet_head_form.html', {'form': form, 'title': 'Edit Balance Sheet Head'})


@login_required
def balance_sheet_head_delete(request, id):
    head = get_object_or_404(BalanceSheetHead, id=id)
    
    if request.method == "POST":
        head.delete()
        messages.success(request, f"Balance Sheet Head '{head.name}' has been deleted.")
        return redirect('balance_sheet_head_list')
    
    return render(request, 'balancesheethead/balance_sheet_head_delete.html', {'head': head})
    
    
    
    
    
## -- cheque book manage ---
@login_required
def main_cheque_book_list(request):
    # Add ChequeBook
    if request.method == 'POST':
        form = MainChequeBookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_cheque_book_list')
    else:
        form = MainChequeBookForm()

    books = MainChequeBook.objects.all().order_by('-id')
    return render(request, 'cheques/main_cheque_book_list.html', {'form': form, 'books': books})


# ---- Page 2: View Cheques for a specific ChequeBook ----
@login_required
def main_cheque_list(request, book_id):
    book = get_object_or_404(MainChequeBook, id=book_id)
    #cheques = book.cheques.all().order_by('cheque_number')
    cheques = book.cheques.annotate(
        cheque_num_int=Cast('cheque_number', IntegerField())
    ).order_by('cheque_num_int')

    # Optional: Add new cheque manually
    if request.method == 'POST':
        form = MainChequeForm(request.POST)
        if form.is_valid():
            cheque = form.save(commit=False)
            cheque.cheque_book = book
            cheque.save()
            return redirect('main_cheque_list', book_id=book.id)
    else:
        form = MainChequeForm(initial={'cheque_book': book})

    return render(request, 'cheques/main_cheque_list.html', {
        'book': book,
        'cheques': cheques,
        'form': form,
    })




from django.utils import timezone
@login_required
def cheque_book_print(request, book_id):
    book = get_object_or_404(MainChequeBook, id=book_id)
    cheques = book.cheques.all()  # adjust related_name if different

    context = {
        "book": book,
        "cheques": cheques,
        "print_time": timezone.now(),
    }
    return render(request, "cheques/cheque_book_print.html", context)



@login_required
def get_cheques_by_cash_type(request, cash_type_id):
    print(cash_type_id)
    
    cheques = MainCheque.objects.filter(
        cheque_book__account_id=cash_type_id,
        cheque_book__is_active=True,
        status="unused"
    ).values("id", "cheque_number")
    return JsonResponse(list(cheques), safe=False) 
    
    
    


# ---- Edit/Delete ----
@login_required
def main_edit_book(request, pk):
    book = get_object_or_404(MainChequeBook, pk=pk)
    if request.method == 'POST':
        form = MainChequeBookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('main_cheque_book_list')
    else:
        form = MainChequeBookForm(instance=book)
    return render(request, 'cheques/main_edit_book.html', {'form': form})




@login_required
def main_delete_book(request, pk):
    book = get_object_or_404(MainChequeBook, pk=pk)
    book.delete()
    return redirect('main_cheque_book_list')




@login_required
def main_edit_cheque(request, pk):
    cheque = get_object_or_404(MainCheque, pk=pk)
    if request.method == 'POST':
        form = MainChequeForm(request.POST, instance=cheque)
        if form.is_valid():
            form.save()
            return redirect('main_cheque_list', book_id=cheque.cheque_book.id)
    else:
        form = MainChequeForm(instance=cheque)
    return render(request, 'cheques/main_edit_cheque.html', {'form': form})




@login_required
def main_delete_cheque(request, pk):
    cheque = get_object_or_404(MainCheque, pk=pk)
    book_id = cheque.cheque_book.id
    cheque.delete()
    return redirect('main_cheque_list', book_id=book_id)






## -- Profit ledger --

# @login_required
# def profit_ledger_list(request):
#     projectNames = ProjectFirstLevelName.objects.select_related('location', 'project_owner').all()
#     context = {
#         'projectNames': projectNames,
#         'today': date.today(),
#     }
#     return render(request, 'profitreport/profit_ledger_list.html', context)
    
    
    
from django.db.models import Sum
from datetime import date
from decimal import Decimal

# @login_required
# def profit_ledger_list(request):

#     projects = ProjectFirstLevelName.objects.select_related('project_owner').all()

#     result = []

#     for project in projects:

#         land_total = LandPurchase.objects.filter(
#             land_supplier=project.project_owner
#         ).aggregate(total=Sum('total_price'))['total'] or Decimal("0")

#         sales_total = PropertySales.objects.filter(
#             project_name=project
#         ).aggregate(total=Sum('total_amount'))['total'] or Decimal("0")

#         profit = sales_total - land_total

#         # NEW: Correct Decimal multiplication
#         profit_25 = profit * Decimal("0.25")
#         final_profit = profit - profit_25

#         result.append({
#             'project_name': project.project_first_name,
#             'project_owner': project.project_owner.owner_name if project.project_owner else "-",
#             'land_total': land_total,
#             'sales_total': sales_total,
#             'profit': profit,
#             'profit_25': profit_25,
#             'final_profit': final_profit,
#         })

#     context = {
#         'rows': result,
#         'today': date.today(),
#     }

#     return render(request, 'profitreport/profit_ledger_list.html', context)
    
    


@login_required
def profit_ledger_list(request):

    projects = ProjectFirstLevelName.objects.select_related('project_owner').all()
    result = []

    for project in projects:

        land_total = LandPurchase.objects.filter(
            land_supplier=project.project_owner
        ).aggregate(total=Sum('total_price'))['total'] or Decimal("0")

        sales_total = PropertySales.objects.filter(
            project_name=project
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal("0")

        profit = sales_total - land_total
        profit_25 = profit * Decimal("0.25")
        final_profit = profit - profit_25

        # NEW: SAVE / UPDATE INTO NEW TABLE
        record, created = ProjectProfitRecord.objects.update_or_create(
            project=project,
            defaults={
                'profit': profit,
                'profit_25': profit_25,
                'final_profit': final_profit,
            }
        )

        result.append({
            'project_name': project.project_first_name,
            'project_owner': project.project_owner.owner_name if project.project_owner else "-",
            'land_total': land_total,
            'sales_total': sales_total,
            'profit': profit,
            'profit_25': profit_25,
            'final_profit': final_profit,
        })

    context = {
        'rows': result,
        'today': date.today(),
    }

    return render(request, 'profitreport/profit_ledger_list.html', context)





# @login_required
# def profit_shareamount_list(request):
#     records = ProjectProfitRecord.objects.select_related("project").all()

#     context = {
#         "records": records,
#         "today": date.today(),
#     }
#     return render(request, "profitreport/profit_shareamount_list.html", context)



@login_required
def profit_shareamount_list(request):
    records = ProjectProfitRecord.objects.select_related("project").all()

    # Calculate column totals
    total_profit = sum(r.profit for r in records)
    total_profit_25 = sum(r.profit_25 for r in records)
    total_final_profit = sum(r.final_profit for r in records)

    context = {
        "records": records,
        "today": date.today(),
        "total_profit": total_profit,
        "total_profit_25": total_profit_25,
        "total_final_profit": total_final_profit,
    }
    return render(request, "profitreport/profit_shareamount_list.html", context)




  
@login_required
def profit_ledger_manage(request):
    donations = Donation.objects.all()
    projectName = ProjectFirstLevelName.objects.all()
    head = HeadOfAccount.objects.all()
    form = LedgerFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  # <-- clearer naming
    cashTypes = CashType.objects.all()
    
    context = {
        'donations': donations,
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'profitreport/profit_ledger_manage.html', context)


   


# @login_required
# def profit_ledger_report(request):

#     project_id = request.GET.get("project")
#     donation_id = request.GET.get("donation_name")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")
#     show_projects = request.GET.get("show_projects")

#     # -----------------------
#     # DATE PARSE
#     # -----------------------
#     def parse_date(v):
#         try:
#             return datetime.strptime(v, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # ======================================================
#     # 1️⃣ PROJECT SUMMARY (ONLY ONE ROW)
#     # ======================================================
#     total_profit = 0
#     total_profit_25 = 0
#     total_final_profit = 0
#     project_title = "All Projects"

#     if show_projects == "on":   # only when checkbox is checked

#         if project_id:
#             projects = ProjectFirstLevelName.objects.filter(id=project_id)
#             project_title = projects.first().project_first_name
#         else:
#             projects = ProjectFirstLevelName.objects.all()

#         # sum profit values
#         for p in projects:
#             profit = ProjectProfitRecord.objects.filter(project=p).first()

#             total_profit += profit.profit if profit else 0
#             total_profit_25 += profit.profit_25 if profit else 0
#             total_final_profit += profit.final_profit if profit else 0

#         project_summary = {
#             "project_name": project_title,
#             "profit": total_profit,
#             "profit_25": total_profit_25,
#             "final_profit": total_final_profit,
#         }

#     else:
#         project_summary = None  # nothing shown

#     # ======================================================
#     # 2️⃣ DONATION LEDGER TABLE (ALWAYS APPLY)
#     # ======================================================
#     donation_rows = LedgerEntry.objects.filter(type="Donation")

#     if donation_id:
#         donation_rows = donation_rows.filter(donation_name_id=donation_id)

#     if project_id:
#         donation_rows = donation_rows.filter(project_name_id=project_id)
        
#     else:
#             projects = donation_rows.filter(type="Donation")

#     if fd:
#         donation_rows = donation_rows.filter(date__gte=fd)
#     if td:
#         donation_rows = donation_rows.filter(date__lte=td)

#     donation_list = []
#     for l in donation_rows.order_by("date"):
#         donation_list.append({
#             "date": l.date,
#             "donation_name": l.donation_name.donation_name if l.donation_name else "",
#             "description": l.description,
#             "debit": l.debit,
#             "credit": l.credit,
#             "balance": float(l.debit) - float(l.credit)
#         })

#     # ======================================================
#     # RETURN
#     # ======================================================
#     return render(request, "profitreport/profit_ledger_report.html", {
#         "project_summary": project_summary,
#         "donation_list": donation_list,
#     })




##  -- correct code --


# @login_required
# def profit_ledger_report(request):

#     project_id = request.GET.get("project")
#     donation_id = request.GET.get("donation_name")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")
#     show_projects = request.GET.get("show_projects")

#     # -----------------------
#     # DATE PARSE
#     # -----------------------
#     def parse_date(v):
#         try:
#             return datetime.strptime(v, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # ======================================================
#     # 1️⃣ PROJECT SUMMARY (ONLY ONE ROW)
#     # ======================================================
#     total_profit = 0
#     total_profit_25 = 0
#     total_final_profit = 0
#     project_title = "All Projects"

#     if show_projects == "on":   # only when checkbox is checked

#         if project_id:
#             projects = ProjectFirstLevelName.objects.filter(id=project_id)
#             project_title = projects.first().project_first_name
#         else:
#             projects = ProjectFirstLevelName.objects.all()

#         # sum profit values
#         for p in projects:
#             profit = ProjectProfitRecord.objects.filter(project=p).first()

#             total_profit += profit.profit if profit else 0
#             total_profit_25 += profit.profit_25 if profit else 0
#             total_final_profit += profit.final_profit if profit else 0

#         project_summary = {
#             "project_name": project_title,
#             "profit": total_profit,
#             "profit_25": total_profit_25,
#             "final_profit": total_final_profit,
#         }

#     else:
#         project_summary = None  # nothing shown

#     # ======================================================
#     # 2️⃣ DONATION LEDGER TABLE (ALWAYS APPLY)
#     # ======================================================
#     donation_rows = LedgerEntry.objects.filter(type="Donation")

#     if donation_id:
#         donation_rows = donation_rows.filter(donation_name_id=donation_id)

#     if project_id:
#         donation_rows = donation_rows.filter(project_name_id=project_id)
        
#     else:
#             projects = donation_rows.filter(type="Donation")

#     if fd:
#         donation_rows = donation_rows.filter(date__gte=fd)
#     if td:
#         donation_rows = donation_rows.filter(date__lte=td)

#     donation_list = []
#     for l in donation_rows.order_by("date"):
#         donation_list.append({
#             "date": l.date,
#             "donation_name": l.donation_name.donation_name if l.donation_name else "",
#             "description": l.description,
#             "debit": l.debit,
#             "credit": l.credit,
#             "balance": float(l.debit) - float(l.credit)
#         })

#     # ======================================================
#     # RETURN
#     # ======================================================
#     return render(request, "profitreport/profit_ledger_report.html", {
#         "project_summary": project_summary,
#         "donation_list": donation_list,
#     })
    
    


from datetime import datetime
from decimal import Decimal
@login_required
def profit_ledger_report(request):
    project_id = request.GET.get("project")
    donation_id = request.GET.get("donation_name")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    show_projects = request.GET.get("show_projects")
    transaction_type = request.GET.get("transaction", "datewise")  # default to datewise

    # -----------------------
    # DATE PARSE
    # -----------------------
    def parse_date(v):
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # ======================================================
    # 1️⃣ PROJECT SUMMARY (ONLY IF SHOW PROJECTS CHECKED)
    # ======================================================
    project_summary = None
    if show_projects == "on":
        if project_id:
            projects = ProjectFirstLevelName.objects.filter(id=project_id)
        else:
            projects = ProjectFirstLevelName.objects.all()

        total_profit = total_profit_25 = total_final_profit = 0
        for p in projects:
            profit = ProjectProfitRecord.objects.filter(project=p).first()
            total_profit += profit.profit if profit else 0
            total_profit_25 += profit.profit_25 if profit else 0
            total_final_profit += profit.final_profit if profit else 0

        project_summary = {
            "project_name": projects.first().project_first_name if project_id else "All Projects",
            "profit": total_profit,
            "profit_25": total_profit_25,
            "final_profit": total_final_profit,
        }

    # ======================================================
    # 2️⃣ DONATION LEDGER
    # ======================================================
    donation_rows = LedgerEntry.objects.filter(type="Donation")

    if donation_id:
        donation_rows = donation_rows.filter(donation_name_id=donation_id)

    if project_id:
        donation_rows = donation_rows.filter(project_name_id=project_id)

    # Apply date filters only if transaction_type is "datewise"
    if transaction_type == "datewise":
        if fd:
            donation_rows = donation_rows.filter(date__gte=fd)
        if td:
            donation_rows = donation_rows.filter(date__lte=td)

    # Compute running balance
    donation_list = []
    running_balance = Decimal("0.00")
    for l in donation_rows.order_by("date", "id"):
        debit = l.debit or Decimal("0.00")
        credit = l.credit or Decimal("0.00")
        running_balance += debit - credit
        donation_list.append({
            "date": l.date,
            "donation_name": l.donation_name.donation_name if l.donation_name else "N/A",
            "description": l.description or "",
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })

    return render(request, "profitreport/profit_ledger_report.html", {
        "project_summary": project_summary,
        "donation_list": donation_list,
        "selected_filters": {
            "project": project_id or "All",
            "donation_name": donation_id or "All",
            "from_date": fd,
            "to_date": td,
            "transaction": transaction_type
        },
        "print_time": datetime.now()
    })







# @login_required
# def profit_ledger_manage_pdf(request):
#     project_id = request.GET.get("project")
#     donation_id = request.GET.get("donation_name")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")

#     # -----------------------
#     # DATE PARSE
#     # -----------------------
#     def parse_date(v):
#         try:
#             return datetime.strptime(v, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # ======================================================
#     # 1️⃣ PROJECT SUMMARY (ALWAYS CALCULATE)
#     # ======================================================
#     total_profit = 0
#     total_profit_25 = 0
#     total_final_profit = 0
#     project_title = "All Projects"

#     if project_id:
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#         if projects.exists():
#             project_title = projects.first().project_first_name
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     # sum profit values
#     for p in projects:
#         profit = ProjectProfitRecord.objects.filter(project=p).first()
#         total_profit += profit.profit if profit else 0
#         total_profit_25 += profit.profit_25 if profit else 0
#         total_final_profit += profit.final_profit if profit else 0

#     project_summary = {
#         "project_name": project_title,
#         "profit": total_profit,
#         "profit_25": total_profit_25,
#         "final_profit": total_final_profit,
#     }

#     # ======================================================
#     # 2️⃣ DONATION LEDGER TABLE (ALWAYS APPLY)
#     # ======================================================
#     donation_rows = LedgerEntry.objects.filter(type="Donation")

#     if donation_id:
#         donation_rows = donation_rows.filter(donation_name_id=donation_id)

#     if project_id:
#         donation_rows = donation_rows.filter(project_name_id=project_id)

#     if fd:
#         donation_rows = donation_rows.filter(date__gte=fd)
#     if td:
#         donation_rows = donation_rows.filter(date__lte=td)

#     donation_list = []
#     for l in donation_rows.order_by("date"):
#         donation_list.append({
#             "date": l.date,
#             "donation_name": l.donation_name.donation_name if l.donation_name else "",
#             "description": l.description,
#             "debit": l.debit,
#             "credit": l.credit,
#             "balance": float(l.debit) - float(l.credit)
#         })

#     # ======================================================
#     # RETURN
#     # ======================================================
#     return render(request, "profitreport/profit_ledger_manage_pdf.html", {
#         "project_summary": project_summary,
#         "donation_list": donation_list,
#         "print_time": datetime.now(),
#         "selected_filters": {
#             "from_date": fd,
#             "to_date": td
#         }
#     })







# from datetime import datetime
# from decimal import Decimal

# @login_required
# def profit_ledger_manage_pdf(request):
#     project_id = request.GET.get("project")
#     donation_id = request.GET.get("donation_name")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")

#     # -----------------------
#     # DATE PARSE
#     # -----------------------
#     def parse_date(v):
#         try:
#             return datetime.strptime(v, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # ======================================================
#     # 1️⃣ PROJECT SUMMARY (ALWAYS CALCULATE)
#     # ======================================================
#     total_profit = Decimal('0.00')
#     total_profit_25 = Decimal('0.00')
#     total_final_profit = Decimal('0.00')
#     project_title = "All Projects"

#     if project_id:
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#         if projects.exists():
#             project_title = projects.first().project_first_name
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     for p in projects:
#         profit = ProjectProfitRecord.objects.filter(project=p).first()
#         total_profit += profit.profit if profit else 0
#         total_profit_25 += profit.profit_25 if profit else 0
#         total_final_profit += profit.final_profit if profit else 0

#     project_summary = {
#         "project_name": project_title,
#         "profit": total_profit,
#         "profit_25": total_profit_25,
#         "final_profit": total_final_profit,
#     }

#     # ======================================================
#     # 2️⃣ DONATION LEDGER TABLE (RUNNING BALANCE)
#     # ======================================================
#     donation_rows = LedgerEntry.objects.filter(type="Donation")

#     # Filter by donation_id only if provided
#     if donation_id:
#         donation_rows = donation_rows.filter(donation_name_id=donation_id)

#     if project_id:
#         donation_rows = donation_rows.filter(project_name_id=project_id)

#     if fd:
#         donation_rows = donation_rows.filter(date__gte=fd)
#     if td:
#         donation_rows = donation_rows.filter(date__lte=td)

#     donation_list = []
#     running_balance = Decimal('0.00')

#     for l in donation_rows.order_by("date"):
#         debit = Decimal(l.debit or 0)
#         credit = Decimal(l.credit or 0)
#         running_balance += credit - debit

#         donation_list.append({
#             "date": l.date,
#             "donation_name": l.donation_name.donation_name if l.donation_name else "",
#             "description": l.description,
#             "debit": debit,
#             "credit": credit,
#             "balance": running_balance
#         })

#     # ======================================================
#     # RETURN
#     # ======================================================
#     return render(request, "profitreport/profit_ledger_manage_pdf.html", {
#         "project_summary": project_summary,
#         "donation_list": donation_list,
#         "print_time": datetime.now(),
#         "selected_filters": {
#             "from_date": fd,
#             "to_date": td
#         }
#     })

    
    
#### -------ok code

# from datetime import datetime
# from decimal import Decimal

# @login_required
# def profit_ledger_manage_pdf(request):
#     project_id = request.GET.get("project")
#     donation_id = request.GET.get("donation_name")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")
#     transaction_option = request.GET.get("transaction", "datewise")  # 'all' or 'datewise'

#     # -----------------------
#     # DATE PARSE
#     # -----------------------
#     def parse_date(v):
#         try:
#             return datetime.strptime(v, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = parse_date(from_date)
#     td = parse_date(to_date)

#     # ======================================================
#     # 1️⃣ PROJECT SUMMARY
#     # ======================================================
#     total_profit = Decimal("0.00")
#     total_profit_25 = Decimal("0.00")
#     total_final_profit = Decimal("0.00")
#     project_title = "All Projects"

#     if project_id:
#         projects = ProjectFirstLevelName.objects.filter(id=project_id)
#         if projects.exists():
#             project_title = projects.first().project_first_name
#     else:
#         projects = ProjectFirstLevelName.objects.all()

#     for p in projects:
#         profit = ProjectProfitRecord.objects.filter(project=p).first()
#         total_profit += profit.profit if profit else 0
#         total_profit_25 += profit.profit_25 if profit else 0
#         total_final_profit += profit.final_profit if profit else 0

#     project_summary = {
#         "project_name": project_title,
#         "profit": total_profit,
#         "profit_25": total_profit_25,
#         "final_profit": total_final_profit,
#     }

#     # ======================================================
#     # 2️⃣ DONATION LEDGER
#     # ======================================================
#     donation_rows = LedgerEntry.objects.filter(type="Donation")

#     # Filter by donation_id ONLY if user selected a specific donation
#     if donation_id:
#         donation_rows = donation_rows.filter(donation_name_id=donation_id)

#     # Filter by project if selected
#     if project_id:
#         donation_rows = donation_rows.filter(project_name_id=project_id)

#     # Apply date filter only if transaction_option is 'datewise'
#     if transaction_option == "datewise":
#         if fd:
#             donation_rows = donation_rows.filter(date__gte=fd)
#         if td:
#             donation_rows = donation_rows.filter(date__lte=td)

#     # Prepare donation list with running balance
#     donation_list = []
#     running_balance = Decimal("0.00")
#     for l in donation_rows.order_by("date"):
#         debit = Decimal(l.debit or 0)
#         credit = Decimal(l.credit or 0)
#         running_balance += credit - debit
#         donation_list.append({
#             "date": l.date,
#             "donation_name": l.donation_name.donation_name if l.donation_name else "",
#             "description": l.description,
#             "debit": debit,
#             "credit": credit,
#             "balance": running_balance
#         })

#     # ======================================================
#     # RETURN
#     # ======================================================
#     return render(request, "profitreport/profit_ledger_manage_pdf.html", {
#         "project_summary": project_summary,
#         "donation_list": donation_list,
#         "donations": donation_rows.values("donation_name__id", "donation_name__donation_name").distinct(),
#         "print_time": datetime.now(),
#         "selected_filters": {
#             "donation_id": donation_id,
#             "from_date": fd,
#             "to_date": td,
#             "transaction": transaction_option,
#             "project_id": project_id,
#         }
#     })


from datetime import datetime
from decimal import Decimal

@login_required
def profit_ledger_manage_pdf(request):
    project_id = request.GET.get("project")
    donation_id = request.GET.get("donation_name")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    transaction_option = request.GET.get("transaction", "datewise")  # 'all' or 'datewise'

    # -----------------------
    # DATE PARSE
    # -----------------------
    def parse_date(v):
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except:
            return None

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # ======================================================
    # 1️⃣ PROJECT SUMMARY
    # ======================================================
    total_profit = Decimal("0.00")
    total_profit_25 = Decimal("0.00")
    total_final_profit = Decimal("0.00")
    project_title = "All Projects"

    if project_id:
        projects = ProjectFirstLevelName.objects.filter(id=project_id)
        if projects.exists():
            project_title = projects.first().project_first_name
    else:
        projects = ProjectFirstLevelName.objects.all()

    for p in projects:
        profit = ProjectProfitRecord.objects.filter(project=p).first()
        total_profit += profit.profit if profit else 0
        total_profit_25 += profit.profit_25 if profit else 0
        total_final_profit += profit.final_profit if profit else 0

    project_summary = {
        "project_name": project_title,
        "profit": total_profit,
        "profit_25": total_profit_25,
        "final_profit": total_final_profit,
    }

    # ======================================================
    # 2️⃣ DONATION LEDGER
    # ======================================================
    donation_rows = LedgerEntry.objects.filter(type="Donation")

    if donation_id:
        donation_rows = donation_rows.filter(donation_name_id=donation_id)

    if project_id:
        donation_rows = donation_rows.filter(project_name_id=project_id)

    if transaction_option == "datewise":
        if fd:
            donation_rows = donation_rows.filter(date__gte=fd)
        if td:
            donation_rows = donation_rows.filter(date__lte=td)

    # Prepare donation list with running balance
    donation_list = []
    running_balance = Decimal("0.00")

    # ➕ ADD (before loop)
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for l in donation_rows.order_by("date"):
        debit = Decimal(l.debit or 0)
        credit = Decimal(l.credit or 0)

        running_balance += credit - debit

        # ➕ ADD (inside loop)
        total_debit += debit
        total_credit += credit

        donation_list.append({
            "date": l.date,
            "donation_name": l.donation_name.donation_name if l.donation_name else "",
            "description": l.description,
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })

    # ➕ ADD (after loop)
    final_balance = running_balance

    # ======================================================
    # RETURN
    # ======================================================
    return render(request, "profitreport/profit_ledger_manage_pdf.html", {
        "project_summary": project_summary,
        "donation_list": donation_list,

        # ➕ ADD
        "total_debit": total_debit,
        "total_credit": total_credit,
        "final_balance": final_balance,

        "donations": donation_rows.values(
            "donation_name__id",
            "donation_name__donation_name"
        ).distinct(),
        "print_time": datetime.now(),
        "selected_filters": {
            "donation_id": donation_id,
            "from_date": fd,
            "to_date": td,
            "transaction": transaction_option,
            "project_id": project_id,
        }
    })
