from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer
from .paginators import MessagePagination
from .models import Conversation, Message

User = get_user_model()

# Create your views here.
class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
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


class CustomObtainAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})