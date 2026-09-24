# erp_api/serializers.py
from rest_framework import serializers
from purchase.models import Requisition,Notification
from projects.models import ProjectFirstLevelName,BOQ,Suppliers,SiteSupervisor
from crm.models import Customer
from inventories.models import Inventories
from tenant.models import Room,Bill,Rent,ReceiveVoucher,PaymentVoucher
from accounting.models import DebitVoucher,CreditVoucher,LedgerEntry,TransactionHistory,HeadOfAccount,CashType
from tenant.models import LedgerEntry as TenantLedgerEntry
from decimal import Decimal
from datetime import datetime



class DebitVoucherSerializer(serializers.ModelSerializer):
    # ✅ Display related names instead of IDs
    project_name = serializers.CharField(source='project_name.project_first_name', read_only=True)
    contructor = serializers.CharField(source='contructor.supervisor_name', read_only=True)
    vendor = serializers.CharField(source='vendor.supplier_name', read_only=True)
    capi_name = serializers.CharField(source='capi_name.head_of_account', read_only=True)
    invest_name = serializers.CharField(source='invest_name.head_of_account', read_only=True)
    cash_type = serializers.CharField(source='cash_type.cash_type_name', read_only=True)
    head_of_account = serializers.CharField(source='head_of_account.head_of_account', read_only=True)

    is_confirmed = serializers.SerializerMethodField()
    approval_dr_status = serializers.SerializerMethodField()

    def get_is_confirmed(self, obj):
        return True  

    def get_approval_dr_status(self, obj):
        return False 

    class Meta:
        model = DebitVoucher
        fields = [
            "id",
            "type",
            "contructor",
            "vendor",
            "expense",
            "empl_name",
            "capi_name",
            "invest_name",
            "bill_phase",
            "bill_date",
            "project_name",
            "cash_type",
            "cheque_number",
            "head_of_account",
            "amount",
            "mr_or_bill_no",
            "date",
            "particulars",
            "is_confirmed",
            "approval_dr_status",
            "requi_id",
            "return_requisition",
            "carrier",
            "create_dr",
        ]

    # ✅ Replace all None/null values with ""
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key, value in data.items():
            if value is None:
                data[key] = ""
        return data


class DebitVoucherUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitVoucher
        fields = "__all__"




class CreditVoucherSerializer(serializers.ModelSerializer):
    # ✅ Display related names instead of IDs
    project_name = serializers.CharField(source="project_name.project_first_name", read_only=True)
    customer_name = serializers.CharField(source="customer_name.customer_name", read_only=True)
    lead_name = serializers.CharField(source="lead_name.lead_name", read_only=True)
    capi_name = serializers.CharField(source="capi_name.head_of_account", read_only=True)
    cash_type = serializers.CharField(source="cash_type.cash_type_name", read_only=True)
    head_of_account = serializers.CharField(source="head_of_account.head_of_account", read_only=True)

    # ✅ Boolean or computed fields
    is_confirmed = serializers.SerializerMethodField()
    approval_cr_status = serializers.SerializerMethodField()

    def get_is_confirmed(self, obj):
        return bool(obj.is_confirmed)

    def get_approval_cr_status(self, obj):
        return bool(obj.approval_cr_status)

    class Meta:
        model = CreditVoucher
        fields = [
            "id",
            "project_name",
            "type",
            "customer_name",
            "lead_name",
            "capi_name",
            "others",
            "cash_type",
            "cheque_number",
            "bill_date",
            "head_of_account",
            "mr_or_bill_no",
            "date",
            "amount",
            "particulars",
            "is_confirmed",
            "approval_cr_status",
            "carrier",
            "create_cr",
        ]

    # ✅ Convert null → "" in output
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key, value in data.items():
            if value is None or (isinstance(value, str) and value.lower() == "none"):
                data[key] = ""
        return data

# ✅ Optional: For full field serialization (update, create, etc.)
class CreditVoucherUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditVoucher
        fields = "__all__"
        
        


# class RequisitionSerializer(serializers.ModelSerializer):
#     project_name = serializers.CharField(source='project_name.project_first_name', read_only=True)
#     employee_name = serializers.CharField(source='employee_name.emp_name', read_only=True)

#     class Meta:
#         model = Requisition
#         fields = [
#             'id',
#             'requi_uniq_id',
#             'requisition_date',
#             'project_name',
#             'employee_name',
#             'amount',
#             'vendor_name',
#             'approv_status',
#         ]



class RequisitionSerializer(serializers.ModelSerializer):
    project_display = serializers.CharField(source='project_name.project_first_name', read_only=True)
    employee_display = serializers.CharField(source='employee_name.emp_name', read_only=True)

    class Meta:
        model = Requisition
        fields = [
            'id',
            'requi_uniq_id',
            'requisition_date',
            'project_name',
            'employee_name',
            'item_name',
            'type',
            'vendor_name',
            'unit',
            'qty',
            'rate',
            'discount',
            'amount',
            'remark',
            'approv_status',
            'project_display', 
            'employee_display', 
        ]


# class InventoriesSerializer(serializers.ModelSerializer):   # detailed record
#     project_id = serializers.CharField(source='project_name.id', read_only=True)
#     project_name = serializers.CharField(source='project_name.project_first_name', read_only=True)
#     employee_name = serializers.CharField(source='employee_name.emp_name', read_only=True)
#     item_name = serializers.CharField(source='item_name.head_requi_name', read_only=True)
#     vendor_name = serializers.CharField(source='vendor_name.supplier_name', read_only=True)

#     class Meta:
#         model = Inventories
#         fields = [
#             'id',
#             'project_id',
#             'project_name',
#             'item_name',
#             'employee_name',
#             'amount',
#             'vendor_name',
#             'remark',
#         ]


class InventoriesSerializer(serializers.ModelSerializer):  
    project_id = serializers.CharField(source='project_name.id', read_only=True)
    project_name = serializers.CharField(source='project_name.project_first_name', read_only=True)

    class Meta:
        model = Inventories
        fields = [
            'id',
            'project_id',
            'project_name',
        ]

class InventoryStockSummarySerializer(serializers.Serializer):   # summary report
    item_id = serializers.IntegerField(source='item_name__id')
    item_name = serializers.CharField(source='item_name__head_requi_name')
    total_qty = serializers.IntegerField()
    total_qtysub = serializers.IntegerField()



class InventoryStockSummaryCheckSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(source='item_name')
    item_name = serializers.CharField(source='item_name__head_requi_name')
    employee_name = serializers.CharField(source='employee_name__emp_name')
    vendor_name = serializers.CharField(source='vendor_name__supplier_name')
    total_qty = serializers.IntegerField()
    available_qty = serializers.IntegerField()
    use_qty = serializers.IntegerField()
    last_purchase_qty = serializers.IntegerField(allow_null=True)
    last_remark = serializers.CharField(allow_null=True)



# Ledger Reports ----
class LedgerEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project_name.project_first_name', default='', read_only=True)
    head = serializers.CharField(source='head.head_name', default='', read_only=True)
    type_name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    vendor = serializers.CharField(source='vendor.supplier_name', default='', read_only=True)
    bank = serializers.CharField(source='bankName.cash_type_name', default='', read_only=True)
    contractor = serializers.CharField(source='contructor.supervisor_name', default='', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'type',
            'type_name',
            'project_name',
            'vendor',
            'bank',
            'contractor',
            'head',
            'date',
            'description',
            'cheque_number',
            'debit',
            'credit'
        ]

# For combined ledger + inventory output
class CombinedLedgerSerializer(serializers.Serializer):
    source = serializers.CharField()
    type = serializers.CharField()  # Added type
    project_name = serializers.CharField()
    head = serializers.CharField()
    name = serializers.CharField()
    date = serializers.DateField()
    description = serializers.CharField()
    cheque_number = serializers.CharField()
    payment = serializers.DecimalField(max_digits=12, decimal_places=2)
    received = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    


class TransactionLedgerSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source="project.project_first_name", read_only=True)
    head = serializers.CharField(source="head_of_account.head_name", read_only=True)
    cash_type = serializers.CharField(source="cash_type.cash_type_name", read_only=True)
    debit = serializers.SerializerMethodField()
    credit = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = TransactionHistory
        fields = [
            "id",
            "project",
            "transaction_type",
            "head",
            "cash_type",
            "date",
            "reference",
            "debit",
            "credit",
            "balance"
        ]

    def get_debit(self, obj):
        return str(obj.amount) if obj.type_name and "_payment" in (obj.type_name or "").lower() else "0.00"

    def get_credit(self, obj):
        return str(obj.amount) if not (obj.type_name and "_payment" in (obj.type_name or "").lower()) else "0.00"

    def get_balance(self, obj):
        balances = self.context.get("balances", {})
        return str(balances.get(obj.id, "0.00"))
        
        
        

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project_name.project_name", read_only=True)

    def get_sender_name(self, obj):
        if obj.sender:
            full = obj.sender.get_full_name()
            return full if full.strip() else obj.sender.username
        return None

    def get_recipient_name(self, obj):
        if obj.recipient:
            full = obj.recipient.get_full_name()
            return full if full.strip() else obj.recipient.username
        return None

    class Meta:
        model = Notification
        fields = [
            "id",
            "sender_name",
            "recipient_name",
            "project_name",
            "message",
            "is_read",
            "link",
            "pass_url",
            "created_at",
            "role",
        ]
        


class BOQListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project_name.project_first_name", read_only=True)
    supplier_name = serializers.CharField(source="supplier_name.supplier_name", read_only=True)

    class Meta:
        model = BOQ
        fields = [
            "id", "boq_date", "project_name", "category_type",
            "category_name", "item_name", "qty", "rate",
            "amount", "supplier_name", "status_item"
        ]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFirstLevelName
        fields = ["id", "project_first_name"]
        
        
        
class CustomerSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    profession = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    contact_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_name',
            'profession',            
            'organization',
            'contact_no',
            'email',
            'address',
            'status',
        ]

    def get_field_or_empty(self, obj, field_name):
        value = getattr(obj, field_name, "")
        if value is None:
            return ""
        return str(value)

    def get_customer_name(self, obj):
        return self.get_field_or_empty(obj, 'customer_name')

    def get_profession(self, obj):
        return self.get_field_or_empty(obj, 'profession')

    def get_organization(self, obj):
        return self.get_field_or_empty(obj, 'organization')

    def get_contact_no(self, obj):
        return self.get_field_or_empty(obj, 'contact_no')

    def get_email(self, obj):
        return self.get_field_or_empty(obj, 'email')

    def get_address(self, obj):
        return self.get_field_or_empty(obj, 'address')

    def get_status(self, obj):
        return str(obj.status)





class RoomSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    total_monthly_rent = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id',
            'room_name',
            'flat',
            'project_name',
            'client_name',
            'status',
            'core_room_rent',
            'parking_cost',
            'service_rent',
            'gas_rent',
            'water_rent',
            'electricity_rent',
            'garbage_rent',
            'other_cost',
            'meter_number',
            'opening_reading',
            'last_month_reading',
            'unit_charge',
            'created_at',
            'total_monthly_rent',
        ]

    def get_project_name(self, obj):
        return obj.project.name if obj.project else ""

    def get_client_name(self, obj):
        # Adjust field name according to Varatiya model (here assumed 'name')
        return getattr(obj.client, "name", "") if obj.client else ""

    def get_total_monthly_rent(self, obj):
        return str(obj.total_monthly_rent or Decimal("0.00"))

    def to_representation(self, instance):
        """Convert nulls to empty strings and decimals to string"""
        data = super().to_representation(instance)
        for key, value in data.items():
            if value is None:
                data[key] = ""
            elif isinstance(value, Decimal):
                data[key] = f"{value:.2f}"
        return data
        
        
        
        



# class BillSerializer(serializers.ModelSerializer):
#     rent_id = serializers.SerializerMethodField()
#     project_name = serializers.SerializerMethodField()
#     room_name = serializers.SerializerMethodField()
#     flat = serializers.CharField(default="", allow_blank=True)
#     varatiya_name = serializers.CharField(default="", allow_blank=True)

#     class Meta:
#         model = Bill
#         fields = [
#             'id', 'room_name', 'flat', 'varatiya_name', 'core_room_rent',
#             'service_rent', 'other_cost', 'subtotal', 'bill_month', 'status',
#             'created_at', 'rent_id', 'project_name', 'room_name'
#         ]

#     def get_rent_id(self, obj):
#         return obj.rent.id if obj.rent else ""

#     def get_project_name(self, obj):
#         return obj.rent.projectref.name if obj.rent and obj.rent.projectref else ""

#     def get_room_name(self, obj):
#         return obj.rent.room.room_name if obj.rent and obj.rent.room else ""
       
     
        

class BillSerializer(serializers.ModelSerializer):
    rent_id = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    room_name = serializers.SerializerMethodField()
    flat = serializers.CharField(default="", allow_blank=True)
    varatiya_name = serializers.CharField(default="", allow_blank=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'room_name', 'flat', 'varatiya_name', 'core_room_rent',
            'service_rent', 'other_cost', 'subtotal', 'bill_month', 'status',
            'created_at', 'rent_id', 'project_name', 'room_name'
        ]

    def get_rent_id(self, obj):
        # Return rent.id as string if it exists, else empty string
        if obj.rent and obj.rent.id is not None:
            return str(obj.rent.id)
        return ""

    def get_project_name(self, obj):
        return obj.rent.projectref.name if obj.rent and obj.rent.projectref else ""

    def get_room_name(self, obj):
        return obj.rent.room.room_name if obj.rent and obj.rent.room else ""

    def get_rent_rent_id(self, obj):
        """Return rent.rent_id as string if exists, else empty string"""
        if obj.rent and getattr(obj.rent, 'rent_id', None) is not None:
            return str(obj.rent.rent_id)
        return ""
        
        
        
        
class RentSerializer(serializers.ModelSerializer):
    projectref = serializers.CharField(source='projectref.name', read_only=True)
    room = serializers.CharField(source='room.room_name', read_only=True)
    varatiya = serializers.CharField(source='varatiya.name', read_only=True)
    endmonths = serializers.SerializerMethodField()

    class Meta:
        model = Rent
        fields = ['id', 'startmonths', 'endmonths', 'status', 'projectref', 'room', 'varatiya']

    def get_endmonths(self, obj):
        """Return empty string if endmonths is None"""
        return obj.endmonths.strftime('%Y-%m-%d') if obj.endmonths else ""
    
    def validate(self, data):
        varatiya = self.instance.varatiya if self.instance else data.get('varatiya')
        status = data.get('status', self.instance.status if self.instance else None)

        if varatiya and status == 'Active':
            active_rent = Rent.objects.filter(varatiya=varatiya, status='Active')
            if self.instance:
                active_rent = active_rent.exclude(pk=self.instance.pk)
            if active_rent.exists():
                raise serializers.ValidationError(f"{varatiya} already has an active rent.")
        return data
        
        
        

class ReceiveVoucherSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    rent_bill = serializers.SerializerMethodField()
    gas_bill = serializers.SerializerMethodField()
    water_bill = serializers.SerializerMethodField()
    parking_bill = serializers.SerializerMethodField()
    service_bill = serializers.SerializerMethodField()
    electricity_bill = serializers.SerializerMethodField()
    mainbill = serializers.SerializerMethodField()
    mr_or_bill_no = serializers.SerializerMethodField()  # override to always show ""

    class Meta:
        model = ReceiveVoucher
        fields = [
            'id',
            'type',
            'cheque_number',
            'bill_date',
            'head_of_account',
            'mr_or_bill_no',
            'date',
            'amount',
            'generated_amount',
            'particulars',
            'is_confirmed',
            'approval_rv_status',
            'carrier',
            'project_name',
            'tenant_name',
            'rent_bill',
            'gas_bill',
            'water_bill',
            'parking_bill',
            'service_bill',
            'electricity_bill',
            'mainbill',
        ]

    def get_project_name(self, obj):
        return obj.project_name.name if obj.project_name else ""

    def get_tenant_name(self, obj):
        return obj.tenant_name.name if obj.tenant_name else ""

    def get_rent_bill(self, obj):
        return obj.rent_bill.varatiya_name if obj.rent_bill else ""

    def get_gas_bill(self, obj):
        return obj.gas_bill.varatiya_name if obj.gas_bill else ""

    def get_water_bill(self, obj):
        return obj.water_bill.varatiya_name if obj.water_bill else ""

    def get_parking_bill(self, obj):
        return obj.parking_bill.varatiya_name if obj.parking_bill else ""

    def get_service_bill(self, obj):
        return obj.service_bill.varatiya_name if obj.service_bill else ""

    def get_electricity_bill(self, obj):
        return obj.electricity_bill.varatiya_name if obj.electricity_bill else ""

    def get_mainbill(self, obj):
        return obj.mainbill.tenant.name if getattr(obj, 'mainbill', None) and obj.mainbill.tenant else ""

    def get_mr_or_bill_no(self, obj):
        # Always return empty string
        return ""
        
        
        
        
    
class PaymentVoucherSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project_name.name', default="", allow_null=True)
    tenant_name = serializers.CharField(source='tenant_name.name', default="", allow_null=True)
    cash_type = serializers.CharField(source='cash_type.name', default="", allow_null=True)
    tenant_advance = serializers.CharField(source='tenant_advance.name', default="", allow_null=True)  # or any field to show

    pv_or_bill_no = serializers.SerializerMethodField()

    class Meta:
        model = PaymentVoucher
        fields = [
            'id', 'type', 'cheque_number', 'bill_date', 'head_of_account',
            'pv_or_bill_no', 'date', 'amount', 'particulars', 'approval_pv_status',
            'carrier', 'project_name', 'tenant_name', 'cash_type', 'tenant_advance'
        ]

    def get_pv_or_bill_no(self, obj):
        return obj.pv_or_bill_no or ""
        
        
        
class LedgerEntryCustomSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', default='')
    receive_voucher = serializers.SerializerMethodField()
    payment_voucher = serializers.SerializerMethodField()
    bill_no = serializers.SerializerMethodField()  # override field

    class Meta:
        model = TenantLedgerEntry
        fields = [
            "id",
            "tenant_name",
            "bill_month",
            "date",
            "description",
            "bill_no",
            "debit",
            "credit",
            "is_opening",
            "receive_voucher",
            "payment_voucher",
        ]

    def get_receive_voucher(self, obj):
        if obj.receive_voucher:
            carrier = getattr(obj.receive_voucher, 'carrier', '')
            return f"{obj.receive_voucher.id} - {carrier or ''}"
        return ""

    def get_payment_voucher(self, obj):
        if obj.payment_voucher:
            carrier = getattr(obj.payment_voucher, 'carrier', '')
            return f"{obj.payment_voucher.id} - {carrier or ''}"
        return ""

    def get_bill_no(self, obj):
        # Always return empty string
        return ""
        
        
## Trail Balance ----Ledger ----       
class LedgerEntryCustomTrailSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source='project_name.project_first_name', default="", allow_null=True)
    cash_type = serializers.CharField(source='cash_type.cash_type_name', default="", allow_null=True)
    account_name = serializers.SerializerMethodField()
    date = serializers.DateField(format="%Y-%m-%d")
    balance = serializers.SerializerMethodField()

    class Meta:
        model = LedgerEntry
        fields = [
            "project",
            "cash_type",
            "type_name",
            "date",
            "debit",
            "credit",
            "balance",
            "account_name",
        ]

    def get_account_name(self, obj):
        if obj.type == "Vendor" and obj.vendor:
            return getattr(obj.vendor, "supplier_name", "N/A")
        elif obj.type == "Customer" and obj.customer_name:
            return getattr(obj.customer_name, "customer_name", "N/A")
        elif obj.type == "Contructor" and obj.contructor:
            return getattr(obj.contructor, "supervisor_name", "N/A")
        elif obj.type == "Bank" and obj.bankName:
            return getattr(obj.bankName, "head_name", "N/A")
        elif obj.type == "Capital" and obj.capi_name:
            return getattr(obj.capi_name, "person_name", "N/A")
        elif obj.type == "Investment" and obj.invest_name:
            return getattr(obj.invest_name, "person_name", "N/A")
        elif obj.type == "Expense" and obj.exp_name:
            return getattr(obj.exp_name, "head_exp_name", "N/A")
        elif obj.type == "Employee" and obj.empl_name:
            return obj.empl_name or "N/A"
        elif obj.type == "Balance_Trf" and obj.balance_trf:
            return obj.balance_trf
        return obj.type_name or "N/A"

    def get_balance(self, obj):
        return (obj.debit or 0) - (obj.credit or 0)


class TrialBalanceTotalsSerializer(serializers.Serializer):
    debit = serializers.DecimalField(max_digits=12, decimal_places=2)
    credit = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    
    
## head of Accunt ---

class HeadOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeadOfAccount
        fields = ['id', 'head_name', 'head_code']
        
        
## Cash Tylpe
class CashTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashType
        fields = ['id', 'cash_type_name']
        
        
        
## Project --
class ProjectFirstLevelNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFirstLevelName
        fields = ['id', 'project_first_name']
        
        
## Supplier --
class SuppliersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suppliers
        fields = [
            'id',
            'supplier_name'
        ]
        
        
##  COntractors ---
class SiteSupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSupervisor
        fields = ['id', 'supervisor_name']