from django.utils.translation import ugettext as _

import filer
from filer.models import File

from ...helpers import check_file_label_exists_in_folder


def save_model(func):
    """Override the FileAdmin save_model method"""
    def inner(self, request, obj, form, change):
        func(self, request, obj, form, change)
        try:
            from djangocms_internalsearch.helpers import emit_content_change
        except ImportError:
            return

        emit_content_change(obj, sender=self.model)
    return inner
filer.admin.fileadmin.FileAdmin.save_model = save_model(  # noqa: E305
    filer.admin.fileadmin.FileAdmin.save_model
)


def clean(func):
    """
    Override the ChangeFilenameFormMixin clean method
    to block uploading with different file name
    """
    def inner(self):
        current_filename = self.instance.file.name.split('/')[-1]
        cleaned_data = func(self)
        file = cleaned_data.get('file')
        if file and file.name.split('/')[-1].lower() != current_filename.lower():
            self.add_error('file', _('Uploaded file must have the same name as current file'))

        folder_name = getattr(self.instance.folder, 'name', None) or _('Unsorted Uploads')
        file_name = cleaned_data.get('name') or cleaned_data.get('changed_filename') or self.instance.original_filename
        if file_name and check_file_label_exists_in_folder(
            file_name, self.instance.folder, exclude_file_pks=[self.instance.pk]
        ):
            msg = _('File with name "{}" already exists in "{}" folder').format(file_name, folder_name)
            self.add_error('name', msg)
        return cleaned_data
    return inner
filer.admin.fileadmin.FileAdminChangeFrom.clean = clean(  # noqa: E305
    filer.admin.fileadmin.FileAdminChangeFrom.clean
)


def init(func):
    """
    Override the FileAdminChangeFrom __init__ method
    to pop grouper field form required fields
    """
    def inner(self, *args, **kwargs):
        func(self, *args, **kwargs)
        if 'grouper' in self.fields:
            self.fields.pop('grouper')
    return inner
filer.admin.fileadmin.FileAdminChangeFrom.__init__ = init(  # noqa: E305
    filer.admin.fileadmin.FileAdminChangeFrom.__init__
)


def has_delete_permission(self, request, obj=None):
    return False
filer.admin.fileadmin.FileAdmin.has_delete_permission = has_delete_permission  # noqa: E305
