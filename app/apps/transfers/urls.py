from django.urls import path

from apps.transfers.views import TransferHistoryView

app_name = 'transfers'

urlpatterns = [
    path('history/', TransferHistoryView.as_view(), name='history'),
]
