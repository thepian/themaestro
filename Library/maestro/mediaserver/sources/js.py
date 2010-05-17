from __future__ import with_statement
import fs, re
from fs.filters import fnmatch
from os.path import join,isdir,exists

from thepian.conf import structure

from base import SourceNode

include_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*\)\s*;')
include_with_scope_statement = re.compile(r'@include\s*\(\s*"([^"]+)","([^"]+)"\s*\)\s*;')
insert_statement = re.compile(r'@insert\s*\(\s*\)\s*;')
attributes_statement = re.compile(r'@attributes\s*\(\s*\)\s*;')
fold_statement = re.compile(r'@fold\s*\(\s*\)\s*;')
unfold_statement = re.compile(r'@unfold\s*\(\s*\)\s*;')

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
                include = parts[0] + include + parts[1]
            return line[:m.start(0)] + include + line[m.end(0):]
        return line
        
    def decorated(self,base,attributes=None):
        result = base
        
        # Fold functions etc listed by @fold(..) into a stash for later
        fold = fold_statement.search(result)
        if fold:
            # -- folding code
            result = result[:fold.start()] + "" + result[fold.end()+1:]
            
        # Unfold functions etc stash named by @unfold(..)
        unfold = unfold_statement.search(result)
        if unfold:
            # -- folding code
            result = result[:unfold.start()] + "" + result[unfold.end()+1:]

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

