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
# JOVM: ECMAScript implementation in Python (with some non-standart extendings).
# ------------------------------------------------------------------------------
# 
# Due to similarity of both languages JOVM is basically wrapping pythonic 
# objects and classes with mimics of javascript behavior.
# Although it is not straightforward implementation of ECMA specs (it is mainly being 
# used for script testing).
#
# < -through line-
# The logic is pretty simple and javascripts should running at near of the speed 
# of native pythonic scripts. >
#
# In JOVM ECMAScript 5 strict mode is used by default, it even 
# not raise StrictError, but syntax or runtime exception, 
# see runtime_test.py::test_ecma_5_strict()
#
# Author: Evgen Burzak <buzzilo@gmail.com>
#
# FIXME new BSD license
# FIXME +inf and -inf
# FIXME eval() evaluated in different context, see runtime_test.py::test_ecma_5_strict()
# TODO  port some of ECMA's 5 cool things, see [0] and [1].
#       [0] http://ejohn.org/blog/ecmascript-5-objects-and-properties/
#       [1] http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/
# TODO  pass Sputnik tests (upd: how many lives will it take?)
# TODO  speed optimizations
#
# Implemented:
# ------------
# __ arithmetic operations: +, -, *, %, ...
# __ bitwise operations: &, |, ^, <<, >>, >>>, ...
# __ comparison: if, else, ==, ===, >, <, >=, ...
# __ loops: while(), do .. while(), for() ...
# __ with statement
# __ try .. catch statement
# __ Math methods: with (Math) abs(), round() ...
#
# Partially implemented:
# ----------------
# __ Date
# __ ...
#
# Not implemented:
# ----------------
# __ ...
#
# Non standard:
# -------------
# __ type 
# __ class
# __ package
# __ namespace
#

from __future__ import division, with_statement
from functools import wraps
from functools import partial
import functools

import re, math, operator
from ctypes import c_int

__all__ = ["JOVM"]

class RuntimeError(Exception): 
    def __init__(self, message="", lineno=-1, 
                    start=0, end=0, filename="", stack=[]):
        Exception.__init__(self, message)
        self.fileName = filename
        self.lineNumber = lineno
        self.name = self.__class__.__name__
        self.stack = stack

    def get (self, key): pass
    def set (self, key, value): pass

    __str__ = lambda self: "%s: %s [%s, %i]" % (self.name, self.message, 
            self.fileName, self.lineNumber)

class NotImplemented_(RuntimeError): pass
class Warning(RuntimeError): pass # raise warnings as exception in strict mode

# ECMAScript exceptions
class ECMAError(RuntimeError): pass
class ReferenceError(ECMAError): pass
#class TypeError_(ECMAError): pass
TypeError_ = type("TypeError", (ECMAError,), {})
#class SyntaxError_(ECMAError): pass
SyntaxError_ = type("SyntaxError", (ECMAError,), {})
#class RangeError_(ECMAError): pass
RangeError_ = type("RangeError", (ECMAError,), {})
class URIError(ECMAError): pass

""" it is part of w3c.xml.dom package
# DOM exceptions
class DOMException(RuntimeError): pass
class EventException(DOMException): pass
class RangeException(DOMException): pass
# ... (?)
"""

class BreakOutOfLoops(Exception): pass
class Continue(Exception): pass

class Null():
    __int__ = lambda self: 0

#
# init
#
def init_(jocore, tokens):
    for tok in tokens:
        globals()[tok] = tokens[tok]
    globals()['tokens'] = tokens
    globals()['jocore'] = jocore

# types aliases
inf = 1e10000
nan = inf / inf
null = Null()
undefined = None
false = False 
true = True 

#
# type checks
#

isString = lambda x: isinstance(x, str)
isInt = lambda x: isinstance(x, int)
isFloat = lambda x: isinstance(x, float)
isNumber = lambda x: isinstance(x, (int, float, long)) and not isBoolean(x)
isInfinity = lambda x: x == float("+inf") or x == float("-inf")
# as far as i know NaN is th only value that yields false when compared
# to itself. 
isNaN = lambda x: x != x
isUndefined = lambda x: x == None
isNull = lambda x: id(null) == id(x)
isBoolean = lambda x: isinstance(x, bool) or hasattr(x, '__isbool__')
isObject = lambda x: isinstance(x, (VM_Object))
isFunction = lambda x: callable(x)
isXML = lambda x: isinstance(x, XML) or isinstance(x, XMLList)
isArray = lambda x: isinstance(x, array_proto)

#
# conversion routines
#
intRe = re.compile(r'^(-|\+)?\d+$')
floatRe = re.compile(r'^(-|\+)?(\d+)?\.(\d+)$')
shortFloatRe = re.compile(r'^(-|\+)?(\d+)\.(\d+)e\+(\d+)$')
hexRe = re.compile(r'^(-|\+)?0x([0-9a-fA-F]+)$')

def toNumber(y):
    x = None
    if isNumber(y): x = y
    elif isBoolean(y): x = int(y)
    elif isString(y):
        if y == "":
            x = 0
        else:
            # there is some internal pythonic types like nan and +inf,-inf
            # it may be passed in strings, so using regexp to check
            m = re.match(intRe, y)
            if m: x = int(y)
            else:
                m = re.match(floatRe, y)
                if m: 
                    x = float(y)
                else:
                    m = re.match(shortFloatRe, y)
                    if m:
                        x = float(y)
                    else:
                        m = re.match(hexRe, y)
                        if m: x = int(y, 16)
                        else:
                            x = nan
            """
            try: 
                x = int(y)
            except ValueError:
                try: 
                    x = float(y)
                except ValueError:
                    try:
                        if re.match(hexRe, y): x = int(y, 16)
                        else: x = nan
                    except ValueError: 
                        x = nan
            """
    elif isNull(y):
        x = 0
    elif isObject(y):
        x = toNumber(str_(y))
    else:
        x = nan

    #jocore.warning(", ".join([str(type(y)), str(y), str(x)]))

    # reflects javascript behavior
    return (x >= 0xfffffffffffffffffff or isinstance(x, long)) \
            and float(x) or x

def toInt(y):
    x = toNumber(y)
    if isInfinity(x): return x
    return not isNaN(x) and int(x) or nan

# convertJOVMInternalObjectIntoPythonicNatives()
#
def convert(obj):

    if isinstance(obj, number_proto_):
        if isFloat(obj): return float(obj)
        elif isInt(obj): return int(obj)
    elif isinstance(obj, string_proto):
        return str(obj)
    elif isinstance(obj, object_proto) or isinstance(obj, Globals):
        return dict([[k, convert(v)] for k, v in obj])
    elif isinstance(obj, array_proto):
        return [convert(v) for v in list.__iter__(obj)]
    elif isinstance(obj, func_proto):
        return obj
    elif isinstance(obj, prototype):
        return dict([[k, convert(v)] for k, v in obj])
    elif isinstance(obj, Null): 
        return None

    return obj

def ustr(s):
    if isinstance(s, unicode):
        return s.encode(jocore.encoding)
    else:
        return str(s)

def object_prio(obj):
    if isBoolean(obj): return 800
    if isNumber(obj): return 900
    if isArray(obj): return 400
    if isFunction(obj): return 1000
    if isObject(obj): return 500
    #if isString(obj): return 300

def str_(x):
    if isNull(x): return 'null'
    elif isUndefined(x): return 'undefined'
    elif isNaN(x): return 'NaN'
    elif isBoolean(x): return x and 'true' or 'false'
    elif isInfinity(x): 
        if x > 0: return 'Infinity'
        else: return '-Infinity'
    else: 
        if isinstance(x, unicode):
            return ustr(x)
        return str(x)

def int32(x): 
    if isFloat(x): return 0
    else: return c_int(x).value

def typeof(x):
    if isUndefined(x): return 'undefined' 
    elif isFunction(x): return 'function' 
    elif isNull(x): return 'object' 
    elif isObject(x): return 'object' 
    elif isNumber(x): return 'number' 
    elif isString(x): return 'string' 
    elif isBoolean(x): return 'boolean' 
    elif isXML(x): return 'xml' 
    else: return 'object'

# public function decorator
def public(f):
    return staticmethod(f)

def object_iter(obj):
    for k, v in obj.__dict__.iteritems():
        yield (k, v)

interns = ["__init__", "__setitem__", "__getitem__", "__getattr__",
        "__setattr__", "__getattribute__", "__str__", "__repr__", 
        "__iter__", "__dict__"] # "toString", "valueOf"

#
# VM object prototype
#
class VM_Object(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __setitem__(self, k, v):
        self.__setattr__(k, v)

    def __getitem__(self, k):
        return getattr(self, k)

    def __setattr__(self, k, v):
        #print self, "setattr()", k, v
        if k in interns: return
        object.__setattr__(self, str_(k), v)

    """
    def __getattr__(self, k):
        print self, "getattr()", k
        return object.__getattr__(self, k)
        #self.__dict__.get(k) 
    """

    def __delattr__(self, k):
        #print self, "delattr()", k
        if k in interns: return
        object.__delattr__(self, k)

    __iter__ = lambda self: object_iter(self)

    toString = public(lambda self: self.__str__())

    @staticmethod
    def valueOf(self): 
        """Returns the primitive value of the specified object. Overrides the Object.valueOf method."""
        return

    __str__ = lambda self: "[object "+self.__class__.__name__+"]"
    __repr__ = lambda self: self.__class__.__name__
    __contains__ = lambda self, item: item in self.__dict__

# 
# VM_Context
#
class VM_Context(object):
    def __init__(self, **kwargs):
        self.init(**kwargs)
        self.___cached_scope = {}

    def init(self, context=None, parent=None, scope=None):
        if scope == None:
            self.scope = {}
        else:
            self.scope = scope
        self.stack = []
        self.context = context
        self.returnValue = None
        if parent:
            self.parent = parent
            self.globals = parent.globals
            self.strict = parent.strict
        else:
            self.parent = None

    strict = False
    returnValue = None

    def eval(self, n):
        #print n
        this = self.context
        if isNull(n) or isUndefined(n) \
            or isString(n) or isNumber(n): 
                return n

        t = n.type_
        try:
            if t == NUMBER: return toNumber(n.value)
            elif t == STRING: return n.value
            elif t == SEMICOLON: 
                if n.expression: 
                    return self.eval(n.expression)

            elif t == IDENTIFIER: return self.get_(n)
            elif t == ASSIGN: 
                leftExpr = n[0]
                rightExpr = n[1]
                assignOp = n[0].assignOp
                return self.assign(leftExpr, rightExpr, assignOp)
                """
                tt = leftExpr.type_
                if tt == IDENTIFIER:
                    k = ustr(leftExpr.value)
                    ctx = self
                    while ctx:
                        if k in ctx.scope: break
                        ctx = ctx.parent
                    else:
                        ctx = root_context
                    if assignOp:
                        x = self.var(k, n)
                        y = self.eval(rightExpr)
                        #self.scope[k] = self.assignOp(x, y, assignOp)
                        #value = self.assign(k, self.assignOp(x, y, assignOp))
                        ctx.scope[k] = self.assignOp(x, y, assignOp)
                    else:
                        #self.scope[k] = self.eval(rightExpr)
                        #value = self.assign(k, self.eval(rightExpr))
                        ctx.scope[k] = self.eval(rightExpr)
                    return ctx.scope[k]
                elif tt in (DOT, INDEX):
                    obj = self.object(leftExpr)
                    prop = self.property(leftExpr)
                    if isUndefined(obj) or isNull(obj):
                        self.err(TypeError_, "cannot set property "
                                    "%r of %s" % (prop, str_(obj)), n)
                    val = self.eval(rightExpr)
                    if assignOp: 
                        if tt == DOT:
                            try:
                                x = getattr(obj, prop)
                            except AttributeError, e:
                                x = undefined
                                self.undefPropErr(prop, n)
                        else:  # INDEX
                            try:
                                x = operator.getitem(obj, prop)
                            except (IndexError, AttributeError), e:
                                x = undefined
                                self.undefPropErr(prop, n)
                        val = self.assignOp(x, val, assignOp)
                    #print "!!", obj, prop, val
                    if tt == DOT:
                        setattr(obj, prop, val)
                    else:
                        operator.setitem(obj, prop, val)
                    return val
                """

            elif n.type_ in (VAR, LET, CONST, GLOBAL, STATIC, PUBLIC, 
                    PROTECTED, PRIVATE, MACRO, INTERNAL):
                for x in n:
                    self.initVar(ustr(x.value), 
                            self.eval(getattr(x, 'initializer', undefined)))
                return None

            elif t == UNARY_PLUS: return +toNumber(self.eval(n[0]))
            elif t == UNARY_MINUS: return -toNumber(self.eval(n[0]))
            elif t in (PLUS, MINUS, DIV, MUL, MOD): 
                a = self.eval(n[0])
                b = self.eval(n[1])
                #print t, a, b
                if t == PLUS and (isString(a) or isString(b)):
                    return str_(a) + str_(b)
                else:
                    return self.arithmOp(toNumber(a), toNumber(b), t)

            elif t == BITWISE_NOT:
                try: 
                    return ~toInt(self.eval(n[0]))
                except TypeError:
                    return ~0

            elif t in (BITWISE_OR, BITWISE_AND, BITWISE_XOR,
                    URSH, RSH, LSH):
                a = toInt(self.eval(n[0]))
                b = toInt(self.eval(n[1]))
                return self.bitwiseOp(a, b, t)

            # Warning! This operated on the same scope. 
            # You must create new VM_Context instance in your own class!
            elif t == SCRIPT: 
                if not len(n): return None
                for x in n[0:-1]:
                    self.eval(x)
                return convert(self.eval(n[-1:][0]))

            elif t == GROUP: return self.eval(n[0])
            elif t == (BLOCK, COMMA): 
                for x in n: 
                    last = self.eval(x)
                return last

            elif t == ARRAY_INIT: 
                return array_proto(*[self.eval(x) for x in n])

            elif t == OBJECT_INIT: 
                kwargs = dict([[ustr(x[0].value), self.eval(x[1])]
                    for x in n if x.type_ == PROPERTY_INIT])
                return object_proto(**kwargs)

            elif t in (DOT, INDEX): return self.get_(n)
            elif t == FUNCTION: return self.funDef(n)
            elif t == CLASS: return self.classDef(n)

            elif t in (NEW, NEW_WITH_ARGS, CALL): 
                #print n
                if n[0].type_ in (DOT, INDEX):
                    this = self.object(n[0])
                fun = self.eval(n[0])
                if t in (NEW_WITH_ARGS, CALL):
                    args = [self.eval(x) for x in n[1]]
                if callable(fun):
                    if t == NEW:
                        return fun.__newInstance__()
                    elif t == NEW_WITH_ARGS:
                        return fun.__newInstance__(*args)
                    else:
                        return fun(this, *args)
                else:
                    self.err(TypeError_, "%s is not a function" % str_(fun), n)

            elif t == RETURN: 
                self.returnValue = self.eval(n.value)
                raise BreakOutOfLoops

            elif t == FOR_IN: 
                self.for_in(ustr(n.iterator.value), 
                        self.eval(n.object), n.body)

            elif t == FOR: 
                self.for_(n.setup, n.condition, n.update, n.body)

            elif t == INCREMENT:
                x = self.get_(n[0])
                y = 1
                self.assign(n[0], self.assignOp(x, 1, PLUS))
                return x

            elif t == DECREMENT: 
                x = self.get_(n[0])
                self.assign(n[0], x+1)
                return x

            elif t == IF: 
                if self.compare(n.condition):
                    self.eval(n.thenPart)
                elif n.elsePart:
                    self.eval(n.elsePart)

            elif t == NOT:
                return not self.eval(n[0])
                
            elif t == AND:
                return self.compare(n[0]) and self.compare(n[1])

            elif t == OR:
                return self.compare(n[0]) or self.compare(n[1])

            elif t in (GT, LT, EQ, NE, GE, LE, 
                    STRICT_EQ, STRICT_NE): 
                return self.compare(n)

            elif t == NULL: return null
            elif t == TRUE: return True
            elif t == FALSE: return False
            elif t == UNDEFINED: return undefined
            elif t == VOID: 
                self.eval(n[0])
                return undefined

            elif t == IN:
                return self.eval(n[0]) in self.eval(n[1])

            elif t == THIS: return this

            elif t == TYPEOF: 
                return typeof(self.eval(n[0]))

            elif t == USE:
                if n.value == 'strict':
                    self.strict = True

            elif t == DELETE: 
                delattr(self.object(n[0]), self.property(n[0]))

            else:
                self.err(NotImplemented_, n.type, n)

        except (BreakOutOfLoops, Continue), ex: 
            raise ex.__class__

        except (TypeError_, ReferenceError, NotImplemented_), ex:
            raise

        except Exception, ex:
            #self.err(RuntimeError, ex.message, n)
            raise

    # assign value
    #
    def assign(self, leftExpr, rightExpr, assignOp=None, local=False): 
        """
        if getattr(args[0], 'type_', None) == IDENTIFIER:
            var = ustr(args[0].value)
            self.var(var, args[0])
        elif isString(args[0]):
            var = args[0]
        else:
            raise RuntimeError, "Panic! " + str(args[0])
        value = args[1]
        ctx = self
        print var , value
        while ctx:
            if var in ctx.scope:
                ctx.scope[var] = value
            ctx = ctx.parent
        else:
            self.globals[var] = value
        return value
        """

        #print leftExpr, rightExpr
        tt = leftExpr.type_
        if tt == IDENTIFIER:
            k = ustr(leftExpr.value)
            ctx = self
            if local == False:
                while ctx:
                    if k in ctx.scope: break
                    ctx = ctx.parent
                else:
                    ctx = root_context
            if assignOp:
                x = self.var(k, leftExpr)
                y = self.eval(rightExpr)
                #self.scope[k] = self.assignOp(x, y, assignOp)
                #value = self.assign(k, self.assignOp(x, y, assignOp))
                ctx.scope[k] = self.assignOp(x, y, assignOp)
            else:
                #self.scope[k] = self.eval(rightExpr)
                #value = self.assign(k, self.eval(rightExpr))
                ctx.scope[k] = self.eval(rightExpr)
            return ctx.scope[k]
        elif tt in (DOT, INDEX):
            obj = self.object(leftExpr)
            prop = self.property(leftExpr)
            if isUndefined(obj) or isNull(obj):
                self.err(TypeError_, "cannot set property "
                            "%r of %s" % (prop, str_(obj)), n)
            val = self.eval(rightExpr)
            if assignOp: 
                if tt == DOT:
                    try:
                        x = getattr(obj, prop)
                    except AttributeError, e:
                        x = undefined
                        #self.undefPropErr(prop, n)
                else:  # INDEX
                    try:
                        x = operator.getitem(obj, prop)
                    except (IndexError, AttributeError), e:
                        x = undefined
                        #self.undefPropErr(prop, n)
                val = self.assignOp(x, val, assignOp)
            #print "!!", obj, prop, val
            if tt == DOT:
                setattr(obj, prop, val)
            else:
                operator.setitem(obj, prop, val)
            return val


    # get identifier or object property
    #
    def get_(self, n):
        if n.type_ == IDENTIFIER: 
            return self.var(ustr(n.value), n)

        else: # => t in (DOT, INDEX)
            head = self.object(n)
            tail = self.property(n)

            if isNull(head) or isUndefined(head):
                self.err(TypeError_, "cannot read property "
                          "%r of %s" % (getattr(tail, 'value', tail), str_(head)), n)

            #obj = getattr(head, str_(tail), undefined)
            if n.type_ == DOT:
                try:
                    obj = getattr(head, str_(tail))
                except AttributeError, e:
                    obj = undefined
                    #self.undefPropErr(tail, n)
            else: # INDEX
                try:
                    obj = operator.getitem(head, tail)
                except (IndexError, AttributeError), e:
                    obj = undefined
                    #self.undefPropErr(tail, n)

            return obj


    # build actual scope
    #
    def actualScope(self):
        scope = {}
        par = self.parent
        branch = [self]
        while par:
            branch.append(par)
            par = par.parent
        branch.reverse()
        for p in branch:
            scope.update(p.scope)
        return scope

    def __getitem__(self, k):
        return self.actualScope().get(k)

    # get variable from scope
    #
    def var(self, var, n):
        value = None
        scope = self.actualScope()
        """
        scope = {}
        par = self.parent
        branch = [self]
        while par:
            branch.append(par)
            par = par.parent
        branch.reverse()
        for p in branch:
            scope.update(p.scope)
        """
        if var == 'Infinity':
            return inf
        elif var == 'NaN':
            return nan
        elif var in scope:
            value = scope[var]
        elif var in globals_:
            value = globals_.get(var)
        elif hasattr(self.globals, var):
            value = getattr(self.globals, var)
        else:
            self.err(ReferenceError, "%s is not defined" % var, n)
        
        #if isinstance(value, (Undefined, NaN, Null)):
            #self.warn("%s is %s" % (var, str(value)), n)

        #print "var()", var, str(value)
        return value
    
    # get object
    #
    def object(self, n):
        """ returns object from INDEX and DOT nodes 
            or build new from prototype for certain types
        """ 
        obj = self.eval(n[0])
        if isObject(obj): return obj
        elif isBoolean(obj): return bool_proto()
        elif isNumber(obj) or isInfinity(obj) or isNaN(obj): 
            return number_proto(obj)
        elif isString(obj): return string_proto(obj)
        return obj

    # get property
    #
    def property(self, n):
        if n.type_ == INDEX:
            return self.eval(n[1])
        elif n.type_ == DOT:
            if n[1].type_ == IDENTIFIER:
                return ustr(n[1].value)
            else:
                raise NotImplemented_, str(n[1])

    # arithmetic operations
    #
    def arithmOp(self, x, y, op):
        try:
            if op == PLUS: 
                if isString(x) or isString(y):
                    x = str_(x) + str_(y)
                else: x += y
            elif op == MINUS: x -= y
            elif op == MUL: x *= y
            elif op == DIV: x /= y
            elif op == MOD:
                # there is difference between py and js modulo interpretation
                # http://stackoverflow.com/questions/43775/modulus-operation-with-negatives-values-weird-thing
                if (x > 0 and y > 0): x = abs(x) % abs(y)
                elif (x < 0 and y < 0): x = -(abs(x) % abs(y))
                elif x < 0: x = -(abs(x) % abs(y))
                else: x = abs(x) % abs(y)
            else: self.err(NotImplemented_, "arithmOp(): %s" % op)
        except TypeError, e:
           x = nan
        except ZeroDivisionError, e:
           if op == MOD: 
               x = nan
           else: 
               # FIXME +0 and -0
               #print "!", x, y, (x < 0 or y < 0)
               x = (x < 0 or y < 0) and -inf or inf

        # reflects javascript behavior
        if isNumber(x) and x >= 0xfffffffffffffffffff: 
            x = float(x)

        return x

    # bitwise operations
    #
    def bitwiseOp(self, x, y, op):
        """in javascript, bitwise operators yields int32 
        """
        if isInfinity(x): x = 0
        if isInfinity(y) and op != URSH: y = 0
        try:
            if op == BITWISE_OR: 
                x = int32(int(x) | int(y))
            elif op == BITWISE_XOR: 
                x = int32(int(x) ^ int(y))
            elif op == BITWISE_AND: 
                x = int32(int32(x) & int(y))
            elif op == LSH: 
                x = int32(int32(x) << (int(y) & 0x1f))
            elif op == URSH: 
                if isFloat(y) or y >= 0xffffffff or y <= -0xffffffff:
                    return int(int(x) & 0xffffffff)
                x = int32((int32(x) & 0xFFFFFFFFL) >> (int(y) & 0x1f))
            elif op == RSH: 
                x = int32(int32(x) >> (int(y) & 0x1f))
            else: 
                self.err(NotImplemented_, "bitwiseOp(): %s" % op)
        except TypeError, e:
            print "bitwiseOp(): TypeError", str(x), op, str(y), e.message
            x = 0

        return x

    def assignOp(self, x, y, op):
        #print "assignOp()", x, y, op
        if op in (BITWISE_OR, BITWISE_AND, BITWISE_XOR, 
                        BITWISE_NOT, URSH, RSH, LSH):
            return self.bitwiseOp(x, y, op)
        else:
            return self.arithmOp(x, y, op)

    def funDef(self, f):
        #args = id(self.this) == id(self.globals) and [self.this] or []
        #print "funDef()", id(self.this) == id(self.globals)
        fun = function(self, f)
        if f.functionForm == 0:
            #self.scope[f.name] = fun
            #return self.assign(ustr(f.name), fun, local=True)
            fname = ustr(f.name)
            self.scope[fname] = fun
            return self.scope[fname]
        return fun

    def classDef(self, c):
        cls = buildClass(self, c)
        if c.classForm == 0:
            #return self.assign(ustr(c.name), cls, local=True)
            cname = ustr(c.name)
            self.scope[cname ] = cls
            return self.scope[cname ]
        return cls

    def initVar(self, var, value):
        if id(self) == id(root_context):
            self.globals[var] = value
        else:
            self.scope[var] = value

    def while_(self, cond, body):
        while self.compare(cond):
            try: 
                self.eval(body)
            except BreakOutOfLoops, e: break
            except Continue, e: continue
            except Exception: raise

    def for_(self, setup, cond, update, body):
        self.eval(setup)
        while self.compare(cond):
            try:
                self.eval(update)
                self.eval(body)
            except BreakOutOfLoops, e: break
            except Continue, e: continue
            except Exception: raise

    def for_in(self, iterator, object, body):
        for k, v in object:
            try:
                self.assign(iterator, k)
                self.eval(body)
            except BreakOutOfLoops, e: break
            except Continue, e: continue
            except Exception: raise

    def compare(self, n):
        #print "compare()", n

        t = n.type_
        if t in (GT, LT, EQ, NE, GE, LE, 
                STRICT_EQ, STRICT_NE):
            a = self.eval(n[0])
            b = self.eval(n[1])
            # reflect javascript behavior
            #
            if isNaN(a) and isNaN(b):
                return t in (NE, STRICT_NE)
            elif isNull(a) or isNull(b):
                if t in (EQ, STRICT_EQ):
                    return isNull(a) and isNull(b)
                elif t in (NE, STRICT_NE):
                    return not (isNull(a) and isNull(b))
                a = toNumber(a)
                b = toNumber(b)
            elif isObject(a) and isObject(b):
                #print a, b
                if t in (STRICT_EQ, EQ):
                    return id(a) == id(b)
                elif t in (STRICT_NE, NE):
                    return id(a) != id(b)
                else:
                    x = object_prio(a)
                    y = object_prio(b)
                    if (isNumber(a) or isNumber(b) \
                            or isBoolean(a) or isBoolean(b)) and x != y:
                        a = toNumber(a)
                        b = toNumber(b)
                    elif x == y:
                        a = str_(a)
                        b = str_(b)
                    else:
                        a = x
                        b = y
                    #print a, b, x, y
            elif t not in (STRICT_EQ, STRICT_NE):
                if isNumber(a) or isNumber(b) \
                        or isBoolean(a) or isBoolean(b):
                    a = toNumber(a)
                    b = toNumber(b)
                elif isString(a) or isString(b):
                    a = str_(a)
                    b = str_(b)
        else:
            return self.eval(n)


        if t == GT: return a > b 
        elif t == LT: return a < b 
        elif t == EQ: return a == b 
        elif t == NE: return a != b 
        elif t == GE: return a >= b 
        elif t == LE: return a <= b 
        elif t == STRICT_EQ:
            return a == b and type(a) == type(b)
        elif t == STRICT_NE: 
            return not(a == b) or not type(a) == type(b)

    def undefPropErr(self, prop, n):
        err = "undefined object property %s" % getattr(prop, 'value', prop)
        if self.strict:
            raise RuntimeError, err
        self.warn(err, n)

    def err(self, ex, msg, n=None):
        if n:
            raise ex(msg, n.lineno, n.start, n.end, n.filename, self.stack)
        else:
            raise ex(msg, 0, 0, 0, "", self.stack)

    def warn(self, msg, n):
        jocore.warning(msg, n.lineno)

# = = = = = = = = = = = = = = = 
#   prototype implementation
# = = = = = = = = = = = = = = = 
# FIXME, Note
# Regarding to tests Object.prototype.__proto__ is real prototype object, 
# but in JOVM it just link to String.prototype
class prototype(VM_Object):
    """ prototype ...
        the first initialized class will become prototype
    """ 
    def __init__(self):
        #print "prototype.__init__()", getattr(self, "__proto__", None)
        """
        if self.__proto__ == None: 
            self.__proto__ = self
            #self.__proto__ = self.__class__
            self.__class__.__proto__ = self.__proto__
        else:
        """
        if hasattr(self, '__proto__'):
            for k, v in object_iter(self.__proto__):
                #print "%", k, v
                setattr(self, k, v)
    
    def __getattr__(self, k):
        if k == 'constructor': return None
        elif k == '__proto__': return self
        raise AttributeError, self.__class__.__name__ + ", " + k

    """
    def __setattr__(self, k, v):
        cls = self.__class__
        #print cls, "setattr()", k, v, id(cls.__proto__) == id(self)
        if id(cls.__proto__) == id(self):
            setattr(cls, k, v)
        else:
            VM_Object.__setattr__(self, k, v)
    """

    """
    def __getattr__(self, k):
        cls = self.__class__
        print cls, "getattr()", k
        #if id(cls.__proto__) == id(self):
            #return getattr(cls, k)
        #else:
            #return self.__dict__.get(k)
            #if k in self.__dict__: return self.__dict__[k]
            #else: return undefined
    """
    
    __iter__ = lambda self: object_iter(self)

    def __delattr__(self, k):
        cls = self.__class__
        #print cls, "delattr()", k
        if k == '__proto__' and \
                id(self.__proto__) == id(self): pass
        else:
            if id(cls.__proto__) == id(self):
                delattr(self.__class__, k)
            else:
                VM_Object.__delattr__(self, k)

# = = = = = = = = = = = = = = = 
#           numbers
# = = = = = = = = = = = = = = = 
# number prototype
# note: to make it work there is two classes for float and int
class number_proto_(prototype):
    def __init__(self, x=0):
        prototype.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return number
        elif k == '__proto__': return number_prototype
        else: return prototype.__getattr__(self, k)

def number_proto(x):
    if isInt(x):
        return type("<int %s>" % x, (int, number_proto_), {}) (x)
    if isFloat(x):
        return type("<float %s>" % x, (float, number_proto_), {}) (x)

number_prototype = number_proto(0)

#
# Number object
# 
class Number(VM_Object):
    def __init__(self):
        VM_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: number_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return number_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        # Number.prototype returns 0 so we should to do this test
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return toNumber(str_(args[0]))
        return 0
        #type("<" + (len(args) and str(args[0]) or "0") + ">", (number_proto,), {}) 
        
# = = = = = = = = = = = = = = = 
#           strings
# = = = = = = = = = = = = = = = 
# string prototype
class string_proto(str, prototype):
    def __init__(self, s=""):
        str.__init__(self, s)
        prototype.__init__(self)
    
    # strings is not allowed setting chars by index
    def __setitem__(self, i, v): 
        if id(self) == id(self.__proto__):
            object.__setattr__(self, i, v)
        else: pass

    def __getitem__(self, i, j=None):
        if j is not None:
            return str.__getitem__(self, slice(i, j))
        else:
            if isNumber(i):
                if i < 0: return undefined
                try:
                    return str.__getitem__(self, i)
                except IndexError, e:
                    return undefined
            else:
                return getattr(self, str_(i))

    def __getattr__(self, k):
        if k == 'length': return len(self)
        elif k == 'constructor': return string
        elif k == '__proto__': return string_prototype
        else: return prototype.__getattr__(self, k)

    @public
    def substr(self, start=None, n=None):
        """Returns the characters in a string beginning at the specified location through the specified number of characters."""
        #print "substr()", self, start, n
        s = str_(self)
        if start == None and n == None: return s
        else:
            if start == None: start = 0
            else: start = toNumber(start)
            if n == None: end = len(s) 
            else: end = toNumber(n)
            if end < 0: return ''
            if start > 0 and end < 0 and n != None: return ''
            if end > len(s): end = len(s)
            #print start, end
            return s[start:start+end]

    @public
    def split(self, sep=None):
        """Splits a String object into an array of strings by separating the string into substrings."""
        return self.split(sep)

    """
    charAt
        Returns the character at the specified index.
    charCodeAt
        Returns a number indicating the Unicode value of the character at the given index.
    concat
        Combines the text of two strings and returns a new string.
    indexOf
        Returns the index within the calling String object of the first occurrence of the specified value, or -1 if not found.
    lastIndexOf
        Returns the index within the calling String object of the last occurrence of the specified value, or -1 if not found.
    localeCompare
        Returns a number indicating whether a reference string comes before or after or is the same as the given string in sort order.
    match
        Used to match a regular expression against a string.
    quote
        Non-standard
        Wraps the string in double quotes ('"').
    replace
        Used to find a match between a regular expression and a string, and to replace the matched substring with a new substring.
    search
        Executes the search for a match between a regular expression and a specified string.
    slice
        Extracts a section of a string and returns a new string.
    split
        Splits a String object into an array of strings by separating the string into substrings.
    substr
        Returns the characters in a string beginning at the specified location through the specified number of characters.
    substring
        Returns the characters in a string between two indexes into the string.
    toLocaleLowerCase
        The characters within a string are converted to lower case while respecting the current locale. For most languages, this will return the same as toLowerCase.
    toLocaleUpperCase
        The characters within a string are converted to upper case while respecting the current locale. For most languages, this will return the same as toUpperCase.
    toLowerCase
        Returns the calling string value converted to lower case.
    toSource
        Non-standard
        Returns an object literal representing the specified object; you can use this value to create a new object. Overrides the Object.toSource method.
    toString
        Returns a string representing the specified object. Overrides the Object.toString method.
    toUpperCase
        Returns the calling string value converted to uppercase.
    trim
        New in Firefox 3.5 Non-standard
        Trims whitespace from the beginning and end of the string.
    trimLeft
        New in Firefox 3.5 Non-standard
        Trims whitespace from the left side of the string.
    trimRight
        New in Firefox 3.5 Non-standard
        Trims whitespace from the right side of the string.
    """

string_prototype = string_proto()

#
# String object
#
class String(VM_Object):
    def __init__(self, s=''):
        str.__init__(self)
        #self.prototype.constructor = self
        
    prototype = property(lambda self: string_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return string_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return str_(args[0])
        return str_("")

# = = = = = = = = = = = = = = = 
#           boolean
# = = = = = = = = = = = = = = = 
# boolean prototype
# note: bool class cannot be extended so boolean type is emulated
class bool_proto(int, prototype):
    #__isbool__ = True
    def __init__(self, x=0):
        int.__init__(self, int(x))
        prototype.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return boolean
        elif k == '__proto__': return bool_prototype
        elif k == '__isbool__': return True
        else: return prototype.__getattr__(self, k)

bool_prototype = bool_proto()

#
# Boolean object
#
class Boolean(VM_Object):
    def __init__(self):
        VM_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: bool_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return bool_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return bool(args[0])
        return false

# = = = = = = = = = = = = = = = 
#            object
# = = = = = = = = = = = = = = = 
# object prototype
class object_proto(prototype):
    def __init__(self, **kwargs):
        prototype.__init__(self)
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __getattr__(self, k):
        if k == 'constructor': return object_
        elif k == '__proto__': return object_prototype
        else: return prototype.__getattr__(self, k)

    __str__ = lambda self: "[object Object]"

object_prototype = object_proto()

#
# Object
#
class Object(VM_Object):
    def __init__(self):
        VM_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: object_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

    def __call__(self, this, *args):
        if len(args):
            t = args[0]
            if isString(t): return string.__newInstance__(t)
            elif isNumber(t): 
                #print "!", t
                return number.__newInstance__(t)
            elif isBoolean(t): 
                return boolean.__newInstance__(t)
            # new Object(obj) could be returning copy of objects, but unlucky monkeys...
            else: 
                return args[0]
        return object_proto()

# = = = = = = = = = = = = = = = 
#            array
# = = = = = = = = = = = = = = = 
# array prototype
class array_proto(list, prototype):
    def __init__(self, *args):
        list.__init__(self, args)
        prototype.__init__(self)

    def __setitem__(self, i, value):
        #if id(self.__proto__) == id(self):
            #prototype.__setitem__(self, i, value)
        if isNull(i): index = "null"
        elif isUndefined(i): index = "undefined"
        else: index = toNumber(i)
        if isInt(index) and index >= 0:
            if index > len(self)-1:
                arr = list(self)
                list.__setitem__(self, slice(0, index + 1), [None] * (index + 1))
                list.__setitem__(self, slice(0, len(arr)), arr)
            list.__setitem__(self, index, value)
        else:
            setattr(self, str_(i), value)

    def __getitem__(self, i):
        #if id(self.__proto__) == id(self):
            #prototype.__getitem__(self, i)
        if isNull(i): index = "null"
        elif isUndefined(i): index = "undefined"
        else: index = toNumber(i)
        if isInt(index) and index >= 0:
            if index >= len(self):
                # reflected JS behavior, get value of prototype
                return list.__getitem__(self.__proto__, index)
            return list.__getitem__(self, index)
        return getattr(self, str_(i))

    def __getattr__(self, k):
        if k == 'length': return len(self)
        elif k == 'constructor': return array
        elif k == '__proto__': return array_prototype
        else: return prototype.__getattr__(self, k)

    @public
    def push(self, x): 
        list.append(self, x)
        return x

    @public
    def pop(self): return list.pop(self)

    __iter__ = lambda self: array_iter(self)
    """
    if id(self.__proto__) == id(self):
        return object_iter(self)
    return list.__iter__(self)
    """

    __str__ = lambda self: ",".join([str_(x)
                  for x in list.__iter__(self)])

array_prototype = array_proto()

def array_iter(arr):
    collect = list()
    i = 0
    for x in list.__iter__(arr):
        collect.append((str(i), x))
        i+=1
    collect.extend(arr.__dict__.items())
    for k, v in collect:
        yield (k, v)

#
# Array
#
class Array(VM_Object): 
    def __init__(self):
        VM_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: array_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __getattr__(self, k):
        if k == 'constructor': return array
        elif k == '__proto__': return array_prototype
        else: prototype.__getattr__(self, k)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            if len(args) == 1:
                if isNumber(args[0]):
                    if args[0] < 0 or isNaN(args[0]) or \
                            isInfinity(args[0]) or isFloat(args[0]): 
                        raise RangeError_, "Invalid array length"
                    _args = [None] * args[0]
                    return array_proto(*_args)
                else:
                    return array_proto(*args)
            else:
                return array_proto(*args)
        else:
            return array_proto()

# = = = = = = = = = = = = = = = 
#           function
# = = = = = = = = = = = = = = = 
# function prototype
# Note: constructor return some object or class instance
# FIXME fun.__proto__ and fun.prototype.__proto__ is against specs
class func_proto(prototype):
    def __init__(self):
        prototype.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return function_
        elif k == '__proto__': return func_prototype
        else: return prototype.__getattr__(self, k)

    @public
    def call(this, context=None, *args):
        return this.__constructor__(context, *args)

    @public
    def apply(this, context=None, *args):
        return func_proto.call(this, context, *args[0])

    def __call__(self, context, *args):
        return self.__constructor__(context, *args)

    def __newInstance__(self, *args):
        init = dict([x for x in self.prototype])
        instance = VM_Object(**init)
        instance.__constructor__ = self.__constructor__
        obj = instance.__constructor__(instance, *args)
        if isObject(obj): return obj
        return instance 

    __str__ = lambda self: self.__constructor__.toString()

func_prototype = func_proto()

# function  constructor
#
def function(parent, f):
    params = f.params
    body = f.body
    name = getattr(f, 'name', None)
    lambda_ = getattr(f, 'lambdaFun', None)
    vm = VM_Context(parent = parent)
    def constructor(context, *args):
        #print "constructor()", context, args
        returnValue = None
        vm.scope['arguments'] = args
        vm.context = context
        i=0
        for p in params:
            #vm.scope[p.name] = i < len(args) and args[i] or undefined
            VM_Context.assign(vm, p, i < len(args) and args[i] or undefined, local=True)
            i+=1
        try:
            returnValue = vm.eval(body)
        except BreakOutOfLoops: 
            returnValue = vm.returnValue
        scope = body.localScope
        for k, n in scope.iteritems():
            if n.decl == STATIC:
                setattr(fun, k, vm.scope.get(k))
            elif n.decl == PUBLIC:
                setattr(fun.prototype, k, vm.scope.get(k))
        
        return returnValue != None and \
                (lambda_ and returnValue or vm.returnValue) \
                or undefined

    constructor.__name__ = ustr(getattr(f, "name", 'anonymous'))
    constructor.__lambda__ = lambda_
    constructor.toString = lambda: "function %s(%s) %s" % (
            constructor.__name__, 
            ",".join([p.name for p in f.params]),
            jocore.convert(body)) 
    constructor.__hash__ = f.hash.digest()
    proto = dict(__constructor__ = staticmethod(constructor))
    fun = type(ustr(getattr(f, "name", 'anonymous')), (func_proto,), proto) ()
    fun.prototype = object_proto()
    for k, v in func_prototype:
        fun[k] = v
    return fun

#
# Function
#
class Function(VM_Object):
    def __init__(self):
        VM_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: func_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __call__(self, this, *args):
        if len(args):
            raise NotImplemented_, "Function(args, body)"
        else:
            return function(root_context, empty_function)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

def buildClass(parent, c):
    ns = null
    this = None
    lazy = 0
    className = c.name or null
    hash = c.hash.hexdigest()
    scope = dict([(var, n.decl) 
        for var, n in c.body.localScope.iteritems() 
            if n.decl in (PUBLIC, STATIC, PROTECTED)])
    body = c.body
    args = (lazy, ns, hash, this, className, object_proto(**scope), body)
    return root_context['buildClass'](root_context, args)

    #print parent, c
    #cls = function(parent, c)
    #cls = 

"""
# = = = = = = = = = = = = = = = 
#            class
# = = = = = = = = = = = = = = = 
# class prototype
class class_proto(func_proto):
    def __init__(self):
        func_proto.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return class__
        elif k == '__proto__': return class_prototype
        else: return prototype.__getattr__(self, k)

    def __newInstance__(self, *args):

class_prototype = class_proto()


#
# Class
#
class Class(Function): 
    def __init__(self):
        Function.__init__(self)

    prototype = property(lambda self: class_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

    def __call__(self, this, *args):
        if len(args):
            raise NotImplemented_, "Class(ancestors, body)"
        else:
            return class_(root_context, empty_function)
"""

# = = = = = = = = = = = = = = = 
#            regExp
# = = = = = = = = = = = = = = = 
#
# RegExp
#
class RegExp(): pass

#
# Math object
#
class Math(VM_Object):
    def __init__(self): 
        VM_Object.__init__(self)

    #native = VM_Object.native + ["PI", "E", "LN2", "LN10", "LN2E", "LN10E",
        #"SQRT2", "SQRT1_2", "sqrt", "abs", "sin", "cos", "tan",
        #"acos", "asin", "atan", "atan2", "ceil", "ext", "floor",
        #"log", "max", "min", "pow", "random", "round"]

    # Pi value
    PI = property(lambda self: self.number(math.pi))

    # The constant of E, the base of natural logarithms.
    E = property(lambda self: math.e)

    # The natural logarithm of 2.
    LN2 = property(lambda self: math.log(2))

    # The natural logarithm of 10.
    LN10 = property(lambda self: math.log(10))

    # Base 2 logarithm of E.
    LN2E = property(lambda self: math.log(math.e, 2))

    # Base 10 logarithm of E.
    LN10E = property(lambda self: math.log(math.e, 10))

    # Square root of 1/2.
    SQRT1_2 = property(lambda self: math.sqrt(1/2))

    # Square root of 2.
    SQRT2 = property(lambda self: math.sqrt(2))

    # Returns the square root of x.
    sqrt = lambda self, x: math.sqrt(x)

    # Returns the Sin of x, where x is in radians.
    sin = lambda self, x: math.sin(x)

    # Returns absolute value of x.
    abs = lambda self, x: abs(x)

    """
    cos(x) 	Returns cosine of x, where x is in radians.
    tan(x) 	Returns the Tan of x, where x is in radians.
    acos(x) 	Returns arc cosine of x in radians.
    asin(x) 	Returns arc sine of x in radians.
    atan(x) 	Returns arc tan of x in radians.
    atan2(y, x) 	Counterclockwise angle between x axis and point (x,y).
    ceil(x) 	Returns the smallest integer greater than or equal to x. (round up).
    exp(x) 	Returns ex
    floor(x) 	Returns the largest integer less than or equal to x. (round down)
    log(x) 	Returns the natural logarithm (base E) of x.
    max(a, b) 	Returns the larger of a and b.
    min(a, b) 	Returns the lesser of a and b.
    pow(x, y) 	Returns X^y
    random() 	Returns a pseudorandom number between 0 and 1.
    round(x) 	Rounds x up or down to the nearest integer. It rounds .5 up. Example(s).
    """

    __repr__ = lambda self: "Math"

#
# Date
#
class Date(VM_Object):
    def __init__(self):
        VM_Object.__init__(self)
    
    def __str__(self): return "<date>"

# todo
""" 
#
# Event
#
class Event(Class): pass

#
# XML
#
class XML(): pass

#
# XML list
#
class XMLList(): pass

#
# main citizens of Jo world
#
"""

number = Number()
string = String()
boolean = Boolean()
function_ = Function()
#class__ = Class()
array = Array()
object_ = Object()
#xml = XML()
#xmlist = XMLList()

globals_ = dict(
    # base objects
    Number = number,
    String = string,
    Boolean = boolean,
    Array = array,
    Object = object_,
    Function = function_,
    #Class = class__,
    Math = Math(),
    #XML = xml,
    #XMLList = xmlist,

    # Exceptions,
    RuntimeError = RuntimeError,

    # ECMAScript exceptions,
    Error = ECMAError,
    ReferenceError = ReferenceError,
    TypeError = TypeError_,
    SyntaxError = SyntaxError_,
    RangeError = RangeError_,
    URIError = URIError,

)
""" # it is part of w3c.xml.dom package
    # DOM exceptions,
    DOMException = DOMException,
    EventException = EventException,
    RangeException = RangeException
"""

#
# Globals object, or root
#
class Globals(VM_Object): pass

def print_(self, this, *args):
    print (" ".join([str(s) for s in args]))

setattr(Globals, 'print', print_)

#
# JOVM class
#
class JOVM(VM_Context):
    def __init__(self, jocore, tokens, glob):
        init_(jocore, tokens)
        self.globals = Globals()
        VM_Context.__init__(self, context=self.globals, scope = self.globals)
        globals()['empty_function'] = jocore.parse("function empty__ (){}")[0]
        globals()['root_context'] = self

    RuntimeError = RuntimeError
    ReferenceError = ReferenceError
    TypeError = TypeError_

"""
def function__(context, f):
    #print "function()", context #, f
    fun = func_proto(context, f)
    def wrapper(this, *args):
        #print 'Calling decorated function', this, args
        return fun.call(this, *args)
    wrapper.__name__ = getattr(f, "name", 'anonymous')
    wrapper.call = fun.call
    wrapper.apply = fun.apply
    return wrapper #staticmethod(wrapper)
"""

'''
class prototype():
    """ prototype ...
    """ 
    def __init__(self, proto=None):
        self.__class__.prototype_init(self, proto)

    protoId = None
    isPrototype = False

    @classmethod
    def prototype_init(cls, instance, proto):
        if cls.protoId:
            instance.isPrototype = False
            if id(cls.__proto__) == id(cls):
                instance.instance = instance
            else:
                instance.instance = cls.__proto__()
        else:
            instance.isPrototype = True
            cls.protoId = id(instance)
            if proto != None:
                cls.__proto__ = proto
            else:
                cls.__proto__ = cls
        cls.init(instance)

    @classmethod
    def init(cls, self): pass # extend this

    def key(self, k): return str_(k)

    def get(self, k):
        if self.isPrototype:
            return getattr(self.__proto__, k, undefined)
        else:
            return getattr(self.instance, k, undefined)

    def set(self, k, v):
        if self.isPrototype:
            return setattr(self.__proto__, k, v)
        else:
            return setattr(self.instance, k, v)

    def __setitem__(self, k, v):
        self.set(k, v)

    def __getitem__(self, k):
        return self.get(k)
'''
