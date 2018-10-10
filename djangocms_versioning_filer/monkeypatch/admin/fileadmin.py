from django import forms
from django.utils.translation import ugettext as _

import filer
from filer.fields.multistorage_file import MultiStorageFieldFile
from filer.models import File


class ChangeFilenameFormMixin(forms.Form):
    changed_filename = forms.CharField(
        max_length=256,
        required=False,
        label=_('Change file name'),
    )

    def __init__(self, *args, **kwargs):
        super(ChangeFilenameFormMixin, self).__init__(*args, **kwargs)
        instance = kwargs.pop('instance', None)
        if instance and instance.file:
            self.fields['changed_filename'].initial = instance.file.name.split('/')[-1]
        else:
            self.fields['changed_filename'].widget = forms.HiddenInput()

    def clean(self):
        present_filename = self.instance.file.name.split('/')[-1]
        cleaned_data = super(ChangeFilenameFormMixin, self).clean()
        file = cleaned_data.get('file')
        if (
                file and
                type(file) != MultiStorageFieldFile and
                file.name.split('/')[-1] != present_filename
        ):
            self.add_error('file', _('Upload file must have the same name as present file'))
        return self.cleaned_data

    def save(self, **kwargs):
        self.instance.new_filename = self.cleaned_data.get('changed_filename', None)
        return super(ChangeFilenameFormMixin, self).save(**kwargs)


class FileAdminChangeFrom(ChangeFilenameFormMixin, forms.ModelForm):
    class Meta(object):
        model = File
        exclude = ()
filer.admin.fileadmin.FileAdmin.form = FileAdminChangeFrom  # noqa: E305
