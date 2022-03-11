from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class FilerVersioningPicturePluginAppConfig(AppConfig):
    name = 'djangocms_versioning_filer.plugins.picture'
    verbose_name = _('django CMS versioning filer picture plugin')

    def ready(self):
        try:
            apps.get_app_config('djangocms_versioning_filer')
            apps.get_app_config('djangocms_picture')
        except LookupError:
            raise ImproperlyConfigured(
                'djangocms_versioning_filer or djangocms_picture not found in INSTALLED_APPS. Please '
                'add that two apps above {}'.format(self.name)
            )
