from rest_framework import serializers

from apps.loans.models.loan_request import LoanRequest


class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRequest
        fields = [
            'id',
            'borrower',
            'requested_amount',
            'repayment_period_months',
            'is_active',
            'created',
            'updated'
        ]
        read_only_fields = ['id', 'borrower', 'created', 'updated']

    def validate_requested_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Requested amount must be greater than zero.")
        return value

    def validate_repayment_period_months(self, value):
        if value <= 0:
            raise serializers.ValidationError("Repayment period must be greater than zero.")
        return value
