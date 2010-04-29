from __future__ import with_statement
from os.path import join,isdir

from thepian.conf import structure
from sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web

class HomeHandler(tornado.web.RequestHandler):
    
    def get(self):
        pass

class CssHandler(tornado.web.RequestHandler):

    def get(self,file_name):
        header_ip = self.get_header('X-Real-IP') or self.get_header('X-Forwarded-For')

        src = join(structure.CSS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
        text = None
        if newer_assets(src,target):
            lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
            with open(target,"w") as f:
                text = ''.join(lines)
                f.write(text)
                
        self.set_header("Content-Type","text/css")
        if header_ip:
            # if nginx in front accelerate
            self.set_header('X-Accel-Redirect',"/targetmedia/css/"+file_name)
        else:
            if not text:
                with open(target,"w") as f:
                    text = f.read()
            self.write(text) 


class JsHandler(tornado.web.RequestHandler):
    def get(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise Http404
        target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
        text = None
        if newer_assets(src,target) or request.GET.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with open(target,"w") as f:
                text = ''.join(lines)
                f.write(text)

        self.set_header("Content-Type","text/javascript")
        if header_ip:
            # if nginx in front accelerate
            self.set_header('X-Accel-Redirect',"/targetmedia/js/"+file_name)
        else:
            if not text:
                with open(target,"w") as f:
                    text = f.read()
            self.write(text) 

