import fs
from os.path import splitext, join, exists
from base import AssetFile

from thepian.conf import structure
from distutils.dep_util import newer

def StaticPath(path):
    assert path[0] == "static"
    return path
    
class Static(object):
    """
    
    status  invalid,noimage,novideo,ready
    """
    
    INVALID_CAPTION = "Invalid Upload"
    #objects = AssetManager()
    
    unsupported_file = None
    """Asset for unsupported file icons"""
    
    subdomain = "media"
    
    class NotFound(Exception):
        """Thrown by Asset.objects methods when no matching asset exists"""
        pass
    
    def __init__(self,path=None,parent=None,file_name=None):
        """Create asset based on the original file path
        file_name can be with or without extension
        
        top,area,file_name = path"""
        if path:
            st,top,area,file_name = StaticPath(path)
        else:
            st,top,area = StaticPath(parent.path)

        self.upload_directory = join(structure.MEDIASITE_DIRS[0],top,area)
        if not exists(self.upload_directory):
            self.original = None
            return #TODO use unsupported file
        name,ext = splitext(file_name)
        if ext is '':
            originals = fs.listdir(self.upload_directory,filters=(fs.filters.fnmatch(file_name+".*"),fs.filters.no_hidden,fs.filters.no_system))
            if len(originals)==0:
                self.original = None
                return #TODO use unsupported file
            file_name = originals[0]
            
        self.download_directory = join(structure.DOWNLOADS_DIR,"static",top,area,name)
        fs.makedirs(self.download_directory)
        
        self.original = AssetFile(self,join(self.upload_directory,file_name))
        self.original_category = self.original.filetype[1]
        self.caption = self.original.caption
        self.path = "/%s/%s/%s/%s"  % ('static',top,area,name)
        
    
    def __unicode__(self):
        return unicode(self.path)
        
    def to_json(self):
        return {
            'path':self.path,
            'parent':"/".join(self.path.split("/")[:-1]),
            'caption':self.caption
        }
        
    def build_upload_file(self,upload_file_name):
        return AssetFile(self,join(self.upload_directory,upload_file_name))
    def build_download_file(self,download_file_name):
        return AssetFile(self,join(self.download_directory,download_file_name))

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
    
    def refresh(self):
        """Create download/video.* audio.* imageN.*
        returns: mimetype, category, supported, bases_directory, thumbnail_directory, path, image_bases, video_bases
        """
        supported = False
        category = "file"
        mimetype = "unknown/unknown"
        if self.original: 
            mimetype, category, supported = self.original.filetype
        if not supported:
            print "not supported ", category, mimetype, self.original.file_name
            bases_directory = join(structure.MEDIASITE_DIRS[0],"icons","unsupported-%s" % category)
            thumbnail_directory = join(structure.DOWNLOADS_DIR,"icons","unsupported-%s" % category)
            path = "/%s/%s"  % ('icons',"unsupported-%s" % category)
        else:
            bases_directory = thumbnail_directory = self.download_directory
            path = self.path
            
            if self.original.filetype[0] == "image/png":
                image0 = AssetFile(self,join(bases_directory,"image0.png"),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,"image0.png"))
            else:            
                image0 = AssetFile(self,join(bases_directory,"image0.jpg"),thumbnail_directory=thumbnail_directory,path="%s/%s" % (path,"image0.jpg"))
            if not image0.exists or newer(self.original.file_path,image0.file_path):
                image0.make_base_image(self.original,0)

        existing = fs.listdir(bases_directory,filters=(fs.filters.no_hidden,fs.filters.no_system,fs.filters.no_directories))
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
        
