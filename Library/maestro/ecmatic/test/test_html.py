from pymeta.grammar import OMeta, OMetaGrammar
from pymeta.runtime import ParseError as OMetaParseError
import os
import unittest

html_grammar = r"""
hspace    = ' ' | '\t'
vspace    = '\n'
optspace  = ?(self.parenthesis) (hspace | '\\'? vspace | comment)* | (hspace | '\\' vspace)* comment?
mandspace = ?(self.parenthesis) (hspace | '\\'? vspace | comment)+ | (hspace | '\\' vspace)+ comment?

comment  = '#' line_rest:c -> ['comment', c]

name_start = letter | '$' | '_'
name_rest = name_start | digit
iname = name_start:s name_rest*:r -> s + ''.join(r)
isreserved :x = ?(self.is_reserved(x))
name = iname:n ~isreserved(n)  -> ['name',n]

escaped_char = '\\' :x -> ('\\' + x).decode('string_escape')
string3 :e = match_string(e) (escaped_char | ~(?(len(e) != 3) vspace | match_string(e)) anything)*:c match_string(e) -> ''.join(c)
string2 = string3('\"\"\"') | string3("\'\'\'") | string3('"') | string3("'")
string = (string2:s optspace -> s)+:s -> ['string', ''.join(s)]

tag = '<' name:n '>' html:c '<' '/' token:n '>'
html = tag*
"""

"""
tag = '<' spaces name:n spaces attribute*:attrs '>' html:c '<' '/' token:n spaces '>'
        -> [n.lower(), dict(attrs), c]

html = (text | tag)*

text = (~('<') anything)+:t -> ''.join(t)

attribute = spaces name:k '=' quotedString:v -> (k, v)

quotedString = (('"' | '\''):q (~exactly:q anything)*:xs exactly:q
                     -> ''.join(xs))
"""

def p(s):
    print s
    
class Grammar(OMeta.makeGrammar(html_grammar, {'p': p})):
    def is_reserved(self,name):
        "Is the attribute name reserved"
        return False
    

class GrammarTestCase(unittest.TestCase):
    
    def test_makeGrammar(self):
        g = Grammar("<html><body></body></html>")
        print g.apply("html")
        # self.assertEqual(g.apply("num")[0], 314159)
        # self.assertNotEqual(len(results), 0)

    