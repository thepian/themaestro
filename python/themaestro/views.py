from fs import walk,listdir

from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control

from thepian.conf import structure
from thepian.assets import *
from themaestro.sources import CssSourceNode,JsSourceNode, combine_asset_sources 

@cache_control(no_cache=True)
def generate_css(request, file_name):
	from os.path import join,isdir
	from distutils.dep_util import newer_group
	
	src = join(structure.CSS_DIR,file_name)
	if not isdir(src):
		raise Http404
	target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
	sources = listdir(src,full_path=True,recursed=True)
	if newer_group(sources,target):
		pass #print sources

	lines = combine_asset_sources(sources,structure.CSS_DIR,source_node=CssSourceNode)	
	response = HttpResponse(''.join(lines),mimetype="text/css")
	# response['X-Accel-Redirect'] = "/mediatarget/css/"+file_name
	return response
	
@cache_control(no_cache=True)
def generate_js(request, file_name):
	from os.path import join,isdir
	from distutils.dep_util import newer_group
	
	src = join(structure.JS_DIR,file_name)
	if not isdir(src):
		raise Http404
	target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
	sources = listdir(src,full_path=True,recursed=True)
	if newer_group(sources,target):
		pass #print sources

	lines = combine_asset_sources(sources,structure.JS_DIR,source_node=JsSourceNode)	
	response = HttpResponse(''.join(lines),mimetype="text/javascript")
	# response['X-Accel-Redirect'] = "/mediatarget/css/"+file_name
	return response
	
def static_fallback(request):
    response = HttpResponse('',mimetype="text/plain")
    r = response['X-Accel-Redirect'] = "/static_fallback"+request.path
    print r
    return response