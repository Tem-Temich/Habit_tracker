from datetime import timedelta, time
from unittest.mock import patch

from django.utils import timezone
from habits.models import Habit


def _now_at(t: time):
    base = timezone.now()
    return base.replace(
        hour=t.hour, minute=t.minute, second=0, microsecond=0
    )


def _make_due_habit(*, user, t: time, periodicity: int = 1):
    now = _now_at(t)
    last_sent_at = now - timedelta(days=periodicity)

    return Habit.objects.create(
        user=user,
        place="home",
        time=t,
        action="do-it",
        is_pleasant=False,
        periodicity=periodicity,
        reward="reward",
        execution_time=60,
        is_public=False,
        last_sent_at=last_sent_at,
    )


def test_send_habit_reminder_due_updates_last_sent_at(auth_user):
    t = time(10, 30, 0)
    now = _now_at(t)
    habit = _make_due_habit(user=auth_user, t=t)

    with patch("telegram_bot.tasks.timezone.now", return_value=now), patch(
        "telegram_bot.tasks._send_telegram_message"
    ) as send_mock, patch(
        "telegram_bot.tasks.schedule_next_reminder_for_habit"
    ) as schedule_mock:
        from telegram_bot import tasks as tg_tasks

        tg_tasks.send_habit_reminder(habit.pk)

    send_mock.assert_called_once()
    # Один вызов идёт “вручную” в конце задачи, второй — из post_save signal.
    assert schedule_mock.call_count >= 1
    habit.refresh_from_db()
    assert habit.last_sent_at == now


def test_send_habit_reminder_uses_related_habit_action(
    auth_user,
):
    pleasant = Habit.objects.create(
        user=auth_user,
        place="spa",
        time=time(7, 0, 0),
        action="bath",
        is_pleasant=True,
        periodicity=1,
        reward=None,
        execution_time=30,
        is_public=False,
        last_sent_at=None,
    )

    t = time(10, 0, 0)
    now = _now_at(t)
    due_habit = Habit.objects.create(
        user=auth_user,
        place="home",
        time=t,
        action="walk",
        is_pleasant=False,
        periodicity=1,
        related_habit=pleasant,
        reward=None,
        execution_time=60,
        is_public=False,
        last_sent_at=now - timedelta(days=1),
    )

    with patch("telegram_bot.tasks.timezone.now", return_value=now), patch(
        "telegram_bot.tasks._send_telegram_message"
    ) as send_mock, patch(
        "telegram_bot.tasks.schedule_next_reminder_for_habit"
    ):
        from telegram_bot import tasks as tg_tasks

        tg_tasks.send_habit_reminder(due_habit.pk)

    message_text = send_mock.call_args.kwargs["text"]
    assert "bath" in message_text


def test_send_habit_reminder_not_due_schedules_next(auth_user):
    # last_sent_at ставим так, чтобы привычка не была “в минуту”.
    t = time(23, 0, 0)
    habit = Habit.objects.create(
        user=auth_user,
        place="home",
        time=t,
        action="late",
        is_pleasant=False,
        periodicity=7,
        reward="reward",
        execution_time=60,
        is_public=False,
        last_sent_at=None,
    )

    with patch(
        "telegram_bot.tasks.schedule_next_reminder_for_habit"
    ) as schedule_mock, patch(
        "telegram_bot.tasks.timezone.now"
    ) as now_mock:
        now_mock.return_value = _now_at(time(0, 0, 0))
        from telegram_bot import tasks as tg_tasks

        tg_tasks.send_habit_reminder(habit.pk)

    schedule_mock.assert_called_once()


def test_resync_due_habits_delays_only_due_habits(auth_user):
    from telegram_bot import tasks as tg_tasks

    t = time(10, 0, 0)
    now = _now_at(t)

    due_habit = Habit.objects.create(
        user=auth_user,
        place="home",
        time=t,
        action="do",
        is_pleasant=False,
        periodicity=1,
        reward="reward",
        execution_time=60,
        is_public=False,
        last_sent_at=now - timedelta(days=1),
    )
    not_due_habit = Habit.objects.create(
        user=auth_user,
        place="home",
        time=t,
        action="later",
        is_pleasant=False,
        periodicity=1,
        reward="reward",
        execution_time=60,
        is_public=False,
        last_sent_at=now,
    )

    with patch(
        "telegram_bot.tasks.timezone.now", return_value=now
    ), patch.object(tg_tasks.send_habit_reminder, "delay") as delay_mock:
        tg_tasks.resync_due_habits()

    delayed_ids = [call.args[0] for call in delay_mock.call_args_list]
    assert due_habit.pk in delayed_ids
    assert not_due_habit.pk not in delayed_ids

