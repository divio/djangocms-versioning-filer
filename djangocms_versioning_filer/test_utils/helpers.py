# -*- coding: utf-8 -*-
"""Module taken from filer repo tests.helpers
As that can no longer be imported the path of least resistance was to copy it over
"""

from __future__ import absolute_import

from filer.models.clipboardmodels import Clipboard, ClipboardItem
from filer.models.foldermodels import Folder
from filer.utils.compatibility import PILImage, PILImageDraw


def create_image(mode='RGB', size=(800, 600)):
    image = PILImage.new(mode, size)
    draw = PILImageDraw.Draw(image)
    x_bit, y_bit = size[0] // 10, size[1] // 10
    draw.rectangle((x_bit, y_bit * 2, x_bit * 7, y_bit * 3), 'red')
    draw.rectangle((x_bit * 2, y_bit, x_bit * 3, y_bit * 8), 'red')
    return image
