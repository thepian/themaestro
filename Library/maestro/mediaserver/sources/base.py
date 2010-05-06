from __future__ import with_statement
import fs, re
from os.path import join,isdir,exists

from thepian.conf import structure

scope_statement = re.compile(r'@scope [^"]*"([^"]+)"')
requires_statement = re.compile(r'@requires [^"]*"([^"]+)"')

class SourceNode(object):
    
    used = False
    
    def __init__(self,path,basedir):
        self.path = path
        self.basedir = basedir
        self.scope = None
        try:
            self._lines = [line for line in fileinput.FileInput(files=(self.path,))]
        except IOError:
            try:
                self._lines = [line for line in fileinput.FileInput(files=(join(self.basedir,self.path),))]
            except IOError:
                self._lines = []
                print "failed to load Asset Source: %s" % self.path
        includes = []
        for line in self._lines[:25]:
            m = requires_statement.search(line)
            if m:
                includes.extend(m.groups())
            m = scope_statement.search(line)
            if m:
                self.get_scope(m.groups()[0]) 
        self.includes = [join(basedir,i) for i in includes]
        
    def __repr__(self):
        return self.path
    
    def get_scope(self,name):
        # print 'scope',name
        try:
            with open(join(self.basedir,name)) as f:
                self.scope = f.read()
        except:
            pass

    @classmethod
    def list_dependencies(cls,src,full_path=True):
        """Naive implementation returning all files in the directory"""
        return fs.listdir(src,full_path=full_path,recursed=True,followlinks=True)

    @classmethod
    def decorate_lines(cls,lines,ordered_sources):
        return lines
        
