
from django import forms
from .models import Transaction
from django import forms
from .models import Budget

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

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "receipt": forms.ClearableFileInput(
                attrs={"accept": "image/*"}
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "Amount must be greater than zero."
            )

        return amount

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
        limit = self.cleaned_data["limit"]

        if limit <= 0:
            raise forms.ValidationError(
                "Your budget must be greater than zero."
            )

        return limit
