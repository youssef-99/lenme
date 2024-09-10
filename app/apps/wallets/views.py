from decimal import Decimal

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.views import APIView

from .models import Wallet
from .serializers import WalletSerializer, TransactionSerializer
from ..transfers import config
from ..transfers.models import Transfer


class WalletDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the wallet details of the authenticated user.",
        responses={
            200: WalletSerializer,
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            404: "Not Found - No wallet found for the authenticated user."
        },
    )
    def get(self, request):
        """
        Retrieve the wallet details of the authenticated user.
        """
        wallet = get_object_or_404(Wallet, user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class DepositView(APIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Deposit money into the authenticated user's wallet.",
        request_body=TransactionSerializer,
        responses={
            200: openapi.Response(
                description="Deposit successful, returning the updated balance.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'balance': openapi.Schema(type=openapi.TYPE_NUMBER, format='float')
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid amount or request data.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        if amount and Decimal(amount) > 0:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                wallet.deposit(Decimal(amount))

                # Create a Transfer record for the deposit
                Transfer.objects.create(
                    transfer_type=config.TRANSFER_TYPE_ADD_MONEY,
                    amount=float(amount),
                    user=request.user,
                    transfer_status=config.TRANSFER_STATUS_COMPLETED,
                )
                return Response({'balance': wallet.balance}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)


class WithdrawView(APIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Withdraw money from the authenticated user's wallet.",
        request_body=TransactionSerializer,
        responses={
            200: openapi.Response(
                description="Withdrawal successful, returning the updated balance.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'balance': openapi.Schema(type=openapi.TYPE_NUMBER, format='float')
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid amount, insufficient funds, or other error.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=request.user)
            try:
                wallet.withdraw(Decimal(amount))
                wallet.save()

                # Create a Transfer record for the withdrawal
                Transfer.objects.create(
                    transfer_type=config.TRANSFER_TYPE_WITHDRAWAL,
                    amount=float(amount),
                    user=request.user,
                    transfer_status=config.TRANSFER_STATUS_COMPLETED,
                )
                return Response({'balance': wallet.balance}, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
