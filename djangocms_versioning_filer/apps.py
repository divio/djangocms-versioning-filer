from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FilerVersioningAppConfig(AppConfig):
    name = 'djangocms_versioning_filer'
    verbose_name = _('django CMS versioning filer')

    def ready(self):
        from . import monkeypatch  # noqa: F401
