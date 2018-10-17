from cms.api import add_plugin
from cms.models import CMSPlugin
from cms.toolbar.utils import get_object_preview_url

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerVideoPluginTestCase(BaseFilerVersioningTestCase):

    def setUp(self):
        super().setUp()
        self.video_file_grouper = FileGrouper.objects.create()
        self.video_file = self.create_file_obj(
            original_filename='test.mp4',
            folder=self.folder,
            grouper=self.video_file_grouper,
        )

    def test_add_plugin(self):
        parent_plugin = add_plugin(
            self.placeholder,
            'VideoPlayerPlugin',
            language=self.language,
            template='default',
            poster_grouper=self.image_grouper,
        )
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='VideoSourcePlugin',
            language=self.language,
            parent=parent_plugin,
        )

        with self.login_user_context(self.superuser):
            data = {'file_grouper': self.video_file_grouper.pk}
            response = self.client.post(uri, data)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.get_bound_plugin().file_grouper.file.url, self.video_file.url)

    def test_add_video_player_without_poster(self):
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='VideoPlayerPlugin',
            language=self.language,
        )

        with self.login_user_context(self.superuser):
            data = {'template': 'default'}
            response = self.client.post(uri, data)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.plugin_type, 'VideoPlayerPlugin')

    def test_add_video_player_with_wrong_file_type_for_poster(self):
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='VideoPlayerPlugin',
            language=self.language,
        )

        with self.login_user_context(self.superuser):
            data = {'template': 'default', 'poster_grouper': self.file_grouper.pk}
            self.client.post(uri, data)
        self.assertEquals(CMSPlugin.objects.count(), 0)

        with self.login_user_context(self.superuser):
            data = {'template': 'default', 'poster_grouper': self.image_grouper.pk}
            self.client.post(uri, data)
        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.plugin_type, 'VideoPlayerPlugin')
        self.assertEquals(plugin.get_bound_plugin().poster, self.image)

    def test_plugin_rendering(self):
        parent_plugin = add_plugin(
            self.placeholder,
            'VideoPlayerPlugin',
            language=self.language,
            template='default',
        )
        add_plugin(
            self.placeholder,
            'VideoSourcePlugin',
            language=self.language,
            target=parent_plugin,
            file_grouper=self.video_file_grouper,
        )
        video_file_grouper_2 = FileGrouper.objects.create()
        video_track_file_obj = self.create_file_obj(
            original_filename='sandstorm-subtitles.mp4',
            folder=self.folder,
            grouper=video_file_grouper_2,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))
        self.assertContains(response, self.video_file.url)
        self.assertNotContains(response, video_track_file_obj.url)

        draft_file = self.create_file_obj(
            original_filename='sandstorm.mp4',
            folder=self.folder,
            grouper=self.video_file_grouper,
            publish=False,
        )
        add_plugin(
            self.placeholder,
            'VideoTrackPlugin',
            language=self.language,
            target=parent_plugin,
            file_grouper=video_file_grouper_2,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))
        self.assertContains(response, draft_file.url)
        self.assertContains(response, video_track_file_obj.url)
