from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/documents/", include("apps.documents.urls")),
    path("health/", include("apps.audit.health_urls")),
]

# Serve uploaded documents from local storage in development so the results
# page can preview the original PDF. In production these are served from S3.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
