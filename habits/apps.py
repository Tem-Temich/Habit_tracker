from django.apps import AppConfig


class HabitsConfig(AppConfig):
    name = 'habits'

    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Регистрируем сигналы приложения при старте Django.
        from . import signals  # noqa: F401
