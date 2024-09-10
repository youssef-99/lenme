from rest_framework import serializers
from .models import Transfer


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['id', 'transfer_type', 'amount', 'loan_request_id', 'loan_id',
                  'borrower_id', 'from_account', 'to_account', 'created']
