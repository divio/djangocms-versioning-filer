from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


class FilerVersioningAudioPluginAppConfig(AppConfig):
    name = 'djangocms_versioning_filer.plugins.audio'
    verbose_name = _('django CMS versioning filer audio plugin')

    def ready(self):
        try:
            apps.get_app_config('djangocms_versioning_filer')
            apps.get_app_config('djangocms_audio')
        except LookupError:
            raise ImproperlyConfigured(
                'djangocms_versioning_filer or djangocms_audio not found in INSTALLED_APPS. Please '
                'add that two apps above {}'.format(self.name)
            )
