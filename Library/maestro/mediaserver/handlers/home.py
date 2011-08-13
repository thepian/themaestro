from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings
from mediaserver.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from mediaserver.verify import VerifySource
from mediaserver.persisted import *

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


class SelfTestHandler(tornado.web.RequestHandler):
    def get(self,account,project,exec_name):
        self.render("pagespec/selftest.html")

class KnownSpecsHandler(tornado.web.RequestHandler):
    def get(self,account,project,exec_name):
        specs = describe_specs(account,project)
        self.render("pagespec/known-spec.html",
            specs=specs)

class IntroductionHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id):
        account = "essentialjs"
        self.render("pagespec/introduction.html", 
            project=project,
            account=account,
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id)
