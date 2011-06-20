from __future__ import with_statement

import unittest

from ecmatic.basic import Grammar, ast    

class GrammarTestCase(unittest.TestCase):
    
    def test_comment(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("comment")
        assert result == ["comment", {}, " hello"]

        g = Grammar("""/*
*/""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment', {}, "\n"]

        g = Grammar("""/***
///
***/""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment',{}, "**\n///\n**"]

        g = Grammar("""/*
 * hello ** ..
 * abc
 */""")
        result,error = g.apply("mlcomment")
        assert result == ['mlcomment', {},"\n * hello ** ..\n * abc\n "]

    def test_something_star_no_slash(self):
        g = Grammar("""\
 hello *""")
        result,error = g.apply("something_star_no_slash")
        assert result == " hello *"
        
    def test_linebreaks(self):
        """ backslash, CR LF LS PS"""
        pass
        
    def test_whitespace(self):
        pass
        
    def test_annotation(self):
        g = Grammar("""\
@abc""")
        result,error = g.apply("annotation")
        assert result == ['annotation', {}, 'abc']

        g = Grammar("""@abc()""")
        result,error = g.apply("annotation")
        assert result == ['annotation', {}, 'abc']

        g = Grammar("""@abc("url",5)""")
        result,error = g.apply("annotation")
        assert result == ['annotation', {}, 'abc','"url",5']

    def test_blocks(self):
        g = Grammar("""\
// hello""")
        result,error = g.apply("blocks")
        assert result == [["comment", {}, " hello"]]
        
        g = Grammar("""
// hello
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["comment", {}, " hello"],["comment", {}, " hello"]]

        g = Grammar("""
/* hello */
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", {}, " hello "],'\n',["comment", {}, " hello"]]

        g = Grammar("""
/* hello
 * hello*/
// hello""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", {}, " hello\n * hello"],'\n',["comment", {}, " hello"]]

        g = Grammar("""
/* hello */
// hello
@abc""")
        result,error = g.apply("blocks")
        assert result == ['\n',["mlcomment", {}, " hello "],'\n',["comment", {}, " hello"], ['annotation', {}, 'abc']]

    def test_k(self):
        g = Grammar("""typeof""")
        # result,error = g.apply("Keyword")
        # assert result == 'typeof'
        # result,error = g.apply("k","typeof")
        # assert result == 'typeof'
        
    def test_Statement(self):
        g = Grammar(""";""")
        result,error = g.apply("sourceElement")
        assert result == g.ast("empty")
        
    def test_function(self):
        g = Grammar("""function abc(){}""")
        result,error = g.apply("sourceElement")
        assert result == g.ast("func","abc",[],[])
        
        g = Grammar("""function abc(){}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[],[])]
        
        g = Grammar("""/* lead comment */ function abc(){}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("mlcomment"," lead comment "),g.ast("func","abc",[],[])]
        
        g = Grammar("""function abc(/* in args */){}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[g.ast("mlcomment"," in args ")],[])]
        
        g = Grammar("""function abc(// in args
def,ghi){}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[g.ast("comment"," in args"),"def,ghi"],[])]
        
        g = Grammar("""function abc(){;;}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[],[g.ast("empty"),g.ast("empty")])]
        
        g = Grammar("""function abc(){/* in block */;;}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[],[g.ast("mlcomment"," in block "),g.ast("empty"),g.ast("empty")])]
        
    def test_var(self):
        g = Grammar("""a""")
        result,error = g.apply("varDeclarations")
        assert result == [g.ast("a",[])]
        
        g = Grammar("""a,b,c,
        d""")
        result,error = g.apply("varDeclarations")
        assert result == [g.ast("a",[]),g.ast("b",[]),g.ast("c",[]),g.ast("d",[])]
        
        g = Grammar("""a = b""")
        result,error = g.apply("varDeclarations")
        assert result == [g.ast("a",["b"])]
        
        g = Grammar("""var abc = def
        var b = c; var d = e""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("var",[g.ast("abc",['def'])]),g.ast("var",[g.ast("b",['c'])]),g.ast("var",[g.ast("d",['e'])])]
        
        g = Grammar("""var abc
        var b; var d""")
        result,error = g.apply("sourceElements")
        assert result == [ 
            g.ast("var",[g.ast("abc",[])]), 
            g.ast("var",[g.ast("b",[])]), 
            g.ast("var",[g.ast("d",[])]) 
            ]

        g = Grammar("""var abc, def
        var a,b,c; var d,e""")
        result,error = g.apply("sourceElements")
        assert result == [
            g.ast("var",[
                g.ast("abc",[]),g.ast("def",[])
            ]),
            g.ast("var",[
                g.ast("a",[]),g.ast("b",[]),g.ast("c",[])
            ]),
            g.ast("var",[
                g.ast("d",[]),g.ast("e",[])
            ])
            ]
        
        g = Grammar("""var a,
        b = 5; var d/* = undefined */,e
        var
        x = 10""")
        result,error = g.apply("sourceElements")
        expect = [
            g.ast("var",[ g.ast("a",[]), g.ast("b",["5"]) ]),
            g.ast("var",[ g.ast("d",[],postfix=g.ast("mlcomment"," = undefined ")), g.ast("e",[]) ]),
            g.ast("var",[ g.ast("x",['10']) ])
        ]
        # assert result == expect
        
        
    def test_keyword_statements(self):
        g = Grammar("""debugger; debugger
        debugger""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","debugger", []),g.ast("simple","debugger", []),g.ast("simple","debugger", [])]

        g = Grammar("""continue; continue
        continue""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","continue", []),g.ast("simple","continue", []),g.ast("simple","continue", [])]

        g = Grammar("""break; break
        break""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","break", []),g.ast("simple","break", []),g.ast("simple","break", [])]
        
    def test_simple_statements(self):
        g = Grammar("""delete a; delete b
        delete c""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","delete", 'a'),g.ast("simple","delete", 'b'),g.ast("simple","delete", 'c')]

        g = Grammar("""return a; return b
        return c""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","return", 'a'),g.ast("simple","return", 'b'),g.ast("simple","return", 'c')]

        g = Grammar("""throw a; throw b
        throw c""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("simple","throw", 'a'),g.ast("simple","throw", 'b'),g.ast("simple","throw", 'c')]

        
    def test_block(self):
        g = Grammar("""function abc() {;}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[],[g.ast("empty")])]
        
        g = Grammar("""function abc() {; }""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("func","abc",[],[g.ast("empty")])]
        
        g = Grammar(""" {;}""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("block",[g.ast("empty")])]
        
        g = Grammar(""" {; }""")
        result,error = g.apply("sourceElements")
        assert result == [g.ast("block",[g.ast("empty")])]
        
    """
    function decl
    var decl
    assignment
    function call
    
    expression
    
    """ 
    
    def test_expression(self):
        g = Grammar(""" ++ """)
        result,error = g.apply("surrounded","++")
        assert result == "++"

        g = Grammar("""==""")
        result,error = g.apply("surrounded","==")
        assert result == "=="
        
        g = Grammar("""a""")
        result,error = g.apply("expression")
        assert result == ['a']
        
        g = Grammar("""a + b""")
        result,error = g.apply("expression")
        assert result == ['a','+','b']
        

        """
        a[b][c][d]
        a.b.c
        a[b].c
        (a[b])
        c + 5
        1 + 2
        "abc" 'def'
        0x123
        012
        12
        /abc/
        
        
        variable expressions
        literal expressions
        
        
        ['expr',{},'a']
        ['()',{},['a','-','b']]
        """
        pass
    
    def test_assignment(self):
        """Regular assignment of a previously declared variable or member of one"""
        pass
        
    def test_with(self):
        pass
        
    def test_control(self):
        " if / else / for / do / while "
        pass
        
    def test_try(self):
        " try / catch / finally "
        pass
    
    def test_labelledStatement(self):
        pass   
        
    def test_scanIdentifier(self):
        g = Grammar("""abc""")
        # result,error = g.apply("scanIdentifier")
        # assert result == 'abc'
        
        
        """
        function abc(a,b,c) { var hello = 5; }
        function abc(a,b,c) { var hello = 5 }
        function /* abc */ abc(a,b,c) { var hello = 5; }
        function abc/* abc */(/* abc() */a,b,c) {/* abc{} */ var hello = 5; }
        """
        