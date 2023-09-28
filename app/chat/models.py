from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = None
        self.conversation_name = None
        self.conversation = None
    
    def get_online_count(self):
        return self.online.count()
    
    def join(self, user):
        self.online.add(user)
        self.save()
        
    def leave(self, user):
        self.online.remove(user)
        self.save()
        
    def __str__(self) -> str:
        return f"{self.name} ({self.get_online_count()})"
    
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_from_me"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_to_me"
    )
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"From {self.from_user.username} to {self.to_user.username}: {self.content} [{self.timestamp}]"
        
