from rest_framework import serializers

from apps.loans.models.loan_offer import LoanOffer
from apps.loans.serializers.loan_requests_serializers import LoanRequestSerializer


class LoanOfferSerializer(serializers.ModelSerializer):
    monthly_payment = serializers.DecimalField(source='calculate_monthly_payment', decimal_places=2, max_digits=10,
                                               read_only=True)

    class Meta:
        model = LoanOffer
        fields = [
            'id',
            'loan_request',
            'lender',
            'interest_rate',
            'offered_amount',
            'offer_status',
            'total_repayable_amount',
            'monthly_payment',
            'admin_fee',
            'created_at',
        ]
        read_only_fields = ['id', 'lender', 'created_at', 'offer_status', 'total_repayable_amount', 'monthly_payment', 'admin_fee']

    def validate(self, data):
        """
        Custom validation to ensure the offer amount does not exceed the requested amount
        and to validate the interest rate.
        """
        loan_request = data.get('loan_request')
        offer_amount = data.get('offered_amount')

        if offer_amount <= 0:
            raise serializers.ValidationError("Offer amount must be greater than zero.")

        # Ensure the offer amount does not exceed the requested amount
        if loan_request and offer_amount > loan_request.requested_amount:
            raise serializers.ValidationError("Offer amount cannot exceed the requested loan amount.")

        return data

    def validate_interest_rate(self, value):
        """
        Validate that the interest rate is a positive value.
        """
        if value <= 0:
            raise serializers.ValidationError("Interest rate must be greater than zero.")
        return value

    def to_representation(self, instance):
        """
        Custom representation to include detailed information about the loan request.
        """
        representation = super().to_representation(instance)
        representation['loan_request'] = LoanRequestSerializer(instance=instance.loan_request).data
        return representation
