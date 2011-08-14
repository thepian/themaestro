from __future__ import with_statement
from os.path import join, exists
from fs import listdir, filters
import hashlib
import simplejson as json

from ecmatic.es import translate, load_and_translate, load_expand_and_translate, load_and_add_scope, extract_examples  

import redis

UNIT_SEP = "\x1F"
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Key structure in Redis
ALL_SPECS_KEY = '%s/%s/all.set'.replace("/",UNIT_SEP) # collection of spec hashes, TODO change to set
TRANSLATED_SPEC_KEY = '%s/%s/%s.js'.replace("/",UNIT_SEP)
SPECS_PREFIX = '%s/%s/specs'.replace("/",UNIT_SEP)
SPEC_INFO_KEY = '%s/%s/specs/%s/info'.replace("/",UNIT_SEP)
EXAMPLE_NAMES_KEY = '%s/%s/specs/%s/examples'.replace("/",UNIT_SEP)
ONGOING_RUNS_KEY = '%s/%s/specs/%s/ongoing'.replace("/",UNIT_SEP)
ONGOING_RUN_KEY = '%s/%s/specs/%s/ongoing/%s'.replace("/",UNIT_SEP)
ONGOING_EXAMPLE_NAMES_KEY = '%s/%s/specs/%s/ongoing/%s/examples'.replace("/",UNIT_SEP)
ONGOING_EXAMPLES_KEY = '%s/%s/specs/%s/ongoing/%s/examples/%s'.replace("/",UNIT_SEP)
COMPLETED_RUNS_KEY = '%s/%s/specs/%s/completed'.replace("/",UNIT_SEP)
COMPLETED_RUN_KEY = '%s/%s/specs/%s/completed/%s'.replace("/",UNIT_SEP)

# Redis connection
REDIS = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

# REDIS = brukva.Client(REDIS_HOST, REDIS_PORT)
# REDIS.connect()
# REDIS.select(9)

def load_seed():
    from thepian.conf import structure
    
    base = join(structure.PROJECT_DIR,"seed")
    if exists(base):
        for a in listdir(base):
            account = join(base,a)

            for p in listdir(account):
                project = join(account,p)
            
                for s in listdir(project, filters=(filters.fnmatch("*.pagespec.js"),)):
                    src,expanded,translated = load_expand_and_translate(join(project,s))
                    h = hashlib.sha256(src).hexdigest()
                    idx = 0
                    for spec in expanded:
                        spec_hash = h + "-" + str(idx)

                        translated = translate([ spec ])

                        id = TRANSLATED_SPEC_KEY % (a,p,spec_hash)
                        # print "adding", id, ":", t, "name", spec[2]
                        REDIS.set(id,translated)
                        info_id = SPEC_INFO_KEY % (a,p,spec_hash)
                        info = {"id":spec_hash,"name":spec[2],"filename":s}
                        REDIS.set(info_id , json.dumps(info))

                        examples_id = EXAMPLE_NAMES_KEY % (a,p,spec_hash)
                        examples = [e[1].replace('"','') for e in extract_examples(expanded)]
                        # print h, "seed examples", examples
                        # sadd is supposed to be callable by REDIS.sadd(examples_id,*examples)
                        for e in examples:
                            REDIS.sadd(examples_id, e)
                
                        # added the hash to the all list
                        REDIS.sadd(ALL_SPECS_KEY % (a,p), spec_hash)

                        ++idx

           
    print "Done loading seed." 
    
def load_scopes():
    from thepian.conf import structure

    base = join(structure.JS_DIR)
    for s in listdir(base,filters=(filters.fnmatch("*.scope.js"),)):
        load_and_add_scope('"%s"' % s[:-9],join(base,s))
    
# REDIS.flushdb()
load_seed()
load_scopes()

def persist_results(results, account=None, project=None, run=None):
    """
    results take the form of
    {
        outcome: ended, skipped, exception, failed
        spec: name of the spec context
        example: name of the example

    }

    when a result of context ended all ongoing results are moved to completed.
    """

    # unfinished results for examples indexed by redis key
    examples = {}

    def flush_unfinished(examples):
        for key in examples.keys():
            e = examples[key]
            REDIS.set(key , json.dumps(e))
        examples = {}

    for r in results:
        if r["outcome"] == "ended" and r["example"] == "":
            # Spec completed, move out of ongoing
            flush_unfinished(examples)
            log_ongoing_spec(account,project,r["spec"])
            move_to_completed(account,project,r["spec"],run)

        elif r["example"] != "":
            ongoing_key = ONGOING_RUNS_KEY % (account,project,r["spec"])
            REDIS.sadd(ongoing_key,run)
            example_names_id = ONGOING_EXAMPLE_NAMES_KEY % (account,project,r["spec"],run)
            REDIS.sadd(example_names_id,r["example"])
            print "ongoing example:", example_names_id
            example_id = ONGOING_EXAMPLES_KEY % (account,project,r["spec"],run,r["example"])
            if example_id not in examples:
                examples[example_id] = []
            examples[example_id].append( r )

    flush_unfinished(examples)

def log_ongoing_spec(account, project, spec):
    print "ongoing spec: ", account, project, spec
    ongoing_id = ONGOING_RUNS_KEY % (account,project,spec)
    runs = REDIS.smembers(ongoing_id)
    for run in runs:
        print "run %s:" % run
        examples_id = EXAMPLE_NAMES_KEY % (account,project,spec)
        for e in REDIS.smembers(examples_id):
            example_run_id = ONGOING_EXAMPLES_KEY % (account,project,spec,run,e)
            if example_run_id in REDIS:
                result = REDIS[example_run_id]
                print example_run_id, json.loads(result)
            else:
                print "no result for", e
    print "."

    # example = json.loads(e_text)

def move_to_completed(account, project, spec, run):
    examples = {}

    # make json of the examples and save that
    example_names_id = ONGOING_EXAMPLE_NAMES_KEY % (account,project,spec,run)
    if example_names_id in REDIS:
        for example_name in REDIS[example_names_id]:
            example_id = ONGOING_EXAMPLES_KEY % (account,project,spec,run,example_name)
            example_results = json.loads(REDIS[example_id])
            examples[example_name] = example_results

    completed_runs_key = COMPLETED_RUNS_KEY % (account,project,spec)
    REDIS.sadd(completed_runs_key,run)
    completed_key = COMPLETED_RUN_KEY % (account,project,spec,run)
    REDIS[completed_key] = json.dumps(examples)

    # remove the keys for ongoing
    if example_names_id in REDIS:
        for example_name in REDIS[example_names_id]:
            example_id = ONGOING_EXAMPLES_KEY % (account,project,spec,run,example_name)
            del REDIS[example_id]

    ongoing_key = ONGOING_RUNS_KEY % (account,project,spec)
    REDIS.srem(ongoing_key,run)


def describe_specs(account,project):
    specs = []
    ids = REDIS.smembers(ALL_SPECS_KEY % (account,project))
    for spec_id in ids:
        translated_source = REDIS[TRANSLATED_SPEC_KEY % (account,project,spec_id)]
        examples_id = EXAMPLE_NAMES_KEY % (account,project,spec_id)
        examples = []
        for e in REDIS.smembers(examples_id):
            example_text = e
            examples.append(example_text)
        info_id = SPEC_INFO_KEY % (account,project,spec_id)
        info = json.loads(REDIS.get(info_id))

        ongoing_runs_id = ONGOING_RUNS_KEY % (account,project,spec_id)
        ongoing_runs = [e for e in REDIS.smembers(ongoing_runs_id)]

        completed_runs_id = COMPLETED_RUNS_KEY % (account,project,spec_id)
        completed_runs = [e for e in REDIS.smembers(completed_runs_id)]


        specs.append({ "examples":examples, "info": info, "ongoing_runs": ongoing_runs, "completed_runs":completed_runs })

    return specs


