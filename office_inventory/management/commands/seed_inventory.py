"""
Seeds departments, locations, categories and starter stock items that
mirror the BTP LTD spreadsheets (Kitchen Equipment, Furniture, Stationery),
plus the default dynamic Assignment Types and Damage master data so the
Assign / Damage dropdowns aren't empty on a fresh install.

Run with:  python manage.py seed_inventory
"""
from django.core.management.base import BaseCommand
from office_inventory.models import (
    Department, Location, Category, InventoryItem, AssignmentType,
    DamageResponsibleType, DamageReason,
)
from office_inventory import services


class Command(BaseCommand):
    help = "Seed starter departments, locations, categories, stock items and dynamic master data."

    def handle(self, *args, **options):
        depts = [
            ('DPT-001', 'Admin'), ('DPT-002', 'Accounts'), ('DPT-003', 'HR'),
            ('DPT-004', 'Sales'), ('DPT-005', 'Engineering'), ('DPT-006', 'Store'),
        ]
        for dept_id, name in depts:
            Department.objects.get_or_create(dept_id=dept_id, defaults={'name': name})
        self.stdout.write(self.style.SUCCESS(f"Departments ready ({len(depts)})"))

        loc, _ = Location.objects.get_or_create(code='LOC-001', defaults={'name': 'Head Office Store'})

        categories = ['Kitchen Equipment', 'Furniture', 'Stationery']
        cat_objs = {name: Category.objects.get_or_create(name=name)[0] for name in categories}
        self.stdout.write(self.style.SUCCESS(f"Categories ready ({len(categories)})"))

        stationery_items = [
            ('ST-001', 'A4 Paper', 'REAM', 10),
            ('ST-002', 'Ball Pen', 'PCS', 10),
            ('ST-003', 'File', 'PCS', 10),
            ('ST-004', 'Marker', 'PCS', 10),
        ]
        created = 0
        for code, name, unit, min_stock in stationery_items:
            _, was_created = InventoryItem.objects.get_or_create(
                item_code=code,
                defaults={
                    'name': name, 'category': cat_objs['Stationery'], 'location': loc,
                    'unit': unit, 'min_stock': min_stock, 'current_stock': 0,
                }
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Stationery items ready ({created} created)"))

        # Dynamic Assignment Types - "who/what can an item be assigned to".
        assignment_types = [
            ('Employee', True, 'Assigned directly to an employee.'),
            ('Restaurant', False, 'Assigned to a restaurant branch/outlet.'),
            ('Department Pool', False, 'Shared pool held by a department, not one person.'),
            ('Warehouse', False, 'Deployed to a warehouse/store location.'),
        ]
        for name, requires_employee, desc in assignment_types:
            AssignmentType.objects.get_or_create(
                name=name, defaults={'requires_employee': requires_employee, 'description': desc}
            )
        self.stdout.write(self.style.SUCCESS(f"Assignment types ready ({len(assignment_types)})"))

        # Dynamic Damage Responsible Types.
        responsible_types = [
            ('Employee', 'Damage caused by the employee holding the item.'),
            ('Office / Location', 'Damage tied to a branch/office rather than one person.'),
            ('Stock / Inventory', 'Damage discovered in store stock (not yet assigned).'),
            ('Vendor', 'Damage caused by a supplier/vendor (e.g. delivery damage).'),
            ('Other', "Anything that doesn't fit the categories above."),
        ]
        for name, desc in responsible_types:
            DamageResponsibleType.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write(self.style.SUCCESS(f"Damage responsible types ready ({len(responsible_types)})"))

        # Dynamic Damage Reasons.
        damage_reasons = [
            'Mishandling', 'Wear & Tear', 'Accident', 'Manufacturing Defect',
            'Natural Disaster', 'Theft/Loss', 'Other',
        ]
        for name in damage_reasons:
            DamageReason.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f"Damage reasons ready ({len(damage_reasons)})"))

        self.stdout.write(self.style.SUCCESS(
            "Done. Add Kitchen Equipment / Furniture items via the UI or admin - "
            "use 'Add Item' with an opening Current Stock to auto-create the first ledger entry."
        ))
