from django.urls import path

from .views import HealthView, LoginView, MetricsView, RegisterView, ValidateTokenView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/validate/", ValidateTokenView.as_view(), name="auth-validate"),
    path("health/", HealthView.as_view(), name="health"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
]
