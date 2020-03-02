from djangocms_versioning.helpers import nonversioned_manager
from filer.models import File, Folder

from djangocms_versioning_filer.models import FileGrouper
from djangocms_versioning_filer.templatetags.versioning_filer import get_url

from .base import CONTEXT, BaseFilerVersioningTestCase


class VersioningConfigTestCase(BaseFilerVersioningTestCase):

    def test_changing_file_path_when_publishing_file(self):

        folder = Folder.objects.create(name='folder_no_3', parent=self.folder_inside)
        grouper = FileGrouper.objects.create()
        file_obj = self.create_file_obj(
            original_filename='test-test.doc',
            folder=folder,
            grouper=grouper,
            publish=False,
        )
        storage = file_obj.file.storage
        draft_url = get_url(CONTEXT, file_obj)

        self.assertIn('/media/filer_public/', draft_url)
        self.assertIn('test-test.doc', draft_url)
        draft_file_path = file_obj.file.path
        self.assertTrue(storage.exists(draft_file_path))

        version = file_obj.versions.first()
        version.publish(self.superuser)
        with nonversioned_manager(File):
            file_obj.refresh_from_db()
            file_obj.grouper.file.refresh_from_db()

        self.assertEquals(
            file_obj.url,
            '/media/{}/{}/{}/test-test.doc'.format(
                self.folder.name, self.folder_inside.name, folder.name
            )
        )
        self.assertFalse(storage.exists(draft_file_path))
        self.assertTrue(storage.exists(file_obj.file.path))

    def test_changing_file_path_when_unpublishing_file(self):
        storage = self.file.file.storage
        published_file_path = self.file.file.path
        self.assertTrue(storage.exists(published_file_path))
        self.assertEquals(self.file.url, '/media/{}/test.pdf'.format(self.folder.name))
        self.assertTrue(storage.exists(published_file_path))

        version = self.file.versions.first()
        version.unpublish(self.superuser)
        with nonversioned_manager(File):
            self.file.refresh_from_db()

        unpublished_url = get_url(CONTEXT, self.file)
        self.assertFalse(storage.exists(published_file_path))
        self.assertTrue(storage.exists(self.file.file.path))
        self.assertIn('/media/filer_public', unpublished_url)
        self.assertIn('test.pdf', unpublished_url)
