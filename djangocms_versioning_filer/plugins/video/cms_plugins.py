from django.utils.translation import gettext_lazy as _

from cms.plugin_pool import plugin_pool

from djangocms_video.cms_plugins import (
    VideoPlayerPlugin as BaseVideoPlayerPlugin,
    VideoSourcePlugin as BaseVideoSourcePlugin,
    VideoTrackPlugin as BaseVideoTrackPlugin,
)
from djangocms_video.forms import VideoPlayerPluginForm

from .models import (
    VersionedVideoPlayer,
    VersionedVideoSource,
    VersionedVideoTrack,
)


class VersionedVideoPlayerPluginForm(VideoPlayerPluginForm):
    class Meta:
        model = VersionedVideoPlayer
        exclude = []


class VideoPlayerPlugin(BaseVideoPlayerPlugin):
    model = VersionedVideoPlayer
    form = VersionedVideoPlayerPluginForm

    fieldsets = [
        (None, {
            'fields': (
                'template',
                'label',
            )
        }),
        (_('Embed video'), {
            'classes': ('collapse',),
            'fields': (
                'embed_link',
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'poster_grouper',
                'attributes',
            )
        })
    ]

    def get_render_template(self, context, instance, placeholder):
        return 'djangocms_versioning_filer/plugins/{}/video_player.html'.format(
            instance.template
        )


class VideoSourcePlugin(BaseVideoSourcePlugin):
    model = VersionedVideoSource

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
        return 'djangocms_versioning_filer/plugins/{}/video_source.html'.format(
            context['video_template']
        )


class VideoTrackPlugin(BaseVideoTrackPlugin):
    model = VersionedVideoTrack

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
        return 'djangocms_versioning_filer/plugins/{}/video_track.html'.format(
            context['video_template']
        )


plugin_pool.unregister_plugin(BaseVideoPlayerPlugin)
plugin_pool.unregister_plugin(BaseVideoSourcePlugin)
plugin_pool.unregister_plugin(BaseVideoTrackPlugin)

plugin_pool.register_plugin(VideoPlayerPlugin)
plugin_pool.register_plugin(VideoSourcePlugin)
plugin_pool.register_plugin(VideoTrackPlugin)
