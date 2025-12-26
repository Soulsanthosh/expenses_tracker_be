from django.db import models
from django.conf import settings


class TransactionType(models.TextChoices):
    GIVEN = "given", "Money Given"
    RECEIVED = "received", "Money Received"
    BORROWED = "borrowed", "Money Borrowed"
    RETURNED = "returned", "Money Returned"


class LendReturn(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lend_returns"
    )

    person_name = models.CharField(max_length=100)

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person_name} - {self.transaction_type} - ₹{self.amount}"
