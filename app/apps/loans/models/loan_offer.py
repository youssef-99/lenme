from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.loans import config
from apps.loans.models.loan_request import LoanRequest

User = get_user_model()


class LoanOffer(models.Model):
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name='offers')
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_offers')
    offered_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="The amount offered by the lender.")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2,
                                        help_text="Annual interest rate offered by the lender (as a percentage).")
    total_repayable_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                                 help_text="Total amount to be repaid including interest.")
    offer_status = models.CharField(
        max_length=20,
        choices=config.OFFER_STATUS_CHOICES,
        default=config.OFFER_STATUS_PENDING,
        help_text="Status of the loan offer."
    )
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,
                                    help_text="Administrative fee for the loan offer.")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Loan Offer {self.id} by {self.lender.username} - Amount: {self.offered_amount} USD @ {self.interest_rate}%"

    def calculate_monthly_payment(self):
        """
        Calculates the monthly payment amount for the loan based on the loan amount, interest rate, and repayment period.
        Uses the formula for an amortizing loan payment:

        M = P [ r(1 + r)^n ] / [ (1 + r)^n – 1 ]

        Where:
        M = monthly payment
        P = principal loan amount (offered_amount)
        r = monthly interest rate (annual rate / 12)
        n = number of payments (repayment period in months)
        """
        P = float(self.offered_amount)
        annual_rate = float(self.interest_rate)
        r = annual_rate / 100 / 12  # Monthly interest rate
        n = self.loan_request.repayment_period_months  # Number of payments

        if r == 0:  # Handling the case of zero interest
            return P / n

        M = P * (r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
        return round(M, 2)

    def save(self, *args, **kwargs):
        if not self.admin_fee:
            self.admin_fee = settings.PROCESSING_FEE

        # Calculate the total repayable amount including interest
        if not self.total_repayable_amount:
            self.total_repayable_amount = (self.calculate_monthly_payment() *
                                           self.loan_request.repayment_period_months) \
                                          + (float(self.offered_amount) * float(self.admin_fee))
        super().save(*args, **kwargs)
