# erp_api/views.py
from rest_framework import viewsets, permissions, status, serializers,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from decimal import Decimal,ROUND_HALF_UP
import math 
import datetime as dt_module
from django.db.models import Min
from datetime import datetime, time
from rest_framework.permissions import AllowAny
from purchase.models import Requisition,Notification
from inventories.models import Inventories
from tenant.models import Room,Bill,Rent,ReceiveVoucher,PaymentVoucher
from .serializers import RequisitionSerializer,NotificationSerializer,InventoriesSerializer,InventoryStockSummarySerializer,InventoryStockSummaryCheckSerializer,ProjectSerializer,TransactionLedgerSerializer,CustomerSerializer,RoomSerializer,BillSerializer,RentSerializer,ReceiveVoucherSerializer,PaymentVoucherSerializer,LedgerEntryCustomSerializer,LedgerEntryCustomTrailSerializer, TrialBalanceTotalsSerializer,HeadOfAccountSerializer,CashTypeSerializer,ProjectFirstLevelNameSerializer,SuppliersSerializer,SiteSupervisorSerializer
from django.db.models import Sum, F, OuterRef, Subquery, IntegerField, ExpressionWrapper
import time
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from accounting.models import DebitVoucher,CreditVoucher,LedgerEntry,TransactionHistory,CashType,HeadOfAccount
from tenant.models import LedgerEntry as TenantLedgerEntry
from projects.models import ProjectFirstLevelName,Suppliers,BOQ,SiteSupervisor
from crm.models import Customer
from hrm.models import Employee
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    DebitVoucherSerializer,
    CreditVoucherSerializer,
    DebitVoucherUpdateSerializer,
    LedgerEntrySerializer,
    CombinedLedgerSerializer,
)

import re
from django.db import transaction
import datetime
from django.utils.dateparse import parse_date
from django.db.models import DateTimeField, DateField


class CreditVoucherViewSet(viewsets.ModelViewSet):
    queryset = CreditVoucher.objects.filter(
        Q(approval_cr_status=False) | Q(approval_cr_status__isnull=True)
    ).order_by("-id")
    serializer_class = CreditVoucherSerializer
    permission_classes = [permissions.IsAuthenticated]

    # --- List with filters + pagination ---
    def list(self, request, *args, **kwargs):
        vouchers = self.get_queryset()

        # --- Filters ---
        voucher_type = request.GET.get("voucher_type")
        project_id = request.GET.get("project_id")
        customer_id = request.GET.get("customer_id")
        confirmed = request.GET.get("confirmed")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if voucher_type:
            vouchers = vouchers.filter(type=voucher_type)
        if project_id:
            vouchers = vouchers.filter(project_name_id=project_id)
        if customer_id:
            vouchers = vouchers.filter(customer_name_id=customer_id)
        if confirmed is not None:
            vouchers = vouchers.filter(is_confirmed=(confirmed.lower() == "true"))
        if date_from and date_to:
            vouchers = vouchers.filter(date__range=[date_from, date_to])

        # --- Pagination ---
        paginator = Paginator(vouchers, 10)  # 10 per page
        page_number = request.GET.get("page")
        vouchers_page = paginator.get_page(page_number)

        serializer = self.serializer_class(vouchers_page, many=True)

        return Response({
            "vouchers": serializer.data,
            "pagination": {
                "page": vouchers_page.number,
                "pages": paginator.num_pages,
                "has_next": vouchers_page.has_next(),
                "has_previous": vouchers_page.has_previous(),
            }
        })

    # --- Approve credit voucher ---
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        with transaction.atomic():
            voucher = get_object_or_404(CreditVoucher.objects.select_for_update(), pk=pk)

            if voucher.approval_cr_status:
                return Response(
                    {"message": "Voucher already approved"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # --- Generate MR/Bill No if missing ---
            if not voucher.mr_or_bill_no:
                base_code = "MBC-"
                last_code = (
                    CreditVoucher.objects
                    .filter(mr_or_bill_no__startswith=base_code)
                    .order_by("-id")
                    .values_list("mr_or_bill_no", flat=True)
                    .first()
                )
                next_seq = 1
                if last_code:
                    m = re.search(rf'^{re.escape(base_code)}(\d+)$', last_code)
                    if m:
                        try:
                            next_seq = int(m.group(1)) + 1
                        except ValueError:
                            next_seq = 1

                generated_code = f"{base_code}{next_seq:05d}"
                while CreditVoucher.objects.filter(mr_or_bill_no=generated_code).exists():
                    next_seq += 1
                    generated_code = f"{base_code}{next_seq:05d}"

                voucher.mr_or_bill_no = generated_code

            # --- Approve voucher ---
            voucher.approval_cr_status = True
            voucher.is_confirmed = True
            voucher.save()

            # --- Update cash type balance ---
            if voucher.cash_type:
                ct = voucher.cash_type
                current = ct.type_amount or Decimal("0")
                add_amt = voucher.amount or Decimal("0")
                ct.type_amount = current + add_amt
                ct.type_note = f"Update Received Amount of voucher ID {voucher.id}"
                ct.save()

            # --- LedgerEntry ---
            LedgerEntry.objects.create(
                project_name=voucher.project_name,
                type=voucher.type,
                vendor=getattr(voucher, "vendor", None),
                customer_name=getattr(voucher, "customer_name", None),
                capi_name=getattr(voucher, "capi_name", None),
                cash_type=voucher.cash_type,
                cheque_number=voucher.cheque_number,
                head=voucher.head_of_account,
                mr_or_bill_no=voucher.mr_or_bill_no,
                date=voucher.date,
                description=voucher.particulars,
                debit=Decimal("0.00"),
                credit=voucher.amount,
                loan_status="received",
                tbl_id=voucher.id,
                tbl_name="Received",
            )

            # --- Response ---
            serializer = self.serializer_class(voucher, context={"request": request})
            return Response({
                "message": "Credit Voucher approved successfully",
                "approved": True
            }, status=status.HTTP_200_OK)




class DebitVoucherViewSet(viewsets.ModelViewSet):
    queryset = DebitVoucher.objects.filter(
        Q(approval_dr_status=None) | Q(approval_dr_status__isnull=True)
    ).order_by("-id")
    serializer_class = DebitVoucherSerializer
    permission_classes = [permissions.IsAuthenticated]

    # --- List with filters + pagination ---
    def list(self, request, *args, **kwargs):
        vouchers = self.get_queryset()

        # --- Filters ---
        voucher_type = request.GET.get("voucher_type")
        project_id = request.GET.get("project_id")
        customer_id = request.GET.get("customer_id")
        confirmed = request.GET.get("confirmed")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if voucher_type:
            vouchers = vouchers.filter(type=voucher_type)
        if project_id:
            vouchers = vouchers.filter(project_name_id=project_id)
        if customer_id:
            vouchers = vouchers.filter(customer_name_id=customer_id)
        if confirmed is not None:
            vouchers = vouchers.filter(is_confirmed=(confirmed.lower() == "true"))
        if date_from and date_to:
            vouchers = vouchers.filter(date__range=[date_from, date_to])

        # --- Pagination ---
        paginator = Paginator(vouchers, 10)  # 10 per page
        page_number = request.GET.get("page")
        vouchers_page = paginator.get_page(page_number)

        serializer = self.serializer_class(vouchers_page, many=True)

        return Response({
            "vouchers": serializer.data,
            "pagination": {
                "page": vouchers_page.number,
                "pages": paginator.num_pages,
                "has_next": vouchers_page.has_next(),
                "has_previous": vouchers_page.has_previous(),
            }
        })

    # --- Approve debit voucher ---
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        try:
            with transaction.atomic():
                # Lock voucher row to prevent race conditions
                voucher = get_object_or_404(DebitVoucher.objects.select_for_update(), pk=pk)

                if voucher.approval_dr_status:
                    return Response(
                        {"message": "Voucher already approved"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # --- Generate MR/Bill No if missing ---
                if not voucher.mr_or_bill_no:
                    base_code = "MBD-"
                    last_code = (
                        DebitVoucher.objects
                        .filter(mr_or_bill_no__startswith=base_code)
                        .order_by("-id")
                        .values_list("mr_or_bill_no", flat=True)
                        .first()
                    )
                    next_seq = 1
                    if last_code:
                        m = re.search(rf'^{re.escape(base_code)}(\d+)$', last_code)
                        if m:
                            try:
                                next_seq = int(m.group(1)) + 1
                            except ValueError:
                                next_seq = 1

                    generated_code = f"{base_code}{next_seq:05d}"

                    # --- Ensure uniqueness across both tables ---
                    while (
                        DebitVoucher.objects.filter(mr_or_bill_no=generated_code).exists() or
                        LedgerEntry.objects.filter(mr_or_bill_no=generated_code).exists()
                    ):
                        next_seq += 1
                        generated_code = f"{base_code}{next_seq:05d}"

                    voucher.mr_or_bill_no = generated_code

                # --- Approve voucher ---
                voucher.approval_dr_status = True
                voucher.is_confirmed = True
                voucher.save()

                # --- Update cash type balance ---
                if voucher.cash_type:
                    ct = voucher.cash_type
                    current = Decimal(ct.type_amount or 0)
                    deduct = Decimal(voucher.amount or 0)
                    ct.type_amount = current - deduct
                    ct.type_note = f"Update Paid Amount of voucher ID {voucher.id}"
                    ct.save()

                # --- Determine type_name for TransactionHistory ---
                type_name = None
                if voucher.type == "Vendor" and getattr(voucher, "vendor", None):
                    type_name = getattr(voucher.vendor, "supplier_name", None)
                elif voucher.type == "Contructor" and getattr(voucher, "contructor", None):
                    type_name = getattr(voucher.contructor, "supervisor_name", None)
                elif voucher.type == "Employee" and getattr(voucher, "empl_name", None):
                    type_name = voucher.empl_name
                elif voucher.type == "Capital" and getattr(voucher, "capi_name", None):
                    type_name = voucher.capi_name
                elif voucher.type == "Investment" and getattr(voucher, "invest_name", None):
                    type_name = voucher.invest_name
                elif voucher.type == "Expense" and getattr(voucher, "expense", None):
                    type_name = voucher.expense

                # --- Create TransactionHistory ---
                TransactionHistory.objects.create(
                    project=voucher.project_name,
                    transaction_type=voucher.type,
                    head_of_account=voucher.head_of_account,
                    cash_type=voucher.cash_type,
                    amount=Decimal(voucher.amount or 0),
                    date=voucher.date,
                    type_name=type_name,
                    reference=voucher.mr_or_bill_no,
                    create_by=voucher.create_dr,
                    particulars=voucher.particulars,
                )

                # --- Create LedgerEntry ---
                LedgerEntry.objects.create(
                    project_name=voucher.project_name,
                    type=voucher.type,
                    vendor=getattr(voucher, "vendor", None),
                    contructor=getattr(voucher, "contructor", None),
                    customer_name=getattr(voucher, "empl_name", None),
                    capi_name=getattr(voucher, "capi_name", None),
                    cash_type=voucher.cash_type,
                    cheque_number=voucher.cheque_number,
                    head=voucher.head_of_account,
                    mr_or_bill_no=voucher.mr_or_bill_no,
                    date=voucher.date,
                    description=voucher.particulars,
                    debit=Decimal(voucher.amount or 0),
                    credit=Decimal("0.00"),
                    loan_status="paid",
                    tbl_id=voucher.id,
                    tbl_name="Paid",
                )

                return Response({
                    "message": "Debit Voucher approved successfully",
                    "approved": True
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Failed to approve voucher",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class RequisitionViewSet(viewsets.ModelViewSet):
    serializer_class = RequisitionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Default queryset → only show pending requisitions.
        """
        return Requisition.objects.filter(approv_status__iexact='pending').order_by('-id')

    def list(self, request, *args, **kwargs):
        """
        List all pending requisitions.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """
        View requisition details by ID.
        """
        instance = get_object_or_404(Requisition, pk=kwargs.get("pk"))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ✅ NEW API for dropdown list of projects
    @action(detail=False, methods=['get'], url_path='projects')
    def projects(self, request):
        """
        Return unique project names with pending requisitions.
        """
        projects = ProjectFirstLevelName.objects.filter(
            requisition__approv_status__iexact="pending"
        ).distinct()

        project_list = [
            {"id": proj.id, "name": proj.project_first_name}
            for proj in projects
        ]
        return Response({"projects": project_list})

    # ✅ NEW API for project-wise pending requisitions
    @action(detail=False, methods=['get'], url_path='project-requisitions/(?P<project_id>[^/.]+)')
    def project_requisitions(self, request, project_id=None):
        """
        Return all pending requisitions for a given project.
        """
        queryset = self.get_queryset().filter(project_name_id=project_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})

    # === Approve Action ===
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        requisition = get_object_or_404(Requisition, pk=pk)

        if requisition.approv_status.lower() != "pending":
            return Response(
                {"error": "This requisition is already processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        requisition.approv_status = "approved"
        requisition.requi_uniq_id = int(time.time())  # unique ID
        requisition.save()

        return Response({
            "message": "Requisition approved successfully.",
            "id": requisition.id,
            "requi_uniq_id": requisition.requi_uniq_id,
            "status": requisition.approv_status
        })

    # === Reject Action ===
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        requisition = get_object_or_404(Requisition, pk=pk)

        if requisition.approv_status.lower() != "pending":
            return Response(
                {"error": "This requisition is already processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        requisition.approv_status = "rejected"
        requisition.save()

        return Response({
            "message": "Requisition rejected successfully.",
            "id": requisition.id,
            "status": requisition.approv_status
        })
        
    
    
    # ============================================================
    # ✅ CREATE / UPDATE REQUISITION (MULTIPLE ITEMS) — ACCEPT QUERY PARAMS OR JSON BODY
    # ============================================================
    @action(detail=False, methods=['post', 'put'], url_path='create')
    def create_requisition(self, request):
        """
        Create or update requisitions.
        Accepts JSON body with 'data' array (recommended).
        """
        try:
            data = request.data

            # Extract main fields
            employee_id = data.get("employee_id")
            project_id = data.get("project_id")
            req_type = data.get("type")
            remark_text = data.get("remark")

            if not employee_id or not project_id or not req_type:
                return Response(
                    {"status": "error", "message": "Missing required fields: employee_id, project_id, or type."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            employee_ids = 17
            project = get_object_or_404(ProjectFirstLevelName, pk=project_id)
            employee = get_object_or_404(Employee, pk=employee_ids)

            saved_requisitions = []
            new_requisition_ids = []

            # Get items
            items = data.get("data")
            if not items or not isinstance(items, list):
                return Response(
                    {"status": "error", "message": "Missing or invalid 'data' array."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for item in items:
                # Validate required fields
                required_fields = ["item_name", "vendor_name", "unit", "qty", "rate"]
                for field in required_fields:
                    if item.get(field) in [None, ""]:
                        return Response(
                            {"status": "error", "message": f"Missing required field: {field}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # Convert numeric fields
                try:
                    qty = Decimal(str(item.get("qty"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    rate = Decimal(str(item.get("rate"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    discount = Decimal(str(item.get("discount", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                except Exception as e:
                    return Response(
                        {"status": "error", "message": f"Invalid numeric value: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                amount = (qty * rate - discount).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                requisition_date = timezone.now().date()  # match DateField

                requisition_data = {
                    "project_name": project.id,
                    "employee_name": employee.id,
                    "item_name": item.get("item_name"),
                    "type": req_type,
                    "vendor_name": item.get("vendor_name"),
                    "unit": item.get("unit"),
                    "qty": qty,
                    "rate": rate,
                    "discount": discount,
                    "amount": amount,
                    "remark": remark_text,
                    "requisition_date": requisition_date,
                }

                # Update if id exists, else create
                req_id = item.get("id")
                if req_id:
                    instance = get_object_or_404(Requisition, pk=req_id)
                    serializer = RequisitionSerializer(instance, data=requisition_data)
                else:
                    serializer = RequisitionSerializer(data=requisition_data)

                if serializer.is_valid():
                    saved_obj = serializer.save()
                    saved_requisitions.append(saved_obj)
                    if not req_id:
                        new_requisition_ids.append(saved_obj.id)
                else:
                    return Response(
                        {"status": "error", "message": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Send notifications only for new requisitions
            if new_requisition_ids:
                sender_user = request.user
                admin_users = User.objects.filter(groups__name__iexact="admin")
                for admin in admin_users:
                    Notification.objects.create(
                        sender=sender_user,
                        recipient=admin,
                        project_name=project,
                        message=f"New requisition submitted by {employee} for project {project.project_first_name}.",
                        is_read=False,
                        link="",
                        pass_url="requisition_admin_confirm",
                        role="admin",
                        created_at=timezone.now(),
                    )

            return Response(
                {
                    "status": "success",
                    "message": "Requisition(s) created successfully.",
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    


# class InventoriesViewSet(viewsets.ModelViewSet):
#     queryset = Inventories.objects.all().order_by('-id')
#     serializer_class = InventoriesSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response({"data": serializer.data})

#     @action(detail=False, methods=['get'], url_path='stock-summary')
#     def stock_summary(self, request):
#         summary = (
#             Inventories.objects
#             .values('item_name__id', 'item_name__head_requi_name')
#             .annotate(total_qty=Sum('qty'), total_qtysub=Sum('qtysub'))
#             .order_by('item_name__head_requi_name')
#         )
#         serializer = InventoryStockSummarySerializer(summary, many=True)
#         return Response({"data": serializer.data})

#     @action(detail=False, methods=['get'], url_path='stock-summary-check')
#     def stock_summary_check(self, request):
#         project_id = request.GET.get('project_id')
#         item_id = request.GET.get('item_id')

#         if not project_id or not project_id.isdigit():
#             return Response({"error": "Invalid or missing project_id."}, status=400)

#         project = ProjectFirstLevelName.objects.filter(id=int(project_id)).first()
#         if not project:
#             return Response({"error": "Project not found."}, status=404)

#         queryset = Inventories.objects.filter(project_name=project)
#         if item_id and item_id.isdigit():
#             queryset = queryset.filter(item_name_id=int(item_id))

#         last_purchase_subquery = Inventories.objects.filter(
#             project_name=project,
#             item_name=OuterRef('item_name')
#         ).order_by('-purch_date').values('qty')[:1]

#         last_remark_subquery = Inventories.objects.filter(
#             project_name=project,
#             item_name=OuterRef('item_name')
#         ).order_by('-purch_date').values('remark')[:1]

#         inventory_data = (
#             queryset
#             .values('item_name', 'item_name__head_requi_name', 'employee_name__emp_name', 'vendor_name__supplier_name')
#             .annotate(
#                 total_qty=Sum('qty'),
#                 available_qty=Sum('qtysub'),
#                 last_purchase_qty=Subquery(last_purchase_subquery, output_field=IntegerField()),
#                 last_remark=Subquery(last_remark_subquery),
#             )
#             .annotate(
#                 use_qty=ExpressionWrapper(
#                     F('total_qty') - F('available_qty'),
#                     output_field=IntegerField()
#                 )
#             )
#             .order_by('item_name__head_requi_name')
#         )

#         serializer = InventoryStockSummaryCheckSerializer(inventory_data, many=True)
#         return Response({
#             "project": {"id": project.id, "name": project.project_first_name},
#             "data": serializer.data
#         })
    




class InventoriesViewSet(viewsets.ModelViewSet):
    queryset = Inventories.objects.all().order_by('-id')
    serializer_class = InventoriesSerializer
    permission_classes = [permissions.IsAuthenticated]

    
    def list(self, request, *args, **kwargs):
        # pick one inventory row per project
        queryset = Inventories.objects.filter(
            id__in=Inventories.objects
                .values('project_name_id')
                .annotate(min_id=Min('id'))
                .values('min_id')
        ).select_related('project_name')
    
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})


    @action(detail=False, methods=['get'], url_path='stock-summary')
    def stock_summary(self, request):
        summary = (
            Inventories.objects
            .values('item_name__id', 'item_name__head_requi_name')
            .annotate(total_qty=Sum('qty'), total_qtysub=Sum('qtysub'))
            .order_by('item_name__head_requi_name')
        )
        serializer = InventoryStockSummarySerializer(summary, many=True)
        return Response({"data": serializer.data})

    @action(detail=False, methods=['get'], url_path='stock-summary-check')
    def stock_summary_check(self, request):
        project_id = request.GET.get('project_id')
        item_id = request.GET.get('item_id')

        if not project_id or not project_id.isdigit():
            return Response({"error": "Invalid or missing project_id."}, status=400)

        project = ProjectFirstLevelName.objects.filter(id=int(project_id)).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)

        queryset = Inventories.objects.filter(project_name=project)
        if item_id and item_id.isdigit():
            queryset = queryset.filter(item_name_id=int(item_id))

        last_purchase_subquery = Inventories.objects.filter(
            project_name=project,
            item_name=OuterRef('item_name')
        ).order_by('-purch_date').values('qty')[:1]

        last_remark_subquery = Inventories.objects.filter(
            project_name=project,
            item_name=OuterRef('item_name')
        ).order_by('-purch_date').values('remark')[:1]

        inventory_data = (
            queryset
            .values('item_name', 'item_name__head_requi_name', 'employee_name__emp_name', 'vendor_name__supplier_name')
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

        serializer = InventoryStockSummaryCheckSerializer(inventory_data, many=True)
        return Response({
            "project": {"id": project.id, "name": project.project_first_name},
            "data": serializer.data
        })




## general ledger --- ok code...
class LedgerEntryPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LedgerEntryPagination
    serializer_class = None  # Using custom serializer method

    def get_queryset(self):
        qs = LedgerEntry.objects.all().order_by('date', 'id')

        project = self.request.query_params.get('project')
        head = self.request.query_params.get('head')
        type_filter = self.request.query_params.get('type')
        cash_type = self.request.query_params.get('cash_type')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if project:
            qs = qs.filter(project_name_id=project)
        if head:
            qs = qs.filter(head_id=head)
        if type_filter:
            qs = qs.filter(type=type_filter)
        if cash_type:
            qs = qs.filter(cash_type=cash_type)
        if from_date:
            qs = qs.filter(date__gte=parse_date(from_date))
        if to_date:
            qs = qs.filter(date__lte=parse_date(to_date))

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = self.serialize_ledger(page)
            return Response({
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "data": data
            })

        # No pagination case
        data = self.serialize_ledger(queryset)
        return Response({
            "count": len(data),
            "next": None,
            "previous": None,
            "data": data
        })

    def serialize_ledger(self, queryset):
        data = []
        for entry in queryset:
            # Determine cash_type/vendor_name/etc.
            if entry.type == 'Vendor' and entry.vendor:
                name = entry.vendor.supplier_name
            elif entry.type == 'Contructor' and entry.contructor:
                name = entry.contructor.supervisor_name
            elif entry.type == 'Capital' and entry.capi_name:
                name = entry.capi_name.person_name
            elif entry.type == 'Customer' and entry.customer_name:
                name = entry.customer_name.customer_name
            elif entry.type == 'cash_type' and entry.bankName:
                name = entry.bankName.cash_type_name
            elif entry.type == 'Expense' and entry.exp_name:
                name = entry.exp_name.head_exp_name
            
            elif entry.cash_type == 'cash_type' and entry.cash_type:
                name = entry.cash_type.cash_type_name
            else:
                name = 'N/A'

            # Safely parse decimal fields
            try:
                debit = Decimal(entry.debit or 0)
            except:
                debit = Decimal(0)

            try:
                credit = Decimal(entry.credit or 0)
            except:
                credit = Decimal(0)

            try:
                balance = Decimal(entry.balance or 0)
            except:
                balance = Decimal(0)

            data.append({
                "id": entry.id,
                "project": entry.project_name.project_first_name if entry.project_name else "",
                "transaction_type": entry.type or "",
                "vendor": entry.vendor.supplier_name if entry.vendor else "",
                "contractor": entry.contructor.supervisor_name if entry.contructor else "",
                "head": entry.head.head_name if entry.head else "",
                "cash_type": entry.cash_type.cash_type_name if entry.cash_type else "",
                "date": entry.date.strftime("%Y-%m-%d") if entry.date else "",
                "reference": getattr(entry, 'reference', ''),
                "debit": f"{debit:.2f}",
                "credit": f"{credit:.2f}",
                "balance": f"{balance:.2f}",
            })
        return data




# from datetime import datetime, time
# class LedgerEntryPagination(PageNumberPagination):
#     page_size = 25
#     page_size_query_param = 'page_size'


# class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
#     serializer_class = LedgerEntrySerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = LedgerEntryPagination

#     # ---------------- HELPER FUNCTION ----------------
#     def parse_date(self, date_str):
#         """
#         Parse date safely.
#         Accepts YYYY-MM-DD or YY-MM-DD.
#         Returns a date object or None.
#         """
#         if not date_str:
#             return None
#         date_str = date_str.strip()
#         for fmt in ("%Y-%m-%d", "%y-%m-%d"):
#             try:
#                 return datetime.strptime(date_str, fmt).date()
#             except ValueError:
#                 continue
#         return None

#     # ---------------- QUERYSET ----------------
#     def get_queryset(self):
#         qs = LedgerEntry.objects.all().order_by("date", "id")

#         project = self.request.query_params.get("project")
#         head = self.request.query_params.get("head")
#         type_filter = self.request.query_params.get("type")
#         from_date = self.parse_date(self.request.query_params.get("from_date"))
#         to_date = self.parse_date(self.request.query_params.get("to_date"))

#         if project:
#             qs = qs.filter(project_name_id=project)
#         if head:
#             qs = qs.filter(head_id=head)
#         if type_filter:
#             qs = qs.filter(type=type_filter)

#         # Swap dates if from_date > to_date
#         if from_date and to_date and from_date > to_date:
#             from_date, to_date = to_date, from_date

#         # Detect if date field is DateTimeField
#         date_field = qs.model._meta.get_field("date")
#         is_datetime = isinstance(date_field, DateTimeField)

#         # Apply open-ended filters
#         if from_date:
#             if is_datetime:
#                 qs = qs.filter(date__gte=datetime.combine(from_date, time.min))
#             else:
#                 qs = qs.filter(date__gte=from_date)
#         if to_date:
#             if is_datetime:
#                 qs = qs.filter(date__lte=datetime.combine(to_date, time.max))
#             else:
#                 qs = qs.filter(date__lte=to_date)

#         return qs

#     # ---------------- SERIALIZE LEDGER ----------------
#     def serialize_ledger(self, queryset):
#         data = []
#         for entry in queryset:
#             # Determine vendor/party name
#             if entry.type == "Vendor" and entry.vendor:
#                 name = entry.vendor.supplier_name
#             elif entry.type == "Contructor" and entry.contructor:
#                 name = entry.contructor.supervisor_name
#             elif entry.type == "Capital" and entry.capi_name:
#                 name = entry.capi_name.person_name
#             elif entry.type == "Customer" and entry.customer_name:
#                 name = entry.customer_name.customer_name
#             elif entry.type == "Bank" and entry.bankName:
#                 name = entry.bankName.cash_type_name
#             elif entry.type == "Expense" and entry.exp_name:
#                 name = entry.exp_name.head_exp_name
#             else:
#                 name = "N/A"

#             debit = Decimal(entry.debit or 0)
#             credit = Decimal(entry.credit or 0)
#             amount = debit if debit > 0 else credit

#             data.append({
#                 "id": entry.id,
#                 "purch_id": entry.id,
#                 "requisition_date": entry.date.strftime("%Y-%m-%d") if entry.date else "",
#                 "head_name": entry.head.head_name if entry.head else "",
#                 "project_name": entry.project_name.project_first_name if entry.project_name else "",
#                 "employee_name": entry.description or "",
#                 "amount": f"{amount:.2f}",
#                 "vendor_name": name,
#             })
#         return data

#     # ---------------- MAIN LIST ----------------
#     def list(self, request, *args, **kwargs):
#         try:
#             qs = self.filter_queryset(self.get_queryset())
#             if not qs.exists():
#                 return Response({
#                     "count": 0,
#                     "next": None,
#                     "previous": None,
#                     "data": []
#                 })

#             page = self.paginate_queryset(qs)
#             if page is not None:
#                 data = self.serialize_ledger(page)
#                 paginated = self.get_paginated_response(data).data
#                 return Response({
#                     "count": paginated.get("count"),
#                     "next": paginated.get("next"),
#                     "previous": paginated.get("previous"),
#                     "data": paginated.get("results")
#                 })

#             data = self.serialize_ledger(qs)
#             return Response({
#                 "count": len(data),
#                 "next": None,
#                 "previous": None,
#                 "data": data
#             })
#         except Exception as e:
#             return Response({
#                 "code": "500",
#                 "status": "Error",
#                 "messages": [{"message": f"Internal server error: {str(e)}"}]
#             }, status=500)
            
            
            
        


## Transection ledger ---
class TransactionLedgerPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'

from datetime import datetime
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class TransactionLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransactionHistory.objects.all()
    serializer_class = TransactionLedgerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionLedgerPagination

    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    def get_filtered_queryset(self):
        queryset = self.get_queryset()
        request = self.request

        project_id = request.query_params.get("project")
        head_id = request.query_params.get("head_value") or request.query_params.get("head")
        from_date = self.parse_date(request.query_params.get("from_date"))
        to_date = self.parse_date(request.query_params.get("to_date"))

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        if head_id:
            queryset = queryset.filter(head_of_account_id=head_id)

        # swap if user sends reversed range
        if from_date and to_date and from_date > to_date:
            from_date, to_date = to_date, from_date

        if from_date:
            queryset = queryset.filter(date__gte=from_date)

        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        return queryset.order_by("-id")

    def list(self, request, *args, **kwargs):
        queryset = self.get_filtered_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return Response({
                "count": paginated.data["count"],
                "next": paginated.data["next"],
                "previous": paginated.data["previous"],
                "data": paginated.data["results"],
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "next": None,
            "previous": None,
            "data": serializer.data,
        })




# class TransactionLedgerViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = TransactionHistory.objects.all()
#     serializer_class = TransactionLedgerSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = TransactionLedgerPagination

#     def parse_date(self, date_str):
#         if not date_str:
#             return None
#         try:
#             return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
#         except Exception:
#             return None

#     def filter_queryset(self, queryset):
#         try:
#             request = self.request
#             project_id = request.query_params.get("project")
#             head_id = request.query_params.get("head_value") or request.query_params.get("head")
#             from_date = self.parse_date(request.query_params.get("from_date"))
#             to_date = self.parse_date(request.query_params.get("to_date"))

#             if project_id:
#                 queryset = queryset.filter(project_id=project_id)
#             if head_id:
#                 queryset = queryset.filter(head_of_account_id=head_id)

#             if from_date and to_date and from_date > to_date:
#                 from_date, to_date = to_date, from_date

#             # Check field type
#             try:
#                 date_field = queryset.model._meta.get_field("date")
#                 is_datetime = isinstance(date_field, DateTimeField)
#             except Exception:
#                 # fallback if field not found
#                 is_datetime = False

#             if from_date:
#                 if is_datetime:
#                     queryset = queryset.filter(date__gte=datetime.combine(from_date, time.min))
#                 else:
#                     queryset = queryset.filter(date__gte=from_date)

#             if to_date:
#                 if is_datetime:
#                     queryset = queryset.filter(date__lte=datetime.combine(to_date, time.max))
#                 else:
#                     queryset = queryset.filter(date__lte=to_date)

#             return queryset.order_by("-id")
#         except Exception as e:
#             # Catch any unexpected errors in filtering
#             return queryset.none()

#     def list(self, request, *args, **kwargs):
#         try:
#             queryset = self.filter_queryset(self.get_queryset())
#             page = self.paginate_queryset(queryset)

#             if page is not None:
#                 serializer = self.get_serializer(page, many=True)
#                 paginated = self.get_paginated_response(serializer.data)
#                 return Response({
#                     "count": paginated.data.get("count"),
#                     "next": paginated.data.get("next"),
#                     "previous": paginated.data.get("previous"),
#                     "data": paginated.data.get("results")
#                 })

#             serializer = self.get_serializer(queryset, many=True)
#             return Response({
#                 "count": len(serializer.data),
#                 "next": None,
#                 "previous": None,
#                 "data": serializer.data
#             })
#         except Exception as e:
#             # Return error info for debugging
#             return Response({
#                 "code": "500",
#                 "status": "Error",
#                 "messages": [{"message": f"Internal server error: {str(e)}"}]
#             }, status=500)
        
        
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.all().order_by("-created_at")

        # Filter by role
        role = self.request.query_params.get("role")
        if role:
            role = role.lower()
            qs = qs.filter(role=role, recipient=user)
        else:
            qs = qs.filter(recipient=user)

        # Filter by is_read
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=(is_read.lower() in ["true", "1"]))

        return qs

    # Wrap list response in "data"
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})

    # Mark a single notification as read and return dynamic URL
    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        user = request.user
        try:
            notification = Notification.objects.get(
                pk=pk,
                is_read=False,               # Only unread notifications
                recipient=user,              # Only recipient can mark
                role__in=["admin", "accounts"]  # Only admin/accounts
            )
        except Notification.DoesNotExist:
            return Response(
                {"success": False, "message": "Notification cannot be marked as read."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark as read
        notification.is_read = True
        notification.save(update_fields=["is_read"])

        # Prepare dynamic redirect URL
        if notification.project_name:
            project_id = notification.project_name.id
            dynamic_url = f"/api/v1/requisitions/project-requisitions/{project_id}/"
        else:
            dynamic_url = "/"  # fallback

        return Response({
            "success": True,
            "id": notification.id,
            "redirect_url": dynamic_url
        })





class ProjectBOQViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # 1️⃣ List all projects
    def list(self, request):
        projects = ProjectFirstLevelName.objects.all().values("id", "project_first_name")
        return Response({"data": list(projects)})

    # 2️⃣ Project-wise BOQ list (pending or not approved)
    def retrieve(self, request, pk=None):
        project = get_object_or_404(ProjectFirstLevelName, pk=pk)
        boq_items = BOQ.objects.filter(project_name=project).exclude(status_item="Approved")
        serializer = BOQListSerializer(boq_items, many=True)

        return Response({
            "project": project.project_first_name,
            "data": serializer.data
        })

    # 3️⃣ Approve all BOQs for a project
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        project = get_object_or_404(ProjectFirstLevelName, pk=pk)
        updated_count = BOQ.objects.filter(project_name=project).exclude(status_item="Approved").update(status_item="Approved")
        return Response({
            "message": f"{updated_count} BOQ items approved for project {project.project_first_name}."
        }, status=status.HTTP_200_OK)
        
        
        
        
# class CustomerViewSet(viewsets.ModelViewSet):
#     queryset = Customer.objects.all().order_by('-id')
#     serializer_class = CustomerSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     filter_backends = [filters.SearchFilter]
#     search_fields = ['customer_name', 'profession', 'organization', 'contact_no', 'email', 'address']

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         serializer = self.get_serializer(queryset, many=True)
#         return Response({"data": serializer.data})





class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-id')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_name', 'profession', 'organization', 'contact_no', 'email', 'address']

    @action(detail=False, methods=['get'], url_path='search')
    def search_customers(self, request):
        name_query = request.GET.get('name', '').strip()
        queryset = self.queryset

        if name_query:
            queryset = queryset.filter(customer_name__icontains=name_query)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})
        
        


class RoomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'data': data
        })


class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all().select_related('project', 'client').order_by('-created_at')
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = RoomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'next': None,
            'previous': None,
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'count': 1,
            'next': None,
            'previous': None,
            'data': [serializer.data]
        })       




class ActiveRoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.filter(status='Active').select_related('project', 'client').order_by('-created_at')
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = RoomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'next': None,
            'previous': None,
            'data': serializer.data
        })




class DeactiveRoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.filter(status='Deactive').select_related('project', 'client').order_by('-created_at')
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = RoomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'next': None,
            'previous': None,
            'data': serializer.data
        })
        
        
        

class BillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bill.objects.all().order_by('-id')
    serializer_class = BillSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data": [serializer.data]})
        
        
        
        
class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.all().select_related('projectref', 'room', 'varatiya').order_by('-id')
    serializer_class = RentSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data": serializer.data})
        
        

class ReceiveVoucherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReceiveVoucher.objects.all().order_by('-id')
    serializer_class = ReceiveVoucherSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({"data": serializer.data})
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=500)
            
            
            
class PaymentVoucherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentVoucher.objects.all().order_by('-id')
    serializer_class = PaymentVoucherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        # Wrap inside "data" key
        return Response({"data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data": serializer.data})
        
        
        
        
class LedgerEntryCustomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'

class LedgerEntryCustomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TenantLedgerEntry.objects.select_related(
        'tenant', 'receive_voucher', 'payment_voucher'
    ).order_by('-date')
    serializer_class = LedgerEntryCustomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LedgerEntryCustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "data": serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})
        
        
        
        
## Trail Balance ---
# class LedgerEntryCustomtrailViewSet(viewsets.ViewSet):   
#     permission_classes = [AllowAny]

#     def list(self, request):
#         try:
#             start_date = request.query_params.get('start_date')
#             end_date = request.query_params.get('end_date')
#             project = request.query_params.get('project', '')
#             vendor = request.query_params.get('vendor', '')

#             # --- Safe date parsing ---
#             def parse_date(date_str):
#                 if not date_str:
#                     return None
#                 try:
#                     return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
#                 except Exception:
#                     return None

#             start = parse_date(start_date)
#             end = parse_date(end_date)

#             # --- Build filters ---
#             filters = Q()
#             if start:
#                 filters &= Q(date__gte=start)
#             if end:
#                 filters &= Q(date__lte=end)
#             if project:
#                 # ✅ use your actual project field name
#                 filters &= Q(project_name__project_first_name__icontains=project)
#             if vendor:
#                 filters &= (
#                     Q(vendor__supplier_name__icontains=vendor)
#                     | Q(customer_name__customer_name__icontains=vendor)
#                     | Q(contructor__supervisor_name__icontains=vendor)
#                     | Q(bankName__head_name__icontains=vendor)
#                 )

#             # --- Fetch ledger entries ---
#             entries = LedgerEntry.objects.filter(filters).order_by("date")

#             # --- Totals ---
#             total_debit = sum([float(e.debit or 0) for e in entries])
#             total_credit = sum([float(e.credit or 0) for e in entries])
#             total_balance = total_debit - total_credit

#             totals = {
#                 "debit": total_debit,
#                 "credit": total_credit,
#                 "balance": total_balance,
#             }

#             # --- Serialize ---
#             serializer = LedgerEntryCustomTrailSerializer(entries, many=True)
#             totals_serializer = TrialBalanceTotalsSerializer(totals)

#             return Response({                
#                 "data": serializer.data,
#                 "totals": totals_serializer.data,
#             })

#         except Exception as e:
#             import traceback
#             print(traceback.format_exc())  # ✅ show full traceback in console
#             return Response({"error": str(e)}, status=500)




# class LedgerEntryCustomtrailPagination(PageNumberPagination):
#     page_size = 20
#     page_size_query_param = 'page_size'
#     max_page_size = 1000

# class LedgerEntryCustomtrailViewSet(viewsets.ViewSet):
#     permission_classes = [permissions.AllowAny]
#     pagination_class = LedgerEntryCustomtrailPagination

#     def list(self, request):
#         try:
#             start_date = request.query_params.get('start_date')
#             end_date = request.query_params.get('end_date')
#             project = request.query_params.get('project', '')
#             vendor = request.query_params.get('vendor', '')

#             def parse_date(date_str):
#                 if not date_str:
#                     return None
#                 try:
#                     return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
#                 except:
#                     return None

#             start = parse_date(start_date)
#             end = parse_date(end_date)

#             filters = Q()
#             if start:
#                 filters &= Q(date__gte=start)
#             if end:
#                 filters &= Q(date__lte=end)
#             if project:
#                 filters &= Q(project_name__project_first_name__icontains=project)
#             if vendor:
#                 filters &= (
#                     Q(vendor__supplier_name__icontains=vendor)
#                     | Q(customer_name__customer_name__icontains=vendor)
#                     | Q(contructor__supervisor_name__icontains=vendor)
#                     | Q(bankName__head_name__icontains=vendor)
#                 )

#             entries = LedgerEntry.objects.filter(filters).order_by("date")

#             paginator = self.pagination_class()
#             page = paginator.paginate_queryset(entries, request)
#             serializer = LedgerEntryCustomTrailSerializer(page, many=True)

#             return paginator.get_paginated_response(serializer.data)

#         except Exception as e:
#             import traceback
#             print(traceback.format_exc())
#             return Response({"error": str(e)}, status=500)
            

## Trail Balance Ledger ----
class LedgerEntryCustomtrailPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'data': data  # <-- rename 'results' to 'data'
        })

# ViewSet
class LedgerEntryCustomtrailViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntryCustomTrailSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated
    pagination_class = LedgerEntryCustomtrailPagination

    def get_queryset(self):
        queryset = LedgerEntry.objects.all().order_by('date')

        # Filters from query params
        start_date = self.request.query_params.get('from_date')
        end_date = self.request.query_params.get('to_date')
        project = self.request.query_params.get('project')
        vendor = self.request.query_params.get('vendor')
        customer = self.request.query_params.get('customer')
        entry_type = self.request.query_params.get('type')

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        if project:
            queryset = queryset.filter(project_name__project_first_name__icontains=project)
        if vendor:
            queryset = queryset.filter(vendor__supplier_name__icontains=vendor)
        if customer:
            queryset = queryset.filter(customer_name__customer_name__icontains=customer)
        if entry_type:
            queryset = queryset.filter(type__iexact=entry_type)

        return queryset
        
        
        
        
        


## Head of Account ----
class HeadOfAccountViewSet(viewsets.ModelViewSet):
    queryset = HeadOfAccount.objects.all()
    serializer_class = HeadOfAccountSerializer
    permission_classes = [IsAuthenticated]

    # Override list method to wrap data
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})


## Cash Type---
class CashTypeViewSet(viewsets.ModelViewSet):
    queryset = CashType.objects.all()
    serializer_class = CashTypeSerializer
    permission_classes = [IsAuthenticated]  # Or AllowAny if public

    # Wrap list response in "data"
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})
        
        
        
## Project --
class ProjectFirstLevelNameViewSet(viewsets.ModelViewSet):
    queryset = ProjectFirstLevelName.objects.all()
    serializer_class = ProjectFirstLevelNameSerializer
    permission_classes = [IsAuthenticated]  # Or [AllowAny] if public

    # Custom "data" wrapper
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})
        
        

## Supplier --
class SuppliersViewSet(viewsets.ModelViewSet):
    queryset = Suppliers.objects.all().order_by('id')
    serializer_class = SuppliersSerializer
    permission_classes = [IsAuthenticated]  # Change to [AllowAny] if public API

    # Wrap list output with "data"
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})
        
        
## Contractor ----
class SiteSupervisorViewSet(viewsets.ModelViewSet):
    queryset = SiteSupervisor.objects.all().order_by('id')
    serializer_class = SiteSupervisorSerializer
    permission_classes = [IsAuthenticated]  # Or [AllowAny] if you want public access

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})