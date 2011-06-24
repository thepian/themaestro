from __future__ import with_statement

import unittest

from ecmatic.es import Grammar    

class GrammarTestCase(unittest.TestCase):
    
    def assertExpression(self, expr, expected):
        result, error = Grammar(expr).apply("expr")
        print result
        assert result == expected
        
    def assertStatements(self, expr, expected):
        result, error = Grammar(expr).apply("statements")
        print result
        assert result == expected
    
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
        assert result == '"abc"'
        
    def test_expression(self):
        self.assertExpression("a + b - 5", ["a", " ", "+", " ", "b", " ", "-", " ", "5"])
        self.assertExpression("a == b + 0x5", ["a"," ","=="," ","b"," ","+"," ","0x5"])
        self.assertExpression("a = b > .5e-10", ["a"," ","="," ","b"," ",">"," ",".5e","-","10"])
        self.assertExpression("a + b/*...*/ - 5", ["a", " ", "+", " ", "b", "/*...*/", " ", "-", " ", "5"])
        
        # ['call', ["a",".","f"],["a"," ","+"," ","b"]]
        # ['call', ["new"," ","a",".","f"],["a"," ","+"," ","b"]]
        # ['index', ["a",".","f"],["a"," ","+"," ","b"]]
        # ['paren',["5"]]

        """
        inline function void
        conditional ?:
        operators: single, combo, assignments
        lhs expr: just that, call, index, this
        simple expression: obj array lit space comment ()
        """
        
    def test_statements(self):
        self.assertStatements("""a?b:c""", [ ["conditional", ["a"], ["b"], ["c"]] ])
        self.assertStatements("""[(5)]""", [["square",[ ["parenthesis", [ "5" ] ] ]]])
        self.assertStatements("""function(){}""", [["function", [], [], None, [], [], [], [] ]])
        
        self.assertStatements("""function(a){ b }""", [["function", [], [], None, [], ["a"], [], [" ","b"," "] ]])
        self.assertStatements("""function a(b) {c;d}""", [["function", [], [" "], "a", [], ["b"], [" "], ["c",";","d"] ]])
        self.assertStatements("""var f = function(){};""", ["var"," ", "f", " ","="," ",["function", [], [], None, [], [], [], [] ], ";"])
        self.assertStatements("""function(){void(0);}""", [["function", [], [], None, [], [], [], ["void", ["parenthesis",["0"]],";"] ]])
        
        self.assertStatements("""{a:b,c:d}""", [[ "curly",["a",":","b", ",", "c",":","d"] ]])
        self.assertStatements("""{"a":"b","c":"d"}""", [[ "curly",['"a"',":",'"b"', ",", '"c"',":",'"d"'] ]])
        
        self.assertStatements("""[1,"b",function(){}]""",
            [ ["square",[ "1", ",", '"b"', ",", [ "function", [], [], None, [], [], [], [] ] ]] ])
        
        self.assertStatements("""if(a==b){ print x; }""",
            [ "if", ["parenthesis", ["a","==","b"]], ["curly", [" ", "print", " ", "x", ";"," "]] ])
            
    def test_macros(self):
        self.assertStatements("""@scope "a/b/c"  { function(){} }""", [
            ["scope", [" "], '"a/b/c"', [" "," "], [
                " ", [ "function", [], [], None, [], [], [], [] ], " "
            ]]
            ])