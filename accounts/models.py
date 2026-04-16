from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    telegram_chat_id = models.IntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=50, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email


# End of file
# EOF2
# EOF3