from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages as form_error_message
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Max as models_max

from .models import ChatRoom, Message, User, ROOM_TYPE_CHOICES
from .forms import ChatRoomForm, UserCreationForm, AddFriendForm



def __print_error(err):
    print(f"Huh got error!!!!!!!!!!!!!!!!!!!!!!!!!!\n{err}")

# Create your views here.

def signup_view(request):
    print("in signup view")

    # If user is already logged in, logout the user
    if request.user.is_authenticated:
        logout(request)

    try:
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                print("User Created Successfully")
                login(request, user)
                return redirect('/home')
            else:
                form_error_message.error(request, form.errors)
                return redirect('signup')
    except Exception as e:
        __print_error(e)

    form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    print("in login view")
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
    return render(request, 'login.html')


def logout_view(request):
    print("logout view....")
    logout(request)
    return redirect('/home')


def test(request):
    return render(request, 'test.html')


def has_permission_to_create_message_room(user):
    return user.has_perm('chat.can_create_message_room')

@login_required
@user_passes_test(has_permission_to_create_message_room)
def create_chat_room(request):
    errors = None
     
    try:
        if request.method == 'POST':
            form = ChatRoomForm(request.POST, current_user = request.user)
            if form.is_valid():
                chat_room = form.save(commit=False)
                chat_room.creator = request.user
                chat_room.room_type = ROOM_TYPE_CHOICES[1][0]
                chat_room.save()
                print('message_room')

                # Add the members, including the creator to the ManyToMany field
                form.save_m2m()  # Save the members selected in the form
                chat_room.members.add(request.user)  # Optionally add the creator to the members
                
                print(f"message room created; {chat_room}")
                return redirect('chat', chat_room_id=chat_room.id)
            else:
                errors = form.errors
                print(errors)
    except Exception as e:
        __print_error(e)
    __print_error("new create form")
    new_form = ChatRoomForm(current_user = request.user)
    return render(request, 'createChatRoom.html', {'form': new_form, 'errors': errors})


@login_required
def add_friend(request):
    if request.method == 'POST':
        friend_username = request.POST.get('friend_username')
        user = request.user

        try:
            friend = User.objects.get(username=friend_username)
            if friend == user:
                form_error_message.error(request, "You cannot add yourself as a friend.")
            else:
                # Check if a direct chat room already exists between the users
                existing_room = ChatRoom.objects.filter(
                    room_type='individual',
                    members=user
                ).filter(members=friend).first()

                if existing_room:
                    form_error_message.info(request, f"You already have a chat room with {friend.username}.")
                    return redirect('chat', chat_room_id=existing_room.id)
                else:
                    # Create a new chat room for both users
                    chat_room_name = f"{friend.username} & {user.username}" if friend.username < user.username else f"{user.username} & {friend.username}"
                    chat_room = ChatRoom.objects.create(
                        name=chat_room_name,
                        description=f"Private chat room between {user.username} and {friend.username}",
                        creator=user,
                        room_type='individual'
                    )
                    chat_room.members.add(user, friend)
                    form_error_message.success(request, f"Chat room created with {friend.username}.")
                    # Redirect to the newly created chat room
                    return redirect('chat', chat_room_id=chat_room.id)

        except User.DoesNotExist:
            form_error_message.error(request, "User not found. Please enter a valid username.")
    
    return redirect('home')


@login_required
def home(request):
    print("In Home view ...")
    
    search_query = request.GET.get('q', '')  # Get the search query from the request
    sort_option = request.GET.get('sort', 'recent')  # Get the sorting option from the request, default is 'recent'
    user = request.user

    # Fetch all chat rooms the user is a member of
    chat_rooms = ChatRoom.objects.filter(members=user)

    # If there's a search query, filter the chat rooms by name
    if search_query:
        chat_rooms = chat_rooms.filter(name__icontains=search_query)

    # Sorting options
    if sort_option == 'alphabetical':
        chat_rooms = chat_rooms.order_by('name')
    elif sort_option == 'alphabetical_reverse':
        chat_rooms = chat_rooms.order_by('-name')
    else:
        chat_rooms = chat_rooms.annotate(last_message_timestamp=models_max('messages__timestamp')).order_by('-last_message_timestamp')

    # Annotate each chat room with its last message
    chat_rooms_with_last_message = []
    for room in chat_rooms:
        last_message = room.messages.order_by('-timestamp').first()
        
        # Determine display name for individual chat rooms
        if room.room_type == 'individual':
            other_member = room.members.exclude(id=user.id).first()
            display_name = other_member.username if other_member else room.name
        else:
            display_name = room.name

        chat_rooms_with_last_message.append({
            'room': room,
            'display_name': display_name,
            'last_message': last_message,
        })

    # Get all users excluding the current user
    all_users = User.objects.exclude(id=user.id)

    context = {
        'chat_rooms_with_last_message': chat_rooms_with_last_message,
        'search_query': search_query,
        'sort_option': sort_option,
        'all_users': all_users,  # Pass all users for the dropdown
    }

    return render(request, 'home.html', context)


MESSAGE_PER_PAGE = 50

@login_required
def chat_view(request, chat_room_id):
    # Fetch the chat room by ID, or return a 404 if not found
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)

    # Determine the appropriate name for individual chat rooms
    if chat_room.room_type == 'individual':
        # Get the other member of the room
        other_member = chat_room.members.exclude(id=request.user.id).first()
        chat_room_display_name = other_member.username if other_member else chat_room.name
    else:
        # For group chat, keep the original name
        chat_room_display_name = chat_room.name

    # Fetch the latest 50 messages, ordered by timestamp descending
    messages = chat_room.messages.order_by('-timestamp')[:MESSAGE_PER_PAGE]
    
    # Reverse the messages to display them in the correct order (oldest at top)
    messages = reversed(messages)

    # Prepare context for rendering the template
    context = {
        'chat_room': chat_room,
        'chat_room_display_name': chat_room_display_name,
        'user': request.user,
        'messages': messages,
    }

    # Render the chat room template with the context
    return render(request, 'chat.html', context)



@login_required
@require_POST
def send_message(request, chat_room_id):
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)

    # Prepare context for rendering the template
    context = {
        'chat_room': chat_room,
        'user': request.user,
    }

    if request.method == 'POST':
       message_text = request.POST.get('message')
       if message_text:  # Check if the message is not empty
            # Create and save the new message instance
            Message.objects.create(
                text=message_text,
                author=request.user,
                room=chat_room
            )

    return redirect('chat', chat_room_id=chat_room_id)
