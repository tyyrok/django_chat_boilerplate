from django.contrib import admin
from chat.models import Conversation, Message, GroupMessage, GroupConversation

# Register your models here.
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(GroupConversation)
admin.site.register(GroupMessage)