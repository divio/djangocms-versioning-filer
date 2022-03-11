from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class FilerVersioningVideoPluginAppConfig(AppConfig):
    name = 'djangocms_versioning_filer.plugins.video'
    verbose_name = _('django CMS versioning filer video plugin')

    def ready(self):
        try:
            apps.get_app_config('djangocms_versioning_filer')
            apps.get_app_config('djangocms_video')
        except LookupError:
            raise ImproperlyConfigured(
                'djangocms_versioning_filer or djangocms_video not found in INSTALLED_APPS. Please '
                'add that two apps above {}'.format(self.name)
            )
