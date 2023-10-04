from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from chat.consumers.group_chat_consumer import GroupChatConsumer
from chat.consumers.private_chat_consumer import ChatConsumer
from chat.consumers.notification_consumer import NotificationConsumer
from chat.middleware import TokenAuthMiddleware
import json

User = get_user_model()

class AuthWebsocketCommunicator(WebsocketCommunicator):
    def __init__(self, application, path, headers=None, subprotocols=None, user=None):
        super(AuthWebsocketCommunicator, self).__init__(application, path, headers, subprotocols)
        if user is not None:
            self.scope['user'] = user

class ChatTest(TestCase):
    fixtures = ['users.json', 'conversations.json', 'messages.json', 
                'group_conversations.json', 'group_messages.json']
    
    @classmethod
    def setUpTestData(cls):
        user = User.objects.all()[0]
        cls.token = Token.objects.create(user=user)
    
    async def test_1_chat_consumer_without_credentials(self):

        communicator = AuthWebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path='/chats/test__test2/'
        )
        connected, subprotocol = await communicator.connect()
        assert not connected
    
    async def test_2_chat_consumer_create_new_chat(self):
        conversation_name = "test__test3"
        communicator = AuthWebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path=f'/chats/{conversation_name}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"conversation_name": conversation_name}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()
        assert response == {'type': 'welcome_message', 'message': "You've started a new chat"}
        await communicator.disconnect()
    
    async def test_3_chat_consumer_send_message(self):
        conversation_name = "test__test2"
        test_message = "Test message!"
        communicator = AuthWebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path=f'/chats/{conversation_name}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"conversation_name": conversation_name}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()
        assert 'online_user_list' in response.values()

        response = await communicator.receive_json_from()# last messages
        assert 'last_50_messages' in response.values()
        
        response = await communicator.receive_json_from()# user join
        assert 'user_join' in response.values()
        
        await communicator.send_json_to({"type": "chat_message", "message": test_message})
        response = await communicator.receive_json_from()
        assert 'chat_message_echo' in response.values()
        
        await communicator.send_json_to({"type": "typing", "typing": "content"})
        response = await communicator.receive_json_from()
        assert 'typing' in response.values()
        
        await communicator.disconnect()
        
class GroupChatTest(TestCase):
    fixtures = ['users.json', 'conversations.json', 'messages.json', 
                'group_conversations.json', 'group_messages.json']
    group_conversation_name_new = "group_chat_with__test__2"
    group_conversation_name = "group_chat_with__test__1"
    test_message = "Test message!"
    
    @classmethod
    def setUpTestData(cls):
        user = User.objects.all()[0]
        cls.token = Token.objects.create(user=user)
    
    async def test_1_group_chat_consumer_create_new_chat(self):
        communicator = AuthWebsocketCommunicator(
            application=GroupChatConsumer.as_asgi(),
            path=f'/group_chats/{self.group_conversation_name_new}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"group_chat_name": self.group_conversation_name_new}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()
        assert 'redirect' in response.values()
        assert 'group_chat_with__test__2' in response.values()
        
        await communicator.disconnect()
        
    async def test_2_group_chat_consumer_add_new_member(self):
        communicator = AuthWebsocketCommunicator(
            application=GroupChatConsumer.as_asgi(),
            path=f'/group_chats/{self.group_conversation_name}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"group_chat_name": self.group_conversation_name}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()# last messages
        assert 'last_50_group_messages' in response.values()
        
        response = await communicator.receive_json_from()# members list
        assert 'members_list' in response.values()
        
        response = await communicator.receive_json_from()# user join
        assert 'user_join' in response.values()
        
        await communicator.send_json_to({"type": "add_member", "name": "test4"})
        
        response = await communicator.receive_json_from()
        assert 'members_list' in response.values()
        
        response = await communicator.receive_json_from()
        assert 'User test4 was added to the chat' in response['message']['content']

        await communicator.disconnect()
        
    async def test_3_group_chat_consumer_remove_member(self):
        communicator = AuthWebsocketCommunicator(
            application=GroupChatConsumer.as_asgi(),
            path=f'/group_chats/{self.group_conversation_name}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"group_chat_name": self.group_conversation_name}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()# last messages
        assert 'last_50_group_messages' in response.values()
        
        response = await communicator.receive_json_from()# members list
        assert 'members_list' in response.values()
        
        response = await communicator.receive_json_from()# user join
        assert 'user_join' in response.values()
        
        await communicator.send_json_to({"type": "remove_member", "name": "test3"})
        
        response = await communicator.receive_json_from()
        assert 'members_list' in response.values()
        
        response = await communicator.receive_json_from()
        assert 'User test3 was removed from the chat' in response['message']['content']

        await communicator.disconnect()
        
    async def test_4_group_chat_consumer_send_message(self):
        
        communicator = AuthWebsocketCommunicator(
            application=GroupChatConsumer.as_asgi(),
            path=f'/group_chats/{self.group_conversation_name}/',
            user=self.token.user
        )
        communicator.scope['url_route'] = {'kwargs':{"group_chat_name": self.group_conversation_name}}
        connected, subprotocol = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()# last messages
        assert 'last_50_group_messages' in response.values()
        
        response = await communicator.receive_json_from()# members list
        assert 'members_list' in response.values()
        
        response = await communicator.receive_json_from()# user join
        assert 'user_join' in response.values()
        
        await communicator.send_json_to({"type": "chat_message", "message": self.test_message})
        
        response = await communicator.receive_json_from()
        assert self.test_message in response['message']['content']

        await communicator.disconnect()

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