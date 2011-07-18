from __future__ import with_statement
import brukva
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import redis

from ecmatic.es import translate, add_scope  

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

REDIS = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

# c = brukva.Client(REDIS_HOST, REDIS_PORT)
# c.connect()
# c.select(9)

REDIS.set('account/hash.js', 'aaaaaaa')
# c.set('foo2', 'bar2')

# print c.get('%s/%s.js' % ("account","hash"))

def load_seed():
    from thepian.conf import structure
    from os.path import join
    from fs import listdir, filters
    import hashlib
    
    base = join(structure.PROJECT_DIR,"seed")
    for a in listdir(base):
        account = join(base,a)

        for p in listdir(account):
            project = join(account,p)
            
            if REDIS.exists('%s/%s/all.list' % (a,p)):
                print REDIS.type('%s/%s/all.list' % (a,p))
                REDIS.ltrim('%s/%s/all.list' % (a,p), 0, 0)

            for s in listdir(project, filters=(filters.fnmatch("*.pagespec.js"),)):
                with open(join(project,s),"r") as f:
                    c = f.read()
                    h = hashlib.sha256(c).hexdigest()
                    t = translate(c)
                    id = "%s/%s/%s.js" % (a,p,h)
                    # print "adding", id, ":", t
                    REDIS.set(id,t)
                
                    # added the hash to the all list
                    REDIS.rpush('%s/%s/all.list' % (a,p), h)

           
    print "Done loading seed." 
    
REDIS.flushdb()
load_seed()

class JsPreProcessHandler(tornado.web.RequestHandler):
    
    # @tornado.web.asynchronous
    # @brukva.adisp.process
    def get(self, account, project, hash):
        key = '%s/%s/%s.js' % (account,project,hash)
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
    
    def __init__(self, application, request, transforms=None, core_api=None):
        super(JsExecuteAllHandler,self).__init__(application, request, transforms)
        self.core_api = core_api

    def get(self, account, project, exec_name):
        key = '%s/%s/all.list' % (account,project)
        if not key in REDIS:
            raise tornado.web.HTTPError(404)
            # self.finish()
        else:
            try:
                core_api = ""
                with open(self.core_api,"r") as f:
                    core_api = translate(f.read())
                ids = REDIS.lrange(key,0,1000)
                all_list = [{"id" : i,"run": REDIS['%s/%s/%s.js' % (account,project,i)]} for i in ids]
                self.set_header('Content-Type', 'text/javascript')
                self.render("execute-all.js", account=account, exec_name = exec_name, all_list = all_list, core_api = core_api)
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
