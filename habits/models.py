from django.db import models

from accounts.models import User
from config import settings


# Create your models here.
class Habit(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    place=models.CharField(max_length=100,verbose_name="Место")
    time=models.TimeField(verbose_name='Время выполнения')
    action=models.CharField(max_length=150,verbose_name='Действие')
    is_pleasant = models.BooleanField(default=False, verbose_name="Приятная привычка или нет")
    related_habit=models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    periodicity=models.IntegerField(default=1,help_text='целое число дней, default=1')
    reward=models.TextField(null=True,blank=True,help_text='строка/текст')
    execution_time=models.IntegerField(help_text='целое число в секундах')
    is_public = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    last_sent_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.action