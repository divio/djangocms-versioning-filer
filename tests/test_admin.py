from django.shortcuts import reverse

from filer.admin import FileAdmin
from filer.models import File

from tests.base import BaseFilerVersioningTestCase


class VersioningFilerAdminTestCase(BaseFilerVersioningTestCase):
    def test_admin_edit_button_enabled(self):
        request = self.get_request("/")
        request.user = self.get_superuser()

        filer_admin_url = reverse('admin:filer-directory_listing', kwargs={'folder_id': self.file.folder.id})

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(filer_admin_url)

        self.assertContains(response, "cms-versioning-action-edit")
        self.assertContains(response, "cms-versioning-action-btn")
        self.assertContains(response, "inactive")
