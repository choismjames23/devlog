from typing import Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.social_login.google_service import GoogleService

User = get_user_model()


def IndexView(request: Request) -> Any:
    """로그인 페이지를 렌더링하는 뷰"""
    return render(
        request,
        "users/index.html",
        {"GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID},
    )


class GoogleAuthStartView(APIView):
    """Google OAuth 인증을 시작하는 뷰 (Step 1)"""

    permission_classes = [AllowAny]
    authentication_classes: list[Any] = []

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Any:
        """Google OAuth 동의 화면으로 리다이렉트"""
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        scope = "openid email profile"
        response_type = "code"
        access_type = "offline"

        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type={response_type}"
            f"&scope={scope.replace(' ', '%20')}"
            f"&access_type={access_type}"
            "&prompt=consent"
        )
        return redirect(auth_url)


class GoogleCallbackView(APIView):
    """Google OAuth 콜백을 처리하는 뷰 (Step 2)"""

    permission_classes = [AllowAny]
    authentication_classes: list[Any] = []

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Authorization code를 받아 JWT 토큰을 발급"""

        code = request.query_params.get("code")
        error = request.query_params.get("error")

        # OAuth 에러 처리
        if error:
            return Response(
                {"detail": f"Google OAuth error: {error}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code:
            return Response(
                {"detail": "authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1. Authorization code를 access token으로 교환
            token_data = GoogleService.get_access_token(code)
            access_token = token_data.get("access_token")
            if not access_token:
                return Response(
                    {"detail": "failed to get access token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Access token으로 사용자 정보 가져오기
            google_user = GoogleService.get_user_info(access_token)
            email = google_user.get("email")
            sub = (
                str(google_user.get("id"))
                if google_user.get("id") is not None
                else None
            )

            if not email or not sub:
                return Response(
                    {"detail": "google user info incomplete"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 3. 사용자 생성 또는 조회
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": google_user.get("name") or email.split("@")[0],
                    "google_id": sub,
                    "is_active": True,
                    "created_at": timezone.now(),
                },
            )

            # 기존 유저의 google_id 업데이트
            if not created and not user.google_id:
                user.google_id = sub
                user.save(update_fields=["google_id"])

            # 4. JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "email": email,
                    "name": user.name,
                    "created": created,
                },
                status=status.HTTP_200_OK,
            )

        except requests.RequestException as exc:
            # HTTP 요청 에러 (Google API 통신 실패)
            return Response(
                {"detail": f"Google API request failed: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError as exc:
            # 설정 에러 (환경 변수 누락)
            return Response(
                {"detail": f"Server configuration error: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as exc:
            # 기타 예상치 못한 에러
            return Response(
                {"detail": f"Unexpected error: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
