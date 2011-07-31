"""
Handling results posted by the nodes
"""
from __future__ import with_statement
import urllib, cgi
import os, re

import simplejson

def posted_results(arguments):
    """Pull results from POST into a list of dicts"""

    def split_part(key,val):
        r = { "name":key, "result": cgi.escape(urllib.unquote(val)) }
        sub_keys = key.split("__")
        if len(sub_keys) == 4:
            r["spec"] = sub_keys[0].replace("_"," ")
            r["example"] = sub_keys[1].replace("_"," ")
            r["expectation"] = sub_keys[2] # index
            r["outcome"] = sub_keys[3]
        elif len(sub_keys) == 3:
            r["spec"] = sub_keys[0].replace("_"," ")
            r["example"] = sub_keys[1].replace("_"," ")
            r["outcome"] = sub_keys[2] 
        else:
            r["spec"] = sub_keys[0].replace("_"," ")
            r["example"] = ""
            r["outcome"] = sub_keys[-1] 

        return r

    results = []
    for key in arguments.keys():
        parts = key.split("_")
        # leading _ skipped along with fields of only spec id
        if len(parts) > 1 and len(parts[0]) > 0:
            results.append(split_part(key,arguments[key][0]))
        elif key.endswith("-result"):
            results.append(split_part(key[:-7],arguments[key][0]))
    return results
    
