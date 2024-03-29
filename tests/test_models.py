from django.contrib.contenttypes.models import ContentType

from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.models import Version
from filer.models import File

from djangocms_versioning_filer.models import copy_file

from .base import BaseFilerVersioningTestCase


class FilerCopyFileMethodTests(BaseFilerVersioningTestCase):

    def test_copy_text_file(self):
        file = self.create_file_obj(
            original_filename='test.txt',
            content='some text',
            is_public=True,
            owner=self.superuser,
            folder=self.folder,
        )
        copy = copy_file(file)
        file.refresh_from_db()
        self.assertNotEqual(file.file.path, copy.file.path)
        self.assertTrue(file.file.storage.exists(file.file.path))
        self.assertTrue(copy.file.storage.exists(copy.file.path))
        self.assertFalse(file is copy)
        self.assertNotEqual(file.pk, copy.pk)
        self.assertTrue(copy.is_public)
        self.assertEqual(copy.folder, file.folder)
        self.assertEqual(copy.owner, self.superuser)
        self.assertEqual(copy.original_filename, 'test.txt')
        self.assertEqual(copy.original_filename, 'test.txt')
        self.assertEqual(copy.file.name.split('/')[-1], 'test.txt')
        self.assertEqual(copy.file.readlines(), [b'some text'])

    def test_copy_file_via_version_copy(self):
        version = Version.objects.get_for_content(self.image)
        new_version = version.copy(self.superuser)

        self.assertEquals(version.state, PUBLISHED)
        self.assertEquals(new_version.state, DRAFT)
        self.assertEquals(new_version.content_type_id, ContentType.objects.get_for_model(File).pk)
