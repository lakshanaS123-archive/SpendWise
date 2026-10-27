
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Transaction(models.Model):

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

    TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    CATEGORY_CHOICES = [
        ("Food", "Food"),
        ("Travel", "Travel"),
        ("Shopping", "Shopping"),
        ("Education", "Education"),
        ("Bills", "Bills"),
        ("Health", "Health"),
        ("Entertainment", "Entertainment"),
        ("Salary", "Salary"),
        ("Allowance", "Allowance"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="Other",
    )

    date = models.DateField(default=timezone.localdate)

    description = models.CharField(
        max_length=250,
        blank=True,
    )
    receipt = models.ImageField(
    upload_to="receipts/",
    blank=True,
    null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} - {self.category}"


class Budget(models.Model):

    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
    )

    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)

    year = models.PositiveSmallIntegerField()

    limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "month", "year"],
                name="unique_user_month_budget",
            )
        ]
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.user} - {self.get_month_display()} {self.year}"
