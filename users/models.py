
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from djchoices.choices import ChoiceItem, DjangoChoices


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(
        _("이름"), max_length=150, default=None, null=True, blank=True
    )
    first_name = None
    last_name = None
    email = models.EmailField(_("이메일"), unique=True)
    phone_number = models.CharField("전화번호", max_length=20, default=None, null=True)
    is_kakao = models.BooleanField("카카오 계정", default=False)
    is_facebook = models.BooleanField("페이스북 계정", default=False)
    is_google = models.BooleanField("구글 계정", default=False)
    done_tutorial = models.BooleanField("튜토리얼 완료 여부", default=False)
    staff_memo = models.TextField("관리자메모", default="", blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def formated_phone_number(self):
        if self.phone_number.startswith("+82"):
            # +82 01012345678
            return self.phone_number[:3] + " 0" + self.phone_number[3:]
        else:
            return self.phone_number

    def __str__(self):
        return "{}".format(self.username)


class CustomerManager(UserManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                (Q(is_kakao=True) | Q(is_facebook=True) | Q(is_google=True))
                & (Q(is_staff=False) & Q(is_superuser=False))
            )
        )


class Customer(CustomUser):
    class Meta:
        proxy = True

    objects = CustomerManager()
