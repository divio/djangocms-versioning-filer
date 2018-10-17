from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        try:
            settings['INSTALLED_APPS'].insert(
                settings['INSTALLED_APPS'].index('filer'),
                'djangocms_versioning_filer',
            )
        except ValueError:
            settings['INSTALLED_APPS'].append('djangocms_versioning_filer')
        return settings
