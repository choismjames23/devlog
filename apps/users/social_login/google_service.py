from typing import Any, Dict

import requests
from django.conf import settings


class GoogleService:
    """Google OAuth 2.0 서비스 클래스"""

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @staticmethod
    def get_access_token(code: str) -> Dict[str, Any]:
        """
        Authorization code를 사용하여 Google access token을 가져옵니다.

        Args:
            code: Google OAuth authorization code

        Returns:
            Dict containing access_token, refresh_token, expires_in, etc.

        Raises:
            requests.RequestException: HTTP request 실패 시
            ValueError: 필수 설정값이 없을 때
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is not configured")
        if not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is not configured")
        if not settings.GOOGLE_REDIRECT_URI:
            raise ValueError("GOOGLE_REDIRECT_URI is not configured")

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        response = requests.post(GoogleService.TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        Google access token을 사용하여 사용자 정보를 가져옵니다.

        Args:
            access_token: Google OAuth access token

        Returns:
            Dict containing id, email, name, picture, etc.

        Raises:
            requests.RequestException: HTTP request 실패 시
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            GoogleService.USER_INFO_URL, headers=headers, timeout=10
        )
        response.raise_for_status()

        return response.json()
