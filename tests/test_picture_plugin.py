from cms.api import add_plugin
from cms.toolbar.utils import get_object_preview_url

from djangocms_versioning_filer.plugins.picture.cms_plugins import (
    VersionedPictureForm,
)

from .base import BaseFilerVersioningTestCase


class FilerPicturePluginTestCase(BaseFilerVersioningTestCase):

    def test_plugin_form_create_with_wrong_data(self):
        form = VersionedPictureForm(
            data={
                'file_grouper': self.file,
                'template': 'default',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Select a valid choice. That choice is not one of the available choices.',
            form.errors['file_grouper'],
        )
        self.assertIn(
            'You need to add either an image, or a URL linking to an external image.',
            form.errors['__all__'],
        )

    def test_plugin_form_create(self):
        form = VersionedPictureForm(
            data={
                'file_grouper': self.image.grouper.pk,
                'template': 'default',
                'use_responsive_image': 'yes'
            },
        )
        self.assertTrue(form.is_valid())
        plugin = form.save()
        self.assertEqual(plugin.file_grouper, self.image_grouper)
        self.assertEqual(plugin.picture, self.image)

    def test_plugin_rendering(self):
        add_plugin(
            self.placeholder,
            'PicturePlugin',
            language=self.language,
            template='default',
            file_grouper=self.image_grouper,
            use_no_cropping=True,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))

        self.assertContains(response, self.image.url)

        draft_image = self.create_image_obj(
            original_filename='draft-image.jpg',
            folder=self.folder,
            grouper=self.image_grouper,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))

        self.assertContains(response, draft_image.url)

    def test_plugin_rendering_thumbnails(self):
        add_plugin(
            self.placeholder,
            'PicturePlugin',
            language=self.language,
            template='default',
            file_grouper=self.image_grouper,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_preview_url(self.placeholder.source, self.language))

        self.assertContains(
            response,
            '/media/{}/{}'.format(self.image.file.thumbnail_basedir, self.image.file.name),
        )
