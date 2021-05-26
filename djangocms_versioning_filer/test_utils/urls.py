from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve


try:
    from django.views.i18n import JavaScriptCatalog
    javascript_catalog = JavaScriptCatalog.as_view()
except ImportError:
    from django.views.i18n import javascript_catalog


admin.autodiscover()

urlpatterns = [
    url(r'^media/(?P<path>.*)$', serve,  # NOQA
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^jsi18n/(?P<packages>\S+?)/$', javascript_catalog),  # NOQA
    url(r'^', include('filer.server.urls')),
    url(r'^filer/', include('filer.urls')),
    url(r'^', include('djangocms_versioning_filer.urls')),
]
try:
    i18n_urls = [
        url(r'^admin/', admin.site.urls),
    ]
except Exception:
    i18n_urls = [
        url(r'^admin/', include(admin.site.urls)),
    ]

if settings.USE_CMS:
    i18n_urls.append(
        url(r'^', include('cms.urls'))  # NOQA
    )

urlpatterns += i18n_patterns(*i18n_urls)
urlpatterns += staticfiles_urlpatterns()
