from django.urls import path
from .views import ChatSessionListCreateView, ChatSessionDetailView, ChatMessageCreateView

urlpatterns = [
    path("sessions/", ChatSessionListCreateView.as_view(), name="chat-session-list-create"),
    path("sessions/<uuid:session_id>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("sessions/<uuid:session_id>/messages/", ChatMessageCreateView.as_view(), name="chat-message-create"),
]
