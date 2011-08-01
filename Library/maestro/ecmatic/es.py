from __future__ import with_statement
from pymeta.grammar import OMeta
import os

def translate(source,**insert_vars):
    r = Grammar(source).apply("statements")[0]
    r = expand_macros(r,insert_vars=insert_vars)
    return Grammar(r).apply("statements_out")[0]
    
def load_and_translate(path,**insert_vars):
    import codecs
    with codecs.open(path,"r",encoding="utf-8") as f:
        text = f.read()
        return text, translate(text,**insert_vars)
    
def load_expand_and_translate(path,**insert_vars):
    import codecs
    with codecs.open(path,"r",encoding="utf-8") as f:
        text = f.read()
        r = Grammar(text).apply("statements")[0]
        r = expand_macros(r,insert_vars=insert_vars)
        return text, r, Grammar(r).apply("statements_out")[0]
    
def load_raw(path):
    import codecs
    with codecs.open(path,"r",encoding="utf-8") as f:
        source = f.read()
        return source

def load_and_parse(path):
    import codecs
    with codecs.open(path,"r",encoding="utf-8") as f:
        source = f.read()
        r = Grammar(source).apply("statements")[0]
        return source, r

def compile(source):
    return Translator.parse(Grammar.parse(source))

grammar_path = os.path.join(os.path.dirname(__file__), 'es.ometa')
es_grammar = None
with open(grammar_path, 'r') as f:
    es_grammar = f.read()
    
def p(s):
    print s
    return s

def uc(name):
    return {
        'SP': ' ', 'TAB': '\t', 'NBSP': '\0xA0',
        'CR': '\n', 'LF': '\r',
        'VT': "", 'FF': "", 'BOM': "", 'Zs': "",
        'PS': "", 'LS': ""
    }[name]
    
class Token(object):
    def __init__(self,keyword,prefix):
        self.keyword = keyword
        self.prefix = prefix

    def __eq__(self,other):
        if not hasattr(other,"keyword") or other.keyword != self.keyword: return False
        if not hasattr(other,"prefix") or other.prefix != self.prefix: return False
        return True

    def __repr__(self):
        import pprint
        return pprint.PrettyPrinter().pformat({
            "keyword":self.keyword, "prefix":self.prefix
        })



class Grammar(OMeta.makeGrammar(es_grammar, {'p': p, 'uc': uc, 'Token':Token }, name="EcmaScript")):
    
    hex_digits = '0123456789abcdefABCDEF'

    keywords = set((
        "break","do","instanceof","typeof","case","else","new","var","catch","finally",
         "return", "void", "continue", "for", "switch", "while", "debugger", "function",
         "this", "with", "default", "if", "throw", "delete", "in", "try"
    ))
    nonStrictFutureKws = set((
        "class", "enum", "extends", "super", "const", "export", "import"
    ))
    strictFutureKws = set((
        "implements", "let", "private", "public", "interface", "package",
         "protected", "static", "yield"
    ))
    # PageSpec expectations keywords
    extraKeywords = set(("should","after_ms","within_ms","after","within"))
      
    def __init__(self, *args, **kwargs):
        super(Grammar, self).__init__(*args, **kwargs)
        self.parenthesis = 0
        self.parenthesis_stack = []

    def enter_paren(self):
        self.parenthesis += 1

    def leave_paren(self):
        self.parenthesis -= 1

    def is_reserved(self,name):
        "Is the attribute name reserved"
        if name in self.extraKeywords:
            return True
        return name in self.keywords
        
    describe_out_text = '''\
function(__expect__){
    return [
%(stmts)s
%(constr)s, %(caption)s
];
}'''
    it_out_text = '''
%(caption)s, function(){ if (__expect__.dn) debugger;
%(stmts)s
    },
'''
    should_out_text = '''
        if (__expect__.dne) debugger; __expect__(function(){return %s;}, %s, %s);
'''
    should_rhs_out_text = ''''%s', function(){ return %s; }, %s'''
    

    # def should_lhs_to_text(self,lhs):

    def quote_text(self,text):
        return "'%s'" % text.replace("'",r"\'")

scopes = {}

class Scope(object):
    def __init__(self,source):
        self.source = source
        self.parsed, self.error = Grammar(source).apply("statements")
        # print self.source, "==>",self.parsed
    
    def wrap(self,node, insert_vars):
        return expand_macros(self.parsed,insert=node,insert_vars=insert_vars)
        
def add_scope(name,source):
    scopes[name.replace("'",'"')] = Scope(source)
    
def load_and_add_scope(name,path):
    import codecs
    with codecs.open(path,"r",encoding="utf-8") as f:
        source = f.read()
        scopes[name.replace("'",'"')] = Scope(source)
    
def extract_examples(tree):
    def scan(root):
        for node in root:
            if type(node) == list:
                if len(node) == 0:
                    pass
                elif node[0] == "it":
                    examples.append(node)
                else:
                    scan(node)

    examples = []
    scan(tree)
    return examples

def expand_macros(tree,insert=None,insert_vars={}):
    # print insert_vars
    def wrap_scope(node):
        scope = node[2] in scopes and scopes[node[2].replace("'",'"')] or Scope('/*no scope '+node[2].replace("'",'"')+'*/@insert();')
        return scope.wrap(node[4], insert_vars)
        
    def wrap_expand(node):
        return node
        
    def wrap_import(node):
        return ["statement","var", " ",node[2],"=","resolver",["parenthesis",[]],["parenthesis",['"',node[1],'"']],";"]
        
    def wrap_define(node):
        return node
        
    def expand(root):
        r = []
        for node in root:
            if type(node) == list:
                if len(node) == 0:
                    r.append([])
                elif node[0] == "insert":
                    if len(node) == 1:
                        node = expand(insert)
                    else:
                        from thepian.conf import structure
                        if node[1] == "path raw":
                            try:
                                path = structure.JS_DIR + "/" + node[2].replace("'","").replace('"',"")
                                source = load_raw(path)
                                node = [source]
                            except IOError,e:
                                node = ["/* No such file %s */" % node[2]]
                        elif node[1] == "path":
                            try:
                                path = structure.JS_DIR + "/" + node[2].replace("'","").replace('"',"")
                                node = load_and_parse(path)[1]
                            except IOError,e:
                                node = ["/* No such file %s */" % node[2]]
                        elif node[1] == "var":
                            if node[2] in insert_vars:
                                node = [insert_vars[node[2]]]
                            else:
                                node = ["/* No such var %s */" % node[2]]
                    r.extend(expand(node))
                elif node[0] == "scope":
                    node = wrap_scope(node)
                    r.extend(expand(node))
                elif node[0] == "expand":
                    node = wrap_expand(node)
                    r.append(expand(node))
                elif node[0] == "import":
                    node = wrap_import(node)
                    r.append(expand(node))
                elif node[0] == "define":
                    node = wrap_define(node)
                    r.append(expand(node))
                else:
                    r.append(expand(node))
            else:
                r.append(node)
        return r
        
    return expand(tree)    

"""
Comment = MultiLineComment || SingleLineComment

MultiLineComment = "/*" (MultiLineCommentChars | empty):cs "*/" -> cs
MultiLineCommentChars = MultiLineNotAsteriskChar (MultiLineCommentChars | empty) || '*' (PostAsteriskCommentChars | &seq("*/"))
PostAsteriskCommentChars = MultiLineNotForwardSlashOrAsteriskChar (MultiLineCommentChars | empty) || '*' (PostAsteriskCommentChars | &seq("*/"))
MultiLineNotAsteriskChar = ~('*') SourceCharacter,
MultiLineNotForwardSlashOrAsteriskChar = ~('/' || '*') SourceCharacter
SingleLineComment = "//" (SingleLineCommentChars | empty)
SingleLineCommentChars = SingleLineCommentChar (SingleLineCommentChars | empty)
SingleLineCommentChar = ~LineTerminator SourceCharacter
"""