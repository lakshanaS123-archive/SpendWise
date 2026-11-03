import datetime
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from myapp.assistant_service import AssistantService
from myapp.exchange_service import ExchangeRateService
from myapp.forms import BudgetForm, RegistrationForm, SupportTicketForm, TransactionForm
from myapp.models import Budget, ErrorCode, FAQ, SupportTicket, Transaction
from myapp.mongo_service import MongoService

User = get_user_model()


class ExistingFunctionalityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPassword123!",
        )

        today = timezone.localdate()
        self.today = today

        # Create transactions for user
        self.t1 = Transaction.objects.create(
            user=self.user,
            transaction_type=Transaction.INCOME,
            amount=Decimal("5000.00"),
            category="Salary",
            date=today,
            description="Monthly salary",
        )
        self.t2 = Transaction.objects.create(
            user=self.user,
            transaction_type=Transaction.EXPENSE,
            amount=Decimal("1500.00"),
            category="Food",
            date=today,
            description="Grocery shopping",
        )

        # Create budget for user
        self.budget = Budget.objects.create(
            user=self.user,
            month=today.month,
            year=today.year,
            limit=Decimal("3000.00"),
        )

    # 1. Registration & Authentication tests
    def test_registration_form_valid(self):
        form_data = {
            "username": "newstudent",
            "email": "student@example.com",
            "password1": "Password123!",
            "password2": "Password123!",
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, "newstudent")
        self.assertEqual(user.email, "student@example.com")

    def test_registration_view_post_success(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "registereduser",
                "email": "registered@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))
        self.assertTrue(
            User.objects.filter(username="registereduser").exists()
        )

    def test_login_and_logout(self):
        login_success = self.client.login(
            username="testuser", password="StrongPassword123!"
        )
        self.assertTrue(login_success)

        # Logout via POST (Django standard)
        response = self.client.post(reverse("logout"))
        self.assertIn(response.status_code, [200, 302])

    # 2. Transaction Form and Validation
    def test_transaction_form_widgets(self):
        form = TransactionForm()
        self.assertEqual(
            form.fields["date"].widget.input_type, "date"
        )
        self.assertEqual(
            form.fields["description"].widget.attrs.get("rows"), 3
        )
        self.assertEqual(
            form.fields["receipt"].widget.attrs.get("accept"), "image/*"
        )

    def test_transaction_form_amount_validation(self):
        # Positive amount
        valid_form = TransactionForm(
            data={
                "transaction_type": Transaction.EXPENSE,
                "amount": "100.50",
                "category": "Food",
                "date": str(self.today),
                "description": "Lunch",
            }
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)

        # Non-positive amount: 0
        zero_form = TransactionForm(
            data={
                "transaction_type": Transaction.EXPENSE,
                "amount": "0.00",
                "category": "Food",
                "date": str(self.today),
                "description": "Free food",
            }
        )
        self.assertFalse(zero_form.is_valid())
        self.assertIn("amount", zero_form.errors)

        # Non-positive amount: negative
        negative_form = TransactionForm(
            data={
                "transaction_type": Transaction.EXPENSE,
                "amount": "-50.00",
                "category": "Food",
                "date": str(self.today),
                "description": "Negative expense",
            }
        )
        self.assertFalse(negative_form.is_valid())
        self.assertIn("amount", negative_form.errors)

    # 3. Transaction Views & Permissions
    def test_add_transaction_view(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.post(
            reverse("add_transaction"),
            {
                "transaction_type": Transaction.EXPENSE,
                "amount": "250.00",
                "category": "Travel",
                "date": str(self.today),
                "description": "Bus pass",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Transaction.objects.filter(
                user=self.user, description="Bus pass"
            ).exists()
        )

    def test_edit_transaction_view(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.post(
            reverse("edit_transaction", kwargs={"pk": self.t2.pk}),
            {
                "transaction_type": Transaction.EXPENSE,
                "amount": "1750.00",
                "category": "Food",
                "date": str(self.today),
                "description": "Grocery shopping updated",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.t2.refresh_from_db()
        self.assertEqual(self.t2.amount, Decimal("1750.00"))
        self.assertEqual(self.t2.description, "Grocery shopping updated")

    def test_delete_transaction_view(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.post(
            reverse("delete_transaction", kwargs={"pk": self.t2.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Transaction.objects.filter(pk=self.t2.pk).exists()
        )

    def test_user_transaction_isolation(self):
        # other_user tries to edit user's transaction
        self.client.login(
            username="otheruser", password="StrongPassword123!"
        )
        response = self.client.get(
            reverse("edit_transaction", kwargs={"pk": self.t1.pk})
        )
        self.assertEqual(response.status_code, 404)

        # other_user tries to delete user's transaction
        del_response = self.client.post(
            reverse("delete_transaction", kwargs={"pk": self.t1.pk})
        )
        self.assertEqual(del_response.status_code, 404)

    def test_transaction_list_and_filters(self):
        self.client.login(username="testuser", password="StrongPassword123!")

        # List renders
        response = self.client.get(reverse("transaction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monthly salary")
        self.assertContains(response, "Grocery shopping")

        # Filter by type
        inc_response = self.client.get(
            reverse("transaction_list") + "?type=INCOME"
        )
        self.assertContains(inc_response, "Monthly salary")
        self.assertNotContains(inc_response, "Grocery shopping")

        # Filter by search
        search_response = self.client.get(
            reverse("transaction_list") + "?q=Grocery"
        )
        self.assertContains(search_response, "Grocery shopping")
        self.assertNotContains(search_response, "Monthly salary")

    # 4. Budget Form and Views
    def test_budget_form_validation(self):
        valid_form = BudgetForm(
            data={"month": 5, "year": 2026, "limit": "2000.00"}
        )
        self.assertTrue(valid_form.is_valid())

        invalid_form = BudgetForm(
            data={"month": 5, "year": 2026, "limit": "0.00"}
        )
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("limit", invalid_form.errors)

    def test_budgets_view_and_calculations(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.get(reverse("budgets"))
        self.assertEqual(response.status_code, 200)

        # Save new budget or update
        post_response = self.client.post(
            reverse("budgets"),
            {
                "month": self.today.month,
                "year": self.today.year,
                "limit": "4000.00",
            },
        )
        self.assertEqual(post_response.status_code, 302)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.limit, Decimal("4000.00"))

    # 5. Dashboard View Calculations
    def test_dashboard_calculations(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        # Context checks
        self.assertEqual(response.context["total_income"], Decimal("5000.00"))
        self.assertEqual(response.context["total_expenses"], Decimal("1500.00"))
        self.assertEqual(response.context["balance"], Decimal("3500.00"))
        self.assertEqual(
            response.context["budget_remaining"], Decimal("1500.00")
        )
        self.assertEqual(response.context["budget_status"], "On track")

    # 6. Insights & Learning Pages
    def test_insights_view(self):
        self.client.login(username="testuser", password="StrongPassword123!")
        response = self.client.get(reverse("insights"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("category_labels", response.context)
        self.assertIn("Food", response.context["category_labels"])

    def test_learning_view(self):
        response = self.client.get(reverse("learning"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Budgeting basics")
        self.assertContains(response, "Saving consistently")


class NewFunctionalityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="SecurePassword123!",
        )
        self.staff_user = User.objects.create_user(
            username="staffadmin",
            email="staff@example.com",
            password="SecurePassword123!",
            is_staff=True,
        )
        # Run seed command to populate initial FAQs and ErrorCodes
        call_command("seed_data")

    # 1. SQL FAQ System & Idempotency
    def test_seeded_faqs_count_and_idempotency(self):
        faq_count = FAQ.objects.count()
        self.assertGreaterEqual(faq_count, 10)

        error_code_count = ErrorCode.objects.count()
        self.assertGreaterEqual(error_code_count, 8)

        # Run again to ensure no duplicates
        call_command("seed_data")
        self.assertEqual(FAQ.objects.count(), faq_count)
        self.assertEqual(ErrorCode.objects.count(), error_code_count)

    # 2. FAQ API & Page
    def test_faq_api_and_filters(self):
        # GET all active FAQs
        response = self.client.get(reverse("api_faqs"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 10)

        # Category filter
        tx_response = self.client.get(reverse("api_faqs") + "?category=Transactions")
        self.assertEqual(tx_response.status_code, 200)
        tx_data = tx_response.json()
        self.assertTrue(all(item["category"] == "Transactions" for item in tx_data["faqs"]))

        # Keyword search
        search_res = self.client.get(reverse("api_faqs") + "?q=receipt")
        self.assertEqual(search_res.status_code, 200)
        search_data = search_res.json()
        self.assertTrue(len(search_data["faqs"]) >= 1)

    def test_faq_page_renders(self):
        response = self.client.get(reverse("faq_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frequently Asked Questions")
        self.assertContains(response, "faqSearchInput")

    # 3. Error Code System in SQL
    def test_error_code_records(self):
        auth_err = ErrorCode.objects.filter(code="SW-AUTH-001").first()
        self.assertIsNotNone(auth_err)
        self.assertEqual(auth_err.title, "Authentication Failure")
        self.assertTrue(len(auth_err.possible_causes) > 0)
        self.assertTrue(len(auth_err.recommended_solution) > 0)

        form_err = ErrorCode.objects.filter(code="SW-FORM-001").first()
        self.assertIsNotNone(form_err)
        self.assertEqual(form_err.title, "Invalid Transaction Data")

    # 4. Assistant Intelligence & Ticket Confirmation
    def test_assistant_error_code_lookup(self):
        result = AssistantService.process_message("What is error SW-FORM-001?")
        self.assertEqual(result["intent"], "error_code")
        self.assertEqual(result["error_code"], "SW-FORM-001")
        self.assertIn("Invalid Transaction Data", result["reply"])

    def test_assistant_faq_lookup(self):
        result = AssistantService.process_message("How do I record an expense?")
        self.assertEqual(result["intent"], "faq")
        self.assertIn("Expense", result["reply"])

    def test_assistant_ticket_creation_workflow(self):
        # Step 1: Unknown query triggers ticket confirmation prompt
        step1 = AssistantService.process_message(
            "How do I fly a rocket to the moon from Bangalore?"
        )
        self.assertEqual(step1["intent"], "ticket_prompt")
        self.assertTrue(step1["session_updates"]["awaiting_ticket_confirmation"])

        # Step 2: User confirms with 'Yes'
        session_data = step1["session_updates"]
        step2 = AssistantService.process_message(
            user_message="Yes, please raise a ticket",
            user=self.user,
            session_data=session_data,
        )
        self.assertEqual(step2["intent"], "ticket_created")
        self.assertIsNotNone(step2["ticket_id"])
        self.assertTrue(
            SupportTicket.objects.filter(ticket_id=step2["ticket_id"]).exists()
        )

    # 5. Assistant API & Feedback
    def test_api_chat_endpoint(self):
        # Valid message
        response = self.client.post(
            reverse("api_chat"),
            data=json.dumps({"message": "How do I create a budget?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("reply", data)
        self.assertIn("conversation_id", data)

        # Empty message validation
        empty_res = self.client.post(
            reverse("api_chat"),
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )
        self.assertEqual(empty_res.status_code, 400)

    # 6. Support Ticket CRUD Operations & Isolation
    def test_ticket_crud(self):
        self.client.login(username="regularuser", password="SecurePassword123!")

        # Create
        create_res = self.client.post(
            reverse("ticket_create"),
            {
                "subject": "Need help with receipt upload",
                "description": "PNG image upload returned an error code.",
                "contact_email": "regular@example.com",
                "related_error_code": "SW-MEDIA-001",
                "priority": "HIGH",
            },
        )
        self.assertEqual(create_res.status_code, 302)
        ticket = SupportTicket.objects.filter(subject="Need help with receipt upload").first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.user, self.user)

        # Read (owner can view)
        detail_res = self.client.get(reverse("ticket_detail", kwargs={"ticket_id": ticket.ticket_id}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "SW-MEDIA-001")

        # User isolation: other regular user cannot view ticket
        other_user = User.objects.create_user(username="other", email="o@e.com", password="Pass123!")
        self.client.login(username="other", password="Pass123!")
        forbidden_res = self.client.get(reverse("ticket_detail", kwargs={"ticket_id": ticket.ticket_id}))
        self.assertEqual(forbidden_res.status_code, 403)

        # Staff can view and update ticket
        self.client.login(username="staffadmin", password="SecurePassword123!")
        staff_view = self.client.get(reverse("ticket_detail", kwargs={"ticket_id": ticket.ticket_id}))
        self.assertEqual(staff_view.status_code, 200)

        # Staff updates status
        staff_update = self.client.post(
            reverse("ticket_detail", kwargs={"ticket_id": ticket.ticket_id}),
            {
                "status": "RESOLVED",
                "priority": "HIGH",
                "resolution_notes": "We verified receipt images must be under 5MB and updated instructions.",
            },
        )
        self.assertEqual(staff_update.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "RESOLVED")

        # Delete ticket
        del_res = self.client.post(reverse("ticket_delete", kwargs={"ticket_id": ticket.ticket_id}))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(SupportTicket.objects.filter(ticket_id=ticket.ticket_id).exists())

    # 7. Third-Party Currency Exchange API & Fallback
    def test_exchange_rate_service_and_endpoint(self):
        rates_data = ExchangeRateService.get_exchange_rates()
        self.assertIn("rates", rates_data)
        self.assertIn("INR", rates_data["rates"])

        endpoint_res = self.client.get(reverse("api_exchange_rates"))
        self.assertEqual(endpoint_res.status_code, 200)
        self.assertIn("rates", endpoint_res.json())

    @patch("requests.get")
    def test_exchange_rate_service_fallback_on_timeout(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        from django.core.cache import cache
        cache.delete(ExchangeRateService.CACHE_KEY)

        rates_data = ExchangeRateService.get_exchange_rates()
        self.assertTrue(rates_data.get("from_fallback"))
        self.assertIn("rates", rates_data)
        self.assertIn("INR", rates_data["rates"])

    # 8. Health Check Endpoint
    def test_health_check_endpoint(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["application"], "SpendWise")
        self.assertEqual(data["database"]["status"], "connected")
        self.assertIn("mongodb", data)
        self.assertIn("third_party_api", data)

    # 9. Custom 404 & 500 Pages
    def test_custom_404_page(self):
        response = self.client.get("/non-existent-random-url-path-xyz/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "SW-DATA-001", status_code=404)
        self.assertContains(response, "Ask Assistant", status_code=404)

    def test_custom_500_page(self):
        response = self.client.get("/non-existent-random-url-path-xyz/")
        # Call custom_500_view directly
        from myapp.views import custom_500_view
        from django.test import RequestFactory
        factory = RequestFactory()
        req = factory.get("/test-error/")
        resp_500 = custom_500_view(req)
        self.assertEqual(resp_500.status_code, 500)
        self.assertIn(b"SW-SERVER-001", resp_500.content)
        self.assertIn(b"Ask Assistant", resp_500.content)

    # 10. Request Logging Middleware
    def test_request_logging_header(self):
        response = self.client.get(reverse("home"))
        self.assertIn("X-Request-ID", response.headers)
        self.assertTrue(len(response.headers["X-Request-ID"]) > 0)
