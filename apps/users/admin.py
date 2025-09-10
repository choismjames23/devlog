from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 유저 모델을 위한 관리자 페이지 설정"""

    # 목록 페이지에서 보여줄 필드들
    list_display = ("email", "name", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser", "created_at")
    search_fields = ("email", "name", "google_id")
    ordering = ("-created_at",)

    # 유저 상세 페이지 필드 구성
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("개인 정보"), {"fields": ("name", "google_id")}),
        (
            _("권한"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("중요한 날짜"), {"fields": ("last_login", "created_at")}),
    )

    # 유저 추가 페이지 필드 구성
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2"),
            },
        ),
    )

    # 읽기 전용 필드
    readonly_fields = ("created_at", "last_login")
