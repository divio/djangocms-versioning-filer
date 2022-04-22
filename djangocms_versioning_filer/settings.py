from django.conf import settings


FILER_FILE_CONSTRAINTS = getattr(
    settings, 'FILER_FILE_CONSTRAINTS',
    ["djangocms_versioning_filer.helpers.filename_exists"]
)
