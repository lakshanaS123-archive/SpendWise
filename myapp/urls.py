
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register, name="register"),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html"
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "transactions/",
        views.transaction_list,
        name="transaction_list",
    ),

    path(
        "transactions/add/",
        views.add_transaction,
        name="add_transaction",
    ),
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

]
