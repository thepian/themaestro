from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings

import tornado.web
import tornado.template

from mediaserver.persisted import *

from base import *

class SuiteRunnerHandler(SpecRequestHandler):
    """
    API Site - Sample all-suite-runner.html
    
    Related to Account/Project combo through an upload shortcut url.
    """
    def get(self,project,suite_or_pipeline_id,suite_name):
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)

        node_id = getNodeId(self,info["account"], project)  # node cookie

        suite_script_name = "%s-suite-%s.js" % (info["suite"],info["exec_name"])
        suite_script_url = "%s://%s/%s/%s/%s" % (self.request.protocol,self.request.host,project,suite_or_pipeline_id,suite_script_name)
        
        self.render("pagespec/example/suite-runner.html",
            suite_script_url = suite_script_url, 
            project=project,
            account=info["account"],
            suite=info["suite"],
            exec_name=info["exec_name"],
            suite_id=suite_or_pipeline_id,
            pipeline_id=suite_or_pipeline_id,
            )

class SuiteRunnerScriptHandler(SpecRequestHandler):
    
    def get(self,project,suite_or_pipeline_id):
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)
        else:
            try:
                info["xsrf_input_markup"] = "'%s'" % self.xsrf_form_html().replace("'",'"')  # Session specific token passed to Script
                info["xsrf_token"] = self.xsrf_token
                info["script_name"] = "'%s'" % self.upload_script_name
                
                script = load_expand_and_translate(join(structure.JS_DIR,'suite-runner.js'),**info)[2]

                node_id = getNodeId(self,info["account"], project)  # node cookie

                #self.run_script, 
                
                self.set_header('Content-Type', 'text/javascript')
                self.write(script)
                self.finish()
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
                
    def get2(self, account, project, exec_name):
        key = ALL_SPECS_KEY % (account,project)
        if not key in REDIS:
            raise tornado.web.HTTPError(404)
            # self.finish()
        else:
            try:
                node_id = getNodeId(self,account, project)  # node cookie

                ids = REDIS.smembers(key)
                all_list = [(i,REDIS[TRANSLATED_SPEC_KEY % (account,project,i)]) for i in ids]
                bits = ['''{"id":"%s","describe":%s}''' % e for e in all_list]
                specs = ",".join(bits)
                xsrf_input_markup = "'%s'" % self.xsrf_form_html().replace("'",'"')  # Session specific token passed to Script

                src, run_script = load_and_translate(self.run_script, 
                    xsrf_input_markup = xsrf_input_markup, 
                    xsrf_token = self.xsrf_token,
                    exec_name = exec_name, account=account, project=project, 
                    script_name = '"%s.js"' % exec_name, 
                    specs = specs)
                
                print "Writing 'run_script' "
                self.set_header('Content-Type', 'text/javascript')
                self.write(run_script)
                self.finish()
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
                
