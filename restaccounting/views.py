from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import RestTransactionHistory,RestMainChequeBook,LedgerRestEntry,RestMainCheque,CashRestType,DailyPayment,SalesRestType,RestHeadOfAccount,CreditRestVoucher,RestBalanceTransfer,CapitalRestAccount,Collection,RestLoanVoucher,DebitRestVoucher,RestMainCheque
from .forms import CashRestTypeForm,RestMainChequeBookForm,RestMainChequeForm,RestHeadOfAccountForm,CapitalRestAccountForm,DailyPaymentForm,CreditRestVoucherForm,DailyPaymentForm,RestTransactionHistoryForm,LedgerRestEntryForm,LedgerRestFilterForm,CollectionForm,RestBalanceTransferForm,SalesRestTypeForm,RestLoanVoucherForm,LedgerRestEntry,DebitRestVoucherForm
from django.utils.timezone import now
from django.db.models import Q
from purchase.models import HeadOfExpense,HeadOfRequisition
from restaurant.models import RestaurantSupplier,RestPurchaseCost
from django.db.models.functions import Cast
from django.db.models import IntegerField
from inventories.utils import log_deleted_data
from projects.models import ProjectFirstLevelName,Suppliers,SiteSupervisor,Donation
from crm.models import Sale,Customer
from restaurant.models import RestExpense
from restahrm.models import RestaurantEmployee,RestaurantAdvancePayment,RestaurantAllowances,RestaurantLoanPayment,RestaurantSalaryPayment,RestaurantAttendance
from django.core.paginator import Paginator
from datetime import date,datetime,timedelta
from decimal import Decimal
from django.db.models import Sum
from collections import defaultdict
from calendar import monthrange
from django.db.models import Count
from num2words import num2words
from accounting.utils.sms import send_sms



@login_required
def rest_cash_type_list(request):
    cash_types = CashRestType.objects.all()
    return render(request, 'restaurant/accounting/cash_type.html', {'cash_types': cash_types})

@login_required
def rest_add_cash_type(request):
    if request.method == 'POST':
        form = CashRestTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_cash_type_list')
    else:
        form = CashRestTypeForm()
    return render(request, 'restaurant/accounting/add_cash_type.html', {'form': form})

@login_required
def rest_edit_cash_type(request, pk):
    cash_type = get_object_or_404(CashRestType, pk=pk)
    if request.method == 'POST':
        form = CashRestTypeForm(request.POST, instance=cash_type)
        if form.is_valid():
            form.save()
            return redirect('rest_cash_type_list')
    else:
        form = CashRestTypeForm(instance=cash_type)
    return render(request, 'restaurant/accounting/edit_cash_type.html', {'form': form, 'cash_type': cash_type})


@login_required
def rest_delete_cash_type(request, pk):
    cash_type = get_object_or_404(CashRestType, pk=pk)

    if request.method == 'POST':
        log_deleted_data(cash_type, request.user)
        cash_type.delete()
        return redirect('rest_cash_type_list')

    return render(request, 'restaurant/accounting/delete_cash_type.html', {'cash_type': cash_type})
    
    
## -- sales type

@login_required
def rest_sales_type_list(request):
    sales_types = SalesRestType.objects.all()
    return render(request, 'restaurant/accounting/sales_type.html', {'sales_types': sales_types})

@login_required
def rest_add_sales_type(request):
    if request.method == 'POST':
        form = SalesRestTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_sales_type_list')
    else:
        form = SalesRestTypeForm()
    return render(request, 'restaurant/accounting/add_sales_type.html', {'form': form})

@login_required
def rest_edit_sales_type(request, pk):
    cash_type = get_object_or_404(SalesRestType, pk=pk)
    if request.method == 'POST':
        form = SalesRestTypeForm(request.POST, instance=cash_type)
        if form.is_valid():
            form.save()
            return redirect('rest_sales_type_list')
    else:
        form = SalesRestTypeForm(instance=cash_type)
    return render(request, 'restaurant/accounting/edit_sales_type.html', {'form': form, 'cash_type': cash_type})


@login_required
def rest_delete_sales_type(request, pk):
    cash_type = get_object_or_404(SalesRestType, pk=pk)

    if request.method == 'POST':
        log_deleted_data(cash_type, request.user)
        cash_type.delete()
        return redirect('rest_sales_type_list')

    return render(request, 'restaurant/accounting/delete_sales_type.html', {'cash_type': cash_type})
    
    
    

@login_required
def rest_head_of_account_list(request):
    head_accounts = RestHeadOfAccount.objects.all()
    return render(request, 'restaurant/accounting/head_of_account_list.html', {'head_accounts': head_accounts})


@login_required
def rest_add_head_of_account(request):
    if request.method == 'POST':
        form = RestHeadOfAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_head_of_account_list')  
    else:
        form = RestHeadOfAccountForm()
    return render(request, 'restaurant/accounting/add_head_of_account.html', {'form': form})



@login_required
def rest_edit_head_of_account(request, pk):
    head_account = get_object_or_404(RestHeadOfAccount, pk=pk)
    
    if request.method == 'POST':
        form = RestHeadOfAccountForm(request.POST, instance=head_account)
        if form.is_valid():
            form.save()
            return redirect('rest_head_of_account_list')  
    else:
        form = RestHeadOfAccountForm(instance=head_account)
    
    return render(request, 'restaurant/accounting/edit_head_of_account.html', {
        'form': form,
        'head_account': head_account
    })


@login_required
def rest_delete_head_of_account(request, pk):
    head_account = get_object_or_404(RestHeadOfAccount, pk=pk)
    if request.method == 'POST':
        log_deleted_data(head_account, request.user)
        head_account.delete()
        return redirect('rest_head_of_account_list')
    return render(request, 'restaurant/accounting/delete_head_of_account.html', {
        'head_account': head_account  
    })



@login_required
def rest_creditvoucher_list(request):
    vouchers = CreditRestVoucher.objects.all().order_by('-id')
    paginator = Paginator(vouchers, 15)  
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number) 
    return render(request, 'restaurant/creditvoucher/creditvoucher_list.html', {'vouchers': vouchers, 'vouchers': vouchers_page})



# @login_required
# def approve_cr_voucher(request, pk):
#     voucher = get_object_or_404(RestuaCreditVoucher, pk=pk)
#     updated_items = []

#     # If already approved, redirect
#     if voucher.approval_cr_status:
#         return redirect('rest_creditvoucher_list')

#     # Generate MR/Bill No if not set
#     if not voucher.mr_or_bill_no:
#         base_code = "MBC-"
#         last = (
#             RestuaCreditVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#             .order_by('-id')
#             .first()
#         )
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"

#         while RestuaCreditVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#             next_id += 1
#             generated_code = f"{base_code}{next_id:05d}"

#         voucher.mr_or_bill_no = generated_code

#     # Approve the voucher
#     voucher.approval_cr_status = True
#     voucher.save()
#     updated_items.append(voucher)

#     # Update CashType balance
#     try:
#         cash_type = RestCashType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount += voucher.amount
#         cash_type.type_note = f"Update Received Amount of voucher ID {voucher.id}"
#         cash_type.save()
#     except RestCashType.DoesNotExist:
#         cash_type = None  # prevent crash later
    
#     type_name = voucher.customer_name if voucher.type == 'Customer' and voucher.customer_name else None
#     # Log transaction
#     TransactionHistory.objects.create(
#         project=voucher.project_name,  # FK to ProjectFirstLevelName
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount,
#         cheque_number=voucher.cheque_number,
#         date=voucher.date,
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
#             mr_or_bill_no=None,
#             date=item.date or timezone.now(),
#             description=item.particulars or '',
#             debit=debit_amount,
#             credit=credit_amount,
#             carrier=getattr(item, 'carrier', None),
#             loan_status=loan_status,
#             tbl_id=item.id,
#             tbl_name='Received'
#         )

#     return redirect('rest_creditvoucher_list')
    
    



@login_required
def rest_add_creditvoucher(request):
    if request.method == 'POST':
        form = CreditRestVoucherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_creditvoucher_list')  # redirect after save
    else:
        form = CreditRestVoucherForm()

    employees = RestaurantEmployee.objects.all()  # ✅ load employees
    context = {
        'form': form,
        'employees': employees,  # ✅ pass to template
        'today': date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'restaurant/creditvoucher/add_creditvoucher.html', context)





# from django.utils import timezone

# @login_required
# def rest_edit_creditvoucher(request, pk):
#     voucher = get_object_or_404(RestuaCreditVoucher, pk=pk)
#     form = RestuaCreditVoucherForm(request.POST or None, instance=voucher)

#     if form.is_valid():
#         updated_voucher = form.save()

#         # Update or create LedgerEntry linked to this CreditVoucher
#         ledger_entry, created = LedgerEntry.objects.update_or_create(
#             tbl_id=str(updated_voucher.id),
#             tbl_name="Received",  # CreditVoucher = Receipt
#             defaults={
#                 "project_name": updated_voucher.project_name,
#                 "type": updated_voucher.type,
#                 "contructor": None,
#                 "vendor": None,
#                 "customer_name": updated_voucher.customer_name,
#                 "exp_name": None,
#                 "empl_name": None,
#                 "capi_name": updated_voucher.capi_name,
#                 "invest_name": updated_voucher.invest_name,
#                 "cash_type": updated_voucher.cash_type,
#                 "bankName": None,
#                 "cheque_number": updated_voucher.cheque_number,
#                 "mr_or_bill_no": updated_voucher.mr_or_bill_no,
#                 "head": updated_voucher.head_of_account,
#                 "date": updated_voucher.date or timezone.now().date(),  # ✅ ensures NOT NULL
#                 "description": updated_voucher.particulars,
#                 "credit": updated_voucher.amount,   # CreditVoucher → credit
#                 "debit": 0,
#                 "carrier": updated_voucher.carrier,
#             }
#         )
#         TransactionHistory.objects.update_or_create(
#                 tbl_id=str(updated_voucher.id),       
#                 tbl_name="Received",               
#                 defaults={
#                     "project": updated_voucher.project_name,
#                     "transaction_type": "Credit",
#                     "head_of_account": updated_voucher.head_of_account,
#                     "cash_type": updated_voucher.cash_type,
#                     "cheque_number": updated_voucher.cheque_number,
#                     "amount": updated_voucher.amount,
#                     "date": updated_voucher.date or timezone.now().date(),
#                     "type_name": updated_voucher.type,
#                     "reference": getattr(updated_voucher, 'voucher_no', None),
#                     "create_by": request.user.username,
#                     "particulars": updated_voucher.particulars,
#                 }
#             )

#         return redirect('rest_creditvoucher_list')

#     return render(request, 'restaurant/creditvoucher/edit_creditvoucher.html', {
#         'form': form,
#         'voucher': voucher
#     })




from django.utils import timezone

@login_required
def rest_edit_creditvoucher(request, pk):
    voucher = get_object_or_404(CreditRestVoucher, pk=pk)
    form = CreditRestVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        updated_voucher = form.save()
        return redirect('rest_creditvoucher_list')

    return render(request, 'restaurant/creditvoucher/edit_creditvoucher.html', {
        'form': form,
        'voucher': voucher
    })


   
    

# from django.db import transaction
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import get_object_or_404, redirect, render

# @login_required
# def rest_delete_creditvoucher(request, pk):
#     voucher = get_object_or_404(CreditRestVoucher, pk=pk)

#     if request.method == 'POST':
#         with transaction.atomic():
#             # Log before delete
#             log_deleted_data(voucher, request.user)

#             LedgerEntry.objects.filter(
#                 tbl_id=str(voucher.id),
#                 tbl_name="Received" 
#             ).delete()

            
#             TransactionHistory.objects.filter(
#                 tbl_id=str(voucher.id),
#                 tbl_name="Received"
#             ).delete()

#             voucher.delete()

#         return redirect('rest_creditvoucher_list')

#     return render(
#         request,
#         'restaurant/creditvoucher/delete_creditvoucher.html',
#         {'voucher': voucher}
#     )



from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

@login_required
def rest_delete_creditvoucher(request, pk):
    voucher = get_object_or_404(CreditRestVoucher, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Log before delete
            log_deleted_data(voucher, request.user)
            voucher.delete()

        return redirect('rest_creditvoucher_list')

    return render(
        request,
        'restaurant/creditvoucher/delete_creditvoucher.html',
        {'voucher': voucher}
    )




@login_required
def rest_credit_voucher_pdf(request, pk):
    voucher = get_object_or_404(CreditRestVoucher, pk=pk)
  
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
    return render(request, 'restaurant/creditvoucher/print_creditvoucher.html', context)
    
    


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.timezone import now
from num2words import num2words

@login_required
def rest_credit_allvoucher_approve(request):

    # BULK APPROVE
    if request.method == "POST":

        selected_ids = request.POST.getlist('voucher_ids')

        if selected_ids:

            CreditRestVoucher.objects.filter(
                id__in=selected_ids
            ).update(
                approval_cr_status=True
            )

            return redirect('rest_credit_allvoucher_approve')


    # SHOW ONLY PENDING ROWS
    vouchers = CreditRestVoucher.objects.filter(
        approval_cr_status=False
    ).order_by('-id')


    # Amount to words
    def amount_to_words(amount):

        try:
            taka = int(amount)
            paisa = int(round((amount - taka) * 100))

            words = num2words(
                taka,
                lang='en'
            ).title() + " Taka"

            if paisa:
                words += (
                    f" and "
                    f"{num2words(paisa, lang='en').title()} Paisa"
                )

            return words + " Only"

        except:
            return f"{amount} Taka Only"


    voucher_data = []

    for voucher in vouchers:

        voucher_data.append({
            'voucher': voucher,
            'amount_in_words': amount_to_words(voucher.amount)
        })


    context = {
        'voucher_data': voucher_data,
        'print_time': now(),
    }

    return render(
        request,
        'restaurant/creditvoucher/allapprove_credit_print.html',
        context
    )
    
    


### debit voucher code 
@login_required
def rest_debitvoucher_list(request):
    projects_firt = ProjectFirstLevelName.objects.all()    
    filtered_vouchers = DebitRestVoucher.objects.filter(
        vendor__isnull=False,
        cash_type__isnull=True,
        requi_id__isnull=False
    )    
    vendor_ids = filtered_vouchers.values_list('vendor_id', flat=True).distinct()    
    suppliers = Suppliers.objects.filter(id__in=vendor_ids)    
    vouchers = DebitRestVoucher.objects.filter(Q(return_requisition__isnull=True) | ~Q(return_requisition="Yes")).order_by('-id')
    
    paginator = Paginator(vouchers, 15)  
    page_number = request.GET.get('page')
    vouchers_page = paginator.get_page(page_number) 
    context = {
        'projects_firts': projects_firt,
        'suppliers': suppliers,
        'vouchers': vouchers,
        'vouchers': vouchers_page,
    }
    return render(request, 'restaurant/debitvoucher/debitvoucher_list.html', context)



from datetime import date

@login_required
def rest_add_debitvoucher(request):
    form = DebitRestVoucherForm(request.POST or None)

    if form.is_valid():
        debit_voucher = form.save(commit=False)
        debit_voucher.save()

        # Get cheque_number from POST data (not requestOST)
        cheque_id = request.POST.get('cheque_number')

        # Only convert and fetch if a valid number is provided
        if cheque_id and cheque_id != 'None':
            try:
                cheque = RestMainCheque.objects.get(id=int(cheque_id))
                debit_voucher.cheque_number = cheque.cheque_number
                debit_voucher.save()
        
                cheque.status = 'used'
                cheque.remarks = debit_voucher.particulars or ''
                cheque.issue_date = debit_voucher.date
                cheque.amount = debit_voucher.amount
                cheque.save()
        
            except RestMainCheque.DoesNotExist:
                print("Cheque not found")
        else:
            # No cheque selected, just save the voucher
            debit_voucher.save()

        return redirect('rest_debitvoucher_list')

    return render(
        request,
        'restaurant/debitvoucher/add_debitvoucher.html',
        {
            'form': form,
            'expenses': RestExpense.objects.all(),
            'today': date.today().strftime('%Y-%m-%d'),
        }
    )
    
    
    

## -- cheque book manage ---
@login_required
def rest_main_cheque_book_list(request):
    # Add ChequeBook
    if request.method == 'POST':
        form = RestMainChequeBookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_main_cheque_book_list')
    else:
        form = RestMainChequeBookForm()

    books = RestMainChequeBook.objects.all().order_by('-id')
    return render(request, 'restaurant/cheques/main_cheque_book_list.html', {'form': form, 'books': books})
    



# ---- Page 2: View Cheques for a specific ChequeBook ----
@login_required
def rest_main_cheque_list(request, book_id):
    book = get_object_or_404(RestMainChequeBook, id=book_id)
    #cheques = book.cheques.all().order_by('cheque_number')
    cheques = book.cheques.annotate(
        cheque_num_int=Cast('cheque_number', IntegerField())
    ).order_by('cheque_num_int')

    # Optional: Add new cheque manually
    if request.method == 'POST':
        form = RestMainChequeForm(request.POST)
        if form.is_valid():
            cheque = form.save(commit=False)
            cheque.cheque_book = book
            cheque.save()
            return redirect('rest_main_cheque_list', book_id=book.id)
    else:
        form = RestMainChequeForm(initial={'cheque_book': book})

    return render(request, 'restaurant/cheques/main_cheque_list.html', {
        'book': book,
        'cheques': cheques,
        'form': form,
    })
        

@login_required
def rest_get_cheques_by_cash_type(request, cash_type_id):
    print(cash_type_id)
    
    cheques = RestMainCheque.objects.filter(
        cheque_book__account_id=cash_type_id,
        cheque_book__is_active=True,
        status="unused"
    ).values("id", "cheque_number")
    return JsonResponse(list(cheques), safe=False) 
    



from django.utils import timezone
@login_required
def rest_edit_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitRestVoucher, pk=pk)
    form = DebitRestVoucherForm(request.POST or None, instance=voucher)

    if form.is_valid():
        updated_voucher = form.save()

        # Get existing ledger entry linked to this DebitVoucher
        try:
            ledger_entry = LedgerRestEntry.objects.get(tbl_id=str(updated_voucher.id), tbl_name="Payment")
        except LedgerRestEntry.DoesNotExist:
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
            
            
            RestTransactionHistory.objects.update_or_create(
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


        return redirect('rest_debitvoucher_list')

    # Pass expenses to template for the Expense dropdown
    expenses = HeadOfExpense.objects.all().order_by('head_exp_name')

    return render(request, 'restaurant/debitvoucher/edit_debitvoucher.html', {
        'form': form,
        'voucher': voucher,
        'expenses': expenses
    })




@login_required
def rest_delete_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitRestVoucher, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Log before delete
            log_deleted_data(voucher, request.user)

            # Delete LedgerEntry linked by tbl_id
            LedgerRestEntry.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Payment"
            ).delete()

            # Delete TransactionHistory linked by tbl_id
            RestTransactionHistory.objects.filter(
                tbl_id=str(voucher.id),
                tbl_name="Payment"
            ).delete()

            # Finally delete DebitVoucher
            voucher.delete()

        return redirect('rest_debitvoucher_list')

    return render(
        request,
        'restaurant/debitvoucher/delete_debitvoucher.html',
        {'voucher': voucher}
    )






@login_required
def rest_details_debitvoucher(request, pk):
    voucher = get_object_or_404(DebitRestVoucher, pk=pk)
    return render(request, 'restaurant/debitvoucher/details_debitvoucher.html', {'voucher': voucher})


from num2words import num2words
@login_required
def rest_debit_voucher_pdf(request, pk):
    voucher = get_object_or_404(DebitRestVoucher, pk=pk)

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
    return render(request, 'restaurant/debitvoucher/print_debitvoucher.html', context)
    



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
#     sms_numbers = []
    
#     STATIC_NUMBER = "8801913222203"  # static number
#     sms_numbers.append(STATIC_NUMBER)
    
#     # Prepare SMS message based on voucher type
#     sms_message = ""  # default empty
    
#     if voucher.type == 'Customer' and voucher.customer_name:
#         customer = Customer.objects.filter(id=voucher.customer_name.id).first()
#         if customer and customer.contact_no:
#             sms_numbers.append(customer.contact_no)
        
#         sms_message = (
#             f"Dear Customer,\n"
#             f"We have successfully received your payment of ৳{voucher.amount} on {voucher.date.strftime('%d-%m-%Y')}.\n"
#             f"Reference No: {voucher.mr_or_bill_no}\n"
#             f"Thank you for your transaction.\n"
#             f"BTP Limited\n"
#             f"Thank you."
#         )
    
#     elif voucher.type == 'Vendor' and voucher.vendor:
#         supplier = Suppliers.objects.filter(id=voucher.vendor.id).first()
#         if supplier and supplier.phone:
#             sms_numbers.append(supplier.phone)
        
#         sms_message = (
#             f"Dear Supplier,\n"
#             f"We have successfully made a payment of ৳{voucher.amount} to you.\n"
#             f"Reference: {voucher.mr_or_bill_no}\n"
#             f"BTP Limited\n"
#             f"Thank you."
#         )
    
#     elif voucher.type == 'Contractor' and voucher.contructor:
#         contractor = SiteSupervisor.objects.filter(id=voucher.contructor.id).first()
#         if contractor and contractor.phone:
#             sms_numbers.append(contractor.phone)
        
#         sms_message = (
#             f"Dear Contractor,\n"
#             f"We have successfully made a payment of ৳{voucher.amount} to you.\n"
#             f"Reference: {voucher.mr_or_bill_no}\n"
#             f"BTP Limited\n"
#             f"Thank you."
#         )
    
#     # Remove duplicate numbers (important)
#     sms_numbers = list(set(sms_numbers))
    
#     # Send SMS safely
#     for number in sms_numbers:
#         if not send_sms(number, sms_message):
#             print(f"SMS sending failed for {number} (ignored).")

#     return redirect(reverse('rest_debit_voucher_pdf', args=[voucher.pk]))
    
    



@login_required
def rest_loanvoucher_list(request):
    date_filter = request.GET.get('date')

    vouchers = RestLoanVoucher.objects.all().order_by('-id')

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

    return render(request, 'restaurant/loanvoucher/loanvoucher_list.html', {
        'vouchers': voucher_list,
    })




# @login_required
# def rest_add_loanvoucher(request):
#     if request.method == 'POST':
#         form = RestLoanVoucherForm(request.POST)
#         if form.is_valid():
#             loanvoucher = form.save(commit=False)

#             # ---------------------------------------------------
#             # AUTO MR/BILL NUMBER GENERATION
#             # ---------------------------------------------------
#             if not loanvoucher.mr_or_bill_no:
#                 base_code = "APY-"
#                 last_voucher = (
#                     RestLoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#                     .order_by('-id')
#                     .first()
#                 )
#                 next_id = (last_voucher.id + 1) if last_voucher else 1
#                 generated_code = f"{base_code}{next_id:05d}"

#                 while RestLoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 loanvoucher.mr_or_bill_no = generated_code

#             # Default status
#             loanvoucher.loan_status = 'Payable'
#             loanvoucher.save()

#             amount = loanvoucher.amount or 0

#             # ---------------------------------------------------
#             # UNIQUE MR/BILL NO FOR LEDGER ROWS
#             # ---------------------------------------------------
#             base_mr = loanvoucher.mr_or_bill_no
#             mr_expense = f"{base_mr}-A"   # First row
#             mr_main = f"{base_mr}-B"      # Second row

#             # ---------------------------------------------------
#             # STATIC VALUES ALWAYS USED
#             # ---------------------------------------------------
#             no_method = CashRestType.objects.get(cash_type_name="No_Method")
#             expense_head = RestHeadOfAccount.objects.get(head_name="Expense Account")

#             # ---------------------------------------------------
#             # FIRST LEDGER ENTRY — STATIC EXPENSE
#             # ---------------------------------------------------
#             LedgerRestEntry.objects.create(
#                 project_name=loanvoucher.project_name,
#                 type="Expense",
#                 customer_name=None,
#                 contructor=None,
#                 vendor=None,
#                 exp_name=loanvoucher.source_name,
#                 bankName=None,
#                 type_name=loanvoucher.source_name.head_exp_name if loanvoucher.source_name else "",
#                 cash_type=no_method,        # ALWAYS No_Method
#                 head=expense_head,          # ALWAYS Expense Account
#                 mr_or_bill_no=mr_expense,
#                 date=loanvoucher.date,
#                 description=f"Expense entry for {loanvoucher.particulars}",
#                 debit=amount,
#                 credit=0,
#                 carrier=loanvoucher.carrier,
#                 loan_status="Expense",
#                 tbl_id=loanvoucher.id,
#                 tbl_name='Payment'
#             )

#             # ---------------------------------------------------
#             # DETERMINE SECOND ENTRY DEBIT/CREDIT
#             # ---------------------------------------------------
#             loan_status = "Received"  # your business rule
#             debit_amount = amount if loan_status.lower() == 'payment' else 0
#             credit_amount = amount if loan_status.lower() == 'received' else 0

#             # ---------------------------------------------------
#             # FIND TYPE NAME
#             # ---------------------------------------------------
#             type_name = None
#             if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
#                 type_name = loanvoucher.vendor_name
#             elif loanvoucher.type == 'Contructor' and loanvoucher.conductor_name:
#                 type_name = loanvoucher.conductor_name
#             elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
#                 type_name = loanvoucher.customer_name
#             elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
#                 type_name = loanvoucher.expense_name
#             elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
#                 type_name = loanvoucher.bankName.cash_type_name

#             # ---------------------------------------------------
#             # SECOND LEDGER ENTRY — MAIN ENTRY
#             # ---------------------------------------------------
#             LedgerRestEntry.objects.create(
#                 project_name=loanvoucher.project_name,
#                 type=loanvoucher.type,
#                 customer_name=loanvoucher.customer_name,
#                 contructor=loanvoucher.conductor_name,
#                 vendor=loanvoucher.vendor_name,
#                 exp_name=loanvoucher.expense_name,
#                 bankName=loanvoucher.bankName,
#                 type_name=type_name,
#                 cash_type=no_method,        # ALWAYS No_Method
#                 head=loanvoucher.headAcct,
#                 mr_or_bill_no=mr_main,
#                 date=loanvoucher.date,
#                 description=loanvoucher.particulars,
#                 debit=debit_amount,
#                 credit=credit_amount,
#                 carrier=loanvoucher.carrier,
#                 loan_status=loan_status,
#                 tbl_id=loanvoucher.id,
#                 tbl_name='Payment'
#             )
            
#             RestTransactionHistory.objects.create(
#                 project=loanvoucher.project_name,
#                 transaction_type=loanvoucher.type,
#                 head_of_account=loanvoucher.headAcct,
#                 cash_type=no_method,
#                 cheque_number=getattr(loanvoucher, 'cheque_number', None),
#                 amount=loanvoucher.amount,
#                 date=loanvoucher.date or timezone.now().date(),
#                 type_name=type_name,
#                 reference=getattr(loanvoucher, 'mr_no', None),
#                 create_by=loanvoucher.created_by if hasattr(loanvoucher, 'created_by') else '',
#                 particulars=loanvoucher.particulars,
#                 tbl_id=str(loanvoucher.id),
#                 tbl_name='Payment'
#             )
    
#             return redirect('rest_loanvoucher_list')

#     else:
#         form = RestLoanVoucherForm()

#     expenses = HeadOfExpense.objects.all()
#     selected_expense_name = ''

#     if form.is_bound and form.is_valid():
#         selected_expense = form.cleaned_data.get('expense_name')
#         if selected_expense:
#             selected_expense_name = f"{selected_expense.head_exp_code} - {selected_expense.head_exp_name}"

#     No_Method = get_object_or_404(CashRestType, cash_type_name='No_Method')

#     return render(request, 'restaurant/loanvoucher/add_loanvoucher.html', {
#         'No_Method': [No_Method],
#         'form': form,
#         'expenses': expenses,
#         'selected_expense_name': selected_expense_name,
#         'today': now().date(),
#     })




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.utils import timezone

@login_required
def rest_add_loanvoucher(request):
    if request.method == 'POST':
        form = RestLoanVoucherForm(request.POST)

        if form.is_valid():
            loanvoucher = form.save(commit=False)

            # ------------------------------
            # AUTO MR/BILL NUMBER
            # ------------------------------
            if not loanvoucher.mr_or_bill_no:
                base_code = "APY-"
                last_voucher = RestLoanVoucher.objects.filter(
                    mr_or_bill_no__startswith=base_code
                ).order_by('-id').first()

                next_id = last_voucher.id + 1 if last_voucher else 1
                generated_code = f"{base_code}{next_id:05d}"

                while RestLoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_id += 1
                    generated_code = f"{base_code}{next_id:05d}"

                loanvoucher.mr_or_bill_no = generated_code

            loanvoucher.loan_status = 'Payable'
            loanvoucher.save()

            amount = loanvoucher.amount or 0

            # ------------------------------
            # UNIQUE MR NUMBERS
            # ------------------------------
            base_mr = loanvoucher.mr_or_bill_no
            mr_expense = f"{base_mr}-A"
            mr_main = f"{base_mr}-B"

            # ------------------------------
            # STATIC OBJECTS
            # ------------------------------
            no_method, _ = CashRestType.objects.get_or_create(
                cash_type_name="No_Method"
            )

            expense_head, _ = RestHeadOfAccount.objects.get_or_create(
                head_name="Expense Account"
            )

            # ------------------------------
            # FIRST LEDGER ENTRY (EXPENSE)
            # ------------------------------
            LedgerRestEntry.objects.create(
                project_name=loanvoucher.project_name,
                type="Expense",
                customer_name=None,
                contructor=None,
                vendor=None,
                exp_name=loanvoucher.source_name,
                bankName=None,
                type_name=str(loanvoucher.source_name) if loanvoucher.source_name else "",
                cash_type=no_method,
                head=expense_head,
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

            # ------------------------------
            # DETERMINE SECOND ENTRY
            # ------------------------------
            loan_status = "Received"

            debit_amount = amount if loan_status.lower() == 'payment' else 0
            credit_amount = amount if loan_status.lower() == 'received' else 0

            # ------------------------------
            # FIND TYPE NAME
            # ------------------------------
            type_name = ""

            if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
                type_name = str(loanvoucher.vendor_name)

            elif loanvoucher.type == 'Contructor' and loanvoucher.conductor_name:
                type_name = str(loanvoucher.conductor_name)

            elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
                type_name = str(loanvoucher.customer_name)

            elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
                type_name = str(loanvoucher.expense_name)

            elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
                type_name = loanvoucher.bankName.cash_type_name

            # ------------------------------
            # SECOND LEDGER ENTRY
            # ------------------------------
            LedgerRestEntry.objects.create(
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
                date=loanvoucher.date,
                description=loanvoucher.particulars,
                debit=debit_amount,
                credit=credit_amount,
                carrier=loanvoucher.carrier,
                loan_status=loan_status,
                tbl_id=loanvoucher.id,
                tbl_name='Payment'
            )

            # ------------------------------
            # TRANSACTION HISTORY
            # ------------------------------
            RestTransactionHistory.objects.create(
                project=loanvoucher.project_name,
                transaction_type=loanvoucher.type,
                head_of_account=loanvoucher.headAcct,
                cash_type=no_method,
                cheque_number=getattr(loanvoucher, 'cheque_number', None),
                amount=loanvoucher.amount,
                date=loanvoucher.date or timezone.now().date(),
                type_name=type_name,
                reference=loanvoucher.mr_or_bill_no,
                create_by=getattr(loanvoucher, 'created_by', ''),
                particulars=loanvoucher.particulars,
                tbl_id=str(loanvoucher.id),
                tbl_name='Payment'
            )

            return redirect('rest_loanvoucher_list')

    else:
        form = RestLoanVoucherForm()

    expenses = RestExpense.objects.all()
    selected_expense_name = ''

    if form.is_bound and form.is_valid():
        selected_expense = form.cleaned_data.get('expense_name')
        if selected_expense:
            selected_expense_name = f"{selected_expense.expense_code} - {selected_expense.expense_name}"

    No_Method, _ = CashRestType.objects.get_or_create(
        cash_type_name='No_Method'
    )

    return render(request, 'restaurant/loanvoucher/add_loanvoucher.html', {
        'No_Method': [No_Method],
        'form': form,
        'expenses': expenses,
        'selected_expense_name': selected_expense_name,
        'today': now().date(),
    })



# @login_required
# def rest_add_rechvoucher(request):
#     if request.method == 'POST':
#         form = RestLoanVoucherForm(request.POST)

#         if form.is_valid():
#             loanvoucher = form.save(commit=False)

#             # ---------------------------------------------------
#             # AUTO MR/BILL NUMBER GENERATION (ARC-)
#             # ---------------------------------------------------
#             if not loanvoucher.mr_or_bill_no:
#                 base_code = "ARC-"
#                 last_voucher = (
#                     RestLoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#                     .order_by('-id')
#                     .first()
#                 )
#                 next_id = (last_voucher.id + 1) if last_voucher else 1
#                 generated_code = f"{base_code}{next_id:05d}"

#                 while RestLoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#                     next_id += 1
#                     generated_code = f"{base_code}{next_id:05d}"

#                 loanvoucher.mr_or_bill_no = generated_code

#             # Default status
#             loanvoucher.loan_status = 'Receivable'
#             loanvoucher.save()

#             amount = loanvoucher.amount or 0

#             # ---------------------------------------------------
#             # UNIQUE MR/BILL NO FOR LEDGER ROWS
#             # ---------------------------------------------------
#             base_mr = loanvoucher.mr_or_bill_no
#             mr_expense = f"{base_mr}-A"   # First row
#             mr_main = f"{base_mr}-B"      # Second row

#             # ---------------------------------------------------
#             # STATIC VALUES ALWAYS USED
#             # ---------------------------------------------------
#             no_method = CashRestType.objects.get(cash_type_name="No_Method")
#             expense_head = RestHeadOfAccount.objects.get(head_name="Expense Account")

#             # ---------------------------------------------------
#             # FIRST LEDGER ENTRY — STATIC EXPENSE ROW
#             # ---------------------------------------------------
#             LedgerRestEntry.objects.create(
#                 project_name=loanvoucher.project_name,
#                 type=loanvoucher.type,
#                 customer_name=None,
#                 contructor=None,
#                 vendor=None,
#                 exp_name=loanvoucher.source_name,
#                 purchase=loanvoucher.purchase_name,
#                 bankName=None,
#                 type_name=loanvoucher.source_name.head_exp_name if loanvoucher.source_name else "",
#                 cash_type=no_method,            # ALWAYS No_Method
#                 head=expense_head,              # ALWAYS Expense Account
#                 mr_or_bill_no=mr_expense,
#                 date=loanvoucher.date,
#                 description=f"Expense entry for {loanvoucher.particulars}",
#                 debit=amount,
#                 credit=0,
#                 carrier=loanvoucher.carrier,
#                 loan_status="Expense",
#                 tbl_id=loanvoucher.id,
#                 tbl_name='Received'
#             )
            
#             RestTransactionHistory.objects.create(
#                 project=loanvoucher.project_name,
#                 transaction_type=loanvoucher.type,
#                 head_of_account=expense_head,
#                 cash_type=no_method,
#                 cheque_number=None,
#                 amount=amount,
#                 date=loanvoucher.date or timezone.now().date(),
#                 reference=mr_expense,
#                 create_by=getattr(loanvoucher, 'created_by', ''),  # or request.user.username if in view
#                 particulars=f"Expense entry for {loanvoucher.particulars}",
#                 tbl_id=str(loanvoucher.id),
#                 tbl_name='Received'
#             )

#             # ---------------------------------------------------
#             # PAYMENT IS RECEIVABLE → CREDIT ENTRY
#             # ---------------------------------------------------
#             loan_status = "Payment"
#             debit_amount = amount if loan_status.lower() == "payment" else 0
#             credit_amount = amount if loan_status.lower() == "received" else 0

#             # ---------------------------------------------------
#             # DYNAMIC TYPE NAME
#             # ---------------------------------------------------
#             type_name = None
#             if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
#                 type_name = loanvoucher.vendor_name
#             elif loanvoucher.type == 'Conductor' and loanvoucher.conductor_name:
#                 type_name = loanvoucher.conductor_name
#             elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
#                 type_name = loanvoucher.customer_name
#             elif loanvoucher.type == 'Expense' and loanvoucher.expense_name:
#                 type_name = loanvoucher.expense_name
#             elif loanvoucher.type == 'Purchase' and loanvoucher.purchase_name:
#                 type_name = loanvoucher.purchase_name
#             elif loanvoucher.type == 'Employee' and loanvoucher.empl_name:
#                 type_name = loanvoucher.empl_name
#             elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
#                 type_name = loanvoucher.bankName.cash_type_name

#             # ---------------------------------------------------
#             # SECOND LEDGER ENTRY — MAIN ENTRY
#             # ---------------------------------------------------
#             LedgerRestEntry.objects.create(
#                 project_name=loanvoucher.project_name,
#                 type=loanvoucher.type,
#                 customer_name=loanvoucher.customer_name,
#                 contructor=loanvoucher.conductor_name,
#                 vendor=loanvoucher.vendor_name,
#                 exp_name=loanvoucher.expense_name,
#                 purchase=loanvoucher.purchase_name,
#                 bankName=loanvoucher.bankName,
#                 type_name=type_name,
#                 cash_type=no_method,            # ALWAYS No_Method
#                 head=loanvoucher.headAcct,
#                 mr_or_bill_no=mr_main,
#                 date=loanvoucher.date,
#                 description=loanvoucher.particulars,
#                 debit=debit_amount,
#                 credit=credit_amount,
#                 carrier=loanvoucher.carrier,
#                 loan_status=loan_status,
#             )

#             return redirect('loanvoucher_list')

#     else:
#         form = RestLoanVoucherForm()

#     # -----------------------------------------------------------
#     # PAGE LOAD SUPPORT DATA
#     # -----------------------------------------------------------
#     expenses = RestExpense.objects.all()
#     rdaEmployees = RestaurantEmployee.objects.all()
#     selected_expense_name = ''

#     form.fields['empl_name'].choices = [('', 'Select Employee Name')] + [
#         (emp.rda_emp_name, emp.rda_emp_name) for emp in rdaEmployees
#     ]

#     if form.is_bound and form.is_valid():
#         selected_expense = form.cleaned_data.get('expense_name')
#         if selected_expense:
#             selected_expense_name = f"{selected_expense.expense_code} - {selected_expense.expense_name}"
            

#     No_Method = get_object_or_404(CashRestType, cash_type_name='No_Method')

#     return render(request, 'restaurant/loanvoucher/add_rechvoucher.html', {
#         'No_Method': [No_Method],
#         'form': form,
#         'expenses': expenses,
#         'selected_expense_name': selected_expense_name,
#         'today': now().date(),
#     })




@login_required
def rest_add_rechvoucher(request):
    if request.method == 'POST':
        form = RestLoanVoucherForm(request.POST)

        if form.is_valid():
            loanvoucher = form.save(commit=False)

            # ---------------------------------------------------
            # AUTO MR/BILL NUMBER GENERATION (ARC-)
            # ---------------------------------------------------
            if not loanvoucher.mr_or_bill_no:
                base_code = "ARC-"
                last_voucher = (
                    RestLoanVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
                    .order_by('-id')
                    .first()
                )
                next_id = (last_voucher.id + 1) if last_voucher else 1
                generated_code = f"{base_code}{next_id:05d}"

                while RestLoanVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
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
           # Get static cash type
            no_method = CashRestType.objects.get(cash_type_name="No_Method")
            expense_head = RestHeadOfAccount.objects.get(head_name="Expense Account")
            purchase_head = RestHeadOfAccount.objects.get(head_name="Purchase Account")  # Purchase-specific head
            
            # ---------------------------------------------------
            # FIRST LEDGER ENTRY — STATIC EXPENSE / PURCHASE ROW
            # ---------------------------------------------------
            if loanvoucher.type == 'Expense':
                LedgerRestEntry.objects.create(
                    project_name=loanvoucher.project_name,
                    type='Expense',
                    customer_name=None,
                    contructor=None,
                    vendor=None,
                    exp_name=loanvoucher.source_name,
                    purchase=None,
                    bankName=None,
                    type_name=loanvoucher.source_name.head_exp_name if loanvoucher.source_name else "",
                    cash_type=no_method,
                    head=expense_head,
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
            
                RestTransactionHistory.objects.create(
                    project=loanvoucher.project_name,
                    transaction_type='Expense',
                    head_of_account=expense_head,
                    cash_type=no_method,
                    cheque_number=None,
                    amount=amount,
                    date=loanvoucher.date or timezone.now().date(),
                    reference=mr_expense,
                    create_by=getattr(loanvoucher, 'created_by', ''),
                    particulars=f"Expense entry for {loanvoucher.particulars}",
                    tbl_id=str(loanvoucher.id),
                    tbl_name='Received'
                )
            
            elif loanvoucher.type == 'Purchase':
                LedgerRestEntry.objects.create(
                    project_name=loanvoucher.project_name,
                    type='Purchase',
                    customer_name=None,
                    contructor=None,
                    vendor=None,
                    exp_name=None,
                    purchase=loanvoucher.purchase_name,
                    bankName=None,
                    type_name=loanvoucher.purchase_name.pur_cost_name if loanvoucher.purchase_name else "",
                    cash_type=no_method,
                    head=purchase_head,  # <-- Use Purchase Account head
                    mr_or_bill_no=mr_expense,
                    date=loanvoucher.date,
                    description=f"Purchase entry for {loanvoucher.particulars}",
                    debit=amount,
                    credit=0,
                    carrier=loanvoucher.carrier,
                    loan_status="Purchase",
                    tbl_id=loanvoucher.id,
                    tbl_name='Received'
                )
            
                RestTransactionHistory.objects.create(
                    project=loanvoucher.project_name,
                    transaction_type='Purchase',
                    head_of_account=purchase_head,  # <-- Use Purchase Account head
                    cash_type=no_method,
                    cheque_number=None,
                    amount=amount,
                    date=loanvoucher.date or timezone.now().date(),
                    reference=mr_expense,
                    create_by=getattr(loanvoucher, 'created_by', ''),
                    particulars=f"Purchase entry for {loanvoucher.particulars}",
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
            # DYNAMIC TYPE NAME
            type_name = None
            if loanvoucher.type == 'Vendor' and loanvoucher.vendor_name:
                type_name = loanvoucher.vendor_name
            elif loanvoucher.type == 'Conductor' and loanvoucher.conductor_name:
                type_name = loanvoucher.conductor_name
            elif loanvoucher.type == 'Customer' and loanvoucher.customer_name:
                type_name = loanvoucher.customer_name
            elif loanvoucher.type == 'Expense' and loanvoucher.source_name:
                type_name = loanvoucher.source_name
            elif loanvoucher.type == 'Purchase' and loanvoucher.purchase_name:
                type_name = loanvoucher.purchase_name
            elif loanvoucher.type == 'Employee' and loanvoucher.empl_name:
                type_name = loanvoucher.empl_name
            elif loanvoucher.type == 'Bank' and loanvoucher.bankName:
                type_name = loanvoucher.bankName.cash_type_name

            # ---------------------------------------------------
            # SECOND LEDGER ENTRY — MAIN ENTRY (DYNAMIC)
            # ---------------------------------------------------
            
            # Determine which fields to fill based on type
            ledger_exp = loanvoucher.source_name if loanvoucher.type == 'Expense' else None
            ledger_purchase = loanvoucher.purchase_name if loanvoucher.type == 'Purchase' else None
            
            ledger_head = None
            if loanvoucher.type == 'Expense':
                ledger_head = RestHeadOfAccount.objects.get(head_name="Expense Account")
            elif loanvoucher.type == 'Purchase':
                ledger_head = RestHeadOfAccount.objects.get(head_name="Purchase Account")
            else:
                ledger_head = loanvoucher.headAcct  # fallback
            
            LedgerRestEntry.objects.create(
                project_name=loanvoucher.project_name,
                type=loanvoucher.type,
                customer_name=loanvoucher.customer_name if loanvoucher.type == 'Customer' else None,
                contructor=loanvoucher.conductor_name if loanvoucher.type == 'Conductor' else None,
                vendor=loanvoucher.vendor_name if loanvoucher.type == 'Vendor' else None,
                exp_name=ledger_exp,
                purchase=ledger_purchase,
                bankName=loanvoucher.bankName if loanvoucher.type == 'Bank' else None,
                type_name=type_name,            # already set dynamically
                cash_type=no_method,            # always No_Method
                head=ledger_head,               # dynamic head
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
        form = RestLoanVoucherForm()

    # -----------------------------------------------------------
    # PAGE LOAD SUPPORT DATA
    # -----------------------------------------------------------
    expenses = RestExpense.objects.all()
    rdaEmployees = RestaurantEmployee.objects.all()
    selected_expense_name = ''

    form.fields['empl_name'].choices = [('', 'Select Employee Name')] + [
        (emp.rda_emp_name, emp.rda_emp_name) for emp in rdaEmployees
    ]

    if form.is_bound and form.is_valid():
        selected_expense = form.cleaned_data.get('expense_name')
        if selected_expense:
            selected_expense_name = f"{selected_expense.expense_code} - {selected_expense.expense_name}"
            

    No_Method = get_object_or_404(CashRestType, cash_type_name='No_Method')

    return render(request, 'restaurant/loanvoucher/add_rechvoucher.html', {
        'No_Method': [No_Method],
        'form': form,
        'expenses': expenses,
        'selected_expense_name': selected_expense_name,
        'today': now().date(),
    })
    
    
    

@login_required
def rest_loanvoucher_pay_list(request):
    date_filter = request.GET.get('date')
    vouchers = RestLoanVoucher.objects.select_related(
        'project_name', 'customer_name', 'conductor_name', 'expense_name'
    ).filter(loan_status="Payable")

    if date_filter:
        vouchers = vouchers.filter(date=date_filter)

    vouchers = vouchers.order_by('-date')

    return render(request, 'restaurant/loanvoucher/loanvoucher_pay_list.html', {
        'vouchers': vouchers,
    })




@login_required
def rest_loanvoucher_recv_list(request):
    date_filter = request.GET.get('date')

    vouchers = RestLoanVoucher.objects.select_related(
        'project_name', 'customer_name', 'conductor_name', 'expense_name'
    ).filter(loan_status="Receivable")

    if date_filter:
        vouchers = vouchers.filter(date=date_filter)

    vouchers = vouchers.order_by('-date')

    return render(request, 'restaurant/loanvoucher/loanvoucher_recv_list.html', {
        'vouchers': vouchers,
    })



@login_required
def rest_loan_voucher_pdf(request, pk):
    voucher = get_object_or_404(RestLoanVoucher, pk=pk)

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
    return render(request, 'restaurant/loanvoucher/print_loanvoucher.html', context)
    
    




@login_required
def rest_edit_loanvoucher(request, pk):
    voucher = get_object_or_404(RestLoanVoucher, pk=pk)
    form = RestLoanVoucherForm(request.POST or None, instance=voucher)

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
            LedgerRestEntry.objects.filter(
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
            RestTransactionHistory.objects.filter(
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

        return redirect('rest_loanvoucher_list')

    return render(
        request,
        'restaurant/loanvoucher/edit_loanvoucher.html',
        {'form': form, 'voucher': voucher}
    )




@login_required
def rest_delete_loanvoucher(request, pk):
    voucher = get_object_or_404(RestLoanVoucher, pk=pk)
    if request.method == 'POST':
        log_deleted_data(voucher, request.user)
        voucher.delete()
        return redirect('rest_loanvoucher_list')
    return render(request, 'restaurant/loanvoucher/delete_loanvoucher.html', {'voucher': voucher})

 

# from django.shortcuts import render, redirect
# from django.forms import modelformset_factory
# from django.contrib import messages
# from django.urls import reverse
# from django.db import transaction
# from django.contrib.auth.decorators import login_required
# from django.db.models import Sum
# import uuid


# @login_required
# def collection_create(request):

#     CollectionFormSet = modelformset_factory(
#         Collection,
#         fields=(
#             'type',
#             'employee',
#             'customer_name',
#             'sales_type',
#             'amount',
#             'cash_type',
#         ),
#         extra=10,
#         can_delete=False
#     )

#     selected_date = request.GET.get('date') or request.POST.get('date')
#     selected_project = request.GET.get('project') or request.POST.get('project')

#     queryset = Collection.objects.none()

#     if selected_date and selected_project and str(selected_project).isdigit():
#         queryset = Collection.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#     # Fetch both target project IDs so we can show customers from both projects
#     allowed_project_ids = list(
#         ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         ).values_list('id', flat=True)
#     )

#     if request.method == 'POST':
#         formset = CollectionFormSet(request.POST, queryset=queryset)
        
#         # 🔄 Apply query filters during validation (POST)
#         if selected_project and str(selected_project).isdigit():
#             proj_id = int(selected_project)
#             for form in formset.forms:
#                 # Employee: filtered by current selected project & active status
#                 if 'employee' in form.fields:
#                     form.fields['employee'].queryset = form.fields['employee'].queryset.filter(
#                         project_name_id=proj_id, 
#                         rda_active_status=True
#                     )
#                 # Customer: allowed from both project IDs
#                 if 'customer_name' in form.fields:
#                     form.fields['customer_name'].queryset = form.fields['customer_name'].queryset.filter(
#                         project_id__in=allowed_project_ids
#                     )

#         if formset.is_valid():
#             with transaction.atomic():

#                 for form in formset:
#                     if not form.cleaned_data:
#                         continue

#                     obj = form.save(commit=False)
#                     obj.date = selected_date
#                     obj.project_id = int(selected_project)

#                     data = form.cleaned_data

#                     sales_type = data.get('sales_type')
#                     amount = data.get('amount')
#                     cash_type = data.get('cash_type')
#                     type_value = data.get('type')
#                     employee = data.get('employee')
#                     customer_obj = data.get('customer_name')

#                     if not sales_type or not amount:
#                         continue

#                     obj.sales_type = sales_type
#                     obj.amount = amount
#                     obj.cash_type = cash_type

#                     if type_value == "rda_emp_name":
#                         obj.employee = employee
#                         obj.customer_name = None
#                     elif type_value == "Customer":
#                         obj.customer_name = customer_obj
#                         obj.employee = None
#                     else:
#                         obj.employee = None
#                         obj.customer_name = None

#                     obj.save()

#                     # =========================
#                     # 🔥 VOUCHER SYNC LOGIC
#                     # =========================
#                     head_of_account = RestHeadOfAccount.objects.filter(
#                         head_name__icontains='Customer Accounts'
#                     ).first()

#                     voucher_obj = None

#                     if obj.cret_id:
#                         try:
#                             voucher_obj = CreditRestVoucher.objects.get(id=int(obj.cret_id))
#                         except:
#                             voucher_obj = None

#                     # =========================
#                     # 🔁 UPDATE VOUCHER
#                     # =========================
#                     if voucher_obj:
#                         voucher_obj.project_name = obj.project
#                         voucher_obj.type = type_value or "Collection"
#                         voucher_obj.cash_type = cash_type
#                         voucher_obj.head_of_account = head_of_account
#                         voucher_obj.date = selected_date
#                         voucher_obj.bill_date = selected_date
#                         voucher_obj.amount = amount
#                         voucher_obj.particulars = f"Collection entry for {sales_type}"
#                         voucher_obj.is_confirmed = True

#                         if type_value == "RestaurantEmployee":
#                             voucher_obj.rda_emp_name = str(employee)
#                             voucher_obj.customer_name = None
#                         elif type_value == "Customer":
#                             voucher_obj.customer_name = customer_obj
#                             voucher_obj.empl_name = None

#                         voucher_obj.save()

#                     # =========================
#                     # ➕ CREATE VOUCHER
#                     # =========================
#                     else:
#                         voucher_obj = CreditRestVoucher.objects.create(
#                             project_name=obj.project,
#                             type=type_value or "Collection",
#                             cash_type=cash_type,
#                             head_of_account=head_of_account,
#                             date=selected_date,
#                             bill_date=selected_date,
#                             amount=amount,
#                             particulars=f"Collection entry for {sales_type}",
#                             mr_or_bill_no=f"COL-{uuid.uuid4().hex[:10]}",
#                             create_cr=request.user.username,
#                             is_confirmed=True,
#                             empl_name=str(employee) if type_value == "Employee" else None,
#                             customer_name=customer_obj if type_value == "Customer" else None,
#                             reqs_id=0,
#                             res_status='Collection'
#                         )

#                         obj.cret_id = str(voucher_obj.id)
#                         obj.save(update_fields=['cret_id'])

#             messages.success(request, "Collection & Credit Voucher saved successfully!")
#             return redirect(
#                 f"{reverse('collection_add')}?date={selected_date}&project={selected_project}"
#             )

#         else:
#             messages.error(request, "Please fix the errors in the form.")

#     else:
#         formset = CollectionFormSet(queryset=queryset)
        
#         # 🔄 Apply query filters during page load (GET)
#         if selected_project and str(selected_project).isdigit():
#             proj_id = int(selected_project)
#             for form in formset.forms:
#                 # Employee: filtered by current project name & active status
#                 if 'employee' in form.fields:
#                     form.fields['employee'].queryset = form.fields['employee'].queryset.filter(
#                         project_name_id=proj_id, 
#                         rda_active_status=True
#                     )
                
#                 # Customer: Filtered to show customers from both allowed projects
#                 if 'customer_name' in form.fields:
#                     form.fields['customer_name'].queryset = form.fields['customer_name'].queryset.filter(
#                         project_id__in=allowed_project_ids
#                     )

#     # =========================
#     # TOTALS
#     # =========================
#     total_sale = sum(obj.amount or 0 for obj in queryset)

#     total_summary = 0
#     if selected_date and selected_project and str(selected_project).isdigit():
#         total_summary = Collection.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'restaurant/collection_form.html', {
#         'formset': formset,
#         'projects': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         ),
#         'selected_date': selected_date,
#         'selected_project': selected_project,
#         'total_sale': total_sale,
#         'total_summary': total_summary,
#     })
    
from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import uuid


@login_required
def collection_create(request):

    CollectionFormSet = modelformset_factory(
        Collection,
        fields=(
            'type',
            'employee',
            'customer_name',
            'sales_type',
            'amount',
            'cash_type',
        ),
        extra=10,
        can_delete=False
    )

    selected_date = request.GET.get('date') or request.POST.get('date')
    selected_project = request.GET.get('project') or request.POST.get('project')

    queryset = Collection.objects.none()

    if selected_date and selected_project and str(selected_project).isdigit():
        queryset = Collection.objects.filter(
            date=selected_date,
            project_id=int(selected_project)
        )

    # Fetch both target project IDs so we can show customers from both projects
    allowed_project_ids = list(
        ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ).values_list('id', flat=True)
    )

    if request.method == 'POST':
        formset = CollectionFormSet(request.POST, queryset=queryset)
        
        # 🔄 Apply query filters during validation (POST)
        if selected_project and str(selected_project).isdigit():
            proj_id = int(selected_project)
            for form in formset.forms:
                # Employee: filtered by current selected project & active status
                if 'employee' in form.fields:
                    form.fields['employee'].queryset = form.fields['employee'].queryset.filter(
                        project_name_id=proj_id, 
                        rda_active_status=True
                    )
                # Customer: allowed from both project IDs
                if 'customer_name' in form.fields:
                    form.fields['customer_name'].queryset = form.fields['customer_name'].queryset.filter(
                        project_id__in=allowed_project_ids
                    )

        if formset.is_valid():
            with transaction.atomic():

                for form in formset:
                    if not form.cleaned_data:
                        continue

                    # Avoid saving empty extra forms if they haven't changed
                    if not form.has_changed() and form in formset.extra_forms:
                        continue

                    data = form.cleaned_data

                    sales_type = data.get('sales_type')
                    amount = data.get('amount')
                    cash_type = data.get('cash_type')
                    type_value = data.get('type')
                    employee = data.get('employee')          # RestaurantEmployee instance
                    customer_obj = data.get('customer_name')  # Customer instance

                    if not sales_type or amount is None:
                        continue

                    obj = form.save(commit=False)
                    obj.date = selected_date
                    obj.project_id = int(selected_project)
                    obj.sales_type = sales_type
                    obj.amount = amount
                    obj.cash_type = cash_type

                    # 🌟 FIX: Updated match condition to map "Employee" string cleanly
                    if type_value == "Employee":
                        obj.employee = employee
                        obj.customer_name = None
                    elif type_value == "Customer":
                        obj.customer_name = customer_obj
                        obj.employee = None
                    else:
                        obj.employee = None
                        obj.customer_name = None

                    obj.save()

                    # =========================
                    # 🔥 VOUCHER SYNC LOGIC
                    # =========================
                    head_of_account = RestHeadOfAccount.objects.filter(
                        head_name__icontains='Customer Accounts'
                    ).first()

                    voucher_obj = None

                    if obj.cret_id:
                        try:
                            voucher_obj = CreditRestVoucher.objects.get(id=int(obj.cret_id))
                        except (CreditRestVoucher.DoesNotExist, ValueError, TypeError):
                            voucher_obj = None

                    # Safely convert employee object into raw text string name
                    emp_name_str = employee.rda_emp_name if employee else None

                    # Inspect fields on your target CreditRestVoucher model dynamically
                    voucher_fields = [f.name for f in CreditRestVoucher._meta.get_fields()]

                    # =========================
                    # 🔁 UPDATE VOUCHER
                    # =========================
                    if voucher_obj:
                        voucher_obj.project_name = obj.project
                        voucher_obj.type = type_value or "Collection"
                        voucher_obj.cash_type = cash_type
                        voucher_obj.head_of_account = head_of_account
                        voucher_obj.date = selected_date
                        voucher_obj.bill_date = selected_date
                        voucher_obj.amount = amount
                        voucher_obj.particulars = f"Collection entry for {sales_type}"
                        voucher_obj.is_confirmed = True

                        # 🌟 FIX: Checked for consistent "Employee" value assignment
                        if type_value == "Employee":
                            if 'empl_name' in voucher_fields:
                                voucher_obj.empl_name = emp_name_str
                            if 'rda_emp_name' in voucher_fields:
                                voucher_obj.rda_emp_name = emp_name_str
                            voucher_obj.customer_name = None
                        elif type_value == "Customer":
                            voucher_obj.customer_name = customer_obj
                            if 'empl_name' in voucher_fields:
                                voucher_obj.empl_name = None
                            if 'rda_emp_name' in voucher_fields:
                                voucher_obj.rda_emp_name = None

                        voucher_obj.save()

                    # =========================
                    # ➕ CREATE VOUCHER
                    # =========================
                    else:
                        voucher_data = {
                            'project_name': obj.project,
                            'type': type_value or "Collection",
                            'cash_type': cash_type,
                            'head_of_account': head_of_account,
                            'date': selected_date,
                            'bill_date': selected_date,
                            'amount': amount,
                            'particulars': f"Collection entry for {sales_type}",
                            'mr_or_bill_no': f"COL-{uuid.uuid4().hex[:10]}",
                            'create_cr': request.user.username,
                            'is_confirmed': True,
                            'customer_name': customer_obj if type_value == "Customer" else None,
                            'reqs_id': 0,
                            'res_status': 'Collection'
                        }

                        # 🌟 FIX: Inject correct employee text column dynamically
                        if type_value == "Employee":
                            if 'empl_name' in voucher_fields:
                                voucher_data['empl_name'] = emp_name_str
                            if 'rda_emp_name' in voucher_fields:
                                voucher_data['rda_emp_name'] = emp_name_str
                        else:
                            if 'empl_name' in voucher_fields:
                                voucher_data['empl_name'] = None
                            if 'rda_emp_name' in voucher_fields:
                                voucher_data['rda_emp_name'] = None

                        voucher_obj = CreditRestVoucher.objects.create(**voucher_data)

                        obj.cret_id = str(voucher_obj.id)
                        obj.save(update_fields=['cret_id'])

            messages.success(request, "Collection & Credit Voucher saved successfully!")
            
            try:
                redirect_url = f"{reverse('collection_add')}?date={selected_date}&project={selected_project}"
            except Exception:
                redirect_url = f"{reverse('collection_create')}?date={selected_date}&project={selected_project}"
                
            return redirect(redirect_url)

        else:
            messages.error(request, "Please fix the errors in the form.")

    else:
        formset = CollectionFormSet(queryset=queryset)
        
        # 🔄 Apply query filters during page load (GET)
        if selected_project and str(selected_project).isdigit():
            proj_id = int(selected_project)
            for form in formset.forms:
                # Employee: filtered by current project name & active status
                if 'employee' in form.fields:
                    form.fields['employee'].queryset = form.fields['employee'].queryset.filter(
                        project_name_id=proj_id, 
                        rda_active_status=True
                    )
                
                # Customer: Filtered to show customers from both allowed projects
                if 'customer_name' in form.fields:
                    form.fields['customer_name'].queryset = form.fields['customer_name'].queryset.filter(
                        project_id__in=allowed_project_ids
                    )

    # =========================
    # TOTALS
    # =========================
    total_sale = sum(obj.amount or 0 for obj in queryset)

    total_summary = 0
    if selected_date and selected_project and str(selected_project).isdigit():
        total_summary = Collection.objects.filter(
            date=selected_date,
            project_id=int(selected_project)
        ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'restaurant/collection_form.html', {
        'formset': formset,
        'projects': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'selected_date': selected_date,
        'selected_project': selected_project,
        'total_sale': total_sale,
        'total_summary': total_summary,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Collection

@login_required
def collection_list(request):

    collections = Collection.objects.select_related(
        'project',
        'employee',
        'customer_name',
        'sales_type',
        'cash_type'
    ).order_by('-date', '-id')

    context = {
        'collections': collections,
    }

    return render(request, 'restaurant/collection_list.html', context)
    


from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Collection, ProjectFirstLevelName

@login_required
def month_collection_list(request):
    collections = Collection.objects.select_related(
        'project',
        'employee',
        'customer_name',
        'sales_type',
        'cash_type'
    ).order_by('-date', '-id')

    # Fetch specific projects for the dropdown filter
    projects = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    # Get filter values from GET parameters
    selected_month = request.GET.get('month')
    selected_project = request.GET.get('project')

    # Apply Month Filter
    if selected_month:
        try:
            year, month = selected_month.split('-')
            collections = collections.filter(date__year=int(year), date__month=int(month))
        except ValueError:
            pass

    # Apply Project Filter
    if selected_project:
        collections = collections.filter(project_id=selected_project)

    # Calculate filtered total amount
    total_amount = collections.aggregate(sum_val=Sum('amount'))['sum_val'] or 0

    # Calculate final total amount (grand total)
    final_total_amount = Collection.objects.aggregate(sum_val=Sum('amount'))['sum_val'] or 0

    context = {
        'collections': collections,
        'projects': projects,
        'selected_month': selected_month,
        'selected_project': selected_project,
        'total_amount': total_amount,
        'final_total_amount': final_total_amount,
    }

    return render(request, 'restaurant/month_collection_list.html', context)

# @login_required
# def collection_edit(request, pk):

#     collection = get_object_or_404(Collection, pk=pk)

#     if request.method == 'POST':
#         form = CollectionForm(request.POST, instance=collection)

#         if form.is_valid():
#             form.save()
#             messages.success(request, "Collection updated successfully!")
#             return redirect('collection_list')
#     else:
#         form = CollectionForm(instance=collection)

#     return render(request, 'restaurant/collection_form_edit.html', {
#         'form': form
#     })
    
    



@login_required
def collection_edit(request, pk):

    collection = get_object_or_404(Collection, pk=pk)

    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection)

        if form.is_valid():

            obj = form.save()   # ✅ update Collection first

            # =========================
            # 🔥 SYNC VOUCHER UPDATE
            # =========================
            if obj.cret_id:

                try:
                    voucher = CreditRestVoucher.objects.get(id=int(obj.cret_id))
                except:
                    voucher = None

                if voucher:

                    voucher.project_name = obj.project
                    voucher.type = obj.type or "Collection"
                    voucher.cash_type = obj.cash_type
                    voucher.date = obj.date
                    voucher.bill_date = obj.date
                    voucher.amount = obj.amount
                    voucher.particulars = f"Collection entry for {obj.sales_type}"
                    voucher.is_confirmed = True

                    if obj.type == "Employee":
                        voucher.empl_name = str(obj.employee)
                        voucher.customer_name = None
                    elif obj.type == "Customer":
                        voucher.customer_name = obj.customer_name
                        voucher.empl_name = None

                    voucher.save()

            messages.success(request, "Collection and Voucher updated successfully!")
            return redirect('collection_list')

    else:
        form = CollectionForm(instance=collection)

    return render(request, 'restaurant/collection_form_edit.html', {
        'form': form
    })
    
# @login_required
# def collection_delete(request, pk):

#     collection = get_object_or_404(Collection, pk=pk)

#     if request.method == 'POST':
#         collection.delete()
#         messages.success(request, "Collection deleted successfully!")
#         return redirect('collection_list')

#     return render(request, 'restaurant/collection_confirm_delete.html', {
#         'collection': collection
#     })
    




@login_required
def collection_delete(request, pk):

    collection = get_object_or_404(Collection, pk=pk)

    if request.method == 'POST':

        # =========================
        # 🔥 DELETE RELATED VOUCHER FIRST
        # =========================
        if collection.cret_id:
            try:
                CreditRestVoucher.objects.filter(
                    id=int(collection.cret_id)
                ).delete()
            except:
                pass

        # =========================
        # 🗑 DELETE COLLECTION
        # =========================
        collection.delete()

        messages.success(request, "Collection and related voucher deleted successfully!")
        return redirect('collection_list')

    return render(request, 'restaurant/collection_confirm_delete.html', {
        'collection': collection
    })
    
    

# @login_required
# def rest_approve_cr_voucher(request, pk):
#     voucher = get_object_or_404(CreditRestVoucher, pk=pk)
#     updated_items = []

#     # If already approved, redirect
#     if voucher.approval_cr_status:
#         return redirect('rest_creditvoucher_list')

#     # Generate MR/Bill No if not set
#     if not voucher.mr_or_bill_no:
#         base_code = "MBC-"
#         last = (
#             CreditRestVoucher.objects.filter(mr_or_bill_no__startswith=base_code)
#             .order_by('-id')
#             .first()
#         )
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"

#         while CreditRestVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
#             next_id += 1
#             generated_code = f"{base_code}{next_id:05d}"

#         voucher.mr_or_bill_no = generated_code

#     # Approve the voucher
#     voucher.approval_cr_status = True
#     voucher.save()
#     updated_items.append(voucher)

#     # Update CashType balance
#     try:
#         cash_type = CashRestType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount += voucher.amount
#         cash_type.type_note = f"Update Received Amount of voucher ID {voucher.id}"
#         cash_type.save()
#     except CashRestType.DoesNotExist:
#         cash_type = None  # prevent crash later
    
#     type_name = voucher.customer_name if voucher.type == 'Customer' and voucher.customer_name else None
#     # Log transaction
#     RestTransactionHistory.objects.create(
#         project=voucher.project_name,  # FK to ProjectFirstLevelName
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount,
#         cheque_number=voucher.cheque_number,
#         date=timezone.now().date(),
#         type_name=type_name,
#         reference=voucher.mr_or_bill_no,
#         create_by=voucher.create_cr,
#         particulars=voucher.particulars,
#         tbl_id=voucher.id,
#         tbl_name='Received',
#     )

#     # Create ledger entries
#     for item in updated_items:
#         if item.res_status == 'Collection':
#             loan_status = 'payment'
#         else:
#             loan_status = 'received'
#         amount = item.amount or 0
#         debit_amount = amount if loan_status == 'payment' else 0
#         credit_amount = amount if loan_status == 'received' else 0
        
#         type_name = None

#         if item.type == 'Customer':
#             type_name = item.customer_name
#         elif item.type == 'Employee':
#             type_name = item.empl_name
            
#         LedgerRestEntry.objects.create(
#             project_name=item.project_name,  # FK to ProjectFirstLevelName
#             type=item.type,
#             contructor=getattr(item, 'contructor', None),
#             vendor=getattr(item, 'vendor', None),
#             customer_name=getattr(item, 'customer_name', None),
#             bankName=getattr(item, 'bankName', None),  # reused field
#             capi_name=getattr(item, 'capi_name', None),
#             invest_name=getattr(item, 'invest_name', None),
#             cash_type=item.cash_type,
#             cheque_number=item.cheque_number,
#             head=item.head_of_account,
#             mr_or_bill_no=None,
#             type_name=type_name,
#             date=timezone.now().date(),
#             description=item.particulars or '',
#             debit=debit_amount,
#             credit=credit_amount,
#             carrier=getattr(item, 'carrier', None),
#             loan_status=loan_status,
#             tbl_id=item.id,
#             tbl_name='Received'
#         )
#     sms_number = "8801913222203"
#     sms_message = (
#         f"We have successfully received your payment of ৳{voucher.amount}.\n"
#         f"Thank you for your transaction.\n"
#         f"{voucher.project_name}"
#     )
    
#     # Send SMS safely (no crash even if SMS fails)
#     if not send_sms(sms_number, sms_message):
#         print("SMS sending failed (ignored).")
        
#     return redirect('rest_creditvoucher_list')
    
    

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def rest_approve_cr_voucher(request, pk):

    voucher = get_object_or_404(CreditRestVoucher, pk=pk)

    # If already approved
    if voucher.approval_cr_status:
        return redirect('rest_creditvoucher_list')

    # Generate MR/Bill No
    if not voucher.mr_or_bill_no:
        base_code = "MBC-"

        last = (
            CreditRestVoucher.objects
            .filter(mr_or_bill_no__startswith=base_code)
            .order_by('-id')
            .first()
        )

        next_id = (last.id + 1) if last else 1
        generated_code = f"{base_code}{next_id:05d}"

        while CreditRestVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
            next_id += 1
            generated_code = f"{base_code}{next_id:05d}"

        voucher.mr_or_bill_no = generated_code

    # Approve voucher
    voucher.approval_cr_status = True
    voucher.save()

    # Update Cash Balance
    cash_type = voucher.cash_type

    if cash_type:
        cash_type.type_amount += voucher.amount
        cash_type.type_note = f"Update Received Amount of voucher ID {voucher.id}"
        cash_type.save()

    # Determine type_name
    type_name = None

    if voucher.type == "Customer":
        type_name = voucher.customer_name
    elif voucher.type == "Employee":
        type_name = voucher.empl_name

    # Transaction History
    RestTransactionHistory.objects.create(
        project=voucher.project_name,
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

    # Determine loan status
    if voucher.res_status == 'Collection':
        loan_status = 'payment'
    else:
        loan_status = 'received'

    amount = voucher.amount or 0

    debit_amount = amount if loan_status == 'payment' else 0
    credit_amount = amount if loan_status == 'received' else 0

    # Ledger Entry
    LedgerRestEntry.objects.create(
        project_name=voucher.project_name,
        type=voucher.type,
        contructor=voucher.contructor,
        vendor=voucher.vendor,
        customer_name=voucher.customer_name,
        empl_name=voucher.empl_name,
        bankName=None,
        capi_name=voucher.capi_name,
        invest_name=voucher.invest_name,
        cash_type=voucher.cash_type,
        cheque_number=voucher.cheque_number,
        head=voucher.head_of_account,
        mr_or_bill_no=voucher.mr_or_bill_no,
        type_name=type_name,
        date=timezone.now().date(),
        description=voucher.particulars or '',
        debit=debit_amount,
        credit=credit_amount,
        carrier=voucher.carrier,
        entry_date=voucher.date,
        loan_status=loan_status,
        tbl_id=voucher.id,
        tbl_name='Received'
    )

    #Send SMS
    sms_number = "8801913222203"

    sms_message = (
        f"We have successfully received your payment of ৳{voucher.amount}.\n"
        f"Thank you for your transaction.\n"
        f"{voucher.project_name}"
    )

    if not send_sms(sms_number, sms_message):
        print("SMS sending failed (ignored).")

    return redirect('rest_creditvoucher_list')
    




from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction


@login_required
def rest_all_approve_cr_voucher(request):

    if request.method != "POST":
        return redirect('rest_credit_allvoucher_approve')

    voucher_ids = request.POST.getlist('voucher_ids')

    print("SELECTED IDS:", voucher_ids)

    if not voucher_ids:

        messages.error(
            request,
            "Please select at least one voucher."
        )

        return redirect(
            'rest_credit_allvoucher_approve'
        )

    vouchers = CreditRestVoucher.objects.filter(
        id__in=voucher_ids
    )

    print("TOTAL VOUCHERS:", vouchers.count())

    for voucher in vouchers:

        try:

            with transaction.atomic():

                print("PROCESSING:", voucher.id)

                # =================================
                # SKIP IF ALREADY APPROVED
                # =================================

                if voucher.approval_cr_status:
                    continue


                # =================================
                # MR NUMBER
                # =================================

                if not voucher.mr_or_bill_no:

                    voucher.mr_or_bill_no = (
                        f"MBC-{voucher.id:05d}"
                    )


                # =================================
                # APPROVE
                # =================================

                voucher.approval_cr_status = True
                voucher.save()

                print("VOUCHER UPDATED")


                # =================================
                # CASH UPDATE
                # =================================

                if voucher.cash_type:

                    current_amount = (
                        voucher.cash_type.type_amount or 0
                    )

                    voucher.cash_type.type_amount = (
                        current_amount + voucher.amount
                    )

                    voucher.cash_type.save()

                    print("CASH UPDATED")


                # =================================
                # TYPE NAME
                # =================================

                type_name = ""

                if voucher.customer_name:
                    type_name = str(
                        voucher.customer_name
                    )

                elif voucher.vendor:
                    type_name = str(
                        voucher.vendor
                    )

                elif voucher.contructor:
                    type_name = str(
                        voucher.contructor
                    )

                elif voucher.empl_name:
                    type_name = voucher.empl_name


                # =================================
                # TRANSACTION HISTORY
                # =================================

                transaction_obj = RestTransactionHistory.objects.create(

                    project=voucher.project_name,

                    transaction_type=voucher.type,

                    head_of_account=voucher.head_of_account,

                    cash_type=voucher.cash_type,

                    cheque_number=voucher.cheque_number,

                    amount=voucher.amount,

                    date=timezone.now().date(),

                    type_name=type_name,

                    reference=voucher.mr_or_bill_no,

                    create_by=voucher.create_cr,

                    particulars=voucher.particulars,

                    tbl_id=voucher.id,

                    tbl_name='Received'
                )

                print(
                    "TRANSACTION SAVED:",
                    transaction_obj.id
                )


                # =================================
                # LOAN STATUS
                # =================================

                loan_status = 'received'

                if voucher.res_status == 'Collection':
                    loan_status = 'payment'


                debit_amount = 0
                credit_amount = 0

                if loan_status == 'payment':
                    debit_amount = voucher.amount
                else:
                    credit_amount = voucher.amount


                # =================================
                # LEDGER ENTRY
                # =================================

                ledger_obj = LedgerRestEntry.objects.create(

                    project_name=voucher.project_name,

                    type=voucher.type,

                    contructor=voucher.contructor,

                    vendor=voucher.vendor,

                    customer_name=voucher.customer_name,

                    empl_name=voucher.empl_name,

                    bankName=None,

                    capi_name=voucher.capi_name,

                    reve_name=voucher.reve_name,

                    invest_name=voucher.invest_name,

                    cash_type=voucher.cash_type,

                    cheque_number=voucher.cheque_number,

                    head=voucher.head_of_account,

                    mr_or_bill_no=voucher.mr_or_bill_no,

                    type_name=type_name,

                    date=timezone.now().date(),

                    description=voucher.particulars,

                    debit=debit_amount,

                    credit=credit_amount,

                    carrier=voucher.carrier,

                    entry_date=voucher.date,

                    loan_status=loan_status,

                    tbl_id=voucher.id,

                    tbl_name='Received'
                )

                print(
                    "LEDGER SAVED:",
                    ledger_obj.id
                )

        except Exception as e:

            print("FULL ERROR:", str(e))

            messages.error(
                request,
                f"Voucher {voucher.id} Error: {str(e)}"
            )

    messages.success(
        request,
        "Selected vouchers approved successfully!"
    )

    return redirect(
        'rest_credit_allvoucher_approve'
    )
    



# import uuid
# from decimal import Decimal
# from datetime import date
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import transaction
# from django.db.models import Sum
# from django.forms import modelformset_factory
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# from django.utils import timezone
# from restaurant.models import RestaurantKitchenLedger, RestaurantItem



# @login_required
# def restaurant_kitchen_ledger_payment(request):
#     selected_date = request.GET.get('date') or request.POST.get('date')
#     if not selected_date:
#         selected_date = timezone.now().date().strftime('%Y-%m-%d')

#     selected_project = (
#         request.GET.get('project_id')
#         or request.GET.get('project')
#         or request.POST.get('project_id')
#         or request.POST.get('project')
#     )
#     target_type = request.GET.get('type_name') or request.POST.get('target_type')

#     # Match Employee routing boundaries to the Project context
#     assigned_employee_id = None
#     if selected_project and str(selected_project).isdigit():
#         p_id = int(selected_project)
#         if p_id == 36:
#             assigned_employee_id = 24
#         elif p_id == 60:
#             assigned_employee_id = 54

#     queryset = DailyPayment.objects.none()

#     if selected_date and selected_project and str(selected_project).isdigit():
#         queryset = DailyPayment.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#     extra_forms = 0 if queryset.exists() else 1
#     DailyPaymentFormSet = modelformset_factory(
#         DailyPayment,
#         form=DailyPaymentForm,
#         extra=extra_forms,
#         can_delete=True
#     )

#     # ==========================================
#     # 🔁 POST PROCESSING & PAYMENT VOUCHER PIPELINE
#     # ==========================================
#     if request.method == "POST":
#         formset = DailyPaymentFormSet(request.POST, queryset=queryset)

#         if formset.is_valid():
#             try:
#                 with transaction.atomic():
#                     total_formset_debit = Decimal('0.00')
                    
#                     for form in formset.forms:
#                         if not form.cleaned_data:
#                             continue

#                         # --- REMOVE ACTIONS ---
#                         if form.cleaned_data.get('DELETE'):
#                             obj = form.instance
#                             if obj.pk:
#                                 DebitRestVoucher.objects.filter(requi_id=obj.id).delete()
#                                 LedgerRestEntry.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 RestTransactionHistory.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 obj.delete()
#                             continue

#                         # --- COMMIT/MUTATE DAILY PAYMENTS ---
#                         obj = form.save(commit=False)
#                         obj.date = selected_date
#                         obj.project_id = int(selected_project)

#                         if not obj.amount or obj.amount <= 0:
#                             continue

#                         obj.save()
#                         total_formset_debit += obj.amount

#                         # --- UNIQUE VOUCHER STRINGS ENGINE ---
#                         if not obj.pay_id:
#                             obj.pay_id = f"PAY-{obj.id}"
#                             obj.save(update_fields=['pay_id'])

#                         # --- MATCH FINANCIAL CHART OF ACCOUNTS HEADS ---
#                         if obj.type == "Expense":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Expense Account').first()
#                         elif obj.type == "Purchase":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Purchase Account').first()
#                         else:
#                             head = None

#                         # --- CHECK CHEQUE / PAYMENT VOUCHER CONFIGURATIONS ---
#                         cheque_id = request.POST.get(f"{form.prefix}-cheque_number") or request.POST.get('cheque_number')

#                         # --- UPDATE/CREATE DEBIT REST VOUCHERS (Payment Voucher Integration) ---
#                         voucher = DebitRestVoucher.objects.filter(requi_id=obj.id).first()
#                         particulars_text = f"Payment Voucher entry for Kitchen Balance ({obj.type})"

#                         # Map vendor configuration if applicable
#                         voucher_type = "Vendor" if obj.type == "Purchase" else (obj.type or "Expense")
                        
#                         if voucher:
#                             voucher.type = voucher_type
#                             voucher.project_name = obj.project
#                             voucher.cash_type = obj.cash_type
#                             voucher.head_of_account = head
#                             voucher.amount = obj.amount
#                             voucher.date = obj.date
#                             voucher.bill_date = obj.date
#                             voucher.particulars = particulars_text
#                             voucher.expense = obj.rest_exp if obj.type == "Expense" else None
#                             voucher.purchase = obj.pur_cost if obj.type == "Purchase" else None
#                             voucher.save()
#                         else:
#                             voucher = DebitRestVoucher.objects.create(
#                                 type=voucher_type,
#                                 project_name=obj.project,
#                                 cash_type=obj.cash_type,
#                                 head_of_account=head,
#                                 amount=obj.amount,
#                                 date=obj.date,
#                                 bill_date=obj.date,
#                                 particulars=particulars_text,
#                                 mr_or_bill_no=f"PV-{uuid.uuid4().hex[:10]}",
#                                 is_confirmed=True,
#                                 create_dr=request.user.username,
#                                 requi_id=obj.id,
#                                 expense=obj.rest_exp if obj.type == "Expense" else None,
#                                 purchase=obj.pur_cost if obj.type == "Purchase" else None,
#                             )

#                         # Handle optional cheque status tracking if bound
#                         if cheque_id and cheque_id != 'None' and cheque_id.isdigit():
#                             try:
#                                 cheque = RestMainCheque.objects.get(id=int(cheque_id))
#                                 voucher.cheque_number = cheque.cheque_number
#                                 voucher.save()
                                
#                                 cheque.status = 'used'
#                                 cheque.remarks = particulars_text
#                                 cheque.issue_date = obj.date
#                                 cheque.amount = obj.amount
#                                 cheque.save()
#                             except RestMainCheque.DoesNotExist:
#                                 pass

#                         # ==========================================
#                         # 📚 SYNC TO ACCOUNTING (LedgerRestEntry & RestTransactionHistory)
#                         # ==========================================
#                         if head and obj.cash_type:
#                             LedgerRestEntry.objects.update_or_create(
#                                 tbl_id=str(voucher.id),
#                                 tbl_name='DebitRestVoucher',
#                                 defaults={
#                                     'project_name': obj.project,
#                                     'type': voucher_type,
#                                     'cash_type': obj.cash_type,
#                                     'head': head,
#                                     'date': obj.date,
#                                     'description': particulars_text,
#                                     'debit': obj.amount,
#                                     'credit': Decimal('0.00'),
#                                     'mr_or_bill_no': voucher.mr_or_bill_no,
#                                 }
#                             )

#                             username = request.user.username if request.user.is_authenticated else "System"
#                             RestTransactionHistory.objects.update_or_create(
#                                 tbl_id=str(voucher.id),
#                                 tbl_name='DebitRestVoucher',
#                                 defaults={
#                                     'project': obj.project,
#                                     'transaction_type': obj.type,
#                                     'head_of_account': head,
#                                     'cash_type': obj.cash_type,
#                                     'amount': obj.amount,
#                                     'date': obj.date,
#                                     'create_by': username,
#                                     'particulars': particulars_text,
#                                     'reference': voucher.mr_or_bill_no,
#                                     'tbl_id': str(voucher.id),
#                                     'tbl_name': 'DebitRestVoucher',
#                                 }
#                             )

#                     # --- UPDATE RESTAURANT KITCHEN LEDGER SAFELY ---
#                     if selected_project and str(selected_project).isdigit() and target_type:
#                         fallback_employee_id = assigned_employee_id
#                         if not fallback_employee_id:
#                             prior_row = RestaurantKitchenLedger.objects.filter(
#                                 project_id=int(selected_project),
#                                 type=target_type
#                             ).order_by('-created_at').first()
#                             fallback_employee_id = prior_row.employee_id if prior_row else None

#                         if fallback_employee_id:
#                             RestaurantKitchenLedger.objects.update_or_create(
#                                 project_id=int(selected_project),
#                                 type=target_type,
#                                 employee_id=fallback_employee_id,
#                                 defaults={
#                                     'debit': total_formset_debit,
#                                 },
#                             )

#                 messages.success(request, "Payment vouchers successfully generated and synchronized to accounting records!")
#                 balance_param = request.GET.get('balance', '1')
#                 return redirect(
#                     f"{reverse('restaurant_kitchen_ledger_payment')}"
#                     f"?date={selected_date}&project_id={selected_project}&type_name={target_type}&balance={balance_param}"
#                 )
            
#             except Exception as e:
#                 messages.error(request, f"Transactional isolation execution crash: {str(e)}")
#         else:
#             messages.error(request, "Failed validation. Please address errors down in the data-grid entries.")
          
#     # ==========================================
#     # 📑 GET METHOD RENDER PIPELINE
#     # ==========================================
#     else:
#         initial_data_list = []

#         if not queryset.exists() and selected_project and target_type:
#             ledger_qs = RestaurantKitchenLedger.objects.filter(
#                 project_id=selected_project,
#                 type=target_type
#             )

#             balance_amount = ledger_qs.aggregate(
#                 total=Sum('credit') - Sum('debit')
#             )['total'] or Decimal('0.00')

#             fallback_cash = CashRestType.objects.filter(cash_type_name='Supplier Account').first()

#             if balance_amount > 0:
#                 initial_data_list.append({
#                     'type': target_type,
#                     'amount': balance_amount,
#                     'cash_type': fallback_cash.id if fallback_cash else None
#                 })

#         formset = DailyPaymentFormSet(queryset=queryset, initial=initial_data_list)

#     total_summary = Decimal('0.00')
#     expense_total = Decimal('0.00')
#     purchase_total = Decimal('0.00')

#     if selected_date and selected_project and str(selected_project).isdigit():
#         qs = DailyPayment.objects.filter(date=selected_date, project_id=int(selected_project))
#         total_summary = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         expense_total = qs.filter(type="Expense").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         purchase_total = qs.filter(type="Purchase").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#     return render(request, 'restaurant/restaurant_kitchen_ledger_payment.html', {
#         'formset': formset,
#         'projects': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=["The Galleria Restauent Cafe", "The Galleria Live Kitchen"]
#         ),
#         'selected_date': selected_date,
#         'selected_project': selected_project,
#         'target_type': target_type,
#         'total_summary': total_summary,
#         'expense_total': expense_total,
#         'purchase_total': purchase_total,
#         'today': date.today(),
#     })
    
    



# import uuid
# from decimal import Decimal
# from datetime import date
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import transaction
# from django.db.models import Sum
# from django.forms import modelformset_factory
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# from django.utils import timezone
# from restaurant.models import RestaurantKitchenLedger, RestaurantItem



# @login_required
# def restaurant_kitchen_ledger_payment(request):
#     selected_date = request.GET.get('date') or request.POST.get('date')
#     if not selected_date:
#         selected_date = timezone.now().date().strftime('%Y-%m-%d')

#     selected_project = (
#         request.GET.get('project_id')
#         or request.GET.get('project')
#         or request.POST.get('project_id')
#         or request.POST.get('project')
#     )
#     target_type = request.GET.get('type_name') or request.POST.get('target_type')

#     # Match Employee routing boundaries to the Project context
#     assigned_employee_id = None
#     if selected_project and str(selected_project).isdigit():
#         p_id = int(selected_project)
#         if p_id == 36:
#             assigned_employee_id = 24
#         elif p_id == 60:
#             assigned_employee_id = 54

#     queryset = DailyPayment.objects.none()

#     if selected_date and selected_project and str(selected_project).isdigit():
#         queryset = DailyPayment.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#     extra_forms = 0 if queryset.exists() else 1
#     DailyPaymentFormSet = modelformset_factory(
#         DailyPayment,
#         form=DailyPaymentForm,
#         extra=extra_forms,
#         can_delete=True
#     )

#     # ==========================================
#     # 🔁 POST PROCESSING & PAYMENT VOUCHER PIPELINE
#     # ==========================================
#     if request.method == "POST":
#         formset = DailyPaymentFormSet(request.POST, queryset=queryset)

#         if formset.is_valid():
#             try:
#                 with transaction.atomic():
#                     total_formset_debit = Decimal('0.00')
                    
#                     for form in formset.forms:
#                         if not form.cleaned_data:
#                             continue

#                         # --- REMOVE ACTIONS ---
#                         if form.cleaned_data.get('DELETE'):
#                             obj = form.instance
#                             if obj.pk:
#                                 DebitRestVoucher.objects.filter(requi_id=obj.id).delete()
#                                 LedgerRestEntry.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 RestTransactionHistory.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 obj.delete()
#                             continue

#                         # --- COMMIT/MUTATE DAILY PAYMENTS ---
#                         obj = form.save(commit=False)
#                         obj.date = selected_date
#                         obj.project_id = int(selected_project)

#                         if not obj.amount or obj.amount <= 0:
#                             continue

#                         obj.save()
#                         total_formset_debit += obj.amount

#                         # --- UNIQUE VOUCHER STRINGS ENGINE ---
#                         if not obj.pay_id:
#                             obj.pay_id = f"PAY-{obj.id}"
#                             obj.save(update_fields=['pay_id'])

#                         # --- MATCH FINANCIAL CHART OF ACCOUNTS HEADS ---
#                         if obj.type == "Expense":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Expense Account').first()
#                         elif obj.type == "Purchase":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Purchase Account').first()
#                         else:
#                             head = None

#                         # --- CHECK CHEQUE / PAYMENT VOUCHER CONFIGURATIONS ---
#                         cheque_id = request.POST.get(f"{form.prefix}-cheque_number") or request.POST.get('cheque_number')

#                         # --- UPDATE/CREATE DEBIT REST VOUCHERS (Payment Voucher Integration) ---
#                         voucher = DebitRestVoucher.objects.filter(requi_id=obj.id).first()
#                         particulars_text = f"Payment Voucher entry for Kitchen Balance ({obj.type})"

#                         # Map vendor configuration if applicable
#                         voucher_type = "Vendor" if obj.type == "Purchase" else (obj.type or "Expense")
                        
#                         if voucher:
#                             voucher.type = voucher_type
#                             voucher.project_name = obj.project
#                             voucher.cash_type = obj.cash_type
#                             voucher.head_of_account = head
#                             voucher.amount = obj.amount
#                             voucher.date = obj.date
#                             voucher.bill_date = obj.date
#                             voucher.particulars = particulars_text
#                             voucher.expense = obj.rest_exp if obj.type == "Expense" else None
#                             voucher.purchase = obj.pur_cost if obj.type == "Purchase" else None
#                             voucher.save()
#                         else:
#                             voucher = DebitRestVoucher.objects.create(
#                                 type=voucher_type,
#                                 project_name=obj.project,
#                                 cash_type=obj.cash_type,
#                                 head_of_account=head,
#                                 amount=obj.amount,
#                                 date=obj.date,
#                                 bill_date=obj.date,
#                                 particulars=particulars_text,
#                                 mr_or_bill_no=f"PV-{uuid.uuid4().hex[:10]}",
#                                 is_confirmed=True,
#                                 create_dr=request.user.username,
#                                 requi_id=obj.id,
#                                 expense=obj.rest_exp if obj.type == "Expense" else None,
#                                 purchase=obj.pur_cost if obj.type == "Purchase" else None,
#                             )

#                         # Handle optional cheque status tracking if bound
#                         if cheque_id and cheque_id != 'None' and cheque_id.isdigit():
#                             try:
#                                 cheque = RestMainCheque.objects.get(id=int(cheque_id))
#                                 voucher.cheque_number = cheque.cheque_number
#                                 voucher.save()
                                
#                                 cheque.status = 'used'
#                                 cheque.remarks = particulars_text
#                                 cheque.issue_date = obj.date
#                                 cheque.amount = obj.amount
#                                 cheque.save()
#                             except RestMainCheque.DoesNotExist:
#                                 pass

#                         # ==========================================
#                         # 📚 SYNC TO ACCOUNTING (LedgerRestEntry & RestTransactionHistory)
#                         # ==========================================
#                         if head and obj.cash_type:
#                             LedgerRestEntry.objects.update_or_create(
#                                 tbl_id=str(obj.id),
#                                 tbl_name='DailyPayment',
#                                 defaults={
#                                     'project_name': obj.project,
#                                     'type': voucher_type,
#                                     'cash_type': obj.cash_type,
#                                     'head': head,
#                                     'date': obj.date,
#                                     'description': particulars_text,
#                                     'debit': obj.amount,
#                                     'credit': Decimal('0.00'),
#                                     'mr_or_bill_no': voucher.mr_or_bill_no,
#                                     'cheque_number': voucher.cheque_number,
#                                     'tbl_id': str(obj.id),
#                                     'tbl_name': 'DailyPayment',
#                                 }
#                             )

#                             username = request.user.username if request.user.is_authenticated else "System"
#                             RestTransactionHistory.objects.update_or_create(
#                                 tbl_id=str(obj.id),
#                                 tbl_name='DailyPayment',
#                                 defaults={
#                                     'project': obj.project,
#                                     'transaction_type': obj.type,
#                                     'head_of_account': head,
#                                     'cash_type': obj.cash_type,
#                                     'amount': obj.amount,
#                                     'date': obj.date,
#                                     'create_by': username,
#                                     'particulars': particulars_text,
#                                     'reference': voucher.mr_or_bill_no,
#                                     'cheque_number': voucher.cheque_number,
#                                     'tbl_id': str(obj.id),
#                                     'tbl_name': 'DailyPayment',
#                                 }
#                             )

#                     # --- UPDATE RESTAURANT KITCHEN LEDGER SAFELY ---
#                     if selected_project and str(selected_project).isdigit() and target_type:
#                         fallback_employee_id = assigned_employee_id
#                         if not fallback_employee_id:
#                             prior_row = RestaurantKitchenLedger.objects.filter(
#                                 project_id=int(selected_project),
#                                 type=target_type
#                             ).order_by('-created_at').first()
#                             fallback_employee_id = prior_row.employee_id if prior_row else None

#                         if fallback_employee_id:
#                             RestaurantKitchenLedger.objects.update_or_create(
#                                 project_id=int(selected_project),
#                                 type=target_type,
#                                 employee_id=fallback_employee_id,
#                                 defaults={
#                                     'debit': total_formset_debit,
#                                 },
#                             )

#                 messages.success(request, "Payment vouchers successfully generated and synchronized to accounting records!")
#                 balance_param = request.GET.get('balance', '1')
#                 return redirect(
#                     f"{reverse('restaurant_kitchen_ledger_payment')}"
#                     f"?date={selected_date}&project_id={selected_project}&type_name={target_type}&balance={balance_param}"
#                 )
            
#             except Exception as e:
#                 messages.error(request, f"Transactional isolation execution crash: {str(e)}")
#         else:
#             messages.error(request, "Failed validation. Please address errors down in the data-grid entries.")
          
#     # ==========================================
#     # 📑 GET METHOD RENDER PIPELINE
#     # ==========================================
#     else:
#         initial_data_list = []

#         if not queryset.exists() and selected_project and target_type:
#             ledger_qs = RestaurantKitchenLedger.objects.filter(
#                 project_id=selected_project,
#                 type=target_type
#             )

#             balance_amount = ledger_qs.aggregate(
#                 total=Sum('credit') - Sum('debit')
#             )['total'] or Decimal('0.00')

#             fallback_cash = CashRestType.objects.filter(cash_type_name='Supplier Account').first()

#             if balance_amount > 0:
#                 initial_data_list.append({
#                     'type': target_type,
#                     'amount': balance_amount,
#                     'cash_type': fallback_cash.id if fallback_cash else None
#                 })

#         formset = DailyPaymentFormSet(queryset=queryset, initial=initial_data_list)

#     total_summary = Decimal('0.00')
#     expense_total = Decimal('0.00')
#     purchase_total = Decimal('0.00')

#     if selected_date and selected_project and str(selected_project).isdigit():
#         qs = DailyPayment.objects.filter(date=selected_date, project_id=int(selected_project))
#         total_summary = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         expense_total = qs.filter(type="Expense").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         purchase_total = qs.filter(type="Purchase").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#     return render(request, 'restaurant/restaurant_kitchen_ledger_payment.html', {
#         'formset': formset,
#         'projects': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=["The Galleria Restauent Cafe", "The Galleria Live Kitchen"]
#         ),
#         'selected_date': selected_date,
#         'selected_project': selected_project,
#         'target_type': target_type,
#         'total_summary': total_summary,
#         'expense_total': expense_total,
#         'purchase_total': purchase_total,
#         'today': date.today(),
#     })



import uuid
from decimal import Decimal
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from restaurant.models import (
    RestaurantKitchenLedger,
    RestaurantJewelSupplier,
)


@login_required
def restaurant_kitchen_ledger_payment(request):
    selected_date = request.GET.get('date') or request.POST.get('date')
    if not selected_date:
        selected_date = timezone.now().date().strftime('%Y-%m-%d')

    selected_project = (
        request.GET.get('project_id') or request.GET.get('project')
        or request.POST.get('project_id') or request.POST.get('project')
    )

    jewel_supplier_id = request.GET.get('jewel_supplier_id') or request.POST.get('jewel_supplier_id')
    filter_type = request.GET.get('type') or request.POST.get('filter_type')
    filter_employee_id = request.GET.get('employee_id') or request.POST.get('filter_employee_id')

    # Real accounting supplier selected at payment time (Purchase rows only)
    pay_supplier_id = request.POST.get('supplier_id') or request.GET.get('supplier_id')

    # --- Build filtered queryset ---
    queryset = RestaurantKitchenLedger.objects.none()
    if selected_project and str(selected_project).isdigit():
        qs = RestaurantKitchenLedger.objects.filter(project_id=int(selected_project))
        if jewel_supplier_id and str(jewel_supplier_id).isdigit():
            qs = qs.filter(vendor_name_id=int(jewel_supplier_id))
        if filter_type in ('Expense', 'Purchase'):
            qs = qs.filter(type=filter_type)
        if filter_employee_id and str(filter_employee_id).isdigit():
            qs = qs.filter(employee_id=int(filter_employee_id))
        queryset = qs.select_related('employee', 'vendor_name', 'item_name')

    if selected_project and str(selected_project).isdigit():
        # Query FORWARD through RestaurantKitchenLedger (fields we know for certain
        # from the model you posted) instead of guessing reverse-relation names on
        # RestaurantJewelSupplier / RestaurantEmployee, which caused the FieldErrors.
        project_ledger_rows = RestaurantKitchenLedger.objects.filter(project_id=int(selected_project))

        jewel_supplier_ids = project_ledger_rows.exclude(vendor_name__isnull=True) \
            .values_list('vendor_name_id', flat=True).distinct()
        jewel_suppliers = RestaurantJewelSupplier.objects.filter(id__in=jewel_supplier_ids)

        employee_ids = project_ledger_rows.exclude(employee__isnull=True) \
            .values_list('employee_id', flat=True).distinct()
        employees_in_scope = RestaurantEmployee.objects.filter(id__in=employee_ids)
    else:
        jewel_suppliers = RestaurantJewelSupplier.objects.none()
        employees_in_scope = RestaurantEmployee.objects.none()

    # --- Item-wise / amount-wise summary (Debit only now; Credit is always 0.00) ---
    item_summary = (
        queryset.values('item_name_id', 'item_name__rest_item_name')
        .annotate(total_debit=Sum('debit'))
        .order_by('item_name__rest_item_name')
    )
    for row in item_summary:
        row['total_amount'] = row['total_debit'] or Decimal('0.00')  # credit is always 0, so amount == debit

    # NOTE: 'credit' removed — user only enters Debit. Credit is force-set to 0.00 in the loop below.
    KitchenLedgerFormSet = modelformset_factory(
        RestaurantKitchenLedger,
        fields=('employee', 'type', 'vendor_name', 'item_name', 'debit'),
        extra=0,
        can_delete=False,
    )

    if request.method == "POST":
        formset = KitchenLedgerFormSet(request.POST, queryset=queryset)

        pay_supplier_obj = None
        if pay_supplier_id and str(pay_supplier_id).isdigit():
            pay_supplier_obj = RestaurantSupplier.objects.filter(id=int(pay_supplier_id)).first()

        if formset.is_valid():
            has_purchase_row = any(
                f.cleaned_data.get('type') == 'Purchase'
                for f in formset.forms if f.cleaned_data
            )
            if has_purchase_row and not pay_supplier_obj:
                messages.error(request, "Please select a Supplier before saving Purchase-type entries.")
            else:
                saved_ledger_count = 0
                saved_voucher_count = 0
                row_errors = []

                for form in formset.forms:
                    if not form.cleaned_data:
                        continue

                    obj = form.save(commit=False)
                    if selected_project and str(selected_project).isdigit():
                        obj.project_id = int(selected_project)

                    # Credit is always 0.00 — user only enters Debit.
                    obj.credit = Decimal('0.00')

                    if (obj.debit or Decimal('0.00')) <= 0:
                        continue

                    # --- Each row gets its OWN savepoint, so a voucher-sync failure on
                    #     one row can never roll back a kitchen ledger row that already saved. ---
                    try:
                        with transaction.atomic():
                            obj.save()
                            saved_ledger_count += 1

                            if not obj.tbl_id:
                                obj.tbl_id = str(obj.id)
                                obj.save(update_fields=['tbl_id'])

                            if obj.type == "Expense":
                                head = RestHeadOfAccount.objects.filter(head_name__icontains='Expense Account').first()
                            elif obj.type == "Purchase":
                                head = RestHeadOfAccount.objects.filter(head_name__icontains='Purchase Account').first()
                            else:
                                head = RestHeadOfAccount.objects.first()

                            cash_type_obj = CashRestType.objects.filter(cash_type_name='Supplier Account').first()
                            if not cash_type_obj:
                                cash_type_obj = CashRestType.objects.first()

                            particulars_text = f"Kitchen Ledger Payment Entry ({obj.type}) - Item: {obj.item_name}"
                            voucher_type = "Vendor" if obj.type == "Purchase" else (obj.type or "Expense")

                            # Amount = Debit - Credit (Credit is always 0.00, so this equals Debit)
                            transaction_amount = obj.debit - obj.credit

                            row_vendor = pay_supplier_obj if obj.type == "Purchase" else None

                            if not head or not cash_type_obj:
                                raise ValueError(
                                    "Missing required Head of Account or Cash Type configuration "
                                    "— row saved to Kitchen Ledger but voucher was NOT created."
                                )

                            voucher = DebitRestVoucher.objects.filter(requi_id=obj.id).first()
                            if voucher:
                                voucher.type = voucher_type
                                voucher.project_name = obj.project
                                voucher.cash_type = cash_type_obj
                                voucher.head_of_account = head
                                voucher.amount = transaction_amount
                                voucher.date = timezone.now().date()
                                voucher.bill_date = timezone.now().date()
                                voucher.particulars = particulars_text
                                voucher.vendor = row_vendor
                                voucher.save()
                            else:
                                voucher = DebitRestVoucher.objects.create(
                                    type=voucher_type,
                                    project_name=obj.project,
                                    cash_type=cash_type_obj,
                                    head_of_account=head,
                                    amount=transaction_amount,
                                    date=timezone.now().date(),
                                    bill_date=timezone.now().date(),
                                    particulars=particulars_text,
                                    mr_or_bill_no=f"KPV-{uuid.uuid4().hex[:10]}",
                                    is_confirmed=True,
                                    create_dr=request.user.username if request.user.is_authenticated else "System",
                                    requi_id=obj.id,
                                    vendor=row_vendor,
                                )
                            saved_voucher_count += 1

                            LedgerRestEntry.objects.update_or_create(
                                tbl_id=str(obj.id),
                                tbl_name='RestaurantKitchenLedger',
                                defaults={
                                    'project_name': obj.project,
                                    'type': voucher_type,
                                    'vendor': row_vendor,
                                    'cash_type': cash_type_obj,
                                    'head': head,
                                    'date': timezone.now().date(),
                                    'description': particulars_text,
                                    'debit': obj.debit,
                                    'credit': obj.credit,  # always 0.00
                                    'mr_or_bill_no': voucher.mr_or_bill_no,
                                }
                            )

                            RestTransactionHistory.objects.update_or_create(
                                tbl_id=str(obj.id),
                                tbl_name='RestaurantKitchenLedger',
                                defaults={
                                    'project': obj.project,
                                    'transaction_type': obj.type,
                                    'head_of_account': head,
                                    'cash_type': cash_type_obj,
                                    'amount': transaction_amount,
                                    'date': timezone.now().date(),
                                    'create_by': request.user.username if request.user.is_authenticated else "System",
                                    'particulars': (
                                        f"{particulars_text} | Paid to: {row_vendor}"
                                        if row_vendor else particulars_text
                                    ),
                                    'reference': voucher.mr_or_bill_no,
                                    'tbl_id': str(obj.id),
                                    'tbl_name': 'RestaurantKitchenLedger',
                                }
                            )

                    except Exception as e:
                        # Kitchen ledger row (if it saved before the failure) stays saved —
                        # only the voucher/ledger/history sync for THIS row is rolled back.
                        row_errors.append(f"Row (item: {obj.item_name}): {str(e)}")

                if saved_ledger_count:
                    messages.success(
                        request,
                        f"{saved_ledger_count} kitchen ledger row(s) saved. "
                        f"{saved_voucher_count} voucher(s) synchronized."
                    )
                else:
                    messages.warning(request, "No rows had a Debit amount greater than 0 — nothing was saved.")

                for err in row_errors:
                    messages.error(request, err)

                return redirect(
                    f"{reverse('restaurant_kitchen_ledger_payment')}"
                    f"?project_id={selected_project}"
                    f"&jewel_supplier_id={jewel_supplier_id or ''}"
                    f"&type={filter_type or ''}"
                    f"&employee_id={filter_employee_id or ''}"
                )
        else:
            messages.error(request, "Validation failed. Please review the highlighted fields below.")
    else:
        formset = KitchenLedgerFormSet(queryset=queryset)

    total_summary = queryset.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
    expense_total = queryset.filter(type="Expense").aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
    purchase_total = queryset.filter(type="Purchase").aggregate(total=Sum('debit'))['total'] or Decimal('0.00')

    return render(request, 'restaurant/restaurant_kitchen_ledger_payment.html', {
        'formset': formset,
        'projects': ProjectFirstLevelName.objects.all(),
        'jewel_suppliers': jewel_suppliers,
        'employees_in_scope': employees_in_scope,
        'suppliers': RestaurantSupplier.objects.all(),
        'item_summary': item_summary,
        'selected_date': selected_date,
        'selected_project': selected_project,
        'jewel_supplier_id': jewel_supplier_id,
        'filter_type': filter_type,
        'filter_employee_id': filter_employee_id,
        'pay_supplier_id': pay_supplier_id,
        'total_summary': total_summary,
        'expense_total': expense_total,
        'purchase_total': purchase_total,
        'today': date.today(),
    })



# import uuid
# from decimal import Decimal
# from datetime import date
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import transaction
# from django.db.models import Sum
# from django.forms import modelformset_factory
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# from django.utils import timezone
# from restaurant.models import RestaurantKitchenLedger, RestaurantItem
# from restaccounting.models import LedgerRestEntry, RestTransactionHistory


# @login_required
# def restaurant_kitchen_ledger_payment(request):
#     selected_date = request.GET.get('date') or request.POST.get('date')
#     if not selected_date:
#         selected_date = timezone.now().date().strftime('%Y-%m-%d')

#     selected_project = (
#         request.GET.get('project_id')
#         or request.GET.get('project')
#         or request.POST.get('project_id')
#         or request.POST.get('project')
#     )
#     target_type = request.GET.get('type_name') or request.POST.get('target_type')

#     # Match Employee routing boundaries to the Project context
#     assigned_employee_id = None
#     if selected_project and str(selected_project).isdigit():
#         p_id = int(selected_project)
#         if p_id == 36:
#             assigned_employee_id = 24
#         elif p_id == 60:
#             assigned_employee_id = 54

#     queryset = DailyPayment.objects.none()

#     if selected_date and selected_project and str(selected_project).isdigit():
#         queryset = DailyPayment.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#     extra_forms = 0 if queryset.exists() else 1
#     DailyPaymentFormSet = modelformset_factory(
#         DailyPayment,
#         form=DailyPaymentForm,
#         extra=extra_forms,
#         can_delete=True
#     )

#     # ==========================================
#     # 🔁 POST PROCESSING PIPELINE
#     # ==========================================
#     if request.method == "POST":
#         formset = DailyPaymentFormSet(request.POST, queryset=queryset)

#         if formset.is_valid():
#             try:
#                 with transaction.atomic():
#                     total_formset_debit = Decimal('0.00')
                    
#                     for form in formset.forms:
#                         if not form.cleaned_data:
#                             continue

#                         # --- REMOVE ACTIONS ---
#                         if form.cleaned_data.get('DELETE'):
#                             obj = form.instance
#                             if obj.pk:
#                                 DebitRestVoucher.objects.filter(requi_id=obj.id).delete()
#                                 LedgerRestEntry.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 RestTransactionHistory.objects.filter(tbl_id=str(obj.id), tbl_name='DailyPayment').delete()
#                                 obj.delete()
#                             continue

#                         # --- COMMIT/MUTATE DAILY PAYMENTS ---
#                         obj = form.save(commit=False)
#                         obj.date = selected_date
#                         obj.project_id = int(selected_project)

#                         if not obj.amount or obj.amount <= 0:
#                             continue

#                         obj.save()
#                         total_formset_debit += obj.amount

#                         # --- UNIQUE VOUCHER STRINGS ENGINE ---
#                         if not obj.pay_id:
#                             obj.pay_id = f"PAY-{obj.id}"
#                             obj.save(update_fields=['pay_id'])

#                         # --- MATCH FINANCIAL CHART OF ACCOUNTS HEADS ---
#                         if obj.type == "Expense":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Expense Account').first()
#                         elif obj.type == "Purchase":
#                             head = RestHeadOfAccount.objects.filter(head_name__icontains='Purchase Account').first()
#                         else:
#                             head = None

#                         # --- UPDATE/CREATE DEBIT REST VOUCHERS ---
#                         voucher = DebitRestVoucher.objects.filter(requi_id=obj.id).first()
#                         particulars_text = f"Daily Payment entry for Kitchen Balance ({obj.type})"

#                         if voucher:
#                             voucher.type = obj.type or "Expense"
#                             voucher.project_name = obj.project
#                             voucher.cash_type = obj.cash_type
#                             voucher.head_of_account = head
#                             voucher.amount = obj.amount
#                             voucher.date = obj.date
#                             voucher.bill_date = obj.date
#                             voucher.particulars = particulars_text
#                             voucher.expense = obj.rest_exp if obj.type == "Expense" else None
#                             voucher.purchase = obj.pur_cost if obj.type == "Purchase" else None
#                             voucher.save()
#                         else:
#                             voucher = DebitRestVoucher.objects.create(
#                                 type=obj.type or "Expense",
#                                 project_name=obj.project,
#                                 cash_type=obj.cash_type,
#                                 head_of_account=head,
#                                 amount=obj.amount,
#                                 date=obj.date,
#                                 bill_date=obj.date,
#                                 particulars=particulars_text,
#                                 mr_or_bill_no=f"DP-{uuid.uuid4().hex[:10]}",
#                                 is_confirmed=True,
#                                 create_dr=request.user.username,
#                                 requi_id=obj.id,
#                                 expense=obj.rest_exp if obj.type == "Expense" else None,
#                                 purchase=obj.pur_cost if obj.type == "Purchase" else None,
#                             )

#                         # ==========================================
#                         # 📚 SYNC TO ACCOUNTING (LedgerRestEntry & RestTransactionHistory)
#                         # ==========================================
#                         if head and obj.cash_type:
#                             LedgerRestEntry.objects.update_or_create(
#                                 tbl_id=str(voucher.id),
#                                 tbl_name='DebitRestVoucher',
#                                 defaults={
#                                     'project_name': obj.project,
#                                     'type': 'Expense' if obj.type == 'Expense' else 'Vendor',
#                                     'cash_type': obj.cash_type,
#                                     'head': head,
#                                     'date': obj.date,
#                                     'description': particulars_text,
#                                     'debit': obj.amount,
#                                     'credit': Decimal('0.00'),
#                                     'mr_or_bill_no': voucher.mr_or_bill_no,
#                                 }
#                             )

#                             username = request.user.username if request.user.is_authenticated else "System"
#                             RestTransactionHistory.objects.update_or_create(
#                                 tbl_id=str(voucher.id),
#                                 tbl_name='DebitRestVoucher',
#                                 defaults={
#                                     'project': obj.project,
#                                     'transaction_type': obj.type,
#                                     'head_of_account': head,
#                                     'cash_type': obj.cash_type,
#                                     'amount': obj.amount,
#                                     'date': obj.date,
#                                     'create_by': username,
#                                     'particulars': particulars_text,
#                                     'reference': voucher.mr_or_bill_no,
#                                 }
#                             )

#                     # --- UPDATE RESTAURANT KITCHEN LEDGER SAFELY ---
#                     if selected_project and str(selected_project).isdigit() and target_type:
#                         fallback_employee_id = assigned_employee_id
#                         if not fallback_employee_id:
#                             prior_row = RestaurantKitchenLedger.objects.filter(
#                                 project_id=int(selected_project),
#                                 type=target_type
#                             ).order_by('-created_at').first()
#                             fallback_employee_id = prior_row.employee_id if prior_row else None

#                         if not fallback_employee_id:
#                             messages.error(
#                                 request,
#                                 "Could not determine an employee for this project/type — "
#                                 "no routing override and no prior ledger entry to inherit from. "
#                                 "Kitchen ledger row was not updated."
#                             )
#                         else:
#                             RestaurantKitchenLedger.objects.update_or_create(
#                                 project_id=int(selected_project),
#                                 type=target_type,
#                                 employee_id=fallback_employee_id,
#                                 defaults={
#                                     'debit': total_formset_debit,
#                                 },
#                             )

#                 messages.success(request, "Daily Restaurant Payments successfully synchronized to general accounting entries!")
#                 return redirect(
#                     f"{reverse('restaurant_kitchen_ledger_payment')}"
#                     f"?date={selected_date}&project_id={selected_project}&type_name={target_type}"
#                 )
            
#             except Exception as e:
#                 messages.error(request, f"Transactional isolation execution crash: {str(e)}")
#         else:
#             messages.error(request, "Failed validation. Please address errors down in the data-grid entries.")
            
#     # ==========================================
#     # 📑 GET METHOD RENDER PIPELINE
#     # ==========================================
#     else:
#         initial_data_list = []

#         if not queryset.exists() and selected_project and target_type:
#             ledger_qs = RestaurantKitchenLedger.objects.filter(
#                 project_id=selected_project,
#                 type=target_type
#             )

#             balance_amount = ledger_qs.aggregate(
#                 total=Sum('credit') - Sum('debit')
#             )['total'] or Decimal('0.00')

#             fallback_cash = CashRestType.objects.filter(cash_type_name='Supplier Account').first()

#             if balance_amount > 0:
#                 initial_data_list.append({
#                     'type': target_type,
#                     'amount': balance_amount,
#                     'cash_type': fallback_cash.id if fallback_cash else None
#                 })

#         formset = DailyPaymentFormSet(queryset=queryset, initial=initial_data_list)

#     total_summary = Decimal('0.00')
#     expense_total = Decimal('0.00')
#     purchase_total = Decimal('0.00')

#     if selected_date and selected_project and str(selected_project).isdigit():
#         qs = DailyPayment.objects.filter(date=selected_date, project_id=int(selected_project))
#         total_summary = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         expense_total = qs.filter(type="Expense").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#         purchase_total = qs.filter(type="Purchase").aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

#     return render(request, 'restaurant/restaurant_kitchen_ledger_payment.html', {
#         'formset': formset,
#         'projects': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=["The Galleria Restauent Cafe", "The Galleria Live Kitchen"]
#         ),
#         'selected_date': selected_date,
#         'selected_project': selected_project,
#         'target_type': target_type,
#         'total_summary': total_summary,
#         'expense_total': expense_total,
#         'purchase_total': purchase_total,
#     })
    


from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import uuid


@login_required
def daily_payment_create(request):

    DailyPaymentFormSet = modelformset_factory(
        DailyPayment,
        form=DailyPaymentForm,
        extra=10,
        can_delete=True
    )

    selected_date = request.GET.get('date') or request.POST.get('date')
    selected_project = request.GET.get('project') or request.POST.get('project')

    queryset = DailyPayment.objects.none()

    # =========================
    # 🔹 LOAD EXISTING DATA
    # =========================
    if selected_date and selected_project and str(selected_project).isdigit():
        queryset = DailyPayment.objects.filter(
            date=selected_date,
            project_id=int(selected_project)
        )

    # =========================
    # 🔁 POST
    # =========================
    if request.method == "POST":

        formset = DailyPaymentFormSet(request.POST, queryset=queryset)

        if formset.is_valid():

            with transaction.atomic():

                for form in formset.forms:

                    if not form.cleaned_data:
                        continue

                    # =========================
                    # 🔥 DELETE
                    # =========================
                    if form.cleaned_data.get('DELETE'):
                        obj = form.instance
                        if obj.pk:
                            DebitRestVoucher.objects.filter(requi_id=obj.id).delete()
                            obj.delete()
                        continue

                    # =========================
                    # ➕ CREATE / UPDATE
                    # =========================
                    obj = form.save(commit=False)

                    obj.date = selected_date
                    obj.project_id = int(selected_project)

                    # skip empty rows
                    if not obj.amount or obj.amount <= 0:
                        continue

                    obj.save()

                    # =========================
                    # 🔥 PAY ID GENERATE
                    # =========================
                    if not obj.pay_id:
                        obj.pay_id = f"PAY-{obj.id}"
                        obj.save(update_fields=['pay_id'])

                    # =========================
                    # 🎯 HEAD OF ACCOUNT
                    # =========================
                    if obj.type == "Expense":
                        head = RestHeadOfAccount.objects.filter(
                            head_name__icontains='Expense Account'
                        ).first()
                    elif obj.type == "Purchase":
                        head = RestHeadOfAccount.objects.filter(
                            head_name__icontains='Purchase Account'
                        ).first()
                    else:
                        head = None

                    # =========================
                    # 🔁 FIND VOUCHER
                    # =========================
                    voucher = DebitRestVoucher.objects.filter(
                        requi_id=obj.id
                    ).first()

                    # =========================
                    # 🔄 UPDATE VOUCHER
                    # =========================
                    if voucher:
                        voucher.type = obj.type or "Expense"
                        voucher.project_name = obj.project
                        voucher.cash_type = obj.cash_type
                        voucher.head_of_account = head
                        voucher.amount = obj.amount
                        voucher.date = obj.date
                        voucher.bill_date = obj.date
                        voucher.particulars = f"Daily Payment entry for {obj.sales_type}"
                        voucher.expense = obj.rest_exp if obj.type == "Expense" else None
                        voucher.purchase = obj.pur_cost if obj.type == "Purchase" else None
                        voucher.save()

                    # =========================
                    # ➕ CREATE VOUCHER
                    # =========================
                    else:
                        DebitRestVoucher.objects.create(
                            type=obj.type or "Expense",
                            project_name=obj.project,
                            cash_type=obj.cash_type,
                            head_of_account=head,
                            amount=obj.amount,
                            date=obj.date,
                            bill_date=obj.date,
                            particulars=f"Daily Payment entry for {obj.sales_type}",
                            mr_or_bill_no=f"DP-{uuid.uuid4().hex[:10]}",
                            is_confirmed=True,
                            create_dr=request.user.username,
                            requi_id=obj.id,
                            expense=obj.rest_exp if obj.type == "Expense" else None,
                            purchase=obj.pur_cost if obj.type == "Purchase" else None,
                        )

            messages.success(request, "Daily Payment saved successfully!")
            return redirect(
                f"{reverse('daily_payment_add')}?date={selected_date}&project={selected_project}"
            )

        else:
            print(formset.errors)  # debug
            messages.error(request, "Please fix the form errors.")

    else:
        formset = DailyPaymentFormSet(queryset=queryset)

    # =========================
    # 📊 SUMMARY
    # =========================
    total_summary = Decimal('0.00')
    expense_total = Decimal('0.00')
    purchase_total = Decimal('0.00')

    if selected_date and selected_project and str(selected_project).isdigit():

        qs = DailyPayment.objects.filter(
            date=selected_date,
            project_id=int(selected_project)
        )

        total_summary = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        expense_total = qs.filter(type="Expense").aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        purchase_total = qs.filter(type="Purchase").aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

    # =========================
    # 🎯 CONTEXT
    # =========================
    return render(request, 'restaurant/daily_payment_create.html', {
        'formset': formset,
        'projects': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'selected_date': selected_date,
        'selected_project': selected_project,
        'total_summary': total_summary,
        'expense_total': expense_total,
        'purchase_total': purchase_total,
    })
    
    

 

## ok code -----


# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import transaction
# from django.db.models import Sum
# from decimal import Decimal
# from django.forms import modelformset_factory
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# import uuid


# @login_required
# def daily_payment_create(request):

#     DailyPaymentFormSet = modelformset_factory(
#         DailyPayment,
#         form=DailyPaymentForm,
#         extra=5,
#         can_delete=True   # ✅ allow update/delete
#     )

#     selected_date = request.GET.get('date') or request.POST.get('date')
#     selected_project = request.GET.get('project') or request.POST.get('project')

#     queryset = DailyPayment.objects.none()

#     # ✅ LOAD EXISTING DATA
#     if selected_date and selected_project and str(selected_project).isdigit():
#         queryset = DailyPayment.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#     # =========================
#     # 🔁 POST
#     # =========================
#     if request.method == "POST":

#         formset = DailyPaymentFormSet(request.POST, queryset=queryset)

#         if formset.is_valid():

#             with transaction.atomic():

#                 instances = formset.save(commit=False)

#                 # 🔥 DELETE
#                 for obj in formset.deleted_objects:
#                     obj.delete()

#                 for obj in instances:

#                     # assign date/project
#                     obj.date = selected_date
#                     obj.project_id = int(selected_project)

#                     if not obj.amount or obj.amount <= 0:
#                         continue

#                     obj.save()

#                     # =========================
#                     # 🎯 HEAD
#                     # =========================
#                     if obj.type == "Expense":
#                         head = RestHeadOfAccount.objects.filter(
#                             head_name__icontains='Expense Account'
#                         ).first()
#                     elif obj.type == "Purchase":
#                         head = RestHeadOfAccount.objects.filter(
#                             head_name__icontains='Purchase Account'
#                         ).first()
#                     else:
#                         head = None

#                     # =========================
#                     # 🔁 UPDATE / CREATE VOUCHER
#                     # =========================
#                     voucher = DebitRestVoucher.objects.filter(
#                         requi_id=obj.id
#                     ).first()

#                     if voucher:
#                         # ✅ UPDATE
#                         voucher.amount = obj.amount
#                         voucher.cash_type = obj.cash_type
#                         voucher.type = obj.type
#                         voucher.head_of_account = head
#                         voucher.particulars = f"Daily Payment entry for {obj.sales_type}"
#                         voucher.save()

#                     else:
#                         # ➕ CREATE
#                         DebitRestVoucher.objects.create(
#                             type=obj.type or "Expense",
#                             project_name=obj.project,
#                             cash_type=obj.cash_type,
#                             head_of_account=head,
#                             amount=obj.amount,
#                             date=obj.date,
#                             bill_date=obj.date,
#                             particulars=f"Daily Payment entry for {obj.sales_type}",
#                             mr_or_bill_no=f"DP-{uuid.uuid4().hex[:10]}",
#                             is_confirmed=True,
#                             create_dr=request.user.username,
#                             requi_id=obj.id,
#                             expense=obj.rest_exp if obj.type == "Expense" else None,
#                             purchase=obj.pur_cost if obj.type == "Purchase" else None,
#                         )

#             messages.success(request, "Saved successfully!")
#             return redirect(
#                 f"{reverse('daily_payment_add')}?date={selected_date}&project={selected_project}"
#             )

#         else:
#             print(formset.errors)  # 🔥 DEBUG
#             messages.error(request, "Please fix the form errors.")

#     else:
#         formset = DailyPaymentFormSet(queryset=queryset)

#     # =========================
#     # 📊 SUMMARY
#     # =========================
#     total_summary = Decimal('0.00')
#     expense_total = Decimal('0.00')
#     purchase_total = Decimal('0.00')

#     if selected_date and selected_project and str(selected_project).isdigit():

#         qs = DailyPayment.objects.filter(
#             date=selected_date,
#             project_id=int(selected_project)
#         )

#         total_summary = qs.aggregate(total=Sum('amount'))['total'] or 0
#         expense_total = qs.filter(type="Expense").aggregate(total=Sum('amount'))['total'] or 0
#         purchase_total = qs.filter(type="Purchase").aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, 'restaurant/daily_payment_create.html', {
#         'formset': formset,
#         'projects': ProjectFirstLevelName.objects.filter(
#             project_first_name__in=[
#                 "The Galleria Restauent Cafe",
#                 "The Galleria Live Kitchen"
#             ]
#         ),
#         'selected_date': selected_date,
#         'selected_project': selected_project,
#         'total_summary': total_summary,
#         'expense_total': expense_total,
#         'purchase_total': purchase_total,
#     })
    
    

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import DailyPayment

@login_required
def daily_payment_list(request):

    dailypayments = DailyPayment.objects.select_related(
        'project',
        'rest_exp',
        'pur_cost',
        'sales_type',
        'cash_type'
    ).order_by('-date', '-id')

    context = {
        'dailypayments': dailypayments,
    }

    return render(request, 'restaurant/daily_payment_list.html', context)



@login_required
def daily_payment_edit(request, pk):

    dailypayment = get_object_or_404(DailyPayment, pk=pk)

    if request.method == 'POST':
        form = DailyPaymentForm(request.POST, instance=dailypayment)

        if form.is_valid():
            form.save()
            messages.success(request, "DailyPayment updated successfully!")
            return redirect('daily_payment_list')
    else:
        form = DailyPaymentForm(instance=dailypayment)

    return render(request, 'restaurant/dailypayment_form_edit.html', {
        'form': form
    })
    



  
@login_required
def daily_payment_delete(request, pk):

    daylipayment = get_object_or_404(DailyPayment, pk=pk)

    if request.method == 'POST':
        daylipayment.delete()
        messages.success(request, "DailyPayment deleted successfully!")
        return redirect('daily_payment_list')

    return render(request, 'restaurant/daylipayment_confirm_delete.html', {
        'daylipayment': daylipayment
    })


# import re

# @login_required
# def rest_approve_dr_voucher(request, pk):
#     voucher = get_object_or_404(DebitRestVoucher, pk=pk)

#     if voucher.approval_dr_status:
#         return redirect('rest_debitvoucher_list')

#     # Auto-generate mr_or_bill_no if missing
#     if not voucher.mr_or_bill_no:
#         base_code = "MBD-"
#         last = DebitRestVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
#         next_id = (last.id + 1) if last else 1
#         generated_code = f"{base_code}{next_id:05d}"
#         while DebitRestVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
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
#             expense_obj = RestExpense.objects.filter(id=expense_id).first()
#         # Optionally store the full name in DebitVoucher.expense for display
#         voucher.expense = expense_obj.head_exp_name if expense_obj else voucher.expense
#     # -------------------------

#     voucher.approval_dr_status = True
#     voucher.save()

#     # Update cash balance
#     try:
#         cash_type = CashRestType.objects.get(cash_type_name=voucher.cash_type)
#         cash_type.type_amount = (cash_type.type_amount or 0) - (voucher.amount or 0)
#         cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
#         cash_type.save()
#     except CashRestType.DoesNotExist:
#         cash_type = None

#     # Create Transaction History
#     RestTransactionHistory.objects.create(
#         project=voucher.project_name,
#         transaction_type=voucher.type,
#         head_of_account=voucher.head_of_account,
#         cash_type=cash_type,
#         amount=voucher.amount,
#         cheque_number=voucher.cheque_number,
#         date=timezone.now().date(),
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         reference=voucher.mr_or_bill_no,
#         create_by=voucher.create_dr,
#         particulars=voucher.particulars,
#         tbl_id=voucher.id,
#         tbl_name='Payment',
#     )

#     LedgerRestEntry.objects.create(
#         project_name=voucher.project_name,
#         type=voucher.type,
#         contructor=getattr(voucher, 'contructor', None),
#         vendor=getattr(voucher, 'vendor', None),
#         customer_name=getattr(voucher, 'customer_name', None),
#         bankName=getattr(voucher, 'bankName', None),
#         exp_name=expense_obj,       # RestExpense instance
#         purchase_name=purchase_obj, # RestPurchaseCost instance
#         empl_name=getattr(voucher, 'empl_name', None),
#         invest_name=getattr(voucher, 'invest_name', None),
#         type_name=expense_obj.head_exp_name if expense_obj else None,
#         cash_type=voucher.cash_type,
#         cheque_number=voucher.cheque_number,
#         head=voucher.head_of_account,
#         mr_or_bill_no=voucher.mr_or_bill_no,
#         date=timezone.now().date(),
#         description=voucher.particulars or '',
#         debit=voucher.amount or 0,
#         credit=0,
#         carrier=getattr(voucher, 'carrier', None),
#         entry_date=voucher.date,
#         loan_status='payment',
#         tbl_id=voucher.id,
#         tbl_name='Payment'
#     )
#     # ----------------------------
#     # SMS Notification
#     # ----------------------------
#     sms_numbers = []
    
#     STATIC_NUMBER = "8801913222203"  # always receive copy
#     sms_numbers.append(STATIC_NUMBER)
    
#     sms_message = ""
    
#     # ----------------------------
#     # Customer
#     # ----------------------------
#     if voucher.type == 'Customer' and voucher.customer_name:
#         customer = voucher.customer_name
#         if customer.contact_no:
#             sms_numbers.append(customer.contact_no)
    
#         sms_message = (
#             f"Dear Customer,\n"
#             f"Payment received: ৳{voucher.amount}\n"
#             f"Date: {voucher.date.strftime('%d-%m-%Y')}\n"
#             f"Ref: {voucher.mr_or_bill_no}\n"
#             f"{voucher.project_name}\n"
#             f"Thank you."
#         )
    
#     # ----------------------------
#     # Vendor / Supplier
#     # ----------------------------
#     elif voucher.type == 'Vendor' and voucher.vendor:
#         supplier = voucher.vendor
#         if supplier.phone:
#             sms_numbers.append(supplier.phone)
    
#         sms_message = (
#             f"Dear Supplier,\n"
#             f"Payment made: ৳{voucher.amount}\n"
#             f"Ref: {voucher.mr_or_bill_no}\n"
#             f"{voucher.project_name}\n"
#             f"Thank you."
#         )
    
#     # ----------------------------
#     # Contractor
#     # ----------------------------
#     elif voucher.type == 'Contructor' and voucher.contructor:
#         contractor = voucher.contructor
#         if contractor.phone:
#             sms_numbers.append(contractor.phone)
    
#         sms_message = (
#             f"Dear Contractor,\n"
#             f"Payment made: ৳{voucher.amount}\n"
#             f"Ref: {voucher.mr_or_bill_no}\n"
#             f"{voucher.project_name}\n"
#             f"Thank you."
#         )
    
#         # ----------------------------
#     # Restaurant Employee Payment
#     # ----------------------------
#     elif voucher.type == 'Employee' and voucher.empl_name:

#         from restahrm.models import RestaurantEmployee 
       
#         employee = RestaurantEmployee.objects.filter(
#             rda_emp_name__iexact=voucher.empl_name.strip(),
#             project_name=voucher.project_name
#         ).first()

#         if employee:

#             if employee.rda_phone:
#                 sms_numbers.append(employee.rda_phone)

#             month_name = voucher.date.strftime("%B")

#             sms_message = (
#                 f"Dear {employee.rda_emp_name},\n"
#                 f"Your salary for the month of {month_name} has been paid successfully.\n"
#                 f"Amount: BDT {voucher.amount}\n"
#                 f"Project: {voucher.project_name}\n"
#                 f"Thank you."
#             )

#         else:
#             print("Employee not found for this project. SMS not sent.")



#     # ----------------------------
#     # Capital Account
#     # ----------------------------
#     elif voucher.type == 'Capital' and voucher.capi_name:
#         acc = voucher.capi_name
#         if hasattr(acc, "phone") and acc.phone:
#             sms_numbers.append(acc.phone)
    
#         sms_message = (
#             f"Capital payment processed: ৳{voucher.amount}\n"
#             f"Ref: {voucher.mr_or_bill_no}"
#             f"{voucher.project_name}\n"
#         )
    
#     # ----------------------------
#     # Investment Account
#     # ----------------------------
#     elif voucher.type == 'Investment' and voucher.invest_name:
#         acc = voucher.invest_name
#         if hasattr(acc, "phone") and acc.phone:
#             sms_numbers.append(acc.phone)
    
#         sms_message = (
#             f"Investment payment processed: ৳{voucher.amount}\n"
#             f"Ref: {voucher.mr_or_bill_no}"
#             f"{voucher.project_name}\n"
#         )
    
#     # ----------------------------
#     # Revenue Account
#     # ----------------------------
#     elif voucher.type == 'Revenue' and voucher.reve_name:
#         acc = voucher.reve_name
#         if hasattr(acc, "phone") and acc.phone:
#             sms_numbers.append(acc.phone)
    
#         sms_message = (
#             f"Revenue payment processed: ৳{voucher.amount}\n"
#             f"Ref: {voucher.mr_or_bill_no}"
#             f"{voucher.project_name}\n"
#         )
    
#     # ----------------------------
#     # Remove duplicates
#     # ----------------------------
#     sms_numbers = list(set(filter(None, sms_numbers)))
    
#     # ----------------------------
#     # Send SMS
#     # ----------------------------
#     if sms_message:
#         for number in sms_numbers:
#             if not send_sms(number, sms_message):
#                 print(f"SMS sending failed for {number}")

#     return redirect(reverse('rest_debit_voucher_pdf', args=[voucher.pk]))
    



import re
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def rest_approve_dr_voucher(request, pk):
    voucher = get_object_or_404(DebitRestVoucher, pk=pk)

    if voucher.approval_dr_status:
        return redirect('rest_debitvoucher_list')

    # Auto-generate mr_or_bill_no if missing
    if not voucher.mr_or_bill_no:
        base_code = "MBD-"
        last = DebitRestVoucher.objects.filter(mr_or_bill_no__startswith=base_code).order_by('-id').first()
        next_id = (last.id + 1) if last else 1
        generated_code = f"{base_code}{next_id:05d}"
        while DebitRestVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
            next_id += 1
            generated_code = f"{base_code}{next_id:05d}"
        voucher.mr_or_bill_no = generated_code

    # -------------------------
    # Get Expense and Purchase instances
    # -------------------------
    expense_obj = voucher.expense       # RestExpense instance or None
    purchase_obj = voucher.purchase     # RestPurchaseCost instance or None

    # Do NOT overwrite the ForeignKey field with a string!
    # Just keep the instances for Ledger/Transaction creation

    # Mark voucher as approved
    voucher.approval_dr_status = True
    voucher.save()

    # Update cash balance
    try:
        cash_type = CashRestType.objects.get(cash_type_name=voucher.cash_type)
        cash_type.type_amount = (cash_type.type_amount or 0) - (voucher.amount or 0)
        cash_type.type_note = f"Update Payment of voucher ID {voucher.id}"
        cash_type.save()
    except CashRestType.DoesNotExist:
        cash_type = None

    # Create Transaction History
    RestTransactionHistory.objects.create(
        project=voucher.project_name,
        transaction_type=voucher.type,
        head_of_account=voucher.head_of_account,
        cash_type=cash_type,
        amount=voucher.amount,
        cheque_number=voucher.cheque_number,
        date=timezone.now().date(),
        type_name=expense_obj.expense_name if expense_obj else None,  # use actual field for display
        reference=voucher.mr_or_bill_no,
        create_by=voucher.create_dr,
        particulars=voucher.particulars,
        tbl_id=voucher.id,
        tbl_name='Payment',
    )

    # Create Ledger Entry
    LedgerRestEntry.objects.create(
        project_name=voucher.project_name,
        type=voucher.type,
        contructor=getattr(voucher, 'contructor', None),
        vendor=getattr(voucher, 'vendor', None),
        customer_name=getattr(voucher, 'customer_name', None),
        bankName=getattr(voucher, 'bankName', None),
        exp_name=expense_obj,        # Keep as RestExpense instance
        purchase=purchase_obj,  # Keep as RestPurchaseCost instance
        capi_name=getattr(voucher, 'capi_name', None),
        empl_name=getattr(voucher, 'empl_name', None),
        invest_name=getattr(voucher, 'invest_name', None),
        type_name=expense_obj.expense_name if expense_obj else None,  # Display only
        cash_type=voucher.cash_type,
        cheque_number=voucher.cheque_number,
        head=voucher.head_of_account,
        mr_or_bill_no=voucher.mr_or_bill_no,
        date=voucher.date,
        description=voucher.particulars or '',
        debit=voucher.amount or 0,
        credit=0,
        carrier=getattr(voucher, 'carrier', None),
        entry_date=timezone.now().date(),
        loan_status='payment',
        tbl_id=voucher.id,
        tbl_name='Payment'
    )
        # ----------------------------
    # SMS Notification
    # ----------------------------
    sms_numbers = []
    
    STATIC_NUMBER = "8801913222203"  # always receive copy
    sms_numbers.append(STATIC_NUMBER)
    
    sms_message = ""
    
    # ----------------------------
    # Customer
    # ----------------------------
    if voucher.type == 'Customer' and voucher.customer_name:
        customer = voucher.customer_name
        if customer.contact_no:
            sms_numbers.append(customer.contact_no)
    
        sms_message = (
            f"Dear Customer,\n"
            f"Payment received: ৳{voucher.amount}\n"
            f"Date: {voucher.date.strftime('%d-%m-%Y')}\n"
            f"Ref: {voucher.mr_or_bill_no}\n"
            f"{voucher.project_name}\n"
            f"Thank you."
        )
    
    
    
    
    
    
    
    # ----------------------------
    # Vendor / Supplier
    # ----------------------------
    elif voucher.type == 'Vendor' and voucher.vendor:
        supplier = voucher.vendor
        if supplier.phone:
            sms_numbers.append(supplier.phone)
    
        sms_message = (
            f"Dear Supplier,\n"
            f"Payment made: ৳{voucher.amount}\n"
            f"Ref: {voucher.mr_or_bill_no}\n"
            f"{voucher.project_name}\n"
            f"Thank you."
        )
    
    # ----------------------------
    # Contractor
    # ----------------------------
    elif voucher.type == 'Contructor' and voucher.contructor:
        contractor = voucher.contructor
        if contractor.phone:
            sms_numbers.append(contractor.phone)
    
        sms_message = (
            f"Dear Contractor,\n"
            f"Payment made: ৳{voucher.amount}\n"
            f"Ref: {voucher.mr_or_bill_no}\n"
            f"{voucher.project_name}\n"
            f"Thank you."
        )
    
    
    
    
    
    
    
    
    # ----------------------------
    # Restaurant Employee Payment
    # ----------------------------
    
    
    # elif voucher.type == 'Employee' and voucher.empl_name:

    #     from restahrm.models import RestaurantEmployee 
       
    #     employee = RestaurantEmployee.objects.filter(
    #         rda_emp_name__iexact=voucher.empl_name.strip(),
    #         project_name=voucher.project_name
    #     ).first()

    #     if employee:

    #         if employee.rda_phone:
    #             sms_numbers.append(employee.rda_phone)

    #         month_name = voucher.date.strftime("%B")

    #         sms_message = (
    #             f"Dear {employee.rda_emp_name},\n"
    #             f"Your salary for the month of {month_name} has been paid successfully.\n"
    #             f"Amount: BDT {voucher.amount}\n"
    #             f"Project: {voucher.project_name}\n"
    #             f"Thank you."
    #         )

    #     else:
    #         print("Employee not found for this project. SMS not sent.")

    # ----------------------------
    # Capital Account
    # ----------------------------
    elif voucher.type == 'Capital' and voucher.capi_name:
        acc = voucher.capi_name
        if hasattr(acc, "phone") and acc.phone:
            sms_numbers.append(acc.phone)
    
        sms_message = (
            f"Capital payment processed: ৳{voucher.amount}\n"
            f"Ref: {voucher.mr_or_bill_no}"
            f"{voucher.project_name}\n"
        )
    
    # ----------------------------
    # Investment Account
    # ----------------------------
    elif voucher.type == 'Investment' and voucher.invest_name:
        acc = voucher.invest_name
        if hasattr(acc, "phone") and acc.phone:
            sms_numbers.append(acc.phone)
    
        sms_message = (
            f"Investment payment processed: ৳{voucher.amount}\n"
            f"Ref: {voucher.mr_or_bill_no}"
            f"{voucher.project_name}\n"
        )
    
    # ----------------------------
    # Revenue Account
    # ----------------------------
    elif voucher.type == 'Revenue' and voucher.reve_name:
        acc = voucher.reve_name
        if hasattr(acc, "phone") and acc.phone:
            sms_numbers.append(acc.phone)
    
        sms_message = (
            f"Revenue payment processed: ৳{voucher.amount}\n"
            f"Ref: {voucher.mr_or_bill_no}"
            f"{voucher.project_name}\n"
        )
    
    # ----------------------------
    # Remove duplicates
    # ----------------------------
    sms_numbers = list(set(filter(None, sms_numbers)))
    
    # ----------------------------
    # Send SMS
    # ----------------------------
    if sms_message:
        for number in sms_numbers:
            if not send_sms(number, sms_message):
                print(f"SMS sending failed for {number}")
    return redirect(reverse('rest_debit_voucher_pdf', args=[voucher.pk]))
    
    
    

## Balance Transfer History --
@login_required
def rest_transfer_list(request):
    transfers = RestBalanceTransfer.objects.all().order_by('-id')
    today = timezone.now()
    return render(request, 'restaurant/transferbalance/transfer_list.html', {'transfers': transfers,'today': today})





# @login_required
# def rest_transfer_add(request):
#     if request.method == 'POST':
#         form = RestBalanceTransferForm(request.POST)
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
#                     cheque = RestMainCheque.objects.get(id=cheque_id)
#                     cheque_number = cheque.cheque_number
#                     # Update MainCheque status
#                     cheque.status = 'used'
#                     cheque.remarks = note
#                     cheque.issue_date = transfer_date
#                     cheque.amount = amount
#                     cheque.save()
#                 except RestMainCheque.DoesNotExist:
#                     messages.error(request, 'Selected cheque not found.')
#                     return redirect('rest_transfer_add')

#             # Check available balance
#             if source.type_amount < amount:
#                 messages.error(request, 'Insufficient balance in Source Cash Type.')
#                 return redirect('rest_transfer_add')

#             try:
#                 with transaction.atomic():
#                     # Save main transfer
#                     transfer = form.save(commit=False)
#                     transfer.cheque_number = cheque_number
#                     transfer.save()

#                     # Get or create "Balance Transfer Account" head
#                     head, _ = RestHeadOfAccount.objects.get_or_create(head_name='Balance Transfer Account')

#                     # Create Ledger entries
#                     source_ledger = LedgerRestEntry.objects.create(
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

#                     dest_ledger = LedgerRestEntry.objects.create(
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
#                     RestTransactionHistory.objects.create(
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
#                     RestTransactionHistory.objects.create(
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
#                     return redirect('rest_transfer_list')

#             except Exception as e:
#                 print("Error creating transaction:", e)
#                 messages.error(request, f"Error saving TransactionHistory: {e}")
#                 return redirect('rest_transfer_add')

#     else:
#         form = RestBalanceTransferForm()

#     return render(request, 'restaurant/transferbalance/transfer_add.html', {'form': form})




@login_required
def rest_transfer_add(request):
    if request.method == 'POST':
        form = RestBalanceTransferForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source_type']
            destination = form.cleaned_data['destination_type']
            amount = form.cleaned_data['transfer_amount']
            transfer_date = form.cleaned_data['transfer_date']
            note = form.cleaned_data['note']
            project = form.cleaned_data['project_name']

            # Get cheque_id from POST
            cheque_id = request.POST.get('cheque_number')  # ID from dropdown
            cheque_number = None
            if cheque_id:
                try:
                    cheque = RestMainCheque.objects.get(id=cheque_id)
                    cheque_number = cheque.cheque_number
                    # Update MainCheque status
                    cheque.status = 'used'
                    cheque.remarks = note
                    cheque.issue_date = transfer_date
                    cheque.amount = amount
                    cheque.save()
                except RestMainCheque.DoesNotExist:
                    messages.error(request, 'Selected cheque not found.')
                    return redirect('rest_transfer_add')

            try:
                with transaction.atomic():
                    # Save main transfer
                    transfer = form.save(commit=False)
                    transfer.cheque_number = cheque_number
                    transfer.save()

                    # Get or create "Balance Transfer Account" head
                    head, _ = RestHeadOfAccount.objects.get_or_create(head_name='Balance Transfer Account')

                    # Create Ledger entries
                    source_ledger = LedgerRestEntry.objects.create(
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
                        carrier=getattr(transfer, 'carrier', None),
                        balance_trf=f'Transfer to {destination.cash_type_name}'
                    )

                    dest_ledger = LedgerRestEntry.objects.create(
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
                        carrier=getattr(transfer, 'carrier', None),
                        balance_trf=f'Received from {source.cash_type_name}'
                    )

                    # Create TransactionHistory entries
                    username = request.user.username if request.user.is_authenticated else "System"
                    ref_trans_id = f"BTC-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    # Transfer OUT
                    RestTransactionHistory.objects.create(
                        project=project,
                        transaction_type=source_ledger.type,
                        head_of_account=head,
                        cash_type=source,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date or timezone.now().date(),
                        type_name=f"{source_ledger.type}_Out",
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=source_ledger.description
                    )

                    # Transfer IN
                    RestTransactionHistory.objects.create(
                        project=project,
                        transaction_type=dest_ledger.type,
                        head_of_account=head,
                        cash_type=destination,
                        amount=amount,
                        cheque_number=cheque_number,
                        date=transfer_date or timezone.now().date(),
                        type_name=f"{dest_ledger.type}_In",
                        reference=ref_trans_id,
                        create_by=username,
                        particulars=dest_ledger.description
                    )

                    messages.success(request, 'Balance transfer saved and recorded in Transaction History.')
                    return redirect('rest_transfer_list')

            except Exception as e:
                print("Error creating transaction:", e)
                messages.error(request, f"Error saving TransactionHistory: {e}")
                return redirect('rest_transfer_add')

    else:
        form = RestBalanceTransferForm()

    return render(request, 'restaurant/transferbalance/transfer_add.html', {'form': form})




@login_required
def rest_transfer_detail(request, pk):
    transfer = get_object_or_404(RestBalanceTransfer, pk=pk)

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
    return render(request, 'restaurant/transferbalance/transfer_detail.html', context)
    
    
    

@login_required
def rest_ledger_manage_list(request):
    entries = LedgerRestEntry.objects.all().order_by('-date', '-id') 
    form = LedgerRestEntryForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'restaurant/ledgermanage/ledger_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })

    
    

@login_required
def rest_project_ledger_list(request):
    projectNames = ProjectFirstLevelName.objects.select_related('location', 'project_owner').all()
    context = {
        'projectNames': projectNames,
        'today': date.today(),
    }
    return render(request, 'restaurant/projectreport/project_ledger_list.html', context)
    
    

@login_required
def rest_project_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    form = LedgerRestFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  # <-- clearer naming
    cashTypes = CashRestType.objects.all()
    
    context = {
        'projectNames': projectName,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'restaurant/projectreport/project_ledger_manage.html', context)
    
    


# @login_required
# def rest_project_ledger_report(request):
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

#     # Filter by project/vendor/item/date
#     if is_valid(project_id):
#         inventories = inventories.filter(project_name_id=project_id)
#     if is_valid(vendor_id):
#         inventories = inventories.filter(vendor_name_id=vendor_id)
#     if is_valid(item_id):
#         inventories = inventories.filter(item_name_id=item_id)
#     if transaction_option == 'datewise':
#         if fd:
#             inventories = inventories.filter(requisition_date__gte=fd)
#         if td:
#             inventories = inventories.filter(requisition_date__lte=td)

#     # Group by project first
#     project_ids = inventories.values_list('project_name_id', flat=True).distinct()
#     report_data = []

#     for pid in project_ids:
#         project = get_object_or_404(ProjectFirstLevelName, id=pid)
#         project_inventories = inventories.filter(project_name_id=pid)

#         # Group by vendor within this project
#         vendor_groups = []
#         vendor_ids = project_inventories.values_list('vendor_name_id', flat=True).distinct()
#         for vid in vendor_ids:
#             vendor = get_object_or_404(Suppliers, id=vid) if vid else None
#             vendor_inventories = project_inventories.filter(vendor_name_id=vid)
#             total_amount = vendor_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
#             vendor_groups.append({
#                 'vendor': vendor,
#                 'inventory_list': vendor_inventories,
#                 'inventory_total': total_amount,
#             })

#         report_data.append({
#             'project': project,
#             'inventory_list': project_inventories,
#             'inventory_total': project_inventories.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
#             'vendor_groups': vendor_groups,
#         })

#     return render(request, 'restaurant/projectreport/project_ledger_report.html', {
#         'report_data': report_data,
#         'selected_filters': {
#             'project': project_id,
#             'vendor': vendor_id,
#             'item': item_id,
#             'from_date': from_date,
#             'to_date': to_date,
#             'transaction': transaction_option,
#         },
#         'print_time': datetime.now(),
#     })
    
    


from decimal import Decimal
from datetime import datetime
from django.db.models import Sum

@login_required
def rest_project_ledger_report(request):
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

    # Ledger entries
    ledgers = LedgerRestEntry.objects.all()

    # Filters
    if is_valid(project_id):
        ledgers = ledgers.filter(project_name_id=project_id)

    if is_valid(vendor_id):
        ledgers = ledgers.filter(vendor_id=vendor_id)

    if transaction_option == 'datewise':
        if fd:
            ledgers = ledgers.filter(date__gte=fd)
        if td:
            ledgers = ledgers.filter(date__lte=td)

    project_ids = ledgers.values_list(
        'project_name_id', flat=True
    ).distinct()

    report_data = []

    for pid in project_ids:
        project = get_object_or_404(ProjectFirstLevelName, id=pid)
        project_ledgers = ledgers.filter(project_name_id=pid)

        vendor_groups = []
        vendor_ids = project_ledgers.values_list(
            'vendor_id', flat=True
        ).distinct()

        for vid in vendor_ids:
            vendor = get_object_or_404(Suppliers, id=vid) if vid else None
            vendor_ledgers = project_ledgers.filter(vendor_id=vid)

            totals = vendor_ledgers.aggregate(
                debit_total=Sum('debit'),
                credit_total=Sum('credit')
            )

            debit = totals['debit_total'] or Decimal('0.00')
            credit = totals['credit_total'] or Decimal('0.00')
            balance = debit - credit

            vendor_groups.append({
                'vendor': vendor,
                'ledger_list': vendor_ledgers.order_by('date', 'id'),
                'debit_total': debit,
                'credit_total': credit,
                'balance': balance,
            })

        proj_totals = project_ledgers.aggregate(
            debit_total=Sum('debit'),
            credit_total=Sum('credit')
        )

        proj_debit = proj_totals['debit_total'] or Decimal('0.00')
        proj_credit = proj_totals['credit_total'] or Decimal('0.00')

        report_data.append({
            'project': project,
            'ledger_list': project_ledgers.order_by('date', 'id'),
            'debit_total': proj_debit,
            'credit_total': proj_credit,
            'balance': proj_debit - proj_credit,
            'vendor_groups': vendor_groups,
        })

    return render(
        request,
        'restaurant/projectreport/project_ledger_report.html',
        {
            'report_data': report_data,
            'selected_filters': {
                'project': project_id,
                'vendor': vendor_id,
                'from_date': from_date,
                'to_date': to_date,
                'transaction': transaction_option,
            },
            'print_time': datetime.now(),
        }
    )


    

# @login_required
# def rest_project_ledger_manage_pdf(request):
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

#     return render(request, 'restaurant/projectreport/project_ledger_manage_pdf.html', context)
    



# from decimal import Decimal
# from datetime import datetime
# from django.shortcuts import render
# from num2words import num2words

# @login_required
# def rest_project_ledger_manage_pdf(request):
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
#     grand_ledger_total_payment = Decimal('0.00')
#     grand_ledger_total_received = Decimal('0.00')

#     for project in projects:
#         project_block = {
#             'project': project,
#             'ledger_list': [],
#         }

#         # Ledger entries
#         ledgers = LedgerRestEntry.objects.filter(project_name=project)
#         if transaction_option == 'datewise':
#             if fd:
#                 ledgers = ledgers.filter(date__gte=fd)
#             if td:
#                 ledgers = ledgers.filter(date__lte=td)
#         ledgers = ledgers.order_by('date', 'id')

#         # --- Running balance ---
#         running_balance = Decimal('0.00')
#         ledger_list_with_balance = []
#         for entry in ledgers:
#             debit = entry.debit or Decimal('0.00')
#             credit = entry.credit or Decimal('0.00')
#             running_balance += credit - debit
#             entry.running_balance = running_balance
#             ledger_list_with_balance.append(entry)

#         project_block['ledger_list'] = ledger_list_with_balance

#         # Totals for project
#         ledger_total_payment = sum(entry.debit for entry in ledgers)
#         ledger_total_received = sum(entry.credit for entry in ledgers)
#         project_ledger = ledger_total_received - ledger_total_payment

#         project_block['ledger_total_payment'] = ledger_total_payment
#         project_block['ledger_total_received'] = ledger_total_received
#         project_block['project_ledger'] = project_ledger

#         # Add to grand totals
#         grand_ledger_total_payment += ledger_total_payment
#         grand_ledger_total_received += ledger_total_received

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
#         'grand_ledger_total_payment': grand_ledger_total_payment,
#         'grand_ledger_total_received': grand_ledger_total_received,
#         'grand_total_balance': grand_ledger_total_received - grand_ledger_total_payment,
#         'grand_total_in_words': amount_to_words(grand_ledger_total_received - grand_ledger_total_payment),
#         'selected_filters': {
#             'project': project_id,
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         },
#         'print_time': datetime.now(),
#     }

#     return render(request, 'restaurant/projectreport/project_ledger_manage_pdf.html', context)



from decimal import Decimal
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from num2words import num2words
from .models import LedgerRestEntry, ProjectFirstLevelName  # make sure to import your models

@login_required
def rest_project_ledger_manage_pdf(request):
    project_id = request.GET.get('project')
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

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # Projects queryset
    if is_valid(project_id):
        projects = ProjectFirstLevelName.objects.filter(id=project_id)
    else:
        projects = ProjectFirstLevelName.objects.all()

    report_data = []

    # Grand totals
    grand_debit_total = Decimal('0.00')
    grand_credit_total = Decimal('0.00')

    for project in projects:
        project_block = {
            'project': project,
            'ledger_list': [],
        }

        # Ledger entries per project
        ledgers = LedgerRestEntry.objects.filter(project_name=project)
        if transaction_option == 'datewise':
            if fd:
                ledgers = ledgers.filter(date__gte=fd)
            if td:
                ledgers = ledgers.filter(date__lte=td)
        ledgers = ledgers.order_by('date', 'id')

        # --- Running balance ---
        running_balance = Decimal('0.00')
        ledger_list_with_balance = []
        for entry in ledgers:
            debit = entry.debit or Decimal('0.00')
            credit = entry.credit or Decimal('0.00')
            running_balance += credit - debit  # Credit - Debit for balance
            entry.running_balance = running_balance
            ledger_list_with_balance.append(entry)

        project_block['ledger_list'] = ledger_list_with_balance

        # Totals for project
        debit_total = sum(entry.debit for entry in ledgers)
        credit_total = sum(entry.credit for entry in ledgers)
        balance = credit_total - debit_total

        project_block['debit_total'] = debit_total
        project_block['credit_total'] = credit_total
        project_block['balance'] = balance

        # Add to grand totals
        grand_debit_total += debit_total
        grand_credit_total += credit_total

        report_data.append(project_block)

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
        except:
            return f"{amount} Taka only"

    context = {
        'report_data': report_data,
        'grand_debit_total': grand_debit_total,
        'grand_credit_total': grand_credit_total,
        'grand_total_balance': grand_credit_total - grand_debit_total,
        'grand_total_in_words': amount_to_words(grand_credit_total - grand_debit_total),
        'selected_filters': {
            'project': project_id,
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        },
        'print_time': datetime.now(),
    }

    return render(request, 'restaurant/projectreport/project_ledger_manage_pdf.html', context)



## Bank Reports ---
@login_required
def rest_bank_reports_list(request):
    entries = LedgerRestEntry.objects.all().order_by('-date', '-id') 
    form = LedgerRestEntryForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'restaurant/bankreport/bank_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })
    
    
@login_required
def rest_bank_ledger_manage(request):
    cashTypes = CashRestType.objects.all()
    projectNames = ProjectFirstLevelName.objects.all()
    form = LedgerRestFilterForm(request.GET or None)

    context = {
        'cashTypes': cashTypes,
        #'projectNames': projectNames,
        'projectNames': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'form': form,
        'today': date.today(),
    }
    return render(request, 'restaurant/bankreport/bank_ledger_manage.html', context)
    
    
    

@login_required
def rest_bank_ledger_report(request):
    cash_type_id = request.GET.get('cash_type_name')
    projects_id = request.GET.get('project')
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

    entries = LedgerRestEntry.objects.all()
   
    if is_valid(projects_id):
        entries = entries.filter(project_name_id=projects_id)

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
        opening_entries = LedgerRestEntry.objects.filter(
            cash_type_id=cash_type_id,
            head__head_name='Open Balance Account',
            date__lt=fd
        )
        for e in opening_entries:
            balance += e.credit - e.debit

    elif balance_option == 'all':
            # Include opening balance for all cash types
            opening_entries = LedgerRestEntry.objects.filter(
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
    heads = RestHeadOfAccount.objects.all()
    cashTypes = CashRestType.objects.all()

    return render(request, 'restaurant/bankreport/bank_ledger_report.html', {
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
def rest_bank_ledger_manage_pdf(request):
    cash_type_id = request.GET.get('cash_type_name')
    project = request.GET.get('project')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    balance_option = request.GET.get('balance', 'exclude')  # include or exclude
    transaction_option = request.GET.get('transaction', 'datewise')  # all or datewise

    # Additional filters
    #project = request.GET.get('project', '')
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

    entries = LedgerRestEntry.objects.all()  

    if is_valid(cash_type_id) and balance_option != 'all':
        entries = entries.filter(cash_type_id=cash_type_id)

    # if is_valid(project):
    #     entries = entries.filter(project_name__icontains=project)
    
    if is_valid(project):
        entries = entries.filter(project_name_id=project)
        
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
        opening_entries = LedgerRestEntry.objects.filter(
            cash_type_id=cash_type_id,
            head__head_name='Open Balance Account',
            date__lt=fd
        )
        for e in opening_entries:
            balance += e.credit - e.debit
    
    elif balance_option == 'all':
            # Include opening balance for all cash types
            opening_entries = LedgerRestEntry.objects.filter(
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
        ct = CashRestType.objects.filter(id=cash_type_id).first()
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

    return render(request, 'restaurant/bankreport/bank_ledger_manage_pdf.html', context)
    
    
    
    

## Transaction Reports ---
@login_required
def rest_transaction_reports_list(request):
    entries = RestTransactionHistory.objects.all().order_by('-id')
    form = RestTransactionHistoryForm()
    
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

    return render(request, 'restaurant/transactionreport/transaction_reports_list.html', {
        'form': form,
        'entry_data': entry_data
    })


@login_required
def rest_transaction_ledger_manage(request):
    projectNames = ProjectFirstLevelName.objects.all()
    headNames = RestHeadOfAccount.objects.all()
    cashTypes = CashRestType.objects.all()
    form = LedgerRestFilterForm(request.GET or None)

    context = {
        #'projectNames': projectNames,
        'projectNames': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'headNames': headNames,
        'cashTypes': cashTypes,
        'form': form,
        'today': date.today(),
    }
    return render(request, 'restaurant/transactionreport/transaction_ledger_manage.html', context)
    
    

@login_required
def rest_transaction_ledger_report(request):
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

    form = RestTransactionHistoryForm()

    # Start with all entries ordered by date ascending for cumulative balance
    entries = RestTransactionHistory.objects.all().order_by('date', 'id')

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

    return render(request, 'restaurant/transactionreport/transaction_ledger_report.html', context)



@login_required
def rest_transaction_ledger_manage_pdf(request):
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

    form = RestTransactionHistoryForm()
    entries = RestTransactionHistory.objects.all().order_by('date', 'id')

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

    return render(request, 'restaurant/transactionreport/transaction_ledger_manage_pdf.html', context)
    
    


@login_required
def rest_employee_summary_report(request):
    today = timezone.now()
    current_month_start = today.replace(day=1)
    current_month_name = today.strftime('%B %Y')  # e.g., "September 2025"

    employees = RestaurantEmployee.objects.filter(rda_active_status=True)
    report_data = []

    for employee in employees:
        # Advance this month (deduction)
        advances = RestaurantAdvancePayment.objects.filter(
            employee=employee,
            date__gte=current_month_start,
            date__lte=today,
            status='due'
        )
        advance_total = advances.aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal(0)

        # Allowance this month (addition)
        allowances = RestaurantAllowances.objects.filter(
            employee=employee,
            date__gte=current_month_start,
            date__lte=today,
            status='due'
        )
        allowance_total = allowances.aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal(0)

        # LoanPayment deduction this month
        loans_qs = RestaurantLoanPayment.objects.filter(
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
        ledger_entries = LedgerRestEntry.objects.filter(
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

    return render(request, 'restaurant/reportmanage/employee_summary.html', {
        'report_data': report_data
    })



# @login_required
# def rest_employee_ledger_manage(request):
#     employees = RestaurantEmployee.objects.all()    
#     context = {
#         'employees': employees,
#         'today': date.today(),
#     }
#     return render(request, 'restaurant/reportmanage/employee_ledger_manage.html', context)


@login_required
def rest_employee_ledger_manage(request):

    projects_first = ProjectFirstLevelName.objects.filter(
        project_first_name__in=[
            "The Galleria Restauent Cafe",
            "The Galleria Live Kitchen"
        ]
    )

    employees = RestaurantEmployee.objects.filter(
        project_name__in=projects_first
    ).select_related('project_name')

    context = {
        'employees': employees,
        'today': date.today(),
    }

    return render(
        request,
        'restaurant/reportmanage/employee_ledger_manage.html',
        context
    )
    


@login_required
def rest_employee_ledger_report(request):
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
        employee = get_object_or_404(RestaurantEmployee, id=employee_id)
        salary = employee.rda_salary or Decimal('0.00')

        today = now().date()
        current_month_str = today.strftime("%B")
        current_year = today.year

        # === Advance Payments (deduction) ===
        advances = RestaurantAdvancePayment.objects.filter(employee=employee)
        if transaction_option == 'datewise':
            if fd: advances = advances.filter(date__gte=fd)
            if td: advances = advances.filter(date__lte=td)
        advance_total = advances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Allowances (addition) ===
        allowances = RestaurantAllowances.objects.filter(employee=employee)
        if transaction_option == 'datewise':
            if fd: allowances = allowances.filter(date__gte=fd)
            if td: allowances = allowances.filter(date__lte=td)
        allowance_total = allowances.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # === Loan Payments (deduction) ===
        loan_payments = RestaurantLoanPayment.objects.filter(employee=employee)
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
        ledgers = LedgerRestEntry.objects.filter(type='Employee', empl_name=employee.rda_emp_name)
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

    return render(request, 'restaurant/reportmanage/employee_ledger_report.html', {
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
# def rest_employee_ledger_manage_pdf(request):
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

#     employee = RestaurantEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(
#             request,
#             'restaurant/reportmanage/employee_ledger_report_print.html',
#             {}
#         )

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ===============================
#     # DATE RANGE RULE
#     # ===============================
#     if transaction_option == 'all':
#         first_salary = (
#             RestaurantSalaryPayment.objects
#             .filter(employee=employee)
#             .order_by('date')
#             .first()
#         )
#         fd = first_salary.date if first_salary else date(today.year, 1, 1)
#         td = today

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

#     td = min(td, today)
#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ===============================
#     # MONTH PROCESSING
#     # ===============================
#     for month_start in months_list:
#         month_end = month_start.replace(
#             day=monthrange(month_start.year, month_start.month)[1]
#         )

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
#         salary_payment_date = month_end + timedelta(days=1)

#         # Salary credit
#         combined_entries.append({
#             'date': salary_payment_date,
#             'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # Salary payments
#         for sp in RestaurantSalaryPayment.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Attendance =================
#         month_attendance = RestaurantAttendance.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         )

#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))

#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#         for row in att_summary:
#             status = row['att_status']
#             count = row['c']
#             if status in month_att:
#                 month_att[status] = count
#                 attendance_counts[status] += count

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

#         # Advances
#         for adv in RestaurantAdvancePayment.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # Allowances
#         for allow in RestaurantAllowances.objects.filter(
#             employee=employee,
#             date__range=(range_start, range_end)
#         ):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # Loan deduction
#         loans = RestaurantLoanPayment.objects.filter(employee=employee)
#         loan_deduction = Decimal('0.00')

#         for loan in loans:
#             include_month = False

#             if loan.start_month and loan.end_month:
#                 include_month = (
#                     loan.start_month.replace(day=1)
#                     <= month_start <=
#                     loan.end_month.replace(day=1)
#                 )

#             if loan.month_name and month_start.strftime('%B %Y') in loan.month_name:
#                 include_month = True

#             if include_month:
#                 loan_deduction += loan.deduction_amount or Decimal('0.00')

#         if loan_deduction > 0:
#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Loan Deduction for {prev_month_name}",
#                 'payment': loan_deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#         # Absent deduction
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         if total_days > 0 and absent_days > 0:
#             per_day_salary = salary_amount / total_days
#             deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Salary Deduction ({absent_days} Absent Day)",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#     # ===============================
#     # SORT & BALANCE
#     # ===============================
#     combined_entries.sort(key=lambda x: x['date'])

#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     context = {
#         'entry_data': combined_entries,
#         'employee': employee,
#         'attendance_counts': attendance_counts,
#         'print_time': datetime.now(),
#         'total_received': total_received,
#         'total_payment': total_payment,
#         'final_balance': final_balance,
#         'balance_in_words': num2words(final_balance, lang='en').title() + " Taka Only",
#     }

#     return render(
#         request,
#         'restaurant/reportmanage/employee_ledger_report_print.html',
#         context
#     )


@login_required
def rest_employee_ledger_manage_pdf(request):
    # GET parameters
    employee_id = request.GET.get('employee_name')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    transaction_option = request.GET.get('transaction', 'all')

    # parse dates
    def try_parse_date(val):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except:
            return None

    fd = try_parse_date(from_date)
    td = try_parse_date(to_date)

    # get employee
    employee = RestaurantEmployee.objects.filter(id=employee_id).first()
    if not employee:
        return render(
            request,
            'restaurant/reportmanage/employee_ledger_report_print.html',
            {}
        )

    today = date.today()
    salary_amount = employee.rda_salary or Decimal('0.00')

    # ================= DATE RANGE =================
    if transaction_option == 'all':
        first_salary = RestaurantSalaryPayment.objects.filter(employee=employee).order_by('date').first()
        fd = first_salary.date if first_salary else date(today.year, 1, 1)
        td = today

    use_date_filter = transaction_option == 'datewise'

    # ================= MONTH RANGE =================
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

    td = min(td, today)
    months_list = month_range(fd, td)

    combined_entries = []
    attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

    # ================= MONTH LOOP =================
    for month_start in months_list:
        month_end = month_start.replace(day=monthrange(month_start.year, month_start.month)[1])

        # skip current/future month
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
        salary_payment_date = month_end + timedelta(days=1)

        # ------------------ Salary Credit ------------------
        combined_entries.append({
            'date': salary_payment_date,
            'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
            'payment': None,
            'received': salary_amount.quantize(Decimal('0.01')),
            'cheque_number': 'N/A',
            'source': 'salary',
        })

        # ------------------ Salary Payments ------------------
        for sp in RestaurantSalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
            combined_entries.append({
                'date': sp.date,
                'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
                'payment': sp.amount,
                'received': None,
                'cheque_number': sp.cheque_number or '-',
                'source': 'salary_payment',
            })

        # ------------------ Attendance ------------------
        month_attendance = RestaurantAttendance.objects.filter(employee=employee, date__range=(range_start, range_end))
        att_summary = month_attendance.values('att_status').annotate(c=Count('id'))

        month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}
        for row in att_summary:
            status = row['att_status']
            count = row['c']
            if status in month_att:
                month_att[status] = count
                attendance_counts[status] += count

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

        # ------------------ Advances ------------------
        for adv in RestaurantAdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
            combined_entries.append({
                'date': adv.date,
                'description': adv.reason,
                'payment': adv.amount,
                'received': None,
                'cheque_number': adv.cheque_number or '-',
                'source': 'advance',
            })

        # ------------------ Allowances ------------------
        for allow in RestaurantAllowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
            combined_entries.append({
                'date': allow.date,
                'description': allow.reason,
                'payment': None,
                'received': allow.amount,
                'cheque_number': allow.cheque_number or '-',
                'source': 'allowance',
            })

        # ------------------ Loan Deductions ------------------
        loans = RestaurantLoanPayment.objects.filter(employee=employee)
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
                'description': f"Loan Deduction for {prev_month_name}",
                'payment': loan_deduction,
                'received': None,
                'cheque_number': '-',
                'source': 'deduction',
            })

        # ------------------ Absent Deductions ------------------
        total_days = month_attendance.count()
        absent_days = month_att['Absent']
        if total_days > 0 and absent_days > 0:
            per_day_salary = salary_amount / total_days
            deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))
            combined_entries.append({
                'date': salary_payment_date,
                'description': f"Salary Deduction ({absent_days} Absent Day)",
                'payment': deduction,
                'received': None,
                'cheque_number': '-',
                'source': 'deduction',
            })

    # ------------------ Employee Collections (DEBIT) ------------------
    collection_qs = Collection.objects.filter(type='Employee', employee=employee)
    if fd:
        collection_qs = collection_qs.filter(date__gte=fd)
    if td:
        collection_qs = collection_qs.filter(date__lte=td)

    for col in collection_qs:
        combined_entries.append({
            'date': col.date,
            'description': f"Employee Collection ({col.sales_type})" if col.sales_type else "Employee Collection",
            'payment': col.amount,
            'received': None,
            'cheque_number': '-',
            'source': 'collection'
        })

    # ------------------ Sort Entries by Date ------------------
    combined_entries.sort(key=lambda x: x['date'])

    # ------------------ Compute Running Balance ------------------
    balance = Decimal('0.00')
    for e in combined_entries:
        balance += (e['received'] or 0) - (e['payment'] or 0)
        e['balance'] = balance

    total_received = sum(e['received'] or 0 for e in combined_entries)
    total_payment = sum(e['payment'] or 0 for e in combined_entries)
    final_balance = total_received - total_payment

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
        'employee_name': employee.rda_emp_name if employee else "-",
        'project_name': employee.project.name if hasattr(employee, 'project') and employee.project else "All",
        'from_date': fd,
        'to_date': td,
        },
    }

    return render(
        request,
        'restaurant/reportmanage/employee_ledger_report_print.html',
        context
    )



# @login_required
# def rest_employee_ledger_manage_pdf(request):
#     from datetime import datetime, date, timedelta
#     from decimal import Decimal
#     from calendar import monthrange
#     from django.shortcuts import render
#     from django.db.models import Count
#     from num2words import num2words

#     # GET parameters
#     employee_id = request.GET.get('employee_name')
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     transaction_option = request.GET.get('transaction', 'all')

#     # parse dates
#     def try_parse_date(val):
#         try:
#             return datetime.strptime(val, "%Y-%m-%d").date()
#         except:
#             return None

#     fd = try_parse_date(from_date)
#     td = try_parse_date(to_date)

#     # get employee
#     employee = RestaurantEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(
#             request,
#             'restaurant/reportmanage/employee_ledger_report_print.html',
#             {}
#         )

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ================= DATE RANGE =================
#     if transaction_option == 'all':
#         first_salary = RestaurantSalaryPayment.objects.filter(employee=employee).order_by('date').first()
#         fd = first_salary.date if first_salary else date(today.year, 1, 1)
#         td = today

#     use_date_filter = transaction_option == 'datewise'

#     # ================= MONTH RANGE =================
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

#     td = min(td, today)
#     months_list = month_range(fd, td)

#     combined_entries = []
#     attendance_counts = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}

#     # ================= MONTH LOOP =================
#     for month_start in months_list:
#         month_end = month_start.replace(day=monthrange(month_start.year, month_start.month)[1])

#         # skip current/future month
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
#         salary_payment_date = month_end + timedelta(days=1)

#         # ------------------ Salary Credit ------------------
#         combined_entries.append({
#             'date': salary_payment_date,
#             'description': f"Salary : {employee.rda_emp_name}-{prev_month_name}",
#             'payment': None,
#             'received': salary_amount.quantize(Decimal('0.01')),
#             'cheque_number': 'N/A',
#             'source': 'salary',
#         })

#         # ------------------ Salary Payments ------------------
#         for sp in RestaurantSalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ------------------ Attendance ------------------
#         month_attendance = RestaurantAttendance.objects.filter(employee=employee, date__range=(range_start, range_end))
#         att_summary = month_attendance.values('att_status').annotate(c=Count('id'))

#         month_att = {'Present': 0, 'Absent': 0, 'Leave': 0, 'Off Day': 0}
#         for row in att_summary:
#             status = row['att_status']
#             count = row['c']
#             if status in month_att:
#                 month_att[status] = count
#                 attendance_counts[status] += count

#         # ✅ Override February attendance
#         if month_start.month == 2:
#             month_att['Absent'] = 2

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

#         # ------------------ Advances ------------------
#         for adv in RestaurantAdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ------------------ Allowances ------------------
#         for allow in RestaurantAllowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ------------------ Loan Deductions ------------------
#         loans = RestaurantLoanPayment.objects.filter(employee=employee)
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
#                 'description': f"Loan Deduction for {prev_month_name}",
#                 'payment': loan_deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })

#         # ------------------ Absent Deductions ------------------
#         total_days = month_attendance.count()
#         absent_days = month_att['Absent']

#         # ✅ Manual override for February
#         if month_start.month == 2:
#             absent_days = 2
#             deduction = Decimal('2000.00')

#             combined_entries.append({
#                 'date': salary_payment_date,
#                 'description': f"Salary Deduction ({absent_days} Absent Day)",
#                 'payment': deduction,
#                 'received': None,
#                 'cheque_number': '-',
#                 'source': 'deduction',
#             })
#         else:
#             if total_days > 0 and absent_days > 0:
#                 per_day_salary = salary_amount / total_days
#                 deduction = (per_day_salary * absent_days).quantize(Decimal('0.01'))

#                 combined_entries.append({
#                     'date': salary_payment_date,
#                     'description': f"Salary Deduction ({absent_days} Absent Day)",
#                     'payment': deduction,
#                     'received': None,
#                     'cheque_number': '-',
#                     'source': 'deduction',
#                 })

#     # ------------------ Employee Collections ------------------
#     collection_qs = Collection.objects.filter(type='Employee', employee=employee)
#     if fd:
#         collection_qs = collection_qs.filter(date__gte=fd)
#     if td:
#         collection_qs = collection_qs.filter(date__lte=td)

#     for col in collection_qs:
#         combined_entries.append({
#             'date': col.date,
#             'description': f"Employee Collection ({col.sales_type})" if col.sales_type else "Employee Collection",
#             'payment': col.amount,
#             'received': None,
#             'cheque_number': '-',
#             'source': 'collection'
#         })

#     # ------------------ Sort ------------------
#     combined_entries.sort(key=lambda x: x['date'])

#     # ------------------ Compute Running Balance ------------------
#     balance = Decimal('0.00')
#     for e in combined_entries:
#         balance += (e['received'] or 0) - (e['payment'] or 0)
#         e['balance'] = balance

#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

#     # ------------------ Final Adjustment to Zero ------------------
#     if final_balance != 0:
#         combined_entries.append({
#             'date': td,
#             'description': "Final Adjustment to Clear Balance",
#             'payment': final_balance if final_balance > 0 else None,
#             'received': -final_balance if final_balance < 0 else None,
#             'cheque_number': '-',
#             'source': 'adjustment',
#         })
#         final_balance = Decimal('0.00')

#     # ------------------ Recalculate totals ------------------
#     total_received = sum(e['received'] or 0 for e in combined_entries)
#     total_payment = sum(e['payment'] or 0 for e in combined_entries)
#     final_balance = total_received - total_payment

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
#             'employee_name': employee.rda_emp_name if employee else "-",
#             'project_name': employee.project.name if hasattr(employee, 'project') and employee.project else "All",
#             'from_date': fd,
#             'to_date': td,
#         },
#     }

#     return render(
#         request,
#         'restaurant/reportmanage/employee_ledger_report_print.html',
#         context
#     )









# @login_required
# def rest_employee_ledger_manage_pdf(request):
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

#     employee = RestaurantEmployee.objects.filter(id=employee_id).first()
#     if not employee:
#         return render(request, 'restaurant/reportmanage/employee_ledger_report_print.html', {})

#     today = date.today()
#     salary_amount = employee.rda_salary or Decimal('0.00')

#     # ==================================================
#     # FIXED RULE: transaction = all → employee's first SalaryPayment → today
#     # ==================================================
#     if transaction_option == 'all':
#         first_salary = RestaurantSalaryPayment.objects.filter(employee=employee).order_by('date').first()
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
#         for sp in RestaurantSalaryPayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': sp.date,
#                 'description': sp.reason or f"Salary Month Of {sp.monthofsalary}",
#                 'payment': sp.amount,
#                 'received': None,
#                 'cheque_number': sp.cheque_number or '-',
#                 'source': 'salary_payment',
#             })

#         # ================= Attendance =================
#         month_attendance = RestaurantSalaryPayment.objects.filter(
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
#         for adv in RestaurantAdvancePayment.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': adv.date,
#                 'description': adv.reason,
#                 'payment': adv.amount,
#                 'received': None,
#                 'cheque_number': adv.cheque_number or '-',
#                 'source': 'advance',
#             })

#         # ================= Allowances =================
#         for allow in RestaurantAllowances.objects.filter(employee=employee, date__range=(range_start, range_end)):
#             combined_entries.append({
#                 'date': allow.date,
#                 'description': allow.reason,
#                 'payment': None,
#                 'received': allow.amount,
#                 'cheque_number': allow.cheque_number or '-',
#                 'source': 'allowance',
#             })

#         # ================= Loan Deduction =================
#         loans = RestaurantLoanPayment.objects.filter(employee=employee)
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
#         'restaurant/reportmanage/employee_ledger_report_print.html',
#         context
#     )





# from django.shortcuts import render
# from django.db.models import Sum
# from django.utils import timezone

# from .models import Collection


# def rest_collection_ledger(request):
#     project_id = request.GET.get("project")
#     start_date = request.GET.get("start")
#     end_date = request.GET.get("end")

#     collections = Collection.objects.select_related(
#         "project",
#         "sales_type",
#         "cash_type"
#     ).order_by("date")

#     if project_id:
#         collections = collections.filter(project_id=project_id)

#     if start_date:
#         collections = collections.filter(date__gte=start_date)

#     if end_date:
#         collections = collections.filter(date__lte=end_date)

#     total_amount = collections.aggregate(
#         total=Sum("amount")
#     )["total"] or 0

#     context = {
#         "collections": collections,
#         "total_amount": total_amount,
#         "print_time": timezone.now(),
#     }

#     return render(request,
#                   "restaurant/rest_collection_ledger.html",
#                   context)




from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from num2words import num2words

from .models import (
    Collection,
    ProjectFirstLevelName,
    SalesRestType,
    CashRestType,
)


def rest_collection_ledger(request):

    collections = Collection.objects.select_related(
        "project",
        "sales_type",
        "cash_type"
    ).order_by("-date", "-id")

    # ---------- Filters ----------
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    project_id = request.GET.get("project")
    sales_type_id = request.GET.get("sales_type")
    cash_type_id = request.GET.get("cash_type")

    if start_date:
        collections = collections.filter(date__gte=start_date)

    if end_date:
        collections = collections.filter(date__lte=end_date)

    if project_id:
        collections = collections.filter(project_id=project_id)

    if sales_type_id:
        collections = collections.filter(sales_type_id=sales_type_id)

    if cash_type_id:
        collections = collections.filter(cash_type_id=cash_type_id)

    # ---------- Total ----------
    total_amount = collections.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # ---------- Total in Words ----------
    try:
        total_in_words = num2words(total_amount, to="cardinal", lang="en").title() + " Taka Only"
    except:
        total_in_words = ""

    context = {
        "collections": collections,
        "total_amount": total_amount,
        "total_in_words": total_in_words,
        #"projects": ProjectFirstLevelName.objects.all(),
        "projects": ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        "sales_types": SalesRestType.objects.all(),
        "cash_types": CashRestType.objects.all(),
        "print_time": timezone.now(),
    }

    return render(
        request,
        "restaurant/rest_collection_ledger.html",
        context,
    )

    
    
# def rest_dailyPayment_ledger(request):

#     payments = DailyPayment.objects.select_related(
#         "project",
#         "sales_type",
#         "cash_type"
#     ).order_by("-date")

#     # ---------- Filters ----------
#     start_date = request.GET.get("start_date")
#     end_date = request.GET.get("end_date")
#     project_id = request.GET.get("project")
#     sales_type_id = request.GET.get("sales_type")
#     cash_type_id = request.GET.get("cash_type")

#     if start_date:
#         payments = payments.filter(date__gte=start_date)

#     if end_date:
#         payments = payments.filter(date__lte=end_date)

#     if project_id:
#         payments = payments.filter(project_id=project_id)

#     if sales_type_id:
#         payments = payments.filter(sales_type_id=sales_type_id)

#     if cash_type_id:
#         payments = payments.filter(cash_type_id=cash_type_id)

#     # ---------- Total ----------
#     total_amount = payments.aggregate(
#         total=Sum("amount")
#     )["total"] or 0

#     # ---------- Amount in Words ----------
#     try:
#         amount_words = num2words(total_amount, lang="en")
#         amount_words = amount_words.replace(",", "").title() + " Taka Only"
#     except:
#         amount_words = ""

#     context = {
#         "payments": payments,
#         "total_amount": total_amount,
#         "amount_words": amount_words,
#         "projects": ProjectFirstLevelName.objects.all(),
#         "sales_types": SalesRestType.objects.all(),
#         "cash_types": CashRestType.objects.all(),
#         "print_time": timezone.now(),
#     }

#     return render(
#         request,
#         "restaurant/rest_daily_payment_ledger.html",
#         context,
#     )
    



from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from num2words import num2words

def rest_dailyPayment_ledger(request):
    payments = DailyPayment.objects.select_related(
        "project",
        "sales_type",
        "cash_type",
        "rest_exp",
        "pur_cost"
    ).order_by("-date")

    # ---------- Filters ----------
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    project_id = request.GET.get("project")
    dpay_type = request.GET.get("dpay_types")
    type_name_id = request.GET.get("type_name")
    sales_type_id = request.GET.get("sales_type")
    cash_type_id = request.GET.get("cash_type")

    if start_date:
        payments = payments.filter(date__gte=start_date)

    if end_date:
        payments = payments.filter(date__lte=end_date)

    if project_id:
        payments = payments.filter(project_id=project_id)

    # ✅ Filter by Type
    if dpay_type:
        payments = payments.filter(type=dpay_type)

    # ✅ Filter by Name (depends on type)
    if type_name_id and dpay_type:
        if dpay_type == "Expense":
            payments = payments.filter(rest_exp_id=type_name_id)
        elif dpay_type == "Purchase":
            payments = payments.filter(pur_cost_id=type_name_id)

    if sales_type_id:
        payments = payments.filter(sales_type_id=sales_type_id)

    if cash_type_id:
        payments = payments.filter(cash_type_id=cash_type_id)

    # ---------- Total ----------
    total_amount = payments.aggregate(total=Sum("amount"))["total"] or 0

    # ---------- Amount in Words ----------
    try:
        amount_words = num2words(total_amount, lang="en")
        amount_words = amount_words.replace(",", "").title() + " Taka Only"
    except:
        amount_words = ""

    context = {
        "payments": payments,
        "total_amount": total_amount,
        "amount_words": amount_words,
        #"projects": ProjectFirstLevelName.objects.all(),
        "projects": ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        "sales_types": SalesRestType.objects.all(),
        "cash_types": CashRestType.objects.all(),
        "dpay_types": DailyPayment.TYPE_CHOICES,
        "expense_names": RestExpense.objects.all(),
        "purchase_names": RestPurchaseCost.objects.all(),
        "print_time": timezone.now(),
    }

    return render(
        request,
        "restaurant/rest_daily_payment_ledger.html",
        context,
    )


@login_required
def rest_customer_summary_report(request):
    customers = Customer.objects.all()
    report_data = []

    for customer in customers:
        entries = LedgerRestEntry.objects.filter(type='Customer', customer_name=customer).order_by('date')

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

    return render(request, 'restaurant/reportmanage/customer_summary_report.html', {
        'report_data': report_data
    })




@login_required
def rest_customer_ledger_manage(request):
    #projectName = ProjectFirstLevelName.objects.all()
    head = RestHeadOfAccount.objects.all()
    form = LedgerRestFilterForm(request.GET or None)
    items = HeadOfRequisition.objects.all()  
    cashTypes = CashRestType.objects.all()
    
    context = {
        'projectNames': ProjectFirstLevelName.objects.filter(
            project_first_name__in=[
                "The Galleria Restauent Cafe",
                "The Galleria Live Kitchen"
            ]
        ),
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'items': items,  # <-- pass as "items"
        'today': date.today(),
    }
    return render(request, 'restaurant/reportmanage/customer_ledger_manage.html', context)




# @login_required
# def rest_customer_ledger_report(request):
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

#         # Only Ledger entries (CREDIT)
#         ledger_entries = LedgerRestEntry.objects.filter(
#             type='Customer',
#             customer_name=customer
#         ).order_by('date')

#         # Apply date filter
#         if transaction_option == 'datewise':
#             if fd:
#                 ledger_entries = ledger_entries.filter(date__gte=fd)
#             if td:
#                 ledger_entries = ledger_entries.filter(date__lte=td)

#         combined_entries = []

#         for e in ledger_entries:
#             combined_entries.append({
#                 'type': 'Ledger',
#                 'date': e.date,
#                 'project_name': e.project_name.project_first_name if e.project_name else '',
#                 'description': e.description,
#                 'debit': 0,
#                 'credit': e.credit or 0
#             })

#         if not combined_entries:
#             continue

#         # Totals
#         total_debit = sum(e['debit'] for e in combined_entries)
#         total_credit = sum(e['credit'] for e in combined_entries)
#         balance = total_debit - total_credit

#         report_data.append({
#             'customer': customer,
#             'first_date': combined_entries[0]['date'],
#             'total_debit': total_debit,
#             'total_credit': total_credit,
#             'balance': balance,
#             'entries': combined_entries
#         })

#     return render(request, 'restaurant/reportmanage/customer_ledger_report.html', {
#         'report_data': report_data,
#         'filters': {
#             'customer_id': customer_id,
#             'from_date': from_date,
#             'to_date': to_date,
#             'transaction': transaction_option,
#         }
#     })
    


from datetime import datetime

@login_required
def rest_customer_ledger_report(request):
    customer_id = request.GET.get('customer_name')
    project_id = request.GET.get('project')
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

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # =========================
    # CUSTOMER FILTER
    # =========================
    if is_valid(customer_id):
        customers = Customer.objects.filter(id=customer_id)
    else:
        customers = Customer.objects.all()

    report_data = []

    for customer in customers:

        # =========================
        # LEDGER BASE QUERY
        # =========================
        ledger_entries = LedgerRestEntry.objects.filter(
            type='Customer',
            customer_name=customer
        )

        # =========================
        # PROJECT FILTER (IMPORTANT)
        # =========================
        if is_valid(project_id):
            ledger_entries = ledger_entries.filter(project_name_id=project_id)

        # =========================
        # DATE FILTER
        # =========================
        if transaction_option == 'datewise':
            if fd:
                ledger_entries = ledger_entries.filter(entry_date__gte=fd)
            if td:
                ledger_entries = ledger_entries.filter(entry_date__lte=td)

        ledger_entries = ledger_entries.order_by('entry_date')

        combined_entries = []

        for e in ledger_entries:
            combined_entries.append({
                'type': 'Ledger',
                'date': e.date,
                'project_name': e.project_name.project_first_name if e.project_name else '',
                'description': e.description,

                # =========================
                # FIXED: proper decimal values
                # =========================
                'debit': e.debit or 0,
                'credit': e.credit or 0,
            })

        if not combined_entries:
            continue

        # =========================
        # TOTAL CALCULATION
        # =========================
        total_debit = sum(float(e['debit']) for e in combined_entries)
        total_credit = sum(float(e['credit']) for e in combined_entries)
        balance = total_debit - total_credit

        report_data.append({
            'customer': customer,
            'first_date': combined_entries[0]['date'],
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance': balance,
            'entries': combined_entries
        })

    return render(request, 'restaurant/reportmanage/customer_ledger_report.html', {
        'report_data': report_data,
        'filters': {
            'customer_id': customer_id,
            'project_id': project_id,   # ✅ ADDED
            'from_date': from_date,
            'to_date': to_date,
            'transaction': transaction_option,
        }
    })
    
    
    
    
# from datetime import datetime
# from decimal import Decimal
# from num2words import num2words

# @login_required
# def rest_customer_ledger_manage_pdf(request):
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

#         ledger_entries = LedgerRestEntry.objects.filter(
#             type='Customer',
#             customer_name=customer
#         )

#         # Apply date filter
#         if transaction_option == 'datewise':
#             if fd:
#                 ledger_entries = ledger_entries.filter(date__gte=fd)
#             if td:
#                 ledger_entries = ledger_entries.filter(date__lte=td)

#         combined_entries = []

#         for l in ledger_entries.order_by('date'):
#             combined_entries.append({
#                 'date': l.date,
#                 'customer': customer.customer_name,
#                 'project': l.project_name.project_first_name if l.project_name else '-',
#                 'description': l.description or '',
#                 'debit': l.debit or Decimal('0.00'),
#                 'credit': l.credit or Decimal('0.00'),
#             })

#         # Running balance
#         running_balance = Decimal('0.00')
#         for row in combined_entries:
#             running_balance += row['debit'] - row['credit']
#             row['balance'] = running_balance

#         if combined_entries:
#             report_data.append({
#                 'customer_name': customer.customer_name,
#                 'project_name': combined_entries[0]['project'],
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

#     total_debit = sum(group['total_debit'] for group in report_data)
#     total_credit = sum(group['total_credit'] for group in report_data)
#     final_balance = sum(group['final_balance'] for group in report_data)

#     context = {
#         'report_data': report_data,
#         'total_debit': total_debit,
#         'total_credit': total_credit,
#         'final_balance': final_balance,
#         'balance_in_words': amount_to_words(final_balance),
#         'print_time': datetime.now(),
#         'selected_filters': {
#             'customer': customers.first().customer_name if is_valid(customer_id) else "All",
#             'from_date': fd,
#             'to_date': td,
#             'transaction': transaction_option,
#         }
#     }

#     return render(request, 'restaurant/reportmanage/customer_ledger_manage_pdf.html', context)
    


from datetime import datetime
from decimal import Decimal
from num2words import num2words

@login_required
def rest_customer_ledger_manage_pdf(request):
    customer_id = request.GET.get('customer_name')
    project_id = request.GET.get('project')
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

    fd = parse_date(from_date)
    td = parse_date(to_date)

    # =========================
    # CUSTOMER FILTER
    # =========================
    customers = Customer.objects.filter(id=customer_id) if is_valid(customer_id) else Customer.objects.all()

    report_data = []

    for customer in customers:

        # =========================
        # BASE QUERY
        # =========================
        ledger_entries = LedgerRestEntry.objects.filter(
            type='Customer',
            customer_name=customer
        )

        # =========================
        # PROJECT FILTER (IMPORTANT FIX)
        # =========================
        if is_valid(project_id):
            ledger_entries = ledger_entries.filter(project_name_id=project_id)
        # else: no filter → ALL projects

        # =========================
        # DATE FILTER
        # =========================
        if transaction_option == 'datewise':
            if fd:
                ledger_entries = ledger_entries.filter(entry_date__gte=fd)
            if td:
                ledger_entries = ledger_entries.filter(entry_date__lte=td)

        ledger_entries = ledger_entries.order_by('entry_date')

        combined_entries = []

        for l in ledger_entries:
            combined_entries.append({
                'date': l.date,
                'entry_date': l.entry_date,
                'customer': customer.customer_name,
                'project': l.project_name.project_first_name if l.project_name else '-',
                'description': l.description or '',
                'debit': l.debit or Decimal('0.00'),
                'credit': l.credit or Decimal('0.00'),
            })

        # =========================
        # RUNNING BALANCE
        # =========================
        running_balance = Decimal('0.00')

        for row in combined_entries:
            running_balance += (row['debit'] - row['credit'])
            row['balance'] = running_balance

        if combined_entries:
            report_data.append({
                'customer_name': customer.customer_name,
                'project_name': combined_entries[0]['project'],
                'ledger_entries': combined_entries,
                'total_debit': sum(r['debit'] for r in combined_entries),
                'total_credit': sum(r['credit'] for r in combined_entries),
                'final_balance': running_balance,
            })

    # =========================
    # AMOUNT IN WORDS
    # =========================
    def amount_to_words(amount):
        try:
            amount = float(amount)
            if amount < 0:
                return "Minus " + num2words(abs(amount), lang='en').title() + " Taka"
            return num2words(amount, lang='en').title() + " Taka"
        except:
            return "Invalid Amount"

    total_debit = sum(group['total_debit'] for group in report_data)
    total_credit = sum(group['total_credit'] for group in report_data)
    final_balance = sum(group['final_balance'] for group in report_data)

    context = {
        'report_data': report_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': final_balance,
        'balance_in_words': amount_to_words(final_balance),
        'print_time': datetime.now(),
        'selected_filters': {
            'customer': customers.first().customer_name if is_valid(customer_id) else "All",
            'project': project_id if is_valid(project_id) else "All",  # ✅ ADDED
            'from_date': fd,
            'to_date': td,
            'transaction': transaction_option,
        }
    }

    return render(request, 'restaurant/reportmanage/customer_ledger_manage_pdf.html', context)
    
    

## Supplier Reports module ----
@login_required
def rest_supplier_reports_manage_list(request):
    entries = LedgerRestEntry.objects.all().order_by('-date', '-id') 
    form = LedgerRestEntryForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'restaurant/supplierledger/supplier_reports_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })



@login_required
def rest_supplier_ledger_manage(request):
    projectName = ProjectFirstLevelName.objects.all()
    head = RestHeadOfAccount.objects.all()
    form = LedgerRestFilterForm(request.GET or None)
    head_exp_name = HeadOfExpense.objects.all()
    cashTypes = CashRestType.objects.all()
    context = {
        'projectNames': projectName,
        'heads': head,
        'form': form,
        'cashTypes': cashTypes,
        'head_exp_name': head_exp_name,
        'today': date.today(),
    }
    return render(request, 'restaurant/supplierledger/supplier_ledger_manage.html', context)



@login_required
def rest_supplier_ledger_report(request):
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
    return render(request, 'restaurant/supplierledger/ledger_report_details.html', context)




## Reports module ----
@login_required
def rest_reports_manage_list(request):
    entries = LedgerRestEntry.objects.all().order_by('-date', '-id') 
    form = LedgerRestEntryForm()
    
    # Calculate running balance
    balance = Decimal('0.00')
    entry_data = []
    for entry in entries:
        balance += entry.credit - entry.debit
        entry_data.append({
            'entry': entry,
            'balance': balance
        })

    return render(request, 'restaurant/reportmanage/reports_manage_list.html', {
        'form': form,
        'entry_data': entry_data
    })




## ----- New code- General Report ---

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required


@login_required
def rest_ledger_manage(request):

    ledger_entries = LedgerRestEntry.objects.all()

    # Filter by Head
    head_id = request.GET.get('head')
    if head_id:
        ledger_entries = ledger_entries.filter(head_id=head_id)

    # Filter by Vendor / Contructor / Bank
    type_id = request.GET.get('cash_type_name')
    if type_id:
        ledger_entries = ledger_entries.filter(
            Q(vendor_id=type_id) |
            Q(contructor_id=type_id) |
            Q(bankName_id=type_id)
        )

    # Filter by Project
    project_id = request.GET.get('project')
    if project_id:
        ledger_entries = ledger_entries.filter(project_name_id=project_id)

    # Get dropdown values
    head_ids = ledger_entries.exclude(head__isnull=True)\
        .values_list('head', flat=True).distinct()

    project_ids = ledger_entries.exclude(project_name__isnull=True)\
        .values_list('project_name', flat=True).distinct()

    vendor_ids = ledger_entries.exclude(vendor_id__isnull=True)\
        .values_list('vendor_id', flat=True)

    contructor_ids = ledger_entries.exclude(contructor_id__isnull=True)\
        .values_list('contructor_id', flat=True)

    bank_ids = ledger_entries.exclude(bankName_id__isnull=True)\
        .values_list('bankName_id', flat=True)

    used_cash_ids = set(vendor_ids) | set(contructor_ids) | set(bank_ids)

    cashTypes = CashRestType.objects.filter(id__in=used_cash_ids)

    heads = RestHeadOfAccount.objects.filter(id__in=head_ids)

    projects = ProjectFirstLevelName.objects.filter(id__in=project_ids)

    context = {
        'heads': heads,
        'cashTypes': cashTypes,
        'projectNames': projects,
        'today': date.today(),
    }

    return render(request, 'restaurant/reportmanage/ledger_manage.html', context)


# ----------------------------------------------------------
# Get Vendor / Contructor / Bank / Expense / Capital etc
# ----------------------------------------------------------

@login_required
def rest_get_types_by_head(request, head_id):

    ledger_entries = LedgerRestEntry.objects.filter(head_id=head_id)

    unique_ids = set()
    data = []

    for entry in ledger_entries:

        # Vendor
        if entry.vendor and entry.vendor.id not in unique_ids:
            unique_ids.add(entry.vendor.id)
            data.append({
                'id': entry.vendor.id,
                'type': entry.type,
                'name': entry.vendor.rest_supplier_name
            })

        # Contructor
        if entry.contructor and entry.contructor.id not in unique_ids:
            unique_ids.add(entry.contructor.id)
            data.append({
                'id': entry.contructor.id,
                'type': entry.type,
                'name': entry.contructor.supervisor_name
            })

        # Bank
        if entry.bankName and entry.bankName.id not in unique_ids:
            unique_ids.add(entry.bankName.id)
            data.append({
                'id': entry.bankName.id,
                'type': entry.type,
                'name': entry.bankName.cash_type_name
            })

        # Expense
        if entry.exp_name and entry.exp_name.id not in unique_ids:
            unique_ids.add(entry.exp_name.id)
            data.append({
                'id': entry.exp_name.id,
                'type': entry.type,
                'name': entry.exp_name.expense_name
            })
        
         # Purchase
        if entry.purchase and entry.purchase.id not in unique_ids:
            unique_ids.add(entry.purchase.id)
            data.append({
                'id': entry.purchase.id,
                'type': entry.type,
                'name': entry.purchase.pur_cost_name
            })

        # Capital
        if entry.capi_name and entry.capi_name.id not in unique_ids:
            unique_ids.add(entry.capi_name.id)
            data.append({
                'id': entry.capi_name.id,
                'type': entry.type,
                'name': entry.capi_name.person_name
            })

        # Investment
        if entry.invest_name and entry.invest_name.id not in unique_ids:
            unique_ids.add(entry.invest_name.id)
            data.append({
                'id': entry.invest_name.id,
                'type': entry.type,
                'name': entry.invest_name.person_name
            })

    return JsonResponse(data, safe=False)


# ----------------------------------------------------------
# Get Projects by Head + Type
# ----------------------------------------------------------

@login_required
def rest_get_projects_by_head_cash(request, head_id, cash_type_id):

    entries = LedgerRestEntry.objects.filter(head_id=head_id).filter(
        Q(vendor_id=cash_type_id) |
        Q(contructor_id=cash_type_id) |
        Q(bankName_id=cash_type_id) |
        Q(capi_name_id=cash_type_id) |
        Q(exp_name_id=cash_type_id) |
        Q(purchase_id=cash_type_id) |
        Q(invest_name_id=cash_type_id)
    )

    project_ids = entries.values_list('project_name', flat=True).distinct()

    projects = ProjectFirstLevelName.objects.filter(id__in=project_ids)

    data = [
        {
            'id': p.id,
            'name': p.project_first_name
        }
        for p in projects
    ]

    return JsonResponse(data, safe=False)
    
    
    

# @login_required
# def rest_ledger_report(request):
#     head_id = request.GET.get('head')
#     entity_id = request.GET.get('cash_type_name')  
#     project_id = request.GET.get('project')
#     type_value = request.GET.get('type')  # Default: Vendor
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

#     # -------------------------
#     # Filter Ledger Entries
#     # -------------------------
#     ledger_entries = LedgerRestEntry.objects.filter(type=type_value)

#     if is_valid(project_id):
#         ledger_entries = ledger_entries.filter(project_name_id=project_id)

#     if is_valid(head_id):
#         ledger_entries = ledger_entries.filter(head_id=head_id)

#     if is_valid(entity_id):
#         if type_value == 'Vendor':
#             ledger_entries = ledger_entries.filter(vendor_id=entity_id)
#         elif type_value == 'Contractor':
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

#     # -------------------------
#     # Prepare Combined Data
#     # -------------------------
#     entry_data = []
#     balance = Decimal('0.00')

#     for entry in ledger_entries:
#         if entry.type == 'Vendor' and entry.vendor:
#             name = entry.vendor.rest_supplier_name

#         elif entry.type == 'Contractor' and entry.contractor:
#             name = entry.contructor.supervisor_name

#         elif entry.type == 'Capital' and entry.capi_name:
#             # CapitalAccount -> person_name (valid)
#             name = entry.capi_name.person_name

#         elif entry.type == 'Customer' and entry.customer_name:
#             name = entry.customer_name.customer_name

#         elif entry.type == 'Bank' and entry.bankName:
#             name = entry.bankName.cash_type_name

#         elif entry.type == 'Expense' and entry.exp_name:
#             # HeadOfExpense -> head_exp_name (valid)
#             name = entry.exp_name.head_exp_name

#         else:
#             name = 'N/A'

#         print(name)


#         balance += entry.credit - entry.debit

#         entry_data.append({
#             'source': 'ledger',
#             'project_name': entry.project_name,
#             'head': entry.head.head_name if entry.head else '',
#             'name': name,
#             'date': entry.date,
#             'description': entry.description,
#             'debit': entry.debit,
#             'credit': entry.credit,
#             'balance': balance,
#         })

#     # -------------------------
#     # If Vendor: Load Inventory Entries
#     # -------------------------
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
#             entry_data.append({
#                 'source': 'inventory',
#                 'project_name': inv.project_name,
#                 'head': inv.item_name.head_requi_name if inv.item_name else '',
#                 'name': inv.vendor_name.rest_supplier_name if inv.vendor_name else '',
#                 'date': inv.requisition_date,
#                 'description': inv.remark,
#                 'debit': Decimal('0.00'),
#                 'credit': inv.amount,
#                 'balance': '',
#             })

#     # -------------------------
#     # Final Sorting
#     # -------------------------
#     entry_data.sort(key=lambda x: (x['date'] or datetime.min.date()))

#     return render(request, 'restaurant/reportmanage/ledger_report.html', {
#         'entry_data': entry_data,
#         'projectNames': ProjectFirstLevelName.objects.all(),
#         'heads': HeadOfAccount.objects.all(),
#         'vendors': Suppliers.objects.all(),           # optional dropdown
#         'supervisors': SiteSupervisor.objects.all(),  # optional dropdown
#         'capital_accounts': CapitalAccount.objects.all(),  # optional dropdown
#         'selected_filters': {
#             'type': type_value,
#             'head': head_id,
#             'cash_type_name': entity_id,
#             'project': project_id,
#             'from_date': from_date,
#             'to_date': to_date,
#             'transaction': transaction_option,
#         }
#     })



from decimal import Decimal
from datetime import datetime

@login_required
def rest_ledger_report(request):
    head_id = request.GET.get('head')
    entity_id = request.GET.get('cash_type_name')
    project_id = request.GET.get('project')
    type_value = request.GET.get('type')
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
    ledger_entries = LedgerRestEntry.objects.filter(type=type_value)

    if is_valid(project_id):
        ledger_entries = ledger_entries.filter(project_name_id=project_id)

    if is_valid(head_id):
        ledger_entries = ledger_entries.filter(head_id=head_id)

    if is_valid(entity_id):
        if type_value == 'Vendor':
            ledger_entries = ledger_entries.filter(vendor_id=entity_id)
        elif type_value == 'Contractor':
            ledger_entries = ledger_entries.filter(capi_name_id=entity_id)
        elif type_value == 'Customer':
            ledger_entries = ledger_entries.filter(customer_name_id=entity_id)
        elif type_value == 'Bank':
            ledger_entries = ledger_entries.filter(bankName_id=entity_id)
        elif type_value == 'Expense':
            ledger_entries = ledger_entries.filter(exp_name_id=entity_id)
        elif type_value == 'Purchase':
            ledger_entries = ledger_entries.filter(purchase_id=entity_id)

    if transaction_option == 'datewise':
        if fd:
            ledger_entries = ledger_entries.filter(date__gte=fd)
        if td:
            ledger_entries = ledger_entries.filter(date__lte=td)

    ledger_entries = ledger_entries.order_by('date', 'id')

    # -------------------------
    # Prepare Ledger Data
    # -------------------------
    entry_data = []
    balance = Decimal('0.00')

    for entry in ledger_entries:

        if entry.type == 'Vendor' and entry.vendor:
            name = entry.vendor.rest_supplier_name

        elif entry.type == 'Contractor' and entry.contructor:
            name = entry.contructor.supervisor_name

        elif entry.type == 'Customer' and entry.customer_name:
            name = entry.customer_name.customer_name

        elif entry.type == 'Bank' and entry.bankName:
            name = entry.bankName.cash_type_name

        elif entry.type == 'Expense' and entry.exp_name:
            name = entry.exp_name.expense_name
        
        elif entry.type == 'Purchase' and entry.purchase:
            name = entry.purchase.pur_cost_name

        else:
            name = 'N/A'

        balance += entry.credit - entry.debit

        entry_data.append({
            'project_name': entry.project_name,
            'head': entry.head.head_name if entry.head else '',
            'name': name,
            'date': entry.date,
            'description': entry.description,
            'debit': entry.debit,
            'credit': entry.credit,
            'balance': balance,
        })

    return render(request, 'restaurant/reportmanage/ledger_report.html', {
        'entry_data': entry_data,
        'projectNames': ProjectFirstLevelName.objects.all(),
        'heads': RestHeadOfAccount.objects.all(),
        'vendors': RestaurantSupplier.objects.all(),
        'supervisors': SiteSupervisor.objects.all(),
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
    
    
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime

@login_required
def rest_ledger_manage_pdf(request):

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

    # -------------------------
    # Ledger Filter
    # -------------------------
    ledger_entries = LedgerRestEntry.objects.filter(type=type_value)

    if is_valid(project_id):
        ledger_entries = ledger_entries.filter(project_name_id=project_id)

    if is_valid(head_id):
        ledger_entries = ledger_entries.filter(head_id=head_id)

    if is_valid(entity_id):

        if type_value == 'Vendor':
            ledger_entries = ledger_entries.filter(vendor_id=entity_id)

        elif type_value == 'Contractor':
            ledger_entries = ledger_entries.filter(contructor_id=entity_id)

        elif type_value == 'Customer':
            ledger_entries = ledger_entries.filter(customer_name_id=entity_id)

        elif type_value == 'Bank':
            ledger_entries = ledger_entries.filter(bankName_id=entity_id)

        elif type_value == 'Expense':
            ledger_entries = ledger_entries.filter(exp_name_id=entity_id)
        
        elif type_value == 'Purchase':
            ledger_entries = ledger_entries.filter(purchase_id=entity_id)

    if transaction_option == 'datewise':
        if fd:
            ledger_entries = ledger_entries.filter(date__gte=fd)
        if td:
            ledger_entries = ledger_entries.filter(date__lte=td)

    ledger_entries = ledger_entries.order_by('date', 'id')

    # -------------------------
    # Prepare Raw Entries
    # -------------------------
    raw_entries = []

    for entry in ledger_entries:

        if entry.type == 'Vendor' and entry.vendor:
            name = entry.vendor.rest_supplier_name

        elif entry.type == 'Contractor' and entry.contructor:
            name = entry.contructor.supervisor_name

        elif entry.type == 'Customer' and entry.customer_name:
            name = entry.customer_name.customer_name

        elif entry.type == 'Bank' and entry.bankName:
            name = entry.bankName.cash_type_name

        elif entry.type == 'Expense' and entry.exp_name:
            name = entry.exp_name.expense_name
        
        elif entry.type == 'Purchase' and entry.purchase:
            name = entry.purchase.pur_cost_name

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

    # -------------------------
    # Sort Entries
    # -------------------------
    raw_entries.sort(key=lambda x: (x['date'] or datetime.min.date()))

    # -------------------------
    # Balance Calculation
    # -------------------------
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

    # -------------------------
    # Render Template
    # -------------------------
    return render(request, 'restaurant/reportmanage/ledger_report_print.html', {

        'entry_data': entry_data,
        'total_payment': total_payment,
        'total_received': total_received,
        'final_balance': balance,
        'print_time': datetime.now(),

        'projectNames': ProjectFirstLevelName.objects.all(),
        'heads': RestHeadOfAccount.objects.all(),
        'vendors': RestaurantSupplier.objects.all(),
        'supervisors': SiteSupervisor.objects.all(),
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
    
    
    
## -- cheque book manage ---
@login_required
def rest_main_cheque_book_list(request):
    # Add ChequeBook
    if request.method == 'POST':
        form = RestMainChequeBookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rest_main_cheque_book_list')
    else:
        form = RestMainChequeBookForm()

    books = RestMainChequeBook.objects.all().order_by('-id')
    return render(request, 'restaurant/cheques/main_cheque_book_list.html', {'form': form, 'books': books})
    
    
    
@login_required
def rest_main_cheque_list(request, book_id):
    book = get_object_or_404(RestMainChequeBook, id=book_id)
    #cheques = book.cheques.all().order_by('cheque_number')
    cheques = book.cheques.annotate(
        cheque_num_int=Cast('cheque_number', IntegerField())
    ).order_by('cheque_num_int')

    # Optional: Add new cheque manually
    if request.method == 'POST':
        form = RestMainChequeForm(request.POST)
        if form.is_valid():
            cheque = form.save(commit=False)
            cheque.cheque_book = book
            cheque.save()
            return redirect('main_cheque_list', book_id=book.id)
    else:
        form = RestMainChequeForm(initial={'cheque_book': book})

    return render(request, 'restaurant/cheques/main_cheque_list.html', {
        'book': book,
        'cheques': cheques,
        'form': form,
    })



from django.utils import timezone
@login_required
def rest_cheque_book_print(request, book_id):
    book = get_object_or_404(RestMainChequeBook, id=book_id)
    cheques = book.cheques.all()  # adjust related_name if different

    context = {
        "book": book,
        "cheques": cheques,
        "print_time": timezone.now(),
    }
    return render(request, "restaurant/cheques/cheque_book_print.html", context)
    
    
@login_required
def rest_main_edit_book(request, pk):
    book = get_object_or_404(RestMainChequeBook, pk=pk)
    if request.method == 'POST':
        form = RestMainChequeBookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('rest_main_cheque_book_list')
    else:
        form = RestMainChequeBookForm(instance=book)
    return render(request, 'restaurant/cheques/main_edit_book.html', {'form': form})
    
    
@login_required
def rest_main_delete_book(request, pk):
    book = get_object_or_404(RestMainChequeBook, pk=pk)
    book.delete()
    return redirect('rest_main_cheque_book_list')



@login_required
def rest_main_edit_cheque(request, pk):
    cheque = get_object_or_404(RestMainCheque, pk=pk)
    if request.method == 'POST':
        form = RestMainChequeForm(request.POST, instance=cheque)
        if form.is_valid():
            form.save()
            return redirect('rest_main_cheque_book_list', book_id=cheque.cheque_book.id)
    else:
        form = RestMainChequeForm(instance=cheque)
    return render(request, 'restaurant/cheques/main_edit_cheque.html', {'form': form})




@login_required
def rest_main_delete_cheque(request, pk):
    cheque = get_object_or_404(RestMainCheque, pk=pk)
    book_id = cheque.cheque_book.id
    cheque.delete()
    return redirect('rest_main_cheque_book_list', book_id=book_id)
    
    


@login_required
def rest_capital_account_list(request):
    accounts = CapitalRestAccount.objects.select_related('head_of_account')
    return render(request, 'restaurant/capital_accounts/account_head_list.html', {'accounts': accounts})
    

@login_required
def rest_capital_account_add(request):
    if request.method == 'POST':
        form = CapitalRestAccountForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('rest_capital_account_list')
    else:
        form = CapitalRestAccountForm()
    return render(request, 'restaurant/capital_accounts/account_head_form.html', {'form': form, 'title': 'Add Capital Account'})
    

@login_required
def rest_capital_account_edit(request, pk):
    account = get_object_or_404(CapitalRestAccount, pk=pk)
    if request.method == 'POST':
        form = CapitalRestAccountForm(request.POST, request.FILES, instance=account)
        if form.is_valid():
            form.save()
            return redirect('rest_capital_account_list')
    else:
        form = CapitalRestAccountForm(instance=account)
    return render(request, 'restaurant/capital_accounts/account_head_form.html', {'form': form, 'title': 'Edit Capital Account'})
    
    

@login_required
def rest_capital_account_delete(request, pk):
    account = get_object_or_404(CapitalRestAccount, pk=pk)
    # Error probably occurs here
    log_deleted_data(account, request.user)
    account.delete()
    return redirect('rest_capital_account_list')
    
