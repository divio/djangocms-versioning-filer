from cms.api import add_plugin
from cms.models import CMSPlugin
from cms.toolbar.utils import get_object_preview_url

from filer.models import Folder

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerFilePluginTestCase(BaseFilerVersioningTestCase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

    def test_add_plugin(self):
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='FilePlugin',
            language=self.language,
        )

        data = {'file_grouper': self.file_grouper.pk, 'template': 'default'}
        response = self.client.post(uri, data)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.get_bound_plugin().file_grouper.file.url, self.file.url)

    def test_plugin_rendering(self):
        add_plugin(
            self.placeholder,
            'FilePlugin',
            language=self.language,
            template='default',
            file_grouper=self.file_grouper,
        )

        response = self.client.get(
            get_object_preview_url(self.placeholder.source, self.language)
        )
        self.assertContains(response, self.file.url)

        draft_file = self.create_file_obj(
            original_filename='draft.txt',
            folder=self.folder,
            grouper=self.file_grouper,
            publish=False,
        )

        response = self.client.get(
            get_object_preview_url(self.placeholder.source, self.language)
        )
        self.assertContains(response, draft_file.url)

    def test_plugin_addition_with_multiple_content_versions_for_a_grouper(self):
        """
        The plugin should be able to select a file with multiple versions attached to a grouper.
        """
        self.client.force_login(self.superuser)
        folder = Folder.objects.create(name='test folder')
        file_grouper = FileGrouper.objects.create()
        self.create_file_obj(
            original_filename='myfile.txt',
            folder=folder,
            grouper=file_grouper,
            publish=True,
        )
        file_version_2 = self.create_file_obj(
            original_filename='myfile.txt',
            folder=folder,
            grouper=file_grouper,
            publish=False,
        )

        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='FilePlugin',
            language=self.language,
        )
        data = {'file_grouper': file_grouper.pk, 'template': 'default'}
        response = self.client.post(uri, data)
        plugin = CMSPlugin.objects.latest('pk')

        self.assertEquals(response.status_code, 200)
        self.assertEquals(plugin.get_bound_plugin().file_grouper.file.url, file_version_2.grouper.file.url)


class FilerFolderPluginTestCase(BaseFilerVersioningTestCase):

    def test_plugin_rendering(self):
        self.client.force_login(self.superuser)
        folder = Folder.objects.create(name='test folder 9')
        add_plugin(
            self.placeholder,
            'FolderPlugin',
            language=self.language,
            template='default',
            folder_src=folder,
        )
        file_grouper_1 = FileGrouper.objects.create()
        published_file = self.create_file_obj(
            original_filename='published.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=True,
        )

        draft_file = self.create_file_obj(
            original_filename='draft.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=False,
        )

        file_grouper_2 = FileGrouper.objects.create()
        draft_file_2 = self.create_file_obj(
            original_filename='draft2.txt',
            folder=folder,
            grouper=file_grouper_2,
            publish=False,
        )

        response = self.client.get(
            get_object_preview_url(self.placeholder.source, self.language)
        )

        self.assertContains(response, draft_file.url)
        self.assertContains(response, draft_file_2.url)
        self.assertNotContains(response, published_file.url)
