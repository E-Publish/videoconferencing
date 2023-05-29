from django import forms
from django.contrib.auth.models import User
from django.forms import TextInput
from prompt_toolkit.widgets import TextArea

from .models import ArchivesData


class DateInput(forms.DateInput):
    input_type = 'date'


class EditArchiveInfoForm(forms.ModelForm):
    name = forms.CharField(label='Название', required=False, widget=forms.Textarea(attrs={'rows': 1}))
    lifetime = forms.DateField(label='Время жизни', widget=DateInput())
    is_unremovable = forms.BooleanField(label='Неудаляемый', required=False)
    participants = forms.CharField(label='Участники', required=False, widget=forms.Textarea(attrs={'rows': 1}))
    description = forms.CharField(label='Описание', required=False, widget=forms.Textarea(attrs={'rows': 1}))
    is_private = forms.BooleanField(label='Приватный', required=False)

    class Meta:
        model = ArchivesData
        fields = ('name', 'lifetime', 'is_unremovable', 'participants', 'description', 'is_private')
        widgets = {
            'lifetime': DateInput(),
        }


class EditUserInfoForm(forms.ModelForm):
    username = forms.CharField(label='Логин', required=False)
    first_name = forms.CharField(label='Имя', required=False)
    last_name = forms.CharField(label='Фамилия', required=False)
    email = forms.EmailField(label='Электронная почта', required=False)
    is_staff = forms.BooleanField(label='Администратор', required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')


class AddUserForm(forms.ModelForm):
    username = forms.CharField(label='Логин')
    first_name = forms.CharField(label='Имя')
    last_name = forms.CharField(label='Фамилия')
    email = forms.EmailField(label='Электронная почта')
    is_staff = forms.BooleanField(label='Администратор', required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')
