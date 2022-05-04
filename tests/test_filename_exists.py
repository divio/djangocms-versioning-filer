import json

from django.urls import reverse

from .base import BaseFilerVersioningTestCase


class FileNameExistsTests(BaseFilerVersioningTestCase):

    def test_filename_exists(self):
        self.create_file_obj(
            original_filename='test.txt',
            content='some text',
            is_public=True,
            owner=self.superuser,
            folder=self.folder,
        )
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-check_file_constraints',
                        kwargs={'folder_id': self.folder.id})
                + '?filename={}'.format('test.txt'),
            )
            response = json.loads(response.content.decode('utf-8'))
            self.assertIn('success', response)
            self.assertEqual(False, response['success'])
            self.assertIn('error', response)
            self.assertIn('The file **test.txt** already exists, do you want to overwrite this?', response['error'])

    def test_filename_not_exists(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-check_file_constraints',
                        kwargs={'folder_id': self.folder.id})
                + '?filename={}'.format('test.txt'),

            )
            response = json.loads(response.content.decode('utf-8'))
            self.assertIn('success', response)
            self.assertEqual(True, response['success'])
            self.assertNotIn('error', response)
