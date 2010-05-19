"""
Facilities to build css and JavaScript source from multiple files
"""
from __future__ import with_statement
import fs
from fs.filters import fnmatch, only_directories
from os.path import join,isdir,exists
import fileinput, re
from fs.dependency import newer_group

from thepian.conf import structure

from base import SourceNode
from css import CssSourceNode
from js import JsSourceNode

    
def newer_assets(src,target,source_node=SourceNode):
    """
    Are files needed to produce target path, found in the directory src path, newer in src path
    than target path."""
    sources = source_node.list_dependencies(src)
    return newer_group(sources,target)

def ensure_includes(includes,source_map,basedir,source_node=SourceNode):
    for include in includes:
        if include not in source_map:
            s = source_map[include] = source_node(include,basedir)
            ensure_includes(s.includes,source_map,basedir)

def order_sources(source,source_map,result):
    for include in source.includes:
        order_sources(source_map[include],source_map,result)
    if not source.used:
        result.append(source)
        source.used = True

def expand_inline_asset_sources(inline,basedir,source_node=SourceNode, attributes={}, prepend_lines=[], append_lines=[], default_scope=None):
    """
    Expand a source string
    """
    m = {}
    source = source_node('',basedir,source=inline,attributes=attributes)
    m[''] = source
    ensure_includes(source.includes,m,basedir,source_node=source_node)

    ordered_sources = []
    order_sources(source,m,ordered_sources)
    for path in m:
        source = m[path]
        if not source.used:
            print 'additional source', path
            ordered_sources.append(source)
            source.used = True

    lines = []
    for s in ordered_sources:
        lines.append(u"/* %s */\n" % s.path[len(basedir)+1:]) #TODO asset type dependent comment
        lines.extend(s.decorated_lines(default_scope=default_scope))
        lines.append(u"\n")
        
    if len(prepend_lines) > 0:
        lines[0:0] = prepend_lines
    if len(append_lines) > 0:
        lines.extend(append_lines)
    #TODO apply default scope
    # source_node.decorate_lines(lines,ordered_sources,basedir=basedir,default_scope=default_scope)
    source.prepend_stashes(lines)
    for s in ordered_sources:
        s.prepend_stashes(lines)
    return lines
    
    
    
def combine_asset_sources(src,basedir,source_node=SourceNode, prepend_lines=[], append_lines=[], default_scope=None):
    """
    A loose dependency detection, that ignores whitespace and extra signs
    
    @requires .."path/included.css"..
    
    including external files vs ordering internal files
    """
    sources = source_node.list_sources(src)
    m = {}    	        
    bases = []
    for path in sources:
        source = source_node(path,basedir)
        m[source.path] = source
        bases.append(source)
        
    for path in m.keys():
        source = m[path]
        ensure_includes(source.includes,m,basedir,source_node=source_node)

    ordered_sources = []
    for source in bases:
        order_sources(source,m,ordered_sources)
    for path in m:
        source = m[path]
        if not source.used:
            print 'additional source', path
            ordered_sources.append(source)
            source.used = True
    
    lines = []
    for s in ordered_sources:
        lines.append(u"/* %s */\n" % s.path[len(basedir)+1:]) #TODO asset type dependent comment
        lines.extend(s.lines)
        lines.append(u"\n")
        
    if len(prepend_lines) > 0:
        lines[0:0] = prepend_lines
    if len(append_lines) > 0:
        lines.extend(append_lines)
    #TODO apply default scope
    source_node.decorate_lines(lines,ordered_sources,basedir=basedir,default_scope=default_scope)
    for s in ordered_sources:
        s.prepend_stashes(lines)
    return lines

def source_paths():
    """Iterate url paths for css and js sources"""
    for name in fs.listdir(structure.CSS_DIR, filters=(only_directories,fnmatch("*.css"))):
        yield join("css",name)
    for name in fs.listdir(strucure.JS_DIR, filters=(only_directories,fnmatch("*.js"))):
        yield join("js",name)
        
def source_exists(path):
    if path.startswith("css/") and isdir(structure.CSS_DIR,path[4:]):
        return True
    if path.startswith("js/") and isdir(structure.JS_DIR,path[3:]):
        return True
    return False
     
    