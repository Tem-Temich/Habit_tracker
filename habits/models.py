from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from config import settings


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    place = models.CharField(max_length=100, verbose_name="Место")
    time = models.TimeField(verbose_name="Время выполнения")
    action = models.CharField(max_length=150, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False, verbose_name="Приятная привычка или нет"
    )
    related_habit = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    periodicity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="целое число дней, default=1",
    )
    reward = models.TextField(null=True, blank=True, help_text="строка/текст")
    execution_time = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="целое число в секундах",
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Когда в последний раз отправлялось напоминание пользователю.
    # Для корректной логики напоминаний не должен обновляться автоматически.
    last_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.action

    def clean(self) -> None:
        super().clean()

        reward_value = self.reward if self.reward else None

        if self.related_habit and reward_value is not None:
            raise ValidationError(
                {
                    "reward": (
                        "Нельзя указывать вознаграждение вместе со "
                        "связанной привычкой."
                    ),
                }
            )

        if self.is_pleasant and reward_value is not None:
            raise ValidationError(
                {
                    "reward": (
                        "У приятной привычки не может быть "
                        "вознаграждения."
                    ),
                }
            )

        if self.is_pleasant and self.related_habit is not None:
            raise ValidationError(
                {
                    "related_habit": (
                        "У приятной привычки не может быть "
                        "связанной привычки."
                    ),
                }
            )

        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError(
                {
                    "related_habit": (
                        "Связанная привычка должна быть "
                        "приятной."
                    ),
                }
            )


# End of file
# EOF
# EOF2
# EOF3