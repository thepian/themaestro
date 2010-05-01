#!/usr/bin/python2.5
# coding: utf-8
"""
   Copyright [yyyy] [name of copyright owner]

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
#  TODO
#
#  __*__  replace "+" with "concat(.." where is string processing, it's safe way
#         to process strings and XML streams;
#
#  __*__  Array comprehensions.
#
#  Notes
#    _ in Rhino's XML parser ignoreComments is set to false by default. Not 
#      as in Firefox. Default value should be true.

#from __future__ import print_function

"""
 Formed PyNarcissus S-expression converter.

 Converts a PyNarcissus parse tree into S-expressions.
"""

__author__ = "JT Olds" 
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"

"""

 Joos/JS/ActionScript into JavaScript converter.

"""

__author__ = "burzak" 
__author_email__ = "buzzilo@gmail.com"
__date__ = "2009-10-27"

__all__ = ["convert", "UnknownNode", "OtherError", "ProgrammerError", "SyntaxError", "Error_"]

this_symb = "ŧ"
root_symb = "ṙ"
ns_symb = "Ŋ"
global_symb = "ĝ"
define_symb = "đ"
static_symb = "ŝ"
public_symb = "ṕ"
xml_symb = "ẋ"
xmllist_symb = "ẍ"
with_symb = "ộ"
self_symb = "ṡ"
class_symb = "ḉ"
protected_symb = "ṗ"

minify = False
debug = 0
native_e4x = False

class Error_(Exception): pass
class UnknownNode(Error_): pass
class OtherError(Error_): pass
class ProgrammerError(OtherError): pass

import re, sys, string, copy, random, traceback
import joparser as jo

trimRightRe = re.compile("^(\s+)", re.MULTILINE)
trimRe = re.compile("(\s{2,})", re.MULTILINE)

def Init(jocore, tokens, glob):
    for tok in tokens:
        globals()[tok] = tokens[tok]

    globals()['debug'] = glob['debug']
    globals()['uniqId'] = glob['uniqId']
    globals()['genRandName'] = glob['genRandName']
    globals()['jocore'] = jocore
    globals()['_print'] = glob['_print']

    globals()['internals'] = glob['internals']

    t = glob['tokens']
    globals()['subs'] = dict( joos_version=glob['joos_version'], xml_initializer = xml_symb, 
            xml_list_initializer = xmllist_symb)

def Header():
    header = [
        "var "+this_symb+"=this",
        global_symb+"=root",
        root_symb+"=root",
        "__class__=null",
        "__args__=null",
        "__global__=root"
        #"Public=%i,Private=%i,Static=%i,Protected=%i,Global=%i" % (PUBLIC,
            #PRIVATE, STATIC, PROTECTED, GLOBAL) 
        ]
        # globals is reserved in Chrome and Safari
        #function globals() {return global}",

    return trimRe.sub('', string.join(header, ",")) + ";"
            
def CompileProject(heap_, project_name = "$proj$"):

    header = Header()

    heap = [[x['order'], s, x] for (s, x) in heap_.items() ]
    heap.sort(cmp=lambda x,y: cmp(y[0], x[0]))

    # FIXME shared namespace 'this' for all scripts except classes
    #
    classes = []
    mods = []
    for (i, s, x) in heap:
        if x['type'] == 'class' and x['order'] > 0:
            classes.append("/* %(type)s %(name)s */ " % x + \
                    "{(function(%s)%s)(%s)}" % (this_symb, 
                        convert(x), "new(function(){})"))
            mods.append("'%s'" % (x['namespace'] + "." + x['name']))

    mods.reverse()

    internals = []
    scripts = []
    for (i, s, x) in heap:
        if x['type'] == 'jooscript':
            scope = x['tree'].scope
            let = [y for y in scope 
                        if scope[y].decl == LET and not y.startswith("{")]
            var = [y for y in scope
                        if scope[y].decl in (INTERNAL, VAR, CONST, FUNCTION, CLASS) and \
                            not y.startswith("{")]

            package = "" + \
                    "/* %(type)s %(name)s */ " % x + \
                    ((len(var) and "var %s;\n" % ",".join(var)) or "") + \
                    "{new (function(){var %s=this;" % this_symb + \
                        ((len(let) and "var %s;" % ",".join(let)) or "") + \
                        convert(x) + \
                    "})()}"

            if x['order'] > 0: scripts.append(package)
            elif x['order'] < 0: internals.append(package)
        

    initClass = len(classes) > 0 and "initClass(" + string.join(mods, ",") + ");" + "\n" or ""

    return "new /* project %s */ (function (root, parent) {" % project_name + "\n" + \
           "/* header */ " + header + "\n" + \
                string.join(internals , "\n") + "\n" + \
                string.join(classes, "\n") + "\n" + \
                initClass  + \
                string.join(scripts, "\n") + \
            "})(this, this);"

def qname(scope, id, initialize=False):

    #print "qname()", id, scope.context

    name = None
    namespace = None

    if scope.context == MODULE:
        namespace = this_symb
        name = id

    #if scope.context in [None, -1] + scope.funArgs: 
        #return id

    elif id in subs: 
        return subs[id]
    
    elif scope.isInternal(id):
        if initialize: scope.readOnlyVar.append(id)
        name = id

    elif scope.isClass(id):
        cls = scope.get(id)
        if not hasattr(cls, 'namespace'):
            if scope.context == CLASS and decl in (PUBLIC, PROTECTED):
               cls._ns = "self"  
            elif scope.context == CLASS and decl == STATIC:
               cls._ns = "__class__"
            elif scope.context == FUNCTION and decl == STATIC:
               cls._ns = static_symb
            elif scope.context == FUNCTION and decl == PUBLIC:
               cls._ns = public_symb
            elif decl == GLOBAL:
               cls._ns = global_symb
            else:
               cls._ns = None

        #ns = getattr(cls, 'namespace', None)
        #if ns: namespace = ns 
        name = id
        namespace = cls._ns

    elif scope.isFunction(id):
        fun = scope.get(id)
        if not hasattr(fun, 'namespace'):
            if getattr(fun, 'name', None) == 'new':
               fun.name = 'New'
               fun._ns = 'self'
            elif scope.context == CLASS and decl in (PUBLIC, PROTECTED):
               fun._ns = "self"  
            elif scope.context == CLASS and decl == STATIC:
               fun._ns = "__class__"
            elif scope.context == FUNCTION and decl == STATIC:
               fun._ns = static_symb
            elif scope.context == FUNCTION and decl == PUBLIC:
               fun._ns = public_symb
            elif decl == GLOBAL:
               fun._ns = global_symb
            elif decl == INTERNAL:
               fun._ns = ""
            else:
               fun._ns = None

        name = id
        namespace = fun._ns

    elif scope.isVar(id):
        name = id

    elif scope.isPublic(id):
        pub = scope.get(id)
        if not hasattr(pub, 'namespace'):
            if scope.context == MODULE:
                pub._ns = this_symb
            elif scope.context == PACKAGE:
                pub._ns = ns_symb
            elif scope.context == CLASS:
                pub._ns = public_symb
            elif scope.context == FUNCTION:
                pub._ns = public_symb
            else:
                pub._ns = this_symb

        name = id
        namespace = pub._ns

    elif scope.isProtected(id):
        prot = scope.get(id)
        if not hasattr(prot, 'namespace'):
            if scope.context == CLASS:
                prot._ns = protected_symb
            else:
                raise SyntaxError, "Protected allowed only in class declaration"

        namespace = prot._ns 
        name = id

    elif scope.isPrivate(id):
        name = id

    elif scope.isStatic(id):
        st = scope[id]
        if not hasattr(st, 'namespace'):
            if scope.context == MODULE:
                st._ns = this_symb
            if scope.context == CLASS:
                st._ns = static_symb
            elif scope.context == PACKAGE:
                st._ns = ns_symb
            elif scope.context == FUNCTION:
                st._ns = static_symb
            else:
                st._ns = None

        namespace = st._ns 
        name = id

    # TODO complex expressions
    elif scope.isMacro(id):
        if initialize: scope.readOnlyVar.append(id)
        _def = scope.inScope(id).initializer
        name = _def.type == "STRING" and repr(_def.value) or _def.value

    elif scope.isGlobal(id):
        namespace = global_symb 
        name = id

    elif scope.with_:
        namespace = with_symb
        name = id

    else:
        return id

    qname_ = namespace and ".".join([namespace, id]) or name

    if debug > 2:
        _print('qname('+id+')', qname_, jo.tokens.get(scope.context), scope.namespace, initialize) 

    return qname_


class Package():
    def __init__(self, n, params, scope, this, namespace=None, tab="", className=None):

        self.n = n
        self.context = n.body.context
        self.params = params
        self.parent = scope
        self.namespace = namespace or 'root'
        self.scope = Scope(scope, {"namespace": self.namespace, "context": self.context})
        self.this = this
        self.tab = tab
        self.className = className

    def build(self):
        body = self.n.body
        context = self.context
        c = self.params
        scope = self.scope
        this = self.this
        namespace = self.namespace
        tab = self.tab

        #if context == MODULE:
        # check package for multiplying public class declaration
        i = 0
        for cls in body.classDecls:
            cn = getattr(cls, 'name', None)
            if cn and cn in body.scope and body.scope[cn].decl == PUBLIC:
                className = cn
                i += 1
        if i > 1: 
            raise SyntaxError, "In package " + \
                    "must be declared only one public class"
        if i == 0: 
            raise SyntaxError, "In package " + \
                    "must be declared at least one public class"

        self.parent.addClassDecl(body.scope[className], namespace, True)
        body.scope[className].decl = -1
        
        if debug: _print('Package.build()', className, namespace)

        return "{(function()%s)()}" % o(body,tab,c,[],scope,this)
        
class Class():
    def __init__(self, n, params, scope, this, 
            className=None, namespace=None, tab="", ancestors=None):

        if n.body.context != CLASS:
            raise OtherError, "Class(): unexpected context"
        self.n = n
        self.context = n.body.context
        self.params = params
        self.parent = scope
        self.namespace = namespace
        self.scope = n.body.scope
        self.this = this
        self.className = className
        self.tab = tab
        self.ancestors = ancestors
        self.iface = dict()

    def ns_ (self, n, ns=[]):

        if len(n) == 0: 
            if n.type == "IDENTIFIER":
                return [n.value]
            else:
                return None

        if n[0].type == "DOT":
            head = self.ns_(n[0])
        elif n[0].type == "IDENTIFIER":
            head = [n[0].value]
        else:
            head = None

        if n[1].type == "DOT":
            tail = self.ns_(n[1])
        elif n[1].type == "IDENTIFIER":
            tail = [n[1].value]
        else:
            tail = None

        if head == None or tail == None:
            return None

        return head + tail
        
    # class ABC extends A,B,C ...
    #
    # finding ancestors in:
    # a. current scope
    # b. root or namespace scope
    #
    def augment(self, ancestors_):
        if ancestors_ == None: return
        elif ancestors_.type == "IDENTIFIER": ancestors = [ancestors_]
        else: ancestors = ancestors_

        if debug: _print("Class.augment()", len(ancestors), self.namespace)
        for n in ancestors:
            missedAncestor = True
            ns = self.ns_(n)
            namespace = ""
            name = ""
            if ns:
                if len(ns) > 1: 
                    name = "".join(ns[-1:])
                    namespace = ".".join(ns[:-1])
                else: 
                    name = ns[0]
                    namespace = self.namespace

            if debug: _print("ancestor", namespace, name) 

            if name:
                classDecls = []
                classDecls.extend(self.parent.classDecls)
                classDecls.extend(NS('root').classDecls)
                if namespace and namespace != 'root': 
                    classDecls.extend(NS(namespace).classDecls)

                for cls in classDecls: 
                    if debug > 1: 
                        _print(getattr(cls, 'name', None), getattr(cls, 'id', None),
                            cls.type, getattr(cls, 'namespace_', None))
                    if getattr(cls, 'name', None) == name:
                        if debug > 1: 
                            _print(">", name, getattr(cls, 'namespace_', None))
                        ancestor = cls.body
                        for x in ancestor.scope:
                            decl = ancestor.scope[x].decl
                            if decl in (PUBLIC, PROTECTED, STATIC):
                                self.scope.set(x, ancestor.scope[x])

                        if getattr(cls, 'namespace_', None): 
                            n.ns_s = ".".join([cls.namespace_, name])
                        missedAncestor = False
                        break

            if missedAncestor:
                Warning("missed ancestor %s in class %s" % (ns and ".".join(ns) or \
                        o(n,"",[],[],self.scope,self.this), 
                    (self.namespace and self.namespace + "." or "") + self.className))

    def interface(self, node): 
        self.iface.clear()
        for x in node.scope:
            if node.scope[x].decl == PUBLIC:
                self.iface[x] = PUBLIC
            elif node.scope[x].decl == STATIC:
                self.iface[x] = STATIC
            elif node.scope[x].decl == PROTECTED:
                self.iface[x] = PROTECTED
            elif node.scope[x].decl == GLOBAL:
                self.iface[x] = GLOBAL

    def build(self):

        n = self.n
        context = self.context
        params = self.params
        scope = self.scope
        this = self.this
        className = self.className
        namespace = self.namespace
        tab = self.tab
        ancestors = self.ancestors
        iface = self.iface
        lazy = getattr(n, 'lazy', 0)
        decl = getattr(n, 'decl', 0)
        
        classBody = n.body

        self.augment(ancestors)
        self.interface(classBody)

        className_ = genRandName(5)

        if debug: _print('Class.build()', className, namespace)

        c = copy.copy(params)
        privs_ = [x for x in classBody.scope if classBody.scope[x].decl == PRIVATE]
        privs = len(privs_) > 0 and "," + string.join(privs_, ",") or "";

        classBody.name_ = className
        classBody.context = CLASS

        constructor = ["function(root, parent, __class__, __args__, ",
                            "%s) {" % this_symb,
                         "var self" + privs + ";"
                         "function %s () {" % className_,
                           "self=arguments.callee.prototype;",
                           o(classBody,tab,c,[],scope,this),
                           "self=__class__.instantize(__args__,parent,this,self);"
                         "}"
                       ]

        constructor.append(" return %s }" % className_)

        classScope = ["'%s':%i" % (x, y) for (x, y) in iface.iteritems()]

        #_print(ancestors)
        #ancestors_ = ancestors and "," + o(ancestors,tab,c,[],scope,root) or ""
        ancestors_ = []
        if ancestors:
            if ancestors.type == "COMMA":
                for anc in ancestors:
                    if getattr(anc, 'ns_s', None):
                        ancestors_.append(repr(anc.ns_s))
                    else:  
                        ancestors_.append(o(anc,tab,c,[],scope,this))
            elif ancestors.type == "IDENTIFIER":
                if getattr(ancestors, 'ns_s', None):
                    ancestors_.append(repr(ancestors.ns_s))
                else:
                    ancestors_.append(o(ancestors,tab,c,[],scope,this))

        ns = ""
        if decl == -1: ns = namespace or 'root'

        return "buildClass(%s%s);" % ('%s, %r, %s, %s, %s, {%s}, %s' % \
                    (lazy, ns, "0x" + n.hash.hexdigest(), this_symb,
                        className and '"'+className+'"' or 'null', 
                        string.join(classScope, ","), 
                        string.join(constructor,"")),
                    #ancestors_)
                    len(ancestors_) and "," + ",".join(ancestors_) or "")

class Node (object):
    def __init__(self, type, ns=None):
        self.type = jo.tokens[type]
        self.type_ = type
        self.decl = type
        self.namespace = ns
    
    type = None
    type_ = None
    decl = None
    namespace = None

def o(n, i, c, handledattrs=[], scope=None, this=None):
    if not getattr(n, '_ns', None): n._ns = None
    attrs_ = {'int_attrs':True, '_ns':True} #{'namespace':True}
    for attr in handledattrs:
        attrs_[attr] = True
    subnodes_ = []
    had_error = False
    def check(attrs=[], optattrs=[], subnodes=0):
        if not (type(attrs) == list and type(optattrs) == list and
                type(subnodes) == int):
            raise ProgrammerError, "Wrong arguments to check(...)!"
        for attr in attrs: attrs_[attr] = True
        for attr in optattrs:
            if hasattr(n, attr): attrs_[attr] = True
        for i in xrange(subnodes):
            subnodes_.append(True)

    def props():
        if c["include_props"]:
            props_to_include = [x for x in ("lineno", "start", "end",
                    "readOnly") if hasattr(n, x)]
            if len(props_to_include) > 0:
                s = " (@"
                for prop in props_to_include:
                    s += " (%s %s)" % (prop.upper(), getattr(n, prop))
                return s +")"
        return ""
    try:
        check(attrs=["append", "count", "extend", "filename", "getSource",
                    "indentLevel", "index", "insert", "lineno", "pop",
                    "remove", "reverse", "sort", "tokenizer", "type", "type_",
                    "hash"],
                    optattrs=["end", "start", "value",
                    'addExpression', 'addToString', 'getNextXMLToken', 
                    'readCDATA', 'readQuotedString', 'readXmlComment', 'readPI', 'readEntity',
                    'isAttribute', 'isTagContent', 'openTagsCount'])

        if n.type == "ARRAY_INIT":
            check(subnodes=len(n))
            return "[%s]" % string.join((o(x,i,c,[],scope,this) for x in n), (","))
            s = ""
            for x in n:
                if x is not None:
                    s += "," + o(x,i,c,[],scope,this)
                else:
                    s += ",null"
            return s + ""

        elif n.type == "OBJECT_INIT":
            check(subnodes=len(n))
            if len(n) > 0:
                return ("{\n  " + i + \
                        string.join((o(x,i+"  ",c,[],scope,this) for x in n), 
                            (",\n  "+i)) + "}")
            return "{}"

        elif n.type == "PROPERTY_INIT":
            check(subnodes=2)
            prop = repr(n[0].value)
            init = o(n[1],i,c,[],scope,this)
            return "%s:%s" % (prop, init)

        elif n.type == "REGEXP":
            return "new RegExp(%r,%r)" % (n.value["regexp"],
                    n.value["modifiers"])

        elif n.type == "WITH":
            check(attrs=["body", "object"])

            scope_ = Scope(scope, {"with": with_symb})

            retVar = genRandName(5)
            body = o(n.body,i,c,[],scope_,this)
            if n.body.type != "BLOCK": body = "{%s}" % body
            object = o(n.object,i,c,[],scope,this)

            return "{var %s=(function(%s)%s)(%s);" % (retVar, with_symb, body, object) + \
                        "if(typeof %s!='undefined')return(%s)}" % (retVar, retVar)

        elif n.type == "BLOCK":
            check(attrs=["let"], subnodes=len(n))
            if len(n) > 0:
                if n.let and len(n.let) > 0:
                    funArgs = [k for k in n.let]
                    scope_ = Scope(scope, {"funArgs": funArgs})
                    statements = (o(x,i+"  ",c,[],scope_,this) for x in n)
                    return "{(function(%s){" % ",".join(n.let) + \
                            ";".join(statements) + \
                            "})()}"
                else:
                    return "{" + "\n" + i + \
                            ("\n" + i).join((o(x,i+"  ",c,[],scope,this) for x in n)) + "\n" + i + "}"
            return "{}"

        elif n.type == "INDEX":
            check(subnodes=2)
            return "%s[%s]" % (o(n[0],i,c,[],scope,this), o(n[1],i,c,[],scope,this))

        elif n.type == "XML":
            check(subnodes=len(n))
            s = []

            if not native_e4x:
                Import(scope, "jo.xml", c, None, -100)

            for x in n:
                if getattr(x, "type", None) is not None:
                    if native_e4x:
                        s.append("{%s}" % o(x,i,c,[],scope,this) )
                    else:
                        s.append("%s" % o(x,i,c,[],scope,this) )
                else:
                    if native_e4x:
                        s.append( x )
                    else:
                        s.append( repr(x) )
            
            if native_e4x:
                return string.join(s, "")
            else:
                return  "%s(%s)" % (xml_symb, string.join(s, ""))

        elif n.type == "XMLATTR":
            check(subnodes=len(n))
            return '@%s' % n.value

        elif n.type == "DOTNEW":
            check(subnodes=2)
            return "%s['new']" % o(n[0],i,c,[],scope,this)

        elif n.type in ("DOT", "DOTDOT", "DOTQUERY", "COLONCOLON") :
            check(subnodes=2)
            _context = scope.context
            _c = copy.copy(c)
            head = o(n[0],i,_c,[],scope,this)
            scope.context = None
            tail = o(n[1],i,_c,[],scope,this)
            scope.context = _context

            s = "%s%s%s" % (head, jo.tokens[getattr(jo, n.type, None)], 
                tail)
            if n.type == "DOTQUERY": s += ')'
            return s

        elif n.type == "MUL" and len(n) == 0:
            return "*"

        elif n.type == "DEFAULTXMLNAMESPACE":
            check(attrs=["namespace"])
            return "%s=%s" % (n.value, o(n.namespace,i,c,[],scope,this))

        elif n.type == "DEFAULTUSECAPTURE":
            check(subnodes=len(n))
            scope.defaultusecapture = n[0].value
            return ""

        elif n.type == "USECAPTURE":
            check(subnodes=len(n))
            scope.usecapture = n[0].value
            return ""

        elif n.type == "FOR_IN":
            check(attrs=["body","iterator","object","isLoop","varDecl","for_each"])
            assert n.isLoop
            if n.varDecl:
                assert n.varDecl.type in ("VAR", "LET")
                assert len(n.varDecl) == 1
                assert n.varDecl[0].type == "IDENTIFIER"
                assert n.varDecl[0].value == n.iterator.value

            letIterator = False
            iteratorName = n.iterator.value
            if getattr(n, 'varDecl', None):
                varDecl = n.varDecl.value 
                if varDecl == 'var':
                    scope.add(iteratorName, n.iterator)
                elif varDecl == 'let':
                    varDecl = 'var'
                    letIterator = True
            else:
                varDecl = ""
            object = o(n.object,i,c,[],scope,this)
            if letIterator: scope.funArgs.append(iteratorName)
            body = o(n.body,i,c,[],scope,this)
            iterator = letIterator and iteratorName or o(n.iterator,i,c,[],scope,this)
            if letIterator: scope.funArgs.pop()

            if n.for_each:
                return "{" + (not letIterator and "%s=" % o(n.iterator,i,c,[],scope,this) or "") + \
                    "(function (ž) {for (var ų in ž) {%s %s = ž[ų]; %s}; return %s})(%s)" % (varDecl, 
                            iterator, body, iterator, object) + "}"
            else:
                # iterator already declared in 'vars'
                if not letIterator: varDecl = ''
                elif varDecl: iterator = iteratorName
                else: iterator = qname(scope,iteratorName, True)
                loop = "for (%s %s in %s) {%s}" % (varDecl, iterator, object, body)
                if letIterator:
                    return ("{(function () {") + loop + "})()}"
                return loop

        elif n.type == "FOR":
            check(attrs=["body","setup","condition","update","isLoop"])
            assert n.isLoop
            lets = []
            scope_ = scope
            if n.setup is not None: 
                if n.setup.type_ == LET:
                    lets.extend([x.name for x in n.setup])
                    scope_ = Scope(scope, {"funArgs":lets})

            if n.setup is not None: setup = o(n.setup,i,c,[],scope_,this)
            else: setup = ""
            if n.condition is not None: condition = o(n.condition,i,c,[],scope_,this)
            else: condition = ""
            if n.update is not None: update = o(n.update,i,c,[],scope_,this)
            else: update = ""
            if n.body is not None: body = o(n.body,i+"  ",c,[],scope_,this)
            else: body = ""

            loop = "for (%s;%s;%s)\n%s{%s}" % (setup, condition,
                    update, i, body)

            if len(lets) > 0:
                return "{(function(%s){%s})()}" % (",".join(lets), loop)
            else:
                return loop

        elif n.type == "DO":
            check(attrs=["body", "condition", "isLoop"])
            assert n.isLoop
            return "do %s while (%s)" % (o(n.body,i,c,[],scope,this), o(n.condition,i,c,[],scope,this))

        elif n.type in ("INCREMENT", "DECREMENT"):
            check(optattrs=["postfix"], subnodes=1)
            if getattr(n, "postfix", False):
                return "%s%s" % (o(n[0],i,c,[],scope,this), n.value) 
            return "%s%s" % (n.value, o(n[0],i,c,[],scope,this))

        elif n.type == "LABEL":
            check(attrs=["label","statement"])
            return "%s:\n  %s%s" % (n.label, i,
                    o(n.statement, i+"  ", c, [],scope,this))

        elif n.type == "ASSIGN":
            check(subnodes=2)

            ns = ""

            assignOp = getattr(n[0],"assignOp", None) and \
                jo.tokens[n[0].assignOp] or \
                ""

            init = o(n[1],i,c,[],scope,this)
            op = o(n[0], i, c, handledattrs=["assignOp"], scope=scope)

            """
            if n[0].type == "IDENTIFIER":
                _op = n[0].value
                if scope.isDefine(_op):
                    raise SyntaxError, "Defined variable %r are read-only" % _op
                elif scope.isInternal(_op):
                    raise SyntaxError, "Invalid left-hand side in assignment"
                elif scope.isVar(_op) and getattr(scope.get(_op), 'readOnly', False):
                    raise SyntaxError, "Constant %r are read-only" % _op
            """

            return "%s%s%s=%s" % (ns, op, assignOp, init)

        elif n.type in ("VAR", "CONST", "LET"):
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ',')

        elif n.type == "IDENTIFIER":
            check(optattrs=["initializer","name","readOnly", "isType", "decl"])
            if getattr(n, "readOnly", False): assert hasattr(n,"initializer")


            """
            if getattr(n, 'isType', None) in ('int', 'uint', 'float', 'string',
                    'bool', 'array', 'object', 'string', 'class', 'function', 'func', 
                    'void', 'dynamic'): 
                Import(root, "jo.basic_types", c)
            """
            if getattr(n, 'isType', None):
                Warning("Type validating is not implemented yet [%s:%s]... skip" % (n.value, n.isType))

            if hasattr(n,"name"): assert n.name == n.value
            if hasattr(n,"initializer"):
                name = qname(scope,n.value, True)
                if name: return "%s=%s" % (name,
                            o(n.initializer, i, c, [],scope,this))
                else: return ""
            return qname(scope,n.value, False)

        elif n.type == "SEMICOLON":
            check(attrs=["expression"])
            if not n.expression: return ""
            return o(n.expression, i, c, [],scope,this) + ""

        elif n.type == "GROUP":
            check(subnodes=1)
            return "(%s)" % o(n[0],i,c,[],scope,this)

        elif n.type == "HOOK":
            check(subnodes=3)
            return "%s?%s:%s" % (o(n[0],i,c,[],scope,this),o(n[1],i,c,[],scope,this),
                    o(n[2],i,c,[],scope,this))

        elif n.type == "CALL":
            check(subnodes=2)
            return "%s(%s)" % (o(n[0],i,c,[],scope,this), o(n[1],i,c,[],scope,this))

        elif n.type in ("BREAK", "CONTINUE"):
            check(attrs=["target"], optattrs=["label"])
            if hasattr(n,"label"):
                return "%s %s" % (n.value, n.label)
            return "%s" % (n.value)

        elif n.type == "COMMA":
            check(subnodes=len(n))
            return string.join((o(x, i, c, [],scope,this) for x in n), ',')

        elif n.type == "LIST":
            check(subnodes=len(n))
            return string.join((o(x, i, c, [],scope,this) for x in n), ',')

        elif n.type in ("NEW_WITH_ARGS", "NEW"):
            check(subnodes=len(n))
            isClass = scope.isClass(n[0].value) 
            args = len(n) > 1 and "(" + o(n[1],i,c,[],scope,this) + ")" or (isClass and "()" or "")
            instance = o(n[0],i,c,[],scope,this)
            new_intance = isClass and "(" + instance + args + ")" or instance + args
            return "new %s" % new_intance

        elif n.type in ("NUMBER", "TRUE", "FALSE", "THIS", "NULL", "UNDEFINED"):
            return str(n.value)

        elif n.type == "PUBLIC":
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ';')

        elif n.type == "PROTECTED":
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ';')

        elif n.type == "PRIVATE":
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ';')

        elif n.type == "GLOBAL":
            check(subnodes=len(n)) 
            return string.join((o(x,i,c,[],scope,this) for x in n), ';')

        elif n.type == "STATIC":
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ';')

        elif n.type == "MACRO":
            check(subnodes=len(n))
            return ""

        elif n.type == "USE":
            check(subnodes=len(n))
            use = string.join(n.value, ' ')
            return "%r" % use

        elif n.type == "INTERNAL":
            check(subnodes=len(n))
            return string.join((o(x,i,c,[],scope,this) for x in n), ',')

        elif n.type == "FUNCTION":
            check(attrs=["lambdaFun","functionForm","params", "body","returnType","decl"],
                    optattrs=["name","isClassConstructor","id"])

            _context = scope.context
            isClassContext = scope.isClassContext
            if scope.isStatic(getattr(n, 'name', None)):
                scope.isClassContext = False
                scope.context = None

            if n.lambdaFun:
                if getattr(n, "isClassConstructor", False): ret = ""
                else: ret = "return "
                expression = o(n.body,i,c,[],scope,this)
                expression = trimRightRe.sub('', expression)
                body = "{%s%s}" % (ret, expression[2:-2])
            else:
                body = len(n.body) > 0 and o(n.body,i,c,[],scope,this) or '{}'

            scope.context = _context
            scope.isClassContext = isClassContext
            
            params = [param.name for param in n.params]

            if n.functionForm == 0:
                if getattr(n, "isClassConstructor", None):
                    fname = "self.New"
                else:
                    fname = qname(scope,n.name,True)
                    """
                    if n.name in subs:
                        fname = subs[n.name]
                    else:
                        fname = qname(scope,n.name, True) 
                    """
                init = fname + "=function"

                return "%s (%s) %s;" % (init,
                        string.join(params, ','),
                        body)
            else:
                return "function (%s) %s;" % (string.join(params, ','),
                        body)

        elif n.type == "RETURN":
            check(attrs=["value"])
            if not n.value: return "return"
            return "return(%s)" % o(n.value, i, c,[],scope,this)

        elif n.type == "PACKAGE":
            check(attrs=["body", "namespace"])

            #ImportInternals(scope, c)

            return "/*package %s*/ " % n.namespace + \
                    Package(n, c, scope, this, n.namespace, i).build()

        elif n.type == "CLASS":
            check(attrs=["body", "name", "classForm",
                    "ancestors", "new", "params", "decl"], 
                  optattrs=["skip", "id", "namespace_", "lazy"])

            #ImportInternals(scope, c)

            #if getattr(n, 'decl', None) == -1:
                #return ""
            
            className = n.name 
            initializer = (getattr(n, 'decl', None) != -1 and className) \
                    and qname(scope,className, True) + "=" or "" 
            return "/*class %s*/ " % className + \
                    initializer + Class(n, c, scope, this,
                            className, scope.namespace, i, n.ancestors).build()

        elif n.type == "WHEN":
            check(attrs=["eventHandler","event"],
                    optattrs=["isLoop"])

            Import(scope, "jo.__event__",  c, None, c['order']+1)
            scope.add("__event__", scope.get("__event__"), True)
            
            useCapture = (scope.usecapture or scope.defaultusecapture)
            useCapture = useCapture and "," + useCapture or ""
            scope.usecapture = None

            if n.event.type in ("ON", "IN", "OVER"):
                event = o(n.event[0],i,c,[],scope,this)
                target = o(n.event[1],i,c,[],scope,this)
            else:
                event = o(n.event,i,c,[],scope,this)
                target = qname(scope,"__event__")
            
            if n.eventHandler:
                if n.eventHandler.type == "IDENTIFIER":
                    handler = n.eventHandler.value
                elif n.eventHandler.type == "BLOCK":
                    scope.funArgs.append("event")
                    handler = "function(event)%s" % o(n.eventHandler,i,c,[],scope,this)
                    scope.funArgs.pop()
            else: handler = "null"

            return "%s.addEventListener(%s,%s%s);" % (target, event, handler, useCapture)

        elif n.type == "DISPATCH":
            check(attrs=["event","eventTarget"])

            Import(scope, "jo.__event__",  c, None, c['order']+1)
            scope.add("__event__", scope.get("__event__"), True)

            target = n.eventTarget and o(n.eventTarget,i,c,[],scope,this) or qname(scope,"__event__")
            event = o(n.event,i,c,[],scope,this)

            return "%s.dispatchEvent(%s);" % (target, event)

        elif n.type in ("PLUS", "LT", "EQ", "AND", "OR", "MINUS", "MUL", "LE",
                "NE", "STRICT_EQ", "DIV", "GE", "INSTANCEOF", "IN", "GT",
                "BITWISE_OR", "BITWISE_AND", "BITWISE_XOR", "STRICT_NE", "LSH",
                "RSH", "URSH", "MOD"):
            check(subnodes=2)
            op = n.value
            if op == 'and': op = '&&'
            elif op == 'or': op = '||'
            elif op == 'is': op = '=='
            return "%s %s %s" % (o(n[0],i,c,[],scope,this), op, o(n[1],i,c,[],scope,this))

        elif n.type == "THROW":
            check(attrs=["exception"])
            return "%s %s" % (n.value, o(n.exception,i,c,[],scope,this))

        elif n.type == "TRY":
            check(attrs=["catchClauses","tryBlock"], optattrs=["finallyBlock"])
            for x in n.catchClauses:
                scope.funArgs.append(x.varName)
            if hasattr(n,"finallyBlock"):
                return "%s\n  " % n.value + i + ("\n  "+i).join(
                        [o(n.tryBlock,i+"  ",c,[],scope,this)] + [o(x,i+"  ",c,[],scope,this)
                        for x in n.catchClauses] + ['finally'] + \
                        [o(n.finallyBlock,i+"  ",c,[],scope,this)])
            return "%s\n  " % n.value  + i + ("\n  "+i).join(
                    [o(n.tryBlock,i+"  ",c,[],scope,this)] + [o(x,i+"  ",c,[],scope,this)
                    for x in n.catchClauses])

        elif n.type == "CATCH":
            check(attrs=["block","guard","varName"])
            if n.guard is not None:
                return "(GUARDED-CATCH%s %s %s %s)" % (props(), n.varName,
                        o(n.guard,i,c,[],scope,this), o(n.block,i,c,[],scope,this))
            return "%s (%s) %s" % (n.value, n.varName, o(n.block,i,c,[],scope,this))

        elif n.type == "NAMESPACE":
            check(attrs=["namespace"])
            #scope.namespace = n.namespace
            return "/*namespace %s*/" % n.namespace

        elif n.type == "IMPORT":
            check(attrs=["externals", "from_", "namespace"])

            #ImportInternals(scope, c)
            exts = []
            #script_root = c['include_props']['script_root']
            ns = this.get('namespace')
            for (ext, alias) in n.externals:
                exts_ = jocore.import_(ext, n.from_ or ns)
                for x in exts_:
                    if x['type'] == 'class':
                        exts.append(x, alias or x['name'])
                """
                if c['order']:
                    #order = c['order'] > 0 and c['order']+1 or c['order']+1
                    order = c['order']+1
                else:
                    order = 0
                Import(scope, ext, c, n.from_ or ns, order, n.namespace)
                modules = getModulesPath(script_root, n.from_, ext, n.namespace)
                for x in modules:
                    as = alias or heap[x]['name']
                    exts.append([heap[x], as])
                """

            return string.join(["%s.%s" % (this_symb, alias) + \
                    "=checkClassHash(%r, %s, %s)" % (x['namespace'] == 'root' and x['name'] or \
                                x['namespace'] + "." + x['name'], 
                            x['hash'], this_symb)
                        for (x, alias) in exts if x['type'] == "class" ], ";\n" + i)

        elif n.type == "IF":
            check(attrs=["condition","thenPart","elsePart"])
            if n.elsePart:
                return "if(%s)\n%s%s\n%selse %s" % (o(n.condition,i,c,[],scope,this), i,
                        o(n.thenPart,i + "  ",c,[],scope,this), i,
                        o(n.elsePart,i, c,[],scope,this))
            return "if (%s)\n%s%s" % (o(n.condition,i,c,[],scope,this), i,
                    o(n.thenPart, i + "  ",c,[],scope,this))

        elif n.type == "TRACE":
            check(subnodes=1)
            Import(scope, "jo.trace", c, None, -100)
            out = o(n[0],i,c,[],scope,this)
            return "__trace__(%s)" % (n[0].type in ("LIST", "GROUP") and out[1:-1] or out)

        elif n.type == "LETEXPRESSION":
            check(attrs=["expression"], subnodes=len(n))
            lets = [k.value for k in n]
            inits = [o(k.initializer,i,c,[],scope,this) for k in n]
            return "(function(%s)" % ",".join(lets) + \
                    "{return(" + o(n.expression,i,c,[],Scope(scope, {"funArgs": lets}),this) + \
                    ")})(%s)" % ",".join(inits)

        elif n.type == "LETSTATEMENTS":
            check(attrs=["statements"], subnodes=len(n))
            lets = [k.value for k in n]
            inits = [o(k.initializer,i,c,[],scope,this) for k in n]
            return "{(function(%s)" % ",".join(lets) + \
                    "" + o(n.statements,i,c,[],Scope(scope, {"funArgs": lets}),this) + \
                    ")(%s)}" % ",".join(inits)

        elif n.type == "TYPE":
            check(attrs=["name", "param", "expression"])

            fname = "is" + n.name[0:1].capitalize() + n.name[1:]
            scope.add(fname, Node(INTERNAL), True)
            this['tree'].scope[fname] = scope.get(fname)
            scope.funArgs.append(n.param)
            t = "%s=function(%s){return %s}" % (fname, n.param, 
                    o(n.expression,i,c,[],scope,this))
            scope.funArgs.pop()

            return t
            
        elif n.type in ("DELETE", "TYPEOF", "UNARY_MINUS", "NOT",
                "VOID", "BITWISE_NOT", "UNARY_PLUS"):
            check(subnodes=1)
            op = n.value
            if op == 'not': op = "!"
            return "%s %s" % (op, o(n[0],i,c,[],scope,this))

        elif n.type == "WHILE":
            check(attrs=["condition","body","isLoop"])
            assert n.isLoop
            return "while (%s)\n%s%s" % (o(n.condition,i,c,[],scope,this), i,
                    o(n.body, i+"  ",c,[],scope,this))

        elif n.type == "SWITCH":
            check(attrs=["cases", "defaultIndex", "discriminant"])
            assert (n.defaultIndex == -1 or
                    n.cases[n.defaultIndex].type == "DEFAULT")
            return "switch (%s)\n  %s{%s}" % (o(n.discriminant,i,c,[],scope,this), i,
                    ("\n  "+i).join(o(x,i+"  ",c,[],scope,this) for x in n.cases))

        elif n.type == "CASE":
            check(attrs=["caseLabel","statements"])
            return "case %s: {%s}" % (o(n.caseLabel,i,c,[],scope,this),
                    o(n.statements,i,c,[],scope,this))

        elif n.type == "DEFAULT":
            check(attrs=["statements"])
            return "default: %s" % o(n.statements,i,c,[],scope,this)

        elif n.type == "SCRIPT":
            check(attrs=["scope", "localScope", "funArgs", "classDecls", "funDecls", 
                         "namespace", "context", "name_"], 
                    optattrs=["funName", "className"], subnodes=len(n))

            if debug: _print("script::", jo.tokens.get(getattr(n, "context", None)), 
                        getattr(n, 'name_', ""), getattr(n, 'namespace', ""))

            _c = {'include_props': c['include_props'], 'order': c['order']}

            #scope_ = Scope(scope, {"namespace": n.namespace, 
                #"context": n.context, "this": this}).extend(n)
            #c['scope'] = scope_

            vars = []
            if n.context == FUNCTION:
                stats = [x for x in n.localScope.keys() if n.localScope[x].decl == STATIC]
                pubs = [x for x in n.localScope.keys() if n.localScope[x].decl == PUBLIC]
                if len(stats):
                    vars.append("%s=%s" % (static_symb, n.name_))
                if len(pubs):
                    vars.append(public_symb +"=this")

            if 'skip_vars' not in c:
                vars.extend([x for x in n.localScope.keys() 
                        if getattr(n.localScope[x], 'decl', None) in (VAR, 
                            LET, CONST, CLASS, FUNCTION)])
            body = ""
            for x in n:
                s = o(x,i+"  ",_c,[],n.scope,this) or ""
                #print type(s), s, x
                body += "  " + i + s + "\n"

            if len(vars):
                vars = "var %s;" % string.join(vars,",")
            else:
                vars = ""

            if len(n) > 0:
                return ("{" + vars + "\n" + \
                        "" + body + i + "}") 
            else:
                return "{}"

        elif n.type == "STRING":
            return '"' + n.value + '"'

        elif n.type == "SKIP":
            #check(optattrs=["body","functionForm",
              #"lambdaFun","name","params","visibility"])
            return ""

        elif n.type == "MAGIC":
            if isinstance(n.value, str): return repr(n.value) 
            elif isinstance(n.value, (int, float, long)): return n.value
            else: return 'null'

        else:
            raise UnknownNode, "Unknown node type %s" % n.type
    except Exception, e:
        had_error = True
        if debug == 1:
            raise OtherError("%s\nException in node %s on line %s" % (e, n.type,
                    getattr(n, "lineno", None)))
        else: raise
    finally:
        if not had_error:
            realkeys = [x for x in dir(n) if x[:2] != "__"]
            for key in realkeys:
                if key not in attrs_:
                    raise ProgrammerError, "key '%s' unchecked on node %s!" % (
                            key, n.type)
            if len(realkeys) != len(attrs_):
                #print (attrs_, realkeys, n)
                for key in attrs_:
                    if key not in realkeys:
                        raise ProgrammerError, ("key '%s' checked "
                                "unnecessarily on node %s!" % (key, n.type))
            if len(subnodes_) != len(n):
                raise ProgrammerError, ("%d subnodes out of %d checked on node "
                        "%s" % (len(subnodes_), len(n), n.type))

def convertTree(this, tab=""):
    """
        Convert parsed tree into javascript code

        Args:
            tree: script tree
            include_props: if true, the expressions have additional information
                included via @ attribute expressions, such as line-number.
            scope: 
            this: 
        Returns:
            nothing
        Raises:
            UnknownNode: if a node hasn't been properly accounted for in the
                conversion
            ProgrammerError: if the conversion routine wasn't written with the best
                understanding of the parse tree
            OtherError: if some other error happened we didn't understand.
    """
    return o(this['tree'], tab, this['params'], [], this['tree'].scope, this)

def convert(tree, scope):
    return o(tree, "", dict(include_props={}, order=0), {}, scope, {})

if __name__ == "__main__":
    try:
        include_props = (sys.argv[1] == "--props")
    except:
        include_props = False

    sys.stdout.write(convert(jo.parse(sys.stdin.read()), include_props))

