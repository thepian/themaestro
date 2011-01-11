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
        