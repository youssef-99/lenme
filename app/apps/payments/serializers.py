from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'loan',
            'payment_amount',
            'payment_due_date',
            'payment_status',
            'payment_status_changed',
            'late_payment_fees_amount',
            'created',
            'modified',
            'is_late_payment'
        ]

