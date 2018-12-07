from copy import deepcopy

from filer.admin.fileadmin import FileAdminChangeFrom
from filer.admin.imageadmin import ImageAdminForm

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerFileAdminFormTests(BaseFilerVersioningTestCase):

    def test_upload_image_with_same_name(self):
        file_obj = self.create_image_obj('image.jpg', publish=False)
        new_file = self.create_image('image.jpg')

        form = ImageAdminForm(
            data={'is_public': file_obj.is_public},
            files={'file': new_file},
            instance=file_obj,
        )

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(file_obj.file.name.split('/')[-1], 'image.jpg')
        storage = file_obj.file.storage
        self.assertTrue(storage.exists(file_obj.file.name))

    def test_upload_image_with_different_name(self):
        file_obj = self.create_image_obj('image.jpg', publish=False)
        new_file = self.create_file('new.jpg')
        form = ImageAdminForm(
            instance=file_obj,
            files={'file': new_file},
        )

        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'file': ['Uploaded file must have the same name as current file']},
        )

    def test_upload_file_with_same_name(self):
        file_obj = self.create_file_obj('file.txt', publish=False)
        new_file = self.create_file('file.txt')
        form = FileAdminChangeFrom(
            instance=file_obj,
            data={'is_public': file_obj.is_public},
            files={'file': new_file},
        )

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(file_obj.file.name.split('/')[-1], 'file.txt')
        storage = file_obj.file.storage
        self.assertTrue(storage.exists(file_obj.file.name))

    def test_upload_file_with_different_name(self):
        file_obj = self.create_file_obj('file.txt', publish=False)
        new_file = self.create_file('new.txt')
        form = FileAdminChangeFrom(
            instance=file_obj,
            files={'file': new_file},
        )

        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'file': ['Uploaded file must have the same name as current file']},
        )

    def test_prevent_same_name_files_in_folder(self):
        grouper = FileGrouper.objects.create()

        self.create_image_obj('image.jpg', grouper=grouper, publish=False)
        file_obj = self.create_image_obj('image.jpg', grouper=grouper, publish=False)
        self.create_image_obj('image.jpg', publish=False)

        form = ImageAdminForm(
            instance=deepcopy(file_obj),
            data={'name': ''},
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'name': ['File with name "image.jpg" already exists in "Unsorted Uploads" folder']},
        )

        form = ImageAdminForm(
            instance=deepcopy(file_obj),
            data={'name': 'test.jpg'},
        )
        self.assertTrue(form.is_valid())

        form = ImageAdminForm(
            instance=deepcopy(file_obj),
            data={'name': 'image.jpg'},
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'name': ['File with name "image.jpg" already exists in "Unsorted Uploads" folder']},
        )

        form = ImageAdminForm(
            instance=deepcopy(file_obj),
            data={'changed_filename': 'image.jpg'},
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'name': ['File with name "image.jpg" already exists in "Unsorted Uploads" folder']},
        )
