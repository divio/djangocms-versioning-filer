from django.utils.translation import ugettext as _

import filer
from filer.admin.fileadmin import ChangeFilenameFormMixin
from filer.fields.multistorage_file import MultiStorageFieldFile


def change_filename_form_clean(self):
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
filer.admin.fileadmin.ChangeFilenameFormMixin.clean = change_filename_form_clean  # noqa: E305
