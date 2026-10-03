from django.db import migrations, models


def seed_departments(apps, schema_editor):
    Department = apps.get_model('marketing', 'Department')
    DropdownLists = apps.get_model('marketing', 'DropdownLists')
    database = schema_editor.connection.alias
    names = ['Sales', 'HR', 'Marketing']
    for name in names:
        Department.objects.using(database).get_or_create(name=name)
    dropdown, _ = DropdownLists.objects.using(database).get_or_create(pk=1)
    dropdown.departments = list(dict.fromkeys([*dropdown.departments, *names]))
    dropdown.save(using=database, update_fields=['departments'])


class Migration(migrations.Migration):
    dependencies = [('marketing', '0002_activitytype_productservice_salesstage_unit')]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.RunPython(seed_departments, migrations.RunPython.noop),
    ]
