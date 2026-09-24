# BTP Office Inventory System (Django)

## UPDATE 2 - Min/Opening Stock on Item Create, Auto-Employee Requisitions,
## Dynamic Assignment Types + Location, Damage Tracking, Excel/PDF Reports

This pass adds five things on top of everything below:

1. **Item Master now asks for Min Stock + Opening/Current Qty.** The "Add
   Item" form (`InventoryItemForm`) gained `location`, `unit`, `min_stock`,
   and a non-model `opening_stock` field. Opening qty is never written to
   `current_stock` directly - `item_create()` runs it through
   `services.receive_stock()` so it lands in the stock ledger like every
   other movement (full audit trail). Editing an item (`item_update()`,
   new) shows current stock read-only; it's only ever changed through
   Purchase / Requisition / Assignment / Damage.

2. **Requisition employee auto-fill.** `RequisitionForm(is_admin=...)`
   drops the `employee` field entirely for non-admin users - the view sets
   `req.employee` to the logged-in user's own employee record
   (`_current_employee`). Only Admin/superuser users see the Employee
   dropdown and can raise a requisition on someone else's behalf.

3. **Dynamic Assignment Types + location-wise assignment.** New
   `AssignmentType` model (Admin-managed under **Assign Types**) replaces
   the old "always an employee" assumption - each type has
   `requires_employee` (True for "Employee", False for e.g. "Restaurant",
   "Department Pool", "Warehouse", or anything you add). `EmployeeAssignment`
   gained `assignment_type`, `location`, and `assignee_name` (free text used
   when `requires_employee` is False); `employee` is now nullable. The
   Assign form shows/hides the Employee vs. free-text field client-side
   based on the selected type (`assignment_form.html`), and every
   AssignmentType has its own type-wise profile page
   (`/assignment-types/<id>/profile/`) listing everything currently held vs.
   returned under that type - same shape as the per-employee profile.
   `services.update_assignment()` replaces the old ad-hoc "guess the stock
   field name" hack in `assignment_update` with a proper ledger-audited
   qty/item swap.

4. **Damage tracking.** New `DamageResponsibleType` (Employee, Office/
   Location, Stock/Inventory, Vendor, Other - all Admin-editable/dynamic),
   `DamageReason` (Mishandling, Wear & Tear, Accident, ... - dynamic), and
   `DamageRecord` models under **Damage Records**. A damage record can
   optionally link back to the `EmployeeAssignment` it happened under
   ("damage after assign") or stand alone for damage found directly in
   store stock. `services.report_damage()` optionally writes the damaged
   qty off `current_stock` through the normal ledger (`DMG-xxxxx`
   reference), with an over-deduction guard. Status moves through
   Reported -> Under Review -> Resolved / Written Off via
   `services.set_damage_status()`.

5. **Reports - Excel & PDF export.** New `reports.py` module (openpyxl for
   `.xlsx`, reportlab for `.pdf`) plus a **Reports** hub page
   (`/reports/`) with per-module filters (category/location, status,
   date range, assign type, responsible type) for Inventory, Requisitions,
   Purchases, Assignments, and Damage - each exportable as Excel or PDF
   with one click. `damage_list.html` and `item_list.html` also link
   straight to their filtered export.

Run `python manage.py makemigrations office_inventory && python manage.py
migrate` to apply migration `0003_assignment_and_damage_tracking`, then
`python manage.py seed_inventory` to seed the default Assignment Types
(Employee / Restaurant / Department Pool / Warehouse) and Damage master
data (Responsible Types + Reasons) so the new dropdowns aren't empty.

---

## UPDATE - Simplified Item Master + Purchase-linked Requisition flow

This version changes two things based on the latest requirement:

1. **Item Master is now just Code + Name.** `InventoryItem.category` and
   `.location` are optional (`null=True, blank=True`), and the "Add Item"
   form (`forms.InventoryItemForm`) only shows `item_code`, `name`,
   `category` (optional dropdown) and `is_asset`. There is **no quantity
   field on the item form at all** - stock always starts at 0 and can only
   ever change through a Purchase, a Requisition issue, or an Assignment.
   Run migration `0002_simplify_item_master_and_link_purchase` to apply this.

2. **Purchase Department panel** (`/purchases/queue/`, view `purchase_queue` /
   `purchase_approve_requisition`, group **`PurchaseOfficer`**): once a
   requisition is Admin-Approved, it appears here. The purchase officer can
   **only** enter Supplier + Unit Price - the item and quantity are locked to
   what Department + Admin already approved and cannot be edited. Clicking
   **Approve Purchase** runs `services.process_requisition_purchase()`, which
   atomically: creates and receives the `Purchase` (linked via the new
   `Purchase.requisition` field), adds the qty to store stock via the stock
   ledger, marks the requisition `Issued`, and - if the item `is_asset` - auto
   creates the employee's `EmployeeAssignment` record.

   Updated workflow:
   ```
   Employee creates Requisition
       -> Department Head/Manager approves   (dept_approve_requisition)
       -> Admin approves                     (admin_approve_requisition)
       -> Purchase Officer approves purchase (process_requisition_purchase)
              - item & qty locked, cannot edit
              - stock/inventory updates automatically
              - if is_asset: employee asset profile updated
   ```

3. **Employee-wise Asset Profile** (`/employees/`, `/employees/<id>/profile/`):
   a clean profile page per employee showing everything currently assigned to
   them plus their full return history, linked from the Assignments list.

The original direct Purchase flow (`/purchases/new/`, `/purchases/<id>/receive/`)
and the original Store-Officer issue step (`/requisitions/<id>/issue/`) are
kept as-is for restocking items that aren't tied to a specific requisition.

---


App name: **`office_inventory`** — a complete inventory / requisition /
purchase / employee-assignment module built to plug into your existing
BM ERP Django project, alongside `RestaurantKitchenLedger`,
`projects.ProjectFirstLevelName`, etc.

## Modules

| Module | What it does |
|---|---|
| **Inventory** | Category-wise + location-wise stock items, min-stock/low-stock flag |
| **Requisition** | Employee requests an item |
| **Approval** | Two-stage approval: Department Head, then Admin |
| **Purchase** | Order stock from a supplier, then receive it (stock auto-adds) |
| **Inventory Assign** | Hand an asset directly to an employee (main stock decreases); return it later (stock restored) |
| **Dashboard** | Live totals: requisitions, pending, completed, low stock, pending purchases, assets in employees' hands, plus category/location stock breakdown |

## Workflow implemented

```
Employee (creates Requisition)
    ↓
Department Head Approval  (dept_approve_requisition)
    ↓
Admin Approval             (admin_approve_requisition)
    ↓
Store Issue                (issue_requisition)
    ↓
Stock Auto Deduct          (services._write_ledger, inside select_for_update())
    ↓
Dashboard Update           (dashboard view reads live totals)
```

Purchases follow their own short loop that feeds the same stock/ledger:

```
Purchase Order (Ordered)  ->  Receive  (receive_purchase)  ->  Stock Auto Add  ->  Dashboard Update
```

Every stock change (opening stock, issue, direct assignment, return) is written
through `office_inventory/services.py`, which wraps each operation in
`transaction.atomic()` with `select_for_update()` — the same locking pattern
you're using in `RestaurantKitchenLedger`, so two people issuing the same item
at once can never over-deduct stock.

## What's included

| File | Purpose |
|---|---|
| `office_inventory/models.py` | `Department`, `Location`, `Category`, `InventoryItem` (category + location wise), `Requisition`, `StockLedger`, `Purchase`, `EmployeeAssignment`. **No `RdaEmployee` class** — every employee FK links to your existing `hrm.RdaEmployee` via a string reference. |
| `office_inventory/services.py` | All stock-changing business logic (atomic, race-safe) |
| `office_inventory/views.py` | Dashboard, item list/create, requisition workflow, purchase workflow, employee assignment |
| `office_inventory/forms.py` | Bootstrap-styled ModelForms |
| `office_inventory/admin.py` | Django admin registration (does **not** touch `RdaEmployee` — that's already registered by your `hrm` app) |
| `office_inventory/urls.py` | URL routes under the `office_inventory:` namespace |
| `office_inventory/templates/office_inventory/*.html` | Bootstrap 5 UI (sidebar nav, dashboard cards, tables) |
| `office_inventory/management/commands/seed_inventory.py` | Seeds Departments / Location / Categories / Stationery items to match your spreadsheets |

## Key model design decisions

- **Category-wise + location-wise stock**: `InventoryItem` has both a
  `category` FK (Kitchen Equipment / Furniture / Stationery / IT Asset, etc.)
  and a `location` FK (which store/warehouse/branch holds it), so the
  dashboard and item list can be filtered/grouped either way.
- **`is_asset` flag**: Consumables (paper, pens) get consumed permanently on
  issue. Returnable assets (chairs, laptops) should have `is_asset=True` —
  issuing one through a requisition automatically creates an
  `EmployeeAssignment` row, and returning it restores stock.
- **Employee-wise direct assignment**: `assign_item_to_employee()` lets you
  hand an asset to an employee without going through the requisition
  workflow (e.g. issuing a laptop on day one) — main stock decreases
  immediately, exactly as you described.
- **`RdaEmployee`**: this app does **not** define its own copy. Every FK
  (`Department.manager`, `Requisition.employee/dept_approver/admin_approver/
  store_officer`, `StockLedger.user`, `Purchase.received_by`,
  `EmployeeAssignment.employee`) points at your real `hrm.RdaEmployee` via
  one constant at the top of `models.py`:
  ```python
  RDA_EMPLOYEE_MODEL = 'hrm.RdaEmployee'
  ```
  If your HR app's label isn't `hrm`, change that single line — nothing
  else in the file needs to change.

## Installation

1. Copy the `office_inventory/` folder into your Django project root (next to
   your other apps like `hrm`, `projects`, `restaurant`, etc).

2. Add to `settings.py`:
   ```python
   INSTALLED_APPS = [
       ...
       'office_inventory',
   ]
   ```
   (`hrm` and any app it depends on, e.g. `projects`, must already be listed.)

3. Add to your project's root `urls.py`:
   ```python
   from django.urls import path, include

   urlpatterns = [
       ...
       path('office_inventory/', include('office_inventory.urls')),
   ]
   ```

4. **Confirm your HR app's label.** Open `office_inventory/models.py` and
   check the top of the file:
   ```python
   RDA_EMPLOYEE_MODEL = 'hrm.RdaEmployee'
   ```
   If `RdaEmployee` lives in an app whose `INSTALLED_APPS` label isn't
   `hrm`, change this one line to match (e.g. `'humanresource.RdaEmployee'`).
   This is the only place you ever need to edit for this integration.

5. Run migrations:
   ```bash
   python manage.py makemigrations office_inventory
   python manage.py migrate
   ```

6. Seed starter data (departments, one location, categories, stationery items
   matching your spreadsheet):
   ```bash
   python manage.py seed_inventory
   ```

7. Set up approval roles — create three Django Groups and add the right users:
   - `DeptHead` — can approve/reject at the department stage
   - `Admin` — can approve/reject at the admin stage
   - `StoreOfficer` — can issue stock and receive purchases
   
   (Superusers can do all three regardless of group membership.) You can do
   this from `/admin/auth/group/`.

8. Visit `/office_inventory/` — you'll land on the dashboard.

## Adjusting to your auth system

`views._current_employee()` currently maps the logged-in Django `User` to an
`hrm.RdaEmployee` row by matching email. If your project links them
differently (e.g. a `OneToOneField` from `User` to `RdaEmployee`), update
that one function — everything else (approvals, issuing, assignments) calls
through it.

## Extending further

- **Purchase/GRN module**: `services.receive_stock()` is already wired for
  "stock coming in" — build a simple purchase-order form on top of it to log
  new procurement, matching your `PUR. AMOUNT` / `PURCHASE DATE` spreadsheet
  columns (already fields on `InventoryItem`).
- **Reports**: `StockLedger` gives you a full IN/OUT/balance trail per item —
  useful for a "stock movement report" page or CSV export.
- **Multi-location transfers**: if you need to move stock between two
  locations, add a `transfer_stock()` service that does an OUT ledger entry
  at the source item and an IN at the destination item inside one atomic
  transaction.
