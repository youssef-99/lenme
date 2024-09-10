from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.loans.models.loan_request import LoanRequest
from apps.users import config

User = get_user_model()


class CreateLoanRequestViewTests(APITestCase):

    def setUp(self):
        # Create a borrower user
        self.borrower = User.objects.create_user(
            email='user@borrower.com',
            username='borrower',
            password='borrowerpass',
            user_type=config.USER_TYPE_BORROWER
        )

        # Create a lender user
        self.lender = User.objects.create_user(
            email='user@lender.com',
            username='lender',
            password='lenderpass',
            user_type=config.USER_TYPE_LENDER
        )

        self.valid_payload = {
            'requested_amount': 5000,
            'repayment_period_months': 12
        }

        self.invalid_payload = {
            'requested_amount': -5000,  # Invalid negative amount
            'repayment_period_months': 12
        }

        self.url = reverse('api-v1:loans:requests:create')

    def test_create_loan_request_success_status_code(self):
        """
        Test that a borrower can successfully create a loan request.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.url, data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_loan_request_forbidden_for_lenders(self):
        """
        Test that lenders cannot create loan requests.
        """
        self.client.force_authenticate(user=self.lender)
        response = self.client.post(self.url, data=self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_loan_request_invalid_data(self):
        """
        Test that invalid data submission returns a 400 error.
        """
        self.client.force_authenticate(user=self.borrower)
        response = self.client.post(self.url, data=self.invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_loan_request_unauthenticated(self):
        """
        Test that unauthenticated users cannot create loan requests.
        """
        response = self.client.post(self.url, data=self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Ensure authentication is required

    def test_create_loan_request_missing_fields(self):
        """
        Test that missing required fields returns a 400 error.
        """
        self.client.force_authenticate(user=self.borrower)
        incomplete_payload = {
            'requested_amount': 5000,  # Missing other required fields
        }
        response = self.client.post(self.url, data=incomplete_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
