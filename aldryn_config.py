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

        constraints = settings.get('FILER_FILE_CONSTRAINTS', [])
        if 'djangocms_versioning_filer.helpers.filename_exists' not in constraints:
            constraints.append('djangocms_versioning_filer.helpers.filename_exists')
        settings['FILER_FILE_CONSTRAINTS'] = constraints
        return settings
