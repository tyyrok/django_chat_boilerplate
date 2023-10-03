from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Message, Conversation, GroupMessage

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name"]
        
class MessageSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()
    conversation = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "from_user",
            "to_user",
            "content",
            "timestamp",
            "read",
        )
        
    def get_conversation(self, obj):
        return str(obj.conversation.id)
    
    def get_from_user(self, obj):
        return UserSerializer(obj.from_user).data
    
    def get_to_user(self, obj):
        return UserSerializer(obj.to_user).data
    
class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ("id", "name", "other_user", "last_message")
        
    def get_last_message(self, obj):
        messages = obj.messages.all().order_by("-timestamp")
        if not messages.exists():
            return None
        message = messages[0]
        return MessageSerializer(message).data    
        
    def get_other_user(self, obj):
        usernames = obj.name.split('__')
        context = {}
        for username in usernames:
            if username != self.context['user'].username:
                other_user = User.objects.get(username=username)
                return UserSerializer(other_user, context=context).data
            
class GroupMessageSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()
    group_conversation = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupMessage
        fields = (
            "id",
            "group_conversation",
            "from_user",
            "content",
            "timestamp",
            "read",
        )
    def get_group_conversation(self, obj):
        return str(obj.group_conversation.id)
    
    def get_from_user(self, obj):
        return UserSerializer(obj.from_user).data

class GroupConversationSerializer(ConversationSerializer):
    members = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    class Meta:
        model = Conversation
        fields = ("id", "name", "last_message", "members", "admin")
    
    def get_last_message(self, obj):
        messages = obj.group_messages.all().order_by("-timestamp")
        if not messages.exists():
            return None
        message = messages[0]
        return GroupMessageSerializer(message).data  
    
    def get_members(self, obj):
        members = obj.members.all()
        return UserSerializer(members, many=True).data   
    
    def get_admin(self, obj):
        return UserSerializer(obj.admin).data