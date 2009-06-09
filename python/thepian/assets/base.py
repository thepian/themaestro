from thepian.tickets import Identity
from thepian.conf import structure
from thepian.utils import makedirs
from thepian.utils import magic

from fs import listdir,filters
from os.path import join, splitext, isfile, split, dirname
from os import pathsep, walk, stat

from distutils.dep_util import newer


from PIL import Image, ImageFilter

from query import AssetQuery, AssetManager

extension2mimetype = {
    'png':'image/png', 'jpg':'image/jpeg', 'jpeg':'image/jpeg', 'gif':'image/gif', 'tif':'image/tiff',
    'mov':'video/quicktime', 'qt':'video/quicktime',
    'avi':'video/msvideo',
    'mpeg':'video/mpeg', 'mpg':'video/mpeg', 
    'mpv2': 'video/x-mpeg2', 'mp2v':'video/x-mpeg2',
}

KNOWN_TYPES = {
    'image/png': ('image',True),
    'image/jpeg': ('image',True),
    'image/tiff': ('image',True),
    'image/gif': ('image',True),
    'video/mpeg': ('video',True),
    'video/x-pn-realvideo': ('video',True),
    'video/quicktime': ('video',True),
    'video/matroska': ('video',True),
    'video/x-msvideo': ('video',True),
}
# 'unsupported' if not in dictionary

PIL_TYPE = {
    'image/png' : 'PNG',
    'image/jpeg' : 'JPEG',
    'image/gif' : 'GIF'
}

class AssetException(Exception):
    pass
    
class AssetFile(object):
    """Uploaded file or base download file. 
    Thumbnails are derived from base files but have their own class.
    
    thumbnail dir = absolute path 
    file path = asset path + file name
    """
    def __init__(self,asset,file_path,thumbnail_directory=None,path=None):
        """ file path - absolute path """
        self.asset = asset
        self.file_path = file_path
        self.file_name = split(file_path)[1]
        self.thumbnail_directory = thumbnail_directory or dirname(file_path)
        self.path = path
        # mime type
        
    def __repr__(self):
        return "[%s] %s" %  (repr(self.asset), self.path)

    def _get_caption(self):
        return splitext(self.file_name)[0]
    caption = property(_get_caption)
    
    def _get_filetype(self):
        """
        Describes the file returns a tuple of (mimetype,category,supported?)
        """
        if not hasattr(self, '_filetype'):
            ftype = magic.file(self.file_path)
            if ftype == "audio/x-wav" and self.file_name.endswith(".avi"):
                ftype = "video/x-msvideo"
            if ftype.find('Microsoft Office Document') != -1:
                ftype = 'document/microsoft'
            elif ftype.find('PDF document') != -1:
                ftype = 'document/pdf'
            elif ftype == 'data':
                if self.file_path.endswith(".mkv"):
                    ftype = "video/matroska"
                elif self.file_path.endswith(".avi"):
                    ftype = "video/x-msvideo"
                from subprocess import Popen, PIPE
                filep = Popen(("file",self.file_path),stdout=PIPE,close_fds = True)
                result = filep.communicate()[0].split(':')
                if len(result) == 2:
                    if result[1].startswith("Matroska data"):
                        ftype = "video/matroska"
                
            #TODO extension2mimetype.get(splitext(self.file_path)[1].lower(),"unknown/unknown")
            category, supported = KNOWN_TYPES.get(ftype,('file',False))
            self._filetype = (ftype, category, supported)
            #print self._filetype
        return self._filetype
    filetype = property(_get_filetype)
    
    def _get_file_size(self):
        return stat(self.file_path).st_size
    file_size = property(_get_file_size)

    def _get_image_data(self):
        if not hasattr(self, '_data'):
            if not self.exists:
                raise AssetException("Asset file: '%s' does not exist." % self.file_path)
            try:
                self._data = Image.open(self.file_path)
            except IOError, detail:
                raise AssetException(detail)
        return self._data
    def _set_image_data(self, im):
        self._data = im
    image_data = property(_get_image_data, _set_image_data)
    
    def make_base_image(self,original,index):
        mimetype, category, supported = original.filetype
        #print "make...", category
        #TODO if more than twice the width of 480 / floor(width/640)
        if category == "image":
            tp = PIL_TYPE.get(mimetype,"JPEG")
            try:
                original.image_data.save(self.file_path, tp, optimize=1)
            except IOError:
                try:
                    original.image_data.save(self.file_path, tp)
                except IOError, detail:
                    import traceback
                    traceback.print_exc(detail)
                    raise AssetException(detail)
        elif category == "video":
            print 'video asset: %s ' % original.file_path
            from subprocess import Popen, PIPE
            ff_cmd = 'ffmpeg -y -i "%s" -f mjpeg -ss 10 -vframes 1 -s 480x360 -an %s' % (original.file_path,self.file_path)
            #print ff_cmd
            ffmpegp = Popen(ff_cmd,shell=True)
            sts = os.waitpid(ffmpegp.pid,0)
            #TODO temp, rename, mk/del pid
            """
[me@here dir]$ ffmpeg -y -i someclip.avi  \
[me@here dir]> -f mjpeg -ss 10 -vframes 1 \
[me@here dir]> -s 150x100 -an thumb.jpg
            """
        else:
            print "base image skipped for", mimetype, original.path
            assert False, "should never get here %s,%s" % (category,self.original.file_path)
        

    def _check_exists(self):
        if not hasattr(self, '_exists'):
            self._exists = isfile(self.file_path)
        return self._exists
    exists = property(_check_exists)


IGNORE_IN_UPLOADS = ('.DS_Store',)   #TODO ignore props file     

class Asset(Identity):
    """
    
    status  invalid,noimage,novideo,ready
    """
    
    INVALID_CAPTION = "Invalid Upload"
    objects = AssetManager()
    
    unsupported_file = None
    """Asset for unsupported file icons"""
    
    class NotFound(Exception):
        """Thrown by Asset.objects methods when no matching asset exists"""
        pass
    
    def __init__(self,**kwargs):
        super(Asset,self).__init__(**kwargs)
        self.upload_directory = structure.UPLOADS_DIR + str(self.path)
        self.download_directory = structure.DOWNLOADS_DIR + str(self.path)
        if self.generated:
            makedirs(self.upload_directory) #TODO make conditional
            makedirs(self.download_directory)
    
    def __unicode__(self):
        return unicode(self.path)

    def to_json(self):
        return {
            'path':self.path,
            'parent': self.parent.to_json(),
            #'caption':self.caption
        }
        
    def build_upload_file(self,upload_file_name):
        """Used to construct file uploaded to the site"""
        return AssetFile(self,join(self.upload_directory,upload_file_name))
    def build_download_file(self,download_file_name):
        return AssetFile(self,join(self.download_directory,download_file_name))

    def _get_original(self):
        if not hasattr(self,"_original") or  not self._original:
            uploads = [f for f in listdir(self.upload_directory) if not f.startswith(".") and not f in IGNORE_IN_UPLOADS]
            if len(uploads) == 0:
                return None
            self._original = AssetFile(self,join(self.upload_directory,uploads[0]))
        return self._original
    original = property(_get_original)
    
    def _get_original_category(self):
        original = self._get_original()
        return original.filetype[1]
    original_category = property(_get_original_category)
    
    def _get_status(self):
        mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases = self.refresh()
        if not supported:
            return "invalid"
        if len(image_bases) == 0:
            return "invalid"    
        if category == "video" and len(video_bases) == 0:
            return "valid"
        return "ready"
    status = property(_get_status)
    
    def _get_caption(self):
        original = self._get_original()
        if not original:
            return self.INVALID_CAPTION
        return original.caption
    caption = property(_get_caption)
        
    def force_status(self,status):
        bases_directory = join(structure.MEDIASITE_DIRS[0],"icons",status)
        thumbnail_directory = join(structure.DOWNLOADS_DIR,"icons",status)
        path = "/%s/%s"  % ('icons',status)
        image0 = AssetFile(self,join(bases_directory,"image0.jpg"),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,"image0.jpg"))
        self._image_bases = (image0,)
        
    def refresh(self):
        """Create download/video.* audio.* imageN.*
        returns: mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases
        """
        supported = False
        category = "file"
        mimetype = "unknown/unknown"
        original = self.original
        if original: 
            mimetype, category, supported = original.filetype
        if not supported:
            print "not supported ", category, mimetype, original.file_name
            bases_directory = join(structure.MEDIASITE_DIRS[0],"icons","unsupported-%s" % category)
            thumbnail_directory = join(structure.DOWNLOADS_DIR,"icons","unsupported-%s" % category)
            path = "/%s/%s"  % ('icons',"unsupported-%s" % category)
        else:
            bases_directory = thumbnail_directory = self.download_directory
            path = self.path
            
            if self.original.filetype == "image/png":
                image0 = AssetFile(self,join(bases_directory,"image0.png"),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,"image0.png"))
            else:            
                image0 = AssetFile(self,join(bases_directory,"image0.jpg"),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,"image0.jpg"))
            if not image0.exists or newer(self.original.file_path,image0.file_path):
                image0.make_base_image(self.original,0)

        existing = listdir(bases_directory,filters=(filters.no_hidden,filters.no_system,filters.no_directories))
        image_file_names = ("image0.jpg","image0.png","image1.jpg","image1.png","image2.jpg","image2.png","image3.jpg","image3.png","image4.jpg","image4.png","image5.jpg","image5.png","image6.jpg","image6.png","image7.jpg","image7.png","image8.jpg","image8.png","image9.jpg""image9.png")
        video_file_names = ("video480.m4v","video480.flv","video320.m4v","video320.flv")
        image_bases = []
        video_bases = []
        for f in existing:
            if f in image_file_names:
                image_bases.append(AssetFile(self,join(bases_directory,f),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,f)))
            if f in video_file_names:
                video_bases.append(AssetFile(self,join(bases_directory,f),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,f)))
        
        return mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases
        
    def get_bases(self):
        mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases = self.refresh()
        if category == "video":
            r = []
            r.extend(video_bases)
            r.extend(image_bases)
            return r
        return image_bases
    bases = property(get_bases)
    
    def get_main_bases(self):
        """The primary base files given the category. For video it is the video, for images it is the still"""
        mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases = self.refresh()
        if category == "video":
            return video_bases
        return image_bases
    main_bases = property(get_main_bases)
    
    def get_image_bases(self):
        if hasattr(self,"_image_bases") and self._image_bases:
            return self._image_bases
        mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases = self.refresh()
        return image_bases
    image_bases = property(get_image_bases)
        
    def get_thumb(self,variant="0",width=100,height=100,extension='png'):
        from thumbnail import Thumbnail
        thumb = Thumbnail(asset=self,variant=variant,width=width,height=height,extension=extension,opts=("crop",))
        thumb.ensure()
        return thumb
        
#                                                                                                                                      
# wrapper around PIL 1.1.6 Image.save to preserve PNG metadata
#
# public domain, Nick Galbreath                                                                                                        
# http://blog.modp.com/2007/08/python-pil-and-png-metadata-take-2.html                                                                 
#                                                                                                                                       
def pngsave(im, file):
    # these can be automatically added to Image.info dict                                                                              
    # they are not user-added metadata
    reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')

    # undocumented class
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()

    # copy metadata into new object
    for k,v in im.info.iteritems():
        if k in reserved: continue
        meta.add_text(k, v, 0)

    # and save
    im.save(file, "PNG", pnginfo=meta)
