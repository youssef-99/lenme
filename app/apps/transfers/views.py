from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Transfer
from .serializers import TransferSerializer


class TransferHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the transfer history for the authenticated user.",
        responses={
            200: openapi.Response(
                description="Transfer history retrieved successfully.",
                schema=TransferSerializer()
            ),
            401: openapi.Response(
                description="Unauthorized access."
            )
        },
    )
    def get(self, request, *args, **kwargs):
        # Fetch transfers related to the authenticated user
        transfers = Transfer.objects.filter(
            Q(user=request.user) |
            Q(to_account=request.user) |
            Q(from_account=request.user)
        ).order_by('-created')

        serializer = TransferSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
