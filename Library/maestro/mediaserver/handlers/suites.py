from __future__ import with_statement
import os, fs, os.path, logging
from os.path import join,isdir

from thepian.conf import structure, settings

import tornado.web
import tornado.template

from mediaserver.results import *
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
    
    def get(self,project,suite_or_pipeline_id,suite_name,exec_name):
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)
        account = info["account"]
        specs_key = ALL_SPECS_KEY % (account,project)
        if not info or specs_key not in REDIS:
            raise tornado.web.HTTPError(404)
        else:
            try:
                ids = REDIS.smembers(specs_key)
                all_list = [(i,REDIS[TRANSLATED_SPEC_KEY % (account,project,i)]) for i in ids]
                # print "~~~~~", all_list
                bits = ['''{"id":"%s","describe":%s}''' % e for e in all_list]
                specs = ",".join(bits)
                info["specs"] = specs

                info["xsrf_input_markup"] = "'%s'" % self.xsrf_form_html().replace("'",'"')  # Session specific token passed to Script
                info["xsrf_token"] = self.xsrf_token
                info["script_name"] = "'%s.js'" % info["exec_name"]
                
                script = load_expand_and_translate(join(structure.JS_DIR,'suite-runner.js'),**info)[2]

                node_id = getNodeId(self,info["account"], project)  # node cookie

                self.set_header('Content-Type', 'text/javascript')
                self.write(script)
                self.finish()
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
                
class SpecificRunHandler(tornado.web.RequestHandler):
    def get(self,project,suite_or_pipeline_id,run):
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)
        info["run"] = run
        info["SITE_TITLE"] = "pagespec.com"
        info["MEDIA_URL"] = ""
        info["messages"] = None
        info["reload_url"] = "."
        info["title"] = "Results for %s %s : %s" % (account,project,run)
        info["parts"] = []
        self.render("pagespec/results.html", **info)
        

    def post(self,project,suite_or_pipeline_id,run):
        info = describe_suite(project,suite_or_pipeline_id)
        if not info:
            raise tornado.web.HTTPError(404)
        # directory, file_name, test_path
        try:
            account = info["account"]
            node_id = self.get_cookie("%s__%s__node" % (account,project),default=None)
            # print "Processing results for run %s on node %s" % (run,node_id)
            results = posted_results(self.request.arguments)
            # print 'posted results: ', account,project,run, results
            persist_results(results, account=account, project=project, run=run)
            info["run"] = run
            info["SITE_TITLE"] = "pagespec.com"
            info["MEDIA_URL"] = ""
            info["reload_url"] = "."
            info["title"] = "Results for %s %s : %s" % (account,project,run)
            info["no_results"] = len(results)
            self.render("pagespec/progress-response.html",**info)
        except Exception,e:
            print e
            import traceback; traceback.print_exc()


