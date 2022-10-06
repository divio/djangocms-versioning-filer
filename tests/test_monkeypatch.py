from unittest.mock import MagicMock

from cms.test_utils.testcases import CMSTestCase
from django.db.models import QuerySet
from django.db.models.functions import Lower
from filer.models import Folder, File

from djangocms_versioning_filer.monkeypatch.admin.folderadmin import order_qs, ordering_mapping, validate_order_by


class TestFolderAdminOrderingMapping(CMSTestCase):

    def test_for_folder(self):
        result = ordering_mapping(Folder)
        expected = {
            "1": [Lower("name")],
            "2": ["owner__username"],
            "3": ["modified_at"],
            "-1": [Lower("name").desc()],
            "-2": ["-owner__username"],
            "-3": ["-modified_at"],
        }

        self.assertEqual(result, expected)

    def test_for_file(self):
        result = ordering_mapping(File)
        expected = {
            "1": [Lower("name"), Lower("original_filename")],
            "2": ["owner__username"],
            "3": ["modified_at"],
            "-1": [Lower("name").desc(), Lower("original_filename").desc()],
            "-2": ["-owner__username"],
            "-3": ["-modified_at"],
        }

        self.assertEqual(result, expected)


class TestFolderAdminValidateOrderBy(CMSTestCase):

    def setUp(self):
        self.mapping = {
            "1": "foo",
            "2": "bar",
            "3": "foobar",
        }

    def test_when_not_in_mapping(self):
        order_by = "9.8.7.6.foo"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, [])

    def test_when_in_mapping(self):
        order_by = "1.2.3"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, ["1", "2", "3"])

    def test_when_some_in_mapping(self):
        order_by = "1.2.3.4.5.6"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, ["1", "2", "3"])


class TestFolderAdminOrderQs(CMSTestCase):

    # def setUp(self):
    #     self.mapping = {
    #         "1": "foo",
    #         "2": "foo",
    #         "3": "foo",
    #     }

    def test_when_valid_order_by_string(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = File
        order_by = "2"

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with("owner__username")

    def test_when_invalid_order_by_string_file(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = File
        order_by = "4"

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with(Lower("name"), Lower("original_filename"))

    def test_when_invalid_order_by_string_folder(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = Folder
        order_by = "4"

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with(Lower("name"))

    def test_multiple_valid_ordering(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = File
        order_by = "1.2.3"

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with(
            Lower("name"), Lower("original_filename"), "owner__username", "modified_at",
        )

    def test_order_descending(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = File
        order_by = "-1.-2.-3"

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with(
            Lower("name").desc(), Lower("original_filename").desc(), "-owner__username", "-modified_at",
        )

    def test_order_rows_in_reverse(self):
        queryset = MagicMock(spec=QuerySet)
        queryset.model = File
        order_by = "3.2.1."

        order_qs(queryset, order_by)

        queryset.order_by.assert_called_once_with(
            "modified_at", "owner__username", Lower("name"), Lower("original_filename"),
        )
