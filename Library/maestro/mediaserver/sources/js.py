from __future__ import with_statement
import fs, re
from fs.filters import fnmatch
from os.path import join,isdir,exists

from thepian.conf import structure

from base import SourceNode

include_statement = re.compile(r'@include\s*\(\s*"([^"]+)"\s*\)\s*;')
insert_statement = re.compile(r'@insert\s*\(\s*\)\s*;')

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

    @classmethod
    def decorate_lines(cls,lines,ordered_sources,basedir=None,default_scope=None):
        for source in ordered_sources:
            scope = source.scope or cls.read_scope(default_scope,basedir)
            if scope:
                parts = insert_statement.split(scope,1)
                lines.insert(0,parts[0])
                lines.append(parts[1])
        return lines

