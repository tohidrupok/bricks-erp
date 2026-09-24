"""
menu_app/management/commands/seed_menu.py

Seeds the MenuItem table from the legacy hardcoded sidebar template
and maps department strings directly to real Django `Group` objects.

Run with:
    python manage.py seed_menu

Re-running is safe/idempotent — rows are matched on (title, parent, url_name)
and updated in place.

Note: MenuItem only supports 2 levels (top-level section -> child link) —
enforced by MenuItem.clean(). Any section that needs sub-grouping beyond
that is modeled as its own top-level section rather than a nested child.

IMPORTANT: rows are matched on (title, parent, url_name). Any two DATA
entries sharing all three will collide during update_or_create — the
second one silently overwrites the first. The two "Document" sections
below are uniquely titled "Document (Office)" and "Document (Restaurant)"
so they seed as separate rows.

IMPORTANT: group names created here are all lowercase (hrm, accounts,
purchase, admin, engineer, manager, designer, tenant). If you also have
capitalized Group rows (HRM, Accounts, Purchase, Tenant) left over from
manual admin edits, those are DUPLICATES that will NOT match these menu
permissions. Merge/delete the capitalized duplicates after seeding —
see the group-merge script provided separately.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from menu_app.models import MenuItem


# ---------------------------------------------------------------------------
# Department shorthands (mapped to actual Django Groups)
# ---------------------------------------------------------------------------
PROFILE = "engineer,hrm,accounts,purchase,admin"
PROJECT = "engineer,purchase,admin,accounts"
DOC_MAIN = "hrm,accounts,purchase,admin,engineer"
REQ_MAIN = "engineer,purchase,accounts,admin"
ACC_MAIN = "accounts,admin,purchase"
ADMIN = "admin"
TENANT = "tenant"
DESIGNER = "designer"
MANAGER = "manager"


def d(*groups):
    """Join department-group strings into one deduped comma list."""
    seen, out = set(), []
    for g in groups:
        for part in g.split(","):
            part = part.strip()
            if part and part not in seen:
                seen.add(part)
                out.append(part)
    return ",".join(out)


def item(title, url="", icon="activity", depts=None, children=None):
    return {
        "title": title,
        "url": url,
        "icon": icon,
        "depts": depts or "",
        "children": children or [],
    }


# ---------------------------------------------------------------------------
# The menu tree data structure
# NOTE: every "children" list here must be exactly 1 level — no item inside
# a "children" list may itself have non-empty "children". That's what makes
# this compatible with MenuItem's 2-level constraint.
#
# NOTE: keep (title, url) unique among siblings under the same parent —
# that's the lookup key used to match/update rows on re-run.
# ---------------------------------------------------------------------------
DATA = [
    item("Dashboard", "dashboard", "home", depts=""),  # Unconfigured = superuser only (or make public if desired)

    item("Profile", icon="map-pin", depts=PROFILE, children=[
        item("Donation Name", "donation_list"),
        item("Software User", "employee_list"),
        item("User Permision", "user_group_menu_assign"),
    ]),

    item("Project", icon="map-pin", depts=PROJECT, children=[
        item("Project List", "first_level_list"),
        item("BOQ List", "boq_list"),
        item("BOQ Details List", "boqdetails_list"),
        item("Properties Owner List", "property_owner_list", icon="zap"),
        item("Project Location", "project_location_list"),
        item("Contructor Add", "boq_contructor_list"),
        item("Supplier Add", "boq_supplier_list"),
    ]),

    item("Contractor", icon="map-pin", depts=PROJECT, children=[
        item("Activity List", "activity_list"),
    ]),

    item("Comparation Entry", icon="map-pin", depts=PROJECT, children=[
        item("Item List", "materialentry_list"),
    ]),

    item("File Tracking", icon="shopping-bag", depts=d(ADMIN, MANAGER), children=[
        item("File Manage", "file_record_list", depts=d(ADMIN, MANAGER)),
        item("Land Tracker Tree", "tracker:list", depts=ADMIN),
        item("Tracker Google Drive", "tracker_display", depts=ADMIN),
    ]),

    item("Property/Land", icon="shopping-bag", depts=ADMIN, children=[
        item("Land Dashboard", "land_dashboard", icon="zap"),
        item("Land Purchase List", "land_list", icon="zap"),
    ]),

    item("Admin Document", icon="map-pin", depts=ADMIN, children=[
        item("Private Document", "display"),
        item("Employee Document", "emp_document"),
        item("Document List", "document_list"),
        item("Upload Document", "upload_document"),
    ]),

    item("Tenant", icon="users", depts=d(TENANT, ACC_MAIN), children=[
        item("Dashboard", "tenant_dashboard", icon="layers"),
        item("Project List", "project_page", icon="layers"),
        item("Room List", "room_list", icon="home"),
        item("Tenant List", "varatiya_list", icon="user"),
        item("Rent List", "rent_form_and_list", icon="clipboard-list"),
        item("Deactive Room", "rent_search", icon="ban"),
        item("Bills Generate", "bill_generator_home", icon="file-text"),
        item("Advance Payment", "tenant_advance_list", icon="wallet"),
        item("Adjust Payment", "payment_tenant_advance", icon="credit-card"),
        item("cheque Book Manage", "cheque_book_list", icon="book"),
        item("Accounting", "account_list", icon="dollar-sign"),
        item("Discount Bills", "mainbill_list", icon="book"),
        item("Top Sheet", "main_bill_list", icon="file-bar-chart"),
        item("Ledger Report", "tenant_ledger_input_page", icon="book"),
        item("Receivable Voucher", "bill_summary_page", icon="receipt"),
        item("Received Voucher List", "receive_voucher_list", icon="file-text"),
        item("Payment Voucher List", "payment_voucher_list", icon="file-text"),
        item("Tenant SMS Send", "varatiya_bulk_sms", icon="file-text", depts=ACC_MAIN),
    ]),

    item("Document (Office)", icon="map-pin", depts=DOC_MAIN, children=[
        item("Employee Document", "emp_document"),
        item("File Manage", "file_record_list"),
    ]),

    item("Task Management", icon="clipboard-list",
         depts=d(DOC_MAIN, DESIGNER, MANAGER), children=[
        item("Office (Admin)", "task_assign_btp_employee", depts=d(ADMIN, DESIGNER)),
        item("My Assigned Tasks", "employee_task_dashboard", icon="user",
             depts=d("hrm,accounts,purchase,engineer", MANAGER)),
    ]),

    item("HRM", icon="map-pin", depts=d(DOC_MAIN, MANAGER), children=[
        item("Break Section", "profile", depts=DOC_MAIN),
        item("Employee Add", "rda_employee_list", depts=d(DOC_MAIN, MANAGER)),
        item("Salary Payment", "salary_list", depts=DOC_MAIN),
        item("Attendance List", "attendance_list", depts=d(DOC_MAIN, MANAGER)),
        item("Payroll List", "payroll_list", depts=DOC_MAIN),
        item("Advance Payment", "advance_list", depts=DOC_MAIN),
        item("Allowance Payment", "allowances_list", depts=DOC_MAIN),
        item("Loan Payment", "loanPayment_list", depts=DOC_MAIN),
        item("Leave List", "leave_list", depts=d(DOC_MAIN, MANAGER)),
        item("IOM List", "iom_list", depts=d(DOC_MAIN, MANAGER)),
        item("Note List", "note_list", depts=d(DOC_MAIN, MANAGER)),
        item("Office Inventory", "office_inventory:dashboard", depts=MANAGER),
    ]),

    item("Document (Restaurant)", icon="map-pin", depts=DESIGNER, children=[
        item("Employee Document", "emp_document"),
        item("File Manage", "file_record_list"),
        item("IOM List", "restau_iom_list"),
    ]),

    item("Requisition", icon="map-pin", depts=d(REQ_MAIN, MANAGER), children=[
        item("Requisition List", "requisition_list", depts=d(REQ_MAIN, MANAGER)),
        item("Supplier Approval Payment", "requisition_payment_list",
             depts=d(REQ_MAIN, MANAGER)),
        item("Bill Requisition", "bill_requisition_list", depts=d(REQ_MAIN, MANAGER)),
        item("Bill Approval Payment", "bill_reqs_payment_list", depts=REQ_MAIN),
        item("Requis. Comparative", "requisition_comparative_list",
             depts=d(REQ_MAIN, MANAGER)),
        item("BOQ vs Requisitio", "project_boq_requisition_summary",
             depts=d(REQ_MAIN, MANAGER)),
        item("Revise Requisition", "", depts=d(REQ_MAIN, MANAGER)),
        item("Requisition Invoice", "requisition_invoice_list", depts=d(REQ_MAIN, MANAGER)),
    ]),

    item("Purchase", icon="map-pin", depts=REQ_MAIN, children=[
        item("Purchase Order", "purchase_list"),
        item("Purchase Invoice", "purchase_invoice_list"),
        item("Return Purchase", "return_purchase_list"),
    ]),

    item("Inventory", icon="map-pin", depts=d(REQ_MAIN, MANAGER), children=[
        item("Inventory List", "inventory_item_list"),
        item("Stock Summary", "inventory_stock_summary"),
        item("Inventory Use", "inventory_use_list"),
        item("Product Category", "requisition_category"),
        item("Product Name", "head_of_requisition_list"),
    ]),

    item("CRM", icon="map-pin", depts=d(REQ_MAIN, MANAGER), children=[
        item("Customer Bank", "customer_bank"),
        item("Sales Customer Add", "customer_list"),
        item("Lead Generate List", "customer_lead_list"),
        item("Lead Followup", "lead_followup_list"),
        item("Bulk SMS Send", "bulk_sms_send"),
    ]),

    item("Sales", icon="map-pin", depts=REQ_MAIN, children=[
        item("Flat/Plot Add", "flat_plot_summary"),
        item("Property List", "flat_plot_property_list"),
        item("Flat/Plot Sales", "flat_plot_sales"),
        item("Sales Installment", "flat_plot_installment_management"),
        item("Sales Commission", "sales_commission_list"),
        item("Lillahitaala Amount", "sales_lilahetalah_list"),
        item("Share Plot List", "share_plot_list"),
        item("Share Installment", "share_installment_list"),
    ]),

    item("Expense", icon="map-pin", depts=REQ_MAIN, children=[
        item("Expense List", "expense_list"),
        item("Expense Requisition", "grouped_requisitions"),
        item("Expense Head", "expense_head_list"),
    ]),

    item("Accounting", icon="map-pin", depts=ACC_MAIN, children=[
        item("Cash Type (Method)", "cash_type_list"),
        item("Account Head", "head_of_account_list"),
        item("Others Head", "capital_account_list"),
        item("Cheque Manage", "main_cheque_book_list"),
        item("Received Voucher List", "creditvoucher_list"),
        item("Payment Voucher List", "debitvoucher_list"),
        item("Journal Voucher List", "journal_voucher_list"),
        item("Opening Balance", "openbalance_voucher_list"),
        item("Ledger Manage", "ledger_manage_list"),
        item("Payable/Receivable", "loanvoucher_list"),
        item("Balance Sheet Head", "balance_sheet_head_list"),
        item("Balance Sheet", "balance_item_list"),
        item("Cash Type Balance", "cashType_balance_list"),
        item("Transaction History", "transaction_history_list"),
        item("Balance Transfer", "transfer_list"),
        item("Upload Statement", "upload_statement"),
        item("Reconciliation", "reconciliation_dashboard"),
    ]),

    item("Reports", icon="map-pin", depts=ACC_MAIN, children=[
        item("Genarel Ledger", "reports_manage_list"),
        item("Supplier Ledger", "supplier_summary_report"),
        item("Employee Ledger", "employee_summary_report"),
        item("Customer Ledger", "customer_summary_report"),
        item("Purchase Ledger", "purchase_invoice_filter"),
        item("Project Ledger", "project_ledger_list"),
        item("Inventory Ledger", "invStock_ledger_list"),
        item("Bank Reports", "bank_reports_list"),
        item("Transaction Reports", "transaction_reports_list"),
        item("Top Sheet Reports", "topsheet_reports_list"),
        item("Monthly Collection", "monthly_collection_reports_list"),
        item("Trail Balance", "trial_balance_list"),
        item("Balance Sheet", "balance_sheet_report"),
        item("Profit Ledger", "profit_ledger_list"),
    ]),

    item("RecycleBin", icon="map-pin", depts=ADMIN, children=[
        item("Delete History", "deleted_records"),
    ]),

    item("Restaurant", icon="shopping-bag", depts=MANAGER, children=[
        item("Public Link", "public_restaurant_home", icon="zap"),
    ]),

    item("Restaurant Requisition", icon="activity", depts=MANAGER, children=[
        item("Requisition List", "restau_requisition_list", icon="zap"),
        item("Approval History", "requisition_approval_history_list", icon="zap"),
        item("kitchen Ledger", "restaurant_kitchen_ledger_list", icon="zap"),
        item("Expense List", "restaurant_expense_account_list", icon="zap"),
        item("Item Category", "restaurant_requisition_category", icon="zap"),
        item("Item Name", "restaurant_item_name", icon="zap"),
    ]),

    item("Restaurant HRM", icon="activity", depts=MANAGER, children=[
        item("Employee Details", "restaurant_employee_list", icon="zap"),
        item("Attendance List", "restaurant_attendance_list", icon="zap"),
        item("Leave", "restau_leavelist", icon="zap"),
        item("IOM List", "restau_iom_list"),
    ]),

    item("Restaurant Expense", icon="activity", depts=MANAGER, children=[
        item("Expense Requisition", "restaurant_grouped_requisitions", icon="zap"),
        item("Expense Name", "rest_expense_list", icon="zap"),
        item("Purchase Name", "rest_purchase_cost_list", icon="zap"),
    ]),
]


class Command(BaseCommand):
    help = "Seed MenuItem rows and auto-create Django Group mappings."

    def handle(self, *args, **options):
        created, updated = 0, 0

        all_dept_names = set()

        def collect_depts(nodes):
            for node in nodes:
                if node["depts"]:
                    for dept in node["depts"].split(","):
                        if dept.strip():
                            all_dept_names.add(dept.strip())
                if node["children"]:
                    collect_depts(node["children"])

        collect_depts(DATA)

        seen_top_level = set()
        for node in DATA:
            key = (node["title"], node["url"])
            if key in seen_top_level:
                raise ValueError(
                    f"Duplicate top-level menu entry detected: title={node['title']!r}, "
                    f"url={node['url']!r}. Rename one of them before seeding — "
                    f"identical (title, parent, url) rows overwrite each other."
                )
            seen_top_level.add(key)

        with transaction.atomic():
            group_cache = {}
            for dept_name in all_dept_names:
                group_obj, _ = Group.objects.get_or_create(name=dept_name)
                group_cache[dept_name] = group_obj

            def seed(nodes, parent=None):
                nonlocal created, updated
                for order, node in enumerate(nodes):
                    obj, was_created = MenuItem.objects.update_or_create(
                        title=node["title"],
                        parent=parent,
                        url_name=node["url"],
                        defaults={
                            "icon": node["icon"],
                            "order": order,
                            "is_active": True,
                        },
                    )

                    if node["depts"]:
                        dept_list = [d.strip() for d in node["depts"].split(",") if d.strip()]
                        assigned_groups = [group_cache[d] for d in dept_list if d in group_cache]
                        obj.groups.set(assigned_groups)
                    else:
                        obj.groups.clear()

                    created += was_created
                    updated += not was_created

                    if node["children"]:
                        seed(node["children"], parent=obj)

            seed(DATA)

        self.stdout.write(self.style.SUCCESS(
            f"Menu seeded successfully: {created} created, {updated} updated "
            f"({MenuItem.objects.count()} total rows). Groups verified: {list(group_cache.keys())}"
        ))