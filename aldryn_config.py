from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        constraints = settings.get('FILER_FILE_CONSTRAINTS', [])
        if 'djangocms_versioning_filer.helpers.filename_exists' not in constraints:
            constraints.append('djangocms_versioning_filer.helpers.filename_exists')
        settings['FILER_FILE_CONSTRAINTS'] = constraints
        return settings
