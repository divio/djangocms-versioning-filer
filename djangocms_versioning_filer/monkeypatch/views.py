from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from filer import views as filer_views
from filer.models import File

from djangocms_versioning_filer.models import FileGrouper


def canonical(request, uploaded_at, file_id):
    file_grouper = get_object_or_404(
        FileGrouper,
        canonical_file_id=file_id
    )

    if (not file_grouper.file or int(uploaded_at) != file_grouper.canonical_time):
        raise Http404('No %s matches the given query.' % File._meta.object_name)
    return redirect(file_grouper.file.url)
filer_views.canonical = canonical  # noqa: E305
