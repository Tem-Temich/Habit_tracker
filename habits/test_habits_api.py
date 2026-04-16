from datetime import time

from accounts.models import User
from habits.models import Habit


def _create_habit_payload(
    *,
    place: str,
    action: str,
    t: time,
    is_pleasant: bool,
    periodicity: int = 1,
    execution_time: int = 60,
    reward: str | None = None,
    related_habit: int | None = None,
    is_public: bool = False,
):
    payload = {
        "place": place,
        "time": t.strftime("%H:%M:%S"),
        "action": action,
        "is_pleasant": is_pleasant,
        "periodicity": periodicity,
        "execution_time": execution_time,
        "is_public": is_public,
        "reward": reward,
        "related_habit": related_habit,
    }
    # DRF сериализатор не всегда корректно обрабатывает null/пустые значения
    # для TextField, поэтому приводим None к отсутствию ключа.
    if reward is None:
        payload.pop("reward")
    if related_habit is None:
        payload.pop("related_habit")
    return payload


def test_anonymous_cant_access_private_habits_list(api_client):
    resp = api_client.get("/api/habits/")
    assert resp.status_code in (401, 403)


def test_create_and_list_habits_paginated(auth_client):
    for i in range(6):
        payload = _create_habit_payload(
            place=f"place-{i}",
            action=f"action-{i}",
            t=time(10, 0 + i % 10),
            is_pleasant=False,
            periodicity=1,
            execution_time=60,
            reward=f"reward-{i}",
            is_public=True,
        )
        resp = auth_client.post("/api/habits/", data=payload, format="json")
        assert resp.status_code == 201

    resp_page1 = auth_client.get("/api/habits/?page=1")
    assert resp_page1.status_code == 200
    assert resp_page1.data["count"] == 6
    assert len(resp_page1.data["results"]) == 5

    resp_page2 = auth_client.get("/api/habits/?page=2")
    assert resp_page2.status_code == 200
    assert len(resp_page2.data["results"]) == 1


def test_public_habits_list_is_read_only_for_anonymous(api_client, auth_user):
    # Создаём две привычки: одна публичная, другая нет.
    public_habit = Habit.objects.create(
        user=auth_user,
        place="public-place",
        time=time(12, 0, 0),
        action="public-action",
        is_pleasant=False,
        periodicity=1,
        reward="reward",
        execution_time=60,
        is_public=True,
    )
    Habit.objects.create(
        user=auth_user,
        place="private-place",
        time=time(13, 0, 0),
        action="private-action",
        is_pleasant=False,
        periodicity=1,
        reward="reward",
        execution_time=60,
        is_public=False,
    )

    resp = api_client.get("/api/habits/public/")
    assert resp.status_code == 200
    expected = (public_habit.action, public_habit.place)
    assert any(
        (item["action"], item["place"]) == expected
        for item in resp.data["results"]
    )

    # ReadOnlyModelViewSet: POST должен быть не доступен.
    resp_post = api_client.post(
        "/api/habits/public/",
        data={
            "place": "x",
            "time": "10:00:00",
            "action": "x",
            "is_pleasant": False,
            "periodicity": 1,
            "execution_time": 60,
        },
        format="json",
    )
    assert resp_post.status_code == 405


def test_cant_modify_other_users_habit(auth_client, auth_user):
    other_user = User.objects.create_user(
        email="other@example.com",
        username="other",
        password="strong-pass",
    )
    other_habit = Habit.objects.create(
        user=other_user,
        place="other-place",
        time=time(9, 30, 0),
        action="other-action",
        is_pleasant=False,
        periodicity=1,
        reward="reward",
        execution_time=60,
        is_public=False,
    )

    resp = auth_client.patch(
        f"/api/habits/{other_habit.id}/",
        data={"action": "hacked"},
        format="json",
    )
    assert resp.status_code in (403, 404)


def test_validators_reward_and_related_habit_mutually_exclusive(
    auth_client, auth_user
):
    pleasant = Habit.objects.create(
        user=auth_user,
        place="pleasant-place",
        time=time(8, 0, 0),
        action="pleasant-action",
        is_pleasant=True,
        periodicity=1,
        reward=None,
        execution_time=60,
        is_public=False,
    )

    payload = _create_habit_payload(
        place="place",
        action="useful-action",
        t=time(10, 0, 0),
        is_pleasant=False,
        periodicity=1,
        execution_time=60,
        reward="should-not-be-set",
        related_habit=pleasant.id,
    )
    resp = auth_client.post("/api/habits/", data=payload, format="json")
    assert resp.status_code == 400


def test_pleasant_habit_cannot_have_reward_or_related(
    auth_client, auth_user
):
    payload = _create_habit_payload(
        place="pleasant-place",
        action="pleasant-action",
        t=time(8, 0, 0),
        is_pleasant=True,
        reward="not-allowed",
    )
    resp = auth_client.post("/api/habits/", data=payload, format="json")
    assert resp.status_code == 400

