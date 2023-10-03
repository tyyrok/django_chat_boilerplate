from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class AbstractConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)
    
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
    
    class Meta:
        abstract = True

class Conversation(AbstractConversation):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = None
        self.conversation_name = None
        self.conversation = None
    
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
    
class GroupConversation(AbstractConversation):
    members = models.ManyToManyField(to=User, blank=True, related_name="group_members")
    admin = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="group_chat_admin"
    )
    
    def get_members_count(self):
        return self.members.count()
    
    def join_group(self, user):
        self.members.add(user)
        self.save()
        
    def leave_group(self, user):
        self.members.remove(user)
        self.save()
    
    def __str__(self) -> str:
        return f"{self.name} (members-{self.get_members_count()}, online-{self.get_online_count()})"        

class GroupMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_conversation = models.ForeignKey(
        GroupConversation, on_delete=models.CASCADE, related_name="group_messages"
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_from_user"
    )
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.ManyToManyField(to=User, blank=True)
    
    def __str__(self) -> str:
        return f"Group conversation with {self.from_user} : {self.content} [{self.timestamp}]"
    
    def read_message(self, user):
        if not self.get_read_status(user):
            self.read.add(user)
    
    def get_read_status(self, user):
        if self.from_user == user:
            return True
        if len(self.read.filter(id=user.id)) == 0:
            return False
        return True