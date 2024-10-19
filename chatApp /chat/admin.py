from django.contrib import admin

# Register your models here.

from .models import ChatRoom, Message

@admin.register(ChatRoom)
class MessageRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'room', 'timestamp')
    search_fields = ('text',)
