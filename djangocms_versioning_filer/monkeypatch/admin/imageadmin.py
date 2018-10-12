import filer
from filer.admin.imageadmin import ImageAdminForm

from djangocms_versioning_filer.monkeypatch.admin import clean


def init(self, *args, **kwargs):
    super(ImageAdminForm, self).__init__(*args, **kwargs)
    if 'grouper' in self.fields:
        self.fields.pop('grouper')
filer.admin.imageadmin.ImageAdminForm.__init__ = init  # noqa: E305
filer.admin.imageadmin.ImageAdminForm.clean = clean(
    filer.admin.imageadmin.ImageAdminForm.clean
)
