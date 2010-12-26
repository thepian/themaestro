from __future__ import with_statement

import unittest

from ecmatic.es import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    def test_comment(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("comment")
        assert result == ["comment", " hello"]
        
    def test_constant(self):
        g = Grammar("""\
"abc"\
""")
        result,error = g.apply("string")
        assert result == "abc"
        
    def test_expression(self):
        result, error = Grammar("a + b - 5").apply("expr")
        assert result == ['binop', '-', ['binop', '+', 'a', 'b'],['number', 5]]

        result, error = Grammar("a + b * 5").apply("expr")
        assert result == ['binop', '+', 'a', ['binop', '*', 'b', ['number', 5]]]

        result, error = Grammar("a == b + 5").apply("expr")
        assert result == ['binop', '==', 'a', ['binop', '+', 'b', ['number', 5]]]

        result, error = Grammar("a == b + 0x5").apply("expr")
        assert result == ['binop', '==', 'a', ['binop', '+', 'b', ['hexnumber', 5]]]
        
        result, error = Grammar("a || b || c").apply("expr")
        assert result == ['binop', '||', ['binop', '||', 'a', 'b'], 'c']

        result, error = Grammar("a && b && c").apply("expr")
        assert result == ['binop', '&&', ['binop', '&&', 'a', 'b'], 'c']

