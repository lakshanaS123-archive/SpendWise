# SpendWise — Personal Student Finance & Smart Money Management

SpendWise is a full-stack personal finance web application built with Django, PostgreSQL, MongoDB, WhiteNoise, and Chart.js. Designed specifically for students and young adults, SpendWise provides intuitive income and expense tracking, monthly budget planning with visual spending indicators, receipt image uploads, interactive financial analytics, a Money Learning Centre with text-to-speech audio reader, an SQL-backed FAQ knowledge base, a deterministic floating AI Chat Assistant, a support ticket CRUD system, and real-time currency exchange conversion.

---

## 1. Application Overview

- **Application Name:** SpendWise
- **Primary Domain:** Student Personal Finance & Financial Literacy
- **Architecture:** Monolithic Django with RESTful JSON API endpoints, SQL persistence for transactional/relational data, and MongoDB for conversational chat history and feedback.
- **Repository:** [https://github.com/lakshanaS123-archive/SpendWise](https://github.com/lakshanaS123-archive/SpendWise)
- **Deployment Platform:** Render (Gunicorn, WhiteNoise, PostgreSQL, Cloudinary Media Storage)
- **Live Production URL:** [https://spendwise-i14t.onrender.com](https://spendwise-i14t.onrender.com)

---

## 2. Core Financial Features (Preserved & Enhanced)

1. **User Authentication & Profiles:** Secure registration, login, session management, and logout with password validation and user data isolation.
2. **Personal Finance Dashboard:** Lifetime net balance, total income, total expenses, current month budget remaining, and recent transactions.
3. **Transaction Management:** Full CRUD operations for income and expenses, categorization (Food, Travel, Shopping, Education, Bills, Health, Entertainment, Salary, Allowance, Other), transaction search, category filtering, and date range filters.
4. **Receipt Image Uploads:** Attach physical or digital receipts (JPG, PNG, JPEG) to transactions for audit and record-keeping.
5. **Monthly Budget Planner:** Set target monthly limits; tracks real-time progress bars with dynamic status indicators (`On track`, `Almost at limit` at &ge;80%, or `Over budget`).
6. **Financial Insights & Analytics:** Interactive Chart.js visualizations depicting expense breakdown by category and 6-month historical income vs. expense comparison.
7. **Money Learning Centre:** Six bite-sized financial literacy lessons with integrated browser text-to-speech audio reading.

---

## 3. Upgraded Enterprise Features

1. **Global Floating Chat Assistant:** Reusable assistant widget available across every page with quick suggestion chips, typing indicator, timestamping, and chat history.
2. **SQL-Backed FAQ System & API:** Database-backed knowledge base with category filtering, search, and dynamic asynchronous frontend rendering (`/api/faqs/` and `/faq/`).
3. **Application Error Code Registry:** SQL-backed error code system explaining error titles, root causes, and recommended user solutions (`SW-AUTH-001`, `SW-FORM-001`, `SW-SERVER-001`, etc.).
4. **Deterministic FAQ & Error Intelligence:** Rule-based assistant service that queries SQL as its single source of truth without requiring paid third-party AI APIs.
5. **Support Ticket System (Complete CRUD):** Allows users to open support tickets either directly or via the assistant when an issue is unresolved. Staff administrators can inspect, update status, prioritize, add resolution notes, and delete tickets.
6. **MongoDB Chat History & User Feedback:** Stores conversation threads, message roles, and 5-star user ratings in MongoDB collections (`conversations` and `feedback`) with graceful offline fallback.
7. **Third-Party Currency Exchange API:** Integrates with real-time exchange rates (`https://open.er-api.com/v6/latest/USD`) with 5-second timeout protection, cached fallback, and live currency converter on the Dashboard.
8. **Structured Request Logging:** Middleware recording request method, path, HTTP status, execution duration in milliseconds, IP, and unique `X-Request-ID` correlation headers while strictly redacting sensitive data.
9. **Render-Ready Health Monitoring:** `/health/` endpoint verifying SQL database connectivity, MongoDB status, and third-party API availability.
10. **Custom 404 & 500 Error Pages:** Polished error screens matching SpendWise branding with direct "Ask Assistant" context injection.

---

## 4. Technology Stack

- **Backend Framework:** Django 6.1.2 (Python 3.13)
- **Relational Database (SQL):** SQLite (local development) / PostgreSQL (production on Render via `dj-database-url` and `psycopg2-binary`)
- **Document Database (NoSQL):** MongoDB Atlas / PyMongo (for Chat History and Feedback)
- **Static Assets & Serving:** WhiteNoise 6.12.0 (`CompressedManifestStaticFilesStorage` in production, `CompressedStaticFilesStorage` in development)
- **WSGI Server:** Gunicorn 26.2.0
- **Third-Party API:** Open Exchange Rates API (`open.er-api.com`) via `requests`
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (ES6+), Chart.js, Web Speech API

---

## 5. Project Directory Structure

```text
DJANGO_APP/
├── build.sh                      # Render automated build and migration script
├── db.sqlite3                    # Local SQLite database (perserved)
├── manage.py                     # Django management entry point
├── requirements.txt              # Standardized UTF-8 Python dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Version control exclusions
│
├── myproject/                    # Project package configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py               # Centralized configuration with env-vars
│   ├── urls.py                   # Root URLs with custom 404 & 500 handlers
│   └── wsgi.py
│
├── myapp/                        # Primary Django application
│   ├── admin.py                  # Admin models (Transaction, Budget, FAQ, ErrorCode, SupportTicket)
│   ├── assistant_service.py      # Deterministic SQL FAQ & error code search service
│   ├── exchange_service.py       # Third-party currency rate integration & fallback
│   ├── forms.py                  # Forms with positive amount & budget validation
│   ├── middleware.py             # Structured RequestLoggingMiddleware
│   ├── models.py                 # Transaction, Budget, FAQ, ErrorCode, SupportTicket
│   ├── mongo_service.py          # MongoDB client for chat history and feedback
│   ├── tests.py                  # Comprehensive test suite (32 passing tests)
│   ├── urls.py                   # Application routes & API endpoints
│   ├── views.py                  # Core views, JSON APIs, and error handlers
│   │
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py      # Idempotent FAQ & ErrorCode database seeder
│   │
│   ├── migrations/               # Database migrations (0001, 0002, 0003)
│   │
│   ├── static/
│   │   ├── css/style.css         # Main application styles
│   │   └── js/script.js          # Client interactions & audio reader
│   │
│   └── templates/                # HTML templates
│       ├── base.html             # Common shell with navbar, alerts & assistant
│       ├── 404.html              # Custom 404 Not Found error page
│       ├── 500.html              # Custom 500 Server Error page
│       ├── dashboard.html        # Dashboard with currency rate widget
│       ├── transactions.html     # Transaction listing, search & filters
│       ├── transaction_form.html # Add/edit transaction form
│       ├── confirm_delete.html   # Delete confirmation
│       ├── budgets.html          # Monthly budget planner
│       ├── insights.html         # Chart.js analytics
│       ├── learning.html         # Financial literacy lessons
│       ├── faq.html              # Asynchronous FAQ page
│       ├── login.html            # Sign-in
│       ├── register.html         # Registration
│       ├── components/
│       │   └── assistant_widget.html  # Floating chat assistant & feedback
│       └── tickets/
│           ├── ticket_list.html       # Support ticket listing
│           ├── ticket_form.html       # Support ticket submission form
│           └── ticket_detail.html     # Support ticket detail & staff update
│
└── media/                        # User uploaded receipt images
    └── receipts/
```

---

## 6. SQL Database Models

### 1. `Transaction`
- `user`: Foreign key to `User` (`CASCADE`, `related_name="transactions"`)
- `transaction_type`: `INCOME` or `EXPENSE`
- `amount`: `DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])`
- `category`: Category choice (Food, Travel, Shopping, Education, Bills, Health, Entertainment, Salary, Allowance, Other)
- `date`: `DateField` (defaults to local date)
- `description`: `CharField(max_length=250, blank=True)`
- `receipt`: `ImageField(upload_to="receipts/", blank=True, null=True)`
- `created_at`: `DateTimeField(auto_now_add=True)`

### 2. `Budget`
- `user`: Foreign key to `User`
- `month`: 1 to 12 (`PositiveSmallIntegerField`)
- `year`: `PositiveSmallIntegerField`
- `limit`: `DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])`
- **Constraint:** `UniqueConstraint(fields=["user", "month", "year"], name="unique_user_month_budget")`

### 3. `FAQ`
- `question`: `CharField(max_length=255)`
- `answer`: `TextField`
- `category`: `CharField(max_length=50)` (`Account`, `Transactions`, `Budgets`, `Insights`, `Learning`, `Assistant`, `General`)
- `is_active`: `BooleanField(default=True)`
- `created_at`, `updated_at`: `DateTimeField`

### 4. `ErrorCode`
- `code`: `CharField(max_length=30, unique=True)` (e.g. `SW-AUTH-001`, `SW-FORM-001`)
- `title`: `CharField(max_length=150)`
- `description`: `TextField`
- `possible_causes`: `TextField`
- `recommended_solution`: `TextField`
- `severity`: `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `category`: `CharField(max_length=50)`
- `is_active`: `BooleanField(default=True)`

### 5. `SupportTicket`
- `ticket_id`: Unique identifier (e.g. `SW-TKT-A1B2C3`, auto-generated)
- `user`: Foreign key to `User` (`null=True, blank=True, on_delete=SET_NULL`)
- `contact_email`: `EmailField(blank=True)`
- `subject`: `CharField(max_length=200)`
- `description`: `TextField`
- `related_error_code`: `CharField(max_length=30, blank=True)`
- `priority`: `LOW`, `MEDIUM`, `HIGH`, `URGENT`
- `status`: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`
- `resolution_notes`: `TextField(blank=True)`
- `created_at`, `updated_at`: `DateTimeField`

---

## 7. MongoDB Integration (Chat History & Feedback)

MongoDB stores unstructured and semi-structured interaction data separately from financial records:

### `conversations` Collection
```json
{
  "_id": "ObjectId(...)",
  "conversation_id": "conv_abc123_1730000000000",
  "user_id": 1,
  "created_at": "2026-11-03T09:00:00Z",
  "updated_at": "2026-11-03T09:02:15Z",
  "messages": [
    {
      "message_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "role": "user",
      "content": "How do I create a budget?",
      "timestamp": "2026-11-03T09:00:00Z"
    },
    {
      "message_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
      "role": "assistant",
      "content": "Visit the Budgets page from the main navigation...",
      "timestamp": "2026-11-03T09:00:01Z",
      "metadata": {
        "intent": "faq",
        "faq_id": 8
      }
    }
  ]
}
```

### `feedback` Collection
```json
{
  "_id": "ObjectId(...)",
  "feedback_id": "fed_xyz789",
  "conversation_id": "conv_abc123_1730000000000",
  "user_id": 1,
  "rating": 5,
  "feedback_text": "Great assistance with the budget questions!",
  "created_at": "2026-11-03T09:03:00Z"
}
```

**Graceful Degradation:** If MongoDB Atlas or local MongoDB is offline or unconfigured, the application logs the condition safely and returns a clear status. Core budgeting, transaction, and authentication features continue to function seamlessly.

---

## 8. FAQ JSON API Documentation

### `GET /api/faqs/`
Retrieves active FAQs with optional filtering and search.

**Query Parameters:**
- `category` *(optional)*: Filter by category (e.g. `Transactions`, `Budgets`, `Account`).
- `q` *(optional)*: Keyword search across question and answer texts.

**Response Example (200 OK):**
```json
{
  "status": "success",
  "count": 12,
  "categories": [
    "Account",
    "Transactions",
    "Budgets",
    "Insights",
    "Learning",
    "Assistant"
  ],
  "faqs": [
    {
      "id": 4,
      "question": "How do I record an expense?",
      "answer": "Go to Transactions > 'Add Transaction'. Set the transaction type to 'Expense'...",
      "category": "Transactions",
      "updated_at": "2026-11-03T09:14:00Z"
    }
  ]
}
```

---

## 9. Error Code Reference

| Code | Title | Severity | Category | Recommended Action |
| :--- | :--- | :--- | :--- | :--- |
| `SW-AUTH-001` | Authentication Failure | `WARNING` | Authentication | Verify username and password; ensure caps lock is off. |
| `SW-AUTH-002` | Permission Denied | `ERROR` | Security | Ensure you are logged into the account that owns the transaction or budget. |
| `SW-FORM-001` | Invalid Transaction Data | `WARNING` | Validation | Enter an amount greater than ₹0.00 and select a category. |
| `SW-DATA-001` | Transaction Not Found | `INFO` | Database | Record may have been removed; refresh your transactions list. |
| `SW-DATA-002` | Invalid Budget Configuration | `WARNING` | Validation | Spending limit must be greater than zero and year must be between 2020-2100. |
| `SW-API-001` | Currency Rate Service Unavailable | `WARNING` | External API | Remote API timed out; application serves cached exchange rates automatically. |
| `SW-MEDIA-001`| Receipt Upload Failed | `ERROR` | Media | Upload a JPG, JPEG, or PNG image under 5MB. |
| `SW-SERVER-001`| Unexpected Application Error | `CRITICAL` | System | Refresh page or report error code via Chat Assistant to open a support ticket. |

---

## 10. Assistant Intelligence & Ticket Workflow

1. **Error Code Detection:** User inputs any string matching `SW-[A-Z]+-[0-9]+`. Assistant matches the code against the `ErrorCode` table and displays title, causes, and recommended solution.
2. **FAQ Search:** User asks a natural language question. The search tokenizer removes stop words and scores matching FAQs based on question text, category, and answer content. If confidence score is high, it returns the verified answer with related topics.
3. **Unknown Question Fallback & Ticket Creation:** If no confident FAQ match exists:
   - Assistant honestly indicates that an exact answer was not found.
   - Offers to raise a support ticket for the team.
   - Upon user confirmation ("Yes"), creates a `SupportTicket` in SQL with a unique ticket ID (`SW-TKT-XXXXXX`).

---

## 11. Third-Party Currency Exchange API

- **Endpoint:** `GET /api/exchange-rates/`
- **Default Provider:** Open Exchange Rates API (`https://open.er-api.com/v6/latest/USD`)
- **Timeout Protection:** 5-second hard timeout on HTTP requests.
- **Caching:** Successful API responses are cached in Django's cache for 1 hour (`3600s`).
- **Offline Fallback:** If network connection fails or times out, the service automatically falls back to last-known cached exchange rates without interrupting application execution.
- **UI Integration:** A live converter card on the Dashboard calculates conversions from Indian Rupees (₹) to USD ($), EUR (€), GBP (£), and AED with a live/fallback indicator.

---

## 12. Health Check Endpoint

### `GET /health/`
Provides structured JSON monitoring for uptime checkers (Render, UptimeRobot).

**Sample Response (200 OK):**
```json
{
  "status": "ok",
  "application": "SpendWise",
  "timestamp": "2026-11-03T09:20:00Z",
  "database": {
    "status": "connected",
    "engine": "sqlite"
  },
  "mongodb": {
    "status": "connected",
    "database": "spendwise",
    "connected": true
  },
  "third_party_api": {
    "provider": "open.er-api.com",
    "status": "live"
  }
}
```

---

## 13. Environment Configuration (`.env`)

Copy `.env.example` to `.env` and configure your credentials:

```bash
# Django Security
DJANGO_SECRET_KEY=your-strong-random-production-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,spendwise.onrender.com

# PostgreSQL Database (Render provides DATABASE_URL automatically)
DATABASE_URL=postgresql://user:password@hostname:5432/spendwise_db

# MongoDB Atlas (for chat history and feedback)
MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=spendwise

# Third-party Currency API
EXCHANGE_RATE_API_URL=https://open.er-api.com/v6/latest/USD
EXCHANGE_RATE_API_KEY=

# Render & HTTPS Settings
RENDER_EXTERNAL_HOSTNAME=spendwise.onrender.com
CSRF_TRUSTED_ORIGINS=https://spendwise.onrender.com
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Media storage
MEDIA_ROOT=media
```

---

## 14. Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/lakshanaS123-archive/SpendWise.git
   cd SpendWise
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Seed FAQs and Error Codes:**
   ```bash
   python manage.py seed_data
   ```

6. **Start local development server:**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

---

## 15. Automated Testing

Run the full automated test suite containing 32 test cases:

```bash
python manage.py test
```

**Test Coverage Highlights:**
- User registration, authentication, login, and logout.
- Transaction validation (rejection of zero or negative amounts).
- Transaction CRUD, search, category filtering, and receipt uploads.
- Budget calculation, unique constraint per user/month/year, and status indicators.
- User data isolation (preventing unauthorized cross-user modifications).
- FAQ database seeding, API category filtering, and keyword search.
- ErrorCode retrieval and verification.
- Assistant intelligence for error code explanation, FAQ answering, and ticket creation.
- Support ticket CRUD and role-based permissions (user vs. staff).
- Third-party currency exchange rate retrieval, timeout handling, and cached fallback.
- Health check endpoint verification and diagnostic reporting.
- Cloudinary media storage configuration and initial data fixture integrity.
- Custom 404 and 500 error page handling.
- Request logging middleware and `X-Request-ID` correlation tracking.

---

## 16. Render Deployment Guide

SpendWise is configured for seamless deployment on Render:

1. **Web Service Setup on Render:**
   - **Environment:** Python 3
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn myproject.wsgi:application`
2. **Environment Variables on Render Dashboard:**
   - `DJANGO_SECRET_KEY`: Random 50+ character string.
   - `DJANGO_DEBUG`: `False`
   - `DATABASE_URL`: Connection string of your Render PostgreSQL database.
   - `MONGODB_URI`: Connection string from your MongoDB Atlas cluster.
   - `MONGODB_DATABASE`: `spendwise`
   - `CLOUDINARY_CLOUD_NAME`: Cloud name from your Cloudinary dashboard.
   - `CLOUDINARY_API_KEY`: API key from Cloudinary.
   - `CLOUDINARY_API_SECRET`: API secret from Cloudinary.
   - `PYTHON_VERSION`: `3.13.5`
3. **Build Script Execution (`build.sh`):**
   ```bash
   pip install -r requirements.txt
   python manage.py collectstatic --no-input
   python manage.py migrate
   python manage.py seed_data
   python manage.py load_initial_data
   ```
4. **Permanent Cloud Media Storage:**
   SpendWise integrates with Cloudinary (`django-cloudinary-storage`) so receipt image attachments are permanently persisted and served via high-performance CDN at zero hosting cost.

---

## 17. Known Limitations

1. **MongoDB Atlas Network Peering:** On free-tier MongoDB Atlas instances, ensure network access (`0.0.0.0/0`) is enabled so Render web servers can connect.
2. **Browser Speech Synthesis API:** Text-to-speech audio reader in the Learning Centre requires a modern browser supporting the HTML5 Web Speech API (Chrome, Safari, Edge, Firefox).

---

## 18. Future Improvements

1. **Automated Receipt OCR (Optical Character Recognition):** Integrate Tesseract or AWS Textract to automatically scan uploaded receipts, extract the total amount, merchant name, and date, and pre-fill the transaction creation form.
2. **Multi-Currency Transaction Support:** Allow users to record transactions in foreign currencies (USD, EUR, GBP) and automatically convert them to Indian Rupees (₹) using the live exchange rate service.
3. **Budget Push & Email Notifications:** Implement automated weekly summaries or threshold alerts via email when spending reaches 80% or 100% of the monthly budget.
4. **Export to CSV / PDF:** Provide one-click data export of monthly transactions and tax-ready expense summaries.
5. **Interactive Financial Goal Planner:** Add a savings target module enabling students to set long-term goals (e.g. laptop purchase, emergency fund) with progress projections.
