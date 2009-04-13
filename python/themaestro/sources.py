"""
Facilities to build css and JavaScript source from multiple files
"""

from os.path import join,isdir
import fileinput, re
include_statement = re.compile('@requires [^"]*"([^"]*)"')

class SourceNode(object):
    used = False
    def __init__(self,path,basedir):
        self.path = path
        try:
            self._lines = [line for line in fileinput.FileInput(files=(self.path,))]
        except IOError:
            self._lines = []
            print "failed to load Asset Source: %s" % self.path
        includes = []
        for line in self._lines[:25]:
            m = include_statement.search(line)
            if m:
                includes.extend(m.groups())
        self.includes = [join(basedir,i) for i in includes]
        
    def __repr__(self):
        return self.path
        
    def get_lines(self):
        return self._lines
    lines = property(get_lines)
        
class CssSourceNode(SourceNode):
    def get_lines(self):
        import cssutils
        css = u''.join(self._lines)
        sheet = cssutils.parseString(css)
        cssutils.ser.prefs.useMinified()
        cssutils.ser.prefs.keepComments = False
        return [u'%s\n' % rule.cssText for rule in sheet if rule.cssText and len(rule.cssText)>0]
    lines = property(get_lines)
       
class JsSourceNode(SourceNode):
    pass

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

def combine_asset_sources(sources,basedir,source_node=SourceNode):
    """
    A loose dependency detection, that ignores whitespace and extra signs
    
    @requires .."path/included.css"..
    
    including external files vs ordering internal files
    """
    
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

