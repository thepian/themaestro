from __future__ import with_statement
from pymeta.grammar import OMeta
import os

def compile(source):
    return Translator.parse(Grammar.parse(source))

grammar_path = os.path.join(os.path.dirname(__file__), 'html.ometa')
html_grammar = None
with open(grammar_path, 'r') as f:
    html_grammar = f.read()
    
def p(s):
    print s

class Grammar(OMeta.makeGrammar(html_grammar, {'p': p}, name="HTML")):
    def is_reserved(self,name):
        "Is the attribute name reserved"
        return False

