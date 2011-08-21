from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings

import tornado.web
import tornado.template

from mediaserver.persisted import *

class IntroductionHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id):
    	info = describe_suite(project,suite_or_pipeline_id)
    	if not info:
            raise tornado.web.HTTPError(404)
        self.render("pagespec/introduction.html", 
            project=project,
            account=info["account"],
            suite=info["suite"],
            exec_name=info["exec_name"],
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id)

class SpecIndexHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id):
    	info = describe_suite(project,suite_or_pipeline_id)
    	if not info:
            raise tornado.web.HTTPError(404)
        self.render("pagespec/spec-index.html", 
            project=project,
            account=info["account"],
            suite=info["suite"],
            exec_name=info["exec_name"],
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id)

class SpecZipHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id):
        import zipfile
        import StringIO
        
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)
        
        index = self.render_string("pagespec/spec-index.html", 
            project=project,
            account=info["account"],
            suite=info["suite"],
            exec_name=info["exec_name"],
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id
            )
            
        in_memory_zip = StringIO.StringIO()
        zf = zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED, False)
        zf.writestr('index.html', index)
        zf.writestr('test.spec.js','@describe "Object" { it "" { /* my example here */}}')
        for zfile in zf.filelist:
            zfile.create_system = 0
        zf.close() 
                
        self.set_header("Content-Type","application/octet-stream")
        self.write(in_memory_zip.getvalue())
        self.flush()
           
class SpecUploadHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id):
        account = "essentialjs"
        self.render("pagespec/introduction.html", 
            project=project,
            account=account,
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id)
