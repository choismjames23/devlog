from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """커스텀 유저 매니저 - 이메일을 username으로 사용"""

    def create_user(self, email, password=None, **extra_fields):
        """일반 유저 생성"""
        if not email:
            raise ValueError("이메일은 필수입니다.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """슈퍼유저 생성"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("슈퍼유저는 is_staff=True여야 합니다.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("슈퍼유저는 is_superuser=True여야 합니다.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """커스텀 유저 모델 - 이메일 기반 인증"""

    email = models.EmailField(
        unique=True, verbose_name="이메일", help_text="로그인에 사용되는 이메일 주소"
    )
    name = models.CharField(
        max_length=100, verbose_name="이름", help_text="사용자의 실명 또는 닉네임"
    )
    google_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name="구글 ID",
        help_text="구글 계정의 고유 ID",
    )
    is_active = models.BooleanField(
        default=True, verbose_name="활성 상태", help_text="계정 활성화 여부"
    )
    is_staff = models.BooleanField(
        default=False, verbose_name="스태프 권한", help_text="관리자 페이지 접근 권한"
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="가입일", help_text="계정 생성 날짜"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"
        db_table = "users"

    def __str__(self):
        return f"{self.name} ({self.email})"
