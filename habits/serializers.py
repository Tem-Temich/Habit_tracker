from rest_framework import serializers
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = (
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "execution_time",
            "is_public",
            "created_at",
            "updated_at",
            "last_sent_at",
        )
        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "last_sent_at",
        )

    def validate_execution_time(self, value):
        if value < 1 or value > 120:
            raise serializers.ValidationError(
                "Время выполнения привычки должно быть от 1 до 120 секунд."
            )
        return value

    def validate_periodicity(self, value):
        if value < 1 or value > 7:
            raise serializers.ValidationError(
                "Периодичность должна быть от 1 до 7 дней."
            )
        return value

    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(instance, "is_pleasant", None)
        )
        related_habit = attrs.get(
            "related_habit",
            getattr(instance, "related_habit", None)
        )
        reward = attrs.get("reward", getattr(instance, "reward", None))

        # Приводим пустые строки к None, чтобы валидация не зависела
        # от truthy/falsy.
        if isinstance(reward, str) and reward.strip() == "":
            reward = None

        if instance and related_habit and related_habit.pk == instance.pk:
            raise serializers.ValidationError({
                "related_habit": "Привычка не может ссылаться сама на себя."
            })

        if reward is not None and related_habit is not None:
            raise serializers.ValidationError({
                "reward": (
                    "Нельзя указывать вознаграждение вместе со связанной "
                    "привычкой."
                ),
                "related_habit": (
                    "Нельзя указывать связанную привычку вместе с "
                    "вознаграждением."
                ),
            })

        if is_pleasant and reward is not None:
            raise serializers.ValidationError({
                "reward": "У приятной привычки не может быть вознаграждения."
            })

        if is_pleasant and related_habit is not None:
            raise serializers.ValidationError({
                "related_habit": (
                    "У приятной привычки не может быть связанной "
                    "привычки."
                )
            })

        if related_habit is not None and not related_habit.is_pleasant:
            raise serializers.ValidationError({
                "related_habit": "Связанная привычка должна быть приятной."
            })

        return attrs


# End of file
# EOF
# EOF2
# EOF3