from django.urls import path

from .views import GoogleAuthStartView, GoogleCallbackView

urlpatterns = [
    # Google OAuth 2.0 Authorization Code Flow
    path("auth/login/google/", GoogleAuthStartView.as_view(), name="google-auth-start"),
    path(
        "auth/login/google/callback/",
        GoogleCallbackView.as_view(),
        name="google-auth-callback",
    ),
]
