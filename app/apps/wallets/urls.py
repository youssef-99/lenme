# app/urls.py
from django.urls import path
from .views import WalletDetailView, DepositView, WithdrawView

app_name = 'wallets'

urlpatterns = [
    path('', WalletDetailView.as_view(), name='detail'),
    path('deposit/', DepositView.as_view(), name='deposit'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
]
