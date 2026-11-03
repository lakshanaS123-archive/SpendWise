from django.contrib import admin
from .models import Budget, ErrorCode, FAQ, SupportTicket, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "transaction_type",
        "amount",
        "category",
        "date",
        "created_at",
    )
    list_filter = ("transaction_type", "category", "date")
    search_fields = ("user__username", "description")
    list_per_page = 25


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "limit")
    list_filter = ("month", "year")
    search_fields = ("user__username",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "category", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    list_editable = ("is_active",)
    list_per_page = 20


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "severity",
        "category",
        "is_active",
        "updated_at",
    )
    list_filter = ("severity", "category", "is_active")
    search_fields = ("code", "title", "description", "recommended_solution")
    list_editable = ("is_active",)
    list_per_page = 20


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_id",
        "user",
        "subject",
        "priority",
        "status",
        "related_error_code",
        "created_at",
    )
    list_filter = ("status", "priority", "created_at")
    search_fields = (
        "ticket_id",
        "user__username",
        "subject",
        "description",
        "related_error_code",
    )
    list_editable = ("status", "priority")
    readonly_fields = ("ticket_id", "created_at", "updated_at")
    list_per_page = 25
