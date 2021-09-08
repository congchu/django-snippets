
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
        _("카카오톡 이름"), max_length=150, default=None, null=True, blank=True
    )
    reservation_username = models.CharField(
        _("예약된 이름"), max_length=150, default=None, null=True, blank=True
    )
    first_name = None
    last_name = None
    email = models.EmailField(_("이메일"), unique=True)
    phone_number = models.CharField("전화번호", max_length=20, default=None, null=True)
    is_kakao = models.BooleanField("카카오 계정", default=False)
    is_facebook = models.BooleanField("페이스북 계정", default=False)
    is_google = models.BooleanField("구글 계정", default=False)
    is_teacher = models.BooleanField("선생님", default=False)
    is_operator = models.BooleanField("운영자", default=False)
    done_tutorial = models.BooleanField("튜토리얼 완료 여부", default=False)
    postcode = models.CharField(
        "우편번호", max_length=10, default=None, null=True, blank=True
    )
    address = models.CharField(
        "주소", max_length=300, default=None, null=True, blank=True
    )
    teacher_group = models.ForeignKey(
        "TeacherGroup", on_delete=models.SET_NULL, null=True, verbose_name="그룹"
    )
    voucher = models.ForeignKey(
        "Voucher", on_delete=models.SET_NULL, null=True, verbose_name="바우처", related_name="user"
    )
    
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

    @property
    def taken_class_count(self):
        return self.classreservation_set.all().filter(status="reserved").count()

    def withdraw(self):
        self.username = "탈퇴한유저"
        self.reservation_username = "-"
        self.email = f"deleted{self.id}@thelapis.io"
        self.password = "-"
        self.phone_number = "-"
        self.address = None
        self.postcode = None
        self.save()

    def __str__(self):
        return "{}".format(self.username)


class TeacherGroup(TimeStampedModel):
    name = models.CharField("그룹", max_length=30, blank=True, null=True, default=None)

    def __str__(self):
        return self.name


class StaffManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(is_staff=True) | Q(is_superuser=True))


class Staff(CustomUser):
    class Meta:
        proxy = True

    objects = StaffManager()


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


class TeacherManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_teacher=True)


class Teacher(CustomUser):
    class Meta:
        proxy = True

    objects = TeacherManager()

    def __str__(self):
        return "{}".format(self.username)


class OperatorManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_operator=True)


class Operator(CustomUser):
    class Meta:
        proxy = True

    objects = OperatorManager()

    def __str__(self):
        return "{}".format(self.username)


class MessageToken(TimeStampedModel):
    user = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="message_token"
    )
    fcm_token = models.TextField(unique=True)


class Voucher(TimeStampedModel):
    """ Voucher Model Definition """
    count = models.IntegerField("수강권 잔여 갯수", default=0)
    start_date = models.DateField("시작일", default=None, blank=True, null=True)
    end_date = models.DateField("만료일", default=None, blank=True, null=True)
    last_purchase_date = models.DateField("마지막 이용권 구매일", default=None, blank=True, null=True)
    last_valid_days = models.IntegerField("마지막 이용권 사용 기간", default=7, null=True)
    last_product_count = models.IntegerField("마지막 이용권 갯수", default=0, null=True)

    def __str__(self):
        if self.start_date:
            return f"{self.count}개 ({self.start_date}~{self.end_date})"
        else:
            return f"{self.count}개 (기간 없음)"

    
class VoucherHistory(TimeStampedModel):
    """ Voucher Change History Model Definition """ 
    class TypeChoices(DjangoChoices):
        voucher_add = ChoiceItem("voucher_add", "수강권 추가")
        voucher_refund = ChoiceItem("voucher_refund", "수강권 환불")
        voucher_expiration = ChoiceItem("voucher_expiration", "수강권 만료")
        class_used = ChoiceItem("class_used", "수업 예약")
        class_cancel = ChoiceItem("class_cancel", "수업 예약 취소")
        change_date = ChoiceItem("change_date", "기간 변경")

    user = models.ForeignKey(CustomUser, related_name="voucher_history", on_delete=models.CASCADE)
    type = models.CharField("변경 타입", choices=TypeChoices,max_length=20, default=None, null=True)
    name  = models.CharField("이름", default=None, null=True, max_length=60,  help_text="변경 내용. 유저에게 보여지는 부분입니다.")
    count = models.IntegerField("적용 갯수", default=0, help_text="수강권 만료, 수업 예약/취소인 경우 자동으로 계산됩니다(0으로 작성)." )
    applied_count = models.IntegerField("적용후 갯수", default=0,  help_text="수강권 만료, 수업 예약/취소인 경우 자동으로 계산됩니다 (0으로 작성)." )
    applied_date =  models.CharField("적용후 기간", default=None, null=True, max_length=60)

    def type_display_name (self):
        return dict(VoucherHistory.TypeChoices).get(self.type)

    def __str__(self):
        type = dict(VoucherHistory.TypeChoices).get(self.type)
        return f"{self.user.username}-{type}/{self.name}"
    
    



