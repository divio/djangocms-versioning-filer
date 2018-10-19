from django.utils.translation import ugettext as _

import filer


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
