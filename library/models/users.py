import re

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator


def validate_phone_number(value: str) -> None:
    if not re.fullmatch(
            pattern=r"^\+?\d{1,4}?[\s-]?(?:\(?\d{2,5}\)?[\s-]?)?\d{2,5}[\s-]?\d{2,5}[\s-]?\d{0,5}$",
            string=value
    ):
        raise ValidationError(
            "Invalid phone number. Please, try again."
        )


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        admin = "admin", "Admin"
        moderator = "moderator", "Moderator"
        lib_member = "lib_member", "Library Member"

    class Gender(models.TextChoices):
        male = "male", "Male"
        female = "female", "Female"
        other = "other", "Other"

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=80, unique=True)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    phone = models.CharField(
        max_length=25,
        unique=True,
        null=True,
        blank=True,
        validators=[
            validate_phone_number,
        ]
    )
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=15, choices=Role)
    gender = models.CharField(max_length=10, choices=Gender)
    age = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(10),
            MaxValueValidator(90)
        ]
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(
        default=timezone.now
    )

    # Исправление конфликта: явно переопределяем скрытые поля со своими related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='library_user_groups',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='library_user_permissions',
        related_query_name='user'
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "role", "gender"]


class Membership(models.Model):
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships'
    )