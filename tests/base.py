import django
import django.core.files

from cms.test_utils.testcases import CMSTestCase

from djangocms_versioning.models import Version
from filer.models import File, Folder


class BaseFilerVersioningTestCase(CMSTestCase):
    def setUp(self):
        self.language = 'en'
        self.superuser = self.get_superuser()
        self.info = (File._meta.app_label, File._meta.model_name)
        self.folder = Folder.objects.create(name='folder')
        self.folder_inside = Folder.objects.create(
            name='folder',
            parent=self.folder,
        )
        self.file = self.create_file_obj(
            original_filename='test.pdf',
            folder=self.folder,
            publish=True,
        )

    @staticmethod
    def create_file(original_filename, content=''):
        file = django.core.files.base.ContentFile(content)
        file.name = original_filename
        return file

    def create_file_obj(self, original_filename, file=None, folder=None, publish=True, content='data', **kwargs):
        if file is None:
            file = self.create_file(original_filename, content)

        if not kwargs.get('created_by'):
            kwargs['owner'] = self.superuser

        file_obj = File.objects.create(
            is_public=False,
            original_filename=original_filename,
            file=file,
            folder=folder,
            **kwargs
        )

        version = Version.objects.create(content=file_obj, created_by=kwargs['owner'])
        if publish:
            version.publish(kwargs['owner'])

        return file_obj
