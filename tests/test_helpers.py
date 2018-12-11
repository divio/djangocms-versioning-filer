from django.contrib.contenttypes.models import ContentType

from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.models import Version
from filer.models import File, Folder

from .base import BaseFilerVersioningTestCase
from djangocms_versioning_filer import helpers


class HelperTests(BaseFilerVersioningTestCase):

    def test_check_folder_exists_in_folder(self):
        self.assertFalse(helpers.check_folder_exists_in_folder(self.folder, 'olivertwist'))
        subfolder = Folder(
            parent=self.folder,
            name='olivertwist'
        )
        subfolder.save()
        self.assertEquals(helpers.check_folder_exists_in_folder(self.folder, 'olivertwist'), subfolder)

    def test_add_subfolder(self):
        self.assertFalse(helpers.check_folder_exists_in_folder(self.folder, 'olivertwist'))
        subfolder = helpers.add_subfolder(self.folder, 'olivertwist')
        self.assertEquals(helpers.check_folder_exists_in_folder(self.folder, 'olivertwist'), subfolder)

        # add a folder to the sub-folder, then check that it's in the sub-folder, not the root folder
        subfolder2 = helpers.add_subfolder(subfolder, 'pippilongstockings')
        self.assertEquals(helpers.check_folder_exists_in_folder(subfolder, 'pippilongstockings'), subfolder2)
        self.assertFalse(helpers.check_folder_exists_in_folder(self.folder, 'pippilongstockings'))
        # try add a folder that caauses integrity violation
        subfolder3 = helpers.add_subfolder(self.folder, 'olivertwist')
        self.assertFalse(subfolder3)
