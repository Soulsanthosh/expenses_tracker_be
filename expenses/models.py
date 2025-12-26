from django.db import models
from django.conf import settings

class expenses(models.Model):

    EXPENSES_CHOICES = [
        ('rent', 'Rent'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('shopping', 'Shopping'),
        ('utilities', 'Utilities'),
        ('entertainment', 'Entertainment'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses" 
    )
    date = models.DateField(auto_now_add=True)
    expenses_type = models.CharField(choices=EXPENSES_CHOICES)
    amount = models.CharField(max_length=100, null=False)
    note = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.expenses_type