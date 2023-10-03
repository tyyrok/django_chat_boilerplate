from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer, \
                         GroupConversationSerializer, GroupMessageSerializer
from .paginators import MessagePagination, GroupMessagePagination
from .models import Conversation, Message, GroupConversation, GroupMessage

User = get_user_model()

# Create your views here.
class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    @action(detail=False)
    def all(self, request): 
        serializer = UserSerializer(
            User.objects.all(), many=True, context={"request": request}
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)
    
class ConversationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.none()
    lookup_field = "name"
    
    
    def get_queryset(self):
        queryset = Conversation.objects.filter(
            name__contains=self.request.user.username
        )
        return queryset
    
    def get_serializer_context(self):
        return {"request": self.request, "user": self.request.user}
    
class MessageViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    queryset = Message.objects.none()
    pagination_class = MessagePagination
    
    def get_queryset(self):
        conversation_name = self.request.GET.get("conversation")
        queryset = (
            Message.objects.filter(
                conversation__name__contains=self.request.user.username,
            )
            .filter(conversation__name=conversation_name)
            .order_by("-timestamp")
        )
        return queryset
    
class GroupConversationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupConversationSerializer
    queryset = GroupConversation.objects.none()
    lookup_field = "name"
    
    def get_queryset(self):
        queryset = GroupConversation.objects.filter(
                members=self.request.user
        )
        return queryset
    
    def get_serializer_context(self):
        return {"request": self.request, "user": self.request.user}
    
class GroupMessageViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMessageSerializer
    queryset = GroupMessage.objects.none()
    pagination_class = GroupMessagePagination
    
    def get_queryset(self):
        group_conversation_name = self.request.GET.get("group_conversation")
        queryset = (
            GroupMessage.objects.filter(
                group_conversation__name__contains=self.request.user.username,
                group_conversation__members=self.request.user,
            )
        )
        return queryset

class CustomObtainAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})