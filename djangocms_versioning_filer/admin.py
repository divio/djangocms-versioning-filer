import copy

from django.conf.urls import url
from djangocms_versioning.admin import VersioningAdminMixin
from djangocms_versioning.models import Version
from .monkeypatch.admin.clipboardadmin import file_constraints_check


class VersioningFilerAdminMixin(VersioningAdminMixin):

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

    def get_urls(self):
        return [
               url(r'^operations/upload/check/(?P<folder_id>[0-9]+)/$',
                   file_constraints_check,
                   name='filer-check_file_constraints'),
               url(r'^operations/upload/check/no_folder/$',
                   file_constraints_check,
                   name='filer-check_file_constraints'),
           ] + super().get_urls()
