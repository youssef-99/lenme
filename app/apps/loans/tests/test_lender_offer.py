from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.loans.models.loan_offer import LoanOffer
from apps.loans.models.loan_request import LoanRequest
from apps.loans.serializers.loan_requests_serializers import LoanRequestSerializer
from apps.users import config

User = get_user_model()


class CreateLoanOfferViewTests(APITestCase):

    def setUp(self):
        # Create lender and borrower users
        self.lender = User.objects.create_user(
            username='lender',
            email='user@lender.com',
            password='lenderpass',
            user_type=config.USER_TYPE_LENDER,
        )

        self.lender.wallet.balance = 10000
        self.lender.wallet.save()

        self.borrower = User.objects.create_user(
            username='borrower',
            email='user@borrower.com',
            password='borrowerpass',
            user_type=config.USER_TYPE_BORROWER
        )

        # Create an active loan request by the borrower
        self.loan_request = LoanRequest.objects.create(
            borrower=self.borrower,
            requested_amount=5000,
            repayment_period_months=12,
            is_active=True
        )

        # Payloads
        self.valid_payload = {
            'loan_request': self.loan_request.id,
            'interest_rate': 5,
            'offered_amount': 5000,
            'repayment_period_months': 12,
        }

        self.invalid_payload = {
            'loan_request': self.loan_request.id,
            'interest_rate': 'invalid',  # Invalid interest rate
            'repayment_period_months': 12,
        }

        self.url = reverse('api-v1:loans:offers:create')

    def test_create_loan_offer_success(self):
        """
        Test that a lender can successfully create a loan offer.
        """
        self.client.force_authenticate(user=self.lender)
        response = self.client.post(self.url, data=self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoanOffer.objects.count(), 1)
        self.assertEqual(response.data['loan_request'], dict(LoanRequestSerializer(instance=self.loan_request).data))
        self.assertEqual(response.data['lender'], self.lender.id)  # Assuming lender is returned in response

    def test_create_loan_offer_forbidden_for_borrowers(self):
        """
        Test that borrowers cannot create loan offers.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.url, data=self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'You are not authorized to create a loan offer.')
        self.assertEqual(LoanOffer.objects.count(), 0)  # Ensure no loan offers were created

    def test_create_loan_offer_loan_request_not_found(self):
        """
        Test that a 404 is returned when the loan request is not found.
        """
        self.client.force_authenticate(user=self.lender)
        self.valid_payload['loan_request'] = 9999  # Non-existent loan request ID
        response = self.client.post(self.url, data=self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(LoanOffer.objects.count(), 0)  # Ensure no loan offers were created

    def test_create_loan_offer_insufficient_funds(self):
        """
        Test that a 400 error is returned when the lender's funds are insufficient.
        """
        self.lender.wallet.balance = 1000  # Set a low balance to simulate insufficient funds
        self.lender.wallet.save()
        self.client.force_authenticate(user=self.lender)

        response = self.client.post(self.url, data=self.valid_payload, format='json')

        expected_message = f'Insufficient funds you have to charge your balance to have {float(self.loan_request.requested_amount) + (float(self.loan_request.requested_amount) * settings.PROCESSING_FEE)} USD in your wallet'

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], expected_message)
        self.assertEqual(LoanOffer.objects.count(), 0)  # Ensure no loan offers were created

    def test_create_loan_offer_invalid_data(self):
        """
        Test that invalid data submission returns a 400 error.
        """
        self.client.force_authenticate(user=self.lender)
        response = self.client.post(self.url, data=self.invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('interest_rate', response.data)  # Check if the error is related to the 'interest_rate' field
        self.assertEqual(LoanOffer.objects.count(), 0)  # Ensure no loan offers were created

    def test_create_loan_offer_missing_loan_request_id(self):
        """
        Test that missing the loan request ID returns a 400 error.
        """
        self.client.force_authenticate(user=self.lender)
        payload_without_loan_request = {
            'interest_rate': 5,
            'repayment_period_in_months': 12,
        }
        response = self.client.post(self.url, data=payload_without_loan_request, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Loan request ID is required.')
        self.assertEqual(LoanOffer.objects.count(), 0)  # Ensure no loan offers were created
