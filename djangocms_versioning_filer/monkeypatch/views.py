from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from djangocms_versioning.helpers import override_default_manager
from filer import views as filer_views
from filer.models import File


def canonical(request, uploaded_at, file_id):
    with override_default_manager(File, File._original_manager):
        filer_file = get_object_or_404(File, pk=file_id, is_public=True)

    if (not filer_file.file or int(uploaded_at) != filer_file.canonical_time):
        raise Http404('No %s matches the given query.' % File._meta.object_name)
    return redirect(filer_file.url)
filer_views.canonical = canonical  # noqa: E305
