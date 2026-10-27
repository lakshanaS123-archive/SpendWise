
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from calendar import month_abbr
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import Transaction

from .forms import BudgetForm, RegistrationForm, TransactionForm
from .models import Budget, Transaction


def home(request):
    return render(request, "index.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Your SpendWise account has been created!",
            )
            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})


@login_required
def add_transaction(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            messages.success(
                request,
                "Transaction saved successfully!",
            )
            return redirect("transaction_list")
    else:
        form = TransactionForm()

    return render(
        request,
        "transaction_form.html",
        {"form": form},
    )


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user)

    search = request.GET.get("q", "").strip()
    transaction_type = request.GET.get("type", "")
    category = request.GET.get("category", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search)
            | Q(category__icontains=search)
        )

    if transaction_type in [
        Transaction.INCOME,
        Transaction.EXPENSE,
    ]:
        transactions = transactions.filter(
            transaction_type=transaction_type
        )

    valid_categories = dict(Transaction.CATEGORY_CHOICES)

    if category in valid_categories:
        transactions = transactions.filter(category=category)

    if start_date:
        transactions = transactions.filter(date__gte=start_date)

    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    paginator = Paginator(transactions, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "transactions": page_obj,
        "page_obj": page_obj,
        "search": search,
        "selected_type": transaction_type,
        "selected_category": category,
        "start_date": start_date,
        "end_date": end_date,
        "categories": Transaction.CATEGORY_CHOICES,
    }

    return render(request, "transactions.html", context)


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = TransactionForm(
            request.POST,
            request.FILES,
            instance=transaction,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Transaction updated successfully!",
            )
            return redirect("transaction_list")
    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        "transaction_form.html",
        {
            "form": form,
            "editing": True,
        },
    )


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        transaction.delete()
        messages.success(
            request,
            "Transaction deleted successfully!",
        )
        return redirect("transaction_list")

    return render(
        request,
        "confirm_delete.html",
        {"transaction": transaction},
    )


@login_required
def dashboard(request):
    today = timezone.localdate()

    user_transactions = Transaction.objects.filter(
        user=request.user,
    )

    monthly_transactions = user_transactions.filter(
        date__year=today.year,
        date__month=today.month,
    )

    def total_for(queryset):
        return (
            queryset.aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    total_income = total_for(
        user_transactions.filter(
            transaction_type=Transaction.INCOME,
        )
    )

    total_expenses = total_for(
        user_transactions.filter(
            transaction_type=Transaction.EXPENSE,
        )
    )

    monthly_income = total_for(
        monthly_transactions.filter(
            transaction_type=Transaction.INCOME,
        )
    )

    monthly_expenses = total_for(
        monthly_transactions.filter(
            transaction_type=Transaction.EXPENSE,
        )
    )

    current_budget = Budget.objects.filter(
        user=request.user,
        month=today.month,
        year=today.year,
    ).first()

    budget_remaining = None
    budget_percentage = 0
    budget_progress = 0
    budget_status = "No budget set"
    budget_exceeded = Decimal("0.00")

    if current_budget:
        budget_remaining = current_budget.limit - monthly_expenses

        budget_percentage = float(
            monthly_expenses / current_budget.limit * 100
        )

        budget_progress = min(budget_percentage, 100)

        if budget_remaining < 0:
            budget_status = "Over budget"
            budget_exceeded = abs(budget_remaining)
        elif budget_percentage >= 80:
            budget_status = "Almost at limit"
        else:
            budget_status = "On track"

    recent_transactions = user_transactions.order_by(
        "-date",
        "-created_at",
    )[:5]

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_balance": monthly_income - monthly_expenses,
        "recent_transactions": recent_transactions,
        "current_month": today.strftime("%B %Y"),
        "current_budget": current_budget,
        "budget_spent": monthly_expenses,
        "budget_remaining": budget_remaining,
        "budget_percentage": round(budget_percentage, 1),
        "budget_progress": round(budget_progress, 1),
        "budget_status": budget_status,
        "budget_exceeded": budget_exceeded,
    }

    return render(request, "dashboard.html", context)


@login_required
def budgets(request):
    today = timezone.localdate()

    if request.method == "POST":
        form = BudgetForm(request.POST)

        if form.is_valid():
            month = form.cleaned_data["month"]
            year = form.cleaned_data["year"]
            limit = form.cleaned_data["limit"]

            Budget.objects.update_or_create(
                user=request.user,
                month=month,
                year=year,
                defaults={"limit": limit},
            )

            messages.success(
                request,
                "Monthly budget saved successfully!",
            )
            return redirect("budgets")
    else:
        form = BudgetForm(
            initial={
                "month": today.month,
                "year": today.year,
            }
        )

    user_budgets = Budget.objects.filter(user=request.user)
    budget_items = []

    for budget in user_budgets:
        spent = (
            Transaction.objects.filter(
                user=request.user,
                transaction_type=Transaction.EXPENSE,
                date__year=budget.year,
                date__month=budget.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        remaining = budget.limit - spent
        percentage = float(spent / budget.limit * 100)
        progress = min(percentage, 100)

        if remaining < 0:
            status = "Over budget"
        elif percentage >= 80:
            status = "Almost at limit"
        else:
            status = "On track"

        budget_items.append({
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "exceeded": abs(remaining) if remaining < 0 else Decimal("0.00"),
            "percentage": round(percentage, 1),
            "progress": round(progress, 1),
            "status": status,
        })

    current_budget = next(
        (
            item for item in budget_items
            if item["budget"].month == today.month
            and item["budget"].year == today.year
        ),
        None,
    )

    return render(
        request,
        "budgets.html",
        {
            "form": form,
            "budget_items": budget_items,
            "current_budget": current_budget,
            "current_month": today.strftime("%B %Y"),
        },
    )

@login_required
def insights(request):
    today = timezone.localdate()

    transactions = Transaction.objects.filter(
        user=request.user
    )

    # Expense totals grouped by category.
    category_rows = (
        transactions.filter(
            transaction_type=Transaction.EXPENSE
        )
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    category_labels = [
        row["category"] for row in category_rows
    ]
    category_values = [
        float(row["total"]) for row in category_rows
    ]

    # Income and expenses for the latest six calendar months.
    month_labels = []
    monthly_income_values = []
    monthly_expense_values = []

    for offset in range(5, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        year = month_index // 12
        month = month_index % 12 + 1

        month_labels.append(
            f"{month_abbr[month]} {year}"
        )

        month_transactions = transactions.filter(
            date__year=year,
            date__month=month,
        )

        income = (
            month_transactions.filter(
                transaction_type=Transaction.INCOME
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        expenses = (
            month_transactions.filter(
                transaction_type=Transaction.EXPENSE
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        monthly_income_values.append(float(income))
        monthly_expense_values.append(float(expenses))

    total_income = (
        transactions.filter(
            transaction_type=Transaction.INCOME
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    total_expenses = (
        transactions.filter(
            transaction_type=Transaction.EXPENSE
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return render(
        request,
        "insights.html",
        {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": total_income - total_expenses,
            "category_labels": category_labels,
            "category_values": category_values,
            "month_labels": month_labels,
            "monthly_income_values": monthly_income_values,
            "monthly_expense_values": monthly_expense_values,
        },
    )


def learning(request):
    lessons = [
        {
            "id": "budgeting",
            "title": "Budgeting basics",
            "icon": "🧮",
            "duration": "3 min",
            "summary": "Give every rupee a purpose before spending it.",
            "content": (
                "A budget is a plan for your money. Start by listing "
                "your income, fixed expenses, variable expenses, and "
                "savings. Set realistic limits for categories such as "
                "food, travel, shopping, and entertainment. Compare "
                "your actual spending with your plan every week. "
                "A budget is a guide, not a punishment."
            ),
            "tip": (
                "Start with last month's actual expenses and choose "
                "one category where you can spend less."
            ),
        },
        {
            "id": "saving",
            "title": "Saving consistently",
            "icon": "🐷",
            "duration": "3 min",
            "summary": "Build a saving habit, even with a small amount.",
            "content": (
                "Saving means keeping part of your money for a future "
                "need. Choose a realistic amount after accounting for "
                "essential expenses. Keep emergency savings separate "
                "from money meant for shopping or entertainment. "
                "Consistency matters more than starting with a large "
                "amount. Never assume that an investment is guaranteed "
                "to grow."
            ),
            "tip": (
                "Set a small weekly saving target and track whether "
                "you meet it."
            ),
        },
        {
            "id": "credit",
            "title": "Credit and debt",
            "icon": "💳",
            "duration": "4 min",
            "summary": "Understand borrowing before accepting it.",
            "content": (
                "Credit allows you to use borrowed money and repay it "
                "later. Loans and credit cards can involve interest, "
                "fees, and penalties. Paying only the minimum due on a "
                "credit card can leave you paying interest on the "
                "remaining balance. Before borrowing, check the total "
                "repayment amount, interest rate, due date, and fees. "
                "Borrow only when you understand how you will repay."
            ),
            "tip": (
                "Before taking credit, write down the total amount "
                "you must repay and the monthly payment."
            ),
        },
        {
            "id": "needs-wants",
            "title": "Needs versus wants",
            "icon": "🛍️",
            "duration": "3 min",
            "summary": "Spend intentionally without removing all enjoyment.",
            "content": (
                "Needs are essential costs such as food, basic "
                "transport, and necessary study materials. Wants are "
                "things that improve comfort or enjoyment but can "
                "usually wait. Before an unplanned purchase, pause and "
                "ask whether it fits your budget and priorities. "
                "You do not need to eliminate every want; you need to "
                "make the trade-off consciously."
            ),
            "tip": (
                "For a non-essential purchase, wait 24 hours and "
                "check your available budget again."
            ),
        },
        {
            "id": "scams",
            "title": "Avoiding money scams",
            "icon": "🛡️",
            "duration": "4 min",
            "summary": "Protect your money, passwords, and UPI PIN.",
            "content": (
                "Never share your UPI PIN, OTP, password, or full "
                "banking credentials with someone who contacts you. "
                "Receiving money does not require entering your UPI "
                "PIN. Be suspicious of guaranteed investment returns, "
                "urgent payment demands, and links from unknown "
                "senders. Verify requests using an official app or "
                "contact method. If you suspect fraud, contact your "
                "bank immediately."
            ),
            "tip": (
                "Never approve a payment request or enter a PIN just "
                "because a caller says you will receive money."
            ),
        },
        {
            "id": "investing",
            "title": "Investment fundamentals",
            "icon": "📈",
            "duration": "4 min",
            "summary": "Understand risk before putting money into markets.",
            "content": (
                "Investing means putting money into assets with the "
                "expectation of a possible future return. Returns are "
                "not guaranteed, and you can lose money. Learn about "
                "risk, diversification, fees, and time horizon before "
                "choosing an investment. Do not invest borrowed money "
                "or money needed soon for essential expenses. Trading "
                "is especially risky for beginners and should not be "
                "treated as guaranteed income."
            ),
            "tip": (
                "Learn the risks and costs of a product before "
                "investing any money."
            ),
        },
    ]

    return render(
        request,
        "learning.html",
        {"lessons": lessons},
    )
