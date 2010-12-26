from __future__ import with_statement
from pymeta.grammar import OMeta
import os

def compile(source):
    return Translator.parse(Grammar.parse(source))

grammar_path = os.path.join(os.path.dirname(__file__), 'es.ometa')
html_grammar = None
with open(grammar_path, 'r') as f:
    html_grammar = f.read()
    
def p(s):
    print s

def uc(name):
    return {
        'SP': ' ', 'TAB': '\t', 'NBSP': '\0xA0',
        'CR': '\n', 'LF': '\r',
        'VT': "", 'FF': "", 'BOM': "", 'Zs': "",
        'PS': "", 'LS': ""
    }[name]

class Grammar(OMeta.makeGrammar(html_grammar, {'p': p, 'uc': uc}, name="EcmaScript")):
    
    hex_digits = '0123456789abcdef'

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
        return False


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