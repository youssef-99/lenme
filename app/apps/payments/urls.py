from django.urls import path
from .views import PayMonthlyPaymentView, ListPaymentsView

app_name = 'payments'

urlpatterns = [
    path('', ListPaymentsView.as_view(), name='list'),
    path('<int:pk>/', PayMonthlyPaymentView.as_view(), name='pay-monthly-payment'),
]
