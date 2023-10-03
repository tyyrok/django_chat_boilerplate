from chat.views import ConversationViewSet, MessageViewSet, UserViewSet,  \
                       GroupConversationViewSet, GroupMessageViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
 
router.register("conversations", ConversationViewSet)
router.register("messages", MessageViewSet)
router.register("users", UserViewSet)
router.register("group_conversations", GroupConversationViewSet)
router.register("group_messages", GroupMessageViewSet)

app_name = "api"
urlpatterns = router.urls