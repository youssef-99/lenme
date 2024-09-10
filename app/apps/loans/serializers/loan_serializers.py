from rest_framework import serializers

from apps.loans.models.loan import Loan


class LoanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Loan
        fields = [
            'id',
            'borrower',
            'amount',
            'duration_months',
            'annual_interest_rate',
            'admin_fee',
            'lender',
            'funded_at',
            'status',
            'loan_offer'
        ]

