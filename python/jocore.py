# -*- coding: utf-8 -*-
"""
   Copyright 2010 Evgen Burzak

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

#
# FIXME docstrings and comments
#
__version__ = "0.00001ᵅ" 

import os, sys, urllib, string, copy, random
from types import *
import jo2js, joparser, jovm

class ImportError(Exception): pass
class TranslatorError(Exception): pass
StrictError = joparser.StrictError
RangeError_ = jovm.RangeError_

joos_version = "1.0"
debug = 0
abspath__ = os.path.split(os.path.abspath(__file__))
#os.path.join(sys.path[0], 'lib')
libs = [os.path.join(abspath__[0], 'lib'), os.curdir]

root_scope = None
import_order = 1
tokens = {}
quiet = False

internals = [ 'parent', 'root', "__class__",
         "__global__", "__defs__", "__trace__",

         # Magic keywords
         '__PUBLIC__', '__PRIVATE__', '__STATIC__', '__PROTECTED__', '__GLOBAL__',
         '__INTERNAL__', '__MACRO__',
         '__FILE__', '__PATH__', '__FUNC__', '__CLASS__', '__NAMESPACE__', 

         # ECMAScript internals
         'arguments',
         'alert', 'print',
         'isNaN', 'parseInt', 'parseFloat',
         'String', 'Number', 'Function', 'Math', 'Array', 'RegExp', 'Object', 
         'Boolean', 'Date' ]

def Init(tokens_):
    for tok in tokens_:
        globals()[tok] = tokens_[tok]
    
    tokens.clear()
    tokens.update(tokens_)

def _print(*args):
    a = []
    for s in args: a.append(str(s))
    out = " ".join(a)
    sys.stderr.write(out + "\n")
    #print '/*', str, "*/"

def Warning(message, mtype = "WARNING"):
    sys.stderr.write((mtype and mtype + ": ") + message + "\n")

gen_chars = "$_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
gen_stack = list(gen_chars[1:-10])
gen_slen = 1
gen_generated = []
def genRandName(slen):
    rname = ""
    if slen > 1:
        for k in range(slen):
            l = len(gen_chars) - (k > 0 and 1 or 11)
            i = random.randint(0, l)
            rname += gen_chars[i]
        while rname in gen_generated:
            rname = genRandName(slen)

        gen_generated.append(rname)
        return rname

    else:
        if len(gen_stack):
            i = random.randint(0, len(gen_stack)-1)
            rname = gen_stack[i]
            gen_stack.remove(i)
            return rname
        else:
            raise "Chars are closed"

def uniqId(prefix="x"):
    return "{" + prefix + "-" + genRandName(4) + "-" + genRandName(4) + "}"

#
# import routines
#
cached_paths = {}

def getModulesPath(script_root, from__, mod_, ns=None):
    exts = []
    if debug > 2: 
        _print("getModulesPath()", script_root, from__, mod_, ns)
        #_print(libs)
    mod = mod_.split(".")
    from_ = from__ and from__.split('.') or []
    module = (ns or "") + string.join(mod + from_, '.')
    if module in cached_paths: 
        return cached_paths[module]

    # ns is an net address
    if ns:
        url = "http://%s/%s/%s.%s" % (ns, string.join(from_, "/"), string.join(mod, "/"), "joo")
        exts.append(url)
    else:
        #_print('module', module, mod, from_, mod_)
        path = [script_root] + libs
        _paths = None
        for p in path:
            _paths = joinPath(p, from_, mod[:-1])
            if _paths: break
            _paths = joinPath(p, mod[:-1])
            if _paths: break
            _paths = joinPath(p, from_)
            if _paths: break

        processed = []
        if _paths:
            if mod_[-1:] == "*":
                for d in _paths:
                    found = None
                    for f in os.listdir(d): 
                        file = os.path.splitext(f)
                        if file[1] in ('.joo', '.js', '.as'):
                            if f not in processed:
                                #_print("found", f)
                                found = f
                    if found:
                        processed.append(f)
                        exts.append(os.path.join(d,f))
            else:
                for d in _paths:
                    found = None
                    for f in os.listdir(d):
                        ext = os.path.splitext(f)[1]
                        f = os.path.join(d, f)
                        m = os.path.join(d, string.join(mod[-1:],os.path.sep) + ext)
                        if ext and f == m:
                            if f not in processed: 
                                #_print("found", f)
                                found = f
                                break
                    if found:
                        processed.append(f)
                        exts.append(f)
                        break
                

    if len(exts):
        cached_paths[module] = exts
        return exts
    else:
        raise ImportError, string.join(["External component", 
                mod_, "not found in", "[" + string.join(libs + [script_root], ", ") + "]"], " ")

def joinPath(*args):
    #_print("joinPath()", args)
    _path = []
    path = ""
    paths = []
    script_root = args[0]
    i = 0
    for a in args: 
        if i == 0: pass
        elif type(a) is ListType:
            for p in a: 
                path = os.path.join(path, p)
                _path.append(p)
        elif type(a) is StringType:
            if a != "":
                _path.append(a)
                path = os.path.join(path, a)
        else:
            raise "joinPath(): Unexpected type"
        i += 1

    _lib = copy.copy(libs)
    _lib.append(script_root)

    for l in _lib:
        p = os.path.join(l, path)
        if os.path.exists( p ) and p not in paths:
            paths.append(p)
    
    return len(paths) and paths or None

#
# Scope
#
class Scope(dict):
    def __init__(self, parent_=None, param={}):

        self.funDecls = [] 
        self.classDecls = [] 
        self.funArgs = []
        self.readOnlyVar = []

        if parent_ is not None:
            dict.__init__(self, parent_)
            if isinstance(parent_, Scope):
                self.classDecls.extend(parent_.classDecls)
                self.funDecls.extend(parent_.funDecls)
                self.funArgs.extend(parent_.funArgs)
                self.readOnlyVar.extend(parent_.readOnlyVar)
                self.namespace = parent_.namespace
                self.this = parent_.this
                self.parent = parent_
                self.with_ = parent_.with_
        else:
            dict.__init__(self)
            self.parent = None
            self.namespace = None
            self.with_ = None
            self.this = None
            self.readOnlyVar.extend(internals)

        #self.isModuleContext = getattr(parent_, 'isModuleContext', False) or param.get('context') == MODULE
        self.isClassContext = getattr(parent_, 'isClassContext', False)
        #self.isPackageContext = getattr(parent_, 'isPackageContext', False) or param.get('context') == PACKAGE

        if "funArgs" in param:
            self.funArgs.extend(param['funArgs'])
        if "namespace" in param:
            self.namespace = param['namespace']
        if "with" in param:
            self.with_ = param['with']
        if "this" in param:
            self.this = param['this']

        self.context = param.get('context') or getattr(parent_, 'context', -1)

    def extend(self, augment, extendParent=False): #, 
        
        if debug > 2: before = set(self.keys())

        self.update(augment)

        if getattr(augment, 'readOnlyVar', None):
            for ro in augment.readOnlyVar:
                if ro not in self.readOnlyVar:
                    self.readOnlyVar.append(ro)

        self.funArgs.extend(augment.funArgs)

        for fun in augment.funDecls:
            decl = getattr(fun, 'decl', None)
            if getattr(fun, 'id', None) in self: continue

            if debug > 1: 
                _print("+fun", getattr(fun, 'name', None), jo.tokens.get(self.context))

            fun.id = uniqId("function")
            self[fun.id] = fun
            self.funDecls.append(fun)
               
        for cls in augment.classDecls:
            decl = getattr(cls, 'decl', None)
            if getattr(cls, 'id', None) in self or \
                    decl == -1: continue

            if debug > 1: _print("+cls", getattr(cls, 'name', None), jo.tokens.get(self.context))

            cls.id = uniqId("class")
            self[cls.id] = cls
            self.classDecls.append(cls)

        if debug > 1:
            _print("Scope.extend()", len(self), len(self.readOnlyVar), len(self.funArgs), len(self.classDecls), len(self.funDecls))
            if debug > 2:
                diff = set(self.keys()).difference(before)
                _print("diff", ", ".join(diff))

        # extendParent apply for 'internals' only
        #if extendParent:
            #if self.parent:
                #self.parent.extend(augment, extendParent)

    def isVar(self, id):
        return self.getDecl(id) in (VAR, LET, CONST)

    def isClass(self, id):
        isclass = self.getDecl(id) == CLASS
        for cls in self.classDecls:
            if getattr(cls, 'name', None) == id:
                isclass = True
                break

        return isclass

    def isFunction(self, id):
        return self.getDecl(id) == FUNCTION
        
    def isInternal(self, id):
        return id in internals or self.getDecl(id) == INTERNAL

    def isPrivate(self, id):
        return self.getDecl(id) == PRIVATE

    def isStatic(self, id):
        return self.getDecl(id) == STATIC

    def isPublic(self, id):
        return self.getDecl(id) == PUBLIC

    def isProtected(self, id):
        return self.getDecl(id) == PROTECTED

    def isMacro(self, id):
        return self.getDecl(id) == MACRO

    def isGlobal(self, id):
        return self.getDecl(id) == GLOBAL

    def inScope(self, id):
        if id in self:
            return self[id]
        else:
            return None

    def isLocal(self, id):
        return self.getDecl(id) in (VAR, LET, CONST, CLASS, FUNCTION)

    def getDecl(self, id):
        return id in self and self[id].decl or None

    def get(self, id):
        if not self.inScope(id):
            return None
        return self[id]

    def add(self, name, node, updateParent=False):
        if name not in self:
            self[name] = node

        if updateParent:
            if self.parent: 
                self.parent.add(name, node, updateParent)

    def set(self, name, node, updateParent=False):
        self[name] = node

        if updateParent:
            par = self.parent
            if par: par.set(name, node, updateParent)

    def splitNS(self, ns):
        ns_ = ns.split('.')
        return ns_[0] == 'root' and ns_[1:] or ns_

    def addClassDecl(self, cl, ns=None, updateParent=False):
        id = getattr(cl, 'id', uniqId("class"))
        name = cl.name
        cl.id = id
        if debug > 1: _print("addClassDecl()", name, ns, id, self.namespace)
        
        if id not in self:
            self.classDecls.append(cl)
            self[id] = cl
            self[name] = cl
            if ns: 
                self[name].namespace_ = ns
                cl.namespace = ns != 'root' and root_symb + "." + ns or root_symb
                if ns != 'root':
                    ns_ = self.splitNS(ns)
                    self.add(ns_[0], Node(PUBLIC, root_symb))

        if updateParent:
            par = self.parent
            if par: par.addClassDecl(cl, ns, updateParent)
    
    def save(self): pass
    
    def restore(self): pass

heap = {}
root_scope = Scope()

# 
# ScriptContext
#
class JOContext(object):
    def __init__(self, script=None):
        self.__ns__ = {}
        self.root_scope = root_scope
        self.heap = heap
        self.parser = joparser
        self.path = ""
        self.script_root = ""
        self.script_name = ""
        self.script_type = "jooscript"
        self.namespace = ""
        self.strictMode = False
        self.shell_ = False
        self.encoding = 'utf-8'
        Init(self.parser.Init(self, self.script_type, globals()))
        jo2js.Init(self, tokens, globals())
        self.vm = jovm.JOVM(self, tokens, globals())
        self.import_internals()
        if script:
            self.load(script)

    def import_internals(self, scope=None):
        scope_ = Scope()
        self.import_('base.internals', None, None, -1000)
        if scope:
            scope.extend(scope_, True)
        else:
            self.root_scope.extend(scope_, True)

    def import______(self, exts, from_ = None):
        Import(self.root_scope, exts, from_, self.import_order * 1000)
        import_order += 1

    def scope(self, parent = None, params = {}):
        return Scope(parent, params)

    def import_(self, exts, from__=None, ns=None, order=0, scope = None, depth = 0):
        if from__:
            from_ = from__.split(".")

        scripts = []

        exts_ = exts.split(".")
        namespace = len(exts_) > 1 and string.join(exts_[:-1], '.') or from__

        scripts.extend( [[namespace, s] 
            for s in getModulesPath(self.script_root, from__, exts, ns)] )

        modules = []

        #_print("@@@", scripts)
        for (namespace, script) in scripts:
            if script in self.heap: 
                order_ = self.heap[script]['order']
                if (order < 0 and order_ < 0 and order < order_) or \
                        (order > 0 and order_ > 0 and order > order_):
                    self.heap[script]['order'] = order
                    modules.append(self.heap[script])
                continue

            if debug: _print("JOContext.import_()", script, namespace)

            abspath = os.path.split(script)
            params = {}
            params['include_props'] = dict(script_root=abspath[0], script_name=abspath[1])
            file_ = os.path.splitext(script)
            ext = file_[1] 
            stype = (ext == '.joo' and "jooscript") or (ext == '.js' and "javascript") or \
                    (ext == '.as' and "actionscript")
            name = os.path.splitext(abspath[1])[0]

            # FIXME raise-catch 404 error
            try:
                f = script.startswith("http") and urllib.urlopen(script) or file(script, 'r')
            except IOError, ex:
                raise ImportError, "%s, %s" % (script, str(ex))


            tree = self.parse(f.read(), order or import_order, depth)

            self.heap[script] = dict(
                    compiled = "",
                    namespace = tree.namespace or namespace,
                    name = name,
                    tree = tree,
                    filename = abspath[1],
                    path = self.script_root,
                    params = params,
                    hash = "",
                    type = stype,
                    order = order or import_order )

            this = self.heap[script]

            if this['type'] == 'class':
                params['order'] = this['order']
                pubclass = this['tree'].scope.get(name)
                pubclass.lazy = 1
                pubclass.decl = -1
                scope.addClassDecl(pubclass, this['namespace'], True)
                this['hash'] = pubclass.hash
                this['tree'].context = MODULE
                #this['compiled'] = jo2js.convert(this['tree'], params, scope, this) 
                #this['scope'] = params['scope']

            elif this['type'] == 'jooscript':
                params['skip_vars'] = True
                params['order'] = this['order']
                #this['compiled'] = jo2js.convert(this['tree'], params, scope, this) 
                #this['scope'] = params['scope']
                self.root_scope.extend(this['tree'].scope)
                #ints = [x for x in this['tree'].scope 
                        #if this['tree'].scope[x].decl == INTERNAL]
                #_print(ints)
                #if len(ints) and this['order'] > 0: this['order'] = this['order'] * -1

            modules.append(this)

        return modules

    def load(self, script):
        if script.endswith(('.js', '.joo', '.as')):
            self.path = os.path.abspath(script)
            self.script_root = os.path.split(self.path)[0]
            self.script_name = os.path.split(self.path)[1]
            module_name = os.path.splitext(self.script_name)[0]
        else:
            raise ImportError, "JOContext.load(): Not supported " + script

        self.import_(module_name, None, None, import_order * 1000)
        import_order += 1

    def ns(self, ns):
        if debug > 1: _print("ns()", ns)

        if not ns: raise "ns(): empty namespace"

        if ns not in __ns__: 
            self.__ns__[ns] = Scope()
            self.__ns__[ns].namespace = ns
            self.__ns__[ns].context = None

        return self.__ns__[ns]
    
    def warning(self, message, line=-1, mtype="Warning"):
        if quiet: return
        if self.path:
            sys.stderr.write("Encountered errors in " + self.path + "...\n")
        sys.stderr.write((mtype and mtype + ", line %i: " %line) + message + "\n")
        self.path = ""

    def parse(self, source, order=0, depth=1):
        return self.parser.parse(self, source, 
                    import_order = order, 
                    depth = depth,
                    glob = globals() )

    def shell(self, enable=True):
        if enable:
            #self.__script_name = self.script_name
            #self.__script_type = self.script_type
            self.script_name = "(shell)"
            self.script_type = "script"
            self.shell_ = True
            def quit(*args): raise EOFError
            self.vm.globals['quit'] = quit
            #self.heap[self.script_name] = self
        else:
            #self.script_name = self.__script_name
            #self.script_type = self.__script_type
            self.shell_ = False
            del self.vm.globals['quit']
        return self
    
    eval = lambda self, input: self.vm.eval(self.parse(input, 0, 100))
    
    def translate(self, input, target="javascript"):
        return self.convert(self.parse(input), target)

    def convert(self, input, target="javascript"):
        return jo2js.convert(input, self.root_scope)
        

# 
# public interface

def load(script):
    return JOContext(script)

include = load

def shell():
    return JOContext(False).shell()

def compile():
    try:
        return jo2js.CompileProject(heap)
    except Exception, e:
        raise 
        #raise TranslatorError, e.message
    
def scope(self, parent = None, params = {}):
    return Scope(parent, params)

