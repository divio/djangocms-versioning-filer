from django.shortcuts import redirect

from filer import settings as filer_settings

"""
TODO:

file can output / render: /filer_public/myfile

A url can recieve /filer_public/myfile

A view can send this onto /filer_public/myfile the registered storage backend
"""


def public(request, file_path):
    """
    Redirect to the registered storage
    """
    return redirect("{}{}".format(
        filer_settings.FILER_PUBLICMEDIA_STORAGE.base_url,
        file_path
    ))
