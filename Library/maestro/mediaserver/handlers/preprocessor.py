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

r = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

# c = brukva.Client(REDIS_HOST, REDIS_PORT)
# c.connect()
# c.select(9)

r.set('account/hash.js', 'aaaaaaa')
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

        if r.exists('%s/all.list' % a):
            print r.type('%s/all.list' % a)
            r.ltrim('%s/all.list' % a, 0, 0)

        for s in listdir(account, filters=(filters.fnmatch("*.pagespec.js"),)):
            with open(join(account,s),"r") as f:
                c = f.read()
                h = hashlib.sha256(c).hexdigest()
                t = translate(c)
                id = "%s/%s.js" % (a,h)
                print "adding", id, ":", t
                r.set(id,t)
                
                # added the hash to the all list
                r.rpush('%s/all.list' % a, h)

           
    print r.type('%s/all.list' % a)
    print "Done loading seed." 
    
r.flushdb()
load_seed()

class JsPreProcessHandler(tornado.web.RequestHandler):
    
    # @tornado.web.asynchronous
    # @brukva.adisp.process
    def get(self, account, hash):
        key = '%s/%s.js' % (account,hash)
        if not key in r:
            print 'no entry for ', key
            raise tornado.web.HTTPError(404)
        else:
            try:
                self.set_header('Content-Type', 'text/javascript')
                self.write(r[key])
                self.finish()
            except Exception, e:
                print "preprocessor problem", e
                import traceback; traceback.print_exc()
        
class JsExecuteAllHandler(tornado.web.RequestHandler):
    
    def get(self, account, exec_name):
        key = '%s/all.list' % account
        if not key in r:
            raise tornado.web.HTTPError(404)
            # self.finish()
        else:
            try:
                ids = r.lrange(key,0,1000)
                all_list = [{"id" : i,"run": r['%s/%s.js' % (account,i)]} for i in ids]
                self.set_header('Content-Type', 'text/javascript')
                self.render("execute-all.js", account=account, exec_name = exec_name, all_list = all_list)
            
            except Exception, e:
                print "execute handler problem", e
                import traceback; traceback.print_exc()
