from django.contrib.auth.models import Permission

def create_message_room_permission():
    content_type = ContentType.objects.get(app_label='your_app_name', model='messageroom')
    permission = Permission.objects.create(
        codename='can_create_message_room',
        name='Can create message rooms',
        content_type_id=content_type.id
    )
    return permission
