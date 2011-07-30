from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings
from mediaserver.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from mediaserver.verify import VerifySource

class CssHandler(tornado.web.RequestHandler):

    def getSource(self, file_name):
        from fs.dependency import changed_since, newer_group

        src = join(structure.CSS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(self.application.site["target_path"],"css",file_name)
        text = None
        srcs = []
        srcs = fs.listdir(structure.CSS_DIR,recursed=True,full_path=True)
        #TODO record dependency with target
        if newer_group(srcs,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
            import codecs
            with codecs.open(target,"w",encoding="utf-8") as f:
                text = u''.join(lines)
                f.write(text)
                f.flush()

        if not text:
            with open(target,"r") as f:
                text = f.read()
        return text

    def acceleratedGet(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.CSS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(self.application.site["target_path"],"css",file_name)
        if newer_assets(src,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
            import codecs
            with codecs.open(target,"w",encoding="utf-8") as f:
                text = u''.join(lines)
                f.write(text)
                f.flush()

        self.set_header("Content-Type","text/css")
        self.set_header('X-Accel-Redirect',"/root/target/%s/css/%s" % (self.application.site["dirname"], file_name))
        logging.log(logging.INFO, "served /root/target/%s/css/%s" % (self.application.site["dirname"], file_name))
        
    def get(self, file_name):
        from os.path import join,isdir
        header_ip = 'X-Real-IP' in self.request.headers or 'X-Forwarded-For' in self.request.headers
        if header_ip:
            self.acceleratedGet(file_name)
        else:
            text = self.getSource(file_name)
            self.write(text)
            self.set_header("Content-Type","text/css")

    def getX(self,file_name):
        try:
            return self.get2(file_name)
        except Exception,e:
            print '...',e
            import traceback; traceback.print_exc()
            
# @cache_control(False)
class JsHandler(tornado.web.RequestHandler):
    """
    Builds .js files from js/and-a-name.js directories
    """

    def __init__(self, application, request):
        super(JsHandler,self).__init__(application, request)
        self.verify_doms = {}
        self.js_loader = tornado.template.Loader(structure.JS_DIR)
        
    def acceleratedGet(self, file_name):
        import codecs
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(self.application.site["target_path"],"js",file_name)
        if newer_assets(src,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with codecs.open(target,"w", encoding="utf-8") as f:
                text = u''.join(lines)
                f.write(text)
                f.flush()

        self.set_header("Content-Type","text/javascript")
        self.set_header('X-Accel-Redirect',"/root/target/%s/js/%s" % (self.application.site["dirname"], file_name))
        
    def getSource(self, file_name):
        import codecs
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(self.application.site["target_path"],"js",file_name)
        text = None
        if newer_assets(src,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with codecs.open(target,"w",encoding="utf-8") as f:
                text = u''.join(lines)
                f.write(text)
                f.flush()

        if not text:
            with open(target,"r") as f:
                text = f.read()
        return text
        
    def get(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        header_ip = 'X-Real-IP' in self.request.headers or 'X-Forwarded-For' in self.request.headers
        if header_ip:
            self.acceleratedGet(file_name)
        else:
            text = self.getSource(file_name)
            self.write(text)
            self.set_header("Content-Type","text/javascript")

