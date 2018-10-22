from djangocms_versioning.admin import VersioningAdminMixin
from djangocms_versioning.models import Version


class VersioningFilerAdminMixin(VersioningAdminMixin):

    def get_fieldsets(self, request, obj=None):
        version = Version.objects.get_for_content(obj)
        if not self._can_modify_version(version, request.user):
            fieldsets = super().get_fieldsets(request, obj)
            fieldsets[1][1]['fields'] = tuple(
                f for f in fieldsets[1][1]['fields'] if f != 'changed_filename'
            )
        return fieldsets
