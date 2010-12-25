from __future__ import with_statement
from pymeta.grammar import OMeta

import unittest

from ecmatic.es import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    
    def test_constant_bits(self):
        Grammar = OMeta.makeGrammar(r"""
var = 'v' 'a' 'r' spaces letter+:name ';' -> ['var', ''.join(name)]
""", {})
        g = Grammar("var myvar;")
        result,error = g.apply("var")
        assert result == ['var', 'myvar']
        
    def no_test_read_ahead(self):
        Grammar = OMeta.makeGrammar(r"""
attribute = bool | valued
bool = (letter+):name &(anything ~('=')) -> [name,True]
valued = (letter+):name '=' (letter+):value -> [name,value]
""", {})

        g = Grammar("a=b")
        result,error = g.apply("valued")
        assert result == ('a','b')
