from django.utils.translation import ugettext as _

import filer
from filer.admin.fileadmin import ChangeFilenameFormMixin
from filer.fields.multistorage_file import MultiStorageFieldFile


def clean(func):
    """
    Override the ChangeFilenameFormMixin clean method
    to block uploading with different file name
    """
    def inner(self):
        present_filename = self.instance.file.name.split('/')[-1]
        cleaned_data = super(ChangeFilenameFormMixin, self).clean()
        file = cleaned_data.get('file')
        if (
                file and
                type(file) != MultiStorageFieldFile and
                file.name.split('/')[-1] != present_filename
        ):
            self.add_error('file', _('Upload file must have the same name as present file'))
        return func(self)
    return inner
filer.admin.fileadmin.ChangeFilenameFormMixin.clean = clean(
    filer.admin.fileadmin.ChangeFilenameFormMixin.clean
)
