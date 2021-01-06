import os
from mock import Mock, PropertyMock, patch
from unittest import skipUnless
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.admin import helpers
from django.contrib.contenttypes.models import ContentType
from django.core.files import File as DjangoFile
from django.urls import reverse

from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import add_url_parameters

from djangocms_versioning.constants import ARCHIVED, DRAFT, PUBLISHED
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

        self.assertEqual(response.status_code, 200)
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

        self.assertEqual(response.status_code, 200)
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

    def test_canonical_view(self):
        """
        1.Canonical url creation when file_obj and grouper are created
        check canonical_url is same for the published version of file_obj.
        2.canonical url is same in draft and published version of the file object
        Canonical_url will always link to published file url.
        """
        with self.login_user_context(self.superuser):
            grouper = FileGrouper.objects.create()
            file_obj = self.create_file_obj(
                original_filename='test-test.doc',
                folder=self.file.folder,
                grouper=grouper,
                publish=False,
            )

            self.assertIn('/media/filer_public/', file_obj.url)
            self.assertIn('test-test.doc', file_obj.url)

            version = Version.objects.get_for_content(file_obj)
            self.assertEqual(version.state, DRAFT)

            version.publish(self.superuser)
            self.assertEqual(version.state, PUBLISHED)

            expected_canonical_url = '/filer/{}{}/{}/'.format(
                settings.FILER_CANONICAL_URL,
                grouper.canonical_time,
                grouper.canonical_file_id
            )
            # get canonical url for the published file from grouper
            self.assertEqual(version.content.canonical_url, expected_canonical_url)
            published_version_static_path = '/media/{}/{}'.format(grouper.file.folder, file_obj.original_filename)
            self.assertEqual(published_version_static_path, grouper.file.url)
            response = self.client.get(grouper.file.canonical_url)
        self.assertRedirects(response, grouper.file.url)

        new_draft_version = version.copy(self.superuser)

        new_draft_file_obj = new_draft_version.content
        new_draft_file_obj.refresh_from_db()
        # check the new draft version canonical is same as published version canonical
        self.assertEqual(new_draft_file_obj.canonical_url, grouper.file.canonical_url)
        self.assertIn('/media/filer_public/', new_draft_file_obj.url)
        # clean-up
        new_draft_version.delete()

    def test_ajax_upload_clipboardadmin(self):
        file = self.create_file('test2.pdf')
        same_file_in_other_folder_grouper = FileGrouper.objects.create()
        same_file_in_other_folder = self.create_file_obj(
            original_filename='test2.pdf',
            folder=Folder.objects.create(),
            grouper=same_file_in_other_folder_grouper,
            publish=True,
        )
        current_grouper_count = FileGrouper.objects.count()

        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEqual(FileGrouper.objects.count(), current_grouper_count + 1)
        with nonversioned_manager(File):
            files = self.folder.files.all()
        new_file = files.latest('pk')
        new_file_grouper = FileGrouper.objects.latest('pk')
        self.assertEqual(new_file.label, 'test2.pdf')
        self.assertEqual(new_file.grouper, new_file_grouper)
        versions = Version.objects.filter_by_grouper(new_file_grouper).order_by('pk')
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions[0].state, DRAFT)

        # Checking existing in self.folder file
        self.assertEqual(self.file.label, 'test.pdf')
        self.assertEqual(self.file.grouper, self.file_grouper)
        versions = Version.objects.filter_by_grouper(self.file_grouper).order_by('pk')
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions[0].state, PUBLISHED)

        # Checking file in diffrent folder with the same name as newly created file
        self.assertEqual(same_file_in_other_folder.label, 'test2.pdf')
        self.assertEqual(same_file_in_other_folder.grouper, same_file_in_other_folder_grouper)
        versions = Version.objects.filter_by_grouper(same_file_in_other_folder_grouper).order_by('pk')
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions[0].state, PUBLISHED)

    def test_ajax_upload_clipboardadmin_same_name_as_existing_file(self):
        file = self.create_file('test.pdf')
        current_grouper_count = FileGrouper.objects.count()
        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEqual(FileGrouper.objects.count(), current_grouper_count)

        with nonversioned_manager(File):
            files = self.folder.files.all()
        self.assertEqual(files.count(), 3)
        self.assertEqual(self.file.label, 'test.pdf')
        self.assertEqual(self.file.grouper, self.file_grouper)

        versions = Version.objects.filter_by_grouper(self.file_grouper).order_by('pk')
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions[0].state, PUBLISHED)
        self.assertEqual(versions[0].content, self.file)
        self.assertEqual(versions[1].state, DRAFT)
        self.assertEqual(versions[1].content, files.latest('pk'))

    def test_ajax_upload_clipboardadmin_same_name_as_existing_draft_file(self):
        file_grouper = FileGrouper.objects.create()
        file_obj = self.create_file_obj(
            original_filename='test1.pdf',
            folder=self.folder,
            grouper=file_grouper,
            publish=False,
        )
        file = self.create_file('test1.pdf')
        current_grouper_count = FileGrouper.objects.count()
        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEqual(FileGrouper.objects.count(), current_grouper_count)

        with nonversioned_manager(File):
            files = self.folder.files.all()
        self.assertEqual(files.count(), 4)
        self.assertEqual(file_obj.label, 'test1.pdf')
        self.assertEqual(file_obj.grouper, file_grouper)

        versions = Version.objects.filter_by_grouper(file_grouper).order_by('pk')
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions[0].state, ARCHIVED)
        self.assertEqual(versions[0].content, file_obj)
        self.assertEqual(versions[1].state, DRAFT)
        self.assertEqual(versions[1].content, files.latest('pk'))

    def test_ajax_upload_clipboardadmin_for_image_file(self):
        file = self.create_image('circles.jpg')
        current_grouper_count = FileGrouper.objects.count()
        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEqual(FileGrouper.objects.count(), current_grouper_count + 1)

        with nonversioned_manager(File):
            files = self.folder.files.all()
        new_file = files.latest('pk')
        self.assertEqual(new_file.label, 'circles.jpg')
        self.assertEqual(new_file.grouper, FileGrouper.objects.latest('pk'))

    @skipUnless(
        'djangocms_moderation' in settings.INSTALLED_APPS,
        'Test only relevant when djangocms_moderation enabled',
    )
    def test_ajax_upload_clipboardadmin_same_name_as_existing_file_in_moderation(self):
        image = self.create_image_obj(
            original_filename='test1.jpg',
            folder=self.folder,
            publish=False,
        )
        file = self.create_image('test1.jpg')
        current_grouper_count = FileGrouper.objects.count()
        with nonversioned_manager(File):
            self.assertEqual(File.objects.count(), 3)

        from djangocms_moderation.models import Workflow, ModerationCollection
        wf = Workflow.objects.create(name='Workflow 1', is_default=True)
        collection = ModerationCollection.objects.create(
            author=self.superuser, name='Collection 1', workflow=wf,
        )
        collection.add_version(Version.objects.get_for_content(image))

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-ajax_upload', kwargs={'folder_id': self.folder.id}),
                data={'file': file},
            )

        self.assertEqual(FileGrouper.objects.count(), current_grouper_count)
        with nonversioned_manager(File):
            self.assertEqual(File.objects.count(), 3)
        error_msg = 'Cannot archive existing test1.jpg file version'
        self.assertEqual(response.json()['error'], error_msg)

    def test_folderadmin_directory_listing(self):
        folder = Folder.objects.create(name='test folder 9')
        file_grouper_1 = FileGrouper.objects.create()
        published_file = self.create_file_obj(
            original_filename='published.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=True,
        )

        draft_file = self.create_file_obj(
            original_filename='draft.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=False,
        )

        file_grouper_2 = FileGrouper.objects.create()
        draft_file_2 = self.create_file_obj(
            original_filename='draft2.txt',
            folder=folder,
            grouper=file_grouper_2,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': folder.pk})
            )

        self.assertContains(response, draft_file.label)
        self.assertContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)

    def test_folderadmin_directory_listing_unfiled_images(self):
        file_grouper_1 = FileGrouper.objects.create()
        published_file = self.create_file_obj(
            original_filename='published.txt',
            folder=None,
            grouper=file_grouper_1,
            publish=True,
        )

        draft_file = self.create_file_obj(
            original_filename='draft.txt',
            folder=None,
            grouper=file_grouper_1,
            publish=False,
        )

        file_grouper_2 = FileGrouper.objects.create()
        draft_file_2 = self.create_file_obj(
            original_filename='draft2.txt',
            folder=None,
            grouper=file_grouper_2,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                reverse('admin:filer-directory_listing-unfiled_images')
            )

        self.assertContains(response, draft_file.label)
        self.assertContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)

    def test_folderadmin_directory_listing_files_with_missing_data(self):
        file_grouper_1 = FileGrouper.objects.create()
        published_file = self.create_file_obj(
            original_filename='published.txt',
            folder=None,
            grouper=file_grouper_1,
            publish=True,
            has_all_mandatory_data=False,
        )

        draft_file = self.create_file_obj(
            original_filename='draft.txt',
            folder=None,
            grouper=file_grouper_1,
            publish=False,
            has_all_mandatory_data=False,
        )

        file_grouper_2 = FileGrouper.objects.create()
        draft_file_2 = self.create_file_obj(
            original_filename='draft2.txt',
            folder=None,
            grouper=file_grouper_2,
            publish=False,
            has_all_mandatory_data=False,
        )

        file_grouper_3 = FileGrouper.objects.create()
        file_with_all_mandatory_data = self.create_file_obj(
            original_filename='mandatory_data.docx',
            folder=None,
            grouper=file_grouper_3,
            has_all_mandatory_data=True,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                reverse('admin:filer-directory_listing-images_with_missing_data')
            )

        self.assertContains(response, draft_file.label)
        self.assertContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)
        self.assertNotContains(response, file_with_all_mandatory_data.label)

    def test_folderadmin_directory_listing_file_search(self):
        folder = Folder.objects.create(name='test folder 9')
        file_grouper_1 = FileGrouper.objects.create()
        published_file = self.create_file_obj(
            original_filename='draft1.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=True,
        )

        draft_file = self.create_file_obj(
            original_filename='draft2.txt',
            folder=folder,
            grouper=file_grouper_1,
            publish=False,
        )

        draft_file_2 = self.create_file_obj(
            original_filename='draft3.txt',
            folder=folder,
            publish=False,
        )

        draft_file_3 = self.create_file_obj(
            original_filename='shape.txt',
            folder=folder,
            publish=False,
        )

        draft_file_3 = self.create_file_obj(
            original_filename='shape.txt',
            folder=folder,
            publish=False,
        )

        with self.login_user_context(self.superuser):
            response = self.client.get(
                add_url_parameters(
                    reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.pk}),
                    q='draft',
                )
            )
        self.assertContains(response, draft_file.label)
        self.assertContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)
        self.assertNotContains(response, draft_file_3.label)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                add_url_parameters(
                    reverse('admin:filer-directory_listing', kwargs={'folder_id': folder.pk}),
                    q='draft',
                )
            )
        self.assertContains(response, draft_file.label)
        self.assertContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)
        self.assertNotContains(response, draft_file_3.label)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                add_url_parameters(
                    reverse('admin:filer-directory_listing', kwargs={'folder_id': self.folder.pk}),
                    q='draft',
                    limit_search_to_folder='on',
                )
            )
        self.assertNotContains(response, draft_file.label)
        self.assertNotContains(response, draft_file_2.label)
        self.assertNotContains(response, published_file.label)
        self.assertNotContains(response, draft_file_3.label)

    def test_folder_name_change_rebuild_urls_for_published_files(self):
        folder0 = Folder.objects.create(name='f0')
        folder1 = Folder.objects.create(name='f1')
        folder2 = Folder.objects.create(name='f2', parent=folder1)
        folder3 = Folder.objects.create(name='f3', parent=folder1)
        folder4 = Folder.objects.create(name='f4', parent=folder3)

        file0 = self.create_file_obj(original_filename='test.xls', folder=folder0)

        file1 = self.create_file_obj(original_filename='test.xls', folder=folder1)
        file2 = self.create_file_obj(original_filename='test.xls', folder=folder2)
        file3 = self.create_file_obj(original_filename='test.xls', folder=folder3)
        file4 = self.create_file_obj(original_filename='test.xls', folder=folder4)
        draft_file = self.create_file_obj(original_filename='test2.xls', folder=folder4, publish=False)
        unpublished_file = self.create_file_obj(original_filename='test3.xls', folder=folder4, publish=True)
        unpublished_file.versions.latest('pk').unpublish(self.superuser)
        archived_file = self.create_file_obj(original_filename='test4.xls', folder=folder4, publish=False)
        archived_file.versions.latest('pk').archive(self.superuser)

        files = [file0, file1, file2, file3, file4, draft_file, unpublished_file, archived_file]

        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer_folder_change', args=[folder0.id]),
                data={'name': 'f00'},
            )
        for f in files:
            with nonversioned_manager(File):
                f.refresh_from_db()

        self.assertEqual(file0.url, '/media/f00/test.xls')
        self.assertFalse(file0.file.storage.exists('f0/test.xls'))
        self.assertTrue(file0.file.storage.exists('f00/test.xls'))

        self.assertEqual(file1.url, '/media/f1/test.xls')
        self.assertEqual(file2.url, '/media/f1/f2/test.xls')
        self.assertEqual(file3.url, '/media/f1/f3/test.xls')
        self.assertEqual(file4.url, '/media/f1/f3/f4/test.xls')
        self.assertIn('filer_public', draft_file.url)
        self.assertIn('test2.xls', draft_file.url)
        self.assertIn('filer_public', unpublished_file.url)
        self.assertIn('test3.xls', unpublished_file.url)
        self.assertIn('filer_public', archived_file.url)
        self.assertIn('test4.xls', archived_file.url)

        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer_folder_change', args=[folder1.id]),
                data={'name': 'fol10'},
            )
        for f in files:
            with nonversioned_manager(File):
                f.refresh_from_db()

        self.assertEqual(file0.url, '/media/f00/test.xls')
        self.assertEqual(file1.url, '/media/fol10/test.xls')
        self.assertEqual(file2.url, '/media/fol10/f2/test.xls')
        self.assertEqual(file3.url, '/media/fol10/f3/test.xls')
        self.assertEqual(file4.url, '/media/fol10/f3/f4/test.xls')
        self.assertIn('filer_public', draft_file.url)
        self.assertIn('test2.xls', draft_file.url)
        self.assertNotIn('fol10', draft_file.url)
        self.assertIn('filer_public', unpublished_file.url)
        self.assertIn('test3.xls', unpublished_file.url)
        self.assertNotIn('fol10', unpublished_file.url)
        self.assertIn('filer_public', archived_file.url)
        self.assertIn('test4.xls', archived_file.url)
        self.assertNotIn('fol10', archived_file.url)

        with self.login_user_context(self.superuser):
            self.client.post(
                reverse('admin:filer_folder_change', args=[folder3.id]),
                data={'name': 'f30 test'},
            )
        for f in files:
            with nonversioned_manager(File):
                f.refresh_from_db()

        self.assertEqual(file0.url, '/media/f00/test.xls')
        self.assertEqual(file1.url, '/media/fol10/test.xls')
        self.assertEqual(file2.url, '/media/fol10/f2/test.xls')
        self.assertEqual(file3.url, '/media/fol10/f30%20test/test.xls')
        self.assertEqual(file4.url, '/media/fol10/f30%20test/f4/test.xls')
        self.assertIn('filer_public', draft_file.url)
        self.assertIn('test2.xls', draft_file.url)
        self.assertNotIn('fol10', draft_file.url)
        self.assertIn('filer_public', unpublished_file.url)
        self.assertIn('test3.xls', unpublished_file.url)
        self.assertNotIn('fol10', unpublished_file.url)
        self.assertIn('filer_public', archived_file.url)
        self.assertIn('test4.xls', archived_file.url)
        self.assertNotIn('fol10', archived_file.url)

    @skipUnless(
        'djangocms_moderation' in settings.INSTALLED_APPS,
        'Test only relevant when djangocms_moderation enabled',
    )
    def test_folderadmin_add_to_moderation(self):
        root_folder = Folder.objects.create(name='f0')
        folder1 = Folder.objects.create(name='f1', parent=root_folder)
        folder2 = Folder.objects.create(name='f2', parent=folder1)
        folder3 = Folder.objects.create(name='f3', parent=folder2)

        file0 = self.create_image_obj(original_filename='file0.jpg', folder=root_folder, publish=False)
        file1 = self.create_file_obj(original_filename='test.xls', folder=folder1, publish=False)
        file2 = self.create_file_obj(original_filename='test.xls', folder=folder2, publish=False)
        file3 = self.create_file_obj(original_filename='test.xls', folder=folder3, publish=False)

        draft_grouper = FileGrouper.objects.create()
        # published_file
        self.create_file_obj(
            original_filename='test4.txt', folder=folder3, publish=True, grouper=draft_grouper
        )
        draft_file4 = self.create_file_obj(
            original_filename='test4.txt', folder=folder3, publish=False, grouper=draft_grouper
        )

        # published_file
        self.create_file_obj(
            original_filename='published.xls', folder=folder3, publish=True
        )

        unpublished_file = self.create_file_obj(
            original_filename='unpublished.xls', folder=folder3, publish=True
        )
        unpublished_file.versions.latest('pk').unpublish(self.superuser)

        archived_file = self.create_file_obj(original_filename='archived.xls', folder=folder3, publish=False)
        archived_file.versions.latest('pk').archive(self.superuser)

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer-directory_listing', kwargs={'folder_id': root_folder.id}),
                data={
                    'action': 'add_items_to_collection',
                    helpers.ACTION_CHECKBOX_NAME: [
                        'folder-{}'.format(folder1.id),
                        'file-{}'.format(file0.id),
                    ],
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            '/en/admin/djangocms_moderation/moderationcollection/item/add-items/',
            response.url,
        )

        version_ids = parse_qs(urlparse(response.url).query)['version_ids'][0].split(',')
        version_ids = [int(i) for i in version_ids]
        proper_ids = Version.objects.filter(
            content_type_id=ContentType.objects.get_for_model(File),
            object_id__in=[file0.pk, file1.pk, file2.pk, file3.pk, draft_file4.pk],
        ).values_list('id', flat=True)
        self.assertEqual(set(proper_ids), set(version_ids))

    def test_image_file_name_change(self):
        """
        Update the name attribute for image and check the updated name in folder listing
        """
        folder = Folder.objects.create(name='f0')
        draft_grouper = FileGrouper.objects.create()
        new_file_name = 'image1'
        image_file = self.create_image_obj(
            original_filename='image.jpg',
            publish=False,
            grouper=draft_grouper,
            folder=folder
        )

        with self.login_user_context(self.superuser):
            response = self.client.post(
                reverse('admin:filer_image_change', args=[image_file.id]),
                data={'name': new_file_name},
            )
        folder_dir_list_url = reverse('admin:filer-directory_listing', kwargs={'folder_id': folder.pk})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(folder_dir_list_url, response.url)

        with self.login_user_context(self.superuser):
            response = self.client.get(response.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_file_name)


# NOTE: Returning 200 when permissions don't match is a bit strange,
# one would expect a 403 or 400, but this is what the frontend
# seems to expect currently
class TestAjaxUploadViewPermissions(CMSTestCase):

    def create_file(self, original_filename, content='content'):
        filename = os.path.join(
            settings.FILE_UPLOAD_TEMP_DIR, original_filename)
        with open(filename, 'w') as f:
            f.write(content)
        return DjangoFile(open(filename, 'rb'), name=original_filename)

    @patch.object(Folder, 'has_add_children_permission', Mock(return_value=True))
    def test_ajax_upload_clipboardadmin_user_with_perms_for_adding_children_can_access(self):
        """If folder.has_add_children_permissions returns True then
        we should allow file upload
        """
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'has_add_children_permission', Mock(return_value=False))
    def test_ajax_upload_clipboardadmin_user_without_perms_for_adding_children_cannot_access(self):
        """If folder.has_add_children_permissions returns False then
        we should not allow file upload
        """
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'has_add_children_permission', Mock(return_value=True))
    def test_ajax_upload_clipboardadmin_user_with_perms_for_adding_children_can_access_with_existing_path_and_folder_id(self):  # noqa
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    # NOTE: Mocked to return True for check on parent and False on subfolder
    @patch.object(Folder, 'has_add_children_permission', side_effect=[True, False])
    def test_ajax_upload_clipboardadmin_user_without_perms_for_adding_children_cannot_access_with_existing_path_and_folder_id(  # noqa
        self, mocked_perms
    ):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'has_add_children_permission', Mock(return_value=True))
    def test_ajax_upload_clipboardadmin_user_with_perms_for_adding_children_can_access_with_existing_nested_path_without_folder_id(self):  # noqa
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(name='subfolder', parent=folder)
        Folder.objects.create(name='subsubfolder', parent=subfolder)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    # NOTE: Mocked to return True for check on parents and False on subsubfolder
    @patch.object(Folder, 'has_add_children_permission', side_effect=[True, True, False])
    def test_ajax_upload_clipboardadmin_user_without_perms_for_adding_children_cannot_access_with_existing_nested_path_without_folder_id(  # noqa
        self, mocked_perms
    ):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(name='subfolder', parent=folder)
        Folder.objects.create(name='subsubfolder', parent=subfolder)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'has_add_children_permission', Mock(return_value=True))
    def test_ajax_upload_clipboardadmin_user_with_perms_for_adding_children_can_access_with_existing_nested_path_with_folder_id(self):  # noqa
        user = self.get_superuser()
        root_folder = Folder.objects.create(name='root')
        folder = Folder.objects.create(name='folder', parent=root_folder)
        subfolder = Folder.objects.create(name='subfolder', parent=folder)
        Folder.objects.create(name='subsubfolder', parent=subfolder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': root_folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    # NOTE: Mocked to return True for check on parents and False on subsubfolder
    @patch.object(Folder, 'has_add_children_permission', side_effect=[True, True, True, False])
    def test_ajax_upload_clipboardadmin_user_without_perms_for_adding_children_cannot_access_with_existing_nested_path_with_folder_id(  # noqa
        self, mocked_perms
    ):
        user = self.get_superuser()
        root_folder = Folder.objects.create(name='root')
        folder = Folder.objects.create(name='folder', parent=root_folder)
        subfolder = Folder.objects.create(name='subfolder', parent=folder)
        Folder.objects.create(name='subsubfolder', parent=subfolder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': root_folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_anonymous_user_cant_access_with_folder_id(self):
        """If trying to access the url as an anonymous user with an
        upload folder specified, we should not allow file upload
        """
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_anonymous_user_cant_get_info_if_folder_exists(self):
        """If trying to access the url as an anonymous user with an
        id of an upload folder that doesn't exist, we should
        give the user the same message as when a folder exists.
        Otherwise a potential attacker could use this to find out which
        folders exist or not.
        """
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': 333})
        file_obj = self.create_file('test-file')

        response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_anonymous_user_cant_access_no_folder_id(self):
        """If trying to access the url as an anonymous user with no
        upload folder specified, we should not allow file upload.
        """
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_superuser_can_access_with_folder_id(self):
        """If trying to access the url as a superuser with an
        upload folder specified but no path, we should allow file upload
        """
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')
        user = self.get_superuser()

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_superuser_can_access_with_folder_id_and_path(self):
        """If trying to access the url as a superuser with an
        upload folder and path specified, we should allow file upload
        """
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')
        user = self.get_superuser()

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_superuser_can_access_no_folder_id(self):
        """If trying to access the url as a superuser with no
        upload folder or path specified, we should allow file upload.
        """
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')
        user = self.get_superuser()

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    def test_ajax_upload_clipboardadmin_superuser_can_access_no_folder_id_with_path(self):
        """If trying to access the url as a superuser with no
        upload folder but a path specified, we should allow file upload.
        """
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')
        user = self.get_superuser()

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_root_folder_that_can_have_subfolders_new_path_specified(self):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_root_folder_that_can_have_subfolders_path_unspecified(self):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', False)
    def test_ajax_upload_clipboardadmin_folder_that_cant_have_subfolders_new_path_specified(self):
        """If trying to access the url with a folder and path param
        specified, then we should not allow access for a folder that
        can't have subfolders
        """
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', False)
    def test_ajax_upload_clipboardadmin_folder_that_cant_have_subfolders_path_unspecified(self):
        """If trying to access the url with a folder specified but no
        path, then we should allow access for a folder that
        can't have subfolders because we definitely won't be creating
        any folders (it's the path param that can trigger folder
        creation).
        """
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_existing_folder_in_path_that_can_have_subfolders_with_folder_id(self):  # noqa
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', new_callable=PropertyMock)
    def test_ajax_upload_clipboardadmin_existing_folder_in_path_that_cant_have_subfolders_with_folder_id(  # noqa
        self, mocked_perms
    ):
        # Returns True for folder and False for subfolder
        mocked_perms.side_effect = [True, False]
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_existing_folder_in_path_that_can_have_subfolders_no_folder_id(self):
        user = self.get_superuser()
        Folder.objects.create(name='folder')
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', False)
    def test_ajax_upload_clipboardadmin_existing_folder_in_path_that_cant_have_subfolders_no_folder_id(self):
        user = self.get_superuser()
        Folder.objects.create(name='folder')
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_existing_nested_path_that_can_have_subfolders_with_folder_id(self):
        user = self.get_superuser()
        root_folder = Folder.objects.create(name='root')
        folder = Folder.objects.create(name='folder', parent=root_folder)
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': root_folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', new_callable=PropertyMock)
    def test_ajax_upload_clipboardadmin_existing_nested_path_that_cant_have_subfolders_with_folder_id(
        self, mocked_perms
    ):
        # Return True for parent folder and False for subfolder
        mocked_perms.side_effect = [True, False]
        user = self.get_superuser()
        root_folder = Folder.objects.create(name='root')
        folder = Folder.objects.create(name='folder', parent=root_folder)
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': root_folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', True)
    def test_ajax_upload_clipboardadmin_existing_nested_path_that_can_have_subfolders_no_folder_id(self):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch.object(Folder, 'can_have_subfolders', False)
    def test_ajax_upload_clipboardadmin_existing_nested_path_that_cant_have_subfolders_no_folder_id(self):
        user = self.get_superuser()
        folder = Folder.objects.create(name='folder')
        Folder.objects.create(name='subfolder', parent=folder)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder/subsubfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_no_path(self):
        """If trying to upload to the "Unsorted Uploads" folder (i.e
        not specifying folder_id) with filer set to allow creating of
        folders in root and the POST params do not specify a path,
        allow access
        """
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_false_no_path(self):
        """If trying to upload to the "Unsorted Uploads" folder (i.e
        not specifying folder_id) with filer set to disallow creating of
        folders in root and the POST params do not specify a path,
        allow access (because it's the path param that may trigger
        folder creation so everything is safe)
        """
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_with_new_path(self):
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_disallow_if_folder_is_root_and_setting_false_with_new_path(self):
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_with_existing_path(self):
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_disallow_if_folder_is_root_and_setting_false_with_existing_path(self):
        user = self._create_user('albert', is_staff=True)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't use this folder, Permission Denied. Please select another folder."
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_no_path_superuser(self):
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_false_no_path_superuser(self):
        """If trying to upload to the "Unsorted Uploads" folder (i.e
        not specifying folder_id) with filer set to disallow creating of
        folders in root and the POST params do not specify a path,
        allow access (because it's the path param that may trigger
        folder creation so everything is safe)
        """
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(url, {'file': file_obj})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_with_new_path_superuser(self):
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_disallow_if_folder_is_root_and_setting_false_with_new_path_superuser(self):
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', True)
    def test_ajax_upload_clipboardadmin_allow_if_folder_is_root_and_setting_true_with_existing_path_superuser(self):
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)

    @patch('filer.settings.FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS', False)
    def test_ajax_upload_clipboardadmin_disallow_if_folder_is_root_and_setting_false_with_existing_path_superuser(self):  # noqa
        user = self.get_superuser()
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(user):
            response = self.client.post(
                url, {'file': file_obj, 'path': 'folder/subfolder'})

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'file_id': 1,
            'thumbnail': '/static/filer/icons/file_32x32.png',
            'grouper_id': 1,
            'alt_text': '',
            'label': 'test-file'
        }
        self.assertDictEqual(response.json(), expected_json)


class TestAjaxUploadViewFolderOperations(CMSTestCase):

    def setUp(self):
        self.superuser = self.get_superuser()

    def create_file(self, original_filename, content='content'):
        filename = os.path.join(
            settings.FILE_UPLOAD_TEMP_DIR, original_filename)
        with open(filename, 'w') as f:
            f.write(content)
        return DjangoFile(open(filename, 'rb'), name=original_filename)

    def test_ajax_upload_clipboardadmin_no_folder(self):
        """If no folder is specified in the POST url or data, no folder
        should be created or set on the file object.
        """
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'file': file_obj})

        # No folders were created
        self.assertEqual(Folder.objects.all().count(), 0)

        # We should have one file which has its folder field set to None
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertIsNone(files.get().folder)

    def test_ajax_upload_clipboardadmin_folder_id_does_not_exist(self):
        """If folder with folder_id does not exist, don't create any
        folders or files and return error msg in json response.
        """
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': 88})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            response = self.client.post(url, {'file': file_obj})

        # We should get a 200 json response with an error
        self.assertEqual(response.status_code, 200)
        expected_json = {
            'error': "Can't find folder to upload. Please refresh and try again"
        }
        self.assertDictEqual(response.json(), expected_json)

        # We should no folders and no files after this POST call
        self.assertEqual(Folder.objects.all().count(), 0)
        self.assertEqual(File._base_manager.all().count(), 0)

    def test_ajax_upload_clipboardadmin_with_folder_id(self):
        """If a folder id is specified in the POST url then the
        file should be added to that folder.
        """
        # Set up some nested folders
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(
            name='subfolder', parent=folder)
        subsubfolder = Folder.objects.create(
            name='subsubfolder', parent=subfolder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': subsubfolder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'file': file_obj})

        # We should still have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        # The tree structure of these folders should not change
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        subsubfolder.refresh_from_db()
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which is in subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)

    def test_ajax_upload_clipboardadmin_no_folder_id_new_folder(self):
        """If no folder id is specified, but a path param is sent
        in the POST data then the folder in the path param should be
        created and the file added to it.
        """
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'folder', 'file': file_obj})

        # We should have 1 folder after this POST call
        self.assertEqual(Folder.objects.all().count(), 1)
        folder = Folder.objects.get(name='folder')
        # No parent should be created
        self.assertIsNone(folder.parent)

        # We should have one file which is in folder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, folder)

    def test_ajax_upload_clipboardadmin_with_folder_id_new_folder(self):
        """If both a folder id and a path are specified, the new
        folder containing the file should be created in the folder
        specified by folder_id.
        """
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'subfolder', 'file': file_obj})

        # We should have 2 folders after this POST call:
        # folder, subfolder
        self.assertEqual(Folder.objects.all().count(), 2)
        folder.refresh_from_db()
        subfolder = Folder.objects.get(name='subfolder')
        # The folder structure should be folder/subfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)

        # We should have one file which is in subfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subfolder)

    def test_ajax_upload_clipboardadmin_with_folder_id_new_folder_nested(self):
        """If both a folder id and a nested path param are
        specified, the newly created folders should be created in the
        folder specified by folder_id."""
        folder = Folder.objects.create(name='folder')
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'subfolder/subsubfolder', 'file': file_obj})

        # We should have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        folder.refresh_from_db()
        subfolder = Folder.objects.get(name='subfolder')
        subsubfolder = Folder.objects.get(name='subsubfolder')
        # The folder structure should be folder/subfolder/subsubfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which has its parent set to subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)

    def test_ajax_upload_clipboardadmin_no_folder_id_existing_folder(self):
        """If no folder id is specified, but a path param of an existing
        folder is sent in the POST data then the existing folder from
        the path should be used (but not created anew).
        """
        folder = Folder.objects.create(name='folder')
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'folder', 'file': file_obj})

        # We should still have 1 folder after this POST call
        self.assertEqual(Folder.objects.all().count(), 1)
        folder.refresh_from_db()
        # No parent should have been created
        self.assertIsNone(folder.parent)

        # We should have one file which has its folder set to folder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, folder)

    def test_ajax_upload_clipboardadmin_with_folder_id_existing_folder(self):
        """If both a folder id and a path to an existing folder are
        specified, the code should look for the existing folder in the
        folder specified by folder id.
        """
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'subfolder', 'file': file_obj})

        # We should still have 2 folders after this POST call:
        # folder, subfolder
        self.assertEqual(Folder.objects.all().count(), 2)
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        # The folder structure should still be folder/subfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)

        # We should have one file which has its parent set to subfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subfolder)

    def test_ajax_upload_clipboardadmin_without_folder_id_existing_folder_nested(self):
        """If there's no folder id specified, but there's a nested path
        to an existing folder in the POST params,
        the file should be added to the existing folder."""
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(
            name='subfolder', parent=folder)
        subsubfolder = Folder.objects.create(
            name='subsubfolder', parent=subfolder)
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(
                    url, {'path': 'folder/subfolder/subsubfolder', 'file': file_obj}
                )

        # We should still have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        subsubfolder.refresh_from_db()
        # The folder structure should be as folder/subfolder/subsubfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which has its parent set to subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)

    def test_ajax_upload_clipboardadmin_with_folder_id_existing_folder_nested(self):
        """If both a folder id and a nested path to an existing folder
        are specified, the file should be added to the existing folder.
        """
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(
            name='subfolder', parent=folder)
        subsubfolder = Folder.objects.create(
            name='subsubfolder', parent=subfolder)

        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'subfolder/subsubfolder', 'file': file_obj})

        # We should still have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        subsubfolder.refresh_from_db()
        # The folder structure should be folder/subfolder/subsubfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which has its parent set to subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)

    def test_ajax_upload_clipboardadmin_nested_with_existing_and_new_with_folder_id(self):
        """A folder id is specified and one of the nested folders in
        path already exists.
        """
        folder = Folder.objects.create(name='folder')
        subfolder = Folder.objects.create(
            name='subfolder', parent=folder)
        url = reverse(
            'admin:filer-ajax_upload', kwargs={'folder_id': folder.id})
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'subfolder/subsubfolder', 'file': file_obj})

        # We should have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        subsubfolder = Folder.objects.get(name='subsubfolder')
        # The folder structure should be folder/subfolder/subsubfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which has its parent set to subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)

    def test_ajax_upload_clipboardadmin_nested_with_existing_and_new_no_folder_id(self):
        """No folder id is specified and one of the three folders in
        the nested path already exist.
        """
        folder = Folder.objects.create(name='folder')
        url = reverse('admin:filer-ajax_upload')
        file_obj = self.create_file('test-file')

        with self.login_user_context(self.superuser):
            self.client.post(url, {'path': 'folder/subfolder/subsubfolder', 'file': file_obj})

        # We should have 3 folders after this POST call:
        # folder, subfolder and subsubfolder
        self.assertEqual(Folder.objects.all().count(), 3)
        folder.refresh_from_db()
        subfolder = Folder.objects.get(name='subfolder')
        subsubfolder = Folder.objects.get(name='subsubfolder')
        # The folder structure should be folder/subfolder/subsubfolder
        self.assertIsNone(folder.parent)
        self.assertEqual(subfolder.parent, folder)
        self.assertEqual(subsubfolder.parent, subfolder)

        # We should have one file which has its parent set to subsubfolder
        files = File._base_manager.all()
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.get().folder, subsubfolder)
