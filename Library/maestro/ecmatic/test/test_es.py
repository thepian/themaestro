from __future__ import with_statement

import unittest

from ecmatic.es import Grammar, expand_macros, add_scope, scopes    

class GrammarTestCase(unittest.TestCase):
    
    def assertExpression(self, expr, expected):
        result, error = Grammar(expr).apply("expr")
        assert result == expected
        
    def assertStatements(self, expr, expected):
        result, error = Grammar(expr).apply("statements")
        # print '>>', result
        # print '==', expected
        assert result == expected
    
    def assertExpressionsOut(self, expr, expected, rule = "exprs_out"):
        result, error = Grammar(expr).apply(rule)
        assert result == expected

    def assertStatementsOut(self, expr, expected, rule = "statements_out"):
        result, error = Grammar(expr).apply(rule)
        assert result == expected

    def test_comment(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("comment")
        assert result == ["comment", " hello"]
        g = Grammar("""\
/* hello */""")
        result,error = g.apply("slcomment")
        assert result == ["slcomment", " hello "]

        g = Grammar("""\
/* hello */""")
        result,error = g.apply("mlcomment")
        assert result == ["mlcomment", " hello "]
        
        g = Grammar("""\
/* hello "a/b/c"*/""")
        result,error = g.apply("mlcomment")
        assert result == ["mlcomment", ' hello "a/b/c"']
        
        #TODO slcomment in statements and expressions

    def test_constant(self):
        g = Grammar("""\
"abc"\
""")
        result,error = g.apply("string")
        assert result == '"abc"'

        g = Grammar("""\
'abc'\
""")
        result,error = g.apply("string")
        assert result == "'abc'"
        
    def test_expression(self):
        self.assertExpression("a + b - 5", ["a", " ", "+", " ", "b", " ", "-", " ", "5"])
        self.assertExpression("a == b + 0x5", ["a"," ","=="," ","b"," ","+"," ","0x5"])
        self.assertExpression("a = b > .5e-10", ["a"," ","="," ","b"," ",">"," ",".5e","-","10"])
        self.assertExpression("a + b/*...*/ - 5", ["a", " ", "+", " ", "b", ["slcomment","..."], " ", "-", " ", "5"])
        
        self.assertExpression('''/*abc*/abc''',[ ["slcomment","abc"], "abc"])
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
        self.assertStatements("""function(a,b,c){ }""", [["function", [], [], None, [], ["a",",","b",",","c"], [], [" "] ]])
        self.assertStatements("""function a(b) {c;d}""", [["function", [], [" "], "a", [], ["b"], [" "], ["c",";","d"] ]])
        self.assertStatements("""var f = function(){};""", ["var"," ", "f", " ","="," ",["function", [], [], None, [], [], [], [] ], ";"])
        self.assertStatements("""function(){void(0);}""", [["function", [], [], None, [], [], [], ["void", ["parenthesis",["0"]],";"] ]])
        
        self.assertStatements("""{a:b,c:d}""", [[ "curly",["a",":","b", ",", "c",":","d"] ]])
        self.assertStatements("""{"a":"b","c":"d"}""", [[ "curly",['"a"',":",'"b"', ",", '"c"',":",'"d"'] ]])
        
        self.assertStatements("""[1,"b",function(){}]""",
            [ ["square",[ "1", ",", '"b"', ",", [ "function", [], [], None, [], [], [], [] ] ]] ])
        
        self.assertStatements("""if(a==b){ print x; }""",
            [ "if", ["parenthesis", ["a","==","b"]], ["curly", [" ", "print", " ", "x", ";"," "]] ])
            
        self.assertStatements("""
( (a+b)*5==11 )
""", [ "\n", ["parenthesis",[" ",["parenthesis",["a","+","b"]],"*","5", "==", "11"," "]],"\n"])
            
        self.assertStatements("""var a=5,b=6;""",[ "var"," ","a","=","5", "," , "b", "=", "6", ";" ])
        self.assertStatements("""var a={"a":"b","c":"d"},b=6;""", [ "var"," ","a","=",[ "curly",['"a"',":",'"b"', ",", '"c"',":",'"d"'] ], ",", "b","=","6",";"])

        self.assertStatements('''
(function(window,document,mark,assertion,fail){
})(window,document,mark,assertion,fail);
''', [
    "\n",
    ['parenthesis',[ ['function', [], [], None, [], ["window",",","document",",","mark",",","assertion",",","fail"], [], [
        "\n",
    ]] ]],
    ['parenthesis',["window",",","document",",","mark",",","assertion",",","fail"]],
    ";","\n"
])
        self.assertStatements('''
function(){
@insert();
}''',[
    "\n",
    ['function', [], [], None, [], [], [], [
        "\n", ["insert"], "\n"
    ]]
])

    def test_out(self):
        self.assertStatementsOut([";"], ";")

        self.assertStatementsOut(["a", " ", "+", " ", "b", " ", "-", " ", "5"], "a + b - 5")
        self.assertStatementsOut(["a"," ","=="," ","b"," ","+"," ","0x5"], "a == b + 0x5")
        self.assertStatementsOut(["a"," ","="," ","b"," ",">"," ",".5e","-","10"], "a = b > .5e-10")
        self.assertStatementsOut(["a", " ", "+", " ", "b", "/*...*/", " ", "-", " ", "5"], "a + b/*...*/ - 5")
        
        self.assertExpressionsOut(["12","+"," ","23","==","abc"], "12+ 23==abc")

        # self.assertExpressionsOut(["conditional", ["a"], ["b"], ['c']], """a?b:c""", rule="conditional_out")
        self.assertStatementsOut([ ["conditional", ["a"], ["b"], ["c"]] ], """a?b:c""")
        # self.assertExpressionsOut( ["parenthesis", [ " ","10", "+"," ","312","*","abc"]] , """(10 + 312*abc)""", rule="parenthesis_out")
        self.assertExpressionsOut([ ["parenthesis", " "] ], """( )""")
        self.assertExpressionsOut([ ["parenthesis", [ " ","10", "+"," ","312","*","abc"]] ], """( 10+ 312*abc)""")
        self.assertStatementsOut([["square",[ ["parenthesis", [ "5" ] ] ]]], """[(5)]""")

#         self.assertStatementsOut(["comment", " hello"], """\
# // hello""",rule="comment_out")
        self.assertStatementsOut([["comment", " hello"]], """\
// hello""")
        # self.assertStatementsOut([";"], ";")
        self.assertStatementsOut([["pass"]], "")
        
        self.assertStatementsOut([ ["function", [], [], None, [], [], [], [] ] ],"function(){}")
        self.assertStatementsOut([ ["function", [], ["/**/"], "A", [], [], [], [";"] ] ],"function/**/A(){;}")
        
    def test_macros(self):
        self.assertStatements("""@scope "a/b/c"  { function(){} }""", [
            ["scope", [" "], '"a/b/c"', [" "," "], [
                " ", [ "function", [], [], None, [], [], [], [] ], " "
            ]]
            ])
            
        self.assertStatements('''
@insert();
addExtension(new Extension());
''',["\n", ["insert"], "\n",
"addExtension", ['parenthesis',["new"," ","Extension",['parenthesis',[]] ]], ";",
"\n"
])
        self.assertStatements('''
''',["\n"
])

        
        self.assertStatements('''
(function(window,document,mark,assertion,fail,pagecore,addExtension){

    @insert();

    addExtension(new Extension());

})(window,document,mark,assertion,fail,pagecore,addExtension);
''', [
    "\n",
    ['parenthesis',[ ['function', [], [], None, [], ["window",",","document",",","mark",",","assertion",",","fail",",","pagecore",",","addExtension"], [], [
        "\n","\n"," "," "," "," ",
        ["insert"],
        "\n","\n"," "," "," "," ",
        "addExtension",
        ['parenthesis',["new"," ","Extension",['parenthesis',[]] ]],
        ";","\n","\n"
    ]] ]],
    ['parenthesis',["window",",","document",",","mark",",","assertion",",","fail",",","pagecore",",","addExtension"]],
    ";","\n"
])
            
        add_scope("'extension'",'''
(function(window,document,mark,assertion,fail,pagecore,addExtension){

    @insert();

    addExtension(new Extension());

})(window,document,mark,assertion,fail,pagecore,addExtension);

''')
        assert '"extension"' in scopes
            
        scoped = expand_macros([
            ["scope", [" "], '"a/b/c"', [" "," "], [
                " ", [ "function", [], [], None, [], [], [], [] ], " "
            ]]
        ]) 
        # print 'scoped', scoped
        assert scoped == [
            ["slcomment",'no scope "a/b/c"'],
            " ", [ "function", [], [], None, [], [], [], [] ], " "
        ]