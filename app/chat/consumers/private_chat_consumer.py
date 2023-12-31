from typing import Any
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import Conversation, Message, GroupMessage, GroupConversation
from django.contrib.auth import get_user_model
from django.db.models import Q
from chat.serializers import MessageSerializer, GroupMessageSerializer, UserSerializer
import json
from uuid import UUID

User = get_user_model()

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj) -> Any:
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)
    
class ChatConsumer(JsonWebsocketConsumer):
    """
    This consumer is used to show user's online status,
    and send notifications.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.user = None
        
    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)
        
    def connect(self):
        try:
            self.user = self.scope["user"]
        except KeyError:
            return self.close()
        if not self.user.is_authenticated:
            return
        self.accept()
        self.conversation_name = f"{self.scope['url_route']['kwargs']['conversation_name']}"
        self.conversation, created = Conversation.objects.get_or_create(name=self.conversation_name)
        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name,
            self.channel_name,
        )
        if created:
            self.send_json(
                {
                    "type": "welcome_message",
                    "message": "You've started a new chat",
                }
            )
        self.send_json(
            {
                "type": "online_user_list",
                "users": [user.username for user in self.conversation.online.all()],
            }
        )
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_name,
            {
                "type": "user_join",
                "user": self.user.username,
            }
        )
        self.conversation.online.add(self.user)
        
        messages = self.conversation.messages.all().order_by("-timestamp")[0:50]
        message_count = self.conversation.messages.all().count()
        self.send_json(
            {
                "type": "last_50_messages",
                "messages": MessageSerializer(messages, many=True).data,
                "has_more": message_count > 50,
            }
        )
        
    def disconnect(self, code):
        print("Disconnected!")
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "user_leave",
                    "user": self.user.username,
                },
            )
            self.conversation.online.remove(self.user)
        return super().disconnect(code)
    
    def receive_json(self, content, **kwargs):
        message_type = content['type']
        if message_type == "chat_message":
            message = Message.objects.create(
                from_user = self.user,
                to_user = self.get_receiver(),
                content = content["message"],
                conversation = self.conversation
            )
            
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "chat_message_echo",
                    "username": self.user.username,
                    "message": MessageSerializer(message).data
                },
            )
            notification_group_name = self.get_receiver().username + "__notifications"
            async_to_sync(self.channel_layer.group_send)(
                notification_group_name,
                {
                    "type": "new_message_notification",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data
                }
            )
        elif message_type == "typing":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "typing",
                    "user": self.user.username,
                    "typing": content["typing"]
                },
            )
        elif message_type == "read_messages":
            messages_to_me = self.conversation.messages.filter(to_user=self.user)
            messages_to_me.update(read=True)
            
            unread_count = Message.objects.filter(to_user=self.user, read=False).count()
            async_to_sync(self.channel_layer.group_send)(
                self.user.username + "__notifications",
                {
                    "type": "unread_count",
                    "unread_count": unread_count
                },
            )
            
        return super().receive_json(content, **kwargs)
    
    def chat_message_echo(self, event):
        self.send_json(event)
        
    def user_join(self, event):
        self.send_json(event)
    
    def user_leave(self, event):
        self.send_json(event)
        
    def typing(self, event):
        self.send_json(event)
        
    def new_message_notification(self, event):
        self.send_json(event)
        
    def unread_count(self, event):
        self.send_json(event)
        
    def get_receiver(self):
        usernames = self.conversation_name.split('__')
        for username in usernames:
            if username != self.user.username:
                return User.objects.get(username=username)

