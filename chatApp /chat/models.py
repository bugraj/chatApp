from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, rate_plan='basic'):
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            username=username,
            rate_plan=rate_plan
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, rate_plan='pro'):
        user = self.create_user(
            username=username,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

RATE_PLAN_CHOICES = [
    ('basic', 'Basic'),
    ('pro', 'Pro'),
]

class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    rate_plan = models.CharField(max_length=10, choices=RATE_PLAN_CHOICES, default='basic')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, perm, obj=None):
        return True

    @property
    def is_staff(self):
        return self.is_admin


ROOM_TYPE_CHOICES = [
    ('individual', 'Individual'),
    ('group', 'Group'),
]

class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    members = models.ManyToManyField(User, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='individual')


    def __str__(self):
        return self.name
    
    class Meta:
        permissions = [
            ('can_create_message_room', 'Can create message rooms'),
        ]

class Message(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.text[:50]}..."
    

