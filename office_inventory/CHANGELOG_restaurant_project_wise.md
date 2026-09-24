# Update: Restaurant-employee assignment + place-wise tracking

This update is **fully additive** — every new field is nullable/blank, no
existing field was removed, renamed, or changed type, and no existing table
data is touched except one safe backfill (see below). Your current
Departments, Locations, Items, Requisitions, Assignments, Purchases and
Damage records are untouched.

There is **no dependency on a "projects" app** in this version — that was
removed per your last message. Everything is scoped by `Location`
(Head Office / Restaurant branch / Kitchen under either) instead.

## 0. App label used

| Constant (in `models.py`) | Value |
|---|---|
| `RESTAURANT_EMPLOYEE_MODEL` | `'restahrm.RestaurantEmployee'` |

If your app label for `RestaurantEmployee` is ever renamed, update:
1. `RESTAURANT_EMPLOYEE_MODEL` at the top of `models.py`.
2. `from restahrm.models import RestaurantEmployee` in `forms.py` and `views.py`.
3. The `dependencies` and `to='...'` value in
   `migrations/0010_restaurant_assignment_and_project_wise.py`.

## 1. What changed, file by file

**models.py**
- New constant `RESTAURANT_EMPLOYEE_MODEL = 'restahrm.RestaurantEmployee'`.
- `Location`: added `location_type` (Head Office / Restaurant / Kitchen /
  Warehouse / Other) and `parent` (self-FK — model "Kitchen under Head
  Office" or "Kitchen under a Restaurant branch" by setting `parent`).
  Added a `full_path` property (`"Gulshan Restaurant > Kitchen"`).
- `AssignmentType`: added `employee_source` (`HR` / `RESTAURANT` / `NONE`).
  The old `requires_employee` boolean is kept and auto-synced from
  `employee_source` by `AssignmentTypeForm.save()`, so nothing that reads
  `requires_employee` elsewhere in your project breaks.
- `Requisition`: added `location` FK and a `unit` snapshot (auto-filled
  from `item.unit` on save if left blank).
- `StockLedger`: added `location`, `department`, `unit` — every stock
  movement is now traceable to a specific place, department, and unit, on
  top of the existing item/user tracking.
- `EmployeeAssignment`: added `restaurant_employee` FK, `department` FK,
  `unit` snapshot. `assignee_label` now also handles restaurant employees.

**migrations/0010_restaurant_assignment_and_project_wise.py**
- Adds all of the above as nullable/blank fields (no data loss).
- One `RunPython` data migration: for every existing `AssignmentType` row,
  sets `employee_source = 'HR'` if `requires_employee` was `True`, else
  `'NONE'` — so your existing assign types keep behaving exactly as before
  until you deliberately change one to `RESTAURANT` in the Assignment
  Types screen.
- Its only cross-app dependency is `('restahrm', '__first__')`.

**forms.py**
- `RequisitionForm`: added optional `location` field.
- `AssignmentForm`: now has three target fields — `employee` (HR),
  `restaurant_employee` (Restaurant), `assignee_name` (free text) — plus
  `department` and `unit`. `clean()` enforces exactly one target based on
  the selected AssignmentType's `employee_source`.
- `AssignmentTypeForm`: exposes `employee_source`; keeps `requires_employee`
  in sync automatically on save.
- `LocationForm`: exposes `location_type`, `parent`.

**services.py**
- `_write_ledger` now accepts/records `location_id`, `department_id`, `unit`.
- `assign_item_to_employee` / `update_assignment` accept `restaurant_employee`,
  `department`, `unit` and route to the right target field based on
  `assignment_type.employee_source`.
- `issue_requisition` / `process_requisition_purchase` carry the
  requisition's `location` / `department` / `unit` onto both the ledger
  entry and any auto-created `EmployeeAssignment`.
- `return_assignment` carries the assignment's `location` / `department` /
  `unit` back onto the return (`IN`) ledger entry.

**views.py**
- `assignment_create` / `assignment_update` pass the new fields through and
  supply `employee_source_map` + `item_unit_map` to drive the form's JS.
- `assignment_list` now passes `is_admin` — the general list only shows the
  **Mark Returned** button to Admin.
- `employee_profile_list` is now **Admin-only** (`@user_passes_test(is_admin_approver)`).
- `employee_asset_profile` now checks the viewer is Admin **or** viewing
  their own profile; only then is `can_return` `True` and the Return button
  shown.
- New `my_assignments` view/url (`/my-assignments/`) — takes the logged-in
  user straight to their own profile without needing Admin rights.

**urls.py** — added `path('my-assignments/', ..., name='my_assignments')`.

**admin.py** — registered the new fields on the relevant admin list/filter.

**Templates touched**
- `assignment_form.html` — 3-way JS toggle (HR / Restaurant / free-text)
  driven by `employee_source_map`; unit auto-fill driven by `item_unit_map`.
- `assignment_list.html` — Mark Returned gated by `{% if is_admin %}`; added
  a "My Assignments" shortcut button; shows restaurant employee + full
  location path + unit.
- `employee_profile.html` — Mark Returned gated by `{% if can_return %}`.
- `requisition_list.html` / `requisition_detail.html` — show Place + Unit.
- `location_list.html` — show Type / Under (parent).

## 2. How the "Head Office / Restaurant / Kitchen" hierarchy works

Location now supports nesting:

1. Create `Location(code='HO', name='Head Office', location_type='HEAD_OFFICE')`.
2. Create `Location(code='HO-KIT', name='Kitchen', location_type='KITCHEN', parent=<Head Office>)`.
3. Create `Location(code='RES-GUL', name='Gulshan Branch', location_type='RESTAURANT')`.
4. Create `Location(code='RES-GUL-KIT', name='Kitchen', location_type='KITCHEN', parent=<Gulshan Branch>)`.

Every Requisition, Assignment, and StockLedger entry can now point at any of
these, so a report can be sliced "Head Office only", "this Restaurant
branch only", or "just its Kitchen".

## 3. How the Restaurant-employee assignment works

In **Assignment Types**, create (or edit) a type, e.g. "Restaurant Staff",
and set **Employee source = Restaurant Employee**. When that type is
selected on the Assign Item form, the Restaurant Employee dropdown (backed
by your `RestaurantEmployee` table in the `restahrm` app, filtered to
`rda_active_status=True`) appears instead of the HR employee dropdown or
the free-text field.

## 4. Return button visibility

- The general **Assignments** list (`/assignments/`) only shows "Mark
  Returned" to users in the `Admin` group / superusers.
- Every employee gets their own page at **/my-assignments/** (also linked
  from the Assignments list toolbar) showing just their own assigned
  items, with a Return button there.
- Admin can still open anyone's profile from `/employees/` and return
  items on their behalf.

## 5. Running it

```bash
python manage.py migrate office_inventory
```

No `--fake`, no data loss, no destructive operations anywhere in this
migration.
