from django.conf import settings


PUBLIC_RELATIVE_PATH = getattr(settings, 'FILER_VERSIONING_PUBLIC_RELATIVE_PATH', "/filer_public/")
