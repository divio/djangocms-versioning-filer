import copy
from collections import OrderedDict

from django.utils.http import urlencode

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


class SortableHeadersChangeList:

    ORDER_VAR = "o"
    model = Folder
    model_admin = FolderAdmin
    # action_checkbox needs to be included so that the column numbers are correctly aligned when the result_headers
    # template tag runs through the list_display
    list_display = ["action_checkbox", "name", "owner", "modified_at"]
    sortable_by = ["name", "owner", "modified_at"]

    def __init__(self, request):
        self.params = dict(request.GET.items())

    def get_ordering_field_columns(self):
        """
        Build ordering dict made up of column number, and ordering type e.g.:
        {
            1: "asc",
            2: "desc",
            3: "asc",
        }
        This is then used by the result_headers templatetag to indicate which columns are being used for sorting.
        It is used purely for display purposes and to build the links used by the sorting headers.
        """
        ordered_by = self.params.get(self.ORDER_VAR)
        ordering = OrderedDict()
        if not ordered_by:
            # default to indicate ordering by name, as this is how the files are ordered by default in the
            # directory_listing view
            index = self.list_display.index("name")
            ordering[index] = "asc"
            return ordering

        for order in ordered_by.split("."):
            _, desc, col_num = order.rpartition('-')
            try:
                col_num = int(col_num)
            except ValueError:
                continue  # skip it
            ordering[col_num] = 'desc' if desc == '-' else 'asc'

        return ordering

    def get_query_string(self, new_params=None, remove=None):
        """
        Method copied unchanged from django.contrib.admin.views.main.ChangeList
        """
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))
