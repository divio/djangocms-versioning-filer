from .base import BaseFilerVersioningTestCase

from djangocms_versioning_filer.plugins.picture.cms_plugins import (
    VersionedPictureForm,
)


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
                'file_grouper': self.image,
                'template': 'default',
            },
        )
        self.assertTrue(form.is_valid())
        plugin = form.save()
        self.assertEqual(plugin.file_grouper, self.image_grouper)
        self.assertEqual(plugin.picture, self.image)
