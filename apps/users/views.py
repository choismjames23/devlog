from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        id_token_str: str | None = request.data.get("id_token")
        if not id_token_str:
            return Response(
                {"detail": "id_token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Server misconfigured: GOOGLE_CLIENT_ID is not set"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            google_request = google_requests.Request()
            payload: Dict[str, Any] = id_token.verify_oauth2_token(
                id_token_str, google_request, settings.GOOGLE_CLIENT_ID
            )
        except Exception:
            return Response(
                {"detail": "Invalid Google ID token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email: str | None = payload.get("email")
        name: str | None = payload.get("name") or payload.get("given_name")
        google_sub: str | None = payload.get("sub")

        if not email or not google_sub:
            return Response(
                {"detail": "Token missing required claims"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": name or email.split("@")[0],
                "google_id": google_sub,
                "is_active": True,
                "created_at": timezone.now(),
            },
        )

        if not created and (not user.google_id):
            user.google_id = google_sub
            user.save(update_fields=["google_id"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
