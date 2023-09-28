from chat.views import ConversationViewSet, MessageViewSet, UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
 
router.register("conversations", ConversationViewSet)
router.register("messages", MessageViewSet)
router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls