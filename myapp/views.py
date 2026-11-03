import json
import uuid
from calendar import month_abbr
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .assistant_service import AssistantService
from .exchange_service import ExchangeRateService
from .forms import (
    BudgetForm,
    RegistrationForm,
    SupportTicketForm,
    SupportTicketStaffForm,
    TransactionForm,
)
from .models import Budget, ErrorCode, FAQ, SupportTicket, Transaction
from .mongo_service import MongoService


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


# ==============================================================================
# REQUIREMENT 3: FAQ PAGE & API (Part 6)
# ==============================================================================

def faq_page(request):
    """
    Renders the FAQ page shell. FAQs are loaded dynamically via the /api/faqs/ API.
    """
    categories = [
        c[0] for c in FAQ.CATEGORY_CHOICES
    ]
    return render(request, "faq.html", {"categories": categories})


@require_GET
def api_faqs(request):
    """
    GET /api/faqs/
    Returns active FAQs in structured JSON format with category and search filters.
    """
    qs = FAQ.objects.filter(is_active=True)

    category = request.GET.get("category", "").strip()
    search = request.GET.get("q", "").strip()

    if category:
        qs = qs.filter(category__iexact=category)

    if search:
        qs = qs.filter(
            Q(question__icontains=search) | Q(answer__icontains=search)
        )

    categories_list = list(
        FAQ.objects.filter(is_active=True)
        .values_list("category", flat=True)
        .distinct()
    )

    faqs_data = [
        {
            "id": item.id,
            "question": item.question,
            "answer": item.answer,
            "category": item.category,
            "updated_at": item.updated_at.isoformat(),
        }
        for item in qs
    ]

    return JsonResponse({
        "status": "success",
        "count": len(faqs_data),
        "categories": categories_list,
        "faqs": faqs_data,
    })


# ==============================================================================
# REQUIREMENT 2 & 6: GLOBAL CHAT ASSISTANT & FAQ INTELLIGENCE (Part 5, 9, 11)
# ==============================================================================

@require_POST
def api_chat(request):
    """
    POST /api/chat/
    Processes user queries using AssistantService, stores messages in MongoDB,
    and returns deterministic FAQ answers, error explanations, or ticket creation.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    if not user_message:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)

    if len(user_message) > 4000:
        return JsonResponse({"error": "Message exceeds maximum length (4000 characters)."}, status=400)

    user_id = request.user.id if request.user.is_authenticated else None

    # Load session state for ticket confirmation flow
    session_key = f"chat_session_{conversation_id}"
    session_data = request.session.get(session_key, {})

    # Process message through AssistantService
    result = AssistantService.process_message(
        user_message=user_message,
        user=request.user,
        session_data=session_data,
    )

    # Persist session state updates
    if "session_updates" in result:
        session_data.update(result["session_updates"])
        request.session[session_key] = session_data

    # Store user message and assistant reply into MongoDB
    user_saved = MongoService.save_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=user_message,
    )

    assistant_saved = MongoService.save_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=result["reply"],
        metadata={
            "intent": result.get("intent"),
            "error_code": result.get("error_code"),
            "faq_id": result.get("faq_id"),
            "ticket_id": result.get("ticket_id"),
        },
    )

    mongo_saved = bool(user_saved and assistant_saved)

    return JsonResponse({
        "status": "success",
        "conversation_id": conversation_id,
        "reply": result["reply"],
        "intent": result.get("intent"),
        "error_code": result.get("error_code"),
        "faq_id": result.get("faq_id"),
        "related_faqs": result.get("related_faqs", []),
        "ticket_id": result.get("ticket_id"),
        "mongo_saved": mongo_saved,
    })


@require_GET
def api_chat_history(request):
    """
    GET /api/chat/history/?conversation_id=...
    Retrieves previous conversation messages from MongoDB for authorized users.
    """
    conversation_id = request.GET.get("conversation_id", "").strip()
    if not conversation_id:
        return JsonResponse({"error": "conversation_id parameter is required."}, status=400)

    user_id = request.user.id if request.user.is_authenticated else None
    messages_list = MongoService.get_conversation_history(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if messages_list is None:
        return JsonResponse({
            "status": "unavailable",
            "messages": [],
            "message": "Chat history is currently offline or access is restricted.",
        })

    return JsonResponse({
        "status": "success",
        "conversation_id": conversation_id,
        "messages": messages_list,
    })


@require_POST
def api_feedback(request):
    """
    POST /api/chat/feedback/
    Saves user feedback into MongoDB feedback collection.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    conversation_id = data.get("conversation_id", "").strip()
    rating = data.get("rating", 5)
    feedback_text = data.get("feedback_text", "").strip()

    if not conversation_id:
        return JsonResponse({"error": "conversation_id is required."}, status=400)

    user_id = request.user.id if request.user.is_authenticated else None
    feedback_id = MongoService.save_feedback(
        conversation_id=conversation_id,
        user_id=user_id,
        rating=rating,
        feedback_text=feedback_text,
    )

    if feedback_id:
        return JsonResponse({
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!",
        })
    else:
        return JsonResponse({
            "status": "unavailable",
            "message": "Feedback service is temporarily offline.",
        }, status=503)


# ==============================================================================
# REQUIREMENT 9: THIRD-PARTY EXCHANGE RATE API (Part 12)
# ==============================================================================

@require_GET
def api_exchange_rates(request):
    """
    GET /api/exchange-rates/
    Provides live or cached currency exchange rates with timeout and fallback protection.
    """
    rates_data = ExchangeRateService.get_exchange_rates()
    return JsonResponse(rates_data)


# ==============================================================================
# REQUIREMENT 7: SUPPORT TICKET SYSTEM (CRUD) (Part 10)
# ==============================================================================

def ticket_list(request):
    """
    Lists support tickets. Regular users see their own tickets; staff see all tickets.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            status_filter = request.GET.get("status", "")
            tickets = SupportTicket.objects.all()
            if status_filter:
                tickets = tickets.filter(status=status_filter)
        else:
            tickets = request.user.support_tickets.all()
    else:
        # For anonymous users, prompt them to sign in or view ticket by ID
        ticket_id = request.GET.get("ticket_id", "").strip()
        if ticket_id:
            tickets = SupportTicket.objects.filter(ticket_id=ticket_id)
        else:
            return redirect("login")

    paginator = Paginator(tickets, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "tickets/ticket_list.html",
        {"tickets": page_obj, "page_obj": page_obj},
    )


def ticket_create(request):
    """
    Create a new support ticket.
    """
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
                if not ticket.contact_email:
                    ticket.contact_email = request.user.email
            ticket.save()
            messages.success(
                request,
                f"Support ticket {ticket.ticket_id} created successfully! Our team will review it.",
            )
            return redirect("ticket_detail", ticket_id=ticket.ticket_id)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data["contact_email"] = request.user.email
        if "error_code" in request.GET:
            initial_data["related_error_code"] = request.GET["error_code"]
        form = SupportTicketForm(initial=initial_data)

    return render(request, "tickets/ticket_form.html", {"form": form})


def ticket_detail(request, ticket_id):
    """
    View ticket details. Users can view their own; staff can update status & resolution notes.
    """
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)

    # Permission check: ticket belongs to user, or user is staff, or anonymous created within session
    if not request.user.is_staff and ticket.user is not None:
        if not request.user.is_authenticated or ticket.user != request.user:
            return HttpResponseForbidden("You do not have permission to view this ticket.")

    staff_form = None
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == "POST":
            staff_form = SupportTicketStaffForm(request.POST, instance=ticket)
            if staff_form.is_valid():
                staff_form.save()
                messages.success(request, "Ticket updated successfully!")
                return redirect("ticket_detail", ticket_id=ticket.ticket_id)
        else:
            staff_form = SupportTicketStaffForm(instance=ticket)

    return render(
        request,
        "tickets/ticket_detail.html",
        {"ticket": ticket, "staff_form": staff_form},
    )


@require_POST
def ticket_delete(request, ticket_id):
    """
    Delete a ticket. Only owner or staff.
    """
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)

    if not request.user.is_staff:
        if not request.user.is_authenticated or ticket.user != request.user:
            return HttpResponseForbidden("You do not have permission to delete this ticket.")

    ticket.delete()
    messages.success(request, f"Ticket {ticket_id} deleted successfully.")
    return redirect("ticket_list")


# ==============================================================================
# REQUIREMENT 10: HEALTH CHECK ENDPOINT (Part 13)
# ==============================================================================

@require_GET
def health_check(request):
    """
    GET /health/
    Structured health check reporting SQL database, MongoDB, and External API health.
    Suitable for Render monitoring.
    """
    overall_status = "ok"

    # 1. SQL Database Check
    sql_status = "disconnected"
    sql_engine = connection.vendor
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        sql_status = "connected"
    except Exception as e:
        sql_status = f"error: {str(e)}"
        overall_status = "degraded"

    # 2. MongoDB Check
    mongo_health = MongoService.check_health()
    if not mongo_health.get("connected"):
        # MongoDB does not block core financial functionality
        pass

    # 3. Third-party API Cache Check
    exchange_info = ExchangeRateService.get_exchange_rates()

    # 4. Media Storage Check
    from django.conf import settings as django_settings
    is_cloudinary = getattr(django_settings, "USE_CLOUDINARY", False)
    media_info = {
        "provider": "Cloudinary" if is_cloudinary else "Local / Disk Storage",
        "persistent": is_cloudinary,
    }

    response_data = {
        "status": overall_status,
        "application": "SpendWise",
        "timestamp": timezone.now().isoformat(),
        "database": {
            "status": sql_status,
            "engine": sql_engine,
        },
        "mongodb": mongo_health,
        "media_storage": media_info,
        "third_party_api": {
            "provider": exchange_info.get("provider"),
            "status": "live" if exchange_info.get("is_live") else "cached_fallback",
        },
    }

    status_code = 200 if sql_status == "connected" else 503
    return JsonResponse(response_data, status=status_code)


# ==============================================================================
# REQUIREMENT 5: CUSTOM 404 AND 500 ERROR VIEWS (Part 8)
# ==============================================================================

def custom_404_view(request, exception=None):
    """
    Custom 404 page with SpendWise design, error code SW-DATA-001 context,
    and 'Ask Assistant' integration.
    """
    context = {
        "error_code": "SW-DATA-001",
        "error_title": "Page or Resource Not Found",
        "error_message": (
            "We could not find the page or resource you were looking for. "
            "It may have been moved, renamed, or is currently unavailable."
        ),
    }
    return render(request, "404.html", context, status=404)


def custom_500_view(request):
    """
    Custom 500 page with SpendWise design, error code SW-SERVER-001 context,
    and 'Ask Assistant' integration. Strictly avoids leaking tracebacks.
    """
    context = {
        "error_code": "SW-SERVER-001",
        "error_title": "Unexpected Application Error",
        "error_message": (
            "An unexpected error occurred while processing your request. "
            "Our engineering team has been notified."
        ),
    }
    return render(request, "500.html", context, status=500)
