from django.urls import path, include
from .views import DocumentListCreateView, DocumentDetailView, DocumentStatusView

urlpatterns = [
    path("", DocumentListCreateView.as_view(), name="document-list-create"),
    path("<uuid:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:document_id>/status/", DocumentStatusView.as_view(), name="document-status"),
    path("<uuid:document_id>/analysis/", include("apps.analysis.urls")),
    path("<uuid:document_id>/translations/", include("apps.translations.urls")),
    path("<uuid:document_id>/chat/", include("apps.chat.urls")),
]
