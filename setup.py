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
    'Django>=1.11,<2.0',
    'django-cms',
    'djangocms-versioning',
    'django-filer>=1.5.0'
]

TEST_REQUIREMENTS = [
    'djangocms_helper',
    'djangocms-picture>=2.3.0',
    'djangocms-audio>=1.1.0',
    'djangocms-file>=2.3.0',
    'djangocms-video>=2.1.1',
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
        "http://github.com/divio/django-cms/tarball/release/4.0.x#egg=django-cms-4.0.0",
        "http://github.com/divio/djangocms-versioning/tarball/master#egg=djangocms-versioning-0.0.24",
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
