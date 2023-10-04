from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your tests here.
class TestApi(APITestCase):
    fixtures = ['users.json', 'conversations.json', 'messages.json', 
                'group_conversations.json', 'group_messages.json']
    
    @classmethod
    def setUpTestData(cls):
        user = User.objects.all()[0]
        print("User", user.username)
        cls.token = Token.objects.create(user=user)
    
    def setUp(self) -> None:
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
    def test_1_get_user_view_set(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test")
        self.assertContains(response, "test2")
        self.assertContains(response, "test3")
    
    def test_2_get_conversation_viewset(self):
        response = self.client.get('/api/conversations/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "test3")
    
    def test_3_get_message_viewset(self):
        conversation_name = "test__test2"
        url = f'/api/messages/?conversation={conversation_name}'
        response = self.client.get(url)
        self.assertContains(response, "650169d4-4da3-44bb-8fc0-c7bb5a7a3087")
        self.assertContains(response, "08cd297c-ba0c-485a-97c0-1585a9519218")
        self.assertContains(response, "776890fb-0f15-4c59-90c3-88fbc3adb2f0")
        self.assertNotContains(response, "c2c280b2-4cf9-4bb7-bc9d-b8ae9c7e7d97")
        
    
    def test_4_get_group_conversation_viewset(self):
        response = self.client.get('/api/group_conversations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "43d80639-a10d-4b46-b872-b561c0c4b7b2")
        self.assertNotContains(response, "00d80639-a10d-4b46-b872-b561c0c4b7b2")
        
    
    def test_5_get_group_message_viewset(self):
        group_conversation_name = "group_chat_with__test__1"
        url = f"/api/group_messages/?group_conversation={group_conversation_name}"
        response = self.client.get(url)
        self.assertContains(response, "0ac284e4-b641-446c-85d4-87b36ece602e")
        self.assertContains(response, "0c2c0c9b-2c50-4b3a-ae7c-1a5ca1080805")
        self.assertContains(response, "0b5ac10c-9021-41d6-bacf-29374dc9a3c9")
        self.assertNotContains(response, "0e8037be-39f2-4849-9121-89385eceaa02")
        