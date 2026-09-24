# Generated for: simplified Item Master (Code + Name only) and
# Purchase <-> Requisition linkage for the Purchase Department panel.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('office_inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='category',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items', to='office_inventory.category',
            ),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='location',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items', to='office_inventory.location',
            ),
        ),
        migrations.AddField(
            model_name='purchase',
            name='requisition',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purchases', to='office_inventory.requisition',
            ),
        ),
    ]
