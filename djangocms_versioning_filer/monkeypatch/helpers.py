from collections import OrderedDict

from django.contrib.admin.templatetags.admin_list import result_headers, ORDER_VAR
from django.utils.http import urlencode
from filer.admin import FolderAdmin
from filer.models import Folder


class SortableHeaderHelper:
    """
    Object used to build the sortable headers in the monkey patched directory_listing view. Implements the minimum
    required attributes and methods to allow us to use the django provided result_headers templatetag function, rather
    than using a full ChangeList class which this method expects.
    """

    # attrs required for by result_headers
    model = Folder
    model_admin = FolderAdmin
    # action_checkbox needs to be included so that the column numbers are correctly aligned
    list_display = ["action_checkbox", "name", "owner", "modified_at"]
    sortable_by = ["name", "owner", "modified_at"]

    def __init__(self, request):
        self.params = dict(request.GET.items())
        self.sortable_headers = [header for header in result_headers(self) if header["sortable"]]

    @property
    def num_headers_sorted(self):
        """
        Count the number of headers currently sorted by
        """
        return len([header for header in self.sortable_headers if header["sorted"]])

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
        ordered_by = self.params.get(ORDER_VAR)
        ordering = OrderedDict()
        if not ordered_by:
            # default to indicate ordered by name column, as this is the default ordering in the directory_listing view
            ordering[self.list_display.index("name")] = "asc"
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
