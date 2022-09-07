import os
from tempfile import mkdtemp


ENABLE_MODERATION = bool(os.environ.get('ENABLE_MODERATION', False))
EXTRA_INSTALLED_APPS = []
if ENABLE_MODERATION:
    EXTRA_INSTALLED_APPS += ['adminsortable2', 'djangocms_moderation']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HELPER_SETTINGS = {
    'SECRET_KEY': 'versioningfilertestsuitekey',
    'ROOT_URLCONF': 'djangocms_versioning_filer.test_utils.urls',
    'TIME_ZONE': 'Europe/Zurich',
    'INSTALLED_APPS': [
        'easy_thumbnails',
        'mptt',
        'djangocms_versioning_filer',
        'filer',
        'djangocms_versioning',
        'djangocms_picture',
        'djangocms_versioning_filer.plugins.picture',
        'djangocms_audio',
        'djangocms_versioning_filer.plugins.audio',
        'djangocms_file',
        'djangocms_versioning_filer.plugins.file',
        'djangocms_video',
        'djangocms_versioning_filer.plugins.video',
    ] + EXTRA_INSTALLED_APPS,
    'MIGRATION_MODULES': {
        'sites': None,
        'contenttypes': None,
        'admin': None,
        'easy_thumbnails': None,
        'sessions': None,
        'auth': None,
        'cms': None,
        'menus': None,
        'filer': None,
        'djangocms_versioning_filer': None,
        'djangocms_versioning': None,
        'djangocms_moderation': None,
        'djangocms_picture': None,
        'picture': None,
        'djangocms_audio': None,
        'audio': None,
        'djangocms_file': None,
        'file': None,
        'djangocms_video': None,
        'video': None,
    },
    'CMS_PERMISSION': True,
    'LANGUAGE_CODE': 'en',
    'LANGUAGES': (
        ('en', 'English'),
        ('de', 'German'),
        ('fr', 'French'),
        ('it', 'Italiano'),
    ),
    'CMS_LANGUAGES': {
        1: [
            {
                'code': 'en',
                'name': 'English',
                'fallbacks': ['de', 'fr']
            },
            {
                'code': 'de',
                'name': 'Deutsche',
                'fallbacks': ['en']  # FOR TESTING DO NOT ADD 'fr' HERE
            },
            {
                'code': 'fr',
                'name': 'Française',
                'fallbacks': ['en']  # FOR TESTING DO NOT ADD 'de' HERE
            },
            {
                'code': 'it',
                'name': 'Italiano',
                'fallbacks': ['fr']  # FOR TESTING, LEAVE AS ONLY 'fr'
            },
        ],
    },
    'THUMBNAIL_PROCESSORS': (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    ),
    'FILE_UPLOAD_TEMP_DIR': mkdtemp(),
    'FILER_CANONICAL_URL': 'test-path/',
    'DEFAULT_AUTO_FIELD': 'django.db.models.AutoField',
    'CMS_CONFIRM_VERSION4': True,
}


def run():
    from app_helper import runner
    runner.cms('djangocms_versioning_filer', extra_args=[])


if __name__ == "__main__":
    run()
