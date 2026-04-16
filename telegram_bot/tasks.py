import os
import urllib.parse
import urllib.request
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone


def _send_telegram_message(chat_id: int, text: str) -> None:
    """
    Отправка сообщения через Telegram Bot API (без внешних библиотек).
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text}
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        # Тело ответа не нужно, но прочитать полезно для корректной обработки.
        resp.read()


def _is_habit_due(habit, now) -> bool:
    if habit.is_pleasant:
        return False

    if not habit.user.telegram_chat_id:
        return False

    # Срабатываем ровно в минуту "Время выполнения".
    if habit.time.hour != now.hour or habit.time.minute != now.minute:
        return False

    if habit.last_sent_at is None:
        return True

    next_allowed_dt = habit.last_sent_at + timedelta(days=habit.periodicity)
    return now >= next_allowed_dt


def _compute_next_eta(habit, now=None):
    """
    Следующее время отправки напоминания.
    Логика:
    - если привычка ещё не выполнялась (last_sent_at == None) ->
      ближайшая "время выполнения"
      (сегодня, если ещё не наступило; иначе завтра)
    - иначе ->
      last_sent_at + periodicity дней с выставлением time-of-day из
      habit.time
    """
    now = now or timezone.now()
    scheduled_time = now.replace(
        hour=habit.time.hour,
        minute=habit.time.minute,
        second=0,
        microsecond=0,
    )

    if habit.last_sent_at is None:
        if scheduled_time > now:
            return scheduled_time

        # Если уже прошло начало минуты, но hour:minute совпадают —
        # отправляем в этой же минуте.
        if now.hour == habit.time.hour and now.minute == habit.time.minute:
            return now + timedelta(seconds=10)

        return scheduled_time + timedelta(days=1)

    next_dt = habit.last_sent_at + timedelta(days=habit.periodicity)
    next_dt = next_dt.replace(
        hour=habit.time.hour,
        minute=habit.time.minute,
        second=0,
        microsecond=0,
    )

    # На случай смены periodicity/time: сдвигаем вперёд пока время в прошлом.
    # (Кап защищает от бесконечного цикла при некорректных данных.)
    for _ in range(0, 370):
        if next_dt > now:
            return next_dt
        next_dt = next_dt + timedelta(days=habit.periodicity)

    return now + timedelta(minutes=1)


def schedule_next_reminder_for_habit(habit_id: int) -> None:
    """
    Планирует отправку ближайшего напоминания через Celery delayed tasks.
    """
    from habits.models import Habit  # локальный импорт, чтобы избежать циклов

    try:
        habit = Habit.objects.select_related("user").get(pk=habit_id)
    except Habit.DoesNotExist:
        return

    if habit.is_pleasant:
        return
    if not habit.user.telegram_chat_id:
        return

    eta = _compute_next_eta(habit)
    send_habit_reminder.apply_async(args=[habit_id], eta=eta)


@shared_task(ignore_result=True)
def send_habit_reminder(habit_id: int) -> None:
    from habits.models import Habit  # локальный импорт, чтобы избежать циклов

    try:
        habit = Habit.objects.select_related("user").get(pk=habit_id)
    except Habit.DoesNotExist:
        return

    now = timezone.now()

    if not _is_habit_due(habit, now):
        # Даже если задача вызвалась “не вовремя”, планируем следующую.
        schedule_next_reminder_for_habit(habit_id)
        return

    # Сообщение для пользователя.
    reward_text = None
    if habit.related_habit_id:
        # related_habit имеет признак приятной привычки
        # (валидируется сериализатором/моделью).
        reward_text = habit.related_habit.action
    elif habit.reward:
        reward_text = habit.reward

    when_text = habit.time.strftime("%H:%M")
    text = f"Напоминание! Я буду {habit.action} в {habit.place} в {when_text}."
    if habit.execution_time:
        text += f"\nНа выполнение: до {habit.execution_time} сек."
    if reward_text:
        text += f"\nПосле: {reward_text}"

    chat_id = habit.user.telegram_chat_id
    if not chat_id:
        return

    try:
        with transaction.atomic():
            _send_telegram_message(chat_id=chat_id, text=text)
            # Сохраняем время последнего выполнения,
            # чтобы соблюдать периодичность.
            habit.last_sent_at = now
            habit.save(update_fields=["last_sent_at"])
    except Exception:
        # Если Telegram недоступен — пробуем ещё раз позже (через планировщик).
        schedule_next_reminder_for_habit(habit_id)
        return

    # Планируем следующее напоминание.
    schedule_next_reminder_for_habit(habit_id)


@shared_task(ignore_result=True)
def resync_due_habits() -> None:
    """
    Периодическая синхронизация:
    находит “просроченные” или “текущие по времени” привычки и отправляет
    напоминания.
    Это страховка от перезапусков воркера/очереди.
    """
    from habits.models import Habit  # локальный импорт, чтобы избежать циклов

    now = timezone.now()
    # Ограничиваем выборку:
    # только полезные привычки с telegram_chat_id у пользователя.
    habits_qs = (
        Habit.objects.select_related("user")
        .filter(is_pleasant=False, user__telegram_chat_id__isnull=False)
    )

    for habit in habits_qs:
        if _is_habit_due(habit, now):
            # Делаем отправку “прямо сейчас”.
            send_habit_reminder.delay(habit.pk)


# End of file
# EOF
# EOF2

