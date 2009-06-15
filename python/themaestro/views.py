from __future__ import with_statement
from fs import walk,listdir

from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control

from thepian.conf import structure
from thepian.assets import *
from themaestro.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources 

@cache_control(no_cache=True)
def generate_css(request, file_name):
	from os.path import join,isdir
	
	src = join(structure.CSS_DIR,file_name)
	if not isdir(src):
		raise Http404
	target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
	if newer_assets(src,target):
	    lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)	
	    with open(target,"w") as f:
	        f.write(''.join(lines))

	response = HttpResponse('',mimetype="text/css")
	response['X-Accel-Redirect'] = "/targetmedia/css/"+file_name
	return response
	
@cache_control(no_cache=True)
def generate_js(request, file_name):
	from os.path import join,isdir
	from distutils.dep_util import newer_group
	
	src = join(structure.JS_DIR,file_name)
	if not isdir(src):
		raise Http404
	target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
	if newer_assets(src,target):
	    lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)	
	    with open(target,"w") as f:
	        f.write(''.join(lines))

	response = HttpResponse('',mimetype="text/javascript")
	response['X-Accel-Redirect'] = "/targetmedia/js/"+file_name
	return response
	
def static_fallback(request):
    response = HttpResponse('',mimetype="text/plain")
    r = response['X-Accel-Redirect'] = "/static_fallback"+request.path
    print r
    return response