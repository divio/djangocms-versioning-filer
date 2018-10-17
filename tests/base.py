import os

from django.conf import settings
from django.core.files import File as DjangoFile

from cms.api import create_page
from cms.models import Placeholder
from cms.test_utils.testcases import CMSTestCase

import filer
from djangocms_versioning.constants import DRAFT
from djangocms_versioning.helpers import nonversioned_manager
from djangocms_versioning.models import Version
from filer.models import File, Folder
from filer.tests.helpers import create_image
from filer.utils.loader import load_model

from djangocms_versioning_filer.helpers import create_file_version
from djangocms_versioning_filer.models import FileGrouper


class BaseFilerVersioningTestCase(CMSTestCase):

    def setUp(self):
        self.language = 'en'
        self.superuser = self.get_superuser()
        self.page = create_page(
            title='test page',
            language=self.language,
            template='page.html',
            menu_title='test page',
            in_navigation=True,
            limit_visibility_in_menu=None,
            site=None,
            created_by=self.superuser,
        )
        self.page_draft_version = Version.objects.filter_by_grouper(self.page).filter(state=DRAFT).first()
        self.placeholder = Placeholder.objects.get_for_obj(self.page_draft_version.content).get(slot='content')

        self.info = (File._meta.app_label, File._meta.model_name)
        self.folder = Folder.objects.create(name='folder')
        self.folder2 = Folder.objects.create(name='folder2')
        self.folder_inside = Folder.objects.create(
            name='folder_inside',
            parent=self.folder,
        )
        self.file_grouper = FileGrouper.objects.create()
        self.file = self.create_file_obj(
            original_filename='test.pdf',
            folder=self.folder,
            grouper=self.file_grouper,
            publish=True,
        )

        self.image_grouper = FileGrouper.objects.create()
        self.image = self.create_image_obj(
            original_filename='test-image.jpg',
            folder=self.folder,
            grouper=self.image_grouper,
            publish=True,
        )

    def create_file(self, original_filename, content='content'):
        filename = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, original_filename)
        with open(filename, 'w') as f:
            f.write(content)
        return DjangoFile(open(filename, 'rb'), name=original_filename)

    def create_image(self, original_filename):
        filename = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, original_filename)
        img = create_image()
        img.save(filename, 'JPEG')
        return DjangoFile(open(filename, 'rb'), name=original_filename)

    def create_file_obj(
        self,
        original_filename,
        file=None,
        folder=None,
        publish=True,
        content="data",
        is_public=True,
        grouper=None,
        **kwargs
    ):
        if not kwargs.get('created_by'):
            kwargs['owner'] = self.superuser

        if file is None:
            file = self.create_file(original_filename, content)

        if grouper is None:
            grouper = FileGrouper.objects.create()

        for filer_class in filer.settings.FILER_FILE_MODELS:
            FileSubClass = load_model(filer_class)
            if FileSubClass.matches_file_type(original_filename, file, request=None):
                break

        file_obj = FileSubClass.objects.create(
            is_public=is_public,
            original_filename=original_filename,
            file=file,
            folder=folder,
            grouper=grouper,
            **kwargs
        )
        version = create_file_version(file_obj, kwargs['owner'])
        if publish:
            version.publish(kwargs['owner'])
            with nonversioned_manager(File):
                file_obj.refresh_from_db()

        return file_obj

    def create_image_obj(self, original_filename, **kwargs):
        return self.create_file_obj(
            original_filename,
            file=self.create_image(original_filename),
            **kwargs,
        )
