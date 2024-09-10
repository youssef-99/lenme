from django.urls import path, include

app_name = 'loans'

urlpatterns = [
    path('requests/', include('apps.loans.urls.loan_requests_urls', namespace='requests')),
    path('offers/', include('apps.loans.urls.loan_offers_urls', namespace='offers')),
]
