import filer
from filer.admin.imageadmin import ImageAdminForm

from djangocms_versioning_filer.monkeypatch.admin import clean


def init(func):
    """
    Override the ImageAdminForm __init__ method
    to pop grouper field form required fields
    """
    def inner(self, *args, **kwargs):
        func(self, *args, **kwargs)
        if 'grouper' in self.fields:
            self.fields.pop('grouper')
    return inner
filer.admin.imageadmin.ImageAdminForm.__init__ = init(
    filer.admin.imageadmin.ImageAdminForm.__init__
)

filer.admin.imageadmin.ImageAdminForm.clean = clean(
    filer.admin.imageadmin.ImageAdminForm.clean
)
