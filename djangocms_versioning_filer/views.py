from django.shortcuts import redirect

from filer import settings as filer_settings


def public(request, file_path):
    """
    Redirect to the registered storage
    """
    return redirect("{}{}".format(
        filer_settings.FILER_PUBLICMEDIA_STORAGE.base_url,
        file_path
    ))
