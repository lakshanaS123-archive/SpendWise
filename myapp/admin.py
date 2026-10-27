
from django.contrib import admin
from .models import Transaction, Budget


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "transaction_type",
        "amount",
        "category",
        "date",
    )

    list_filter = ("transaction_type", "category", "date")
    search_fields = ("user__username", "description")
    list_per_page = 20


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "limit")
    list_filter = ("month", "year")
    search_fields = ("user__username",)
