from __future__ import with_statement
import fs, re
from fs.filters import fnmatch
from os.path import join,isdir,exists

from thepian.conf import structure

from base import SourceNode

include_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*\)\s*;')
include_with_scope_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)\s*;')
insert_statement = re.compile(r'@insert\s*\(\s*\)\s*;')

decorator_statement = re.compile(r'@(\w+\s*\([^\)]*\)\s*);')

attributes_statement = re.compile(r'attributes\s*\(\s*\)\s*')
stash3_statement = re.compile(r'stash\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([^\)]*)\s*\)\s*')
stash2_statement = re.compile(r'stash\s*\(\s*"([^"]+)"\s*,\s*([^\)]*)\s*\)\s*')
stash1_statement = re.compile(r'stash\s*\(\s*"([^"]+)"\s*\)\s*')

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

        m = include_with_scope_statement.search(line)
        if m:
            include = '/* %s not found */' % m.group(1)
            try:
                full_path = join(self.basedir,m.group(1))
                with open(full_path,"r") as f:
                    include = f.read()
            except IOError:
                pass
            scope = self.get_scope(m.group(2))
            parts = insert_statement.split(scope,1)
            if parts:
                include = self.decorated(parts[0],attributes=self.attributes) + include + self.decorated(parts[1],attributes=self.attributes)
            return line[:m.start(0)] + include + line[m.end(0):]
        return line
        
    folding_code = """\
var __folded_%s__ = %s; """

    unfolding_code = """
eval((function(){
    var res = [];
    var map = __folded_%(name)s__;
    for(var n in map) res.push('var '+n+' = __folded_%(name)s__.'+n+';');
    return res.join(' ');
})());
"""
    stashall_code = """
__folded_%(name)s__ = %(value)s;
"""

    stashone_code = """
__folded_%(name)s__.%(entry)s = %(value)s;
"""

    def decorated(self,base,attributes=None):
        result = []
        decs = decorator_statement.split(base)
        for filler,decorator in zip(decs[::2],decs[1::2]):

            # Stash single functions etc specified by 3rd param @stash(..) into a stash for later
            stash = stash3_statement.match(decorator)
            if stash:
                self.stashes.add(stash.group(1))
                code = self.stashone_code % { "name": stash.group(1), "entry": stash.group(2), "value": stash.group(3) }
                result.append(filler)
                result.append(code)
                continue
            
            # Stash functions etc listed by @stash(..) into a stash for later
            stash = stash2_statement.match(decorator)
            if stash:
                self.stashes.add(stash.group(1))
                code = self.stashall_code % { "name": stash.group(1), "value": stash.group(2) }
                result.append(filler)
                result.append(code)
                continue

            # Pull functions etc out of predefined stash 
            stash = stash1_statement.match(decorator)
            if stash:
                self.stashes.add(stash.group(1))
                code = self.unfolding_code % { 'name':stash.group(1) }
                result.append(filler)
                result.append(code)
                continue

            # @attributes();
            a = attributes_statement.match(decorator)
            if a:
                result.append(filler)
                result.append(attributes)
                continue
                
            result.append(filler)
            result.append("/* %s */" % decorator)    
            
        result.append(decs[-1])

        return ''.join(result)

    @classmethod
    def decorate_lines(cls,lines,ordered_sources,basedir=None,default_scope=None):
        for source in ordered_sources:
            scope = source.scope or cls.read_scope(default_scope,basedir)
            attributes = source.attributes
            if scope:
                parts = insert_statement.split(scope,1)
                lines.insert(0,source.decorated(parts[0],attributes=attributes))
                lines.append(source.decorated(parts[1],attributes=attributes))
        return lines
        
    def decorated_lines(self,default_scope=None):
        scope = self.scope
        if not scope and default_scope:
            scope = self.get_scope(default_scope)
        lines = [self.decorated(line) for line in self.lines]
        if scope:
            parts = insert_statement.split(scope,1)
            if parts:
                lines.insert(0,self.decorated(parts[0],attributes=self.attributes))
                lines.append(self.decorated(parts[1],attributes=self.attributes))
            else:
                pass #TODO warning scope has no @insert statement
        return lines

    def stash_init_lines(self):
        lines = []
        for s in self.stashes:
            lines.append(self.folding_code % (s,"{}"))
        return lines
        
    def prepend_stashes(self,lines):
        for s in self.stashes:
            lines.insert(0,self.folding_code % (s,"{}"))
        return lines

class JsScopeNode(JsSourceNode):
    
    def __init__(self,scope,basedir,source=None,lines=None,attributes={}):
        super(JsScopeNode,self).__init__('',basedir,source,lines,attributes)
        self.scope = self.get_scope(scope)
        
    def decorated_lines(self):
        lines = super(JsScopeNode,self).decorated_lines()
        lines[0:0] = self.stash_init_lines()
        return lines
        
    
