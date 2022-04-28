from unittest import TestCase
from unittest.mock import Mock

from cms import app_registration
from cms.test_utils.testcases import CMSTestCase

from djangocms_versioning.helpers import nonversioned_manager
from filer.models import File, Folder

from djangocms_versioning_filer.cms_config import FilerVersioningExtension
from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class CMSConfigExtensionTestCase(CMSTestCase, TestCase):
    def setUp(self):
        app_registration.get_cms_extension_apps.cache_clear()
        app_registration.get_cms_config_apps.cache_clear()

    def test_file_changelist_configuration_can_be_set(self):
        """
        Ensure that the configuration for the list file_changelist_actions can be set
        by the cms_config setting: djangocms_versioning_filer_file_changelist_actions
        """
        expected_config_value = [
            "some_value"
        ]
        extension = FilerVersioningExtension()
        cms_config = Mock(
            djangocms_versioning_filer_enabled=True,
            djangocms_versioning_enabled=False,
            djangocms_versioning_filer_file_changelist_actions=expected_config_value,
            app_config=Mock(label="testing_versioning_filer_config"),
        )

        extension.configure_app(cms_config)

        self.assertEqual(extension.file_changelist_actions, expected_config_value)


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
        self.assertIn('/media/filer_public/', file_obj.url)
        self.assertIn('test-test.doc', file_obj.url)
        draft_file_path = file_obj.file.path
        self.assertTrue(storage.exists(draft_file_path))

        version = file_obj.versions.first()
        version.publish(self.superuser)
        with nonversioned_manager(File):
            file_obj.refresh_from_db()

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

        self.assertFalse(storage.exists(published_file_path))
        self.assertTrue(storage.exists(self.file.file.path))
        self.assertIn('/media/filer_public', self.file.url)
        self.assertIn('test.pdf', self.file.url)
