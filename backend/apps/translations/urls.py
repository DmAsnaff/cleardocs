from django.urls import path
from .views import TranslationListCreateView, TranslationDetailView

urlpatterns = [
    path("", TranslationListCreateView.as_view(), name="translation-list-create"),
    path("<str:language>/", TranslationDetailView.as_view(), name="translation-detail"),
]
