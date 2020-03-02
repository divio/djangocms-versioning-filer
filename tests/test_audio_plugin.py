from cms.api import add_plugin
from cms.models import CMSPlugin
from cms.toolbar.utils import get_object_edit_url, get_object_preview_url

from djangocms_versioning_filer.models import FileGrouper
from djangocms_versioning_filer.templatetags.versioning_filer import get_url

from .base import CONTEXT, BaseFilerVersioningTestCase


class FilerAudioPluginTestCase(BaseFilerVersioningTestCase):

    def setUp(self):
        super().setUp()
        self.audio_file_grouper = FileGrouper.objects.create()
        self.audio_file = self.create_file_obj(
            original_filename='test.mp3',
            folder=self.folder,
            grouper=self.audio_file_grouper,
        )
        self.client.force_login(self.superuser)

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

        data = {'file_grouper': self.audio_file_grouper.pk}
        response = self.client.post(uri, data)
        self.assertEquals(response.status_code, 200)

        plugin = CMSPlugin.objects.latest('pk')
        audioplayer = plugin.get_bound_plugin()
        self.assertEquals(audioplayer.file_grouper.file.url, self.audio_file.url)

    def test_plugin_rendering(self):
        """
        Previews does not contain the source for drafts.
        Edit urls contains the source for drafts.
        """

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
        unpublished_audio_track = self.create_file_obj(
            original_filename='sandstorm-subtitles.mp3',
            folder=self.folder,
            grouper=audio_file_grouper_2,
            publish=False,
        )
        unpublished_audio_url = get_url(CONTEXT, unpublished_audio_track)

        response = self.client.get(
            get_object_preview_url(self.placeholder.source, self.language)
        )
        self.assertContains(response, self.audio_file.url)
        self.assertNotContains(response, unpublished_audio_url)

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
        unpublished_audio_url = get_url(CONTEXT, unpublished_audio_track)
        draft_url = get_url(CONTEXT, draft_file)

        preview_url = get_object_preview_url(self.placeholder.source, self.language)
        response = self.client.get(preview_url)

        self.assertNotContains(response, draft_url)
        self.assertNotContains(response, unpublished_audio_url)

        edit_url = get_object_edit_url(self.placeholder.source, self.language)
        response = self.client.get(edit_url)

        self.assertContains(response, draft_url)
        self.assertContains(response, unpublished_audio_url)

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

        response = self.client.get(
            get_object_preview_url(self.placeholder.source, self.language)
        )

        draft_url = get_url(CONTEXT, draft_file)
        draft_url2 = get_url(CONTEXT, draft_file_2)

        self.assertContains(response, draft_url)
        self.assertContains(response, draft_url2)
        self.assertNotContains(response, published_nonaudio_file.url)
        self.assertNotContains(response, self.audio_file.url)
