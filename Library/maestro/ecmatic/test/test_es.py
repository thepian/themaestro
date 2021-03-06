from __future__ import with_statement

import unittest

from ecmatic.es import Grammar, expand_macros, add_scope, scopes, load_and_add_scope, load_and_translate    

class GrammarTestCase(unittest.TestCase):
    
    def assertExpression(self, expr, expected, rule="expr"):
        result, error = Grammar(expr).apply(rule)
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
        
        self.assertExpression("a.b.c",["a",".","b",".","c"],rule="expr_lhs")
        self.assertExpression("a ",["a"],rule="expr_lhs")

        self.assertExpression("""?b:c""",  ["conditional", ["b"], ["c"]] , rule="conditional")
        self.assertExpression("""a?b:c""", [ "a", ["conditional", ["b"], ["c"]] ])
        self.assertExpression("""x=a?b:c""", [ "x","=","a", ["conditional", ["b"], ["c"]] ])
        self.assertExpression("""a?a():null""", [ "a", ["conditional", ["a",["parenthesis",[]]], ["null"]] ])
        """
        TODO labels, comma ops
        
        inline function void
        conditional ?:
        operators: single, combo, assignments
        lhs expr: just that, call, index, this
        simple expression: obj array lit space comment ()
        """
        
    def test_regex_vs_divide(self):
        """
        Test that there is proper differentiation between the two
        """
        pass
        
    def test_statements(self):
        self.assertStatements("""a?b:c""", [ "a", ["conditional", ["b"], ["c"]] ])
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
        self.assertStatements("""var x =a?b:c;""", [ "var"," ","x"," ","=", "a", ["conditional", ["b"], ["c"]], ";" ])
        self.assertStatements("""var x =a?a():null;""", [ "var"," ","x"," ","=", "a", ["conditional", ["a",["parenthesis",[]]], ["null"]], ";" ])

    def test_out(self):
        self.assertStatementsOut([";"], ";")

        self.assertStatementsOut(["a", " ", "+", " ", "b", " ", "-", " ", "5"], "a + b - 5")
        self.assertStatementsOut(["a"," ","=="," ","b"," ","+"," ","0x5"], "a == b + 0x5")
        self.assertStatementsOut(["a"," ","="," ","b"," ",">"," ",".5e","-","10"], "a = b > .5e-10")
        self.assertStatementsOut(["a", " ", "+", " ", "b", "/*...*/", " ", "-", " ", "5"], "a + b/*...*/ - 5")
        
        self.assertExpressionsOut(["12","+"," ","23","==","abc"], "12+ 23==abc")

        # self.assertExpressionsOut(["conditional", ["b"], ['c']], """?b:c""", rule="conditional_out")
        self.assertStatementsOut([ "a", ["conditional", ["b"], ["c"]] ], """a?b:c""")
        # self.assertExpressionsOut( ["parenthesis", [ " ","10", "+"," ","312","*","abc"]] , """(10 + 312*abc)""", rule="parenthesis_out")
        self.assertExpressionsOut([ ["parenthesis", " "] ], """( )""")
        self.assertExpressionsOut([ ["parenthesis", [ " ","10", "+"," ","312","*","abc"]] ], """( 10+ 312*abc)""")
        self.assertStatementsOut([["square",[ ["parenthesis", [ "5" ] ] ]]], """[(5)]""")

#         self.assertStatementsOut(["comment", " hello"], """\
# // hello""",rule="comment_out")
        self.assertStatementsOut([["comment", " hello"]], """\
// hello""")
        self.assertStatementsOut([["slcomment", " hello"]], """\
/* hello*/""")
        self.assertStatementsOut([["mlcomment", " hello"]], """\
/* hello*/""")
        # self.assertStatementsOut([";"], ";")
        self.assertStatementsOut([["pass"]], "")
        
        self.assertStatementsOut([ ["function", [], [], None, [], [], [], [] ] ],"function(){}")
        self.assertStatementsOut([ ["function", [], ["/**/"], "A", [], [], [], [";"] ] ],"function/**/A(){;}")
        
        self.assertStatementsOut([ ["statement",";"] ],";")

        self.assertStatementsOut([ ["function", [], [" "], "A", [], [], [], [ ["statement", "var"," ","a",";"], ";" ] ] ],"function A(){var a;;}")
        self.assertStatementsOut([ ["function", [], [" "], "A", [], ["one",",","two"], [], [ ["statement", "var"," ","a",";"], ";" ] ] ],"function A(one,two){var a;;}")
        
    def test_define_macros(self):
        self.assertStatements('''@define a;''',[
            ["define", None, "a", None]
        ])
        self.assertStatements('''@define a = b;''',[
            ["define", None, "a", [" ","b"]]
        ])
        self.assertStatements('''@define a = function(){;;};''',[
            ["define", None, "a", [" ",
                ["function", [], [], None, [], [], [], [";",";"] ] 
            ]]
        ])
        
    def test_insert_macros(self):
        # @insert var "abc";
        self.assertStatements('''@insert var exec_name;''',[
            ["insert", "var", "exec_name"]
        ])
        self.assertStatements('''@insert var "exec_name";''',[
            ["insert", "var", '"exec_name"']
        ])
        
    def test_import_macros(self):
        self.assertStatements('''@import a.b.c as c;''',[
            ["import","a.b.c","c"]
        ])
        self.assertStatements('''@import a.b.* as *;''',[
            ["starimport","a.b"]
        ])
        
         
         
        g = Grammar("""\
@import a.b.c as c;""")
        result,error = g.apply("statements")
        resolved = expand_macros(result)
        assert resolved == [["statement","var", " ","c","=","resolver",["parenthesis",[]],["parenthesis",['"',"a.b.c",'"']],";"]]
        self.assertStatementsOut(resolved,'var c=resolver()("a.b.c");')
         
    def test_scope_macros(self):
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
                    
        add_scope("'extension'",'''
(function(window,document,mark,assertion,fail,pagecore,addExtension){
@insert();
addExtension(new Extension());
})(window,document,mark,assertion,fail,pagecore,addExtension);
''')
        assert '"extension"' in scopes
            
        scoped = expand_macros([
            ["scope", [" "], '"extension"', [" "," "], [
                " ", [ "function", [], [], None, [], [], [], [] ], " "
            ]]
        ]) 
        # print 'scoped', scoped
        assert scoped == [
            "\n",
            ['parenthesis',[ ['function', [], [], None, [], ["window",",","document",",","mark",",","assertion",",","fail",",","pagecore",",","addExtension"], [], [
                "\n",
                " ", [ "function", [], [], None, [], [], [], [] ], " ",
                "\n",
                "addExtension", ['parenthesis',["new"," ","Extension",['parenthesis',[]] ]],
                ";","\n"
            ]] ]],
            ['parenthesis',["window",",","document",",","mark",",","assertion",",","fail",",","pagecore",",","addExtension"]],
            ";","\n"
        ]


        add_scope("'named'",'''
var @insert:test = (function(){
@insert();
})();
''')
        assert '"named"' in scopes

        scoped = expand_macros([
            ["scope", [" "], '"named"', [" "," "], [
                "/*before*/", [ "function", [], ["nested"], None, [], [], [], [] ], "/*after*/"
            ]]
        ], insert_vars=dict(test="test_var")) 
        
        print scoped
        
        assert scoped == [
            "\n", "var", " ", "test_var", " ", "=", " ",
            ['parenthesis',[ ['function', [], [], None, [], [], [], [
                "\n",
                "/*before*/", [ "function", [], ["nested"], None, [], [], [], [] ], "/*after*/",
                "\n"
            ]] ]],
            ['parenthesis',[]],
            ";","\n"
        ]
        
    def test_load_and_translate(self):
        from os.path import dirname, join
        named_path = join(dirname(__file__),"assets","named.scope.js")
        api_path = join(dirname(__file__),"assets","api.js")
        
        print named_path
        load_and_add_scope('"%s"' % "named.scope.js"[:-9], named_path)
        src, translated = load_and_translate(api_path, exec_name = "_exec_name_", specs = "_specs_")
        
        print translated
        
        assert translated == u'''\
var _exec_name_ = (function(specs){

alert();

})(_specs_);
''' 
        
    def test_should_expression(self):
        # should expression rule
        self.assertExpression('''a should == 5;
''', ["should",["a"],  ["==","5"] ], rule="should_expr")
#         self.assertExpression('''(a) should == 5;
# ''', ["should",[ ["parenthesis",["a"]] ], "==", ["5"]], rule="should_expr")
        self.assertExpression('''a[1] should == 5;
''', ["should",["a",["square",["1"]]], ["==", "5"]], rule="should_expr")
        self.assertExpression('''a.b should == 5;
''', ["should",["a",".","b"], ["==", "5"]], rule="should_expr")
        self.assertExpression('''a.b should < 5;
''', ["should",["a",".","b"], ["<", "5"]], rule="should_expr")
        self.assertExpression('''a should > 1 should <= 5;
''', ["should",["a"], [">", "1", " "], ["<=", "5"]], rule="should_expr")
        self.assertExpression('''a("b") should == 5;
''', ["should",["a",["parenthesis",['"b"']]], ["==", "5"]], rule="should_expr")
        self.assertExpression('''a should == 5 after_ms(100);
''', ["should",["a"],  ["==","5"," "], ["after_ms", "100"] ], rule="should_expr")
        self.assertExpression('''a should == 5 within_ms(100);
''', ["should",["a"],  ["==","5", " "], ["within_ms", "100"] ], rule="should_expr")

        self.assertExpression('''a should be_empty();
''', ["should",["a"],  ["be_empty", ["parenthesis", []]] ], rule="should_expr")

        self.assertExpression('''a should == 5;
''', [ ["should",["a"],  ["==","5"] ], "\n" ], rule="it_statements")
        self.assertExpression('''a should > 1 should < 5;
''', [ ["should",["a"],  [">","1"," "],  ["<","5"] ], "\n" ], rule="it_statements")
        
    def test_describe_macros(self):
        """
        @describe
        """
        #TODO lhs_opt_call possibility
        
        self.assertStatements('''
@describe "pagecore browser identification" {}
''',["\n",
        ["describe",None,'"pagecore browser identification"', []], 
        "\n"])

        self.assertStatements('''
@describe Object, "pagecore browser identification" {}
''',["\n",
        ["describe","Object",'"pagecore browser identification"', []], 
        "\n"])

        self.assertStatements('''
@describe String {}
''',["\n",
        ["describe","String",None, []], 
        "\n"])

        self.assertStatements('''
@describe "pagecore browser identification" {
it "should identify" {
}
}
''',["\n",
        ["describe", None,'"pagecore browser identification"',["\n",
            ["it", '"should identify"', [
                "\n"
            ]],
        "\n"]],
        "\n"])

        # Expanding describe and it
        described = expand_macros(["describe", None,'"pagecore browser identification"',["\n", 
            ["it", '"should identify"', [ "\n" ]],
        "\n"]])
        assert described == ["describe", None,'"pagecore browser identification"',["\n", 
            ["it", '"should identify"', [ "\n" ]],
        "\n"]]

        self.assertStatements('''
@describe "pagecore browser identification" {
it "should identify" {
a should == 5;
}
}
''',["\n",
        ["describe", None,'"pagecore browser identification"', ["\n", 
            ["it", '"should identify"', ["\n", 
                ["should", ["a"], ["==", "5"]], 
                "\n" 
            ]],
        "\n"]],
        "\n"])
        
        # Expanding should expression statement
        described = expand_macros(["describe", None,'"pagecore browser identification"', ["\n", 
            ["it", '"should identify"', ["\n", 
                ["should", ["a"], ["==", "5"]], 
                "\n" 
            ]],
        "\n"]])
        assert described == ["describe", None,'"pagecore browser identification"', ["\n", 
            ["it", '"should identify"',["\n", 
                ["should", ["a"], ["==", "5"]], 
                "\n" 
            ]],
        "\n"]]

    def test_describe_out(self):
        self.assertStatementsOut([ ["describe",None, '"pagecore browser identification"', []] ], Grammar.describe_out_text % ("null",'"pagecore browser identification"', ""))
        self.assertStatementsOut([ ["describe", "Object", None, []] ], Grammar.describe_out_text % ("Object",'null', ""))
        self.assertStatementsOut([ ["it",'"should identify"', []] ], Grammar.it_out_text % ('"should identify"', ""))
        self.assertStatementsOut([ ["it",'"should identify"', [";", "var"," ","a","=","5", ";",";"]] ], Grammar.it_out_text % ('"should identify"', ";var a=5;;"))
        self.assertStatementsOut([ ["it",'"should identify"', [";", "var"," ","f","=", [ "function", [], [], None, [], [], [], [] ], ";",";"]] ], Grammar.it_out_text % ('"should identify"', ";var f=function(){};;"))
        self.assertStatementsOut([ ["should", ["a"], ["==", "5"]] ], Grammar.should_out_text % ("a","'a'", "[ '==', function(){ return 5; }, '5' ]"))
        self.assertStatementsOut([ ["should", ["a"], ["<", "5"], [">", "1"]] ], Grammar.should_out_text % ("a","'a'", "[ '<', function(){ return 5; }, '5','>', function(){ return 1; }, '1' ]"))
    
    def no_test_describe_macros(self):
        self.assertStatements('''
@describe "pagecore browser identification" {
it "should identify" {
a should == 5;
}
}
''',["\n",
        ["describe", None,'"pagecore browser identification"', ["\n",
            ["it", '"should identify"', ["\n",
                ["should", ["a"], ["==", "5"]], 
                "\n"
            ]],
        "\n"]],
        "\n"])
    
    