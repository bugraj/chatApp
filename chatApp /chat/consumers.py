import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone 
import pytz  # Required for timezone conversion

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Rename to use room_id for consistency
        self.room_id = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Save the message to the database
        saved_message = await self.save_message(self.room_id, username, message)

        # Send message to room group, including timestamp
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': saved_message['text'],
                'username': saved_message['username'],
                'timestamp': saved_message['timestamp']  # IST timestamp included
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'timestamp': timestamp  # IST timestamp sent to WebSocket client
        }))

    @sync_to_async
    def save_message(self, room_id, username, message):
        # Add model import here to avoid issues with circular imports
        from .models import Message, ChatRoom, User

        # Save the message to the database
        user = User.objects.get(username=username)
        chat_room = ChatRoom.objects.get(id=room_id)
        new_message = Message.objects.create(room=chat_room, author=user, text=message)

        # Convert the timestamp to IST (Indian Standard Time)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_timestamp = new_message.timestamp.astimezone(ist_timezone)

        # Return details including the formatted timestamp in IST
        return {
            'text': new_message.text,
            'username': new_message.author.username,
            'timestamp': ist_timestamp.strftime('%Y-%m-%d %H:%M')  # Formatted IST timestamp
        }
