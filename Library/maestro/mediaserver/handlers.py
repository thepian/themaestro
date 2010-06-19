from __future__ import with_statement
import os, fs, os.path
from os.path import join,isdir

from thepian.conf import structure
from sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from verify import VerifySource

class HomeHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.render("mediahome.html")
        
    def post(self):
        if "stop-server" in self.request.arguments.keys():
            self.application.ioloop.stop()
        self.write('done.')

class DirectoryHandler(tornado.web.RequestHandler):
    
    def get(self):
        # print self.application.site['path']
        info = {
            "list": os.listdir(self.application.site['path'] + self.request.path), 
            "path": self.request.path,
            "SITE_TITLE": "PageSpec",
            "MEDIA_URL": ""
        }
        self.render("directory.html",**info)
        
class StaticSiteHandler(tornado.web.RequestHandler):
    """
    Serve static the content located in the site specific static file directory
    """
    def __init__(self, application, request):
        RequestHandler.__init__(self, application, request)
        self.root = os.path.abspath(application.site["path"]) + os.path.sep

    def head(self):
        self.get()

    def get(self):
        abspath = os.path.abspath(os.path.join(self.root, self.request.path))
        print abspath
        if not abspath.startswith(self.root):
            raise HTTPError(403, "%s is not in root static directory", path)
        if not os.path.exists(abspath):
            raise HTTPError(404)
        if not os.path.isfile(abspath):
            raise HTTPError(403, "%s is not a file", path)

        stat_result = os.stat(abspath)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

        self.set_header("Last-Modified", modified)
        if "v" in self.request.arguments:
            self.set_header("Expires", datetime.datetime.utcnow() + \
                                       datetime.timedelta(days=365*10))
            self.set_header("Cache-Control", "max-age=" + str(86400*365*10))
        else:
            self.set_header("Cache-Control", "public")
        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                self.set_status(304)
                return

        header_ip = 'X-Real-IP' in self.request.headers or 'X-Forwarded-For' in self.request.headers
        if header_ip:
            print "/root/%s" % join(self.application.site["dirname"], file_name)
            self.set_header('X-Accel-Redirect',"/root/%s" % join(self.application.site["dirname"], file_name))
        else:
            self.write(abspath,stat_result)
            
    def write(self,abspath,stat_result):
        self.set_header("Content-Length", stat_result[stat.ST_SIZE])
        file = open(abspath, "rb")
        try:
            self.write(file.read())
        finally:
            file.close()


        
class CssHandler(tornado.web.RequestHandler):

    def getSource(self, file_name):
        from fs.dependency import changed_since, newer_group

        src = join(structure.CSS_DIR,file_name)
        if not isdir(src):
            raise tornado.web.HTTPError(404)
        target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
        text = None
        srcs = []
        srcs = fs.listdir(structure.CSS_DIR,recursed=True,full_path=True)
        #TODO record dependency with target
        if newer_group(srcs,target) or self.request.headers.get("force",False):
            lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
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
            
class StaticFallbackHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('X-Accel-Redirect',"/static_fallback"+self.request.path)
        # self.set_header("Content-Type","text/javascript")

# @cache_control(False)
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
        self.set_header('X-Accel-Redirect',"/target/js/"+file_name)
        
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
            self.render("verify/index.html", 
                title="Specs for %s - %s" % (file_name,test_path), 
                reload_url='../verify/',
                source = source, specs = specs)
        except Exception,e:
            print e
            
    def post(self, file_name, test_path):
        try:
            print 'posted results: ', file_name
            self.write('results noted.')
        except Exception,e:
            print e
        
class JsVerifyDetailHandler(JsHandler):
        
    def get(self, directory, file_name, test_path):
        try:
            print 'browser id =', 'new'
            print 'useragent', self.request.headers.get("User-Agent")
            print 'page url =', self.request.headers.get("Referer","??")
            print 'pipeline =', 'na'
            print 'page stage', 'loaded vs poll no vs other'
            path = join(directory,'verify')
            verify = VerifySource.get(path,file_name[:-3])
            if not verify.source:
                raise tornado.web.HTTPError(404)
            
            self.write(verify.render(xsrf_token = self.xsrf_token, arguments = self.request.arguments))
            VerifySource.discard(path,file_name[:-3]) #TODO configure in application settings, drop-js-cache
        except Exception,e:
            print e
            import traceback; traceback.print_exc()
            
    def split_part(self,key,val):
        import urllib, cgi
        r = { "name":key, "result": cgi.escape(urllib.unquote(val)) }
        sub_keys = key.split("__")
        if len(sub_keys) == 3:
            r["spec"] = sub_keys[0].replace("_"," ")
            r["example"] = sub_keys[1].replace("_"," ")
            r["subject"] = sub_keys[2] # index
        else:
            r["spec"] = key
            r["example"] = ""
            r["subject"] = "nil"
            
        return r
            
    def post(self, directory, file_name, test_path):
        try:
            results = VerifySource.posted_results(self.request.arguments)
            # print 'posted results: ', directory, file_name, results
            info = {
                "SITE_TITLE": "pagespec.com",
                "MEDIA_URL": "",
                "messages": None,
                "reload_url": "../verify/",
                "title": "Results for %s %s" % (directory,file_name),
                "parts": [self.split_part(key,val) for key,val in results]
            }
            self.render("verify/results.html",**info)
        except Exception,e:
            print e
            import traceback; traceback.print_exc()

        
class JsVerifyAllHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.render("verify/all.html")
        
class VerifyAssetsHandler(tornado.web.StaticFileHandler):
    
    def get(self,base,asset):
        path = "%s/verify/assets/%s" % (base,asset)
        tornado.web.StaticFileHandler.get(self,path)
        
        
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


