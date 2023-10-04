from typing import Any
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import GroupMessage, GroupConversation
from django.contrib.auth import get_user_model
from chat.serializers import GroupMessageSerializer, UserSerializer
import json
from uuid import UUID

User = get_user_model()

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj) -> Any:
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)
    
class GroupChatConsumer(JsonWebsocketConsumer):
    """
    This consumer is used to implement group chat functional
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.user = None
        
    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)
    
    def get_conversation_id(self):
        group_conversation_count = GroupConversation.objects.filter(admin=self.user).count()
        return group_conversation_count + 1
    
    def send_members(self):
        """Send chat members to frontend"""
        members = self.conversation.members
        self.send_json(
            {
                "type": "members_list",
                "users": UserSerializer(members, many=True).data,
            }
        )
        
    def send_chat_message_echo(self, username, message):
        """Sending chat message echo"""
        async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "chat_message_echo",
                    "username": username,
                    "message": message,
                },
            )
    
    def send_new_message_group_notification(self, message):
        """Sending new message notification"""
        users = self.get_receivers()
        for user in users:
            if user == self.user:
                continue
            notification_group_name = user.username + "__notifications"
            async_to_sync(self.channel_layer.group_send)(
                notification_group_name,
                {
                    "type": "new_message_group_notification",
                    "name": self.user.username,
                    "message": message
                }
            )
        
    
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.close()
            return
        elif self.scope['url_route']['kwargs']['group_chat_name'] == 'undefined':
            self.close()
            return 
        
        self.accept()
        if self.scope['url_route']['kwargs']['group_chat_name'] == 'new':           
            self.conversation_name = f"group_chat_with__{self.user}__{self.get_conversation_id()}"
        else:
            self.conversation_name = f"{self.scope['url_route']['kwargs']['group_chat_name']}"
        
        conv = GroupConversation.objects.filter(name=self.conversation_name)
        created = False
        if len(conv) == 0:
            self.conversation = GroupConversation.objects.create(
                name=self.conversation_name, admin=self.user
            )
            created = True
        else:
            self.conversation = conv[0]
            
        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name,
            self.channel_name,
        )
        if created: # Redirect to correct group url if group chat has been just created
            self.conversation.join_group(self.user)
            self.conversation.get_members_count()
            self.send_json(
                {
                    "type": "redirect",
                    "url": self.conversation.name,
                }
            )
            self.close()
        
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_name,
            {
                "type": "user_join",
                "user": self.user.username,
            }
        )
        self.conversation.online.add(self.user)
        
        group_messages = self.conversation.group_messages.all().order_by('-timestamp')[:50]
        group_messages_count = self.conversation.group_messages.all().count()
        self.send_json(
            {
                "type": "last_50_group_messages",
                "group_messages": GroupMessageSerializer(group_messages, many=True).data,
                "has_more": group_messages_count > 50,
            }
        )
        self.send_members()
    
    def receive_json(self, content, **kwargs):
        message_type = content['type']
        
        if message_type == "add_member":
            user = User.objects.filter(username=content['name'])
            if len(user) == 0:
                return
            user = user[0]
            self.conversation.members.add(user.id)
            self.send_members()
            message = GroupMessage.objects.create( # Create message about added member
                from_user = self.conversation.admin,
                content = f"User {user.username} was added to the chat",
                group_conversation = self.conversation
            )
            self.send_chat_message_echo(
                username=self.user.username,
                message=GroupMessageSerializer(message).data
            )
            self.send_new_message_group_notification(
                message=GroupMessageSerializer(message).data)
            
        elif message_type == "remove_member":
            user = User.objects.filter(username=content['name'])[0]
            self.conversation.members.remove(user.id)
            self.send_members()
            message = GroupMessage.objects.create( # Create message about removed member
                from_user = self.conversation.admin,
                content = f"User {user.username} was removed from the chat",
                group_conversation = self.conversation
            )
            self.send_chat_message_echo(
                username=self.user.username,
                message=GroupMessageSerializer(message).data
            )
            self.send_new_message_group_notification(
                message=GroupMessageSerializer(message).data)
            
        elif message_type == "chat_message":
            message = GroupMessage.objects.create(
                from_user = self.user,
                content = content["message"],
                group_conversation = self.conversation
            )
            message.read.add(self.user)
            self.send_chat_message_echo(
                self.user.username,
                GroupMessageSerializer(message).data
            )
            self.send_new_message_group_notification(
                message=GroupMessageSerializer(message).data
            )

            
        elif message_type == "read_group_messages":
            messages = self.conversation.group_messages.all()
            for message in messages:
                message.read.add(self.user)
                
            unread_group_count = (
                GroupMessage.objects.filter(group_conversation__members=self.user)
                                    .exclude(read=self.user)
                                    .count()
            )
            async_to_sync(self.channel_layer.group_send)(
                self.user.username + "__notifications",
                {
                    "type": "unread_group_count",
                    "unread_group_count": unread_group_count,
                },
            )
            
        return super().receive_json(content, **kwargs)
        
    
    def disconnect(self, code):
        print("Disconnected!")
        if self.user.is_authenticated:
            self.send_json(
                {
                    "type": "user_leave",
                    "user": self.user.username,
                }
            )
        try:
            self.conversation.online.remove(self.user)
        except:
            pass
        return super().disconnect(code)
    
    def user_join(self, event):
        self.send_json(event)
        
    def chat_message_echo(self, event):
        self.send_json(event)
        
    def new_message_group_notification(self, event):
        self.send_json(event)
    
    def unread_group_count(self, event):
        self.send_json(event)
        
    def get_receivers(self):
        return User.objects.filter(group_members=self.conversation)