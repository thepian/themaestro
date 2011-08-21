from __future__ import with_statement
# import brukva
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop

from ecmatic.es import translate, load_and_translate, add_scope, load_and_add_scope  
from mediaserver.persisted import *

from base import *        

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
        
class JsExecuteAllHandler(SpecRequestHandler):
    
    def get(self, account, project, exec_name):
        key = ALL_SPECS_KEY % (account,project)
        if not key in REDIS:
            raise tornado.web.HTTPError(404)
            # self.finish()
        else:
            try:
                node_id = self.getNodeId(account, project)  # node cookie

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
