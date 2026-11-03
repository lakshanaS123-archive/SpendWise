from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

import myapp.views as myapp_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", myapp_views.health_check, name="root_health_check"),
    path("", include("myapp.urls")),
    # Serve media files (receipts) across local and persistent disk deployments
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler404 = "myapp.views.custom_404_view"
handler500 = "myapp.views.custom_500_view"
