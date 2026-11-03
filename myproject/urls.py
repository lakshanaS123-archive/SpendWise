from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

import myapp.views as myapp_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", myapp_views.health_check, name="root_health_check"),
    path("", include("myapp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

handler404 = "myapp.views.custom_404_view"
handler500 = "myapp.views.custom_500_view"
