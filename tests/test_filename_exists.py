import json
from .base import BaseFilerVersioningTestCase
from django.urls import reverse


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
            self.assertIn('success', json.loads(response.content))
            self.assertEqual(False, json.loads(response.content)['success'])
            self.assertIn('message', json.loads(response.content))

    def test_filename_not_exists(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-check_file_constraints',
                        kwargs={'folder_id': self.folder.id})
                + '?filename={}'.format('test.txt'),

            )
            self.assertIn('success', json.loads(response.content))
            self.assertEqual(True, json.loads(response.content)['success'])
