from __future__ import with_statement
import os
from os.path import join,isdir

from thepian.conf import structure
from sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from verify import VerifySource

class HomeHandler(tornado.web.RequestHandler):
    
    def get(self):
        pass

class CssHandler(tornado.web.RequestHandler):

    def get(self,file_name):
        try:
            return self.get2(file_name)
        except Exception,e:
            print '...',e
            import traceback; traceback.print_exc()
            
    def get2(self,file_name):
        header_ip = 'X-Real-IP' in self.request.headers or 'X-Forwarded-For' in self.request.headers
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
                f.flush()
                
        self.set_header("Content-Type","text/css")
        if header_ip:
            # if nginx in front accelerate
            self.set_header('X-Accel-Redirect',"/targetmedia/css/"+file_name)
        else:
            if not text:
                with open(target,"r") as f:
                    text = f.read()
            self.write(text) 


class JsHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, transforms=None):
        super(JsHandler,self).__init__(application, request, transforms)
        self.verify_doms = {}
        self.js_loader = tornado.template.Loader(structure.JS_DIR)
        
    def acceleratedGet(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
        if newer_assets(src,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with open(target,"w") as f:
                text = ''.join(lines)
                f.write(text)
                f.flush()

        self.set_header("Content-Type","text/javascript")
        self.set_header('X-Accel-Redirect',"/targetmedia/js/"+file_name)
        
    def getSource(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
        text = None
        if newer_assets(src,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with open(target,"w") as f:
                text = ''.join(lines)
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

class JsVerifyHandler(JsHandler):
    
    def render_js(self, template_name, **kwargs):
        t = self.js_loader.load(template_name)
        base = {}
        #TODO add some extras ?
        base.update(**kwargs)
        html = t.generate(base)
        self.finish(html)
    
    def get(self, file_name, test_path):
        try:
            source = self.getSource(file_name)
            src = join(structure.JS_DIR,file_name,'verify')
            if not isdir(src):
                raise tornado.web.HTTPError(404)

            specs = VerifySource.list(src)
            #TODO if index.html exists use that
            self.render("verify/index.html", title="Specs for %s - %s" % (file_name,test_path), source = source, specs = specs)
        except Exception,e:
            print e
            
    def post(self, file_name, test_path):
        try:
            print 'posted results: ', file_name
            self.write('results noted.')
        except Exception,e:
            print e
        
class JsVerifyDetailHandler(JsHandler):
    
    
    def getVerifyPage(self,path):
        if path not in self.verify_doms:
            import html5lib
            from xml.etree import cElementTree 
            p = join(structure.JS_DIR,path)
            # parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilders("dom"))
            parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("etree", cElementTree))
            with open(p) as f:
                doc = parser.parse(f)
                self.verify_doms[path] = doc
            
        return self.verify_doms[path]
        
    
    def get(self, directory, file_name, test_path):
        try:
            path = join(directory,'verify')
            verify = VerifySource.get(path,file_name[:-3])
            if not verify.source:
                raise tornado.web.HTTPError(404)
            
            self.write(verify.render(xsrf_form_html = self.xsrf_form_html()))
        except Exception,e:
            print e
            
        
class JsVerifyAllHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.render("verify/all.html")
        
class JoHandler(tornado.web.RequestHandler):

    def get(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        header_ip = 'X-Real-IP' in self.request.headers or 'X-Forwarded-For' in self.request.headers
        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)

        print 'hello'
        text = ''
        with open(join(src,'1.js'),"r") as f:
            text = f.read()
        try:
            class SC(object):
                pass
            sc = SC()
            sc.path = file_name
            sc.script_name = file_name
            sc.script_type = "JavaScript"
            sc.namespace = ""
            sc.root_scope = ""
            sc.strictMode = False
            from sources import joparser
            node = joparser.parse(sc,text)

            # jocore.libs.extend(structure.JS_DIR)
            # jocore.load(file_name)
            # text = jocore.compile()
        except Exception,e:
            print e, "......."
            import traceback; traceback.print_exc()
        
        self.set_header("Content-Type","text/javascript")
        self.write(text) 


