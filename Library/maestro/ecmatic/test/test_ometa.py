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
        
    def fails_test_empty(self):
#         Grammar = OMeta.makeGrammar(r"""
# stuff = letter+:letters -> ''.join(letters) | empty -> 'nao'
# """, {})

        # doesn't seem to work, try alternative
        Grammar = OMeta.makeGrammar(r"""
stuff = letters | nothing
letters = letter+:letters -> ''.join(letters)
nothing = empty -> 'nao'
""", {})

        result,error = Grammar("").apply("stuff")
        assert result == "nao"
        result,error = Grammar("abc").apply("stuff")
        assert result == "abc"
        
    def test_spaces(self):
        Grammar = OMeta.makeGrammar(r"""
spaces_and_letters = spaces letter+:letters -> letters 
""", {})

        result, error = Grammar(" a").apply("spaces_and_letters")
        assert result == ['a']
        
    def test_tokens(self):
        Grammar = OMeta.makeGrammar(r"""
a = token('a') -> ('t','a')
b = token('b') -> ('t','b')
t = a | b
""",{})
        result, error = Grammar(" a").apply("t")
        assert result == ('t','a')
        result, error = Grammar(" b").apply("t")
        assert result == ('t','b')
        # result, error = Grammar("\0xa0 a").apply("t")
        # assert result == ('t','a')
        result, error = Grammar("\t a").apply("t")
        assert result == ('t','a')
        result, error = Grammar("\n a").apply("t")
        assert result == ('t','a')
        result, error = Grammar("a\n").apply("t")
        assert result == ('t','a')
        # TODO test that we are not at the end
        
    def no_test_begin(self):
        Grammar = OMeta.makeGrammar(r"""
from_start = begin 'a' -> 'a'
at_end = 'b' end -> 'b'
any = (from_start | at_end)*
""", {})
        result, error = Grammar(" a").apply("any")
        assert result == []
        
    def test_end(self):
        Grammar = OMeta.makeGrammar(r"""
at_end = 'b' end -> 'b|'
any = (at_end | anything)*
""", {})
        result, error = Grammar(" a").apply("any")
        assert result == [' ','a']
        result, error = Grammar("b a").apply("any")
        assert result == ['b',' ','a']
        result, error = Grammar(" ab").apply("any")
        assert result == [' ','a','b|']
        
    def test_uc(self):
        import sys
        # sys.setdefaultencoding('utf-8')
        import unicodedata
        assert unicodedata.category(u"a") == "Ll"
        
        Grammar = OMeta.makeGrammar(r"""
letters = UnicodeLetter*
number = UnicodeDigit*

UnicodeLetter = uc('L') | uc('Nl') | uc('Ll') | uc('Lu')
UnicodeCombiningMark = uc('Mn') | uc('Mc')
UnicodeDigit = uc('Nd')
UnicodeConnectorPunctuation = uc('Pc')
""",{})
        result, error = Grammar(u"a").apply("UnicodeLetter")
        assert result == u'a'
        result, error = Grammar(u"\u0393").apply("UnicodeLetter")
        assert result == u'\u0393'
        result, error = Grammar(u"\u03931").apply("letters")
        assert result == [u'\u0393']
        result, error = Grammar(u"123a").apply("number")
        assert result == [u'1', u'2', u'3']
        
    def test_ub(self):
        # paragraph test ub('B') 
        # segment test ub('S')
        # whitespace test ub('WS')
        pass
        
    def test_builtins(self):
        # char spaces letter anything
        pass

    def tets_cr_nl_encoding(self):
        pass
