.. _extending_filer:

Adding custom file upload constraints
.....................................

Overview
````````
Using custom file upload constraints functionality, it allows to add a check before it get uploaded.

Setting
~~~~~~~

Set ``FILER_FILE_CONSTRAINTS`` to project ``settings.py`` file with a list of dotted paths to functions which does the validation.

For example, Let's say project has ``myapp`` package which has ``helper.py`` file where we define constraint method as below

.. code-block:: python

    def file_validation(request, folder_id=None):
        VALIDATION_MESSAGE = _('This is the custom validation message')

        # Do the custom check if not valid then raise error
        ...

        if not valid:
            raise ValidationError(VALIDATION_MESSAGE)
        return

Then, `FILER_FILE_CONSTRAINTS` attribute can be added to project ``setting.py`` file as below.

.. code-block:: python

    FILER_FILE_CONSTRAINTS = ['myapp.helper.file_validation']
