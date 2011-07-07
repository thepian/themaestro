from __future__ import with_statement
from pymeta.grammar import OMeta
import os

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
        return name in self.keywords
        
    describe_out_text = '''
(function(){
    var pagespec = resolver()("pagespec");
    pagespec.current_constr = %s;
    pagespec.current_caption = %s;
%s
})();
'''
    it_out_text = '''
    pagespec.example_name = %s;
    (function(){
        %s
    })();
'''
    should_out_text = '''
        pagespec.expect(%s,%s,pagespec.should["%s"],function(){return %s;});
'''

    def quote_text(self,text):
        return "'%s'" % text.replace("'",r"\'")

scopes = {}

class Scope(object):
    def __init__(self,source):
        self.source = source
        self.parsed, self.error = Grammar(source).apply("statements")
        # print self.source, "==>",self.parsed
    
    def wrap(self,node):
        return expand_macros(self.parsed,node)
        
def add_scope(name,source):
    scopes[name.replace("'",'"')] = Scope(source)
    
def expand_macros(tree,insert=None):
    
    def wrap_scope(node):
        scope = node[2] in scopes and scopes[node[2].replace("'",'"')] or Scope('/*no scope '+node[2]+'*/@insert();')
        return scope.wrap(node[4])
        
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
                    node = expand(insert)
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