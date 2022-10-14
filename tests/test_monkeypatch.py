from unittest.mock import MagicMock

from django.db.models import QuerySet
from django.db.models.functions import Lower

from cms.test_utils.testcases import CMSTestCase

from filer.models import File, Folder

from djangocms_versioning_filer.monkeypatch.admin.folderadmin import (
    order_qs,
    ordering_mapping,
    validate_order_by,
)


class TestFolderAdminOrderingMapping(CMSTestCase):

    def test_for_folder(self):
        """
        The mapping used for the Folder model should not include original_filename
        """
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
        """
        The mapping used for the File model should include original_filename
        """
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
        """
        An empty list is returned when the values in the ordering string are in the mapping dictionary
        """
        order_by = "9.8.7.6.foo"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, [])

    def test_when_in_mapping(self):
        """
        A list of values that are in the mapping are returned
        """
        order_by = "1.2.3"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, ["1", "2", "3"])

    def test_when_some_in_mapping(self):
        """
        If a mixture of valid and invalid values are given, invalid values not included in the returned list
        """
        order_by = "1.2.3.4.5.6"

        result = validate_order_by(order_by_str=order_by, mapping=self.mapping)

        self.assertEqual(result, ["1", "2", "3"])


class TestFolderAdminOrderQs(CMSTestCase):

    def setUp(self):
        """
        The queryset is mocked so that we can assert that order_by is called with the correct argument
        """
        self.queryset = MagicMock(spec=QuerySet)

    def test_when_valid_order_by_string(self):
        """
        The queryset should be ordered by the correct field when the string contains a valid column number
        """
        self.queryset.model = File
        order_by = "2"

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with("owner__username")

    def test_when_invalid_order_by_string_file(self):
        """
        The queryset should be ordered by the fields for the name column when an invalid string is given
        """
        self.queryset.model = File
        order_by = "4"

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with(Lower("name"), Lower("original_filename"))

    def test_when_invalid_order_by_string_folder(self):
        """
        The queryset should be ordered by the fields for the name column when an invalid string is given
        """
        self.queryset.model = Folder
        order_by = "4"

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with(Lower("name"))

    def test_multiple_valid_ordering(self):
        """
        When the string contains multiple column numbers it should be ordered by each of them in the correct order
        """
        self.queryset.model = File
        order_by = "1.2.3"

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with(
            Lower("name"), Lower("original_filename"), "owner__username", "modified_at",
        )

    def test_order_descending(self):
        """
        When the string includes - before a column number the order_by query uses descending type
        """
        self.queryset.model = File
        order_by = "-1.-2.-3"

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with(
            Lower("name").desc(), Lower("original_filename").desc(), "-owner__username", "-modified_at",
        )

    def test_order_columns_in_reverse(self):
        """
        The order_by query respects the order of the column numbers in the given string
        """
        self.queryset.model = File
        order_by = "3.2.1."

        order_qs(self.queryset, order_by)

        self.queryset.order_by.assert_called_once_with(
            "modified_at", "owner__username", Lower("name"), Lower("original_filename"),
        )
