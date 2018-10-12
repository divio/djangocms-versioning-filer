from django.utils.translation import ugettext_lazy as _

from cms.plugin_pool import plugin_pool

from djangocms_file.cms_plugins import FilePlugin as BaseFilePlugin

from .models import VersionedFile


class FilePlugin(BaseFilePlugin):
    model = VersionedFile

    fieldsets = [
        (None, {
            'fields': (
                'file_grouper',
                'file_name',
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'template',
                ('link_target', 'link_title'),
                'show_file_size',
                'attributes',
            )
        }),
    ]

    def get_render_template(self, context, instance, placeholder):
        return 'djangocms_versioning_filer/plugins/{}/file.html'.format(instance.template)


plugin_pool.unregister_plugin(BaseFilePlugin)
plugin_pool.register_plugin(FilePlugin)
