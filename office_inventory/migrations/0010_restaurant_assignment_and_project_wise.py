"""
Additive migration only:
  - No existing field is removed, renamed, or has its type changed.
  - Every new field is null=True/blank=True (FKs) or blank=True with a safe
    default (choice fields), so this is 100% backward compatible with your
    existing rows - nothing is dropped or rewritten.

Cross-app FK:
  - EmployeeAssignment.restaurant_employee -> 'restahrm.RestaurantEmployee'

If your actual app label for the restaurant-employee app is different from
'restahrm', update BOTH this file (the dependency + the `to=` below) and
the RESTAURANT_EMPLOYEE_MODEL constant at the top of models.py before
running `migrate`.
"""
from django.db import migrations, models
import django.db.models.deletion


def set_employee_source_from_requires_employee(apps, schema_editor):
    """Data migration: keep existing AssignmentType rows working exactly as
    before by translating the old boolean into the new, more precise
    employee_source field. Nothing here can lose data."""
    AssignmentType = apps.get_model('office_inventory', 'AssignmentType')
    for a_type in AssignmentType.objects.all():
        if a_type.requires_employee:
            a_type.employee_source = 'HR'
        else:
            a_type.employee_source = 'NONE'
        a_type.save(update_fields=['employee_source'])


def noop_reverse(apps, schema_editor):
    """Reverse is a no-op - the requires_employee boolean is untouched by
    the forward migration, so nothing needs to be restored."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('office_inventory', '0009_alter_inventoryitem_unit'),
        ('restahrm', '__first__'),
    ]

    operations = [
        # -- Location: hierarchy + type ---------------------------------
        migrations.AddField(
            model_name='location',
            name='location_type',
            field=models.CharField(
                choices=[('HEAD_OFFICE', 'Head Office'), ('RESTAURANT', 'Restaurant'),
                         ('KITCHEN', 'Kitchen'), ('WAREHOUSE', 'Warehouse'), ('OTHER', 'Other')],
                default='OTHER', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='location',
            name='parent',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='sub_locations', to='office_inventory.location',
            ),
        ),

        # -- AssignmentType: precise employee source -------------------------
        migrations.AddField(
            model_name='assignmenttype',
            name='employee_source',
            field=models.CharField(
                choices=[('NONE', 'No specific employee (free-text name)'),
                         ('HR', 'HR / Office Employee (hrm.RdaEmployee)'),
                         ('RESTAURANT', 'Restaurant Employee (RestaurantEmployee)')],
                default='HR', max_length=20,
            ),
        ),
        migrations.RunPython(set_employee_source_from_requires_employee, noop_reverse),

        # -- Requisition: place + unit snapshot -------------------------------
        migrations.AddField(
            model_name='requisition',
            name='location',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='requisitions', to='office_inventory.location',
            ),
        ),
        migrations.AddField(
            model_name='requisition',
            name='unit',
            field=models.CharField(
                blank=True,
                choices=[('PCS', 'Pcs'), ('REAM', 'Ream'), ('BOX', 'Box'), ('SET', 'Set'),
                         ('KG', 'Kg'), ('LTR', 'Litre'), ('UNIT', 'Unit'), ('GRAM', 'Gram')],
                max_length=10,
            ),
        ),

        # -- StockLedger: place + department + unit --------------------------
        migrations.AddField(
            model_name='stockledger',
            name='location',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='ledger_entries', to='office_inventory.location',
            ),
        ),
        migrations.AddField(
            model_name='stockledger',
            name='department',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='ledger_entries', to='office_inventory.department',
            ),
        ),
        migrations.AddField(
            model_name='stockledger',
            name='unit',
            field=models.CharField(
                blank=True,
                choices=[('PCS', 'Pcs'), ('REAM', 'Ream'), ('BOX', 'Box'), ('SET', 'Set'),
                         ('KG', 'Kg'), ('LTR', 'Litre'), ('UNIT', 'Unit'), ('GRAM', 'Gram')],
                max_length=10,
            ),
        ),

        # -- EmployeeAssignment: restaurant employee + department + unit -----
        migrations.AddField(
            model_name='employeeassignment',
            name='restaurant_employee',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='assigned_items', to='restahrm.restaurantemployee',
            ),
        ),
        migrations.AddField(
            model_name='employeeassignment',
            name='department',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='assignments', to='office_inventory.department',
            ),
        ),
        migrations.AddField(
            model_name='employeeassignment',
            name='unit',
            field=models.CharField(
                blank=True,
                choices=[('PCS', 'Pcs'), ('REAM', 'Ream'), ('BOX', 'Box'), ('SET', 'Set'),
                         ('KG', 'Kg'), ('LTR', 'Litre'), ('UNIT', 'Unit'), ('GRAM', 'Gram')],
                max_length=10,
            ),
        ),
    ]
