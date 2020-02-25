from cms.api import add_plugin
from cms.models import CMSPlugin, PageContent
from cms.toolbar.utils import get_object_edit_url, get_object_preview_url
from cms.views import details

from djangocms_versioning.constants import DRAFT
from filer.models import Folder

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerFilePluginTestCase(BaseFilerVersioningTestCase):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

        self.draft_file_grouper = FileGrouper.objects.create()
        self.draft_file = self.create_file_obj(
            original_filename='test_draft.pdf',
            folder=self.folder,
            grouper=self.draft_file_grouper,
            publish=False,
        )

    def add_plugin(self, grouper_pk):
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='FilePlugin',
            language=self.language,
        )

        data = {'file_grouper': grouper_pk, 'template': 'default'}
        response = self.client.post(uri, data)
        return response

    def detail_response(self, page):
        """Renders the article page, it's in draft at first so we also publish it"""
        pagecontent = PageContent._original_manager.get(page=self.page.pk)
        content_version = pagecontent.versions.all()[0]
        content_version.publish(self.superuser)

        url = page.get_absolute_url()
        request = self.get_request(url)
        response = details(request, page.get_path('en'))
        return response

    def test_render_detail_with_published_file(self):
        """Rendering the article page should show the file"""
        self.add_plugin(self.file_grouper.pk)

        response = self.detail_response(self.page)
        self.assertContains(response, self.file.url)

    def test_render_detail_with_draft_file_only(self):
        """Rendering article page with draft file does not render the draft file"""
        self.add_plugin(self.draft_file_grouper)

        response = self.detail_response(self.page)
        self.assertNotContains(response, self.draft_file.url)
        self.assertNotContains(response, 'href="/media')

    def test_render_detail_with_published_file_and_draft(self):
        """
        Rendering article page with a file that has both a draft and published
        file will render the published file.
        """
        self.assertEqual(self.file.versions.all().count(), 1)
        version = self.file.versions.all().first()
        v2 = version.copy(self.superuser)

        self.assertEqual(v2.state, DRAFT)
        self.assertEqual(v2.grouper.pk, self.file.grouper.pk)

        self.add_plugin(self.file_grouper.pk)

        response = self.detail_response(self.page)
        self.assertContains(response, self.file.url)

        # clean-up
        v2.delete()

    def test_edit_endpoint_with_published_file(self):
        """Edit endpoint contains published file"""
        self.add_plugin(self.file_grouper.pk)

        response = self.client.get(get_object_edit_url(self.placeholder.source))
        self.assertContains(response, self.file.url)

    def test_edit_endpoint_with_draft_file(self):
        """Edit endpoint contains draft file"""
        self.add_plugin(self.draft_file_grouper.pk)

        response = self.client.get(get_object_edit_url(self.placeholder.source))
        self.assertContains(response, self.draft_file.url)

    def test_edit_endpoint_with_published_file_and_draft(self):
        """Edit endpoint contains draft file when there is a published
        and a draft version."""
        self.assertEqual(self.file.versions.all().count(), 1)
        version = self.file.versions.all().first()
        v2 = version.copy(self.superuser)

        self.assertEqual(v2.state, DRAFT)
        self.assertEqual(v2.grouper.pk, self.file.grouper.pk)

        self.add_plugin(self.file_grouper.pk)

        response = self.client.get(get_object_edit_url(self.placeholder.source))
        self.assertContains(response, v2.content.url)

        # clean-up
        v2.delete()

    def test_add_plugin(self):
        response = self.add_plugin(self.file_grouper.pk)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.get_bound_plugin().file_grouper.file.url, self.file.url)

    def test_plugin_rendering(self):
        """Test plugin rendering for published file"""
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
