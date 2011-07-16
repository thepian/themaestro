import brukva
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

r = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

c = brukva.Client(REDIS_HOST, REDIS_PORT)
c.connect()
c.select(9)

c.set('account/hash.js', 'aaaaaaa')
c.set('foo2', 'bar2')

# print c.get('%s/%s.js' % ("account","hash"))

class JsPreProcessHandler(tornado.web.RequestHandler):
    
    @tornado.web.asynchronous
    @brukva.adisp.process
    def get(self, account, hash):
        try:
            tx = yield c.async.get('%s/%s.js' % (account,hash))
            
            self.set_header('Content-Type', 'text/javascript')
            self.write(tx)
            self.finish()
            return 
        except Exception, e:
            print e
            import traceback; traceback.print_exc()
        
