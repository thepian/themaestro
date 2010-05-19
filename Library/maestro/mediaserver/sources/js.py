from __future__ import with_statement
import fs, re
from fs.filters import fnmatch
from os.path import join,isdir,exists

from thepian.conf import structure

from base import SourceNode

include_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*\)\s*;')
include_with_scope_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)\s*;')
insert_statement = re.compile(r'@insert\s*\(\s*\)\s*;')
attributes_statement = re.compile(r'@attributes\s*\(\s*\)\s*;')
stash2_statement = re.compile(r'@stash\s*\(\s*"([^"]+)"\s*,\s*([^\)]*)\s*\)\s*;')
stash1_statement = re.compile(r'@stash\s*\(\s*"([^"]+)"\s*\)\s*;')
fold_statement = re.compile(r'@fold\s*\(\s*"([^"]+)"\s*,\s*([^\)]*)\s*\)\s*;')
unfold_statement = re.compile(r'@unfold\s*\(\s*"([^"]+)"\s*\)\s*;')

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
        
    folding_code = """
var __folded_%s__ = %s;
"""

    unfolding_code = """
    eval((function(){
        var res = [];
        var map = __folded_%(name)s__;
        for(var n in map) res.push('var '+n+' = __folded_%(name)s__['+n+'];');
        return res.join(' ');
    })());
"""
    def decorated(self,base,attributes=None):
        result = base

        # Stash functions etc listed by @stash(..) into a stash for later
        while(True):
            stash = stash1_statement.search(result)
            if stash:
                print stash.group(1), "marked"
                self.stashes.add(stash.group(1))
                code = "" # self.folding_code % (fold.group(1),fold.group(2))
                result = result[:stash.start()] + code + result[stash.end()+1:]
            else:
                break
        
        # Fold functions etc listed by @fold(..) into a stash for later
        while(True):
            fold = fold_statement.search(result)
            if fold:
                # -- folding code
                code = self.folding_code % (fold.group(1),fold.group(2))
                result = result[:fold.start()] + code + result[fold.end()+1:]
            else:
                break
            
        # Unfold functions etc stash named by @unfold(..)
        while(True):
            unfold = unfold_statement.search(result)
            if unfold:
                code = self.unfolding_code % { 'name':unfold.group(1) }
                result = result[:unfold.start()] + code + result[unfold.end()+1:]
            else:
                break

        a = attributes_statement.search(result)
        if a:
            if attributes:
                result = result[:a.start()] + attributes + ";" + result[a.end()+1:]
            else:
                result = result[:a.start()] + result[a.end()+1:]

        return result

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
        lines = self.lines[:]
        if scope:
            parts = insert_statement.split(scope,1)
            if parts:
                lines.insert(0,source.decorated(parts[0],attributes=source.attributes))
                lines.append(source.decorated(parts[1],attributes=source.attributes))
            else:
                pass #TODO warning scope has no @insert statement
        return lines

    def prepend_stashes(self,lines):
        print self.stashes
        for s in self.stashes:
            lines.insert(0,self.folding_code % (s,"{}"))
        return lines
