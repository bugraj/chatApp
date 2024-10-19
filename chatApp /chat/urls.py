from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.contrib.auth.views import LogoutView


from . import views

urlpatterns = [
    # Basic urls
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),

    # feature specific urls
    path('create-chat-room/', views.create_chat_room, name='create_chat_room'),
    path('add-friend/', views.add_friend, name='add_friend'),
    path('chat/<int:chat_room_id>/', views.chat_view, name='chat'),
    path('send_message/<int:chat_room_id>/', views.send_message, name='send_message'),


    # fallback urls
    path('test/', views.test, name='test'),
    re_path(r'^.*$', RedirectView.as_view(url='/home/')),
]
