from django.conf import settings
from django.db import migrations


def link_approved_sales_users(apps, schema_editor):
    Profile = apps.get_model('Auth', 'Profile')
    Salesperson = apps.get_model('marketing', 'Salesperson')
    using = schema_editor.connection.alias
    people = Salesperson.objects.using(using)
    profiles = Profile.objects.using(using).filter(is_approved=True, user__is_active=True).select_related('user')
    for profile in profiles.iterator():
        if profile.department.strip().casefold() != 'sales':
            continue
        user = profile.user
        if people.filter(user_id=user.pk).exists():
            continue
        base = (f'{user.first_name} {user.last_name}'.strip() or user.email or user.username)[:100]
        name = base
        counter = 0
        while people.filter(name=name).exists():
            counter += 1
            suffix = f' ({user.pk})' if counter == 1 else f' ({user.pk}-{counter})'
            name = base[:100 - len(suffix)] + suffix
        people.create(user_id=user.pk, name=name, email=user.email, department='Sales', is_active=True)


class Migration(migrations.Migration):
    dependencies = [
        ('marketing', '0005_followupnotification'),
        ('Auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [migrations.RunPython(link_approved_sales_users, migrations.RunPython.noop)]
