from filer.admin.fileadmin import FileAdminChangeFrom
from tests.base import BaseFilerVersioningTestCase


class FilerFileAdminFormTests(BaseFilerVersioningTestCase):

    def test_upload_image_with_same_name(self):
        file_obj = self.create_file_obj('image.jpg', publish=False)
        new_file = self.create_file('image.jpg')
        form = FileAdminChangeFrom(
            instance=file_obj,
            data={'file': new_file}
        )

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(file_obj.file.name.split('/')[-1], 'image.jpg')
        storage = file_obj.file.storage
        self.assertTrue(storage.exists(file_obj.file.name))

    def test_upload_image_with_different_name(self):
        file_obj = self.create_file_obj('image.jpg', publish=False)
        new_file = self.create_file('new.jpg')
        form = FileAdminChangeFrom(
            instance=file_obj,
            data={'file': new_file}
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
            data={'file': new_file}
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
            data={'file': new_file}
        )

        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors,
            {'file': ['Uploaded file must have the same name as current file']},
        )
