from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings

import tornado.web
import tornado.template

from mediaserver.persisted import *

from base import *

# Related to a particular Suite
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


class SpecIndexHandler(SpecRequestHandler):
    """
    API Site - Sample spec/index.html
    
    Related to Account/Project combo through an upload shortcut url.
    """
    def get(self,project,upload_id):
        info,script = describe_upload(project,upload_id)
        if not info:
            raise tornado.web.HTTPError(404)

        node_id = getNodeId(self,info["account"], project)  # node cookie

        spec_upload_url = "%s://%s/%s/%s/%s" % (self.request.protocol,self.request.host,project,upload_id,self.upload_script_name)
        
        self.render("pagespec/spec/index.html",
            spec_upload_url = spec_upload_url, 
            project=project,
            account=info["account"],
            upload_id=upload_id)

class SpecZipHandler(SpecRequestHandler):
    """
    API Site - Sample spec.zip
    
    Sample spec/index.html + example.spec.js combined in a Zip.
    
    Related to Account/Project combo through an upload shortcut url.
    """
    def get(self,project,upload_id):
        import zipfile
        import StringIO
        
        info,script = describe_upload(project,upload_id)
        if not info:
            raise tornado.web.HTTPError(404)
        
        node_id = getNodeId(self,info["account"], project)  # node cookie
        spec_upload_url = "%s://%s/%s/%s/%s" % (self.request.protocol,self.request.host,project,upload_id,self.upload_script_name)

        index = self.render_string("pagespec/spec/index.html", 
            spec_upload_url = spec_upload_url, 
            project=project,
            account=info["account"],
            upload_id=upload_id)
        example_spec = self.render_string("pagespec/spec/example.spec.js")
            
        in_memory_zip = StringIO.StringIO()
        zf = zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED, False)
        zf.writestr('index.html', index)
        zf.writestr('example.spec.js',example_spec)
        for zfile in zf.filelist:
            zfile.create_system = 0
        zf.close() 
                
        self.set_header("Content-Type","application/octet-stream")
        self.write(in_memory_zip.getvalue())
        self.flush()
           
class SpecUploadHandler(tornado.web.RequestHandler):

    def post(self,project,upload_id,path):
        info,script = describe_upload(project,upload_id)
        if not info:
            raise tornado.web.HTTPError(404)
        
        content_type = self.request.headers['Content-Type']
        if content_type == 'application/x-www-form-urlencoded':
        	script_text = self.get_argument("script")
        	script_language = self.get_argument("language")
        	print self.request.query, "language", script_language
        	print script_text
        else:
        	# TODO handle text/plain and text/pagespec for build scripts
        	print "No handling of spec script update", content_type
        
        self.write("Update received.")
        self.flush()


class SpecUploadScriptHandler(SpecRequestHandler):
    
    def get(self,project,upload_id):
        info,script = describe_upload(project,upload_id)
        if not info:
            raise tornado.web.HTTPError(404)
        else:
            try:
                info["xsrf_input_markup"] = "'%s'" % self.xsrf_form_html().replace("'",'"')  # Session specific token passed to Script
                info["xsrf_token"] = self.xsrf_token
                info["script_name"] = "'%s'" % self.upload_script_name
                
                script = load_expand_and_translate(join(structure.JS_DIR,'upload-specs.js'),**info)[2]

                node_id = getNodeId(self,info["account"], project)  # node cookie

                #self.run_script, 
                
                self.set_header('Content-Type', 'text/javascript')
                self.write(script)
                self.finish()
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
