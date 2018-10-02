import os
from tempfile import mkdtemp


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HELPER_SETTINGS = {
    'TIME_ZONE': 'Europe/Zurich',
    'INSTALLED_APPS': [
        'easy_thumbnails',
        'mptt',
        'djangocms_versioning',
        'djangocms_versioning_filer',
        'filer',
    ],
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
}


def run():
    from djangocms_helper import runner
    runner.cms('djangocms_versioning_filer', extra_args=[])


if __name__ == "__main__":
    run()
