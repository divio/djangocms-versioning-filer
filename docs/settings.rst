.. _settings:

Settings
========

``FILER_FILE_CONSTRAINTS``
--------------------------

Defines dotted path to function. Default is None

If you would like to introduce new constraint to filer, you can use this setting and pass a list of dotted paths to functions. The
method should raise validation error for the case which is not valid.

e.g::

    FILER_FILE_CONSTRAINTS = ['myapp.helper.file_check_method_name']
