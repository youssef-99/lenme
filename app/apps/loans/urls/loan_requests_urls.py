from django.urls import path

from apps.loans.views.loan_request_views import CreateLoanRequestView, ListLoanRequestsView

app_name = 'requests'

urlpatterns = [
    path('', ListLoanRequestsView.as_view(), name='list'),
    path('create/', CreateLoanRequestView.as_view(), name='create'),
]
