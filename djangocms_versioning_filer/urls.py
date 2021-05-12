from django.urls import path

from . import views


# Url on the way out (get_absolute_url) needs to know to use the local site, going against the storage backend!

urlpatterns = [
    path('filer_public/<path:file_path>', views.public, name='public')
]