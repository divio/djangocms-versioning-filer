from djangocms_versioning.models import Version
from filer.models import File


def create_file_version(file, user):
    # Make sure Version.content_type uses File
    file.__class__ = File
    Version.objects.create(content=file, created_by=user)
    file.__class__ = file.get_real_instance_class()
