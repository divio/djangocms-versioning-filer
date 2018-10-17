from django.contrib.admin import helpers
from django.urls import reverse

from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.helpers import nonversioned_manager
from djangocms_versioning.models import Version
from filer.models import File, Folder

from djangocms_versioning_filer.models import FileGrouper

from .base import BaseFilerVersioningTestCase


class FilerViewTests(BaseFilerVersioningTestCase):

    def test_not_allow_user_delete_file(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.file.get_admin_delete_url())
        self.assertEqual(response.status_code, 403)

    def test_not_allow_user_delete_folder(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.folder.get_admin_delete_url())
        self.assertEqual(response.status_code, 403)

    def test_not_allow_rename_files(self):
        file_obj = self.create_file_obj(
            original_filename='rename.pdf',
            folder=self.folder,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'rename_files',
                    'post': 'yes',
                    'rename_format': 'new_name',
                    helpers.ACTION_CHECKBOX_NAME: 'file-%d' % (file_obj.id,),
                }
            )

        self.assertEquals(response.status_code, 200)
        original_filename = file_obj.original_filename
        filename = file_obj.file.name.split('/')[-1]
        file_obj.refresh_from_db()
        self.assertEqual(file_obj.original_filename, original_filename)
        self.assertEqual(file_obj.file.name.split('/')[-1], filename)

    def test_not_allow_move_files(self):
        file_obj = self.create_file_obj(
            original_filename='move_file.txt',
            folder=self.folder,
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'move_files_and_folders',
                    'post': 'yes',
                    'destination': self.folder2.id,
                    helpers.ACTION_CHECKBOX_NAME: 'file-%d' % (file_obj.id,),
                }
            )

        self.assertEquals(response.status_code, 200)
        file_obj.refresh_from_db()
        self.assertEqual(file_obj.folder_id, self.folder.id)
        self.assertIn(file_obj, self.folder.files)
        self.assertFalse(self.folder2.files)

    def test_copy_files_to_different_folder(self):
        dst_folder = Folder.objects.create()
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'copy_files_and_folders',
                    'post': 'yes',
                    'destination': dst_folder.id,
                    'suffix': '',
                    helpers.ACTION_CHECKBOX_NAME: [
                        'folder-{}'.format(self.folder_inside.id),
                        'file-{}'.format(self.file.id),
                    ],
                }
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.file, self.folder.files)
        self.assertTrue(self.folder.contains_folder(self.folder_inside))
        moved_file = Version._base_manager.last()
        moved_file.publish(self.superuser)
        dst_folder.refresh_from_db()
        self.assertIn(moved_file.content.file, dst_folder.files.values_list('file', flat=True))
        self.assertIn(self.folder_inside.name, dst_folder.get_children().values_list('name', flat=True))

    def test_copy_file_to_different_folder(self):
        dst_folder = Folder.objects.create()
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'copy_files_and_folders',
                    'post': 'yes',
                    'destination': dst_folder.id,
                    'suffix': '',
                    helpers.ACTION_CHECKBOX_NAME: 'file-{}'.format(self.file.id),
                }
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.file, self.folder.files)
        moved_file = Version._base_manager.last()
        moved_file.publish(self.superuser)
        dst_folder.refresh_from_db()
        self.assertIn(moved_file.content.file, dst_folder.files.values_list('file', flat=True))

    def test_copy_folder_to_different_folder(self):
        dst_folder = Folder.objects.create()
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'copy_files_and_folders',
                    'post': 'yes',
                    'destination': dst_folder.id,
                    'suffix': '',
                    helpers.ACTION_CHECKBOX_NAME: 'folder-{}'.format(self.folder_inside.id),
                }
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.folder_inside, self.folder.get_children())
        dst_folder.refresh_from_db()
        self.assertIn(self.folder_inside.name, dst_folder.get_children().values_list('name', flat=True))

    def test_do_not_copy_files_to_actual_folder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'copy_files_and_folders',
                    'post': 'yes',
                    'destination': self.folder.id,
                    helpers.ACTION_CHECKBOX_NAME: [
                        'file-{}'.format(self.file.id),
                        'folder-{}'.format(self.folder_inside.id),
                    ],
                }
            )

        self.assertEqual(response.status_code, 403)

    def test_do_not_copy_files_to_not_an_existing_folder(self):
        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.id}),
                data={
                    'action': 'copy_files_and_folders',
                    'post': 'yes',
                    'destination': 999,
                    helpers.ACTION_CHECKBOX_NAME: [
                        'file-{}'.format(self.file.id),
                        'folder-{}'.format(self.folder_inside.id),
                    ],
                }
            )

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
            '<a href="#" class="js-action-move" title="Move"><span class="fa fa-move"></span></a>',
        )
        self.assertContains(
            response,
            '<a href="#" class="js-action-copy" title="Copy"><span class="fa fa-copy"></span></a>',
        )

    def test_not_allow_create_duplicate_folder(self):
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='other', parent=folder)

        with self.login_user_context(self.superuser):
            url = reverse(
                'admin:filer-directory_listing-make_folder',
                kwargs={'folder_id': folder.id}
            ) + '?parent_id={}'.format(folder.id)
            response = self.client.post(
                url,
                data={
                    'name': 'other',
                    '_save': 'Save',
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Folder with this name already exists.')

    def test_not_allow_upload_duplicate_file(self):
        folder = Folder.objects.create(name='folder')
        file_obj = self.create_file_obj(
            original_filename='file.txt',
            folder=folder,
        )
        new_file = self.create_file('file.txt', 'new custom content.')

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': folder.id}),
                files={'file': new_file},
            )

        self.assertEquals(response.status_code, 200)
        folder.refresh_from_db()
        self.assertIn(file_obj, folder.files)
        file = open(folder.files.first().file.path)
        self.assertEqual(file.readline(), 'data')

    def test_canonical_view(self):
        with self.login_user_context(self.superuser):
            # testing published file
            response = self.client.get(self.file.canonical_url)
        self.assertRedirects(response, self.file.url)

        draft_file_in_the_same_grouper = self.create_file_obj(
            original_filename='test-1.pdf',
            folder=self.folder,
            grouper=self.file_grouper,
            publish=False,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(draft_file_in_the_same_grouper.canonical_url)
        self.assertRedirects(response, draft_file_in_the_same_grouper.url)

        draft_file = self.create_file_obj(
            original_filename='test-1.pdf',
            folder=Folder.objects.create(name='folder test 55'),
            grouper=FileGrouper.objects.create(),
            publish=False,
        )
        with self.login_user_context(self.superuser):
            response = self.client.get(draft_file.canonical_url)
        self.assertRedirects(response, draft_file.url)

    def test_ajax_upload_clipboardadmin(self):
        file = self.create_file('test2.pdf')
        same_file_in_other_folder_grouper = FileGrouper.objects.create()
        same_file_in_other_folder = self.create_file_obj(
            original_filename='test2.pdf',
            folder=Folder.objects.create(),
            grouper=same_file_in_other_folder_grouper,
            publish=True,
        )
        self.assertEquals(FileGrouper.objects.count(), 3)

        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEquals(FileGrouper.objects.count(), 4)
        with nonversioned_manager(File):
            files = self.folder.files.all()
        new_file = files.latest('pk')
        new_file_grouper = FileGrouper.objects.latest('pk')
        self.assertEquals(new_file.label, 'test2.pdf')
        self.assertEquals(new_file.grouper, new_file_grouper)
        versions = Version.objects.filter_by_grouper(new_file_grouper)
        self.assertEquals(versions.count(), 1)
        self.assertEquals(versions[0].state, DRAFT)

        # Checking existing in self.folder file
        self.assertEquals(self.file.label, 'test.pdf')
        self.assertEquals(self.file.grouper, self.file_grouper)
        versions = Version.objects.filter_by_grouper(self.file_grouper)
        self.assertEquals(versions.count(), 1)
        self.assertEquals(versions[0].state, PUBLISHED)

        # Checking file in diffrent folder with the same name as newly created file
        self.assertEquals(same_file_in_other_folder.label, 'test2.pdf')
        self.assertEquals(same_file_in_other_folder.grouper, same_file_in_other_folder_grouper)
        versions = Version.objects.filter_by_grouper(same_file_in_other_folder_grouper)
        self.assertEquals(versions.count(), 1)
        self.assertEquals(versions[0].state, PUBLISHED)

    def test_ajax_upload_clipboardadmin_same_name_as_existing_file(self):
        file = self.create_file('test.pdf')
        self.assertEquals(FileGrouper.objects.count(), 2)
        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEquals(FileGrouper.objects.count(), 2)

        with nonversioned_manager(File):
            files = self.folder.files.all()
        self.assertEquals(files.count(), 3)
        self.assertEquals(self.file.label, 'test.pdf')
        self.assertEquals(self.file.grouper, self.file_grouper)

        versions = Version.objects.filter_by_grouper(self.file_grouper)
        self.assertEquals(versions.count(), 2)
        self.assertEquals(versions[0].state, PUBLISHED)
        self.assertEquals(versions[0].content, self.file)
        self.assertEquals(versions[1].state, DRAFT)
        self.assertEquals(versions[1].content, files.latest('pk'))

    def test_ajax_upload_clipboardadmin_for_image_file(self):
        file = self.create_image('circles.jpg')
        self.assertEquals(FileGrouper.objects.count(), 2)
        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEquals(FileGrouper.objects.count(), 3)

        with nonversioned_manager(File):
            files = self.folder.files.all()
        new_file = files.latest('pk')
        self.assertEquals(new_file.label, 'circles.jpg')
        self.assertEquals(new_file.grouper, FileGrouper.objects.latest('pk'))
