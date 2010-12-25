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
attributes = (attribute:a ' ')+ -> a
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
