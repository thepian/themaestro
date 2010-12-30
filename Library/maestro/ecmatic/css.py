from __future__ import with_statement
from pymeta.grammar import OMeta
import os

def compile(source):
    return Translator.parse(Grammar.parse(source))

grammar_path = os.path.join(os.path.dirname(__file__), 'css.ometa')
css_grammar = None
with open(grammar_path, 'r') as f:
    css_grammar = f.read()
