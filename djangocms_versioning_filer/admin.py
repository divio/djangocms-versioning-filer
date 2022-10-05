import copy
from collections import OrderedDict

from django.contrib.admin.views.main import ChangeList

from djangocms_versioning.admin import VersioningAdminMixin
from djangocms_versioning.models import Version
from filer.admin import FolderAdmin
from filer.models import Folder


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


class SortableHeadersChangeList(ChangeList):

    model = Folder
    model_admin = FolderAdmin
    list_display = ["action_checkbox", "name", "owner", "modified_at"]
    sortable_by = ["name", "owner", "modified_at"]

    def __init__(self, request):  # noqa
        self.params = dict(request.GET.items())
        self.lookup_opts = self.model._meta
