from __future__ import with_statement
import fs, re, fileinput
from os.path import join,isdir,exists

from thepian.conf import structure

from simplejson import JSONEncoder
encoder = JSONEncoder()

scope_statement = re.compile(r'@scope [^"]*"([^"]+)"')
requires_statement = re.compile(r'@requires [^"]*"([^"]+)"')

class SourceNode(object):
    
    used = False
    
    def __init__(self,path,basedir,source=None,lines=None,attributes={}):
        """
        Loads the source code for the node from *path* unless *source* is specified.
        Then determines scope, includes and requires
        
        source Optional string with inline source code
        """
        self.path = path
        self.basedir = basedir
        self.scope = None
        if lines:
            self._lines = lines
        elif source is None:
            try:
                self._lines = [line for line in fileinput.FileInput(files=(self.path,))]
            except IOError:
                try:
                    self._lines = [line for line in fileinput.FileInput(files=(join(self.basedir,self.path),))]
                except IOError, e:
                    self._lines = []
                    print "failed to load Asset Source: '%s'" % self.path, e
                    import traceback; traceback.print_exc()
        else:
            self._lines = source.split('\n')
        includes = []
        for line in self._lines[:25]:
            m = requires_statement.search(line)
            if m:
                includes.extend(m.groups())
            m = scope_statement.search(line)
            if m:
                self.scope = self.get_scope(m.groups()[0]) 
        self.includes = [join(basedir,i) for i in includes]
        
        self.attributes_json = encoder.encode(attributes)
        self.attributes = attributes
        
        self.stashes = set()
        
    def __repr__(self):
        return self.path
        
    def prepend_stashes(self,lines):
        return lines
    
    def get_scope(self,name):
        try:
            with open(join(self.basedir,name)) as f:
                return f.read()
        except:
            return ''

    @classmethod
    def read_scope(self,name,basedir):
        # print 'scope',name
        try:
            with open(join(basedir,name)) as f:
                return f.read()
        except:
            return ''

    @classmethod
    def list_dependencies(cls,src,full_path=True):
        """Naive implementation returning all files in the directory"""
        return fs.listdir(src,full_path=full_path,recursed=True,followlinks=True)

    @classmethod
    def decorate_lines(cls,lines,ordered_sources,basedir=None,default_scope=None):
        return lines
        
