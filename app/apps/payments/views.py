from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.loans import config as loan_config
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from . import config
from apps.transfers import config as transfers_config
from .models import Payment
from .serializers import PaymentSerializer
from ..transfers.models import Transfer


class ListPaymentsView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all payments made by the borrower",
        responses={
            200: openapi.Response(description="A list of payments", schema=PaymentSerializer(many=True)),
            401: openapi.Response(description="Unauthorized access")
        }
    )
    def get_queryset(self):
        # Filter payments by the authenticated borrower
        return Payment.objects.filter(~Q(payment_status=config.PAYMENT_STATUS_PAID), loan__borrower=self.request.user)


class PayMonthlyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Allow borrower to make a monthly payment",
        responses={
            200: openapi.Response(description="Payment successful", schema=PaymentSerializer),
            400: openapi.Response(description="Invalid data or payment amount"),
            404: openapi.Response(description="Loan or payment not found")
        }
    )
    def post(self, request, pk, *args, **kwargs):
        with transaction.atomic():
            # Lock the payment object and related loan object
            payment = get_object_or_404(Payment.objects.select_for_update(), id=pk)
            loan = payment.loan

            # Validate payment amount
            if request.user.wallet.balance < payment.payment_amount:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)
            elif payment.payment_status == config.PAYMENT_STATUS_PAID:
                return Response({'error': 'This payment is already paid'}, status=status.HTTP_400_BAD_REQUEST)

            # Update borrower and lender accounts
            request.user.wallet.balance -= payment.payment_amount
            request.user.wallet.save()

            payment.loan.lender.wallet.balance += payment.payment_amount
            payment.loan.lender.wallet.save()

            # Update payment status
            payment.payment_status = config.PAYMENT_STATUS_PAID
            payment.save()

            # Create transfer records
            Transfer.objects.create(
                user=request.user,
                amount=payment.payment_amount,
                transfer_status=transfers_config.TRANSFER_TYPE_MONTHLY_PAYMENT,
                loan=payment.loan,
                to_account=payment.loan.lender,
            )

            # Update the loan status
            remaining_payments = Payment.objects.filter(~Q(payment_status=config.PAYMENT_STATUS_PAID), loan=loan)
            if not remaining_payments.exists():
                loan.status = loan_config.COMPLETED
                loan.save()

            # Serialize and return the payment
            payment_serializer = PaymentSerializer(payment)
            return Response(payment_serializer.data, status=status.HTTP_200_OK)
