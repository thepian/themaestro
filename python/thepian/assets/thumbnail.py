import os
from os.path import isfile, isdir, getmtime, dirname, splitext, getsize
from tempfile import mkstemp
from shutil import copyfile
from subprocess import Popen, PIPE

from PIL import Image, ImageFilter

from thepian.conf import structure
from thepian.utils import makedirs

from base import extension2mimetype
from processors import get_valid_options, dynamic_import

class ThumbnailException(Exception):
    pass


class Thumbnail(object):
    
    def __init__(self,asset,variant,width,height,extension=None, opts=None, quality=85, processors=None):
        self.asset = asset
        self.extension = extension if extension in extension2mimetype else 'png'
        self.variant = variant
        self.requested_size = (width,height)
        self.quality = quality
        
        self.source = self.asset.image_bases[0]
        self.filename = "%s-%sx%s.%s" % (splitext(self.source.file_name)[0], width,height,extension)
        self.mimetype = extension2mimetype[self.extension]
        self.path = "%s/%s/%s" % (dirname(self.source.path),self.variant,self.filename)
        self.file_path = "%s/%s/%s" % (self.source.thumbnail_directory,self.variant,self.filename)
        
        if processors is None:
            processors = dynamic_import(structure.THUMBNAIL_PROCESSORS)
        self.processors = processors
        
        # Set Thumbnail opt(ion)s
        VALID_OPTIONS = get_valid_options(processors)
        opts = opts or []
        # Check that all options received are valid
        for opt in opts:
            if not opt in VALID_OPTIONS:
                raise TypeError('Thumbnail received an invalid option: %s' % opt)
        self.opts = [opt for opt in VALID_OPTIONS if opt in opts]

    def ensure(self):
        if not isfile(self.file_path) or (self.source.exists and getmtime(self.source.file_path) > getmtime(self.file_path)):
            makedirs(dirname(self.file_path))
            self._do_generate()

    def _get_data(self):
        if not hasattr(self, '_data'):
            return None
        return self._data

    def _set_data(self, image):
        if isinstance(image, Image.Image):
            self._data = image
        else:
            try:
                self._data = Image.open(image)
            except IOError, detail:
                raise ThumbnailException("%s: %s" % (detail, image))
    data = property(_get_data, _set_data)

    
    def _do_generate(self):
        """
        Generates the thumbnail image.

        This a semi-private method so it isn't directly available to template
        authors if this object is passed to the template context.
        """
        im = self.source.image_data

        for processor in self.processors:
            im = processor(im, self.requested_size, self.opts)

        self.data = im

        if self.source.image_data == self.data and self.source.filetype == 'jpg':
            copyfile(self.source.file_path, self.file_path)
        else:
            try:
                im.save(self.file_path, "PNG", quality=self.quality, optimize=1)
            except IOError:
                # Try again, without optimization (the JPEG library can't
                # optimize an image which is larger than ImageFile.MAXBLOCK
                # which is 64k by default)
                try:
                    im.save(self.file_path, "PNG", quality=self.quality)
                except IOError, detail:
                    raise ThumbnailException(detail)

    
    