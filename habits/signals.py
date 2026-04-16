from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Habit


@receiver(post_save, sender=Habit)
def schedule_habit_reminder_on_save(
    sender, instance: Habit, created: bool, **kwargs
):
    # Приятные привычки являются “вознаграждением”, а напоминания нужны
    # полезным.
    if instance.is_pleasant:
        return

    # Планируем следующую отправку напоминания.
    try:
        from telegram_bot.tasks import schedule_next_reminder_for_habit

        schedule_next_reminder_for_habit(instance.pk)
    except Exception:
        # Сигналы не должны ломать сохранение модели.
        pass


@receiver(post_delete, sender=Habit)
def schedule_habit_reminder_on_delete(sender, instance: Habit, **kwargs):
    # Ничего делать не нужно: scheduled task обработает отсутствие
    # привычки/изменения.
    return

# End of file
# EOF
