from decimal import Decimal
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Budget, SupportTicket, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "amount",
            "category",
            "date",
            "description",
            "receipt",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "receipt": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None or amount <= Decimal("0"):
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["month", "year", "limit"]
        widgets = {
            "month": forms.Select(),
            "year": forms.NumberInput(
                attrs={
                    "min": 2020,
                    "max": 2100,
                    "placeholder": "e.g. 2026",
                }
            ),
            "limit": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "e.g. 5000",
                }
            ),
        }

    def clean_limit(self):
        limit = self.cleaned_data.get("limit")
        if limit is None or limit <= Decimal("0"):
            raise forms.ValidationError("Your budget must be greater than zero.")
        return limit


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = [
            "subject",
            "description",
            "contact_email",
            "related_error_code",
            "priority",
        ]
        widgets = {
            "subject": forms.TextInput(
                attrs={"placeholder": "Brief summary of your question or issue"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Please provide full details of what occurred...",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={"placeholder": "your.email@example.com"}
            ),
            "related_error_code": forms.TextInput(
                attrs={"placeholder": "e.g. SW-FORM-001 (optional)"}
            ),
        }


class SupportTicketStaffForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["status", "priority", "resolution_notes"]
        widgets = {
            "resolution_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Enter resolution notes or troubleshooting advice for the user...",
                }
            ),
        }
