from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings
from mediaserver.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from mediaserver.verify import VerifySource

class MediaHomeHandler(tornado.web.RequestHandler):
    
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
            "MEDIA_URL": settings.MEDIA_URL
        }
        self.render("directory.html",**info)
                
class StaticFallbackHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('X-Accel-Redirect',"/static_fallback"+self.request.path)
        # self.set_header("Content-Type","text/javascript")


class NodesHandler(tornado.web.RequestHandler):
    def get(self,account,project,node):
        info = {
            "account": account,
            "project": project,
            "node": node,
            
            "SITE_TITLE": "pagespec.com",
            "MEDIA_URL": "",
            "messages": None,
            "reload_url": ".",

            "title": "Results for %s %s : %s" % (account,project,node),
            
            "parts": []
        }
        self.render("pagespec/results.html", **info)
        
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

    def post(self,account,project,node):
        # directory, file_name, test_path
        try:
            results = VerifySource.posted_results(self.request.arguments)
            # print 'posted results: ', directory, file_name, results
            info = {
                "account": account,
                "project": project,

                "SITE_TITLE": "pagespec.com",
                "MEDIA_URL": "",
                "messages": None,
                "reload_url": "../verify/",
                "title": "Results for %s %s" % (directory,file_name),
                "parts": [self.split_part(key,val) for key,val in results]
            }
            self.render("pagespec/results.html",**info)
        except Exception,e:
            print e
            import traceback; traceback.print_exc()


class SpecificRunHandler(tornado.web.RequestHandler):
    def get(self,account,project,run):
        info = {
            "account": account,
            "project": project,
            "run": run,
            
            "SITE_TITLE": "pagespec.com",
            "MEDIA_URL": "",
            "messages": None,
            "reload_url": ".",

            "title": "Results for %s %s : %s" % (account,project,run),
            
            "parts": []
        }
        self.render("pagespec/results.html", **info)
        
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

    def post(self,account,project,run):
        # directory, file_name, test_path
        try:
            results = VerifySource.posted_results(self.request.arguments)
            # print 'posted results: ', directory, file_name, results
            info = {
                "account": account,
                "project": project,
                "run": run,

                "SITE_TITLE": "pagespec.com",
                "MEDIA_URL": "",
                "messages": None,
                "reload_url": "../verify/",
                "title": "Results for %s %s : %s" % (account,project,run),
                "parts": [self.split_part(key,val) for key,val in results]
            }
            self.render("pagespec/results.html",**info)
        except Exception,e:
            print e
            import traceback; traceback.print_exc()


class SelfTestHandler(tornado.web.RequestHandler):
    def get(self,account,project,exec_name):
        self.render("pagespec/selftest.html")
