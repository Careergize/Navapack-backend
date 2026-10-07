from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from Auth.models import Profile
from .models import Salesperson
from .salesperson_sync import sync_salesperson


@receiver(post_save, sender=Profile)
def sync_profile_salesperson(sender, instance, raw=False, using='default', **kwargs):
    if not raw:
        sync_salesperson(instance.user_id, using=using)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_salesperson(sender, instance, raw=False, using='default', **kwargs):
    if not raw:
        sync_salesperson(instance.pk, using=using)


@receiver(pre_delete, sender=Profile)
def deactivate_profile_salesperson(sender, instance, using='default', **kwargs):
    # Retain pipeline/activity ownership when a profile or user is removed.
    for person in Salesperson.objects.using(using).filter(user_id=instance.user_id, is_active=True):
        person.is_active = False
        person.save(using=using, update_fields=['is_active'])
