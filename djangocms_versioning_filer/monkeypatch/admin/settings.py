from django.conf import settings

import filer


FILER_FILE_CONSTRAINTS = getattr(
    settings, 'FILER_FILE_CONSTRAINTS',
    ['djangocms_versioning_filer.helpers.filename_exists', ]
)


filer.settings.FILER_FILE_CONSTRAINTS = FILER_FILE_CONSTRAINTS
