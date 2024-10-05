from email.policy import default

from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(models.Model):
    username = models.CharField(max_length=40, unique=True)
    chat_id = models.BigIntegerField(unique=True)
    is_staff = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username}"


class Ad(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    location = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    user = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, db_column='user')
    phone = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} - {self.user} - {self.created_at}'

class SearchCriteria(models.Model):
    chat_id = models.ForeignKey(User, to_field='chat_id', on_delete=models.CASCADE, db_column='chat_id')
    keywords = ArrayField(ArrayField(models.CharField(max_length=40), default="{%%}", blank=True))
    min_price = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    max_price = models.DecimalField(max_digits=7, decimal_places=2, default=99999.99)

    def __str__(self):
        return f'{self.chat_id}'
