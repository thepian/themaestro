from __future__ import with_statement
# import brukva
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop

from ecmatic.es import translate, load_and_translate, add_scope, load_and_add_scope  
from mediaserver.persisted import *

class JsPreProcessHandler(tornado.web.RequestHandler):
    
    # @tornado.web.asynchronous
    # @brukva.adisp.process
    def get(self, account, project, hash):
        key = TRANSLATED_SPEC_KEY % (account,project,hash)
        if not key in REDIS:
            print 'no entry for ', key
            raise tornado.web.HTTPError(404)
        else:
            try:
                self.set_header('Content-Type', 'text/javascript')
                self.write(REDIS[key])
                self.finish()
            except Exception, e:
                print "preprocessor problem", e
                import traceback; traceback.print_exc()
        
class JsExecuteAllHandler(tornado.web.RequestHandler):
    
    def __init__(self, application, request, core_api=None, run_script=None):
        super(JsExecuteAllHandler,self).__init__(application, request)
        self.core_api = core_api
        self.run_script = run_script

    def get(self, account, project, exec_name):
        key = ALL_SPECS_KEY % (account,project)
        if not key in REDIS:
            raise tornado.web.HTTPError(404)
            # self.finish()
        else:
            try:
                # node cookie
                node_id = self.get_cookie("%s__%s__node" % (account,project),default=None)
                if node_id == None:
                    import random, string
                    node_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(20))
                    print "new node id", node_id
                    self.set_cookie("%s__%s__node" % (account,project), node_id, expires_days=365)

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
