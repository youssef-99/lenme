from django.urls import path

from apps.loans.views.loan_offers_views import CreateLoanOfferView, LoanOffersListView, AcceptRejectLoanOfferView

app_name = 'offers'

urlpatterns = [
    path('', LoanOffersListView.as_view(), name='list'),
    path('create/', CreateLoanOfferView.as_view(), name='create'),
    path('<int:offer_id>/<str:action>/', AcceptRejectLoanOfferView.as_view(),
         name='respond'),

]
