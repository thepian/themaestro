from __future__ import with_statement
from pymeta.grammar import OMeta

import unittest

from ecmatic.es import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    
    def test_constant_bits(self):
        Grammar = OMeta.makeGrammar(r"""
var = "var" spaces letter+:name ';' -> ['var', ''.join(name)]
""", {})
        g = Grammar("var myvar;")
        result,error = g.apply("var")
        assert result == ['var', 'myvar']
        
    def test_read_ahead(self):
        Grammar = OMeta.makeGrammar(r"""
attribute = bool | valued
bool = (letter+):name ~('=') -> (''.join(name),True)
valued = (letter+):name '=' (letter+):value -> (''.join(name),''.join(value))
""", {})

        g = Grammar("a")
        result,error = g.apply("attribute")
        assert result == ('a',True)

        g = Grammar("a=b")
        result,error = g.apply("attribute")
        assert result == ('a','b')

    def test_nested_productions(self):
        Grammar = OMeta.makeGrammar(r"""
attributes = spaces (attribute:a spaces -> a)+:as -> as
attribute = bool | valued
bool = (letter+):name ~('=') -> (''.join(name),True)
valued = (letter+):name '=' (letter+):value -> (''.join(name),''.join(value))
""", {})

        g = Grammar("a=b")
        result,error = g.apply("attributes")
        assert result == [('a','b')]

        g = Grammar("a=b c d=e")
        result,error = g.apply("attributes")
        assert result == [('a','b'),('c',True),('d','e')]
        

    def test_optional(self):
        Grammar = OMeta.makeGrammar(r"""
word_comment = "/*" ' '? letter*:t ' '? "*/" -> ['comment', ''.join(t)]
""", {})
        result,error = Grammar("/* abc */").apply("word_comment")
        assert result == ['comment', 'abc']
        
        result,error = Grammar("/*abc*/").apply("word_comment")
        assert result == ['comment', 'abc']

        result,error = Grammar("/* */").apply("word_comment")
        assert result == ['comment', '']

        result,error = Grammar("/**/").apply("word_comment")
        assert result == ['comment', '']
        
    def test_builtins(self):
        # empty char spaces letter anything begin end
        pass

    def tets_cr_nl_encoding(self):
        pass
