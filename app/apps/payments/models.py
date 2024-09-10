from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from apps.loans.models.loan import Loan
from apps.payments import config


class Payment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                         help_text="The amount paid for this installment.")
    payment_due_date = models.DateField(help_text="The due date for the payment.")
    payment_status = models.CharField(
        max_length=20,
        choices=config.PAYMENT_STATUS_CHOICES,
        default=config.PAYMENT_STATUS_PENDING,
        help_text="Status of the payment."
    )
    payment_status_changed = models.DateTimeField(null=True, blank=True,
                                                  help_text="Timestamp when the payment status was last changed.")
    late_payment_fees_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                   help_text="Amount of fees charged for late payment.")
    created = models.DateTimeField(default=timezone.now, help_text="Timestamp when the payment record was created.")
    modified = models.DateTimeField(auto_now=True, help_text="Timestamp when the payment record was last modified.")
    is_late_payment = models.BooleanField(default=False, help_text="Indicates whether the payment was made late.")

    def __str__(self):
        return f"Payment {self.id} for Loan {self.loan.id} - Status: {self.payment_status}"

    def save(self, *args, **kwargs):
        # Automatically update `is_late_payment` and `payment_status` fields based on due date and payment status
        if self.payment_status == 'paid' and self.payment_status_changed:
            self.is_late_payment = self.payment_due_date < self.payment_status_changed.date()
            if self.is_late_payment and self.late_payment_fees_amount is None:
                self.late_payment_fees_amount = self.calculate_late_fee()

        super().save(*args, **kwargs)

    def calculate_late_fee(self):
        return round(self.payment_amount * 0.05, 2)  # 5% of the payment amount as a late fee
