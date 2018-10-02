from django.db.models import Value
from django.db.models.functions import Coalesce
from django.forms.models import modelform_factory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import filer
from djangocms_versioning.models import Version
from filer import settings as filer_settings
from filer.models import Folder, Image
from filer.utils.files import (
    UploadException,
    handle_request_files_upload,
    handle_upload,
)
from filer.utils.loader import load_model

from ...models import FileGrouper, NullIfEmptyStr, get_files_distinct_grouper_queryset


@csrf_exempt
def ajax_upload(request, folder_id=None):
    folder = None
    if folder_id:
        try:
            # Get folder
            folder = Folder.objects.get(pk=folder_id)
        except Folder.DoesNotExist:
            return JsonResponse({'error': filer.admin.clipboardadmin.NO_FOLDER_ERROR})

    # check permissions
    if folder and not folder.has_add_children_permission(request):
        return JsonResponse({'error': filer.admin.clipboardadmin.NO_PERMISSIONS_FOR_FOLDER})
    try:
        if len(request.FILES) == 1:
            # dont check if request is ajax or not, just grab the file
            upload, filename, is_raw = handle_request_files_upload(request)
        else:
            # else process the request as usual
            upload, filename, is_raw = handle_upload(request)

        # find the file type
        for filer_class in filer_settings.FILER_FILE_MODELS:
            FileSubClass = load_model(filer_class)
            # TODO: What if there are more than one that qualify?
            if FileSubClass.matches_file_type(filename, upload, request):
                FileForm = modelform_factory(
                    model=FileSubClass,
                    fields=('original_filename', 'owner', 'file')
                )
                break
        uploadform = FileForm({'original_filename': filename,
                               'owner': request.user.pk},
                              {'file': upload})
        if uploadform.is_valid():
            file_obj = uploadform.save(commit=False)
            # Enforce the FILER_IS_PUBLIC_DEFAULT
            file_obj.is_public = filer_settings.FILER_IS_PUBLIC_DEFAULT
            file_obj.folder = folder

            same_name_file_qs = get_files_distinct_grouper_queryset().annotate(
                _name=NullIfEmptyStr('name'),
                _original_filename=NullIfEmptyStr('original_filename'),
                _label=Coalesce('_name', '_original_filename', Value('unnamed file')),
            ).filter(folder=folder, _label=file_obj.label)
            file_grouper = FileGrouper.objects.filter(files__in=same_name_file_qs).distinct().first()
            new_file_grouper = False

            if not file_grouper:
                new_file_grouper = True
                file_grouper = FileGrouper.objects.create()

            file_obj.grouper = file_grouper
            file_obj.save()
            Version.objects.create(content=file_obj, created_by=request.user)

            # Try to generate thumbnails.
            if not file_obj.icons:
                # There is no point to continue, as we can't generate
                # thumbnails for this file. Usual reasons: bad format or
                # filename.
                file_obj.delete()
                if new_file_grouper:
                    file_grouper.delete()
                # This would be logged in BaseImage._generate_thumbnails()
                # if FILER_ENABLE_LOGGING is on.
                return JsonResponse(
                    {'error': 'failed to generate icons for file'},
                    status=500,
                )
            thumbnail = None
            # Backwards compatibility: try to get specific icon size (32px)
            # first. Then try medium icon size (they are already sorted),
            # fallback to the first (smallest) configured icon.
            for size in (['32'] +
                         filer_settings.FILER_ADMIN_ICON_SIZES[1::-1]):
                try:
                    thumbnail = file_obj.icons[size]
                    break
                except KeyError:
                    continue

            data = {
                'thumbnail': thumbnail,
                'alt_text': '',
                'label': str(file_obj),
                'file_id': file_obj.pk,
            }
            # prepare preview thumbnail
            if type(file_obj) == Image:
                thumbnail_180_options = {
                    'size': (180, 180),
                    'crop': True,
                    'upscale': True,
                }
                thumbnail_180 = file_obj.file.get_thumbnail(
                    thumbnail_180_options)
                data['thumbnail_180'] = thumbnail_180.url
                data['original_image'] = file_obj.url
            return JsonResponse(data)
        else:
            form_errors = '; '.join(['%s: %s' % (
                field,
                ', '.join(errors)) for field, errors in list(
                    uploadform.errors.items())
            ])
            raise UploadException(
                "AJAX request not valid: form invalid '%s'" % (
                    form_errors,))
    except UploadException as e:
        return JsonResponse({'error': str(e)}, status=500)
filer.admin.clipboardadmin.ajax_upload = ajax_upload  # noqa: E305
