from django.conf import settings
from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.loans.models.loan_request import LoanRequest
from apps.loans.serializers.loan_requests_serializers import LoanRequestSerializer
from apps.users import config


class CreateLoanRequestView(APIView):
    """
    Create a new loan request.
    """
    @swagger_auto_schema(
        request_body=LoanRequestSerializer,
        responses={
            201: openapi.Response(
                description="Loan request created successfully",
                schema=LoanRequestSerializer
            ),
            400: openapi.Response(
                description="Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden for lenders",
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
        if request.user.user_type == config.USER_TYPE_LENDER:
            return Response({'error': 'You cannot perform this action as a lender'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LoanRequestSerializer(data=request.data)
        if serializer.is_valid():
            loan_request = serializer.save(borrower=request.user)
            return Response(LoanRequestSerializer(loan_request).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListLoanRequestsView(APIView):
    """
    List all loan requests available for lenders.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="List of loan requests",
                schema=LoanRequestSerializer()
            ),
            403: openapi.Response(
                description="Forbidden for non-lenders",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        if request.user.user_type != config.USER_TYPE_LENDER:
            return Response({'error': 'You are not authorized to view loan requests.'},
                            status=status.HTTP_403_FORBIDDEN)

        loan_requests = cache.get(settings.ACTIVE_LOAN_REQUESTS_CACHE_KEY)

        if loan_requests is None:
            loan_requests = LoanRequest.objects.filter(is_active=True)
            cache.set(settings.ACTIVE_LOAN_REQUESTS_CACHE_KEY, loan_requests, timeout=settings.CACHE_TIMEOUT)

        serializer = LoanRequestSerializer(loan_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
