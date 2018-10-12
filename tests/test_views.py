from django.urls import reverse

from filer.admin.fileadmin import FileAdminChangeFrom
from tests.base import BaseFilerVersioningTestCase


class FilerFileAdminViewTests(BaseFilerVersioningTestCase):

    def test_upload_image_with_same_name(self):
        file_obj = self.create_file_obj('image.jpg')
        new_file = self.create_file('image.jpg')
        form = FileAdminChangeFrom(
            instance=file_obj,
            data={'file': new_file}
        )

        self.assertTrue(form.is_valid())
        form.save()
        file_obj.refresh_from_db()
        self.assertIn('image.jpg', file_obj.file.name)
        storage = file_obj.file.storage
        self.assertTrue(storage.exists(file_obj.file.name))

    def test_upload_image_with_different_name(self):
        file_obj = self.create_file_obj('image.jpg')
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
        file_obj = self.create_file_obj('file.txt')
        new_file = self.create_file('file.txt')
        form = FileAdminChangeFrom(
            instance=file_obj,
            data={'file': new_file}
        )

        self.assertTrue(form.is_valid())
        form.save()
        file_obj.refresh_from_db()
        self.assertIn('file.txt', file_obj.file.name)
        storage = file_obj.file.storage
        self.assertTrue(storage.exists(file_obj.file.name))

    def test_upload_file_with_different_name(self):
        file_obj = self.create_file_obj('file.txt')
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

    def test_not_allow_user_delete_file(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.file.get_admin_delete_url())
        self.assertEqual(response.status_code, 403)

    def test_not_allow_user_delete_folder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.folder.get_admin_delete_url())
        self.assertEqual(response.status_code, 403)

    def test_not_allow_user_edit_folder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.folder.get_admin_change_url())
        self.assertEqual(response.status_code, 403)

    def test_blocked_directory_listing_links(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
            )

        self.assertNotContains(response, '/en/admin/filer/folder/{}/change/'.format(self.folder.id))
        self.assertNotContains(response, '/en/admin/filer/folder/{}/delete/'.format(self.folder_inside.id))
        self.assertNotContains(response, '/en/admin/filer/file/{}/delete/'.format(self.file.id))
        self.assertNotContains(
            response,
            '<a href="#" class="js-action-delete" title="Delete"><span class="fa fa-trash"></span></a>',
        )
        self.assertNotContains(
            response,
            '<a href="#" class="js-action-copy" title="Copy"><span class="fa fa-copy"></span></a>',
        )
        self.assertNotContains(
            response,
            '<a href="#" class="js-action-move" title="Move"><span class="fa fa-cut"></span></a>',
        )
        self.assertNotContains(
            response,
            '<a href="#" class="js-action-move" title="Move"><span class="fa fa-cut"></span></a>',
        )
