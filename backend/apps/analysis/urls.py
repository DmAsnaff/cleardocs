from django.urls import path
from .views import DocumentAnalysisView, DocumentClausesView, DocumentRisksView, DocumentExportView

urlpatterns = [
    path("", DocumentAnalysisView.as_view(), name="document-analysis"),
    path("clauses/", DocumentClausesView.as_view(), name="document-clauses"),
    path("risks/", DocumentRisksView.as_view(), name="document-risks"),
    path("export/", DocumentExportView.as_view(), name="document-export"),
]
