from django import forms
from django.utils.translation import ugettext_lazy as _

from cms.plugin_pool import plugin_pool

from djangocms_picture.cms_plugins import PicturePlugin as BasePicturePlugin

from .models import OverridenPicture


class OverridenPictureForm(forms.ModelForm):
    file_grouper = 

    class Meta:
        model = OverridenPicture
        fields = '__all__'
        widgets = {
            'caption_text': forms.Textarea(attrs={'rows': 2}),
        }


class PicturePlugin(BasePicturePlugin):
    model = OverridenPicture
    form = OverridenPictureForm

    fieldsets = [
        (None, {
            'fields': (
                'file_grouper',
                'external_picture',
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'template',
                ('width', 'height'),
                'alignment',
                'caption_text',
                'attributes',
            )
        }),
        (_('Link settings'), {
            'classes': ('collapse',),
            'fields': (
                ('link_url', 'link_page'),
                'link_target',
                'link_attributes',
            )
        }),
        (_('Cropping settings'), {
            'classes': ('collapse',),
            'fields': (
                ('use_automatic_scaling', 'use_no_cropping'),
                ('use_crop', 'use_upscale'),
                'thumbnail_options',
            )
        })
    ]

    def get_render_template(self, context, instance, placeholder):
        return 'djangocms_versioning_filer/plugins/{}/picture.html'.format(instance.template)


plugin_pool.unregister_plugin(BasePicturePlugin)
plugin_pool.register_plugin(PicturePlugin)
