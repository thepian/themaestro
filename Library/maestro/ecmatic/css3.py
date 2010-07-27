"""
A grammar for parsing a tiny CSS-like language, plus a transformer for it.
"""
from pymeta.grammar import OMeta
from itertools import chain

tinyCSSGrammar = """

name ::= <letterOrDigit>+:ls => ''.join(ls)

tag ::= ('<' <spaces> <name>:n <spaces> <attribute>*:attrs '>'
         <html>:c
         '<' '/' <token n> <spaces> '>'
             => [n.lower(), dict(attrs), c])

html ::= (<text> | <tag>)*

text ::= (~('<') <anything>)+:t => ''.join(t)

attribute ::= <spaces> <name>:k <token '='> <quotedString>:v => (k, v)

quotedString ::= (('"' | '\''):q (~<exactly q> <anything>)*:xs <exactly q>
                     => ''.join(xs))

"""
TinyCSS = OMeta.makeGrammar(tinyCSSGrammar, globals(), name="TinyCSS")

