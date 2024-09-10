from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from apps.loans import config as loan_config
from apps.loans.models.loan import Loan
from apps.loans.models.loan_offer import LoanOffer
from apps.loans.models.loan_request import LoanRequest
from apps.payments.models import Payment
from apps.transfers.models import Transfer
from apps.users import config as user_config
from apps.transfers import config as transfer_config
from apps.wallets.models import Wallet

User = get_user_model()


class AcceptRejectLoanOfferViewTests(APITestCase):

    def setUp(self):
        # Create lender and borrower users
        self.lender = User.objects.create_user(
            username='lender',
            email='user@lender.com',
            password='lenderpass',
            user_type=user_config.USER_TYPE_LENDER,
        )
        self.lender_wallet = self.lender.wallet
        self.lender_wallet.balance = 10000
        self.lender_wallet.save()

        self.borrower = User.objects.create_user(
            username='borrower',
            email='user@borrower.com',
            password='borrowerpass',
            user_type=user_config.USER_TYPE_BORROWER
        )
        self.borrower_wallet = self.borrower.wallet
        self.borrower_wallet.balance = 500
        self.borrower_wallet.save()

        # Create an active loan request by the borrower
        self.loan_request = LoanRequest.objects.create(
            borrower=self.borrower,
            requested_amount=5000,
            repayment_period_months=12,
            is_active=True
        )

        # Create a loan offer for the loan request
        self.loan_offer = LoanOffer.objects.create(
            loan_request=self.loan_request,
            lender=self.lender,
            offered_amount=5000,
            interest_rate=5,
            admin_fee=0.1,  # 10% admin fee
            offer_status=loan_config.OFFER_STATUS_PENDING
        )

        self.accept_url = reverse('api-v1:loans:offers:respond', kwargs={'offer_id': self.loan_offer.id, 'action': 'accept'})
        self.reject_url = reverse('api-v1:loans:offers:respond', kwargs={'offer_id': self.loan_offer.id, 'action': 'reject'})
        self.invalid_url = reverse('api-v1:loans:offers:respond', kwargs={'offer_id': self.loan_offer.id, 'action': 'invalid'})

    def test_accept_loan_offer_success(self):
        """
        Test that a borrower can successfully accept a loan offer.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.accept_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Loan.objects.count(), 1)
        self.assertEqual(Transfer.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), self.loan_offer.loan_request.repayment_period_months)
        self.loan_offer.refresh_from_db()
        self.loan_request.refresh_from_db()
        self.assertEqual(self.loan_offer.offer_status, loan_config.OFFER_STATUS_ACCEPTED)
        self.assertFalse(self.loan_request.is_active)

    def test_reject_loan_offer_success(self):
        """
        Test that a borrower can successfully reject a loan offer.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.reject_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.loan_offer.refresh_from_db()
        self.assertEqual(self.loan_offer.offer_status, loan_config.OFFER_STATUS_REJECTED)
        self.assertEqual(response.data['message'], 'Loan offer rejected successfully.')

    def test_accept_loan_offer_unauthorized(self):
        """
        Test that someone other than the borrower cannot accept or reject the loan offer.
        """
        self.client.force_authenticate(user=self.lender)
        response = self.client.post(self.accept_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'You are not authorized to perform this action.')

    def test_accept_loan_offer_inactive_request(self):
        """
        Test that a loan offer cannot be accepted if the loan request is inactive.
        """
        self.loan_request.is_active = False
        self.loan_request.save()

        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.accept_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'This loan is not available any more')

    def test_accept_loan_offer_insufficient_funds_in_lender_wallet(self):
        """
        Test that accepting a loan offer fails if the lender has insufficient funds.
        """
        self.lender_wallet.balance = 1000  # Set balance lower than required amount
        self.lender_wallet.save()

        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.accept_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Insufficient funds in lender\'s wallet.')

    def test_invalid_action(self):
        """
        Test that an invalid action returns a 400 error.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.invalid_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid action. Use "accept" or "reject".')

