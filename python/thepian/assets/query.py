from thepian.tickets import Identity, IdentityPath
from thepian.conf import structure

from os.path import join
from fs import walk, listdir, makedirs

class AssetManager(object):
    
    def create(self,**kwargs):
        from base import Asset
        return Asset(**kwargs)
    
    def get(self,path):
        return AssetQuery(paths=(path,)).get()
        
    def all(self):
        q = AssetQuery()
        return q
        
    def filter(self,path=None,paths=None,valid=None,ready=None):
        if not paths and path:
            paths = (path,)
        q = AssetQuery(paths=paths,valid=valid,ready=ready)
        return q
        
    def get_static_asset(self,path):
        #TODO phase out, use filter().get() instead
        from static import Static
        static = Static(path=path)
        return static
        
    def get_status_asset(self,status):
        from base import Asset
        asset = Asset(ip4="127.0.0.1")
        asset.force_status(status)
        return asset
        
class AssetEntity(Identity):
    """Top level entity containing assets. It is used to track changes"""

    def __init__(self,**kwargs):
        super(AssetEntity,self).__init__(**kwargs)
        self.upload_directory = structure.UPLOADS_DIR + str(self.path)
        makedirs(self.upload_directory)
        self.download_directory = structure.DOWNLOADS_DIR + str(self.path)
        makedirs(self.download_directory)

    def get_uploaded_assets(self):
        from base import Asset 
        return [Asset(parent=self,encoded=e) for e in listdir(self.upload_directory)]

class StaticEntity(object):
    def __init__(self,path):
        self.path = path
        self.upload_directory = structure.MEDIASITE_DIRS[0] + "/%s/%s" % (self.path[1],self.path[2])
        makedirs(self.upload_directory)
        self.download_directory = structure.DOWNLOADS_DIR + str(self.path)
        makedirs(self.download_directory)
        
    def get_uploaded_assets(self):
        from static import Static
        return [Static(parent=self, file_name=file_name) for file_name in listdir(self.upload_directory)]
        
class AssetQuery(object):
    """
    valid   Only valid assets
    ready   Only ready assets
    """
    
    description = ""
    
    def __init__(self,paths=None,valid=None,ready=None):
        self.valid = valid
        self.ready = ready
        self.assets = []
        if not paths:
            self.paths = None
        else:
            self.paths = []
            for p in paths:
                if isinstance(p,IdentityPath):
                    self.paths.append(p)
                elif isinstance(p,basestring):
                    self.paths.append(IdentityPath(path_string=p))
                else:
                    self.paths.append(IdentityPath(*iter(p)))
    
    def get_all_entries_as_paths(self):
        r = []
        for top in listdir(structure.UPLOADS_DIR):
            for middle in listdir(join(structure.UPLOADS_DIR,top)):
                for ipnumber in listdir(join(structure.UPLOADS_DIR,top,middle)):
                    r.append(IdentityPath(top,middle,ipnumber))
        return r
        
    def __load(self):
        from base import Asset
        from static import Static
        paths = self.paths or self.get_all_entries_as_paths()

        self.assets = []
        for path in paths:
            if len(path) == 3:
                klass = path.static_path and StaticEntity or AssetEntity
                self.assets.extend(klass(path=path).get_uploaded_assets())
            if len(path) == 4:
                klass = path.static_path and Static or Asset
                self.assets.append(klass(path=path)) #parent_class=AssetEntity
        
    def __len__(self):
        self.__load()
        return len(self.assets)
        
    def __iter__(self):
        self.__load()
        for a in self.assets:
            if self.valid is True and not a.status in ("valid","ready"):
                continue
            if self.valid is False and a.status in ("valid","ready"):
                continue
            if self.ready is True and not a.status in ("ready",):
                continue
            if self.ready is False and a.status in ("ready",):
                continue
            yield a
            
    def __getitem__(self,i):
        return self.assets[i]
        
    def extend(self,assets):
        self.assets.extend(assets)
        
    def append(self,asset):
        self.assets.append(asset)
        
    def get(self):
        from base import Asset
        self.__load()
        l = len(self.assets)
        if not l:
            raise Asset.NotFound, "Query didn't match any assets: %s" % self.description
        if l>1:
            pass #TODO raise ?
        return self.assets[0]

    def ensure_bases(self):
        """Ensure that bases are being made or present for the assets in the query"""
        self.__load()
        for asset in self.assets:
            asset.refresh()
            
    

def get_entity(id):
    if isinstance(id,Identity):
        return id
    return Identity(encoded=id)
    
