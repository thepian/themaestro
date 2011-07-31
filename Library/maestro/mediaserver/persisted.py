from __future__ import with_statement
from os.path import join, exists
from fs import listdir, filters
import hashlib
from ecmatic.es import translate, load_and_translate, load_and_add_scope  

import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

REDIS = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

# c = brukva.Client(REDIS_HOST, REDIS_PORT)
# c.connect()
# c.select(9)

def load_seed():
    from thepian.conf import structure
    
    base = join(structure.PROJECT_DIR,"seed")
    if exists(base):
        for a in listdir(base):
            account = join(base,a)

            for p in listdir(account):
                project = join(account,p)
            
                if REDIS.exists('%s/%s/all.list' % (a,p)):
                    # print REDIS.type('%s/%s/all.list' % (a,p))
                    REDIS.ltrim('%s/%s/all.list' % (a,p), 0, 0)

                for s in listdir(project, filters=(filters.fnmatch("*.pagespec.js"),)):
                    src,translated = load_and_translate(join(project,s))
                    h = hashlib.sha256(src).hexdigest()
                    id = "%s/%s/%s.js" % (a,p,h)
                    # print "adding", id, ":", t
                    REDIS.set(id,translated)
            
                    # added the hash to the all list
                    REDIS.rpush('%s/%s/all.list' % (a,p), h)
           
    print "Done loading seed." 
    
def load_scopes():
    from thepian.conf import structure

    base = join(structure.JS_DIR)
    for s in listdir(base,filters=(filters.fnmatch("*.scope.js"),)):
        load_and_add_scope('"%s"' % s[:-9],join(base,s))
    
REDIS.flushdb()
load_seed()
load_scopes()

