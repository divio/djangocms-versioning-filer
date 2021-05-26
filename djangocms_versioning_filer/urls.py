from django.urls import path

from . import views
from .constants import PUBLIC_RELATIVE_PATH


urlpatterns = [
    path(f"{PUBLIC_RELATIVE_PATH}<path:file_path>".lstrip('/'), views.public, name="public_relative_path")
]