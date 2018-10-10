from django.utils.translation import ugettext as _

import filer


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
filer.admin.fileadmin.ChangeFilenameFormMixin.clean = clean(
    filer.admin.fileadmin.ChangeFilenameFormMixin.clean
)
