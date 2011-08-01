from __future__ import with_statement
from os.path import join, exists
from fs import listdir, filters
import hashlib
import simplejson as json

from ecmatic.es import translate, load_and_translate, load_expand_and_translate, load_and_add_scope, extract_examples  

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
                    src,expanded,translated = load_expand_and_translate(join(project,s))
                    h = hashlib.sha256(src).hexdigest()
                    id = "%s/%s/%s.js" % (a,p,h)
                    # print "adding", id, ":", t
                    REDIS.set(id,translated)

                    examples_id = "%s/%s/%s/examples" % (a,p,h)
                    examples = [e[1].replace('"','') for e in extract_examples(expanded)]
                    # print h, "seed examples", examples
                    # sadd is supposed to be callable by REDIS.sadd(examples_id,*examples)
                    for e in examples:
                        REDIS.sadd(examples_id, e)
            
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

def persist_results(results, account=None, project=None, run=None):

    specs_prefix = "/%s/%s/specs" % (account,project)

    examples = {}

    for r in results:
        if r["outcome"] == "ended" and r["example"] == "":
            # Spec completed, move out of ongoing
            for key in examples.keys():
                e = examples[key]
                REDIS.set(key , json.dumps(e))
            examples = {}

            # TODO make json of the examples and save that
            # TODO remove the keys for ongoing
            log_ongoing_spec(account,project,r["spec"])

        elif r["example"] != "":
            ongoing_prefix = specs_prefix + ("/%s/ongoing" % r["spec"])
            REDIS.sadd(ongoing_prefix,run)
            example_id = ongoing_prefix + ("/%s/examples/%s" % (run,r["example"]))
            if example_id not in examples:
                examples[example_id] = []
            examples[example_id].append( r )

def log_ongoing_spec(account, project, spec):
    print "ongoing spec: ", account, project, spec
    ongoing_id = "/%s/%s/specs/%s/ongoing" % (account,project,spec)
    runs = REDIS.smembers(ongoing_id)
    for run in runs:
        print "run %s:" % run
        examples_id = "%s/%s/%s/examples" % (account,project,spec)
        for e in REDIS.smembers(examples_id):
            example_run_id = ongoing_id + ("/%s/examples/%s" % (run,e))
            if example_run_id in REDIS:
                result = REDIS[example_run_id]
                print example_run_id, json.loads(result)
            else:
                print "no result for", e
    print "."

    # example = json.loads(e_text)

