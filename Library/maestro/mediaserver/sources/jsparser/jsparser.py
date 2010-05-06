"""
 Joo/Java/ActionScript Parser (formed PyNarcissus)

 A lexical scanner and parser. JS implemented in JS, ported to Python, extended with new syntax. <- revert
"""

__author__ = "JT Olds"
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"

__author__ = "buzz"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2009-09-15"

import os, re, sys, types, struct, copy
import md5

hash_ = md5
"""
try:
    import crcmod
    g32 = 0x104C11DB7
    hash_ = crcmod.Crc(g32)
except ImportError:
    hash_ = md5
"""

class Object(object): pass
class Error_(Exception): pass
class ParseError(Error_): pass
class WTF(Exception): pass

def uenc(input):
    return unicode(input, jocore.encoding)

def udec(input):
    return input.encode(jocore.encoding)

def Init(jocore, script_type, glob):

    tokens.clear()

    globals()['jocore'] = jocore
    globals()['debug'] = glob['debug']

    if script_type in ('jooscript', 'class'):
        tokens.update(dict(enumerate(common_tokens + js_tokens + jo_tokens)))
    elif script_type == 'javascript':
        tokens.update(dict(enumerate(common_tokens + js_tokens)))
    elif script_type == 'actionscript':
        jocore.warning("Support for ActionScripts it rather experimental feature: it wasn't tested nor completed yet")
        tokens.update(dict(enumerate(common_tokens + as_tokens)))

    tokens_ = {}
    #
    # Define const, END, etc., based on the token names.  Also map name to index.
    for i, t in tokens.copy().iteritems():
        if re.match(r'^[a-z]', t):
            const_name = t.upper()
            keywords[t] = i
        elif re.match(r'^\W', t):
            const_name = dict(opTypeNames_)[t]
        else:
            const_name = t
        globals()[const_name] = i
        tokens[t] = i
        #setattr(jocore, t, i)
        tokens_[const_name] = i

    # Map assignment operators to their indexes in the tokens array.
    for i, t in enumerate(['|', '^', '&', '<<', '>>', '>>>', '+', '-', '*', '/', '%']):
        assignOps[t] = tokens[t]
        assignOps[i] = t

    # Build a regexp that recognizes operators and punctuators (except newline).
    opRegExpSrc = "^"
    for i, j in opTypeNames_:
        if i == "\n": continue
        if opRegExpSrc != "^": opRegExpSrc += "|^"
        opRegExpSrc += re.sub(r'[?|^&(){}\[\]+\-*\/\.]', lambda x: "\\%s" % x.group(0), i)
    globals()['opRegExp'] = re.compile(opRegExpSrc)

    opTypeNames.clear()
    # Convert opTypeNames to an actual dictionary now that we don't care about ordering
    #opTypeNames = dict(opTypeNames)
    opTypeNames.update(dict(opTypeNames_))

    opPrecedence.clear()
    opPrecedence.update(opPrecedence_)
    # Map operator type code to precedence
    for i in opPrecedence.copy():
        opPrecedence[globals()[i]] = opPrecedence_[i]

    opArity.clear()
    opArity.update(opArity_)
    # Map operator type code to arity.
    for i in opArity.copy():
        opArity[globals()[i]] = opArity_[i]

    return tokens_

common_tokens = (
    # End of source.
    "END",

    # Operators and punctuators. Some pair-wise order matters, e.g. (+, -)
    # and (UNARY_PLUS, UNARY_MINUS).
    "\n", ";",
    ",",
    "=",
    "?", ":", "CONDITIONAL",
    "||",
    "&&",
    "|",
    "^",
    "&",
    "==", "!=", "===", "!==",
    "<", "<=", ">=", ">",
    "<<", ">>", ">>>",
    "+", "-",
    "*", "/", "%",
    "!", "~", "UNARY_PLUS", "UNARY_MINUS",
    "++", "--",
    ".",
    "[", "]",
    "{", "}",
    "(", ")",
    "..", "::", ".(", "@", # XML

    # Nonterminal tree node type codes.
    "SCRIPT", "BLOCK", "LABEL", "FOR_IN", "CALL", "NEW_WITH_ARGS", "INDEX",
    "ARRAY_INIT", "OBJECT_INIT", "PROPERTY_INIT", "GETTER", "SETTER",
    "GROUP", "LIST", 

    # Terminals.
    "IDENTIFIER", "NUMBER", "STRING", "REGEXP",

    # Keywords.
    "break",
    "case", "catch", "const", "continue",
    "debugger", "default", "delete", "do",
    "else", "enum",
    "false", "finally", "for", "function",
    "if", "in", "instanceof",
    "new", "null", "undefined",
    "return",
    "switch",
    "this", "throw", "true", "try", "typeof",
    "var", "void",
    "while", "with",

    # Nonkeywords.
    "MODULE", "MAGIC"
)

js_tokens = (
    # XML
    "XML", "XMLEND", "XMLERROR", "XMLENTITY", "XMLCOMMENT", 
    "XMLCDATA", "XMLPI", "DEFAULTXMLNAMESPACE",

    # Javascript 1.6
    "FOR_EACH", "FOR_EACH_IN",
    
    # Javascript 1.7
    "let", "yield",
    "LETSTATEMENTS", "LETEXPRESSION",

    # Javascript 1.8
    # none
    )

jo_tokens = (

    # Fix: IE raise error on object.new()
    "DOTNEW",

    # Joos
    "URI", "USECAPTURE", "DEFAULTUSECAPTURE", 

    # New keywords 
    "use", "type",
    "import", "defer", "from", "namespace", "self",
    "package", "class", "extends",
    "private", "public", "global", "static", 
    "protected", "internal", "final", "frozen", # namespaces
    "macro",
    "trace", 
    "when", "dispatch", "to", "on", "over")

as2_tokens = ( # TODO

    # ActionScript 2
    'class'
)

as3_tokens = ( # TODO

    # ActionScript 3
    'package', 'class'
)

tokens = {}

# Operator and punctuator mapping from token to tree node type name.
# NB: superstring tokens (e.g., ++) must come before their substring token
# counterparts (+ in the example), so that the opRegExp regular expression
# synthesized from this list makes the longest possible match.
opTypeNames_ = [
        ('\n',   "NEWLINE"),
        (';',    "SEMICOLON"),
        (',',    "COMMA"),
        ('?',    "HOOK"),
        (':',    "COLON"),
        ('||',   "OR"),
        ('&&',   "AND"),
        ('or',   "OR"),
        ('and',  "AND"),
        ('|',    "BITWISE_OR"),
        ('^',    "BITWISE_XOR"),
        ('&',    "BITWISE_AND"),
        ('===',  "STRICT_EQ"),
        ('==',   "EQ"),
        ('is',   "EQ"),
        ('=',    "ASSIGN"),
        ('!==',  "STRICT_NE"),
        ('!=',   "NE"),
        ('<<',   "LSH"),
        ('<=',   "LE"),
        ('<',    "LT"),
        ('>>>',  "URSH"),
        ('>>',   "RSH"),
        ('>=',   "GE"),
        ('>',    "GT"),
        ('++',   "INCREMENT"),
        ('--',   "DECREMENT"),
        ('+',    "PLUS"),
        ('-',    "MINUS"),
        ('*',    "MUL"),
        ('/',    "DIV"),
        ('%',    "MOD"),
        ('!',    "NOT"),
        ('not',  "NOT"),
        ('~',    "BITWISE_NOT"),
        ('.',    "DOT"),
        ('[',    "LEFT_BRACKET"),
        (']',    "RIGHT_BRACKET"),
        ('{',    "LEFT_CURLY"),
        ('}',    "RIGHT_CURLY"),
        ('(',    "LEFT_PAREN"),
        (')',    "RIGHT_PAREN"),
        ('..',   "DOTDOT"),
        ('::',   "COLONCOLON"),
        ('.(',   "DOTQUERY"),
        ('@',    "XMLATTR"),
    ]

opTypeNames = {}
keywords = {}
assignOps = {}

opRegExp = None

# A regexp to match floating point literals (but not integer literals).
fpRegExp = re.compile(r'^\d+\.\d*(?:[eE][-+]?\d+)?|^\d+(?:\.\d*)?[eE][-+]?\d+|^\.\d+(?:[eE][-+]?\d+)?')

# A regexp to match regexp literals.
reRegExp = re.compile(r'^\/((?:\\.|\[(?:\\.|[^\]])*\]|[^\/])+)\/([gimy]*)')

# A regexp to match URLs
# FIXME http://гугла.нет
URIre = re.compile(r"""
  ^
    ([a-z0-9+.-]+):                                       #scheme
    (?:
      //                                                  #it has an authority:
      (?:((?:[a-z0-9-._~!$&'()*+,;=:]|%[0-9A-F]{2})*)@)?  #userinfo
      ((?:[a-z0-9-._~!$&'()*+,;=]|%[0-9A-F]{2})*)         #host
      (?::(\d*))?                                         #port
      (/(?:[a-z0-9-._~!$&'()*+,;=:@/]|%[0-9A-F]{2})*)?    #path
      | (/?                                               #it doesn't have an authority:
          (?:
            [a-z0-9-._~!$&'()*+,;=:@]
            | %[0-9A-F]{2})+
            (?:                                           #path
              [a-z0-9-._~!$&'()*+,;=:@/]
              | %[0-9A-F]{2})*
        )?                          
    )
    (?:\?                                                 #query string
      (
        (?:
          [a-z0-9-._~!$&'()*+,;=:/?@]
          | %[0-9A-F]{2}
        )*
      )   
    )?
    (?:#
      (
        (?:                                               #fragment
          [a-z0-9-._~!$&'()*+,;=:/?@]
          | %[0-9A-F]{2})*) 
    )?
  $
""", re.VERBOSE)

"""
class SyntaxError_(ParseError):
    def __init__(self, message, filename, lineno):
        ParseError.__init__(self, "%s\nin %s, line %s" %
                (message, filename, lineno))
"""
SyntaxError_ = type("SyntaxError", 
        (ParseError,), 
        dict(__init__ = lambda self, m, f, l: ParseError.__init__(self, 
            "%s\nin %s, line %s" % (m, f, l))))

class StrictError(SyntaxError_): pass

def strictErr(t, x, err):
    if x.ecmaStrictMode: 
        raise StrictError(err, t.filename, t.lineno)
    else:
        jocore.warning(err, t.lineno)

class Tokenizer(object):
    def __init__(self, s, p, f, ns, l):
        self.cursor = 0
        if isinstance(s, unicode):
            self.source = udec(s)
        else:
            self.source = str(s)
        self.tokens = {}
        self.tokenIndex = 0
        self.lookahead = 0
        self.scanNewlines = False
        self.scanOperand = True
        self.filename = f
        self.lineno = l
        self.path = p
        self.ns = ns

    input_ = property(lambda self: self.source[self.cursor:])
    done = property(lambda self: self.peek() == END)
    token = property(lambda self: self.tokens.get(self.tokenIndex))

    def dirTokens(self):
        o = []
        for i in self.tokens:
            t = self.tokens.get(i)
            o.append( "[%s,%s,%s]" % (t.value, t.start, t.end) )
        return ">>> %s" % " ".join(o)
        
    def match(self, tt):
        return self.get() == tt or self.unget()

    def mustMatch(self, tt):
        if not self.match(tt):
            raise self.newSyntaxError("Missing " + tokens.get(tt).lower())
        return self.token

    def peek(self):
        if self.lookahead:
            next = self.tokens.get((self.tokenIndex + self.lookahead) & 3)
            if self.scanNewlines and (getattr(next, "lineno", None) !=
                    getattr(self, "lineno", None)):
                tt = NEWLINE
            else:
                tt = getattr(next, "type_", None)
            #print "peek() %s, %s, %s, %s" % (self.tokenIndex, self.lookahead, tokens[next.type_], tokens[tt])
        else:
            tt = self.get()
            self.unget()
        return tt

    def peekOnSameLine(self):
        self.scanNewlines = True
        tt = self.peek()
        self.scanNewlines = False
        return tt

    def get(self):
        while self.lookahead:
            self.lookahead -= 1
            self.tokenIndex = (self.tokenIndex + 1) & 3
            token = self.tokens.get(self.tokenIndex)
            if getattr(token, "type_", None) != NEWLINE or self.scanNewlines:
                return getattr(token, "type_", None)

        while True:
            input__ = self.input_
            if self.scanNewlines:
                match = re.match(r'^[ \t]+', input__)
            else:
                match = re.match(r'^\s+', input__)
            if match:
                spaces = match.group(0)
                self.cursor += len(spaces)
                newlines = re.findall(r'\n', spaces)
                if newlines:
                    self.lineno += len(newlines)
                input__ = self.input_

            match = re.match(r'^\/(?:\*(?:.|\n)*?\*\/|\/.*)', input__)
            if not match:
                break
            comment = match.group(0)
            self.cursor += len(comment)
            newlines = re.findall(r'\n', comment)
            if newlines:
                self.lineno += len(newlines)

        self.tokenIndex = (self.tokenIndex + 1) & 3
        token = self.tokens.get(self.tokenIndex)
        if not token:
            token = Object()
            self.tokens[self.tokenIndex] = token

        if not input__:
            token.type_ = END
            return END

        def matchInput():

            match = re.match(r'__FILE__|__PATH__|__GROUP__|'
                              '__FUNC__|__CLASS__|__LINE__|'
                              '__PUBLIC__|__PRIVATE__|__STATIC__|__PROTECTED__|__GLOBAL__|'
                              '__INTERNAL__|__MACRO__', input__)
            if match:
                token.type_ = MAGIC
                token.value = match.group(0)
                return match.group(0)

            match = re.match(r'^(and|or|is|not)(\s+)', input__)
            if match:
                id_ = match.group(1)
                if id_ == 'and': tok = AND
                elif id_ == 'or': tok = OR
                elif id_ == 'is': tok = EQ
                elif id_ == 'not': tok = NOT
                token.type_ = keywords.get(id_, tok)
                token.value = id_
                return match.group(0)

            match = re.match(r'^@[$_\*\w]+', input__, re.UNICODE)
            if match:
                id_ = match.group(0)
                token.type_ = XMLATTR
                token.value = id_[1:]
                return id_

            match = re.match(r'^\.\.', input__)
            if match:
                token.type_ = DOTDOT
                token.value = ".."
                return match.group(0)

            match = re.match(r'^\.\(', input__)
            if match:
                token.type_ = DOTQUERY
                token.value = ".("
                return match.group(0)

            match = re.match(r'^\:\:', input__)
            if match:
                token.type_ = COLONCOLON
                token.value = match.group(0)
                return match.group(0)

            match = fpRegExp.match(input__)
            if match:
                token.type_ = NUMBER
                token.value = float(match.group(0))
                return match.group(0)

            match = re.match(r'^0[xX][\da-fA-F]+|^0[0-7]*|^\d+', input__)
            if match:
                token.type_ = NUMBER
                token.value = eval(match.group(0))
                return match.group(0)

            match = re.match(r'^"(?:\\.|[^"])*"|^\'(?:\\.|[^\'])*\'', uenc(input__), re.UNICODE)
            if match:
                s = udec(match.group(0))
                token.type_ = STRING
                token.value = eval(s)
                return s

            if self.scanOperand:
                match = reRegExp.match(input__)
                if match:
                    token.type_ = REGEXP
                    token.value = {"regexp": match.group(1),
                                   "modifiers": match.group(2)}
                    return match.group(0)

            match = re.match(r'^[$_\w]+', uenc(input__), re.UNICODE)
            if match:
                id_ = udec(match.group(0))
                token.type_ = keywords.get(id_, IDENTIFIER)
                token.value = id_
                return id_

            match = opRegExp.match(input__)
            if match:
                op = match.group(0)
                if assignOps.has_key(op) and input__[len(op)] == '=':
                    token.type_ = ASSIGN
                    token.assignOp = globals()[opTypeNames[op]]
                    token.value = op
                    return match.group(0) + "="
                token.type_ = globals()[opTypeNames[op]]
                if self.scanOperand and (token.type_ in (PLUS, MINUS)):
                    token.type_ += UNARY_PLUS - PLUS
                token.assignOp = None
                token.value = op
                return match.group(0)

            if self.scanNewlines:
                match = re.match(r'^\n', input__)
                if match:
                    token.type_ = NEWLINE
                    return match.group(0)

            raise self.newSyntaxError("Illegal token")

        token.start = self.cursor
        self.cursor += len(matchInput())
        token.end = self.cursor
        token.lineno = self.lineno
        #print "get() %s, %s, %s, %s" % (getattr(token, "value", None), token.start, token.end, token.lineno)
        return getattr(token, "type_", None)

    def getChar(self):
        input = self.input_
        self.cursor += 1
        if not input:
          return END
        else:
          if input[:1] == "\n": self.lineno += 1
          return input[:1]

    def ungetChar(self, c):
        if c == "\n": self.lineno -= 1
        self.cursor -= 1

    def peekChar(self):
        input = self.input_
        return input[0:1]

    def unget(self):
        self.lookahead += 1
        if self.lookahead == 4: raise "PANIC: too much lookahead!"
        self.tokenIndex = (self.tokenIndex - 1) & 3

    def newSyntaxError(self, m):
        return SyntaxError_(m, os.path.join(self.path, self.filename), self.lineno)

class CompilerContext(object):
    #TODO parent = source_context ?
    def __init__(self, context=-1, parent=None, import_order=None, namespace=None, 
            depth=-1, root_scope=None, strictMode=False):
        self.stmtStack = []
        self.contextStack = []
        if context == MODULE and not parent:
            self.scope = root_scope
        else:
            self.scope = jocore.scope(parent.scope or root_scope, 
                            {'context': context})
        self.localScope = dict()
        self.let = None
        self.funDecls = []
        self.classDecls = []
        self.funArgs = []
        if hasattr(parent, 'funArgs_'):
            self.funArgs_ = list(parent.funArgs_)
        else:
            self.funArgs_ = []
        self.bracketLevel = 0
        self.curlyLevel = 0
        self.parenLevel = 0
        self.hookLevel = 0
        self.ecmaStrictMode = getattr(parent, 'ecmaStrictMode', 
                                strictMode) # 'use strict' to switch on
        self.isXmlAvailable = getattr(parent, 'isXmlAvailable', 
                                False) # 'use e4x' to force
        self.inForLoopInit = False
        self.namespace = namespace or getattr(parent, 'namespace', None)
        self.context = context
        self.public_class = False
        self.parent = parent
        self.import_order = getattr(parent, 'import_order', import_order) + 1
        self.depth = getattr(parent, 'depth', depth) + 1
        if self.context == FUNCTION:
            self.isFunction = True
        else:
            self.isFunction = getattr(parent, 'isFunction', False)

    def getContext(self):
        return self.__context__

    def setContext(self, value):
        self.__context__ = value

    context = property(getContext, setContext, None, "context")

    def decl(self, type, decl, node, t):
        name = getattr(node.name, 'value', node.name)

        #print "decl()", tokens.get(decl), tokens[type], name, "%r" % tokens.get(self.context)

        if name in self.localScope:
            try:
                n = self.localScope[name]
                decl_ = getattr(n, "decl", None)
                if decl_ == VAR:
                    if type == VAR: pass
                    else: raise t.newSyntaxError("'%s' have already declared in 'var's" % name)
                elif decl_ == LET:
                    if type == LET: pass
                    else: raise t.newSyntaxError("'%s' have already declared in 'let's" % name)
                elif decl_ == CONST:
                    if type == CONST: pass
                    else: raise t.newSyntaxError("'%s' have already declared in 'const's" % name)

                elif decl_ == FUNCTION: 
                    raise t.newSyntaxError("'%s' have already declared as function" % name)
                elif decl_ == CLASS: 
                    raise t.newSyntaxError("'%s' have already declared as class" % name)
                elif decl_ == MACRO: 
                    raise t.newSyntaxError("'%s' have already declared as macro" % name)
                elif decl_ == PUBLIC:
                    raise t.newSyntaxError("'%s' have already declared as public" % name)
                elif decl_ == PRIVATE:
                    raise t.newSyntaxError("'%s' have already declared as privated" % name)
                elif decl_ == STATIC: 
                    raise t.newSyntaxError("'%s' have already declared as static" % name)
                elif decl_ == GLOBAL: 
                    raise t.newSyntaxError("'%s' have already declared as global" % name)
                elif decl_ == PROTECTED: 
                    raise t.newSyntaxError("'%s' have already declared as protected" % name)
                elif decl_ == INTERNAL: 
                    raise t.newSyntaxError("'%s' have already declared as internal" % name)
                else:
                    raise t.newSyntaxError("'%s': unknown type %i (%s)" % (name, decl_, tokens[decl_]))
            except SyntaxError_, ex:
                if self.ecmaStrictMode:
                    raise StrictError, ex
                else:
                    jocore.warning(ex.message, t.lineno)

        #print name, decl or type, tokens[decl or type]
        self.localScope[name] = node
        self.localScope[name].decl = decl or type

    def update(self, x, block=False): 
        self.context = x.context
        self.namespace = x.namespace
        self.stmtStack = []
        self.stmtStack.extend(x.stmtStack)
        # 
        self.inForLoopInit = x.inForLoopInit
        self.bracketLevel = x.bracketLevel
        self.curlyLevel = x.curlyLevel
        self.parenLevel = x.parenLevel
        self.hookLevel = x.hookLevel
        #
        self.ecmaStrictMode = x.ecmaStrictMode 
        self.isXmlAvailable = x.isXmlAvailable
        self.localScope.update([[k, x.localScope[k]] for k in x.localScope 
            if getattr(x.localScope[k], 'decl', None) != LET])

        self.public_class = x.public_class

        self.classDecls.extend(x.classDecls)
        self.funDecls.extend(x.funDecls)
        #
        self.new = getattr(x, 'new', None)
        #
        self.name_ = getattr(x, 'name_', None)
        self.funName = getattr(x, 'funName', None)
        self.className = getattr(x, 'className', None)

    def clone(self): 
        newContext = CompilerContext(self.context, self)
        newContext.update(self)
        return newContext

    def save(self): 
        self.contextStack.append(self.context)

    def restore(self):
        self.context = self.contextStack.pop()

def Script(t, x, expression=None):
    n = expression or Statements(t, x)
    n.type_ = SCRIPT
    n.context = x.context
    n.localScope = x.localScope
    n.scope = x.scope
    n.funDecls = x.funDecls
    n.classDecls = x.classDecls
    n.funArgs = x.funArgs
    n.namespace = x.namespace
    n.name_ = getattr(x, 'name_', None)
    n.funName = getattr(x, 'funName', None)
    n.className = getattr(x, 'className', None)
    return n

class Node(list):
    def __init__(self, t, type_=None, args=[]):
        list.__init__(self)

        token = t.token
        self.hash = hash_.new()
        if token:
            self.value = token.value
            self.lineno = token.lineno
            self.start = token.start
            self.end = token.end
            if type_:
                self.type_ = type_
            else:
                self.type_ = getattr(token, "type_", None)
        else:
            self.type_ = type_
            self.lineno = t.lineno

        self.tokenizer = t

        for arg in args:
            self.append(arg)

    type = property(lambda self: tokenstr(self.type_))

    # Always use push to add operands to an expression, to update start and end.
    def append(self, kid, numbers=[]):
        if kid:
            if hasattr(self, "start") and kid.start < self.start:
                self.start = kid.start
            if hasattr(self, "end") and self.end < kid.end:
                self.end = kid.end
            self.hash.update(kid.hash.digest())
        return list.append(self, kid)

    indentLevel = 0
    int_attrs = ['int_attrs', "append", "count", "extend", "getSource", "index",
                    "insert", "pop", "remove", "reverse", "sort", "type_",
                    "target", "filename", "indentLevel", "type"]

    def __str__(self):
        a = list((str(i), v) for i, v in enumerate(self))
        for attr in dir(self):
            if attr[0] == "_": continue
            elif attr == "hash": pass
                #a.append((attr, "0x" + self.hash.hexdigest()))
            elif attr == "tokenizer":
                a.append((attr, "[object Object]"))
            elif attr in self.int_attrs:
                continue
            else:
                a.append((attr, getattr(self, attr)))
        if len(self): a.append(("length", len(self)))
        a.sort(lambda a, b: cmp(a[0], b[0]))
        INDENTATION = "    "
        Node.indentLevel += 1
        n = Node.indentLevel
        s = "{\n%stype: %s" % ((INDENTATION * n), tokenstr(self.type_))
        for i, value in a:
            if isinstance(value, unicode):
                value = udec(value)
            s += ",\n%s%s: " % ((INDENTATION * n), i)
            if i == "value" and self.type_ == REGEXP:
                s += "/%s/%s" % (value["regexp"], value["modifiers"])
            elif value is None:
                s += "null"
            elif value is False:
                s += "false"
            elif value is True:
                s += "true"
            elif type(value) == list:
                s += ','.join((str(x) for x in value))
            else:
                s += str(value)
        Node.indentLevel -= 1
        n = Node.indentLevel
        s += "\n%s}" % (INDENTATION * n)
        return s
    __repr__ = __str__

    def getSource(self):
        if getattr(self, "start", None) is not None:
            if getattr(self, "end", None) is not None:
                return self.tokenizer.source[self.start:self.end]
            return self.tokenizer.source[self.start:]
        if getattr(self, "end", None) is not None:
            return self.tokenizer.source[:self.end]
        return self.tokenizer.source[:]

    filename = property(lambda self: self.tokenizer.filename)

    def __nonzero__(self): return True

    def __setattr__(self, name, value):
        if name == 'type_' and not hasattr(self, 'value'):
            self.hash.update(str(value))
            object.__setattr__(self, name, value)
        elif value == None or name in self.int_attrs or \
                name in ('hash', 'lineno', 'tokenizer',
                         'start', 'end', 'readOnly', 'localScope', 
                         'scope', 'funDecls', 'classDecls', 'funArgs',
                         'name_', 'name', 'defaultIndex', 'for_each'):
            object.__setattr__(self, name, value)
        elif name.startswith("_"):
            object.__setattr__(self, name, value)
        elif name in ('decl', 'value', 'context', 
                'funName', 'functionForm', 'lambdaFun',
                'className', 'classForm', "namespace",
                'isLoop', 'postfix', 'assignOp', "label", "isType"):
            if value != None: 
                if isinstance(value, unicode):
                    self.hash.update(udec(value))
                else:
                    self.hash.update(str(value))
            object.__setattr__(self, name, value)
        elif not isinstance(value, Node):
            raise WTF, "Node(): %s is not Node instance" % name
        else:
            self.hash.update(value.hash.digest())
            object.__setattr__(self, name, value)

# Statement stack and nested statement handler.
def nest(t, x, node, func, end=None, alt1=None, alt2=None):
    x.stmtStack.append(node)
    n = func(t, x)
    x.stmtStack.pop()
    if end and alt1 and alt2:
      if t.match( end ) or t.match( alt1 ) or t.match( alt2 ):
        return n
      tt = t.peek()
      if tt in (end, alt1, alt2):
        t.get()
      else:
        raise t.newSyntaxError("Syntax error")
    else:
      return n

def tokenstr(tt):
    t = tokens[tt]
    if re.match(r'^\W', t):
        return opTypeNames[t]
    return t.upper()

def Statements(t, x):
    n = Node(t, BLOCK)
    if x.context == BLOCK:
        x2 = CompilerContext(x.context, x)
        x2.update(x)
    x.stmtStack.append(n)
    while not t.done and t.peek() != RIGHT_CURLY:
        if x.context == BLOCK:
            n.append(Statement(t, x2))
        else:
            n.append(Statement(t, x))
    x.stmtStack.pop()

    if x.context == BLOCK:
        x.update(x2, True)
        n.let = x2.let

    return n

def Block(t, x):
    t.mustMatch(LEFT_CURLY)
    n = Statements(t, x)
    t.mustMatch(RIGHT_CURLY)
    return n

# dubbed parser code from rhino source
#
class XmlStream(Node):

    def __init__(self,t,x):
        Node.__init__(self, t, XML)

        token = t.token

        self.append('')
        self.index = 0
        self.tokenizer = t
        t.ungetChar(token.value)
        t.scanOperand = False

        while True:
            tt = self.getNextXMLToken(t, x)
            if tt == XML: pass
                #print "XML: %s" % self.stream
            elif tt == XMLEND:
                self.end = t.cursor
                self.lineno = t.lineno
                #print "XMLEND: %s" % self.stream
                break
            elif tt == XMLERROR:
                raise t.newSyntaxError("Bad XML form")
            else:
                raise t.newSyntaxError("Syntax error")

    isTagContent = 0
    isAttribute = 0
    openTagsCount = 0

    def getNextXMLToken(self, t, x):
        while True:
            c = t.getChar()
            #print "getNextXMLToken() ", c

            if self.isTagContent:
                if c == '>':
                    self.addToString(c);
                    self.isTagContent = 0;
                    self.isAttribute = 0;

                elif c == '/':
                    self.addToString(c);
                    if t.peekChar() == '>':
                        c = t.getChar()
                        self.addToString(c)
                        self.isTagContent = 0
                        self.openTagsCount -= 1

                elif c == '{':
                    self.addExpression(t,x)
                    return XML

                elif c in ('\'', '"'):
                    self.addToString(c)
                    if not self.readQuotedString(c):
                        return XMLERROR

                elif c == '=':
                    self.addToString(c);
                    self.isAttribute = 1;
                
                elif c in (' ', '\t', '\r', '\n'):
                    self.addToString(c)

                else:
                    self.addToString(c)
                    self.isAttribute = 0

                if not self.isTagContent and self.openTagsCount == 0:
                    return XMLEND

            else:
                if c == '<':
                    self.addToString(c)
                    c = t.peekChar()

                    if c == '!':
                        c = t.getChar() # Skip !
                        self.addToString(c)
                        c = t.peekChar()
                        if c == '-':
                            c = t.getChar() # Skip -
                            self.addToString(c)
                            c = t.getChar()
                            if c == '-':
                                self.addToString(c);
                                if not self.readXmlComment():
                                    return XMLERROR
                            else:
                                return XMLERROR

                        elif c == '[':
                            c = t.getChar() # Skip [
                            self.addToString(c);
                            if t.getChar() == 'C' and t.getChar() == 'D' and t.getChar() == 'A' and t.getChar() == 'T' and t.getChar() == 'A' and t.getChar() == '[':
                                self.addToString('C')
                                self.addToString('D')
                                self.addToString('A')
                                self.addToString('T')
                                self.addToString('A')
                                self.addToString('[')
                                if not self.readCDATA():
                                    return XMLERROR
                            else:
                                return XMLERROR

                        else:
                            if not self.readEntity():
                                return XMLERROR

                    elif c == '?':
                        c = t.getChar(); # Skip ?
                        self.addToString(c)
                        if not self.readPI():
                            return XMLERROR

                    elif c == '/': # End tag
                        c = t.getChar(); # Skip /
                        self.addToString(c)
                        if self.openTagsCount == 0:
                            return XMLERROR
                        self.isTagContent = 1
                        self.openTagsCount -= 1
                    
                    else: # Start tag
                        self.isTagContent = 1
                        self.openTagsCount += 1

                elif c == '{':
                    self.addExpression(t,x)
                    return XML
                else:
                    self.addToString(c)

        return XMLERROR
                    
    def addExpression(self,t,x):
        t.scanOperand = True
        list.append(self, Expression(t, x, RIGHT_CURLY) ) 
        self.index = len( self )
        list.append(self, '')
        t.get()

    def addToString(self, c):
        self[self.index] += c

    def readQuotedString(self, quote):
        while True:
            c = self.tokenizer.getChar()
            self.addToString(c)
            if c == quote: return True

        return XMLERROR

    def readXmlComment(self):
        t = self.tokenizer
        while True:
            c = t.getChar()
            self.addToString(c)
            if c == '-' and t.peekChar() == '-':
                c = t.getChar()
                self.addToString(c)
                if t.peekChar() == '>':
                    c = t.getChar() # Skip >
                    self.addToString(c)
                    return True
                else:
                    pass

        return XMLERROR

    def readCDATA(self):
        t = self.tokenizer
        while True:
            c = t.getChar()
            self.addToString(c)
            if c == ']' and t.peekChar() == ']':
                c = t.getChar()
                self.addToString(c)
                if t.peekChar() == '>':
                    c = t.getChar() # Skip >
                    self.addToString(c)
                    return True
                else:
                    pass

        return XMLERROR

    def readEntity(self):
        t = self.tokenizer
        declTags = 1
        while True:
            c = t.getChar()
            self.addToString(c)
            if c == '<':
                declTags += 1
                break
            elif c == '>':
                declTags -= 1
                if declTags == 0: return True

        return XMLERROR

    def readPI(self):
        t = self.tokenizer
        while True:
            c = t.getChar()
            self.addToString(c)
            if c == '?' and t.peekChar() == '>':
                c = t.getChar() # Skip >
                self.addToString(c)
                return True

        return XMLERROR

# end of XMLStream

XmlStream.int_attrs.extend(XmlStream.__dict__.keys())

DECLARED_FORM = 0
EXPRESSED_FORM = 1
STATEMENT_FORM = 2

def Statement(t, x, visibility=None, static=False):
    tt = t.get()
    #print "Statement(): %s" % tokens[tt]
    exp = False

    # Cases for statements ending in a right curly return early, avoiding the
    # common semicolon insertion magic after this switch.
    if tt == FUNCTION:
        if len(x.stmtStack) > 1:
            type_ = STATEMENT_FORM
        else:
            type_ = DECLARED_FORM
        return FunctionDefinition(t, x, True, type_, visibility)

    elif tt == LEFT_CURLY:
        x.save()
        x.context = BLOCK
        n = Statements(t, x)
        x.restore()
        t.mustMatch(RIGHT_CURLY)
        return n

    elif tt == IF:
        n = Node(t)
        n.condition = ParenExpression(t, x)
        x.stmtStack.append(n)
        n.thenPart = Statement(t, x)
        if t.match(ELSE):
            n.elsePart = Statement(t, x)
        else:
            n.elsePart = None
        x.stmtStack.pop()
        Eval(t,x,n)
        return n

    elif tt == SWITCH:
        n = Node(t)
        t.mustMatch(LEFT_PAREN)
        n.discriminant = Expression(t, x)
        t.mustMatch(RIGHT_PAREN)
        cases = Node(t)
        n.defaultIndex = -1
        x.stmtStack.append(n)
        t.mustMatch(LEFT_CURLY)
        while True:
            tt = t.get()
            if tt == RIGHT_CURLY: break

            if tt in (DEFAULT, CASE):
                if tt == DEFAULT and n.defaultIndex >= 0:
                    raise t.newSyntaxError("More than one switch default")
                n2 = Node(t)
                if tt == DEFAULT:
                    n.defaultIndex = len(cases)
                else:
                    n2.caseLabel = Expression(t, x, COLON)
            else:
                raise t.newSyntaxError("Invalid switch case")
            t.mustMatch(COLON)
            n2.statements = Node(t, BLOCK)
            n2.statements.let = None
            while True:
                tt = t.peek()
                if(tt == CASE or tt == DEFAULT or tt == RIGHT_CURLY): break
                n2.statements.append(Statement(t, x))
            cases.append(n2)
        n.cases = cases
        x.stmtStack.pop()
        Eval(t,x,n)
        return n

    elif tt == FOR:
        n = Node(t)
        n2 = None
        n.isLoop = True

        tt = t.peek()
        if tt == IDENTIFIER:
            t.get()
            if t.token.value == 'each': for_each = True
            else: raise t.newSyntaxError("Maybe 'for each (...'?")
        else:
            for_each = False

        t.mustMatch(LEFT_PAREN)
        tt = t.peek()
        if tt != SEMICOLON:
            x.inForLoopInit = True
            if tt == VAR:
                t.get()
                n2 = Variables(t, x)
            elif tt == LET:
                t.get()
                x = x.clone()
                n2 = Let(t, x, BLOCK)
            else:
                n2 = Expression(t, x)
            x.inForLoopInit = False

        if n2 and t.match(IN):
            n.type_ = FOR_IN
            n.for_each = for_each
            if n2.type_ == VAR or n2.type_ == LET:
                if len(n2) != 1:
                    raise SyntaxError("Invalid for..in left-hand side",
                            t.filename, n2.lineno)

                n.iterator = n2[0]
                n.varDecl = n2
                n.iterator.decl = n2.type_
            else:
                n.iterator = n2
                n.iterator.decl = None
                n.varDecl = None
            n.object = Expression(t, x)
        else:
            if n2:
                n.setup = n2
            else:
                n.setup = None
            t.mustMatch(SEMICOLON)
            if t.peek() == SEMICOLON:
                n.condition = None
            else:
                n.condition = Expression(t, x)
            t.mustMatch(SEMICOLON)
            if t.peek() == RIGHT_PAREN:
                n.update = None
            else:
                n.update = Expression(t, x)

        t.mustMatch(RIGHT_PAREN)
        n.body = nest(t, x, n, Statement)
        Eval(t,x,n)
        return n

    elif tt == WHILE:
        n = Node(t)
        n.isLoop = True
        n.condition = ParenExpression(t, x)
        n.body = nest(t, x, n, Statement)
        Eval(t,x,n)
        return n

    elif tt == DO:
        n = Node(t)
        n.isLoop = True
        tt = t.peek()
        when = False

        if tt == IDENTIFIER:
            t.get()
            tt = t.peek()
            if tt in (WHEN, ON):
                when = True
                body = Node(t)
                t.get()
            else:
                body = nest(t, x, n, Statement, WHILE)

        elif tt == LEFT_CURLY:
            body = nest(t, x, n, Statement, WHILE, WHEN, ON)
            if t.token.type_ in (WHEN, ON): when = True

        if when: # when statement
            tt = t.peek()

            n.type_ = WHEN

            #t.scanNewlines = True
            n.event = When(t,x,False)

            n.eventHandler = body
            Eval(t,x,n)
            return n
        else: # while .. do statement
            n.body = body
            n.condition = ParenExpression(t, x)
            if not x.ecmaStrictMode:
                # <script language="JavaScript"> (without version hints) may need
                # automatic semicolon insertion without a newline after do-while.
                # See http://bugzilla.mozilla.org/show_bug.cgi?id=238945.
                t.match(SEMICOLON)
                Eval(t,x,n)
                return n

    elif tt in (BREAK, CONTINUE):
        n = Node(t)
        if t.peekOnSameLine() == IDENTIFIER:
            t.get()
            n.label = t.token.value
        ss = x.stmtStack
        i = len(ss)
        label = getattr(n, "label", None)
        if label:
            while True:
                i -= 1
                if i < 0:
                    raise t.newSyntaxError("Label not found")
                if getattr(ss[i], "label", None) == label: break
        else:
            while True:
                i -= 1
                if i < 0:
                    if tt == BREAK:
                        raise t.newSyntaxError("Invalid break")
                    else:
                        raise t.newSyntaxError("Invalid continue")
                if (getattr(ss[i], "isLoop", None) or (tt == BREAK and
                        ss[i].type_ == SWITCH)):
                    break
        n.target = ss[i]

    elif tt == TRY:
        n = Node(t)
        n.tryBlock = Block(t, x)
        catchClauses = Node(t, CATCH)
        while t.match(CATCH):
            n2 = Node(t)
            t.mustMatch(LEFT_PAREN)
            t.mustMatch(IDENTIFIER)
            n2.varName = Node(t)
            x.funArgs.append(n2)
            if t.match(IF):
                if x.ecmaStrictMode:
                    raise t.newSyntaxError("Illegal catch guard")
                if n.catchClauses and not n.catchClauses[-1].guard:
                    raise t.newSyntaxError("Gaurded catch after unguarded")
                n2.guard = Expression(t, x)
            else:
                n2.guard = None
            t.mustMatch(RIGHT_PAREN)
            n2.block = Block(t, x)
            catchClauses.append(n2)
        n.catchClauses = catchClauses
        if t.match(FINALLY):
            n.finallyBlock = Block(t, x)
        if not n.catchClauses and not getattr(n, "finallyBlock", None):
            raise t.newSyntaxError("Invalid try statement")
        Eval(t,x,n)
        return n

    elif tt in (CATCH, FINALLY):
        raise t.newSyntaxError(tokens[tt] + " without preceding try")

    elif tt == THROW:
        n = Node(t)
        n.exception = Expression(t, x)

    elif tt == RETURN:
        if not x.isFunction:
            raise t.newSyntaxError("Invalid return")
        n = Node(t)
        n.value = None
        tt = t.peekOnSameLine()
        if tt not in (END, NEWLINE, SEMICOLON, RIGHT_CURLY):
            n.value = Expression(t, x)

    elif tt == LET:
        n = Let(t,x,x.context)
        
    elif tt in (VAR, CONST):
        n = Variables(t, x)

    elif tt == DEBUGGER:
        n = Node(t)

    elif tt in (NEWLINE, SEMICOLON):
        n = Node(t, SEMICOLON)
        n.expression = None
        return n

    elif tt == WITH:
        n = With(t,x)
        Eval(t,x,n)
        return n

    elif tt in (WHEN, ON):
        n = Node(t, WHEN)
        n.event = When(t,x,True)
        n.eventHandler = EventHandler(t,x)

        Eval(t,x,n)
        return n

    elif tt == DISPATCH:
        n = Node(t)
        tt = t.peek()
        #if tt in (XML, STRING, IDENTIFIER, LEFT_PAREN, LEFT_CURLY):
        n.event = Expression(t, x, TO)
        #elif tt == LEFT_PAREN:
          #n.eventName = ParenExpression(t, x)

        tt = t.peek()
        if tt == TO: 
          t.get()
          n.eventTarget = Expression(t, x)
        else:
          n.eventTarget = None

        Eval(t,x,n)
        return n

    elif tt == PACKAGE:
        n = PackageDefinition(t, x)
        Eval(t,x,n)
        return n

    elif tt == CLASS:
        if len(x.stmtStack) > 1:
            type_ = STATEMENT_FORM
        else:
            type_ = DECLARED_FORM

        n = ClassDefinition(t, x, True, type_, visibility)
        Eval(t,x,n)
        return n

    elif tt == NAMESPACE:
        if x.context != PACKAGE:
            raise t.newSyntaxError("namespace declaration allowed only in package context")
        n = Namespace(t, x)
        x.namespace = n.namespace
        if t.ns != n.namespace:
            err_ = "wrong namespace %s" % n.namespace
            if x.ecmaStrictMode:
                raise t.newSyntaxError(err_)
            else:
                jocore.warning(err_, t.lineno)
        #Eval(t,x,n)
        return n

    elif tt in (GLOBAL, STATIC, PUBLIC, PROTECTED, PRIVATE, MACRO, INTERNAL):

        decl = tt

        tt = t.get()
        tp = t.peekOnSameLine()

        context = x.context

        if decl == PUBLIC and context == PACKAGE and tt == CLASS: 
            if x.public_class:
                raise t.newSyntaxError("Too much public class declarations in package")
                    
        elif decl in (STATIC, PUBLIC) and context not in (CLASS, FUNCTION):
            raise t.newSyntaxError("%s declaration allowed only in class or function context" % tokens[decl])
        elif decl in (PROTECTED, PRIVATE) and context is not CLASS:
            raise t.newSyntaxError("%s declaration allowed only in class context" % tokens[decl])

        if decl == MACRO: pass

        if tt == VAR:
            n = Variables(t, x, decl)
        else:
            if tt == IDENTIFIER and tp in (ASSIGN, COLON, END, SEMICOLON, NEWLINE):
                t.unget()
                n = Variables(t, x, decl)
            elif tt == CLASS and tp == IDENTIFIER:
                tt = t.get()
                tp = t.peek()
                #print ["classDef", t.token.value, tokens[tt], tokens[tp]]
                if tt == IDENTIFIER and tp == ASSIGN:
                    t.unget()
                    n = Variables(t, x, decl)
                elif tt == IDENTIFIER and tp in (LEFT_CURLY, EXTENDS):
                    t.unget()
                    n = ClassDefinition(t, x, True, DECLARED_FORM, decl)
                    if decl == PUBLIC and context == PACKAGE:
                        x.public_class = n
                else:
                    raise t.newSyntaxError("Unexpected class definition")

            elif tt == FUNCTION and tp == IDENTIFIER: 
                t.unget()
                n = Statement(t, x, decl)
            elif tt == IDENTIFIER and tp == IDENTIFIER:
                t.unget()
                n = Variables(t, x, decl)
            elif tp == FUNCTION:
                returnType = typeDef(t,x,FUNCTION)
                n = FunctionDefinition(t, x, True, DECLARED_FORM, decl, returnType)
            else:
                raise t.newSyntaxError("Unexpected token %r" % tokens[tt])

        Eval(t,x,n)
        return n

    elif tt in (DEFER, IMPORT, FROM):
        n = Import(t, x)
        return n

    elif tt == TYPE:
        n = Type(t, x)
        Eval(t,x,n)
        return n

    elif tt == MAGIC:
        n = Magic(t, x)
        Eval(t,x,n)
        return n

    elif tt == DEFAULT:
        n = Node(t)
        t.get() 
        if t.token.value == 'xml' and \
                t.get() and t.token.value == 'namespace':
            n.type_ = DEFAULTXMLNAMESPACE
            t.mustMatch(ASSIGN)
            n.namespace_ = Expression(t,x)
            n.value = "default xml namespace"
            return n
        elif t.token.value == 'use' and \
                t.get() and t.token.value == 'capture':
            n.type_ = DEFAULTUSECAPTURE
            t.mustMatch(ASSIGN)
            t.get()
            if t.token.value in ("true", "false", "null"):
                n.append(Node(t))
            else:
                t.newSyntaxError("Syntax error")
            n.value = "default use capture"
            return n

    elif tt == USE or (tt == STRING and \
        re.match(r'^use (strict|e4x|capture)$', t.token.value)):
      n = Node(t, USE)
      if tt == STRING:
        what = t.token.value.split()[1]
      else:
        t.get()
        what = t.token.value
        #t.get()

      if what == 'e4x': 
          x.isXmlAvailable = True
      elif what == 'strict': 
          x.ecmaStrictMode = True
          if jocore.shell:
              jocore.strictMode = True
      elif what == 'capture':
        t.mustMatch(ASSIGN)
        t.get()
        if t.token.value in ("true", "false", "null"):
            n.append(Node(t))
        else:
            t.newSyntaxError("Syntax error")
        n.type_ = USECAPTURE
      else: 
          raise t.newSyntaxError(str(what) + " is not implemented")

      n.value = what
      return n

    else:
        if tt == IDENTIFIER:
            t.scanOperand = False
            tt = t.peek()
            t.scanOperand = True
            if tt == COLON:
                label = t.token.value
                ss = x.stmtStack
                i = len(ss) - 1
                while i >= 0:
                    if getattr(ss[i], "label", None) == label:
                        raise t.newSyntaxError("Duplicate label")
                    i -= 1
                t.get()
                n = Node(t, LABEL)
                n.label = label
                n.statement = nest(t, x, n, Statement)
                return n

        n = Node(t, SEMICOLON)
        t.unget()
        n.expression = Expression(t, x)
        n.end = n.expression.end
    
        exp = n.expression
        if exp.type_ == ASSIGN:

            if exp[0].type_ not in (IDENTIFIER, DOT, INDEX):
                raise t.newSyntaxError("Invalid left-hand side in assignment")

            if exp[0].type_ == IDENTIFIER:
                var = exp[0].value
                if x.scope.isMacro(var):
                    raise t.newSyntaxError("%s is macro" % var)
                elif x.scope.isInternal(var):
                    raise t.newSyntaxError("%s is internal" % var)
                elif x.scope.isVar(var) and getattr(x.scope.get(var), 'readOnly', False):
                    raise t.newSyntaxError("%s is constant" % var)
                elif var not in x.scope and var not in x.funArgs_:
                    strictErr(t, x, "Assignment to undeclared variable " + var)

        elif exp.type_ in (INCREMENT, DECREMENT) and \
                exp[0].type_ not in (IDENTIFIER, DOT, INDEX):
            raise t.newSyntaxError("Invalid left-hand side expression in "
                    "%s operation" % (getattr(exp, 'postfix', None) and \
                            'postfix' or 'prefix'))

        #if n.expression.type_ in (ASSIGN, CALL):

    if t.lineno == t.token.lineno:
        tt = t.peekOnSameLine()
        if tt not in (END, NEWLINE, SEMICOLON, RIGHT_CURLY, XMLEND):
            raise t.newSyntaxError("Missing ; before statement")
    t.match(SEMICOLON)
    Eval(t, x, exp or n)
    return n

def FunctionDefinition(t, x, requireName, functionForm, decl=None, returnType=None):
    f = Node(t, FUNCTION)

    if f.type_ != FUNCTION:
        if f.value == "get":
            f.type_ = GETTER
        else:
            f.type_ = SETTER

    tt = t.peek()
    isConstructor = False
    if tt == IDENTIFIER:
        t.get()
        f.name = t.token.value
    elif tt == NEW:
        if x.context == CLASS:
            if x.new is None:
                t.get()
                f.name = t.token.value
                f.isClassConstructor = True
                isConstructor = True
                x.new = f
            else:
                raise t.newSyntaxError("Too much class constructors")
        else:
            raise t.newSyntaxError("Class constructor not in class definitions")
    elif requireName:
        raise t.newSyntaxError("Missing function identifier")

    if functionForm == DECLARED_FORM and not isConstructor:
        x.decl(FUNCTION, decl, f, t)
    else:
        f.decl = None

    t.mustMatch(LEFT_PAREN)
    f.params = Node(t, LIST)

    tt = t.peek()
    if tt == RIGHT_PAREN:
        t.get()
    else:
        while True:
            if tt == RIGHT_PAREN: break
            #if tt != IDENTIFIER:
                #raise t.newSyntaxError("Missing formal parameter")
            f.params.append(Identifier(t,x,True,"Missing formal parameter"))
            tt = t.get() 
            if tt not in (RIGHT_PAREN, COMMA):
                raise t.newSyntaxError("err...")

    tt = t.peek()

    if tt == COLON:
        t.get()
        f.returnType = typeDef(t,x, FUNCTION)
        tt = t.peek()

    x2 = CompilerContext(FUNCTION, x)
    x2.funArgs = [par.name for par in f.params]
    x2.funArgs_.extend(x2.funArgs)
    x2.name_ = getattr(f, 'name', None)
    x2.className = getattr(x, 'className', None)
    x2.funName = x2.name_
    if tt != LEFT_CURLY: # probably lambda notation
        if tt == RETURN: 
            raise t.newSyntaxError("Invalid return")
        f.lambdaFun = True
        f.body = Script(t, x2, Node(t))
        f.body.append( Expression(t, x, [COMMA, NEWLINE, RIGHT_PAREN, RIGHT_CURLY]) )
    else:
        t.mustMatch(LEFT_CURLY)
        f.body = Script(t, x2)
        t.mustMatch(RIGHT_CURLY)
        f.end = t.token.end
        f.lambdaFun = False

    f.returnType = returnType

    f.functionForm = functionForm
    if functionForm == DECLARED_FORM:
        x.funDecls.append(f)

    #Eval(t,x,f)
    return f

def ClassDefinition(t, x, requireName, classForm, decl=None):
    c = Node(t, CLASS)
    c.new = None

    if t.match(IDENTIFIER):
        c.name = t.token.value
    elif requireName:
        raise t.newSyntaxError("Missing class identifier")
    else:
        c.name = None

    if classForm == DECLARED_FORM:
        x.decl(CLASS, decl, c, t)
    else:
        c.decl = None

    c.ancestors = None
    tt = t.peek()
    #
    if tt == EXTENDS:
        t.get()
        c.ancestors = Expression(t,x,LEFT_CURLY)
        if c.ancestors.type_ not in (COMMA, IDENTIFIER):
            raise t.newSyntaxError("Broken class extends declaration")

    t.mustMatch(LEFT_CURLY)
    x2 = CompilerContext(CLASS, x)
    x2.new = None
    x2.name_ = c.name
    x2.funName = getattr(x, 'funName', None)
    x2.className = c.name
    c.body = Script(t, x2)
    t.mustMatch(RIGHT_CURLY)
    c.end = t.token.end

    c.new = x2.new
    c.params = c.new and c.new.params or None

    c.body.scope.isClassContext = True

    c.classForm = classForm
    if classForm == DECLARED_FORM:
        x.classDecls.append(c)

    return c

def PackageDefinition(t, x):
    p = Node(t, PACKAGE)

    tt = t.peek()

    p.namespace = None
    if tt == IDENTIFIER:
        p.namespace = Namespace(t,x).namespace
    elif tt == LEFT_CURLY: pass
    else:
        t.get()
        raise t.newSyntaxError("Unexpected token %r" % t.token.value)

    t.mustMatch(LEFT_CURLY)
    x2 = CompilerContext(PACKAGE, x, namespace = p.namespace)
    x2.className = getattr(x, 'className', None)
    x2.funName = getattr(x, 'funName', None)
    p.body = Script(t, x2)
    ValidatePackage(t, x2)
    t.mustMatch(RIGHT_CURLY)
    p.end = t.token.end
    
    if not x2.namespace and not p.namespace: pass
    elif x2.namespace == p.namespace: pass
    elif x2.namespace and p.namespace and x2.namespace != p.namespace: 
        raise t.newSyntaxError("Many concurent namespace declarations")
    elif x2.namespace:
        p.namespace = x2.namespace

    #Eval(t,x,p)
    return p

def Import(t, x):
    n = Node(t, IMPORT)
    from_ = [None, None]

    if t.token.type_ == IMPORT:
        pass
    elif t.token.type_ == FROM:
        from_ = From(t,x,True)
        #t.get()
        t.mustMatch(IMPORT)

    if t.match(TRACE): pass
    else: t.mustMatch( IDENTIFIER )

    externals = Node(t, LIST)
    ext = Node(t)

    i = 0
    pt = None
    while True:
        tt = t.peekOnSameLine()
        if tt in (IDENTIFIER, MUL, DOT, TRACE):
            t.get()
            if t.token.value == 'as':
                t.get()
                ext.alias = t.token.value
            else:
                ext.value += t.token.value
        elif tt == COMMA:
            t.get()
            externals.append(ext)
            ext = Node(t)
            i += 1
        elif tt in (FROM, SEMICOLON, NEWLINE, END):
            externals.append(ext)
            break
        else:
            raise SyntaxError, "Unexpected import declaration"

        pt = tt
    
    if t.peek() == FROM:
        from_ = From(t,x,False)

    n.externals = externals
    n.from_ = from_[0]
    n.namespace = from_[1]
    
    #print n.externals, n.from_, x.import_order, n.namespace
    for ext in n.externals:
        jocore.import_(ext.value, n.from_, n.namespace or x.namespace, 
                x.import_order, x.scope, x.depth)

    return n

def From(t, x, head):
    from_ = ""
    ns = None
    if t.token.type_ != FROM:
        t.mustMatch(FROM)
    
    while True:
        tt = t.peekOnSameLine()
        if head and tt == IMPORT: 
            break
        elif not head and tt in (SEMICOLON, NEWLINE, END):
            break

        tt = t.get()
        if tt in (IDENTIFIER, DOT):
            from_ += t.token.value
        elif tt == COLONCOLON:
            ns = from_
            from_ = ""
        else:
            raise SyntaxError, "Unexpected import declaration"

    return [from_, ns]

def Namespace(t, x):
    n = Node(t)
    n.namespace = ""

    pt = DOT
    while True:
        tt = t.peekOnSameLine()

        if tt == DOT and pt == IDENTIFIER:
            t.get()
            pt = DOT
        elif tt == IDENTIFIER and pt == DOT:
            t.get()
            pt = IDENTIFIER
        elif tt in (LEFT_CURLY, SEMICOLON, NEWLINE, END): break
        else: t.newSyntaxError("Broken namespace")

        n.namespace += t.token.value

        pt = tt

    return n

def Type(t, x):
    n = Node(t)
    n.name = typeDef(t,x, FUNCTION)
    t.mustMatch(LEFT_PAREN)
    t.mustMatch(IDENTIFIER)
    n.param = t.token.value
    t.mustMatch(RIGHT_PAREN)
    n.expression = Expression(t,x)

    return n

def Identifier(t, x, init=False, error="Expected identifier"):
    tt = t.get()
    nt = t.peek()
    
    isType = None

    if stype_ == "actionscript":
        if tt == IDENTIFIER and nt == COLON:
            n = Node(t)
            t.get()
            isType = typeDef(t, x)
        
        elif tt == IDENTIFIER:
            n = Node(t)

        else:
            raise t.newSyntaxError(error)

    else:
        if tt == IDENTIFIER: n = Node(t)
        else: raise t.newSyntaxError(error)

    n.type_ = IDENTIFIER
    n.name = n.value
    n.isType = isType
    #print ["identifier", isType, n.name]
    return n
        
def typeDef(t, x, isFunction=False):
    t.get()
    #print ['typeDef()', t.token.value, tokens[t.token.type_]]
    allowed = [CLASS, FUNCTION, IDENTIFIER]
    if isFunction: allowed.append(VOID)

    if t.token.type_ not in allowed:
        raise t.newSyntaxError("Unexpected type declaration")
    type = t.token.value 
    return type

def Variables(t, x, decl=None):

    n = decl and Node(t, decl) or Node(t)
    while True:
        n2 = Identifier(t, x, True)

        if n.type_ == LET and x.context == BLOCK: 
            if x.let == None: x.let = n
            x.let.append(n2)
        else: x.decl(decl or n.type_, None, n2, t)

        if decl == STATIC and n2.name in ["__class__", "className", "ancestors", 
                "instances", "scope", "prototype"]:
            raise t.newSyntaxError("%s cannot be used as static variable" % n2.name)

        if t.match(ASSIGN):
            if t.token.assignOp:
                raise t.newSyntaxError("Invalid variable initialization")
            n2.initializer = Expression(t, x, COMMA)

        if decl == MACRO:
            if n2.initializer.type_ in (STRING, NUMBER): pass
            else: raise t.newSyntaxError("Not implemented")

        n2.readOnly = not not (n.type_ == CONST)
        n.append(n2)

        x.scope.add(n2.value, n2)
        
        if not t.match(COMMA): break

    return n

def Let(t, x, context):
    tt = t.peek()
    if tt == LEFT_PAREN: 
        n = Node(t)
        t.get()
        tt = t.peek()
        while True:
            if tt == RIGHT_PAREN: break
            let = Identifier(t,x,True)
            t.mustMatch(ASSIGN)
            let.initializer = Expression(t, x, COMMA)
            tt = t.get()
            n.append(let)
        
        tt = t.peek()
        if tt == LEFT_CURLY:
            t.get()
            n.type_ = LETSTATEMENTS
            x.save()
            x.context = BLOCK
            n.statements = Statements(t,x)
            x.restore()
            t.mustMatch(RIGHT_CURLY)
        else:
            n.type_ = LETEXPRESSION
            n.expression = Expression(t,x)

    else:
        n = Variables(t, x)

    return n

def With(t, x):
    n = Node(t, WITH)

    n.object = ParenExpression(t, x)
    if t.peek() == LEFT_CURLY:
        n.body = nest(t, x, n, Statement)
    else:
        n.body = Expression(t,x)

    return n

def Magic(t, x): 
    if t.token.value == '__FILE__':
        t.token.value = t.filename
    elif t.token.value == '__LINE__':
        t.token.value = t.lineno
    elif t.token.value == '__PATH__': 
        t.token.value = t.path
    elif t.token.value == '__NAMESPACE__': 
        t.token.value = t.ns or x.namespace
    elif t.token.value == '__FUNC__':
        t.token.value = getattr(x, 'funName', None)
    elif t.token.value == '__CLASS__': 
        t.token.value = getattr(x, 'className', None)
    elif t.token.value in ['__PUBLIC__','__PRIVATE__','__STATIC__','__PROTECTED__',
            '__GLOBAL__', '__INTERNAL__','__MACRO__']:
        t.token.value = globals()[str(t.token.value[2:-2])]

    return Node(t)

def Eval(t, x, exp):
    #print "Eval()", exp, x.depth
    
    if x.depth > 0: return

    try:
        if exp.type_ == CLASS:
            jocore.vm.classDef(exp)
        elif exp.type_ == FUNCTION:
            jocore.vm.funDef(exp)
        elif exp.type_ == PACKAGE:
            jocore.vm.packDef(exp)
        else:
            return jocore.vm.eval(exp)
    except (jocore.vm.ReferenceError, jocore.vm.TypeError), ex:
        #err = "%s\n in %s, line %i" % (ex.message, 
                #os.path.join(t.path, t.filename), ex.lineNumber)
        raise
    except jocore.vm.RuntimeError, ex:
        if debug > 1:
            raise jocore.vm.RuntimeError(str(ex))
        else:
            jocore.warning(repr(ex), exp.lineno, "Failed runtime operation")

    return None

def ParenExpression(t, x):
    t.mustMatch(LEFT_PAREN)
    n = Expression(t, x)
    t.mustMatch(RIGHT_PAREN)
    return n

def BracketExpression(t, x):
    t.mustMatch(LEFT_BRACKET)
    n = Expression(t, x)
    t.mustMatch(RIGHT_BRACKET)
    return n

def PropertyName(type, t, x, args=[]):
    _t = t.token.value

    n = Node(t)
    tt = t.get()

    if type == DOT:
        if tt not in (IDENTIFIER, XMLATTR, MUL, NEW, TYPE):
            raise t.newSyntaxError("Unexpected operator after dot")
        if tt == NEW: type = DOTNEW
        if tt in (TYPE,):
            args.append(Node(t, IDENTIFIER))
        else:
            args.append(Node(t))
    elif type == DOTDOT:
        args.append(Node(t))
    elif type == DOTQUERY:
        t.unget()
        t.scanOperand = True
        args.append( Expression(t,x) )
        t.scanOperand = False
        t.get()
    elif type == COLONCOLON:
        args.append(Node(t))

    return Node(t, type, args)

# delete me, please
def PropertyName__(type, t, x, chain, c=0):
    _t = t.token.value

    if type == IDENTIFIER:
        t.get()
        chain.append(Node(t))
    #elif type == LEFT_PAREN: #pass
        #t.get()
        #t.scanOperand = True
        #chain.append(Expression(t,x))
        #t.get()
    #elif type == LEFT_BRACKET: #pass
    elif type in (LEFT_BRACKET, LEFT_PAREN):
        t.get()
        _t = t.peek()
        if type == LEFT_BRACKET: n = Node(t, INDEX)
        elif type == LEFT_PAREN: n = Node(t, CALL)

        if (type == LEFT_BRACKET and _t == RIGHT_BRACKET) or \
            (type == LEFT_PAREN and _t == RIGHT_PAREN):
            chain.append(n)
            t.get()
        else:
            t.scanOperand = True
            e = Expression(t,x)
            chain.append(e)
            t.scanOperand = False
            if type == LEFT_BRACKET: t.mustMatch(RIGHT_BRACKET)
            elif type == LEFT_PAREN: t.mustMatch(RIGHT_PAREN)
    elif type == DOT:
        t.get()
        chain.append(Node(t))
    elif type == DOTDOT:
        t.get()
        chain.append(Node(t))
    elif type == DOTQUERY:
        t.get()
        n = Node(t)
        t.scanOperand = True
        n.expression = Expression(t,x)
        chain.append(n)
        #chain.append(XmlQuery(t,x))
        t.scanOperand = False
        t.get()
    elif type == XMLATTR:
        t.get()
        chain.append(XmlAttribute(t,x))
    elif type == COLONCOLON:
        t.get()
        chain.append(Node(t))
    elif type == MUL:
        t.get()
        chain.append(Node(t))
    '''
    if type == DOT:
        t.mustMatch(IDENTIFIER)
        args.append(Node(t))
    elif type == DOTQUERY:
        args.append( Expression(t,x,RIGHT_PAREN) )
    '''

    tt = t.peek()

    if tt in (IDENTIFIER, DOT, DOTDOT, LEFT_BRACKET, LEFT_PAREN, \
          COLONCOLON, DOTQUERY, XMLATTR, MUL):
        return PropertyName(tt, t, x, chain, c+1)
    else:
        return Node(t, DOT, chain)

def When(t,x,head):
    if head and t.peek() == DO:
        return None

    return Expression(t,x,DO,not head)

def EventHandler(t,x):
    tt = t.peek()
    if tt == DO:
        t.get()
        tt = t.peek()
        if tt == IDENTIFIER:
            t.get()
            return Node(t)
        elif tt == LEFT_CURLY:
            return nest(t, x, Node(t), Statement)

    return None

opPrecedence = {}

opPrecedence_ = {
    "SEMICOLON": 0,
    "COMMA": 1,
    "ASSIGN": 2, "HOOK": 2, "COLON": 2,
    # The above all have to have the same precedence, see bug 330975.
    "OR": 4,
    "AND": 5,
    "BITWISE_OR": 6,
    "BITWISE_XOR": 7,
    "BITWISE_AND": 8,
    "EQ": 9, "NE": 9, "STRICT_EQ": 9, "STRICT_NE": 9,
    "LT": 10, "LE": 10, "GE": 10, "GT": 10, "IN": 10, "INSTANCEOF": 10,
    "LSH": 11, "RSH": 11, "URSH": 11,
    "PLUS": 12, "MINUS": 12,
    "MUL": 13, "DIV": 13, "MOD": 13,
    "DELETE": 14, "VOID": 14, "TYPEOF": 14, "TRACE": 14,
    # "PRE_INCREMENT": 14, "PRE_DECREMENT": 14,
    "NOT": 14, "BITWISE_NOT": 14, "UNARY_PLUS": 14, "UNARY_MINUS": 14,
    "INCREMENT": 15, "DECREMENT": 15,     # postfix
    "NEW": 16,
    "DOTDOT": 17, "COLONCOLON": 17, "DOTQUERY": 17, "XMLATTR": 17,
    "DOT": 18,
}

opArity = {}

opArity_ = {
    "COMMA": -2,
    "ASSIGN": 2,
    "HOOK": 3,
    "OR": 2,
    "AND": 2,
    "BITWISE_OR": 2,
    "BITWISE_XOR": 2,
    "BITWISE_AND": 2,
    "EQ": 2, "NE": 2, "STRICT_EQ": 2, "STRICT_NE": 2,
    "LT": 2, "LE": 2, "GE": 2, "GT": 2, "IN": 2, "INSTANCEOF": 2,
    "LSH": 2, "RSH": 2, "URSH": 2,
    "PLUS": 2, "MINUS": 2,
    "MUL": 2, "DIV": 2, "MOD": 2,
    "OVER": 2, "ON": 2,
    "DELETE": 1, "VOID": 1, "TYPEOF": 1, "TRACE": 1, 
    "WHEN": 1, 
    # "PRE_INCREMENT": 1, "PRE_DECREMENT": 1,
    "NOT": 1, "BITWISE_NOT": 1, "UNARY_PLUS": 1, "UNARY_MINUS": 1,
    "INCREMENT": 1, "DECREMENT": 1,     # postfix
    "NEW": 1, "NEW_WITH_ARGS": 2, "DOT": 2, "INDEX": 2, "CALL": 2,
    "DOTDOT": 2, "COLONCOLON": 2, "DOTQUERY": 2, "XMLATTR": 2,
    "ARRAY_INIT": 1, "OBJECT_INIT": 1, "GROUP": 1
}

def Expression(t, x, stop=None, catchEnd=False):
    stop_ = [] 
    if isinstance(stop, list):
        stop_.extend(stop)
    else: stop_.append(stop)
    operators = []
    operands = []
    bl = x.bracketLevel
    cl = x.curlyLevel
    pl = x.parenLevel
    hl = x.hookLevel

    def reduce_():
        n = operators.pop()
        op = n.type_
        arity = opArity[op]
        if arity == -2:
            # Flatten left-associative trees.
            left = (len(operands) >= 2 and operands[-2])
            if left.type_ == op:
                right = operands.pop()
                left.append(right)
                return left
            arity = 2

        # Always use append to add operands to n, to update start and end.
        a = operands[-arity:]
        del operands[-arity:]
        for operand in a:
            n.append(operand)

        # Include closing bracket or postfix operator in [start,end).
        if n.end < t.token.end:
            n.end = t.token.end

        operands.append(n)
        return n

    class BreakOutOfLoops(Exception): pass
    try:
        while True:
            #if catchEnd and t.peekOnSameLine() in (END, SEMICOLON, NEWLINE):
                #raise BreakOutOfLoops

            tt = t.get()
            #print "parenLevel", x.parenLevel
            #print "exp(%s) %s, %s, %s" % (t.token.value, t.scanOperand, tt, stop)

            if tt == END: break
            if (tt in stop_ and x.bracketLevel == bl and x.curlyLevel == cl and
                    x.parenLevel == pl and x.hookLevel == hl):
                # Stop only if tt matches the optional stop parameter, and that
                # token is not quoted by some kind of bracket.
                break
            if tt == SEMICOLON:
                # NB: cannot be empty, Statement handled that.
                raise BreakOutOfLoops

            elif tt in (ASSIGN, HOOK, COLON):
                if t.scanOperand:
                    raise BreakOutOfLoops
                while ((operators and opPrecedence.get(operators[-1].type_,
                        None) > opPrecedence.get(tt)) or (tt == COLON and
                        operators and operators[-1].type_ == ASSIGN)):
                    reduce_()
                if tt == COLON:
                    if operators:
                        n = operators[-1]
                    if not operators or n.type_ != HOOK:
                        raise t.newSyntaxError("Invalid label")
                    x.hookLevel -= 1
                else:
                    operators.append(Node(t))
                    if tt == ASSIGN:
                        operands[-1].assignOp = t.token.assignOp
                    else:
                        x.hookLevel += 1

                t.scanOperand = True

            elif tt in (IN, COMMA, OR, AND, BITWISE_OR, BITWISE_XOR,
                    BITWISE_AND, EQ, NE, STRICT_EQ, STRICT_NE, LT, LE, GE, GT,
                    INSTANCEOF, LSH, RSH, URSH, PLUS, MINUS, MUL, DIV, MOD,
                    DOT, DOTDOT, DOTQUERY, COLONCOLON,
                    ON, OVER):

                # We're treating comma as left-associative so reduce can fold
                # left-heavy COMMA trees into a single array.
                if tt in (IN, ON, OVER):
                    # An in operator should not be parsed if we're parsing the
                    # head of a for (...) loop, unless it is in the then part of
                    # a conditional expression, or parenthesized somehow.
                    if (x.inForLoopInit and not x.hookLevel and not
                            x.bracketLevel and not x.curlyLevel and
                            not x.parenLevel):
                        raise BreakOutOfLoops

                # XML stream encountered in expression.
                if tt == LT and t.scanOperand:
                    operands.append(XmlStream(t,x))
                    t.scanOperand = False
                else:
                    if t.scanOperand:
                        raise BreakOutOfLoops
                    while (operators and opPrecedence.get(operators[-1].type_)
                            >= opPrecedence.get(tt)):
                        reduce_()

                    if tt in (DOT, DOTDOT, DOTQUERY, COLONCOLON):
                        args = []
                        if len(operands): args.append(operands.pop())
                        p = PropertyName(tt, t, x, args)
                        #p.type_ = tt
                        operands.append(p)
                    else:
                        operators.append(Node(t))
                        t.scanOperand = True

            elif tt in (DELETE, VOID, TYPEOF, NOT, BITWISE_NOT, UNARY_PLUS,
                    UNARY_MINUS, NEW, TRACE, WHEN):

                if not t.scanOperand:
                    raise BreakOutOfLoops

                if tt == VOID and t.peek() == FUNCTION:
                    t.unget()
                    returnType = typeDef(t,x,FUNCTION)
                    t.get()
                    operands.append(FunctionDefinition(t, x, False, EXPRESSED_FORM, None, returnType))
                    t.scanOperand = False
                else:
                    operators.append(Node(t))

            elif tt in (INCREMENT, DECREMENT):
                if t.scanOperand:
                    operators.append(Node(t)) # prefix increment or decrement
                else:
                    # Don't cross a line boundary for postfix {in,de}crement.
                    if (t.tokens.get((t.tokenIndex + t.lookahead - 1)
                            & 3).lineno != t.lineno):
                        raise BreakOutOfLoops

                    # Use >, not >=, so postfix has higher precedence than
                    # prefix.
                    while (operators and opPrecedence.get(operators[-1].type_,
                            None) > opPrecedence.get(tt)):
                        reduce_()
                    n = Node(t, tt, [operands.pop()])
                    n.postfix = True
                    operands.append(n)

            elif tt == LET:
                if not t.scanOperand:
                    raise BreakOutOfLoops
                operands.append(Let(t,x.clone(),x.context))
                t.scanOperand = False

            elif tt == FUNCTION:
                if not t.scanOperand:
                    raise BreakOutOfLoops
                operands.append(FunctionDefinition(t, x, False, EXPRESSED_FORM))
                t.scanOperand = False

            elif tt == CLASS:
                if not t.scanOperand:
                    raise BreakOutOfLoops
                operands.append(ClassDefinition(t, x, False, EXPRESSED_FORM))
                t.scanOperand = False

            elif tt == XMLATTR:
                if not t.scanOperand:
                    raise BreakOutOfLoops
                operands.append(Node(t))
                t.scanOperand = False

            elif tt in (NULL, UNDEFINED, THIS, SELF, TRUE, FALSE, IDENTIFIER, 
                    NUMBER, STRING, REGEXP, MAGIC):
                   
                if tt == SELF and x.context != CLASS:
                    raise t.newSyntaxError("self allowed only in class context")

                if not t.scanOperand:
                    raise BreakOutOfLoops

                if tt == MAGIC: n = Magic(t,x)
                else: n = Node(t)
                operands.append(n)
                t.scanOperand = False

            elif tt == LEFT_BRACKET:
                if t.scanOperand:
                    # Array initializer. Parse using recursive descent, as the
                    # sub-grammer here is not an operator grammar.
                    n = Node(t, ARRAY_INIT)
                    while True:
                        tt = t.peek()
                        if tt == RIGHT_BRACKET: break
                        if tt == COMMA:
                            t.get()
                            n.append(None)
                            continue
                        n.append(Expression(t, x, COMMA))
                        if not t.match(COMMA):
                            break
                    t.mustMatch(RIGHT_BRACKET)
                    operands.append(n)
                    t.scanOperand = False
                else:
                    operators.append(Node(t, INDEX))
                    t.scanOperand = True
                    x.bracketLevel += 1

            elif tt == RIGHT_BRACKET:
                if t.scanOperand or x.bracketLevel == bl:
                    raise BreakOutOfLoops
                while reduce_().type_ != INDEX:
                    continue
                x.bracketLevel -= 1

            elif tt == LEFT_CURLY:
                if not t.scanOperand:
                    raise BreakOutOfLoops
                # Object initializer. As for array initializers (see above),
                # parse using recursive descent.
                x.curlyLevel += 1
                n = Node(t, OBJECT_INIT)

                class BreakOutOfObjectInit(Exception): pass
                try:
                    if not t.match(RIGHT_CURLY):
                        while True:
                            tt = t.get()
                            if ((t.token.value == "get" or
                                    t.token.value == "set") and
                                    t.peek == IDENTIFIER):
                                if x.ecmaStrictMode:
                                    raise t.newSyntaxError("Illegal property "
                                            "accessor")
                                n.append(FunctionDefinition(t, x, True,
                                        EXPRESSED_FORM))
                            else:
                                if tt in (IDENTIFIER, NUMBER, STRING, XML, TYPE):
                                    id_ = Node(t)
                                elif tt == MAGIC:
                                    id_ = Magic(t, x)
                                elif tt == RIGHT_CURLY:
                                    if x.ecmaStrictMode:
                                        raise t.newSyntaxError("Illegal "
                                                "trailing ,")
                                    raise BreakOutOfObjectInit
                                else:
                                    raise t.newSyntaxError("Invalid property "
                                            "name")
                                t.mustMatch(COLON)
                                for p in n:
                                    if getattr(p, 'type_', None) == PROPERTY_INIT and \
                                            getattr(p[0], 'value', None) == id_.value:
                                        strictErr(t, x, 
                                                "Object initializer have "
                                                "already defined property " + id_.value)
                                n.append(Node(t, PROPERTY_INIT, [id_,
                                        Expression(t, x, COMMA)]))
                            if not t.match(COMMA): break
                        t.mustMatch(RIGHT_CURLY)
                except BreakOutOfObjectInit, e: pass
                operands.append(n)
                t.scanOperand = False
                x.curlyLevel -= 1

            elif tt == RIGHT_CURLY:
                if not t.scanOperand and x.curlyLevel != cl:
                    raise ParseError("PANIC: right curly botch")
                raise BreakOutOfLoops

            elif tt == LEFT_PAREN:
                if t.scanOperand:
                    operators.append(Node(t, GROUP))
                    x.parenLevel += 1
                else:
                    while (operators and
                            opPrecedence.get(operators[-1].type_) >
                            opPrecedence[NEW]):
                        reduce_()

                    # Handle () now, to regularize the n-ary case for n > 0.
                    # We must set scanOperand in case there are arguments and
                    # the first one is a regexp or unary+/-.
                    if operators:
                        n = operators[-1]
                    else:
                        n = Object()
                        n.type_ = None
                    t.scanOperand = True
                    if t.match(RIGHT_PAREN):
                        if n.type_ == NEW:
                            operators.pop()
                            n.append(operands.pop())
                        else:
                            n = Node(t, CALL, [operands.pop(), Node(t, LIST)])
                        operands.append(n)
                        t.scanOperand = False
                    else:
                        if n.type_ == NEW:
                            n.type_ = NEW_WITH_ARGS
                        else:
                            operators.append(Node(t, CALL))
                        x.parenLevel += 1

            elif tt == RIGHT_PAREN:
                if t.scanOperand or x.parenLevel == pl:
                    raise BreakOutOfLoops
                while True:
                    tt = reduce_().type_
                    if tt in (GROUP, CALL, NEW_WITH_ARGS):
                        break
                if tt != GROUP:
                    if operands:
                        n = operands[-1]
                        if n[1].type_ != COMMA:
                            n[1] = Node(t, LIST, [n[1]])
                        else:
                            n[1].type_ = LIST
                    else:
                        raise ParseError, "Unexpected amount of operands"
                x.parenLevel -= 1

            # Automatic semicolon insertion means we may scan across a newline
            # and into the beginning of another statement. If so, break out of
            # the while loop and let the t.scanOperand logic handle errors.
            else:
                raise BreakOutOfLoops
    except BreakOutOfLoops, e: pass

    if x.hookLevel != hl:
        raise t.newSyntaxError("Missing : after ?")
    if x.parenLevel != pl:
        raise t.newSyntaxError("Missing ) in parenthetical")
    if x.bracketLevel != bl:
        raise t.newSyntaxError("Missing ] in index expression")
    if t.scanOperand:
        raise t.newSyntaxError("Missing operand")

    t.scanOperand = True
    t.unget()
    while operators:
        reduce_()
    #print "Expression() operands: %s" % operands
    return operands.pop()

def ValidatePackage(t,x,class_=False):
    if not x.public_class:
        err = ("In %s must be " % (class_ and t.filename or 'package')) + \
                "declared at least one public class "
        if class_:
            err += t.filename.split(".")[0]
        raise t.newSyntaxError(err)

def Include(t,x): pass

