from django.contrib import admin
from chat.models import Conversation, Message, GroupMessage

# Register your models here.
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(GroupMessage)