from cms.test_utils.testcases import CMSTestCase

from filer.admin import FolderAdmin
from filer.models import Folder

from djangocms_versioning_filer.monkeypatch.helpers import SortableHeaderHelper


class TestSortableHeadersHelper(CMSTestCase):

    def test_init(self):
        """
        The SortableHeaderHelper should initialise with the correct attributes to build the sortable headers
        """
        request = self.get_request("/?o=1.2.3")

        helper = SortableHeaderHelper(request=request)

        self.assertEqual(helper.model, Folder)
        self.assertEqual(helper.model_admin, FolderAdmin)
        self.assertEqual(helper.list_display, ["action_checkbox", "name", "owner", "modified_at"])
        self.assertEqual(helper.sortable_by, ["name", "owner", "modified_at"])
        self.assertEqual(helper.params, {"o": "1.2.3"})
        self.assertEqual(helper.sortable_headers[0]["text"], "name")
        self.assertEqual(helper.sortable_headers[1]["text"], "owner")
        self.assertEqual(helper.sortable_headers[2]["text"], "modified at")

    def test_num_headers_sorted(self):
        """
        Check the number of sorted headers matches the number of columns specified in the querystring
        """
        test_cases = [
            # sorted by name column by default
            {"order_by_param": "", "expected_sorted": 1},
            {"order_by_param": "?o=1", "expected_sorted": 1},
            {"order_by_param": "?o=1.2", "expected_sorted": 2},
            {"order_by_param": "?o=1.2.3", "expected_sorted": 3},
        ]

        for case in test_cases:
            order_by_param = case["order_by_param"]
            num_expected_sorted = case["expected_sorted"]
            request = self.get_request(f"/{order_by_param}")
            helper = SortableHeaderHelper(request=request)
            with self.subTest(msg=f"Expected sorted by {num_expected_sorted}"):
                self.assertEqual(helper.num_headers_sorted, num_expected_sorted)

    def test_num_headers_sorted_no_params(self):
        """
        Should be 1 as by sorting by name is the default when no ordering specified
        """
        request = self.get_request("/")

        helper = SortableHeaderHelper(request=request)

        self.assertEqual(helper.num_headers_sorted, 1)

    def test_get_ordering_field_columns_no_ordering_param(self):
        """
        When no ordering is specified, it should default to the name column in ascending order
        """
        request = self.get_request("/")
        helper = SortableHeaderHelper(request)

        ordering = helper.get_ordering_field_columns()

        self.assertEqual(dict(ordering), {1: "asc"})

    def test_get_ordering_field_columns_with_ordering_param(self):
        """
        A dictionary of the row number and ordering type is returned to match the ordering querystring
        """
        test_cases = [
            {
                "qs": "1.2.3",
                "expected": {
                    1: "asc",
                    2: "asc",
                    3: "asc",
                }
            },
            {
                "qs": "1",
                "expected": {
                    1: "asc",
                }
            },
            {
                "qs": "2",
                "expected": {
                    2: "asc",
                }
            },
            {
                "qs": "3",
                "expected": {
                    3: "asc",
                }
            },

        ]
        for test_case in test_cases:
            qs = test_case["qs"]
            request = self.get_request(f"/?o={qs}")
            helper = SortableHeaderHelper(request)
            with self.subTest(msg=request):
                ordering = helper.get_ordering_field_columns()

                self.assertEqual(dict(ordering), test_case["expected"])

    def test_get_ordering_field_columns_descending(self):
        """
        When column number is preceded by - it is ordered in descending order
        """
        request = self.get_request("/?o=-1.-2.-3")
        helper = SortableHeaderHelper(request)

        ordering = helper.get_ordering_field_columns()
        expected = {
            1: "desc",
            2: "desc",
            3: "desc",
        }
        self.assertEqual(dict(ordering), expected)

    def test_get_ordering_field_invalid_value(self):
        """
        Invalid ordering values are ignored
        """
        request = self.get_request("/?o=foo.2.bar")
        helper = SortableHeaderHelper(request)

        ordering = helper.get_ordering_field_columns()
        expected = {
            2: "asc",
        }
        self.assertEqual(dict(ordering), expected)
