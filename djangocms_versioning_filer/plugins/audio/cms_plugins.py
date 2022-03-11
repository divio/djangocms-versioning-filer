from django.utils.translation import gettext_lazy as _

from cms.plugin_pool import plugin_pool

from djangocms_audio.cms_plugins import (
    AudioFilePlugin as BaseAudioFilePlugin,
    AudioTrackPlugin as BaseAudioTrackPlugin,
)

from .models import VersionedAudioFile, VersionedAudioTrack


class AudioFilePlugin(BaseAudioFilePlugin):
    model = VersionedAudioFile

    fieldsets = [
        (None, {
            'fields': (
                'file_grouper',
                'text_title',
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'text_description',
                'attributes',
            )
        })
    ]

    def get_render_template(self, context, instance, placeholder):
        return 'djangocms_versioning_filer/plugins/{}/audio_file.html'.format(
            context['audio_template']
        )


class AudioTrackPlugin(BaseAudioTrackPlugin):
    model = VersionedAudioTrack

    fieldsets = [
        (None, {
            'fields': (
                'kind',
                'file_grouper',
                'srclang',
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'label',
                'attributes',
            )
        })
    ]

    def get_render_template(self, context, instance, placeholder):
        return 'djangocms_versioning_filer/plugins/{}/audio_track.html'.format(
            context['audio_template']
        )


plugin_pool.unregister_plugin(BaseAudioFilePlugin)
plugin_pool.unregister_plugin(BaseAudioTrackPlugin)
plugin_pool.register_plugin(AudioFilePlugin)
plugin_pool.register_plugin(AudioTrackPlugin)
