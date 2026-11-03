from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Core Finance Application Pages
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.add_transaction, name="add_transaction"),
    path(
        "transactions/<int:pk>/edit/",
        views.edit_transaction,
        name="edit_transaction",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.delete_transaction,
        name="delete_transaction",
    ),
    path("budgets/", views.budgets, name="budgets"),
    path("insights/", views.insights, name="insights"),
    path("learning/", views.learning, name="learning"),

    # Database-Backed FAQ Page and JSON API
    path("faq/", views.faq_page, name="faq_page"),
    path("api/faqs/", views.api_faqs, name="api_faqs"),

    # Assistant & MongoDB Endpoints
    path("api/chat/", views.api_chat, name="api_chat"),
    path("api/chat/history/", views.api_chat_history, name="api_chat_history"),
    path("api/chat/feedback/", views.api_feedback, name="api_feedback"),

    # Third-Party Currency Exchange API
    path("api/exchange-rates/", views.api_exchange_rates, name="api_exchange_rates"),

    # Support Ticket System (CRUD)
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path(
        "tickets/<str:ticket_id>/",
        views.ticket_detail,
        name="ticket_detail",
    ),
    path(
        "tickets/<str:ticket_id>/delete/",
        views.ticket_delete,
        name="ticket_delete",
    ),

    # Health Check
    path("health/", views.health_check, name="health_check"),
]
