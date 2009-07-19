"""
Wrapper for loading templates from "css" and "js" directories in their built forms.
"""

from os.path import isdir

from django.conf import settings
from django.template import TemplateDoesNotExist
from fs.path import safe_join

from thepian.conf import structure

from themaestro.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources 

def load_template_source(template_name, template_dirs=None):
    
    tried = []

    # css sources
    if template_name.startswith("css/"):
        src = safe_join(structure.CSS_DIR,template_name[4:])
        target = safe_join(structure.MEDIASITE_DIRS[-1],"css",template_name[4:])
        if isdir(src):
            if newer_assets(src,target):
                lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)	
                with open(target,"w") as f:
                    f.write(''.join(lines))
            try:
                return (open(target).read().decode(settings.FILE_CHARSET), target)
            except IOError:
                tried.append(target)
    
    # js sources
    if template_name.startswith("js/"):
        src = safe_join(structure.JS_DIR,template_name[3:])
        target = safe_join(structure.MEDIASITE_DIRS[-1],"js",template_name[3:])
        if isdir(src):
            if newer_assets(src,target):
                lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)	
                with open(target,"w") as f:
                    f.write(''.join(lines))
            try:
                return (open(target).read().decode(settings.FILE_CHARSET), target)
            except IOError:
                tried.append(target)
    
    if tried:
        error_msg = "Tried %s" % tried
    else:
        error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
    raise TemplateDoesNotExist, error_msg
load_template_source.is_usable = True