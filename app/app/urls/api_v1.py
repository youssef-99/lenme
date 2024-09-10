from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

app_name = 'api-v1'

urlpatterns = [
    path('users/', include('apps.users.urls.urls_api_v1', namespace='users')),
    path('wallets/', include('apps.wallets.urls', namespace='wallets')),
    path('transfers/', include('apps.transfers.urls', namespace='transfers')),
    path('loans/', include('apps.loans.urls', namespace='loans')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
]

# Define a security scheme for Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Lenme Task APIs",
        default_version='v1',
        description="API documentation for the Lenme lending platform.",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="youssefwilliam970@gmail.com"),
        license=openapi.License(name="Awesome License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns += [
    path("swagger-json/", schema_view.without_ui(cache_timeout=0), name="schema-json-api-v1"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui-api-v1"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc-api-v1"),
]
