from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import Message, GroupMessage
    
class NotificationConsumer(JsonWebsocketConsumer):
    """Single endpoint for user's notifications"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.notification_group_name = None
        
    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return
        self.accept()
        
        self.notification_group_name = self.user.username + "__notifications"
        async_to_sync(self.channel_layer.group_add)(
            self.notification_group_name,
            self.channel_name,
        )
        
        unread_count = Message.objects.filter(to_user=self.user, read=False).count()
        self.send_json(
            {
                "type": "unread_count",
                "unread_count": unread_count,
            }
        )
        
        unread_group_count = (
                GroupMessage.objects.filter(group_conversation__members=self.user)
                                    .exclude(read=self.user)
                                    .count()
        )
        self.send_json(
            {
                "type": "unread_group_count",
                "unread_group_count": unread_group_count,
            }
        )
    
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.notification_group_name,
            self.channel_name,
        )
        return super().disconnect(code)
    
    def new_message_notification(self, event):
        self.send_json(event)
        
    def new_message_group_notification(self, event):
        self.send_json(event)
        
    def unread_count(self, event):
        self.send_json(event)
        
    def unread_group_count(self, event):
        self.send_json(event)