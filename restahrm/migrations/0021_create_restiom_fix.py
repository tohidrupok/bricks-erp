from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('restahrm', '0020_rename_restaurantiom_restiom'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestIom',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('start_date', models.DateField()),
                ('check_in', models.TimeField(null=True, blank=True)),
                ('check_out', models.TimeField(null=True, blank=True)),
                ('reason', models.TextField()),
                ('approved', models.BooleanField(default=False)),
                ('employee', models.ForeignKey(
                    to='restahrm.restaurantemployee',
                    on_delete=django.db.models.deletion.CASCADE,
                )),
            ],
        ),
    ]
