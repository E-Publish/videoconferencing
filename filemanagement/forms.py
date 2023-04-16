from django import forms

from simpleuserpage.models import ArchivesData


class AddNewArchiveForm(forms.ModelForm):

    class Meta:
        model = ArchivesData
        fields = ('code_name', 'is_private')
