from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir
from fs import listdir,filters

from thepian.conf import structure, settings

import tornado.web
import tornado.template

from mediaserver.persisted import *

from base import *

class ProjectOverviewHandler(tornado.web.RequestHandler):
    def get(self,account,project):
    	project_data = describe_project(account,project)
    	specs = describe_specs(account,project)
    	info = {
    		"account": account,
    		"project": ObjectLike(project_data),
    		"specs": specs,
            
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
        self.render("pagespec/project-overview.html",**info)


class ExampleZipHandler(SpecRequestHandler):
    """
    API Site - Sample example.zip
    
    Sample introduction.html + spec/index.html + example.spec.js combined in a Zip.
    
    Related to Account/Project combo through an upload shortcut url.
    """
    def get(self,account,project,file_name_bit):
        import zipfile
        import StringIO
        
        info = describe_project(account,project)
        if not info:
            raise tornado.web.HTTPError(404)
        
        node_id = getNodeId(self,account, project)  # node cookie
        upload_id = info["uploads"][0]["hash"]
        spec_upload_url = "%s://%s/%s/%s/%s" % (self.request.protocol,self.request.host,project,upload_id,self.upload_script_name)

        js_base = join(structure.TEMPLATES_DIR,"pagespec","example","js")
        js_list = listdir(js_base,filters=(filters.no_hidden,filters.no_system,filters.no_directories))

        tdata = {
            "project": project,
            "account": account,
            "spec_upload_url": spec_upload_url,
        }
        introduction = self.render_string("pagespec/example/introduction.html", **tdata)
        index = self.render_string("pagespec/example/spec/index.html", **tdata)
        example_spec = self.render_string("pagespec/example/spec/example.spec.js")
            
        in_memory_zip = StringIO.StringIO()
        zf = zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED, False)
        zf.writestr('introduction.html', introduction)
        zf.writestr('spec/index.html', index)
        zf.writestr('spec/example.spec.js',example_spec)
        for suite in info["suites"]:
            tdata["suite_id"] = suite["hash"]
            tdata["pipeline_id"] = suite["hash"]
            tdata["suite"] = suite["suite"]
            tdata["exec_name"] = suite["exec_name"]
            suite_script_name = "%s-suite-%s" % (suite["suite"],suite["exec_name"])
            tdata["suite_script_url"] = "%s://%s/%s/%s/%s.js" % (self.request.protocol,self.request.host,project,suite["hash"],suite_script_name)
            runner = self.render_string("pagespec/example/suite-runner.html", **tdata)
            zf.writestr("%s-suite-runner.html" % str(suite["suite"]), runner)
	    for js_file in js_list:
	    	contents = self.render_string(join(js_base,js_file), **tdata)
	    	zf.writestr(join("js",js_file),contents)
        for zfile in zf.filelist:
            zfile.create_system = 0
        zf.close() 
                
        self.set_header("Content-Type","application/octet-stream")
        self.write(in_memory_zip.getvalue())
        self.flush()
           

# Related to a particular Suite
class IntroductionHandler(tornado.web.RequestHandler):
    def get(self,account,project):
        info = describe_project(account,project)
        if not info:
            raise tornado.web.HTTPError(404)
        self.render("pagespec/example/introduction.html", **info)


