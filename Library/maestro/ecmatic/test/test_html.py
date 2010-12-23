from pymeta.grammar import OMeta, OMetaGrammar
from pymeta.runtime import ParseError as OMetaParseError
import os
import unittest

html_grammar = r"""
hspace    = ' ' | '\t'
vspace    = '\n'

name_start = letter | '?' | '!'
name_rest = name_start | digit
iname = name_start:s name_rest*:r -> s + ''.join(r)
isreserved :x = ?(self.is_reserved(x))
name = iname:n ~isreserved(n)  -> n

string3 :e = match_string(e) (~(match_string(e)) anything)*:c match_string(e) -> ''.join(c)
string2 = string3('"') | string3("'")
string = (string2:s -> s)+:s -> ''.join(s)

tag = '<' spaces name:n spaces attribute*:attrs '>' html:c '<' '/' name:n spaces '>'
        -> [n.lower(), dict(attrs), c]

html = (text | tag)*

text = (~('<') anything)+:t -> ''.join(t)

string_attribute = name:k '=' string:v -> (k, v)
bool_attribute = name:k (~('=') anything)? -> (k,True)
attribute = spaces (string_attribute | bool_attribute)  
attributes = spaces attribute*:attrs spaces -> dict(attrs)
"""

def p(s):
    print s
    
class Grammar(OMeta.makeGrammar(html_grammar, {'p': p}, name="HTML")):
    def is_reserved(self,name):
        "Is the attribute name reserved"
        return False
    

class GrammarTestCase(unittest.TestCase):
    
    def test_whitespace(self):
        g = Grammar("<html> </html>")
        result,error = g.apply("html")
        assert result == [["html", {}, [" "]]]

        g = Grammar(" <html> </html>")
        result,error = g.apply("html")
        assert result == [" ",["html", {}, [" "]]]

        g = Grammar("""
   <html> </html>""")
        result,error = g.apply("html")
        assert result == ["\n   ",["html", {}, [" "]]]

    def test_html_language(self):
        g = Grammar("<html language='en'> </html>")
        result,error = g.apply("html")
        assert result == [["html", { 'language':'en' }, [" "]]]

    def test_string_attr(self):
        g = Grammar('a="b"')
        result, error = g.apply("string_attribute")
        assert result == ("a","b") 

        g = Grammar('a="b" c="d"')
        result, error = g.apply("attributes")
        assert result == { "a":"b", "c":"d" } 

    def test_bool_attr(self):
        g = Grammar('a')
        result, error = g.apply("bool_attribute")
        assert result == ("a",True) 

        g = Grammar('a c')
        result, error = g.apply("attributes")
        assert result == { "a":True, "c":True } 

        g = Grammar("""\
<html><body><input disabled ></input></body></html>
""")
        result,error = g.apply("html")
        print error
        assert result == [
            ["html", {}, [
                ['body', {}, [['input', { "disabled":True }, [] ]]]
                ]],
            '\n']

    def notest_doctype(self):
         g = Grammar("""\
<|DOCTYPE html>
<html> </html>""")
         result,error = g.apply("html")
         assert result == [["html", {}, [" "]]]
        