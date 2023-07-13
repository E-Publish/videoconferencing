from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User, Group
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
    access = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='local_admin'), label='Доступ', required=False)
    users_list = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='common_user'),
        widget=forms.CheckboxSelectMultiple,
        label='Открыть для пользователей',
        required=False
    )
    access_by_link = forms.BooleanField(label='Доступ по ссылке', required=False)

    def clean_access(self):
        access = self.cleaned_data.get('access')
        if access:
            user = self.cleaned_data['access']
            user_id = user.id
        else:
            user_id = 0
        return user_id

    def clean_users_list(self):
        users_list = self.cleaned_data.get('users_list')
        user_ids = []
        if users_list:
            for user in users_list:
                user_ids.append(user.id)
        return user_ids

    class Meta:
        model = ArchivesData
        fields = ('name', 'lifetime', 'is_unremovable', 'participants', 'description', 'is_private', 'access',
                  'users_list', 'access_by_link')
        widgets = {
            'lifetime': DateInput(),
        }


class EditUserInfoForm(forms.ModelForm):
    username = forms.CharField(label='Логин', required=False)
    first_name = forms.CharField(label='Имя', required=False)
    last_name = forms.CharField(label='Фамилия', required=False)
    email = forms.EmailField(label='Электронная почта', required=False)
    is_staff = forms.BooleanField(label='Администратор', required=False)
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Роль',
        required=False,
        widget=forms.Select(attrs={'class': 'my-select'}),
        empty_label=None
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'groups')


class TechnicalSupportEditUserInfoForm(forms.ModelForm):
    username = forms.CharField(label='Логин', required=False)
    first_name = forms.CharField(label='Имя', required=False)
    last_name = forms.CharField(label='Фамилия', required=False)
    email = forms.EmailField(label='Электронная почта', required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class AddUserForm(forms.ModelForm):
    username = forms.CharField(label='Логин')
    first_name = forms.CharField(label='Имя')
    last_name = forms.CharField(label='Фамилия')
    email = forms.EmailField(label='Электронная почта')
    is_staff = forms.BooleanField(label='Администратор', required=False)
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Роль',
        required=False,
        widget=forms.Select(attrs={'class': 'my-select'}),
        empty_label=None
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'groups')


class LocalAdminAddUserForm(forms.ModelForm):
    username = forms.CharField(label='Логин')
    first_name = forms.CharField(label='Имя')
    last_name = forms.CharField(label='Фамилия')
    email = forms.EmailField(label='Электронная почта')
    groups = forms.ModelChoiceField(
        queryset=Group.objects.filter(name='common_user'),
        label='Роль',
        required=False,
        widget=forms.HiddenInput(),
        initial=Group.objects.get(name='common_user')
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups')


class TechnicalSupportAddUserForm(forms.ModelForm):
    username = forms.CharField(label='Логин')
    first_name = forms.CharField(label='Имя')
    last_name = forms.CharField(label='Фамилия')
    email = forms.EmailField(label='Электронная почта')
    groups = forms.ModelChoiceField(
        queryset=Group.objects.filter(name='local_admin'),
        label='Роль',
        required=False,
        widget=forms.HiddenInput(),
        initial=Group.objects.get(name='local_admin')
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups')
