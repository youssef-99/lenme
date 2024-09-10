from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.loans.models.loan import Loan
from apps.loans.models.loan_offer import LoanOffer
from apps.loans.models.loan_request import LoanRequest
from apps.loans.serializers.loan_offers_serializers import LoanOfferSerializer
from apps.loans.serializers.loan_serializers import LoanSerializer
from apps.payments.models import Payment
from apps.transfers.models import Transfer
from apps.users import config as user_config
from apps.loans import config as loan_config
from apps.transfers import config as transfer_config
from apps.users.models import Lender, Borrower
from apps.wallets.models import Wallet


class CreateLoanOfferView(APIView):
    """
    Create a new loan offer for a specific loan request.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=LoanOfferSerializer,
        responses={
            201: openapi.Response(
                description="Loan offer created successfully",
                schema=LoanOfferSerializer
            ),
            400: openapi.Response(
                description="Bad request due to validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden for non-lenders",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            ),
            404: openapi.Response(
                description="Loan request not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        if request.user.user_type != user_config.USER_TYPE_LENDER:
            return Response({'error': 'You are not authorized to create a loan offer.'},
                            status=status.HTTP_403_FORBIDDEN)

        loan_request_id = request.data.get('loan_request')
        if not loan_request_id:
            return Response({'error': 'Loan request ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        loan_request = get_object_or_404(LoanRequest, id=loan_request_id, is_active=True)

        if request.user.wallet.balance < (float(loan_request.requested_amount) + (
                float(loan_request.requested_amount) * settings.PROCESSING_FEE)):
            return Response({
                'error': f'Insufficient funds you have to charge your balance to have {float(loan_request.requested_amount) + (float(loan_request.requested_amount) * settings.PROCESSING_FEE)} USD in your wallet'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoanOfferSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['lender'] = request.user
            loan_offer = serializer.save()
            return Response(LoanOfferSerializer(loan_offer).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoanOffersListView(APIView):
    """
    Retrieve loan offers based on user type.
    - If the user is a lender: lists their offered loan offers.
    - If the user is a borrower: lists the received loan offers.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve loan offers based on the user's role. Lenders will see their offered loan offers, while borrowers will see the loan offers they have received.",
        responses={
            200: openapi.Response(
                description="A list of loan offers.",
                schema=LoanOfferSerializer(many=True)
            ),
            403: openapi.Response(
                description="Permission denied, user is not authenticated.",
                examples={
                    'application/json': {
                        'detail': 'Authentication credentials were not provided.'
                    }
                }
            ),
            500: openapi.Response(
                description="Internal server error.",
                examples={
                    'application/json': {
                        'detail': 'Internal server error.'
                    }
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        # Check if user is a lender
        if user.user_type == user_config.USER_TYPE_LENDER:
            # List loan offers made by the lender
            offers = LoanOffer.objects.filter(lender=user)
            offers_type = 'offered'
        else:
            # List loan offers received by the borrower
            offers = LoanOffer.objects.filter(loan_request__borrower=user)
            offers_type = "received"

        serializer = LoanOfferSerializer(offers, many=True)
        return Response({
            'offers_type': offers_type,
            'offers': serializer.data
        }, status=status.HTTP_200_OK)


class AcceptRejectLoanOfferView(APIView):
    """
    Allows a borrower to accept or reject a loan offer.
    - If accepted: Marks the loan request as inactive, updates the offer status to accepted, and creates a loan.
    - If rejected: Updates the offer status to rejected.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Accept or Reject a Loan Offer",
        operation_description="Allows a borrower to accept or reject a loan offer.",
        responses={
            201: openapi.Response(
                description="Loan accepted successfully",
                schema=LoanSerializer
            ),
            200: openapi.Response(
                description="Loan offer rejected successfully"
            ),
            400: openapi.Response(
                description="Invalid action or request"
            ),
            403: openapi.Response(
                description="Unauthorized action"
            ),
            500: openapi.Response(
                description="Internal server error"
            )
        },
        manual_parameters=[
            openapi.Parameter('offer_id', openapi.IN_PATH, description="ID of the loan offer",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('action', openapi.IN_PATH, description="Action to perform (accept or reject)",
                              type=openapi.TYPE_STRING)
        ]
    )
    @transaction.atomic
    def post(self, request, offer_id, action, *args, **kwargs):
        # Get the loan offer
        loan_offer = get_object_or_404(LoanOffer, id=offer_id)

        # Check if the requesting user is the borrower of the loan request
        if loan_offer.loan_request.borrower != request.user:
            return Response({'error': 'You are not authorized to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

        # check id loan offer is not active
        if not loan_offer.loan_request.is_active:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'This loan is not available any more'})

        # Handle accept action
        if action == 'accept':
            lender = loan_offer.lender
            offered_amount = loan_offer.offered_amount
            admin_fee = loan_offer.admin_fee
            total_amount = offered_amount + (offered_amount * admin_fee)

            # Ensure the lender has sufficient balance
            with transaction.atomic():
                lender_wallet = Wallet.objects.select_for_update().get(user=lender)
                if lender_wallet.balance < total_amount:
                    return Response({'error': 'Insufficient funds in lender\'s wallet.'},
                                    status=status.HTTP_400_BAD_REQUEST)
                # Create the loan
                loan = Loan.objects.create(
                    borrower=request.user,
                    amount=offered_amount,
                    duration_months=loan_offer.loan_request.repayment_period_months,
                    annual_interest_rate=loan_offer.interest_rate,
                    admin_fee=loan_offer.admin_fee,
                    lender=lender,
                    funded_at=timezone.now(),
                    status=loan_config.FUNDED,
                    loan_offer=loan_offer
                )

                # Update lender and borrower balances
                lender_wallet.balance -= total_amount
                lender_wallet.save()

                borrower_wallet = Wallet.objects.select_for_update().get(user=request.user)
                borrower_wallet.balance += offered_amount
                borrower_wallet.save()

                # Create the transfer
                Transfer.objects.create(
                    user=lender,
                    amount=total_amount,
                    transfer_type=transfer_config.TRANSFER_TYPE_FUND_LOAN,
                    transfer_status=transfer_config.TRANSFER_STATUS_COMPLETED,
                    from_account=lender,
                    to_account=request.user,
                    loan_request=loan_offer.loan_request,
                    loan=loan,
                    borrower=request.user
                )

                # Create payment instances for each month
                payments = []
                monthly_payment_amount = loan_offer.calculate_monthly_payment()
                for month in range(loan.duration_months):
                    payment_due_date = timezone.now().date() + timezone.timedelta(days=(month + 1) * 30)
                    payments.append(Payment(
                        loan=loan,
                        payment_amount=monthly_payment_amount,
                        payment_due_date=payment_due_date
                    ))
                Payment.objects.bulk_create(payments)

                # Update the loan offer status
                loan_offer.offer_status = loan_config.OFFER_STATUS_ACCEPTED
                loan_offer.save()

                # update loan request to inactive
                loan_offer.loan_request.is_active = False
                loan_offer.loan_request.save()

                # reject the remaining loan offers
                remaining_offers = loan_offer.loan_request.offers.exclude(id=loan_offer.id)
                remaining_offers.update(offer_status=loan_config.OFFER_STATUS_REJECTED)

                # Serialize and return the created loan
                loan_serializer = LoanSerializer(loan)
                return Response(loan_serializer.data, status=status.HTTP_201_CREATED)

        # Handle reject action
        elif action == 'reject':
            # Update offer status to rejected
            loan_offer.offer_status = loan_config.OFFER_STATUS_REJECTED
            loan_offer.save()
            return Response({'message': 'Loan offer rejected successfully.'}, status=status.HTTP_200_OK)

        # If action is neither accept nor reject
        else:
            return Response({'error': 'Invalid action. Use "accept" or "reject".'}, status=status.HTTP_400_BAD_REQUEST)
