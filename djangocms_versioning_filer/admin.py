import copy

from djangocms_versioning.admin import VersioningAdminMixin
from djangocms_versioning.models import Version


class VersioningFilerAdminMixin(VersioningAdminMixin):

    # Path for filer change form
    change_form_template = 'admin/filer/change_form.html'

    def get_fieldsets(self, request, obj=None):
        version = Version.objects.get_for_content(obj)
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = copy.deepcopy(fieldsets)
        if not version.check_modify.as_bool(request.user):
            for fieldset in fieldsets:
                fieldset[1]['fields'] = tuple(
                    f for f in fieldset[1]['fields'] if f != 'changed_filename'
                )
        return fieldsets
