"""
Facilities to build css and JavaScript source from multiple files
"""
from __future__ import with_statement
import fs
from fs.filters import fnmatch, only_directories
from os.path import join,isdir
import fileinput, re
from distutils.dep_util import newer_group

from thepian.conf import structure

requires_statement = re.compile(r'@requires [^"]*"([^"]+)"')
include_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*\)\s*;')

class SourceNode(object):
    used = False
    def __init__(self,path,basedir):
        self.path = path
        self.basedir = basedir
        try:
            self._lines = [line for line in fileinput.FileInput(files=(self.path,))]
        except IOError:
            self._lines = []
            print "failed to load Asset Source: %s" % self.path
        includes = []
        for line in self._lines[:25]:
            m = requires_statement.search(line)
            if m:
                includes.extend(m.groups())
        self.includes = [join(basedir,i) for i in includes]
        
    def __repr__(self):
        return self.path
        
    @classmethod
    def list_dependencies(cls,src,full_path=True):
        """Naive implementation returning all files in the directory"""
        return fs.listdir(src,full_path=full_path,recursed=True)
        
def css_fetcher(url):
    print url
    read = u''
    with open(url[7:],"r") as f:
        read = f.read()
    return None, u"/* imported */" + unicode(read)
            
class CssSourceNode(SourceNode):
    
    @classmethod
    def list_sources(cls,src,full_path=True):
        return fs.listdir(src,full_path=True,recursed=False,filters=(fnmatch("*.css"),))
        
    def get_lines(self):
        import cssutils
        css = u''.join(self._lines)
        parser = cssutils.CSSParser(fetcher=css_fetcher)
        sheet = parser.parseString(css,href="file://"+self.path)
        cssutils.ser.prefs.useMinified()
        cssutils.ser.prefs.keepComments = False
        sheet = cssutils.resolveImports(sheet)
        return [u'%s\n' % rule.cssText for rule in sheet if rule.cssText and len(rule.cssText)>0]
    lines = property(get_lines)
       
class JsSourceNode(SourceNode):
    
    @classmethod
    def list_sources(cls,src,full_path=True):
        return fs.listdir(src,full_path=True,recursed=False,filters=(fnmatch("*.js"),))
        
    def get_lines(self):
        return [self.expand(l) for l in self._lines]
    lines = property(get_lines)
    
    def expand(self,line):
        m = include_statement.search(line)
        if m:
            include = '/* %s not found */' % m.group(1)
            try:
                full_path = join(self.basedir,m.group(1))
                with open(full_path,"r") as f:
                    include = f.read()
            except IOError:
                pass
            return line[:m.start(0)] + include + line[m.end(0):]
        return line

    
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

def combine_asset_sources(src,basedir,source_node=SourceNode):
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
     
    