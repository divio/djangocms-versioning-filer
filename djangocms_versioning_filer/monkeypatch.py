from filer.models import File


def get_file_absolute_url(self):
    return self.get_admin_change_url()
File.get_absolute_url = get_file_absolute_url  # noqa: E305
