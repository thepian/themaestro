from __future__ import with_statement
from os.path import join, exists
from fs import listdir, filters
import hashlib
import simplejson as json
import time

from ecmatic.es import translate, load_and_translate, load_expand_and_translate, load_and_add_scope, extract_examples  

import redis

UNIT_SEP = "\x1F"
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Key structure in Redis
PROJECTS_KEY = '%s/project.set'.replace("/",UNIT_SEP)
ALL_SPECS_KEY = '%s/%s/all.set'.replace("/",UNIT_SEP) # collection of spec hashes, TODO change to set
DISABLED_SPECS_KEY = '%s/%s/disabled.set'.replace("/",UNIT_SEP)
MUSTFAIL_SPECS_KEY = '%s/%s/mustfail.set'.replace("/",UNIT_SEP)
SHORTCUT_UPLOADS_KEY = 'shortcut/%s/%s/uploads'.replace("/",UNIT_SEP)
SHORTCUT_SUITES_KEY = 'shortcut/%s/%s/suites'.replace("/",UNIT_SEP)

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

UPLOAD_PATH_KEY = 'shortcut/%s/%s/upload'.replace("/",UNIT_SEP) # json dict describing parameters
UPLOAD_SCRIPT_KEY = 'shortcut/%s/%s/upload.js'.replace("/",UNIT_SEP)
UPLOAD_SCRIPT_HASH_COMBINE = '%s/%s/7mkl37623iwuerqw'

SUITE_KEY = 'shortcut/%s/%s/suite'.replace("/",UNIT_SEP) # json dict describing parameters
SUITE_HASH_COMBINE = '%s/%s/%s/%s/knj897opifgy56'

# Redis connection
REDIS = redis.Redis(REDIS_HOST, REDIS_PORT, db=9)

# REDIS = brukva.Client(REDIS_HOST, REDIS_PORT)
# REDIS.connect()
# REDIS.select(9)

ONE_YEAR_IN_SECONDS = 365 * 24 * 3600
IN_A_YEAR_STAMP = time.time() + ONE_YEAR_IN_SECONDS

def load_seed():
    from thepian.conf import structure
    
    base = join(structure.PROJECT_DIR,"seed")
    if exists(base):
        for a in listdir(base):
            account = join(base,a)
            
            for p in listdir(account):
                project = join(account,p)
                
                REDIS.sadd(PROJECTS_KEY % a, p)

                upload_info = {
                    "account": a,
                    "project": p,
                    "expires": ONE_YEAR_IN_SECONDS,
                }
                upload_hash = hashlib.sha256( UPLOAD_SCRIPT_HASH_COMBINE % (a,p) ).hexdigest()
                REDIS[UPLOAD_PATH_KEY % (p,upload_hash)] = json.dumps(upload_info)
                REDIS[UPLOAD_SCRIPT_KEY % (p,upload_hash)] = load_expand_and_translate(join(structure.JS_DIR,'upload-specs.js'),**upload_info)[2]
                REDIS.sadd(SHORTCUT_UPLOADS_KEY % (a,p), upload_hash)
                print 'Upload URL /%s/%s/upload-specs.js' % (p,upload_hash)
                
                suite_info = {
                    "account": a,
                    "project": p,
                    "suite": "all",
                    "exec_name": "selftest",
                }
                suite_src = SUITE_HASH_COMBINE % (a,p,'all','selftest')
                suite_hash = hashlib.sha256(suite_src).hexdigest()
                suite_id = SUITE_KEY % (p,suite_hash)
                REDIS.set(suite_id , json.dumps(suite_info))
                REDIS.sadd(SHORTCUT_SUITES_KEY % (a,p), suite_hash)
                print 'Project %s URL /%s/%s/introduction.html' % (p,p,suite_hash) 
            
                for s in listdir(project, filters=(filters.fnmatch("*.spec.js"),)):
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
    scopes = [s for s in listdir(base,filters=(filters.fnmatch("*.scope.js"),))]
    for s in scopes:
        load_and_add_scope('"%s"' % s[:-9],join(base,s))
    print "Done loading scopes (", " ".join(scopes),")"
    
# REDIS.flushdb()
load_scopes()
load_seed()

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

    # unfinished results for examples indexed by spec id and then by redis key
    examples = {}

    def flush_unfinished(examples):
        for key in examples.keys():
            example = examples[key]
            REDIS.set(key , json.dumps(example))

    for r in results:
        spec_id = r["spec"]
        if r["outcome"] == "ended" and r["example"] == "":
            # Spec completed, move out of ongoing
            if r["spec"] in examples:
                flush_unfinished(examples[ spec_id ])
                examples[ spec_id ] = {}
            log_ongoing_spec(account,project,spec_id)
            move_to_completed(account,project,spec_id,run)

        elif r["example"] != "":
            ongoing_key = ONGOING_RUNS_KEY % (account,project,spec_id)
            # print "adding ongoing", r["outcome"], "---", ongoing_key, "Run", run
            REDIS.sadd(ongoing_key,run)
            example_names_id = ONGOING_EXAMPLE_NAMES_KEY % (account,project,spec_id,run)
            REDIS.sadd(example_names_id,r["example"])
            # print "------- ongoing example:", example_names_id, r["example"]
            example_id = ONGOING_EXAMPLES_KEY % (account,project,spec_id,run,r["example"])
            if spec_id not in examples:
                examples[spec_id] = {}
            examples4spec = examples[spec_id]
            if example_id not in examples4spec:
                examples4spec[example_id] = []
            examples4spec[example_id].append( r )

    for k in examples:
        flush_unfinished(examples[k])
        examples[k] = {}

def log_ongoing_spec(account, project, spec):
    print "------------"
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
        # print "moving to completed --- ", REDIS.type(example_names_id), example_names_id.replace(UNIT_SEP,"/")
        for example_name in REDIS.smembers(example_names_id):
            example_id = ONGOING_EXAMPLES_KEY % (account,project,spec,run,example_name)
            example_results = json.loads(REDIS[example_id])
            #TODO extract stamps, append results/ongoing and completed
            examples[example_name] = example_results

    completed_runs_key = COMPLETED_RUNS_KEY % (account,project,spec)
    REDIS.sadd(completed_runs_key,run)
    completed_key = COMPLETED_RUN_KEY % (account,project,spec,run)
    REDIS[completed_key] = json.dumps(examples)
    # print "completed:::", completed_key, examples

    # remove the keys for ongoing
    if example_names_id in REDIS:
        for example_name in REDIS.smembers(example_names_id):
            example_id = ONGOING_EXAMPLES_KEY % (account,project,spec,run,example_name)
            del REDIS[example_id]

    ongoing_key = ONGOING_RUNS_KEY % (account,project,spec)
    err = REDIS.srem(ongoing_key,run)
    # print "error(%s)"%err, REDIS.smembers(ongoing_key), "removed key", run, "from", ongoing_key
    REDIS.delete( ONGOING_RUN_KEY % (account,project,spec,run) )
    print "Moved to completed: ", spec, "*", run


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
        last_id = COMPLETED_RUN_KEY % (account,project,spec_id,completed_runs[-1])
        last_completed = json.loads(REDIS[ last_id ])

        specs.append({ "examples":examples, "info": info, "ongoing_runs": ongoing_runs, 
            "completed_runs":completed_runs,
            "last_completed": last_completed })

    return specs

def describe_suite(project,suite_hash):
	suite_id = SUITE_KEY % (project,suite_hash)
	if suite_id not in REDIS:
		return None

	data = json.loads(REDIS[suite_id])
	data["hash"] = suite_hash
	return data
	
def describe_upload(project,upload_hash):
	upload_path = UPLOAD_PATH_KEY % (project,upload_hash)
	upload_script = UPLOAD_SCRIPT_KEY % (project,upload_hash)
	if upload_path not in REDIS:
		return None, None
		
	data = json.loads(REDIS[upload_path])
	data["hash"] = upload_hash
	return data, REDIS[upload_script]

def describe_project(account,project):
    desc = {}
    suites_set_key = SHORTCUT_SUITES_KEY % (account,project)
    uploads_set_key = SHORTCUT_UPLOADS_KEY % (account,project)
    desc["account"] = account
    desc["project"] = project
    desc["suites"] = [describe_suite(project,suite) for suite in REDIS.smembers(suites_set_key)]
    desc["uploads"] = [describe_upload(project,upload)[0] for upload in REDIS.smembers(uploads_set_key)]
    desc["specs"] = REDIS.smembers(ALL_SPECS_KEY % (account,project))
    
    return desc

def describe_projects(account):
    projects = [describe_project(account,p) for p in REDIS.smembers(PROJECTS_KEY % account)]
    
    return projects
