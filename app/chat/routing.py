from django.urls import path
from chat.consumers import ChatConsumer, NotificationConsumer, GroupChatConsumer

websocket_urlpatterns = [
    path("chats/<conversation_name>/", ChatConsumer.as_asgi()),
    path("notifications/", NotificationConsumer.as_asgi()),
    path("group_chats/<group_chat_name>/", GroupChatConsumer.as_asgi()),
]