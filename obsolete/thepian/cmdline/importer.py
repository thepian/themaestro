# http://orestis.gr/blog/2008/12/20/python-import-hooks/
# http://www.python.org/dev/peps/pep-0302/

import sys
import os
import imp

IMP_TYPE = {
    imp.PY_SOURCE: "%(path)s%(ext)s",
    imp.PY_COMPILED: "%(path)s.pyc",
    imp.C_EXTENSION: "%(path)s%(ext)s",
    imp.PKG_DIRECTORY: "%(path)s/__init__.py",
}

class Loader(object):
    print_trace = False
    
    def __init__(self,modfilename,modfile,description,modpath=None):
        self.modfilename = modfilename
        self.modfile = modfile
        self.modpath = modpath
        self.description = description
        
    def load_module(self, name):
        """
        This method returns the loaded module or raises an exception,
        preferably ImportError if an existing exception is not being
        propagated.  If load_module() is asked to load a module that it
        cannot, ImportError is to be raised.
    
        In many cases the importer and loader can be one and the same
        object: importer.find_module() would just return self.
    
        The 'fullname' argument of both methods is the fully qualified
        module name, for example "spam.eggs.ham".  As explained above, when
        importer.find_module("spam.eggs.ham") is called, "spam.eggs" has
        already been imported and added to sys.modules.  However, the
        find_module() method isn't necessarily always called during an
        actual import: meta tools that analyze import dependencies (such as
        freeze, Installer or py2exe) don't actually load modules, so an
        importer shouldn't *depend* on the parent package being available in
        sys.modules.
        """
        if name not in sys.modules:
            try:
                imp.acquire_lock()
                if self.print_trace:
                    print 'loading ',name,'(',self.modfilename,')'
                module = imp.load_module(name,self.modfile,self.modfilename,self.description)
                if self.modfile:
                    self.modfile.close()
                #module.__loader__ = self
                module.__file__ = self.modfilename
                if self.modpath:
                    module.__path__ = self.modpath
                if self.print_trace:
                    print 'loading %s finished' % name
                sys.modules[name] = module
                if '.' in name:
                    parent_name, child_name = name.rsplit('.', 1)
                    setattr(sys.modules[parent_name], child_name, module)
            finally:
                try: fin.close()
                except: pass
                imp.release_lock()
        return sys.modules[name]

class MetaImporter(object):
    print_trace = False
    
    def __init__(self):
        self.alternates = {}
        
    def find_module(self, fullname, path=None):
        """
        This method will be called with the fully qualified name of the
        module.  If the importer is installed on sys.meta_path, it will
        receive a second argument, which is None for a top-level module, or
        package.__path__ for submodules or subpackages[7].  It should return
        a loader object if the module was found, or None if it wasn't.  If
        find_module() raises an exception, it will be propagated to the
        caller, aborting the import.
        """
        if self.print_trace:
            print 'import call: %s (%s)' % (fullname,path)
        if '.' not in fullname and not path:
            alternate = self.alternates.get(fullname,None)
            if alternate:
                if self.print_trace:
                    print 'alternate import %s (%s)' % (fullname,path)
                try:
                    f,pathname,description = imp.find_module(fullname,alternate)
                except ImportError:
                    return None
                modfilename = IMP_TYPE.get(description[2],"%s") % dict(path=pathname,ext=description[0])
                return Loader(pathname,f,description,modpath=[pathname])
        return None
