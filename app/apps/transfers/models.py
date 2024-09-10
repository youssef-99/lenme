from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.loans.models.loan import Loan
from apps.loans.models.loan_request import LoanRequest
from apps.transfers import config


class Transfer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transfers',
        help_text="The user associated with the transfer."
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The amount transferred."
    )
    transfer_type = models.CharField(
        max_length=20,
        choices=config.TRANSFER_TYPE_CHOICES,
        default=config.TRANSFER_TYPE_FUND_LOAN,
        help_text="The type of transfer."
    )
    transfer_status = models.CharField(
        max_length=20,
        choices=config.TRANSFER_STATUS_CHOICES,
        default=config.TRANSFER_STATUS_PENDING,
        help_text="The status of the transfer."
    )
    from_account = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Source of the transfer, can be a user wallet or external account."
    )
    to_account = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Destination of the transfer, can be a user wallet or external account."
    )
    loan_request = models.ForeignKey(
        LoanRequest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The loan request associated with the transfer."
    )
    loan = models.ForeignKey(
        Loan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The loan associated with the transfer."
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='borrower_transfers',
        help_text="The borrower associated with the transfer."
    )
    created = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when the transfer was created."
    )
    modified = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the transfer was last modified."
    )

    def __str__(self):
        return f"Transfer {self.id}: {self.transfer_type} - {self.amount} from {self.from_account} to {self.to_account}"
