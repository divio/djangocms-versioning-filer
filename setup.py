from setuptools import find_packages, setup

import djangocms_versioning_filer


CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Framework :: Django',
    'Framework :: Django :: 1.11',
]

INSTALL_REQUIREMENTS = [
    'Django>=1.11,<3.0',
    'django-cms',
    'django-filer>=1.5.0',
    'djangocms-versioning',
]

TEST_REQUIREMENTS = [
    'djangocms_helper',
    'djangocms-moderation',
    'djangocms-picture',
    'djangocms-audio',
    'djangocms-file',
    'djangocms-video',
    'factory-boy',
    'mock'
]

setup(
    name='djangocms-versioning-filer',
    author='Divio AG',
    author_email='info@divio.ch',
    url='http://github.com/divio/djangocms-versioning-filer',
    license='BSD',
    version=djangocms_versioning_filer.__version__,
    description=djangocms_versioning_filer.__doc__,
    dependency_links=[
        "https://github.com/divio/django-cms/tarball/release/4.0.x#egg=django-cms-4.0.0",
        "https://github.com/divio/djangocms-moderation/tarball/release/1.0.x#egg=djangocms-moderation-1.0.22",
        "https://github.com/divio/djangocms-versioning/tarball/master#egg=djangocms-versioning-0.0.26",
    ],
    long_description=open('README.rst').read(),
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='test_settings.run',
    tests_require=TEST_REQUIREMENTS,
)
