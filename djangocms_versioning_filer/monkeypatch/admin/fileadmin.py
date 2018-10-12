from django.utils.translation import ugettext as _

import filer
from filer.admin.fileadmin import FileAdminChangeFrom


def clean(func):
    """
    Override the ChangeFilenameFormMixin clean method
    to block uploading with different file name
    """
    def inner(self):
        current_filename = self.instance.file.name.split('/')[-1]
        cleaned_data = func(self)
        file = cleaned_data.get('file')
        if (
            file and
            file.name.split('/')[-1] != current_filename
        ):
            self.add_error('file', _('Uploaded file must have the same name as current file'))
        return cleaned_data
    return inner


def init(self, *args, **kwargs):
    super(FileAdminChangeFrom, self).__init__(*args, **kwargs)
    if 'grouper' in self.fields:
        self.fields.pop('grouper')


def has_delete_permission(self, request, obj=None):
    return False
filer.admin.fileadmin.FileAdminChangeFrom.__init__ = init  # noqa: E305
filer.admin.fileadmin.FileAdmin.has_delete_permission = has_delete_permission  # noqa: E305
filer.admin.fileadmin.FileAdminChangeFrom.clean = clean(
    filer.admin.fileadmin.FileAdminChangeFrom.clean
)
