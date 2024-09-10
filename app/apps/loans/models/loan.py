from django.db import models
from decimal import Decimal

from apps.loans import config
from apps.loans.models.loan_offer import LoanOffer
from apps.users.models import Borrower, Lender


class Loan(models.Model):
    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name='borrowed_loans')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField(default=6)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    admin_fee = models.DecimalField(max_digits=5, decimal_places=2, default=3.75)
    lender = models.ForeignKey(Lender, null=True, blank=True, on_delete=models.SET_NULL, related_name='funded_loans')
    funded_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=config.LOAN_STATUS, default=config.PENDING)
    loan_offer = models.OneToOneField(LoanOffer, models.CASCADE, related_name='loan', null=True, blank=True)



