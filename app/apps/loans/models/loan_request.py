from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models
from django.utils import timezone

User = get_user_model()


class LoanRequest(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_requests')
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                           help_text="The amount requested by the borrower.")
    repayment_period_months = models.PositiveIntegerField(
        help_text="Number of months over which the loan will be repaid.")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan Request {self.id} by {self.borrower.username} - Amount: {self.requested_amount} USD"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Cache all active loan requests
        if self.is_active:
            active_requests = LoanRequest.objects.filter(is_active=True)
            cache.set(settings.ACTIVE_LOAN_REQUESTS_CACHE_KEY, active_requests, timeout=3600)
        else:
            # If the saved request is inactive, we should also update the cache
            active_requests = LoanRequest.objects.filter(is_active=True)
            cache.set(settings.ACTIVE_LOAN_REQUESTS_CACHE_KEY, active_requests, timeout=3600)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Update the cache when a LoanRequest is deleted
        active_requests = LoanRequest.objects.filter(is_active=True)
        cache.set(settings.ACTIVE_LOAN_REQUESTS_CACHE_KEY, active_requests, timeout=3600)