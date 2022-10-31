from django.shortcuts import reverse

from djangocms_versioning.helpers import proxy_model
from filer.models import File

from tests.base import BaseFilerVersioningTestCase


class VersioningFilerAdminTestCase(BaseFilerVersioningTestCase):

    def _get_edit_url(self, content):
        version = proxy_model(content.versions.first(), content._meta.model)
        return reverse(
            "admin:{app}_{model}_edit_redirect".format(
                app=version._meta.app_label,
                model=version._meta.model_name,
            ),
            args=(version.pk,),
        )

    def test_admin_edit_button_enabled(self):
        """
        With a file that is edtiable, render the edit button as active
        """
        # Delete the image without a version
        File.objects.last().delete()
        request = self.get_request("/")
        request.user = self.get_superuser()
        edit_url = self._get_edit_url(self.file)
        filer_admin_url = reverse('admin:filer-directory_listing', kwargs={'folder_id': self.file.folder.id})

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(filer_admin_url)

        self.assertContains(response, "cms-versioning-action-edit")
        self.assertContains(response, "cms-versioning-action-btn")
        self.assertContains(response, edit_url)
        self.assertNotContains(response, "inactive")

    def test_admin_edit_button_disabled(self):
        """
        With a file that cannot be edited, edit button should be rendered, but as inactive.
        """
        # Delete the editable file
        File.objects.first().delete()
        request = self.get_request("/")
        request.user = self.get_staff_page_user()
        filer_admin_url = reverse('admin:filer-directory_listing', kwargs={'folder_id': self.file.folder.id})

        with self.login_user_context(self.superuser):
            response = self.client.get(filer_admin_url)

        self.assertContains(response, "cms-versioning-action-edit")
        self.assertContains(response, "cms-versioning-action-btn")
        self.assertContains(response, "js-versioning-action-btn")
        self.assertContains(response, "js-versioning-action")
        self.assertContains(response, "inactive")
