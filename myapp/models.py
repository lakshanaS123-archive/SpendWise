import uuid
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


class FAQ(models.Model):
    """
    Database-backed FAQ system covering all SpendWise features.
    """
    CATEGORY_CHOICES = [
        ("Account", "Account & Security"),
        ("Transactions", "Transactions & Tracking"),
        ("Budgets", "Budgets & Limits"),
        ("Insights", "Insights & Analytics"),
        ("Learning", "Money Learning Centre"),
        ("Assistant", "Chat Assistant & Support"),
        ("General", "General"),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="General",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ErrorCode(models.Model):
    """
    SQL-backed error code registry explaining causes and recommended fixes.
    """
    SEVERITY_CHOICES = [
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    possible_causes = models.TextField()
    recommended_solution = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="ERROR",
    )
    category = models.CharField(max_length=50, default="Application")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Error Code"
        verbose_name_plural = "Error Codes"

    def __str__(self):
        return f"{self.code}: {self.title}"


class SupportTicket(models.Model):
    """
    Support ticket system for user assistance with complete CRUD operations.
    """
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]

    ticket_id = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    contact_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    related_error_code = models.CharField(max_length=30, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Generate short human-readable unique identifier
            random_suffix = uuid.uuid4().hex[:6].upper()
            self.ticket_id = f"SW-TKT-{random_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject} ({self.get_status_display()})"
