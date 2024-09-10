from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.wallets.models import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Signal to create a wallet for the user upon creation.
    """
    if created:
        Wallet.objects.create(user=instance)
