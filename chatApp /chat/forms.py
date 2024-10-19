from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import datetime


from .models import RATE_PLAN_CHOICES, ChatRoom,User

class UserCreationForm(UserCreationForm):
    rate_plan = forms.ChoiceField(choices=RATE_PLAN_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'rate_plan')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        rate_plan = cleaned_data.get('rate_plan')
        
        # Check if passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two passwords didn't match.")
        
        # Validate rate plan
        if rate_plan not in [choice[0] for choice in RATE_PLAN_CHOICES]:
            raise ValidationError(f"Invalid rate plan. Choose one of: {', '.join([f'{choice[0]} - {choice[1]}' for choice in RATE_PLAN_CHOICES])}")
        
        cleaned_data["password"] = cleaned_data["password1"]
        return cleaned_data


class CustomMemberField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({'class': 'selectpicker'})

    def label_from_instance(self, obj):
        return obj.username
    
    def to_python(self, value):
        if not value:
            return []
        return list(value)

    def validate(self, value):
        super().validate(value)
        if not value:
            raise forms.ValidationError("Please select at least one member.")

    def compress(self, data_list):
        return data_list


class ChatRoomForm(forms.ModelForm):
    members = CustomMemberField(queryset=User.objects.all(),required=True, widget=forms.CheckboxSelectMultiple)
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user is not None:
            self.fields['members'].queryset = self.fields['members'].queryset.exclude(id=self.current_user.id)

    class Meta:
        model = ChatRoom
        fields = ['name', 'description', 'members']

    def clean_members(self):
        data = self.cleaned_data['members']
        if not data:
            raise forms.ValidationError("Please select at least one member.")
        return data


class AddFriendForm(forms.ModelForm):
    members = CustomMemberField(queryset=User.objects.all(),required=True, widget=forms.CheckboxSelectMultiple)
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user is not None:
            self.fields['members'].queryset = self.fields['members'].queryset.exclude(id=self.current_user.id)


    class Meta:
        model = ChatRoom
        fields = ['members']

    def clean_members(self):
        data = self.cleaned_data['members']
        if not data:
            raise forms.ValidationError("Please select at least one member.")
        return data