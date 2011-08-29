from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings
from mediaserver.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web
import tornado.template

from base import ObjectLike
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

class AccountOverviewHandler(tornado.web.RequestHandler):
    def get(self,account):
    	projects = describe_projects(account)
    	info = {
    		"account": account,
    		"projects":[ObjectLike(p) for p in projects],
            
            "full_name": "Henrik Vendelbo",
            "public_email": "hvendelbo.dev@googlemail.com",
            "public_website": "http://www.thepian.org/perspective/",
            "company_name": "Thepian Ltd",
            "public_location": "UK",
            "member_since": "Apr 10, 2009",
            "public_projects": "28",
            "private_projects": "9",
            "followers": "4",
			
    	}
        self.render("pagespec/account-overview.html",**info)


