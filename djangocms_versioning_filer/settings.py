from django.conf import settings


FILER_FILE_CONSTRAINTS = getattr(
    settings, 'FILER_FILE_CONSTRAINTS',
    []
)
