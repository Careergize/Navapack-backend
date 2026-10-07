from django.contrib.auth import get_user_model
from django.db import transaction

from Auth.models import Profile
from .models import Salesperson


def sync_salesperson(user_id, using='default'):
    """Maintain one salesperson for each active, approved Sales user."""
    with transaction.atomic(using=using):
        user = get_user_model().objects.using(using).select_for_update().get(pk=user_id)
        profile = Profile.objects.using(using).filter(user_id=user_id).first()
        people = Salesperson.objects.using(using)
        person = people.filter(user_id=user_id).first()
        eligible = (user.is_active and profile is not None and profile.is_approved
                    and profile.department.strip().casefold() == 'sales')
        if not eligible:
            if person is not None and person.is_active:
                person.is_active = False
                person.save(using=using, update_fields=['is_active'])
            return

        base = (user.get_full_name().strip() or user.email or user.get_username())[:100]
        name = base
        others = people.exclude(pk=person.pk) if person else people
        counter = 0
        while others.filter(name=name).exists():
            counter += 1
            suffix = f' ({user.pk})' if counter == 1 else f' ({user.pk}-{counter})'
            name = base[:100 - len(suffix)] + suffix
        if person is None:
            people.create(user_id=user_id, name=name, email=user.email, department='Sales')
        else:
            values = {'name': name, 'email': user.email, 'department': 'Sales', 'is_active': True}
            changed = [field for field, value in values.items() if getattr(person, field) != value]
            for field in changed:
                setattr(person, field, values[field])
            if changed:
                person.save(using=using, update_fields=changed)
