from djangocms_versioning.exceptions import ConditionFailed
from djangocms_versioning.models import Version

from djangocms_versioning_filer.models import FileGrouper
from djangocms_versioning_filer.monkeypatch.models import (
    is_file_content_valid_for_discard,
    is_file_content_valid_for_revert,
)

from .base import BaseFilerVersioningTestCase


class FilerVersioningChecksTestCase(BaseFilerVersioningTestCase):

    def test_checks_only_filer_models(self):
        # Dont expect to raise any error
        self.assertEquals(
            is_file_content_valid_for_discard(self.page_draft_version, self.superuser),
            None,
        )
        self.assertEquals(
            is_file_content_valid_for_revert(self.page_draft_version, self.superuser),
            None,
        )

    def test_check_is_file_content_valid_for_discard(self):
        file_grouper = FileGrouper.objects.create()
        self.create_file_obj(
            original_filename='name.docx',
            grouper=file_grouper,
            publish=False,
        )
        discard_file = self.create_file_obj(
            original_filename='name2.docx',
            grouper=file_grouper,
            publish=True,
        )
        self.create_file_obj(
            original_filename='name.docx',
            publish=False,
        )
        with self.assertRaises(ConditionFailed):
            is_file_content_valid_for_discard(
                Version.objects.get_for_content(discard_file),
                self.superuser,
            )

        file_grouper = FileGrouper.objects.create()
        self.create_file_obj(
            original_filename='name.docx',
            folder=self.folder,
            grouper=file_grouper,
            publish=False,
        )
        self.create_file_obj(
            original_filename='name23.docx',
            folder=self.folder,
            grouper=file_grouper,
            publish=False,
        )
        discard_file = self.create_file_obj(
            original_filename='name2.docx',
            folder=self.folder,
            grouper=file_grouper,
            publish=True,
        )
        self.create_file_obj(
            original_filename='name.docx',
            folder=self.folder,
            publish=False,
        )
        self.assertEquals(
            is_file_content_valid_for_discard(
                Version.objects.get_for_content(discard_file),
                self.superuser,
            ),
            None,
        )

    def test_check_is_file_content_valid_for_revert(self):
        file_grouper = FileGrouper.objects.create()
        revert_file = self.create_file_obj(
            original_filename='name.docx',
            grouper=file_grouper,
            publish=False,
        )
        self.create_file_obj(
            original_filename='name2.docx',
            grouper=file_grouper,
            publish=True,
        )
        self.create_file_obj(
            original_filename='name.docx',
            publish=False,
        )
        with self.assertRaises(ConditionFailed):
            is_file_content_valid_for_revert(
                Version.objects.get_for_content(revert_file),
                self.superuser,
            )

        file_grouper = FileGrouper.objects.create()
        revert_file = self.create_file_obj(
            original_filename='name2.docx',
            folder=self.folder,
            grouper=file_grouper,
            publish=False,
        )
        self.create_file_obj(
            original_filename='name2.docx',
            folder=self.folder,
            grouper=file_grouper,
            publish=True,
        )
        self.create_file_obj(
            original_filename='name.docx',
            folder=self.folder,
            publish=False,
        )
        self.assertEquals(
            is_file_content_valid_for_revert(
                Version.objects.get_for_content(revert_file),
                self.superuser,
            ),
            None,
        )
