from django.core.management.base import BaseCommand
from myapp.models import ErrorCode, FAQ


class Command(BaseCommand):
    help = "Seed initial FAQs and ErrorCodes into the database idempotently."

    def handle(self, *args, **options):
        self.stdout.write("Seeding SpendWise FAQs...")

        faqs_data = [
            {
                "question": "How do I create a new SpendWise account?",
                "answer": (
                    "Click on 'Register' in the top navigation bar. Enter a unique username, "
                    "a valid email address, and a strong password (minimum 8 characters). "
                    "Once submitted, your account will be created immediately and you will be "
                    "logged in directly to your financial dashboard."
                ),
                "category": "Account",
            },
            {
                "question": "How do I log in to my SpendWise account?",
                "answer": (
                    "Click on 'Login' in the navigation bar. Enter your registered username and "
                    "password. If your credentials match, you will be redirected to your transactions "
                    "and personal dashboard."
                ),
                "category": "Account",
            },
            {
                "question": "How do I record an income entry in SpendWise?",
                "answer": (
                    "Navigate to Transactions > 'Add Transaction'. Choose 'Income' as the type, "
                    "enter the amount in rupees, select an income category (e.g. Salary, Allowance, "
                    "or Other), choose the transaction date, and add an optional description. Click "
                    "'Save' to record it."
                ),
                "category": "Transactions",
            },
            {
                "question": "How do I record an expense?",
                "answer": (
                    "Go to Transactions > 'Add Transaction'. Set the transaction type to 'Expense', "
                    "enter an amount greater than zero, select an appropriate category (such as Food, "
                    "Travel, Shopping, Bills, Health, or Entertainment), pick the date, and save. "
                    "Your monthly spending total and budget indicators will update automatically."
                ),
                "category": "Transactions",
            },
            {
                "question": "How do I edit or update an existing transaction?",
                "answer": (
                    "In the Transactions table, locate the transaction you wish to edit and click "
                    "the 'Edit' link. You can change the amount, category, date, description, or "
                    "attach a receipt image. Click 'Update Transaction' to save your changes."
                ),
                "category": "Transactions",
            },
            {
                "question": "How do I delete a transaction?",
                "answer": (
                    "Find the transaction in your Transactions list and click 'Delete'. SpendWise "
                    "will prompt you with a confirmation screen to prevent accidental deletion. "
                    "Confirm the deletion to remove the record and recompute your totals."
                ),
                "category": "Transactions",
            },
            {
                "question": "How do I upload a receipt for a transaction?",
                "answer": (
                    "When adding or editing a transaction, use the 'Receipt Image' file input to "
                    "select a JPG, PNG, or JPEG image of your physical receipt or digital invoice. "
                    "Once uploaded, the receipt is safely stored and can be viewed directly from your "
                    "transaction list."
                ),
                "category": "Transactions",
            },
            {
                "question": "How do I create and manage a monthly budget?",
                "answer": (
                    "Visit the 'Budgets' page from the main navigation. Select the month and year, "
                    "then input your target spending limit. If a budget for that month already exists, "
                    "submitting the form will update its limit. The page will track your actual expenses "
                    "against the limit in real time."
                ),
                "category": "Budgets",
            },
            {
                "question": "What information does the Financial Dashboard show?",
                "answer": (
                    "The Dashboard summarizes your lifetime total income and expenses, net balance, "
                    "current calendar month's income and expenses, current month's budget status "
                    "(On track, Almost at limit, or Over budget), and displays your five most recent transactions."
                ),
                "category": "Insights",
            },
            {
                "question": "How do Financial Insights and Analytics work?",
                "answer": (
                    "The Insights page analyzes your historical transactions. It features interactive "
                    "Chart.js visualizations showing your spending breakdown by category and your 6-month "
                    "income versus expense trends to help you spot saving opportunities."
                ),
                "category": "Insights",
            },
            {
                "question": "What is the Money Learning Centre and how do I use the audio reader?",
                "answer": (
                    "The Learning Centre offers bite-sized student financial literacy lessons covering "
                    "Budgeting, Saving, Credit & Debt, Needs vs Wants, Avoiding Scams, and Investing. "
                    "Each lesson includes an audio speaker icon that uses your browser's Web Speech API "
                    "to read the lesson aloud to you."
                ),
                "category": "Learning",
            },
            {
                "question": "How do I use the SpendWise Chat Assistant and raise a support ticket?",
                "answer": (
                    "Click the floating assistant widget at the bottom right corner of any page. "
                    "You can ask questions about using SpendWise or enter an error code (e.g. SW-FORM-001) "
                    "to get instant troubleshooting steps. If the assistant cannot answer your question, "
                    "it will offer to create a support ticket with a unique tracking ID."
                ),
                "category": "Assistant",
            },
        ]

        faq_created_count = 0
        faq_updated_count = 0
        for data in faqs_data:
            _, created = FAQ.objects.update_or_create(
                question=data["question"],
                defaults={
                    "answer": data["answer"],
                    "category": data["category"],
                    "is_active": True,
                },
            )
            if created:
                faq_created_count += 1
            else:
                faq_updated_count += 1

        self.stdout.write(
            f"FAQs seeded: {faq_created_count} created, {faq_updated_count} updated (Total: {FAQ.objects.count()})."
        )

        self.stdout.write("Seeding SpendWise ErrorCodes...")

        error_codes_data = [
            {
                "code": "SW-AUTH-001",
                "title": "Authentication Failure",
                "description": "Invalid username or password provided during sign-in.",
                "possible_causes": (
                    "Typographical error in username or password; caps lock key enabled; "
                    "account does not exist yet."
                ),
                "recommended_solution": (
                    "Verify your credentials carefully. Ensure caps lock is off. If you do not have "
                    "an account, visit the Register page to create one."
                ),
                "severity": "WARNING",
                "category": "Authentication",
            },
            {
                "code": "SW-AUTH-002",
                "title": "Permission Denied / Access Restricted",
                "description": "You attempted to view, edit, or delete a resource that belongs to another user or requires elevated permissions.",
                "possible_causes": (
                    "Accessing a transaction or budget ID that does not belong to your account; "
                    "session expired or logged out."
                ),
                "recommended_solution": (
                    "Ensure you are logged into the correct account. You can only manage transactions and budgets "
                    "created by your own user account."
                ),
                "severity": "ERROR",
                "category": "Security",
            },
            {
                "code": "SW-FORM-001",
                "title": "Invalid Transaction Data",
                "description": "The submitted transaction contains invalid or non-positive values.",
                "possible_causes": (
                    "Amount entered was zero or negative; date format is invalid; "
                    "required category field was omitted."
                ),
                "recommended_solution": (
                    "Enter a positive amount greater than ₹0.00. Select a valid category and check "
                    "that the date is in a standard YYYY-MM-DD format."
                ),
                "severity": "WARNING",
                "category": "Validation",
            },
            {
                "code": "SW-DATA-001",
                "title": "Transaction Not Found",
                "description": "The requested transaction record could not be found in the database.",
                "possible_causes": (
                    "The transaction may have been deleted in another session; invalid URL identifier."
                ),
                "recommended_solution": (
                    "Return to your Transactions page to verify the current list of transactions."
                ),
                "severity": "INFO",
                "category": "Database",
            },
            {
                "code": "SW-DATA-002",
                "title": "Invalid Budget Configuration",
                "description": "The submitted budget limit is invalid or non-positive.",
                "possible_causes": (
                    "Limit set to ₹0 or a negative number; year entered is out of valid range (2020-2100)."
                ),
                "recommended_solution": (
                    "Set a monthly spending limit greater than zero and pick a valid calendar year."
                ),
                "severity": "WARNING",
                "category": "Validation",
            },
            {
                "code": "SW-API-001",
                "title": "External Exchange Rate API Unavailable",
                "description": "Connection to the third-party currency exchange rate provider timed out or returned an error.",
                "possible_causes": (
                    "Remote API service downtime; network latency; connection timeout (>5 seconds)."
                ),
                "recommended_solution": (
                    "SpendWise automatically serves the latest cached exchange rates. The core application "
                    "continues to work normally while remote connectivity recovers."
                ),
                "severity": "WARNING",
                "category": "External API",
            },
            {
                "code": "SW-MEDIA-001",
                "title": "Receipt Upload Failed",
                "description": "The uploaded receipt file could not be processed or saved.",
                "possible_causes": (
                    "File uploaded is not a supported image format (must be JPG, JPEG, or PNG); "
                    "file size exceeds server limit."
                ),
                "recommended_solution": (
                    "Please upload a clear image in PNG or JPG format under 5MB."
                ),
                "severity": "ERROR",
                "category": "Media",
            },
            {
                "code": "SW-SERVER-001",
                "title": "Unexpected Application Error",
                "description": "An unexpected server condition occurred while processing your request.",
                "possible_causes": (
                    "Transient database connectivity disruption or unhandled system condition."
                ),
                "recommended_solution": (
                    "Refresh the page. If the issue persists, open the floating chat assistant to report "
                    "this error code (SW-SERVER-001) and raise a support ticket."
                ),
                "severity": "CRITICAL",
                "category": "System",
            },
        ]

        err_created_count = 0
        err_updated_count = 0
        for data in error_codes_data:
            _, created = ErrorCode.objects.update_or_create(
                code=data["code"],
                defaults={
                    "title": data["title"],
                    "description": data["description"],
                    "possible_causes": data["possible_causes"],
                    "recommended_solution": data["recommended_solution"],
                    "severity": data["severity"],
                    "category": data["category"],
                    "is_active": True,
                },
            )
            if created:
                err_created_count += 1
            else:
                err_updated_count += 1

        self.stdout.write(
            f"ErrorCodes seeded: {err_created_count} created, {err_updated_count} updated (Total: {ErrorCode.objects.count()})."
        )
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
