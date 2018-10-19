from cms.api import add_plugin
from cms.models import CMSPlugin
from cms.toolbar.utils import get_object_preview_url

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerAudioPluginTestCase(BaseFilerVersioningTestCase):

    def setUp(self):
        super().setUp()
        self.audio_file_grouper = FileGrouper.objects.create()
        self.audio_file = self.create_file_obj(
            original_filename='test.mp3',
            folder=self.folder,
            grouper=self.audio_file_grouper,
        )

    def test_add_plugin(self):
        parent_plugin = add_plugin(
            self.placeholder,
            'AudioPlayerPlugin',
            language=self.language,
            template='default',
        )
        uri = self.get_add_plugin_uri(
            placeholder=self.placeholder,
            plugin_type='AudioFilePlugin',
            language=self.language,
            parent=parent_plugin,
        )

        with self.login_user_context(self.superuser):
            data = {'file_grouper': self.audio_file.pk}
            response = self.client.post(uri, data)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        self.assertEquals(plugin.get_bound_plugin().file_grouper.file.url, self.audio_file.url)

    def test_plugin_rendering(self):
        parent_plugin = add_plugin(
            self.placeholder,
            'AudioPlayerPlugin',
            language=self.language,
            template='default',
        )
        audio_file_plugin = add_plugin(
            self.placeholder,
            'AudioFilePlugin',
            language=self.language,
            target=parent_plugin,
            file_grouper=self.audio_file_grouper,
        )
        audio_file_grouper_2 = FileGrouper.objects.create()
        audio_track_file_obj = self.create_file_obj(
            original_filename='sandstorm-subtitles.mp3',
            folder=self.folder,
            grouper=audio_file_grouper_2,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))
        self.assertContains(response, self.audio_file.url)
        self.assertNotContains(response, audio_track_file_obj.url)

        draft_file = self.create_file_obj(
            original_filename='sandstorm.ogg',
            folder=self.folder,
            grouper=self.audio_file_grouper,
            publish=False,
        )
        add_plugin(
            self.placeholder,
            'AudioTrackPlugin',
            language=self.language,
            target=audio_file_plugin,
            file_grouper=audio_file_grouper_2,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))
        self.assertContains(response, draft_file.url)
        self.assertContains(response, audio_track_file_obj.url)

    def test_audio_folder_plugin(self):
        audio_player_plugin = add_plugin(
            self.placeholder,
            'AudioPlayerPlugin',
            language=self.language,
            template='default',
        )
        add_plugin(
            self.placeholder,
            'AudioFolderPlugin',
            language=self.language,
            target=audio_player_plugin,
            audio_folder=self.folder,
        )
        file_grouper_1 = FileGrouper.objects.create()
        published_nonaudio_file = self.create_file_obj(
            original_filename='published.txt',
            folder=self.folder,
            grouper=file_grouper_1,
            publish=True,
        )

        draft_file = self.create_file_obj(
            original_filename='draft.mp3',
            folder=self.folder,
            grouper=self.audio_file_grouper,
            publish=False,
        )

        file_grouper_2 = FileGrouper.objects.create()
        draft_file_2 = self.create_file_obj(
            original_filename='draft2.mp3',
            folder=self.folder,
            grouper=file_grouper_2,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))

        self.assertContains(response, draft_file.url)
        self.assertContains(response, draft_file_2.url)
        self.assertNotContains(response, published_nonaudio_file.url)
        self.assertNotContains(response, self.audio_file.url)
