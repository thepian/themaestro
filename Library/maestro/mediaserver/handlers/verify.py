from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings
from mediaserver.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from mediaserver.verify import VerifySource

from old import JsHandler

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
            # print 'browser id =', 'new'
            # print 'useragent', self.request.headers.get("User-Agent")
            # print 'page url =', self.request.headers.get("Referer","??")
            # print 'pipeline =', 'na'
            # print 'page stage', 'loaded vs poll no vs other'
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
        
class PageSpecVerifyJsHandler(tornado.web.RequestHandler):
    
    def get(self,account,project):
        src,translated = load_and_translate(join(structure.JS_DIR,"pagespec-verify.js"))
        self.set_header('Content-Type', 'text/javascript')
        self.write(translated)
        self.finish()
