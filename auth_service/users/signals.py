from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserPreferences, UserRole
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CustomUser)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create user preferences when user is created"""
    if created:
        UserPreferences.objects.get_or_create(user=instance)
        logger.info(f"User preferences created for {instance.email}")

@receiver(post_save, sender=CustomUser)
def assign_default_role(sender, instance, created, **kwargs):
    """Assign default role to new users"""
    if created:
        UserRole.objects.get_or_create(
            user=instance,
            role_name='customer',
            defaults={'assigned_by': None}
        )
        logger.info(f"Default role assigned to {instance.email}")