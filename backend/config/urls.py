from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/documents/", include("apps.documents.urls")),
    path("health/", include("apps.audit.health_urls")),
]
